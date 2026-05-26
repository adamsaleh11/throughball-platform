from fastapi.testclient import TestClient

from app.main import app
from app.routes.profile import get_current_user, get_profile_persistence


client = TestClient(app)


class FakeProfilePersistence:
    def __init__(self) -> None:
        self.updated_command = None

    async def current_profile(self, user) -> dict:
        return {
            "profile": {
                "id": user.user_id,
                "display_name": "Alex",
                "avatar_url": None,
                "profile_completed": True,
                "created_at": "2026-05-25T12:00:00Z",
                "updated_at": "2026-05-25T12:00:00Z",
            },
            "preferences": {
                "user_id": user.user_id,
                "home_city_id": "11111111-1111-1111-1111-111111111111",
                "preferred_match_tags": ["rivalry"],
                "favorite_team_ids": ["22222222-2222-2222-2222-222222222222"],
                "created_at": "2026-05-25T12:00:00Z",
                "updated_at": "2026-05-25T12:00:00Z",
            },
        }

    async def save_current_profile(self, user, command) -> dict:
        self.updated_command = {
            "user_id": user.user_id,
            "access_token": user.access_token,
            "command": command,
        }
        favorite_team_ids = [str(team_id) for team_id in command.favorite_team_ids]
        home_city_id = str(command.home_city_id) if command.home_city_id else None
        profile_completed = bool(command.display_name and (home_city_id or favorite_team_ids))
        return {
            "profile": {
                "id": user.user_id,
                "display_name": command.display_name,
                "avatar_url": command.avatar_url,
                "profile_completed": profile_completed,
                "created_at": "2026-05-25T12:00:00Z",
                "updated_at": "2026-05-25T12:05:00Z",
            },
            "preferences": {
                "user_id": user.user_id,
                "home_city_id": home_city_id,
                "preferred_match_tags": command.preferred_match_tags,
                "favorite_team_ids": favorite_team_ids,
                "created_at": "2026-05-25T12:00:00Z",
                "updated_at": "2026-05-25T12:05:00Z",
            },
        }


async def fake_current_user() -> dict:
    from app.core.profile import AuthenticatedUser

    return AuthenticatedUser(
        user_id="00000000-0000-0000-0000-000000000001",
        access_token="valid-token",
    )


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
    app.dependency_overrides[get_profile_persistence] = lambda: FakeProfilePersistence()

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
    app.dependency_overrides[get_profile_persistence] = lambda: FakeProfilePersistence()

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
    fake_persistence = FakeProfilePersistence()
    app.dependency_overrides[get_current_user] = fake_current_user
    app.dependency_overrides[get_profile_persistence] = lambda: fake_persistence

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
    assert fake_persistence.updated_command["command"].display_name == "Alex"
