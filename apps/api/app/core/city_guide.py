from dataclasses import dataclass
from typing import Any, Optional, Protocol

import httpx

from app.core.config import get_settings
from app.core.worldcup import StorePage, build_pagination, city_contract


@dataclass(frozen=True)
class GuideQuery:
    city_id: str
    item_type: Optional[str] = None
    area_label: Optional[str] = None
    tag: Optional[str] = None
    amenity: Optional[str] = None
    page: int = 1
    page_size: int = 20


@dataclass(frozen=True)
class EventGuideQuery:
    city_id: str
    event_type: Optional[str] = None
    starts_after: Optional[str] = None
    starts_before: Optional[str] = None
    tag: Optional[str] = None
    page: int = 1
    page_size: int = 20


class CityGuideStorageError(RuntimeError):
    def __init__(self, message: str, status_code: int = 503) -> None:
        super().__init__(message)
        self.status_code = status_code


class CityGuideNotFoundError(RuntimeError):
    def __init__(self, message: str, code: str = "CITY_NOT_FOUND") -> None:
        super().__init__(message)
        self.code = code


class CityGuideService(Protocol):
    async def city(self, city_id: str) -> dict[str, Any]:
        ...

    async def venues(self, query: GuideQuery) -> dict[str, Any]:
        ...

    async def events(self, query: EventGuideQuery) -> dict[str, Any]:
        ...

    async def tourist_spots(self, query: GuideQuery) -> dict[str, Any]:
        ...

    async def transport_hubs(self, query: GuideQuery) -> dict[str, Any]:
        ...


class CityGuideStore(Protocol):
    async def fetch_city(self, city_id: str) -> Optional[dict[str, Any]]:
        ...

    async def fetch_venues(self, query: GuideQuery) -> StorePage:
        ...

    async def fetch_events(self, query: EventGuideQuery) -> StorePage:
        ...

    async def fetch_tourist_spots(self, query: GuideQuery) -> StorePage:
        ...

    async def fetch_transport_hubs(self, query: GuideQuery) -> StorePage:
        ...


class DefaultCityGuideService:
    def __init__(self, store: CityGuideStore) -> None:
        self._store = store

    async def city(self, city_id: str) -> dict[str, Any]:
        row = await self._store.fetch_city(city_id)
        if row is None:
            raise CityGuideNotFoundError(f"Host city '{city_id}' was not found.")
        return {"city": city_contract(row)}

    async def venues(self, query: GuideQuery) -> dict[str, Any]:
        await self._require_city(query.city_id)
        page = await self._store.fetch_venues(query)
        return {
            "venues": [venue_contract(row) for row in page.rows],
            "pagination": build_pagination(query.page, query.page_size, page.total_items),
        }

    async def events(self, query: EventGuideQuery) -> dict[str, Any]:
        await self._require_city(query.city_id)
        page = await self._store.fetch_events(query)
        return {
            "events": [event_contract(row) for row in page.rows],
            "pagination": build_pagination(query.page, query.page_size, page.total_items),
        }

    async def tourist_spots(self, query: GuideQuery) -> dict[str, Any]:
        await self._require_city(query.city_id)
        page = await self._store.fetch_tourist_spots(query)
        return {
            "tourist_spots": [tourist_spot_contract(row) for row in page.rows],
            "pagination": build_pagination(query.page, query.page_size, page.total_items),
        }

    async def transport_hubs(self, query: GuideQuery) -> dict[str, Any]:
        await self._require_city(query.city_id)
        page = await self._store.fetch_transport_hubs(query)
        return {
            "transport_hubs": [transport_hub_contract(row) for row in page.rows],
            "pagination": build_pagination(query.page, query.page_size, page.total_items),
        }

    async def _require_city(self, city_id: str) -> None:
        if await self._store.fetch_city(city_id) is None:
            raise CityGuideNotFoundError(f"Host city '{city_id}' was not found.")


