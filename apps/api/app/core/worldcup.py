from typing import Any, Optional

import httpx

from app.core.config import get_settings


class WorldCupStorageError(RuntimeError):
    def __init__(self, message: str, status_code: int = 503) -> None:
        super().__init__(message)
        self.status_code = status_code


class SupabaseWorldCupService:
    def __init__(self) -> None:
        settings = get_settings()
        self.supabase_url = settings.effective_supabase_url.rstrip("/")
        self.supabase_anon_key = settings.effective_supabase_anon_key

    async def list_cities(self) -> list[dict[str, Any]]:
        rows = await self._get_many(
            "host_cities",
            "select=id,name,country_code,stadium_name,timezone&order=name.asc",
        )
        return [
            {
                "city_id": row["id"],
                "name": row["name"],
                "country_code": row["country_code"],
                "stadium_name": row.get("stadium_name"),
                "timezone": row.get("timezone"),
            }
            for row in rows
        ]

    async def list_matches(
        self,
        city_id: Optional[str],
        page: int,
        page_size: int,
    ) -> dict[str, Any]:
        offset = (page - 1) * page_size
        query_parts = [
            "select=id,city_id,competition,stage,kickoff_time,status,tags,home_team:teams!matches_home_team_id_fkey(name),away_team:teams!matches_away_team_id_fkey(name)",
            "order=kickoff_time.asc",
            f"limit={page_size}",
            f"offset={offset}",
        ]
        count_query_parts = ["select=id"]
        if city_id:
            query_parts.append(f"city_id=eq.{city_id}")
            count_query_parts.append(f"city_id=eq.{city_id}")

        rows = await self._get_many("matches", "&".join(query_parts))
        count_rows = await self._get_many("matches", "&".join(count_query_parts))
        total_items = len(count_rows)
        total_pages = (total_items + page_size - 1) // page_size if total_items else 0

        return {
            "matches": [self._match_contract(row) for row in rows],
            "pagination": {
                "page": page,
                "page_size": page_size,
                "total_items": total_items,
                "total_pages": total_pages,
                "has_next": page < total_pages,
            },
        }

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
        if response.status_code == 404:
            raise WorldCupStorageError(
                f"Supabase table '{table}' is not available. Apply the World Cup migration."
            )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise WorldCupStorageError("Supabase World Cup storage request failed.") from exc

        data = response.json()
        return data if isinstance(data, list) else [data]

    def _match_contract(self, row: dict[str, Any]) -> dict[str, Any]:
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
