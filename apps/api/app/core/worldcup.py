from dataclasses import dataclass
from typing import Any, Optional, Protocol, TypedDict

import httpx

from app.core.config import get_settings


class Pagination(TypedDict):
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool


class CityContract(TypedDict):
    city_id: str
    name: str
    country_code: str
    stadium_name: Optional[str]
    timezone: Optional[str]


class MatchContract(TypedDict):
    match_id: str
    city_id: str
    home_team: Optional[str]
    away_team: Optional[str]
    competition: str
    starts_at: str
    status: str
    tags: list[str]


class MatchCatalogPage(TypedDict):
    matches: list[MatchContract]
    pagination: Pagination


@dataclass(frozen=True)
class MatchCatalogQuery:
    city_id: Optional[str] = None
    page: int = 1
    page_size: int = 20


@dataclass(frozen=True)
class StorePage:
    rows: list[dict[str, Any]]
    total_items: int


class WorldCupStorageError(RuntimeError):
    def __init__(self, message: str, status_code: int = 503) -> None:
        super().__init__(message)
        self.status_code = status_code


class WorldCupCatalog(Protocol):
    async def cities(self) -> list[CityContract]:
        ...

    async def matches(self, query: MatchCatalogQuery) -> MatchCatalogPage:
        ...


class WorldCupCatalogStore(Protocol):
    async def fetch_host_cities(self) -> list[dict[str, Any]]:
        ...

    async def fetch_matches(self, query: MatchCatalogQuery) -> StorePage:
        ...


class DefaultWorldCupCatalog:
    def __init__(self, store: WorldCupCatalogStore) -> None:
        self._store = store

    async def cities(self) -> list[CityContract]:
        rows = await self._store.fetch_host_cities()
        return [city_contract(row) for row in rows]

    async def matches(self, query: MatchCatalogQuery) -> MatchCatalogPage:
        page = await self._store.fetch_matches(query)
        return {
            "matches": [match_contract(row) for row in page.rows],
            "pagination": build_pagination(query.page, query.page_size, page.total_items),
        }


class SupabaseWorldCupStore:
    def __init__(self) -> None:
        settings = get_settings()
        self.supabase_url = settings.effective_supabase_url.rstrip("/")
        self.supabase_anon_key = settings.effective_supabase_anon_key

    async def fetch_host_cities(self) -> list[dict[str, Any]]:
        return await self._get_many(
            "host_cities",
            "select=id,name,country_code,stadium_name,timezone&order=name.asc",
        )

    async def fetch_matches(self, query: MatchCatalogQuery) -> StorePage:
        offset = (query.page - 1) * query.page_size
        query_parts = [
            "select=id,city_id,competition,stage,kickoff_time,status,tags,home_team:teams!matches_home_team_id_fkey(name),away_team:teams!matches_away_team_id_fkey(name)",
            "order=kickoff_time.asc",
            f"limit={query.page_size}",
            f"offset={offset}",
        ]
        count_query_parts = ["select=id"]
        if query.city_id:
            query_parts.append(f"city_id=eq.{query.city_id}")
            count_query_parts.append(f"city_id=eq.{query.city_id}")

        rows = await self._get_many("matches", "&".join(query_parts))
        count_rows = await self._get_many("matches", "&".join(count_query_parts))
        return StorePage(rows=rows, total_items=len(count_rows))

    def _headers(self) -> dict[str, str]:
        if not self.supabase_url or not self.supabase_anon_key:
            raise WorldCupStorageError(
                "Supabase URL and anon key are required for World Cup data APIs."
            )
        return {
            "apikey": self.supabase_anon_key,
            "authorization": f"Bearer {self.supabase_anon_key}",
        }

    async def _get_many(self, table: str, query: str) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{self.supabase_url}/rest/v1/{table}?{query}",
                headers=self._headers(),
            )
        self._raise_for_storage_error(response, table)
        data = response.json()
        return data if isinstance(data, list) else [data]

    def _raise_for_storage_error(self, response: httpx.Response, table: str) -> None:
        if response.status_code == 404:
            raise WorldCupStorageError(
                f"Supabase table '{table}' is not available. Apply the World Cup migration."
            )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise WorldCupStorageError("Supabase World Cup storage request failed.") from exc


def build_pagination(page: int, page_size: int, total_items: int) -> Pagination:
    total_pages = (total_items + page_size - 1) // page_size if total_items else 0
    return {
        "page": page,
        "page_size": page_size,
        "total_items": total_items,
        "total_pages": total_pages,
        "has_next": page < total_pages,
    }


def city_contract(row: dict[str, Any]) -> CityContract:
    return {
        "city_id": row["id"],
        "name": row["name"],
        "country_code": row["country_code"],
        "stadium_name": row.get("stadium_name"),
        "timezone": row.get("timezone"),
    }


def match_contract(row: dict[str, Any]) -> MatchContract:
    return {
        "match_id": row["id"],
        "city_id": row["city_id"],
        "home_team": row.get("home_team", {}).get("name"),
        "away_team": row.get("away_team", {}).get("name"),
        "competition": row["competition"],
        "starts_at": row["kickoff_time"],
        "status": row["status"],
        "tags": row.get("tags", []),
    }


def get_default_worldcup_catalog() -> WorldCupCatalog:
    return DefaultWorldCupCatalog(SupabaseWorldCupStore())
