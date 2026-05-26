import asyncio

import httpx
import pytest

from app.core.worldcup import (
    DefaultWorldCupCatalog,
    MatchCatalogQuery,
    StorePage,
    SupabaseWorldCupStore,
    WorldCupStorageError,
    build_pagination,
)


class FakeWorldCupStore:
    async def fetch_host_cities(self):
        return [
            {
                "id": "874c6b46-de32-5014-8e54-da12587a7d7f",
                "name": "Toronto",
                "country_code": "CA",
                "stadium_name": "BMO Field",
                "timezone": "America/Toronto",
            }
        ]

    async def fetch_matches(self, query: MatchCatalogQuery):
        assert query == MatchCatalogQuery(
            city_id="874c6b46-de32-5014-8e54-da12587a7d7f",
            page=2,
            page_size=1,
        )
        return StorePage(
            rows=[
                {
                    "id": "1e2fb5ce-9c73-5f6d-9c6b-df5d6d456101",
                    "city_id": "874c6b46-de32-5014-8e54-da12587a7d7f",
                    "home_team": {"name": "Canada"},
                    "away_team": {"name": "Mexico"},
                    "competition": "FIFA World Cup 2026",
                    "kickoff_time": "2026-06-12T23:00:00Z",
                    "status": "scheduled",
                    "tags": ["world-cup", "group-stage", "toronto"],
                }
            ],
            total_items=3,
        )


def test_catalog_maps_city_rows_to_contract() -> None:
    catalog = DefaultWorldCupCatalog(FakeWorldCupStore())

    cities = asyncio.run(catalog.cities())

    assert cities == [
        {
            "city_id": "874c6b46-de32-5014-8e54-da12587a7d7f",
            "name": "Toronto",
            "country_code": "CA",
            "stadium_name": "BMO Field",
            "timezone": "America/Toronto",
        }
    ]


def test_catalog_maps_match_rows_and_pagination() -> None:
    catalog = DefaultWorldCupCatalog(FakeWorldCupStore())

    payload = asyncio.run(
        catalog.matches(
            MatchCatalogQuery(
                city_id="874c6b46-de32-5014-8e54-da12587a7d7f",
                page=2,
                page_size=1,
            )
        )
    )

    assert payload == {
        "matches": [
            {
                "match_id": "1e2fb5ce-9c73-5f6d-9c6b-df5d6d456101",
                "city_id": "874c6b46-de32-5014-8e54-da12587a7d7f",
                "home_team": "Canada",
                "away_team": "Mexico",
                "competition": "FIFA World Cup 2026",
                "starts_at": "2026-06-12T23:00:00Z",
                "status": "scheduled",
                "tags": ["world-cup", "group-stage", "toronto"],
            }
        ],
        "pagination": {
            "page": 2,
            "page_size": 1,
            "total_items": 3,
            "total_pages": 3,
            "has_next": True,
        },
    }


def test_build_pagination_handles_empty_results() -> None:
    assert build_pagination(page=1, page_size=20, total_items=0) == {
        "page": 1,
        "page_size": 20,
        "total_items": 0,
        "total_pages": 0,
        "has_next": False,
    }


def test_supabase_store_maps_missing_table_to_storage_error() -> None:
    response = httpx.Response(404, request=httpx.Request("GET", "https://example.test"))

    with pytest.raises(WorldCupStorageError) as exc_info:
        SupabaseWorldCupStore()._raise_for_storage_error(response, "matches")

    assert exc_info.value.status_code == 503
    assert "matches" in str(exc_info.value)
