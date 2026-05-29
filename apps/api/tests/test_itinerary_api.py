from fastapi.testclient import TestClient

from app.core.profile import AuthenticatedUser
from app.main import app
from app.routes.itineraries import get_current_user


client = TestClient(app)


USER = AuthenticatedUser(
    user_id="00000000-0000-0000-0000-000000000001",
    access_token="valid-token",
)


async def fake_current_user() -> AuthenticatedUser:
    return USER


SAVE_PAYLOAD = {
    "input": {
        "city_id": "874c6b46-de32-5014-8e54-da12587a7d7f",
        "match_id": None,
        "date": "2026-06-12",
        "party_size": 2,
        "interests": ["fan_zone", "food"],
        "pace": "balanced",
    },
    "itinerary": {
        "title": "Match Day in Toronto",
        "summary": "A compact match-day plan.",
        "items": [
            {
                "position": 1,
                "item_type": "venue",
                "source_table": "venues",
                "source_id": "22222222-2222-4222-8222-222222222222",
                "title": "BMO Field",
                "description": "Arrive early around Exhibition Place.",
                "starts_at": "2026-06-12T16:00:00Z",
                "ends_at": "2026-06-12T18:00:00Z",
                "area_label": "Exhibition Place",
                "route_context": {
                    "from_previous_label": None,
                    "approx_minutes": 0,
                    "mode": "unknown",
                },
            }
        ],
    },
}


class FakeItineraryService:
    def __init__(self, *, reused: bool = False) -> None:
        self.reused = reused
        self.saved = None

    async def save_itinerary(self, user, command) -> dict:
        self.saved = (user, command)
        return {
            "itinerary": {
                "itinerary_id": "11111111-1111-4111-8111-111111111111",
                "city_id": str(command.input.city_id),
                "match_id": None,
                "input_hash": "sha256:abc123",
                "input": {
                    "city_id": str(command.input.city_id),
                    "match_id": None,
                    "date": command.input.date,
                    "party_size": command.input.party_size,
                    "interests": command.input.interests,
                    "pace": command.input.pace,
                },
                "title": command.title,
                "summary": command.summary,
                "status": "saved",
                "items": [
                    {
                        "item_id": "33333333-3333-4333-8333-333333333333",
                        "position": 1,
                        "item_type": "venue",
                        "source_table": "venues",
                        "source_id": "22222222-2222-4222-8222-222222222222",
                        "title": "BMO Field",
                        "description": "Arrive early around Exhibition Place.",
                        "starts_at": "2026-06-12T16:00:00Z",
                        "ends_at": "2026-06-12T18:00:00Z",
                        "area_label": "Exhibition Place",
                        "route_context": {
                            "from_previous_label": None,
                            "approx_minutes": 0,
                            "mode": "unknown",
                        },
                    }
                ],
                "created_at": "2026-05-28T18:00:00Z",
                "updated_at": "2026-05-28T18:00:00Z",
            },
            "reused": self.reused,
        }

    async def itineraries_for_user(self, user, query) -> dict:
        self.history_query = (user, query)
        saved = await self.save_itinerary(user, _command_from_payload(SAVE_PAYLOAD))
        return {
            "itineraries": [saved["itinerary"]],
            "pagination": {
                "page": query.page,
                "page_size": query.page_size,
                "total_items": 1,
                "total_pages": 1,
                "has_next": False,
            },
        }


def _command_from_payload(payload):
    from app.routes.itineraries import SaveItineraryRequest

    return SaveItineraryRequest.model_validate(payload).to_command()


def test_generate_itinerary_requires_bearer_token() -> None:
    response = client.post("/itineraries/generate", json={})

    assert response.status_code == 401
    assert response.json()["error"] == {
        "code": "UNAUTHORIZED",
        "message": "Missing bearer token.",
    }


def test_save_itinerary_requires_bearer_token() -> None:
    response = client.post("/itineraries/save", json=SAVE_PAYLOAD)

    assert response.status_code == 401
    assert response.json()["error"] == {
        "code": "UNAUTHORIZED",
        "message": "Missing bearer token.",
    }


def test_my_itineraries_requires_bearer_token() -> None:
    response = client.get("/itineraries/me")

    assert response.status_code == 401
    assert response.json()["error"] == {
        "code": "UNAUTHORIZED",
        "message": "Missing bearer token.",
    }


def test_authenticated_generate_itinerary_returns_phase_06_stub() -> None:
    app.dependency_overrides[get_current_user] = fake_current_user

    try:
        response = client.post(
            "/itineraries/generate",
            headers={"Authorization": "Bearer valid-token"},
            json={"city_id": "874c6b46-de32-5014-8e54-da12587a7d7f"},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 501
    body = response.json()
    assert body["error"] == {
        "code": "ITINERARY_GENERATION_NOT_IMPLEMENTED",
        "message": "Itinerary generation is not implemented until Phase 06.",
        "details": {
            "phase": "Phase 06",
            "contract": "POST /itineraries/save accepts generated itinerary payloads for persistence.",
        },
    }
    assert body["meta"]["request_id"] == response.headers["x-request-id"]
    assert isinstance(body["meta"]["latency_ms"], int)


def test_authenticated_user_can_save_itinerary() -> None:
    from app.routes.itineraries import get_itinerary_service

    fake_service = FakeItineraryService()
    app.dependency_overrides[get_current_user] = fake_current_user
    app.dependency_overrides[get_itinerary_service] = lambda: fake_service

    try:
        response = client.post(
            "/itineraries/save",
            headers={"Authorization": "Bearer valid-token"},
            json=SAVE_PAYLOAD,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 201
    body = response.json()
    assert body["reused"] is False
    assert body["itinerary"]["title"] == "Match Day in Toronto"
    assert body["itinerary"]["items"][0]["position"] == 1
    assert body["meta"]["request_id"] == response.headers["x-request-id"]
    assert fake_service.saved[0] == USER
    assert fake_service.saved[1].title == "Match Day in Toronto"


def test_duplicate_save_returns_existing_itinerary() -> None:
    from app.routes.itineraries import get_itinerary_service

    fake_service = FakeItineraryService(reused=True)
    app.dependency_overrides[get_current_user] = fake_current_user
    app.dependency_overrides[get_itinerary_service] = lambda: fake_service

    try:
        response = client.post(
            "/itineraries/save",
            headers={"Authorization": "Bearer valid-token"},
            json=SAVE_PAYLOAD,
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["reused"] is True
    assert response.json()["itinerary"]["input_hash"] == "sha256:abc123"


def test_authenticated_user_can_fetch_saved_itineraries() -> None:
    from app.routes.itineraries import get_itinerary_service

    fake_service = FakeItineraryService()
    app.dependency_overrides[get_current_user] = fake_current_user
    app.dependency_overrides[get_itinerary_service] = lambda: fake_service

    try:
        response = client.get(
            "/itineraries/me",
            headers={"Authorization": "Bearer valid-token"},
            params={"page": 1, "page_size": 10},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    body = response.json()
    assert body["itineraries"][0]["title"] == "Match Day in Toronto"
    assert body["itineraries"][0]["items"][0]["title"] == "BMO Field"
    assert body["pagination"] == {
        "page": 1,
        "page_size": 10,
        "total_items": 1,
        "total_pages": 1,
        "has_next": False,
    }
    assert body["meta"]["request_id"] == response.headers["x-request-id"]
    assert fake_service.history_query[0] == USER
