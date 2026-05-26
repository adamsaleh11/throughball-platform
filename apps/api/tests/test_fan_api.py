from fastapi.testclient import TestClient

from app.core.profile import AuthenticatedUser
from app.main import app
from app.routes.fan import get_current_user, get_fan_service


client = TestClient(app)


USER = AuthenticatedUser(
    user_id="00000000-0000-0000-0000-000000000001",
    access_token="valid-token",
)


class FakeFanService:
    def __init__(self) -> None:
        self.created = None

    async def create_checkin(self, user, command) -> dict:
        self.created = (user, command)
        return {
            "checkin_id": "11111111-1111-1111-1111-111111111111",
            "city_id": str(command.city_id),
            "match_id": str(command.match_id) if command.match_id else None,
            "venue_id": str(command.venue_id) if command.venue_id else None,
            "checked_in_at": "2026-05-26T12:00:00Z",
            "created_at": "2026-05-26T12:00:01Z",
        }

    async def checkins_for_user(self, user, query) -> dict:
        self.history_query = (user, query)
        return {
            "checkins": [
                {
                    "checkin_id": "11111111-1111-1111-1111-111111111111",
                    "city_id": "874c6b46-de32-5014-8e54-da12587a7d7f",
                    "match_id": None,
                    "venue_id": None,
                    "checked_in_at": "2026-05-26T12:00:00Z",
                    "created_at": "2026-05-26T12:00:01Z",
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

    async def hotspots(self, query) -> dict:
        self.hotspot_query = query
        return {
            "hotspots": [
                {
                    "hotspot_id": "33333333-3333-3333-3333-333333333333",
                    "city_id": str(query.city_id),
                    "match_id": str(query.match_id) if query.match_id else None,
                    "area_label": "Queen West",
                    "center": {
                        "lat": 43.64,
                        "lng": -79.41,
                        "precision": "neighborhood",
                    },
                    "score": 91,
                    "confidence": 0.86,
                    "supporter_count": 240,
                    "top_venue_ids": ["22222222-2222-2222-2222-222222222222"],
                    "ranking_factors": {
                        "check_in_weight": 0.45,
                        "rsvp_weight": 0.25,
                        "signal_weight": 0.2,
                        "recency_weight": 0.1,
                    },
                    "updated_at": "2026-05-26T12:10:00Z",
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


async def fake_current_user() -> AuthenticatedUser:
    return USER


def test_create_checkin_requires_bearer_token() -> None:
    response = client.post(
        "/fan/checkins",
        json={
            "city_id": "874c6b46-de32-5014-8e54-da12587a7d7f",
            "latitude": 43.64,
            "longitude": -79.41,
        },
    )

    assert response.status_code == 401
    assert response.json()["error"] == {
        "code": "UNAUTHORIZED",
        "message": "Missing bearer token.",
    }


def test_authenticated_user_can_create_private_checkin() -> None:
    fake_service = FakeFanService()
    app.dependency_overrides[get_current_user] = fake_current_user
    app.dependency_overrides[get_fan_service] = lambda: fake_service

    try:
        response = client.post(
            "/fan/checkins",
            headers={"Authorization": "Bearer valid-token"},
            json={
                "city_id": "874c6b46-de32-5014-8e54-da12587a7d7f",
                "match_id": "1e2fb5ce-9c73-5f6d-9c6b-df5d6d456101",
                "venue_id": "22222222-2222-2222-2222-222222222222",
                "latitude": 43.64,
                "longitude": -79.41,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    body = response.json()
    assert body["checkin"] == {
        "checkin_id": "11111111-1111-1111-1111-111111111111",
        "city_id": "874c6b46-de32-5014-8e54-da12587a7d7f",
        "match_id": "1e2fb5ce-9c73-5f6d-9c6b-df5d6d456101",
        "venue_id": "22222222-2222-2222-2222-222222222222",
        "checked_in_at": "2026-05-26T12:00:00Z",
        "created_at": "2026-05-26T12:00:01Z",
    }
    assert "latitude" not in body["checkin"]
    assert "longitude" not in body["checkin"]
    assert fake_service.created[0] == USER
    assert fake_service.created[1].latitude == 43.64


def test_authenticated_user_can_fetch_own_checkins() -> None:
    fake_service = FakeFanService()
    app.dependency_overrides[get_current_user] = fake_current_user
    app.dependency_overrides[get_fan_service] = lambda: fake_service

    try:
        response = client.get(
            "/fan/checkins/me",
            headers={"Authorization": "Bearer valid-token"},
            params={"page": 1, "page_size": 10},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["checkins"] == [
        {
            "checkin_id": "11111111-1111-1111-1111-111111111111",
            "city_id": "874c6b46-de32-5014-8e54-da12587a7d7f",
            "match_id": None,
            "venue_id": None,
            "checked_in_at": "2026-05-26T12:00:00Z",
            "created_at": "2026-05-26T12:00:01Z",
        }
    ]
    assert body["pagination"] == {
        "page": 1,
        "page_size": 10,
        "total_items": 1,
        "total_pages": 1,
        "has_next": False,
    }
    assert "latitude" not in body["checkins"][0]
    assert "longitude" not in body["checkins"][0]
    assert fake_service.history_query[0] == USER


def test_public_hotspots_return_aggregate_contract_without_private_fields() -> None:
    fake_service = FakeFanService()
    app.dependency_overrides[get_fan_service] = lambda: fake_service

    try:
        response = client.get(
            "/cities/874c6b46-de32-5014-8e54-da12587a7d7f/hotspots",
            params={
                "match_id": "1e2fb5ce-9c73-5f6d-9c6b-df5d6d456101",
                "page": 1,
                "page_size": 10,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["hotspots"] == [
        {
            "hotspot_id": "33333333-3333-3333-3333-333333333333",
            "city_id": "874c6b46-de32-5014-8e54-da12587a7d7f",
            "match_id": "1e2fb5ce-9c73-5f6d-9c6b-df5d6d456101",
            "area_label": "Queen West",
            "center": {
                "lat": 43.64,
                "lng": -79.41,
                "precision": "neighborhood",
            },
            "score": 91,
            "confidence": 0.86,
            "supporter_count": 240,
            "top_venue_ids": ["22222222-2222-2222-2222-222222222222"],
            "ranking_factors": {
                "check_in_weight": 0.45,
                "rsvp_weight": 0.25,
                "signal_weight": 0.2,
                "recency_weight": 0.1,
            },
            "updated_at": "2026-05-26T12:10:00Z",
        }
    ]
    payload_text = response.text
    assert "user_id" not in payload_text
    assert "checkin_id" not in payload_text
    assert "latitude" not in payload_text
    assert "longitude" not in payload_text
    assert fake_service.hotspot_query.page_size == 10
