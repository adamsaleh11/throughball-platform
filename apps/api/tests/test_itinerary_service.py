import asyncio
from uuid import UUID

import httpx
import pytest

from app.core.itineraries import (
    DefaultItineraryService,
    ItineraryInputCommand,
    ItineraryItemCommand,
    ItineraryStorageError,
    SaveItineraryCommand,
    SupabaseItineraryStore,
)
from app.core.profile import AuthenticatedUser


USER = AuthenticatedUser(
    user_id="00000000-0000-0000-0000-000000000001",
    access_token="valid-token",
)


class FakeItineraryStore:
    def __init__(self) -> None:
        self.existing = None
        self.created = None

    async def find_by_input_hash(self, user, input_hash: str):
        self.lookup = (user, input_hash)
        return self.existing

    async def create_itinerary(self, user, payload, items):
        self.created = (user, payload, items)
        return {
            "id": "11111111-1111-4111-8111-111111111111",
            "city_id": payload["city_id"],
            "match_id": payload["match_id"],
            "input_hash": payload["input_hash"],
            "input_payload": payload["input_payload"],
            "title": payload["title"],
            "summary": payload["summary"],
            "status": "saved",
            "created_at": "2026-05-28T18:00:00Z",
            "updated_at": "2026-05-28T18:00:00Z",
            "items": [
                {
                    "id": "33333333-3333-4333-8333-333333333333",
                    **items[0],
                    "created_at": "2026-05-28T18:00:01Z",
                }
            ],
        }


def command(interests=None) -> SaveItineraryCommand:
    return SaveItineraryCommand(
        input=ItineraryInputCommand(
            city_id=UUID("874c6b46-de32-5014-8e54-da12587a7d7f"),
            match_id=None,
            date="2026-06-12",
            party_size=2,
            interests=interests or ["food", "fan_zone"],
            pace="balanced",
        ),
        title="Match Day in Toronto",
        summary="A compact match-day plan.",
        items=[
            ItineraryItemCommand(
                position=1,
                item_type="venue",
                source_table="venues",
                source_id=UUID("22222222-2222-4222-8222-222222222222"),
                title="BMO Field",
                description="Arrive early around Exhibition Place.",
                starts_at="2026-06-12T16:00:00Z",
                ends_at="2026-06-12T18:00:00Z",
                area_label="Exhibition Place",
                route_context={"mode": "unknown", "approx_minutes": 0},
            )
        ],
    )


def test_save_itinerary_creates_persisted_aggregate_with_input_hash() -> None:
    store = FakeItineraryStore()
    service = DefaultItineraryService(store)

    result = asyncio.run(service.save_itinerary(USER, command()))

    assert result["reused"] is False
    assert result["itinerary"]["itinerary_id"] == "11111111-1111-4111-8111-111111111111"
    assert result["itinerary"]["input_hash"].startswith("sha256:")
    assert result["itinerary"]["items"][0]["position"] == 1
    assert store.created[0] == USER
    assert store.created[1]["user_id"] == USER.user_id
    assert store.created[2][0]["title"] == "BMO Field"


def test_save_itinerary_reuses_existing_for_same_normalized_input() -> None:
    store = FakeItineraryStore()
    store.existing = {
        "id": "99999999-9999-4999-8999-999999999999",
        "city_id": "874c6b46-de32-5014-8e54-da12587a7d7f",
        "match_id": None,
        "input_hash": "will-be-overwritten",
        "input_payload": {},
        "title": "Existing Toronto Plan",
        "summary": None,
        "status": "saved",
        "created_at": "2026-05-28T17:00:00Z",
        "updated_at": "2026-05-28T17:00:00Z",
        "items": [],
    }
    service = DefaultItineraryService(store)

    result = asyncio.run(service.save_itinerary(USER, command(interests=[" fan_zone", "food", "food"])))

    assert result["reused"] is True
    assert result["itinerary"]["itinerary_id"] == "99999999-9999-4999-8999-999999999999"
    assert store.created is None
    assert store.lookup[1].startswith("sha256:")


def test_input_hash_is_stable_for_interest_order_and_whitespace() -> None:
    first_store = FakeItineraryStore()
    second_store = FakeItineraryStore()

    asyncio.run(DefaultItineraryService(first_store).save_itinerary(USER, command(interests=["food", "fan_zone"])))
    asyncio.run(
        DefaultItineraryService(second_store).save_itinerary(
            USER,
            command(interests=[" fan_zone", "food", "food"]),
        )
    )

    assert first_store.created[1]["input_hash"] == second_store.created[1]["input_hash"]
    assert second_store.created[1]["input_payload"]["interests"] == ["fan_zone", "food"]


def test_supabase_itinerary_store_maps_missing_table_to_storage_error() -> None:
    response = httpx.Response(404, request=httpx.Request("GET", "https://example.test"))

    with pytest.raises(ItineraryStorageError) as exc_info:
        SupabaseItineraryStore()._raise_for_storage_error(response, "itineraries")

    assert exc_info.value.status_code == 503
    assert "itineraries" in str(exc_info.value)
