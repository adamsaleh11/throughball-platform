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


class TeamSummaryContract(TypedDict):
    team_id: str
    name: str
    country_code: str


class MatchDetailContract(TypedDict):
    match_id: str
    city: CityContract
    home_team: TeamSummaryContract
    away_team: TeamSummaryContract
    competition: str
    stage: str
    starts_at: str
    status: str
    tags: list[str]


class MatchCatalogPage(TypedDict):
    matches: list[MatchContract]
    pagination: Pagination


class MatchDetailPage(TypedDict):
    match: MatchDetailContract


class MatchStatsContract(TypedDict):
    team_id: str
    team_name: str
    goals: int
    possession_pct: Optional[float]
    shots: int
    shots_on_target: int
    passes: int
    corners: int
    fouls: int


class MatchStatsPage(TypedDict):
    stats: list[MatchStatsContract]


class MatchEventContract(TypedDict):
    event_id: str
    team_id: str
    team_name: str
    player_id: Optional[str]
    player_name: Optional[str]
    event_type: str
    minute: int
    stoppage_minute: Optional[int]
    description: Optional[str]


class MatchEventsPage(TypedDict):
    events: list[MatchEventContract]


class MatchMomentumContract(TypedDict):
    snapshot_id: str
    team_id: str
    team_name: str
    minute: int
    formation: str
    possession_style: str
    press_intensity: str
    defensive_line: str
    confidence: float


class MatchMomentumPage(TypedDict):
    momentum: list[MatchMomentumContract]


@dataclass(frozen=True)
class MatchCatalogQuery:
    city_id: Optional[str] = None
    status: Optional[str] = None
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


class WorldCupNotFoundError(RuntimeError):
    def __init__(self, message: str, code: str = "WORLDCUP_MATCH_NOT_FOUND") -> None:
        super().__init__(message)
        self.code = code


class WorldCupCatalog(Protocol):
    async def cities(self) -> list[CityContract]:
        ...

    async def matches(self, query: MatchCatalogQuery) -> MatchCatalogPage:
        ...

    async def match(self, match_id: str) -> MatchDetailPage:
        ...

    async def match_stats(self, match_id: str) -> MatchStatsPage:
        ...

    async def match_events(self, match_id: str) -> MatchEventsPage:
        ...

    async def match_momentum(self, match_id: str) -> MatchMomentumPage:
        ...


class WorldCupCatalogStore(Protocol):
    async def fetch_host_cities(self) -> list[dict[str, Any]]:
        ...

    async def fetch_matches(self, query: MatchCatalogQuery) -> StorePage:
        ...

    async def fetch_match(self, match_id: str) -> Optional[dict[str, Any]]:
        ...

    async def fetch_match_stats(self, match_id: str) -> list[dict[str, Any]]:
        ...

    async def fetch_match_events(self, match_id: str) -> list[dict[str, Any]]:
        ...

    async def fetch_match_momentum(self, match_id: str) -> list[dict[str, Any]]:
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

    async def match(self, match_id: str) -> MatchDetailPage:
        row = await self._store.fetch_match(match_id)
        if row is None:
            raise WorldCupNotFoundError(f"World Cup match '{match_id}' was not found.")
        return {"match": match_detail_contract(row)}

    async def match_stats(self, match_id: str) -> MatchStatsPage:
        await self._require_match(match_id)
        rows = await self._store.fetch_match_stats(match_id)
        return {"stats": [match_stats_contract(row) for row in rows]}

    async def match_events(self, match_id: str) -> MatchEventsPage:
        await self._require_match(match_id)
        rows = await self._store.fetch_match_events(match_id)
        return {"events": [match_event_contract(row) for row in rows]}

    async def match_momentum(self, match_id: str) -> MatchMomentumPage:
        await self._require_match(match_id)
        rows = await self._store.fetch_match_momentum(match_id)
        return {"momentum": [match_momentum_contract(row) for row in rows]}

    async def _require_match(self, match_id: str) -> None:
        if await self._store.fetch_match(match_id) is None:
            raise WorldCupNotFoundError(f"World Cup match '{match_id}' was not found.")


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
        ]
        if query.city_id:
            query_parts.append(f"city_id=eq.{query.city_id}")
        if query.status:
            query_parts.append(f"status=eq.{query.status}")

        return await self._get_page(
            "matches",
            "&".join(query_parts),
            offset=offset,
            limit=query.page_size,
        )

    async def fetch_match(self, match_id: str) -> Optional[dict[str, Any]]:
        rows = await self._get_many(
            "matches",
            "select=id,competition,stage,kickoff_time,status,tags,"
            "city:host_cities(id,name,country_code,stadium_name,timezone),"
            "home_team:teams!matches_home_team_id_fkey(id,name,country_code),"
            "away_team:teams!matches_away_team_id_fkey(id,name,country_code)"
            f"&id=eq.{match_id}&limit=1",
        )
        return rows[0] if rows else None

    async def fetch_match_stats(self, match_id: str) -> list[dict[str, Any]]:
        return await self._get_many(
            "match_stats",
            "select=match_id,goals,possession_pct,shots,shots_on_target,passes,corners,fouls,"
            "team:teams(id,name)"
            f"&match_id=eq.{match_id}",
        )

    async def fetch_match_events(self, match_id: str) -> list[dict[str, Any]]:
        return await self._get_many(
            "match_events",
            "select=id,event_type,minute,stoppage_minute,description,"
            "team:teams(id,name),player:players(id,full_name)"
            f"&match_id=eq.{match_id}&order=minute.asc&order=stoppage_minute.asc&order=created_at.asc",
        )

    async def fetch_match_momentum(self, match_id: str) -> list[dict[str, Any]]:
        return await self._get_many(
            "tactical_snapshots",
            "select=id,snapshot_minute,formation,possession_style,press_intensity,defensive_line,confidence,"
            "team:teams(id,name)"
            f"&match_id=eq.{match_id}&order=snapshot_minute.asc",
        )

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

    async def _get_page(self, table: str, query: str, offset: int, limit: int) -> StorePage:
        end = offset + limit - 1
        headers = {
            **self._headers(),
            "prefer": "count=exact",
            "range": f"{offset}-{end}",
        }
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{self.supabase_url}/rest/v1/{table}?{query}",
                headers=headers,
            )
        self._raise_for_storage_error(response, table)
        data = response.json()
        rows = data if isinstance(data, list) else [data]
        return StorePage(rows=rows, total_items=parse_content_range_total(response))

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


