from fastapi.testclient import TestClient

from app.main import app
from app.routes.profile import get_current_user, get_profile_service


client = TestClient(app)


class FakeProfileService:
    def __init__(self) -> None:
        self.updated_payload = None

    async def get_profile(self, user_id: str, access_token: str) -> dict:
        return {
            "profile": {
                "id": user_id,
                "display_name": "Alex",
                "avatar_url": None,
                "profile_completed": True,
                "created_at": "2026-05-25T12:00:00Z",
                "updated_at": "2026-05-25T12:00:00Z",
            },
            "preferences": {
                "user_id": user_id,
                "home_city_id": "11111111-1111-1111-1111-111111111111",
                "preferred_match_tags": ["rivalry"],
                "favorite_team_ids": ["22222222-2222-2222-2222-222222222222"],
                "created_at": "2026-05-25T12:00:00Z",
                "updated_at": "2026-05-25T12:00:00Z",
            },
        }

    async def update_profile(self, user_id: str, access_token: str, payload: dict) -> dict:
        self.updated_payload = {
            "user_id": user_id,
            "access_token": access_token,
            "payload": payload,
        }
        profile_completed = bool(
            payload.get("display_name")
            and (payload.get("home_city_id") or payload.get("favorite_team_ids"))
        )
        return {
            "profile": {
                "id": user_id,
                "display_name": payload["display_name"],
                "avatar_url": payload.get("avatar_url"),
                "profile_completed": profile_completed,
                "created_at": "2026-05-25T12:00:00Z",
                "updated_at": "2026-05-25T12:05:00Z",
            },
            "preferences": {
                "user_id": user_id,
                "home_city_id": payload.get("home_city_id"),
                "preferred_match_tags": payload.get("preferred_match_tags", []),
                "favorite_team_ids": payload.get("favorite_team_ids", []),
                "created_at": "2026-05-25T12:00:00Z",
                "updated_at": "2026-05-25T12:05:00Z",
            },
        }


async def fake_current_user() -> dict:
    return {
        "user_id": "00000000-0000-0000-0000-000000000001",
        "access_token": "valid-token",
    }


def test_get_profile_requires_bearer_token() -> None:
    response = client.get("/me/profile")

    assert response.status_code == 401
    assert response.json() == {
        "error": {
            "code": "UNAUTHORIZED",
            "message": "Missing bearer token.",
        },
        "meta": {
            "request_id": response.headers["x-request-id"],
            "trace_id": response.headers["x-trace-id"],
            "degraded": False,
        },
    }


def test_get_profile_rejects_empty_bearer_token() -> None:
    response = client.get("/me/profile", headers={"Authorization": "Bearer "})

    assert response.status_code == 401
    assert response.json()["error"] == {
        "code": "UNAUTHORIZED",
        "message": "Invalid bearer token.",
    }
    assert response.json()["meta"] == {
        "request_id": response.headers["x-request-id"],
        "trace_id": response.headers["x-trace-id"],
        "degraded": False,
    }


def test_get_profile_returns_nested_profile_for_authenticated_user() -> None:
    app.dependency_overrides[get_current_user] = fake_current_user
    app.dependency_overrides[get_profile_service] = lambda: FakeProfileService()

    try:
        response = client.get("/me/profile", headers={"Authorization": "Bearer valid-token"})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json() == {
        "profile": {
            "id": "00000000-0000-0000-0000-000000000001",
            "display_name": "Alex",
            "avatar_url": None,
            "profile_completed": True,
            "created_at": "2026-05-25T12:00:00Z",
            "updated_at": "2026-05-25T12:00:00Z",
        },
        "preferences": {
            "user_id": "00000000-0000-0000-0000-000000000001",
            "home_city_id": "11111111-1111-1111-1111-111111111111",
            "preferred_match_tags": ["rivalry"],
            "favorite_team_ids": ["22222222-2222-2222-2222-222222222222"],
            "created_at": "2026-05-25T12:00:00Z",
            "updated_at": "2026-05-25T12:00:00Z",
        },
        "meta": {
            "request_id": response.headers["x-request-id"],
            "trace_id": response.headers["x-trace-id"],
            "degraded": False,
        },
    }


def test_update_profile_rejects_too_many_favorite_teams() -> None:
    app.dependency_overrides[get_current_user] = fake_current_user
    app.dependency_overrides[get_profile_service] = lambda: FakeProfileService()

    try:
        response = client.put(
            "/me/profile",
            headers={"Authorization": "Bearer valid-token"},
            json={
                "display_name": "Alex",
                "favorite_team_ids": [
                    "22222222-2222-2222-2222-222222222222",
                    "22222222-2222-2222-2222-222222222223",
                    "22222222-2222-2222-2222-222222222224",
                    "22222222-2222-2222-2222-222222222225",
                    "22222222-2222-2222-2222-222222222226",
                    "22222222-2222-2222-2222-222222222227",
                    "22222222-2222-2222-2222-222222222228",
                    "22222222-2222-2222-2222-222222222229",
                    "22222222-2222-2222-2222-222222222230",
                    "22222222-2222-2222-2222-222222222231",
                    "22222222-2222-2222-2222-222222222232",
                ],
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 422


def test_update_profile_returns_computed_completion_state() -> None:
    fake_service = FakeProfileService()
    app.dependency_overrides[get_current_user] = fake_current_user
    app.dependency_overrides[get_profile_service] = lambda: fake_service

    try:
        response = client.put(
            "/me/profile",
            headers={"Authorization": "Bearer valid-token"},
            json={
                "display_name": "Alex",
                "avatar_url": "https://example.com/avatar.png",
                "home_city_id": "11111111-1111-1111-1111-111111111111",
                "preferred_match_tags": ["rivalry", "knockout"],
                "favorite_team_ids": ["22222222-2222-2222-2222-222222222222"],
                "profile_completed": False,
            },
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.json()["profile"]["profile_completed"] is True
    assert response.json()["preferences"]["favorite_team_ids"] == [
        "22222222-2222-2222-2222-222222222222"
    ]
    assert fake_service.updated_payload["payload"]["profile_completed"] is True
