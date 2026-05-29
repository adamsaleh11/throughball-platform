from fastapi.testclient import TestClient

from app.core.city_guide import (
    CityGuideNotFoundError,
    EventGuideQuery,
    GuideQuery,
)
from app.main import app
from app.routes.city_guide import get_city_guide_service


client = TestClient(app)


TORONTO_ID = "874c6b46-de32-5014-8e54-da12587a7d7f"


class FakeCityGuideService:
    def __init__(self) -> None:
        self.venue_query = None
        self.event_query = None
        self.tourist_spot_query = None
        self.transport_hub_query = None

    async def city(self, city_id: str) -> dict:
        assert city_id == TORONTO_ID
        return {
            "city": {
                "city_id": TORONTO_ID,
                "name": "Toronto",
                "country_code": "CA",
                "stadium_name": "BMO Field",
                "timezone": "America/Toronto",
            }
        }

    async def venues(self, query: GuideQuery) -> dict:
        self.venue_query = query
        return {
            "venues": [
                {
                    "venue_id": "22222222-2222-4222-8222-222222222222",
                    "city_id": str(query.city_id),
                    "name": "BMO Field",
                    "venue_type": "stadium",
                    "area_label": "Exhibition Place",
                    "location": {
                        "lat": 43.6332,
                        "lng": -79.4186,
                        "precision": "exact_public_place",
                    },
                    "capacity_estimate": 45000,
                    "amenities": ["transit_access", "accessible"],
                    "tags": ["world-cup", "stadium"],
                    "source_name": "FIFA World Cup 26",
                    "source_url": "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026",
                    "data_origin": "official_site",
                    "last_verified_at": "2026-05-28",
                }
            ],
            "pagination": {
                "page": query.page,
                "page_size": query.page_size,
                "total_items": 1,
                "total_pages": 1,
                "has_next": False,
            },
        }

    async def events(self, query: EventGuideQuery) -> dict:
        self.event_query = query
        return {
            "events": [
                {
                    "event_id": "33333333-3333-4333-8333-333333333333",
                    "city_id": str(query.city_id),
                    "title": "FIFA World Cup 26 Toronto Host City",
                    "event_type": "world_cup_hosting",
                    "area_label": "Exhibition Place",
                    "starts_at": "2026-06-12T00:00:00Z",
                    "ends_at": None,
                    "tags": ["world-cup"],
                    "source_name": "FIFA World Cup 26",
                    "source_url": "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026",
                    "data_origin": "official_site",
                    "last_verified_at": "2026-05-28",
                }
            ],
            "pagination": page(query.page, query.page_size),
        }

    async def tourist_spots(self, query: GuideQuery) -> dict:
        self.tourist_spot_query = query
        return {
            "tourist_spots": [
                {
                    "spot_id": "44444444-4444-4444-8444-444444444444",
                    "city_id": str(query.city_id),
                    "name": "CN Tower",
                    "spot_type": "landmark",
                    "area_label": "Downtown",
                    "location": {
                        "lat": 43.6426,
                        "lng": -79.3871,
                        "precision": "exact_public_place",
                    },
                    "tags": ["landmark"],
                    "source_name": "Wikidata",
                    "source_url": "https://www.wikidata.org/wiki/Q183251",
                    "data_origin": "wikidata",
                    "last_verified_at": "2026-05-28",
                }
            ],
            "pagination": page(query.page, query.page_size),
        }

    async def transport_hubs(self, query: GuideQuery) -> dict:
        self.transport_hub_query = query
        return {
            "transport_hubs": [
                {
                    "hub_id": "55555555-5555-4555-8555-555555555555",
                    "city_id": str(query.city_id),
                    "name": "Toronto Pearson International Airport",
                    "hub_type": "airport",
                    "area_label": "Mississauga",
                    "location": {
                        "lat": 43.6777,
                        "lng": -79.6248,
                        "precision": "exact_public_place",
                    },
                    "tags": ["airport"],
                    "source_name": "Wikidata",
                    "source_url": "https://www.wikidata.org/wiki/Q32191",
                    "data_origin": "wikidata",
                    "last_verified_at": "2026-05-28",
                }
            ],
            "pagination": page(query.page, query.page_size),
        }


class MissingCityGuideService(FakeCityGuideService):
    async def city(self, city_id: str) -> dict:
        raise CityGuideNotFoundError(f"Host city '{city_id}' was not found.")


