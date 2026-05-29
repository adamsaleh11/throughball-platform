import hashlib
import json
from dataclasses import dataclass
from typing import Any, Optional, Protocol
from urllib.parse import quote
from uuid import UUID

import httpx

from app.core.config import get_settings
from app.core.profile import AuthenticatedUser
from app.core.worldcup import build_pagination


@dataclass(frozen=True)
class ItineraryInputCommand:
    city_id: UUID
    match_id: Optional[UUID]
    date: Optional[str]
    party_size: int
    interests: list[str]
    pace: str


@dataclass(frozen=True)
class ItineraryItemCommand:
    position: int
    item_type: str
    source_table: Optional[str]
    source_id: Optional[UUID]
    title: str
    description: Optional[str]
    starts_at: Optional[str]
    ends_at: Optional[str]
    area_label: Optional[str]
    route_context: dict[str, Any]


@dataclass(frozen=True)
class SaveItineraryCommand:
    input: ItineraryInputCommand
    title: str
    summary: Optional[str]
    items: list[ItineraryItemCommand]


@dataclass(frozen=True)
class ItineraryHistoryQuery:
    page: int = 1
    page_size: int = 20


class ItineraryStorageError(RuntimeError):
    def __init__(self, message: str, status_code: int = 503) -> None:
        super().__init__(message)
        self.status_code = status_code


class ItineraryService(Protocol):
    async def save_itinerary(
        self,
        user: AuthenticatedUser,
        command: SaveItineraryCommand,
    ) -> dict[str, Any]:
        ...

    async def itineraries_for_user(
        self,
        user: AuthenticatedUser,
        query: ItineraryHistoryQuery,
    ) -> dict[str, Any]:
        ...


