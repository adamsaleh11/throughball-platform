from dataclasses import dataclass
from typing import Any, Optional, Protocol
from uuid import UUID

import httpx

from app.core.config import get_settings
from app.core.profile import AuthenticatedUser
from app.core.worldcup import build_pagination


@dataclass(frozen=True)
class CreateCheckinCommand:
    city_id: UUID
    match_id: Optional[UUID]
    venue_id: Optional[UUID]
    latitude: float
    longitude: float
    checked_in_at: Optional[str]


@dataclass(frozen=True)
class CheckinHistoryQuery:
    page: int = 1
    page_size: int = 20


@dataclass(frozen=True)
class HotspotQuery:
    city_id: UUID
    match_id: Optional[UUID] = None
    page: int = 1
    page_size: int = 20


class FanStorageError(RuntimeError):
    def __init__(self, message: str, status_code: int = 503) -> None:
        super().__init__(message)
        self.status_code = status_code


class FanService(Protocol):
    async def create_checkin(
        self,
        user: AuthenticatedUser,
        command: CreateCheckinCommand,
    ) -> dict[str, Any]:
        ...

    async def checkins_for_user(
        self,
        user: AuthenticatedUser,
        query: CheckinHistoryQuery,
    ) -> dict[str, Any]:
        ...

    async def hotspots(self, query: HotspotQuery) -> dict[str, Any]:
        ...


class SupabaseFanStore:
    def __init__(self) -> None:
        settings = get_settings()
        self.supabase_url = settings.effective_supabase_url.rstrip("/")
        self.supabase_anon_key = settings.effective_supabase_anon_key

    async def create_checkin(
        self,
        user: AuthenticatedUser,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{self.supabase_url}/rest/v1/fan_checkins",
                headers={
                    **self._user_headers(user),
                    "prefer": "return=representation",
                },
                json=payload,
            )
        self._raise_for_storage_error(response, "fan_checkins")
        data = response.json()
        return data[0] if isinstance(data, list) else data

    async def fetch_checkins(
        self,
        user: AuthenticatedUser,
        page: int,
        page_size: int,
    ) -> tuple[list[dict[str, Any]], int]:
        offset = (page - 1) * page_size
        query = (
            "select=id,city_id,match_id,venue_id,checked_in_at,created_at"
            f"&user_id=eq.{user.user_id}&order=checked_in_at.desc&limit={page_size}&offset={offset}"
        )
        rows = await self._get_many("fan_checkins", query, self._user_headers(user))
        count_rows = await self._get_many(
            "fan_checkins",
            f"select=id&user_id=eq.{user.user_id}",
            self._user_headers(user),
        )
        return rows, len(count_rows)

    async def fetch_hotspots(
        self,
        query: HotspotQuery,
    ) -> tuple[list[dict[str, Any]], int]:
        offset = (query.page - 1) * query.page_size
        query_parts = [
            "select=id,city_id,match_id,area_label,center_lat,center_lng,center_precision,score,confidence,supporter_count,top_venue_ids,ranking_factors,updated_at",
            f"city_id=eq.{query.city_id}",
            "order=score.desc",
            f"limit={query.page_size}",
            f"offset={offset}",
        ]
        count_parts = ["select=id", f"city_id=eq.{query.city_id}"]
        if query.match_id:
            query_parts.append(f"match_id=eq.{query.match_id}")
            count_parts.append(f"match_id=eq.{query.match_id}")

        rows = await self._get_many("fan_hotspots", "&".join(query_parts), self._public_headers())
        count_rows = await self._get_many("fan_hotspots", "&".join(count_parts), self._public_headers())
        return rows, len(count_rows)

    async def _get_many(
        self,
        table: str,
        query: str,
        headers: dict[str, str],
    ) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{self.supabase_url}/rest/v1/{table}?{query}",
                headers=headers,
            )
        self._raise_for_storage_error(response, table)
        data = response.json()
        return data if isinstance(data, list) else [data]

    def _user_headers(self, user: AuthenticatedUser) -> dict[str, str]:
        if not self.supabase_url or not self.supabase_anon_key:
            raise FanStorageError("Supabase URL and anon key are required for fan APIs.")
        return {
            "apikey": self.supabase_anon_key,
            "authorization": f"Bearer {user.access_token}",
            "content-type": "application/json",
        }

    def _public_headers(self) -> dict[str, str]:
        if not self.supabase_url or not self.supabase_anon_key:
            raise FanStorageError("Supabase URL and anon key are required for hotspot APIs.")
        return {
            "apikey": self.supabase_anon_key,
            "authorization": f"Bearer {self.supabase_anon_key}",
        }

    def _raise_for_storage_error(self, response: httpx.Response, table: str) -> None:
        if response.status_code == 404:
            raise FanStorageError(f"Supabase table '{table}' is not available. Apply the fan migration.")
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise FanStorageError("Supabase fan storage request failed.") from exc


class DefaultFanService:
    def __init__(self, store: Optional[SupabaseFanStore] = None) -> None:
        self._store = store or SupabaseFanStore()

    async def create_checkin(
        self,
        user: AuthenticatedUser,
        command: CreateCheckinCommand,
    ) -> dict[str, Any]:
        payload = {
            "user_id": user.user_id,
            "city_id": str(command.city_id),
            "match_id": str(command.match_id) if command.match_id else None,
            "venue_id": str(command.venue_id) if command.venue_id else None,
            "latitude": command.latitude,
            "longitude": command.longitude,
            "visibility": "private",
        }
        if command.checked_in_at:
            payload["checked_in_at"] = command.checked_in_at

        row = await self._store.create_checkin(user, payload)
        return checkin_contract(row)

    async def checkins_for_user(
        self,
        user: AuthenticatedUser,
        query: CheckinHistoryQuery,
    ) -> dict[str, Any]:
        rows, total_items = await self._store.fetch_checkins(user, query.page, query.page_size)
        return {
            "checkins": [checkin_contract(row) for row in rows],
            "pagination": build_pagination(query.page, query.page_size, total_items),
        }

    async def hotspots(self, query: HotspotQuery) -> dict[str, Any]:
        rows, total_items = await self._store.fetch_hotspots(query)
        return {
            "hotspots": [hotspot_contract(row) for row in rows],
            "pagination": build_pagination(query.page, query.page_size, total_items),
        }


def checkin_contract(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "checkin_id": row["id"],
        "city_id": row["city_id"],
        "match_id": row.get("match_id"),
        "venue_id": row.get("venue_id"),
        "checked_in_at": row["checked_in_at"],
        "created_at": row["created_at"],
    }


def hotspot_contract(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "hotspot_id": row["id"],
        "city_id": row["city_id"],
        "match_id": row.get("match_id"),
        "area_label": row["area_label"],
        "center": {
            "lat": row["center_lat"],
            "lng": row["center_lng"],
            "precision": row["center_precision"],
        },
        "score": row["score"],
        "confidence": float(row["confidence"]),
        "supporter_count": row["supporter_count"],
        "top_venue_ids": row.get("top_venue_ids", []),
        "ranking_factors": row.get("ranking_factors", {}),
        "updated_at": row["updated_at"],
    }


def get_default_fan_service() -> FanService:
    return DefaultFanService()
