import asyncio

import httpx
import pytest

from app.core.fan import (
    CheckinHistoryQuery,
    CreateCheckinCommand,
    DefaultFanService,
    FanStorageError,
    HotspotQuery,
    SupabaseFanStore,
)
from app.core.profile import AuthenticatedUser


USER = AuthenticatedUser(
    user_id="00000000-0000-0000-0000-000000000001",
    access_token="valid-token",
)


class FakeFanStore:
    def __init__(self) -> None:
        self.created_payload = None

    async def create_checkin(self, user: AuthenticatedUser, payload: dict):
        self.created_payload = (user, payload)
        return {
            "id": "11111111-1111-1111-1111-111111111111",
            "user_id": user.user_id,
            "city_id": payload["city_id"],
            "match_id": payload["match_id"],
            "venue_id": payload["venue_id"],
            "latitude": payload["latitude"],
            "longitude": payload["longitude"],
            "checked_in_at": "2026-05-26T12:00:00Z",
            "created_at": "2026-05-26T12:00:01Z",
        }

    async def fetch_checkins(self, user: AuthenticatedUser, page: int, page_size: int):
        return (
            [
                {
                    "id": "11111111-1111-1111-1111-111111111111",
                    "user_id": user.user_id,
                    "city_id": "874c6b46-de32-5014-8e54-da12587a7d7f",
                    "match_id": None,
                    "venue_id": None,
                    "latitude": 43.64,
                    "longitude": -79.41,
                    "checked_in_at": "2026-05-26T12:00:00Z",
                    "created_at": "2026-05-26T12:00:01Z",
                }
            ],
            1,
        )

    async def fetch_hotspots(self, query: HotspotQuery):
        return (
            [
                {
                    "id": "33333333-3333-3333-3333-333333333333",
                    "city_id": str(query.city_id),
                    "match_id": str(query.match_id) if query.match_id else None,
                    "area_label": "Queen West",
                    "center_lat": 43.64,
                    "center_lng": -79.41,
                    "center_precision": "neighborhood",
                    "score": 91,
                    "confidence": "0.86",
                    "supporter_count": 240,
                    "top_venue_ids": ["22222222-2222-2222-2222-222222222222"],
                    "ranking_factors": {"check_in_weight": 0.45},
                    "updated_at": "2026-05-26T12:10:00Z",
                }
            ],
            1,
        )


def test_create_checkin_writes_private_coordinates_but_returns_sanitized_contract() -> None:
    store = FakeFanStore()
    service = DefaultFanService(store)

    checkin = asyncio.run(
        service.create_checkin(
            USER,
            CreateCheckinCommand(
                city_id="874c6b46-de32-5014-8e54-da12587a7d7f",
                match_id=None,
                venue_id=None,
                latitude=43.64,
                longitude=-79.41,
                checked_in_at=None,
            ),
        )
    )

    assert store.created_payload[1]["latitude"] == 43.64
    assert store.created_payload[1]["longitude"] == -79.41
    assert "checked_in_at" not in store.created_payload[1]
    assert checkin == {
        "checkin_id": "11111111-1111-1111-1111-111111111111",
        "city_id": "874c6b46-de32-5014-8e54-da12587a7d7f",
        "match_id": None,
        "venue_id": None,
        "checked_in_at": "2026-05-26T12:00:00Z",
        "created_at": "2026-05-26T12:00:01Z",
    }


def test_checkin_history_returns_sanitized_paginated_user_contract() -> None:
    service = DefaultFanService(FakeFanStore())

    payload = asyncio.run(
        service.checkins_for_user(USER, CheckinHistoryQuery(page=1, page_size=10))
    )

    assert payload["checkins"][0]["checkin_id"] == "11111111-1111-1111-1111-111111111111"
    assert "latitude" not in payload["checkins"][0]
    assert "longitude" not in payload["checkins"][0]
    assert payload["pagination"]["total_items"] == 1


def test_hotspots_return_aggregate_contract() -> None:
    service = DefaultFanService(FakeFanStore())

    payload = asyncio.run(
        service.hotspots(
            HotspotQuery(
                city_id="874c6b46-de32-5014-8e54-da12587a7d7f",
                match_id="1e2fb5ce-9c73-5f6d-9c6b-df5d6d456101",
                page=1,
                page_size=10,
            )
        )
    )

    assert payload["hotspots"][0]["center"] == {
        "lat": 43.64,
        "lng": -79.41,
        "precision": "neighborhood",
    }
    assert payload["hotspots"][0]["confidence"] == 0.86
    assert payload["pagination"]["page_size"] == 10


def test_supabase_fan_store_maps_missing_table_to_storage_error() -> None:
    response = httpx.Response(404, request=httpx.Request("GET", "https://example.test"))

    with pytest.raises(FanStorageError) as exc_info:
        SupabaseFanStore()._raise_for_storage_error(response, "fan_checkins")

    assert exc_info.value.status_code == 503
    assert "fan_checkins" in str(exc_info.value)