def test_get_city_returns_host_city_detail_contract() -> None:
    app.dependency_overrides[get_city_guide_service] = lambda: FakeCityGuideService()

    try:
        response = client.get(f"/cities/{TORONTO_ID}")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "city": {
            "city_id": TORONTO_ID,
            "name": "Toronto",
            "country_code": "CA",
            "stadium_name": "BMO Field",
            "timezone": "America/Toronto",
        },
        "meta": {
            "request_id": response.headers["x-request-id"],
            "trace_id": response.headers["x-trace-id"],
            "latency_ms": response.json()["meta"]["latency_ms"],
            "retries": 0,
            "degraded": False,
        },
    }
    assert isinstance(response.json()["meta"]["latency_ms"], int)


def test_get_city_returns_structured_not_found_error() -> None:
    app.dependency_overrides[get_city_guide_service] = lambda: MissingCityGuideService()

    try:
        response = client.get("/cities/00000000-0000-0000-0000-000000000000")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 404
    assert response.json()["error"] == {
        "code": "CITY_NOT_FOUND",
        "message": "Host city '00000000-0000-0000-0000-000000000000' was not found.",
    }


def test_list_city_venues_returns_sourced_filtered_contract() -> None:
    fake_service = FakeCityGuideService()
    app.dependency_overrides[get_city_guide_service] = lambda: fake_service

    try:
        response = client.get(
            f"/cities/{TORONTO_ID}/venues",
            params={
                "venue_type": "stadium",
                "amenity": "transit_access",
                "tag": "world-cup",
                "page": 1,
                "page_size": 10,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["venues"] == [
        {
            "venue_id": "22222222-2222-4222-8222-222222222222",
            "city_id": TORONTO_ID,
            "name": "BMO Field",
            "venue_type": "stadium",
            "area_label": "Exhibition Place",
            "location": {
                "lat": 43.6332,
                "lng": -79.4186,
                "precision": "exact_public_place",
            },
            "capacity_estimate": 45000,
            "amenities": ["transit_access", "accessible"],
            "tags": ["world-cup", "stadium"],
            "source_name": "FIFA World Cup 26",
            "source_url": "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026",
            "data_origin": "official_site",
            "last_verified_at": "2026-05-28",
        }
    ]
    assert response.json()["pagination"] == {
        "page": 1,
        "page_size": 10,
        "total_items": 1,
        "total_pages": 1,
        "has_next": False,
    }
    assert response.json()["meta"]["request_id"] == response.headers["x-request-id"]
    assert fake_service.venue_query.item_type == "stadium"
    assert fake_service.venue_query.amenity == "transit_access"
    assert fake_service.venue_query.tag == "world-cup"
    assert fake_service.venue_query.page_size == 10


def test_city_guide_category_routes_pass_deterministic_filters() -> None:
    fake_service = FakeCityGuideService()
    app.dependency_overrides[get_city_guide_service] = lambda: fake_service

    try:
        events = client.get(
            f"/cities/{TORONTO_ID}/events",
            params={
                "event_type": "world_cup_hosting",
                "starts_after": "2026-06-01T00:00:00Z",
                "starts_before": "2026-07-31T23:59:59Z",
                "tag": "world-cup",
            },
        )
        tourist_spots = client.get(
            f"/cities/{TORONTO_ID}/tourist-spots",
            params={"spot_type": "landmark", "area_label": "Downtown", "tag": "landmark"},
        )
        transport_hubs = client.get(
            f"/cities/{TORONTO_ID}/transport-hubs",
            params={"hub_type": "airport", "tag": "airport"},
        )
    finally:
        app.dependency_overrides.clear()

    assert events.status_code == 200
    assert events.json()["events"][0]["source_name"] == "FIFA World Cup 26"
    assert fake_service.event_query.event_type == "world_cup_hosting"
    assert fake_service.event_query.starts_after == "2026-06-01T00:00:00Z"
    assert fake_service.event_query.starts_before == "2026-07-31T23:59:59Z"
    assert fake_service.event_query.tag == "world-cup"

    assert tourist_spots.status_code == 200
    assert tourist_spots.json()["tourist_spots"][0]["name"] == "CN Tower"
    assert fake_service.tourist_spot_query.item_type == "landmark"
    assert fake_service.tourist_spot_query.area_label == "Downtown"
    assert fake_service.tourist_spot_query.tag == "landmark"

    assert transport_hubs.status_code == 200
    assert transport_hubs.json()["transport_hubs"][0]["hub_type"] == "airport"
    assert fake_service.transport_hub_query.item_type == "airport"
    assert fake_service.transport_hub_query.tag == "airport"


def page(page_number: int, page_size: int) -> dict:
    return {
        "page": page_number,
        "page_size": page_size,
        "total_items": 1,
        "total_pages": 1,
        "has_next": False,
    }
