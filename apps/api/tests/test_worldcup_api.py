from fastapi.testclient import TestClient

from app.main import app
from app.routes.worldcup import get_worldcup_service


client = TestClient(app)


class FakeWorldCupService:
    async def list_cities(self) -> list[dict]:
        return [
            {
                "city_id": "874c6b46-de32-5014-8e54-da12587a7d7f",
                "name": "Toronto",
                "country_code": "CA",
                "stadium_name": "BMO Field",
                "timezone": "America/Toronto",
            },
            {
                "city_id": "474d6beb-b593-5c05-92c4-a06aa502dbed",
                "name": "Vancouver",
                "country_code": "CA",
                "stadium_name": "BC Place",
                "timezone": "America/Vancouver",
            },
        ]

    async def list_matches(self, city_id: str | None, page: int, page_size: int) -> dict:
        assert city_id == "874c6b46-de32-5014-8e54-da12587a7d7f"
        assert page == 1
        assert page_size == 20
        return {
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
                "page": 1,
                "page_size": 20,
                "total_items": 1,
                "total_pages": 1,
                "has_next": False,
            },
        }


def test_list_cities_returns_seeded_host_city_contract() -> None:
    app.dependency_overrides[get_worldcup_service] = lambda: FakeWorldCupService()

    try:
        response = client.get("/cities")
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "cities": [
            {
                "city_id": "874c6b46-de32-5014-8e54-da12587a7d7f",
                "name": "Toronto",
                "country_code": "CA",
                "stadium_name": "BMO Field",
                "timezone": "America/Toronto",
            },
            {
                "city_id": "474d6beb-b593-5c05-92c4-a06aa502dbed",
                "name": "Vancouver",
                "country_code": "CA",
                "stadium_name": "BC Place",
                "timezone": "America/Vancouver",
            },
        ],
        "meta": {
            "request_id": response.headers["x-request-id"],
            "trace_id": response.headers["x-trace-id"],
            "latency_ms": response.json()["meta"]["latency_ms"],
            "retries": 0,
            "degraded": False,
        },
    }
    assert isinstance(response.json()["meta"]["latency_ms"], int)


def test_list_matches_filters_by_city_and_returns_contract() -> None:
    app.dependency_overrides[get_worldcup_service] = lambda: FakeWorldCupService()

    try:
        response = client.get(
            "/matches",
            params={"city_id": "874c6b46-de32-5014-8e54-da12587a7d7f"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
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
            "page": 1,
            "page_size": 20,
            "total_items": 1,
            "total_pages": 1,
            "has_next": False,
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