class ItineraryStore(Protocol):
    async def find_by_input_hash(
        self,
        user: AuthenticatedUser,
        input_hash: str,
    ) -> Optional[dict[str, Any]]:
        ...

    async def create_itinerary(
        self,
        user: AuthenticatedUser,
        payload: dict[str, Any],
        items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        ...

    async def fetch_itineraries(
        self,
        user: AuthenticatedUser,
        page: int,
        page_size: int,
    ) -> tuple[list[dict[str, Any]], int]:
        ...


class DefaultItineraryService:
    def __init__(self, store: Optional[ItineraryStore] = None) -> None:
        self._store = store

    async def save_itinerary(
        self,
        user: AuthenticatedUser,
        command: SaveItineraryCommand,
    ) -> dict[str, Any]:
        if self._store is None:
            raise ItineraryStorageError("Itinerary persistence is not configured.")

        input_payload = normalize_input(command.input)
        input_hash = hash_input(input_payload)
        existing = await self._store.find_by_input_hash(user, input_hash)
        if existing:
            return {"itinerary": itinerary_contract(existing), "reused": True}

        payload = {
            "user_id": user.user_id,
            "city_id": input_payload["city_id"],
            "match_id": input_payload["match_id"],
            "input_hash": input_hash,
            "input_payload": input_payload,
            "title": command.title,
            "summary": command.summary,
            "status": "saved",
        }
        items = [
            {
                "position": item.position,
                "item_type": item.item_type,
                "source_table": item.source_table,
                "source_id": str(item.source_id) if item.source_id else None,
                "title": item.title,
                "description": item.description,
                "starts_at": item.starts_at,
                "ends_at": item.ends_at,
                "area_label": item.area_label,
                "route_context": item.route_context,
            }
            for item in sorted(command.items, key=lambda item: item.position)
        ]
        row = await self._store.create_itinerary(user, payload, items)
        return {"itinerary": itinerary_contract(row), "reused": False}

    async def itineraries_for_user(
        self,
        user: AuthenticatedUser,
        query: ItineraryHistoryQuery,
    ) -> dict[str, Any]:
        if self._store is None:
            raise ItineraryStorageError("Itinerary persistence is not configured.")

        rows, total_items = await self._store.fetch_itineraries(user, query.page, query.page_size)
        return {
            "itineraries": [itinerary_contract(row) for row in rows],
            "pagination": build_pagination(query.page, query.page_size, total_items),
        }


class SupabaseItineraryStore:
    def __init__(self) -> None:
        settings = get_settings()
        self.supabase_url = settings.effective_supabase_url.rstrip("/")
        self.supabase_anon_key = settings.effective_supabase_anon_key

    async def find_by_input_hash(
        self,
        user: AuthenticatedUser,
        input_hash: str,
    ) -> Optional[dict[str, Any]]:
        rows = await self._get_many(
            "itineraries",
            "select=id,user_id,city_id,match_id,input_hash,input_payload,title,summary,status,created_at,updated_at"
            f"&user_id=eq.{user.user_id}&input_hash=eq.{quote(input_hash, safe='')}&limit=1",
            user,
        )
        if not rows:
            return None
        return await self._with_items(rows[0], user)

    async def create_itinerary(
        self,
        user: AuthenticatedUser,
        payload: dict[str, Any],
        items: list[dict[str, Any]],
    ) -> dict[str, Any]:
        itinerary = await self._post_one("itineraries", payload, user)
        item_payloads = [{**item, "itinerary_id": itinerary["id"]} for item in items]
        created_items = (
            await self._post_many("itinerary_items", item_payloads, user)
            if item_payloads
            else []
        )
        return {**itinerary, "items": created_items}

    async def fetch_itineraries(
        self,
        user: AuthenticatedUser,
        page: int,
        page_size: int,
    ) -> tuple[list[dict[str, Any]], int]:
        offset = (page - 1) * page_size
        rows = await self._get_many(
            "itineraries",
            "select=id,user_id,city_id,match_id,input_hash,input_payload,title,summary,status,created_at,updated_at"
            f"&user_id=eq.{user.user_id}&order=updated_at.desc&order=created_at.desc&limit={page_size}&offset={offset}",
            user,
        )
        count_rows = await self._get_many(
            "itineraries",
            f"select=id&user_id=eq.{user.user_id}",
            user,
        )
        return [await self._with_items(row, user) for row in rows], len(count_rows)

    async def _with_items(self, itinerary: dict[str, Any], user: AuthenticatedUser) -> dict[str, Any]:
        items = await self._get_many(
            "itinerary_items",
            "select=id,itinerary_id,position,item_type,source_table,source_id,title,description,starts_at,ends_at,area_label,route_context,created_at"
            f"&itinerary_id=eq.{itinerary['id']}&order=position.asc",
            user,
        )
        return {**itinerary, "items": items}

    async def _get_many(
        self,
        table: str,
        query: str,
        user: AuthenticatedUser,
    ) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{self.supabase_url}/rest/v1/{table}?{query}",
                headers=self._headers(user),
            )
        self._raise_for_storage_error(response, table)
        data = response.json()
        return data if isinstance(data, list) else [data]

    async def _post_one(
        self,
        table: str,
        payload: dict[str, Any],
        user: AuthenticatedUser,
    ) -> dict[str, Any]:
        rows = await self._post_many(table, payload, user)
        return rows[0] if rows else {}

    async def _post_many(
        self,
        table: str,
        payload: Any,
        user: AuthenticatedUser,
    ) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{self.supabase_url}/rest/v1/{table}",
                headers={
                    **self._headers(user),
                    "prefer": "return=representation",
                },
                json=payload,
            )
        self._raise_for_storage_error(response, table)
        data = response.json()
        return data if isinstance(data, list) else [data]

    def _headers(self, user: AuthenticatedUser) -> dict[str, str]:
        if not self.supabase_url or not self.supabase_anon_key:
            raise ItineraryStorageError("Supabase URL and anon key are required for itinerary APIs.")
        return {
            "apikey": self.supabase_anon_key,
            "authorization": f"Bearer {user.access_token}",
            "content-type": "application/json",
        }

    def _raise_for_storage_error(self, response: httpx.Response, table: str) -> None:
        if response.status_code == 404:
            raise ItineraryStorageError(
                f"Supabase table '{table}' is not available. Apply the itinerary persistence migration.",
                status_code=503,
            )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ItineraryStorageError("Supabase itinerary storage request failed.") from exc


def normalize_input(command: ItineraryInputCommand) -> dict[str, Any]:
    interests = sorted({interest.strip() for interest in command.interests if interest.strip()})
    return {
        "city_id": str(command.city_id),
        "match_id": str(command.match_id) if command.match_id else None,
        "date": command.date,
        "party_size": command.party_size,
        "interests": interests,
        "pace": command.pace,
    }


def hash_input(input_payload: dict[str, Any]) -> str:
    encoded = json.dumps(input_payload, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


def itinerary_contract(row: dict[str, Any]) -> dict[str, Any]:
    items = [
        itinerary_item_contract(item)
        for item in sorted(row.get("items", []), key=lambda item: item["position"])
    ]
    return {
        "itinerary_id": row["id"],
        "city_id": row["city_id"],
        "match_id": row.get("match_id"),
        "input_hash": row["input_hash"],
        "input": row["input_payload"],
        "title": row["title"],
        "summary": row.get("summary"),
        "status": row.get("status", "saved"),
        "items": items,
        "created_at": row["created_at"],
        "updated_at": row["updated_at"],
    }


def itinerary_item_contract(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "item_id": row["id"],
        "position": row["position"],
        "item_type": row["item_type"],
        "source_table": row.get("source_table"),
        "source_id": row.get("source_id"),
        "title": row["title"],
        "description": row.get("description"),
        "starts_at": row.get("starts_at"),
        "ends_at": row.get("ends_at"),
        "area_label": row.get("area_label"),
        "route_context": row.get("route_context", {}),
    }


def get_default_itinerary_service() -> ItineraryService:
    return DefaultItineraryService(SupabaseItineraryStore())