class SupabaseCityGuideStore:
    def __init__(self) -> None:
        settings = get_settings()
        self.supabase_url = settings.effective_supabase_url.rstrip("/")
        self.supabase_anon_key = settings.effective_supabase_anon_key

    async def fetch_city(self, city_id: str) -> Optional[dict[str, Any]]:
        rows = await self._get_many(
            "host_cities",
            f"select=id,name,country_code,stadium_name,timezone&id=eq.{city_id}&limit=1",
        )
        return rows[0] if rows else None

    async def fetch_venues(self, query: GuideQuery) -> StorePage:
        query_parts = [
            "select=id,city_id,name,venue_type,area_label,latitude,longitude,location_precision,"
            "capacity_estimate,amenities,tags,source_name,source_url,data_origin,last_verified_at",
            f"city_id=eq.{query.city_id}",
            "order=name.asc",
        ]
        append_guide_filters(query_parts, query, "venue_type", include_amenity=True)
        return await self._get_page("venues", "&".join(query_parts), query.page, query.page_size)

    async def fetch_events(self, query: EventGuideQuery) -> StorePage:
        query_parts = [
            "select=id,city_id,title,event_type,area_label,starts_at,ends_at,tags,"
            "source_name,source_url,data_origin,last_verified_at",
            f"city_id=eq.{query.city_id}",
            "order=starts_at.asc",
        ]
        if query.event_type:
            query_parts.append(f"event_type=eq.{query.event_type}")
        if query.starts_after:
            query_parts.append(f"starts_at=gte.{query.starts_after}")
        if query.starts_before:
            query_parts.append(f"starts_at=lte.{query.starts_before}")
        if query.tag:
            query_parts.append(f"tags=cs.{{{query.tag}}}")
        return await self._get_page("city_events", "&".join(query_parts), query.page, query.page_size)

    async def fetch_tourist_spots(self, query: GuideQuery) -> StorePage:
        query_parts = [
            "select=id,city_id,name,spot_type,area_label,latitude,longitude,location_precision,"
            "tags,source_name,source_url,data_origin,last_verified_at",
            f"city_id=eq.{query.city_id}",
            "order=name.asc",
        ]
        append_guide_filters(query_parts, query, "spot_type")
        return await self._get_page("tourist_spots", "&".join(query_parts), query.page, query.page_size)

    async def fetch_transport_hubs(self, query: GuideQuery) -> StorePage:
        query_parts = [
            "select=id,city_id,name,hub_type,area_label,latitude,longitude,location_precision,"
            "tags,source_name,source_url,data_origin,last_verified_at",
            f"city_id=eq.{query.city_id}",
            "order=name.asc",
        ]
        append_guide_filters(query_parts, query, "hub_type")
        return await self._get_page("transport_hubs", "&".join(query_parts), query.page, query.page_size)

    async def _get_many(self, table: str, query: str) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{self.supabase_url}/rest/v1/{table}?{query}",
                headers=self._headers(),
            )
        self._raise_for_storage_error(response, table)
        data = response.json()
        return data if isinstance(data, list) else [data]

    async def _get_page(self, table: str, query: str, page: int, page_size: int) -> StorePage:
        offset = (page - 1) * page_size
        end = offset + page_size - 1
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

    def _headers(self) -> dict[str, str]:
        if not self.supabase_url or not self.supabase_anon_key:
            raise CityGuideStorageError("Supabase URL and anon key are required for city guide APIs.")
        return {
            "apikey": self.supabase_anon_key,
            "authorization": f"Bearer {self.supabase_anon_key}",
        }

    def _raise_for_storage_error(self, response: httpx.Response, table: str) -> None:
        if response.status_code == 404:
            raise CityGuideStorageError(
                f"Supabase table '{table}' is not available. Apply the city guide migration."
            )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise CityGuideStorageError("Supabase city guide storage request failed.") from exc


def empty_page(key: str, page: int, page_size: int) -> dict[str, Any]:
    return {
        key: [],
        "pagination": build_pagination(page, page_size, 0),
    }


def append_guide_filters(
    query_parts: list[str],
    query: GuideQuery,
    type_column: str,
    include_amenity: bool = False,
) -> None:
    if query.item_type:
        query_parts.append(f"{type_column}=eq.{query.item_type}")
    if query.area_label:
        query_parts.append(f"area_label=eq.{query.area_label}")
    if query.tag:
        query_parts.append(f"tags=cs.{{{query.tag}}}")
    if include_amenity and query.amenity:
        query_parts.append(f"amenities=cs.{{{query.amenity}}}")


def parse_content_range_total(response: httpx.Response) -> int:
    content_range = response.headers.get("content-range", "")
    if "/" not in content_range:
        return 0
    total = content_range.rsplit("/", 1)[-1]
    return 0 if total == "*" else int(total)


def location_contract(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "lat": row.get("latitude"),
        "lng": row.get("longitude"),
        "precision": row.get("location_precision"),
    }


def source_fields(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_name": row["source_name"],
        "source_url": row["source_url"],
        "data_origin": row["data_origin"],
        "last_verified_at": row["last_verified_at"],
    }


def venue_contract(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "venue_id": row["id"],
        "city_id": row["city_id"],
        "name": row["name"],
        "venue_type": row["venue_type"],
        "area_label": row.get("area_label"),
        "location": location_contract(row),
        "capacity_estimate": row.get("capacity_estimate"),
        "amenities": row.get("amenities", []),
        "tags": row.get("tags", []),
        **source_fields(row),
    }


def event_contract(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "event_id": row["id"],
        "city_id": row["city_id"],
        "title": row["title"],
        "event_type": row["event_type"],
        "area_label": row.get("area_label"),
        "starts_at": row.get("starts_at"),
        "ends_at": row.get("ends_at"),
        "tags": row.get("tags", []),
        **source_fields(row),
    }


def tourist_spot_contract(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "spot_id": row["id"],
        "city_id": row["city_id"],
        "name": row["name"],
        "spot_type": row["spot_type"],
        "area_label": row.get("area_label"),
        "location": location_contract(row),
        "tags": row.get("tags", []),
        **source_fields(row),
    }


def transport_hub_contract(row: dict[str, Any]) -> dict[str, Any]:
    return {
        "hub_id": row["id"],
        "city_id": row["city_id"],
        "name": row["name"],
        "hub_type": row["hub_type"],
        "area_label": row.get("area_label"),
        "location": location_contract(row),
        "tags": row.get("tags", []),
        **source_fields(row),
    }


def get_default_city_guide_service() -> CityGuideService:
    return DefaultCityGuideService(SupabaseCityGuideStore())