def parse_content_range_total(response: httpx.Response) -> int:
    content_range = response.headers.get("content-range", "")
    if "/" not in content_range:
        return 0
    total = content_range.rsplit("/", 1)[-1]
    return 0 if total == "*" else int(total)


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


def team_summary_contract(row: dict[str, Any]) -> TeamSummaryContract:
    return {
        "team_id": row["id"],
        "name": row["name"],
        "country_code": row["country_code"],
    }


def match_detail_contract(row: dict[str, Any]) -> MatchDetailContract:
    return {
        "match_id": row["id"],
        "city": city_contract(row["city"]),
        "home_team": team_summary_contract(row["home_team"]),
        "away_team": team_summary_contract(row["away_team"]),
        "competition": row["competition"],
        "stage": row["stage"],
        "starts_at": row["kickoff_time"],
        "status": row["status"],
        "tags": row.get("tags", []),
    }


def match_stats_contract(row: dict[str, Any]) -> MatchStatsContract:
    possession_pct = row.get("possession_pct")
    return {
        "team_id": row["team"]["id"],
        "team_name": row["team"]["name"],
        "goals": row["goals"],
        "possession_pct": float(possession_pct) if possession_pct is not None else None,
        "shots": row["shots"],
        "shots_on_target": row["shots_on_target"],
        "passes": row["passes"],
        "corners": row["corners"],
        "fouls": row["fouls"],
    }


def match_event_contract(row: dict[str, Any]) -> MatchEventContract:
    player = row.get("player")
    return {
        "event_id": row["id"],
        "team_id": row["team"]["id"],
        "team_name": row["team"]["name"],
        "player_id": player.get("id") if player else None,
        "player_name": player.get("full_name") if player else None,
        "event_type": row["event_type"],
        "minute": row["minute"],
        "stoppage_minute": row.get("stoppage_minute"),
        "description": row.get("description"),
    }


def match_momentum_contract(row: dict[str, Any]) -> MatchMomentumContract:
    return {
        "snapshot_id": row["id"],
        "team_id": row["team"]["id"],
        "team_name": row["team"]["name"],
        "minute": row["snapshot_minute"],
        "formation": row["formation"],
        "possession_style": row["possession_style"],
        "press_intensity": row["press_intensity"],
        "defensive_line": row["defensive_line"],
        "confidence": float(row["confidence"]),
    }


def get_default_worldcup_catalog() -> WorldCupCatalog:
    return DefaultWorldCupCatalog(SupabaseWorldCupStore())
