import asyncio

import httpx
import pytest

from app.core.profile import (
    AuthenticatedUser,
    ProfileStorageError,
    ProfileUpdateCommand,
    SupabaseProfilePersistence,
    SupabaseRestClient,
)


class FakeRestClient:
    def __init__(self) -> None:
        self.calls = []
        self.favorite_rows = [{"team_id": "22222222-2222-2222-2222-222222222222"}]
        self.profile = {
            "id": "00000000-0000-0000-0000-000000000001",
            "display_name": "Alex",
            "avatar_url": None,
            "profile_completed": False,
            "created_at": "2026-05-25T12:00:00Z",
            "updated_at": "2026-05-25T12:00:00Z",
        }
        self.preferences = {
            "user_id": "00000000-0000-0000-0000-000000000001",
            "home_city_id": "11111111-1111-1111-1111-111111111111",
            "preferred_match_tags": ["rivalry"],
            "created_at": "2026-05-25T12:00:00Z",
            "updated_at": "2026-05-25T12:00:00Z",
        }

    async def get_many(self, table: str, query: str, user: AuthenticatedUser):
        self.calls.append(("get_many", table, query, user.access_token))
        if table == "profiles":
            return [self.profile]
        if table == "user_preferences":
            return [self.preferences]
        if table == "user_favorite_teams":
            return self.favorite_rows
        raise AssertionError(f"Unexpected table: {table}")

    async def patch(self, table: str, query: str, payload: dict, user: AuthenticatedUser) -> None:
        self.calls.append(("patch", table, query, payload, user.access_token))
        if table == "profiles":
            self.profile = {**self.profile, **payload}

    async def upsert(self, table: str, payload, user: AuthenticatedUser) -> None:
        self.calls.append(("upsert", table, payload, user.access_token))
        if table == "user_preferences":
            self.preferences = {**self.preferences, **payload}
        if table == "user_favorite_teams":
            self.favorite_rows = [{"team_id": row["team_id"]} for row in payload]

    async def delete(self, table: str, query: str, user: AuthenticatedUser) -> None:
        self.calls.append(("delete", table, query, user.access_token))
        if table == "user_favorite_teams":
            self.favorite_rows = []


USER = AuthenticatedUser(
    user_id="00000000-0000-0000-0000-000000000001",
    access_token="valid-token",
)


def test_current_profile_composes_profile_preferences_and_favorites() -> None:
    persistence = SupabaseProfilePersistence(FakeRestClient())

    profile = asyncio.run(persistence.current_profile(USER))

    assert profile["profile"]["id"] == USER.user_id
    assert profile["preferences"]["home_city_id"] == "11111111-1111-1111-1111-111111111111"
    assert profile["preferences"]["favorite_team_ids"] == [
        "22222222-2222-2222-2222-222222222222"
    ]


def test_save_current_profile_computes_completion_and_replaces_favorites() -> None:
    rest = FakeRestClient()
    persistence = SupabaseProfilePersistence(rest)

    profile = asyncio.run(
        persistence.save_current_profile(
            USER,
            ProfileUpdateCommand(
                display_name="Alex",
                avatar_url="https://example.com/avatar.png",
                home_city_id=None,
                preferred_match_tags=["rivalry", "knockout"],
                favorite_team_ids=[
                    "33333333-3333-3333-3333-333333333333",
                    "44444444-4444-4444-4444-444444444444",
                ],
            ),
        )
    )

    assert profile["profile"]["profile_completed"] is True
    assert profile["preferences"]["favorite_team_ids"] == [
        "33333333-3333-3333-3333-333333333333",
        "44444444-4444-4444-4444-444444444444",
    ]
    assert rest.calls[0][0:3] == ("patch", "profiles", f"id=eq.{USER.user_id}")
    assert rest.calls[1][0:2] == ("upsert", "user_preferences")
    assert rest.calls[2][0:3] == ("delete", "user_favorite_teams", f"user_id=eq.{USER.user_id}")
    assert rest.calls[3][0:2] == ("upsert", "user_favorite_teams")


def test_supabase_rest_client_maps_missing_table_to_profile_storage_error() -> None:
    response = httpx.Response(404, request=httpx.Request("GET", "https://example.test"))

    with pytest.raises(ProfileStorageError) as exc_info:
        SupabaseRestClient()._raise_for_storage_error(response, "profiles")

    assert exc_info.value.status_code == 503
    assert "profiles" in str(exc_info.value)
