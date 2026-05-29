import asyncio

from app.core.city_guide import (
    DefaultCityGuideService,
    EventGuideQuery,
    GuideQuery,
)
from app.core.worldcup import StorePage


TORONTO_ID = "874c6b46-de32-5014-8e54-da12587a7d7f"


class FakeCityGuideStore:
    async def fetch_city(self, city_id: str):
        return {
            "id": city_id,
            "name": "Toronto",
            "country_code": "CA",
            "stadium_name": "BMO Field",
            "timezone": "America/Toronto",
        }

    async def fetch_venues(self, query: GuideQuery):
        return StorePage(
            rows=[
                {
                    "id": "22222222-2222-4222-8222-222222222222",
                    "city_id": query.city_id,
                    "name": "BMO Field",
                    "venue_type": "stadium",
                    "area_label": "Exhibition Place",
                    "latitude": 43.6332,
                    "longitude": -79.4186,
                    "location_precision": "exact_public_place",
                    "capacity_estimate": 45000,
                    "amenities": ["transit_access"],
                    "tags": ["world-cup"],
                    "source_name": "FIFA World Cup 26",
                    "source_url": "https://www.fifa.com/en/tournaments/mens/worldcup/canadamexicousa2026",
                    "data_origin": "official_site",
                    "last_verified_at": "2026-05-28",
                }
            ],
            total_items=1,
        )

    async def fetch_events(self, query: EventGuideQuery):
        return StorePage(
            rows=[
                {
                    "id": "33333333-3333-4333-8333-333333333333",
                    "city_id": query.city_id,
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
            total_items=1,
        )

    async def fetch_tourist_spots(self, query: GuideQuery):
        return StorePage(
            rows=[
                {
                    "id": "44444444-4444-4444-8444-444444444444",
                    "city_id": query.city_id,
                    "name": "CN Tower",
                    "spot_type": "landmark",
                    "area_label": "Downtown",
                    "latitude": 43.6426,
                    "longitude": -79.3871,
                    "location_precision": "exact_public_place",
                    "tags": ["landmark"],
                    "source_name": "Wikidata",
                    "source_url": "https://www.wikidata.org/wiki/Q183251",
                    "data_origin": "wikidata",
                    "last_verified_at": "2026-05-28",
                }
            ],
            total_items=1,
        )

    async def fetch_transport_hubs(self, query: GuideQuery):
        return StorePage(
            rows=[
                {
                    "id": "55555555-5555-4555-8555-555555555555",
                    "city_id": query.city_id,
                    "name": "Toronto Pearson International Airport",
                    "hub_type": "airport",
                    "area_label": "Mississauga",
                    "latitude": 43.6777,
                    "longitude": -79.6248,
                    "location_precision": "exact_public_place",
                    "tags": ["airport"],
                    "source_name": "Wikidata",
                    "source_url": "https://www.wikidata.org/wiki/Q32191",
                    "data_origin": "wikidata",
                    "last_verified_at": "2026-05-28",
                }
            ],
            total_items=1,
        )


def test_city_guide_service_maps_sourced_category_rows() -> None:
    service = DefaultCityGuideService(FakeCityGuideStore())

    venues = asyncio.run(service.venues(GuideQuery(city_id=TORONTO_ID, page_size=10)))
    events = asyncio.run(service.events(EventGuideQuery(city_id=TORONTO_ID)))
    tourist_spots = asyncio.run(service.tourist_spots(GuideQuery(city_id=TORONTO_ID)))
    transport_hubs = asyncio.run(service.transport_hubs(GuideQuery(city_id=TORONTO_ID)))

    assert venues["venues"][0]["location"] == {
        "lat": 43.6332,
        "lng": -79.4186,
        "precision": "exact_public_place",
    }
    assert venues["venues"][0]["source_name"] == "FIFA World Cup 26"
    assert venues["pagination"]["page_size"] == 10

    assert events["events"][0]["event_id"] == "33333333-3333-4333-8333-333333333333"
    assert events["events"][0]["title"] == "FIFA World Cup 26 Toronto Host City"

    assert tourist_spots["tourist_spots"][0]["spot_id"] == "44444444-4444-4444-8444-444444444444"
    assert tourist_spots["tourist_spots"][0]["source_url"] == "https://www.wikidata.org/wiki/Q183251"

    assert transport_hubs["transport_hubs"][0]["hub_id"] == "55555555-5555-4555-8555-555555555555"
    assert transport_hubs["transport_hubs"][0]["hub_type"] == "airport"
