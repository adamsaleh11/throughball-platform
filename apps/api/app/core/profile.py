from dataclasses import dataclass
from typing import Any, Optional, Protocol
from uuid import UUID

import httpx

from app.core.config import get_settings


@dataclass(frozen=True)
class AuthenticatedUser:
    user_id: str
    access_token: str


@dataclass(frozen=True)
class ProfileUpdateCommand:
    display_name: Optional[str]
    avatar_url: Optional[str]
    home_city_id: Optional[UUID]
    preferred_match_tags: list[str]
    favorite_team_ids: list[UUID]


class ProfileStorageError(Exception):
    def __init__(self, message: str, status_code: int = 503) -> None:
        super().__init__(message)
        self.status_code = status_code


class ProfilePersistence(Protocol):
    async def current_profile(self, user: AuthenticatedUser) -> dict[str, Any]:
        ...

    async def save_current_profile(
        self,
        user: AuthenticatedUser,
        command: ProfileUpdateCommand,
    ) -> dict[str, Any]:
        ...


class SupabaseRestClient:
    def __init__(self) -> None:
        settings = get_settings()
        self.supabase_url = settings.effective_supabase_url.rstrip("/")
        self.supabase_anon_key = settings.effective_supabase_anon_key

    async def get_many(
        self,
        table: str,
        query: str,
        user: AuthenticatedUser,
    ) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{self.supabase_url}/rest/v1/{table}?{query}",
                headers=self._headers(user),
            )
        self._raise_for_storage_error(response, table)
        data = response.json()
        return data if isinstance(data, list) else [data]

    async def patch(
        self,
        table: str,
        query: str,
        payload: dict[str, Any],
        user: AuthenticatedUser,
    ) -> None:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.patch(
                f"{self.supabase_url}/rest/v1/{table}?{query}",
                headers={**self._headers(user), "prefer": "return=minimal"},
                json=payload,
            )
        self._raise_for_storage_error(response, table)

    async def upsert(
        self,
        table: str,
        payload: Any,
        user: AuthenticatedUser,
    ) -> None:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{self.supabase_url}/rest/v1/{table}",
                headers={
                    **self._headers(user),
                    "prefer": "resolution=merge-duplicates,return=minimal",
                },
                json=payload,
            )
        self._raise_for_storage_error(response, table)

    async def delete(self, table: str, query: str, user: AuthenticatedUser) -> None:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.delete(
                f"{self.supabase_url}/rest/v1/{table}?{query}",
                headers={**self._headers(user), "prefer": "return=minimal"},
            )
        self._raise_for_storage_error(response, table)

    def _headers(self, user: AuthenticatedUser) -> dict[str, str]:
        if not self.supabase_url or not self.supabase_anon_key:
            raise ProfileStorageError("Supabase URL and anon key are required for profile APIs.")
        return {
            "apikey": self.supabase_anon_key,
            "authorization": f"Bearer {user.access_token}",
            "content-type": "application/json",
        }

    def _raise_for_storage_error(self, response: httpx.Response, table: str) -> None:
        if response.status_code == 404:
            raise ProfileStorageError(
                f"Supabase table '{table}' is not available. Apply the Supabase auth/profile migration.",
                status_code=503,
            )
        try:
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            raise ProfileStorageError("Supabase profile storage request failed.") from exc


class SupabaseProfilePersistence:
    def __init__(self, rest_client: Optional[SupabaseRestClient] = None) -> None:
        self._rest = rest_client or SupabaseRestClient()

    async def current_profile(self, user: AuthenticatedUser) -> dict[str, Any]:
        profile = await self._get_single("profiles", f"id=eq.{user.user_id}", user)
        preferences = await self._get_single("user_preferences", f"user_id=eq.{user.user_id}", user)
        favorites = await self._rest.get_many(
            "user_favorite_teams",
            f"user_id=eq.{user.user_id}&select=team_id",
            user,
        )

        return {
            "profile": profile,
            "preferences": {
                **preferences,
                "favorite_team_ids": [row["team_id"] for row in favorites],
            },
        }

    async def save_current_profile(
        self,
        user: AuthenticatedUser,
        command: ProfileUpdateCommand,
    ) -> dict[str, Any]:
        favorite_team_ids = [str(team_id) for team_id in command.favorite_team_ids]
        profile_payload = {
            "display_name": command.display_name,
            "avatar_url": command.avatar_url,
            "profile_completed": self._completed(command),
        }
        preferences_payload = {
            "user_id": user.user_id,
            "home_city_id": str(command.home_city_id) if command.home_city_id else None,
            "preferred_match_tags": command.preferred_match_tags,
        }

        await self._rest.patch("profiles", f"id=eq.{user.user_id}", profile_payload, user)
        await self._rest.upsert("user_preferences", preferences_payload, user)
        await self._rest.delete("user_favorite_teams", f"user_id=eq.{user.user_id}", user)
        favorite_rows = [{"user_id": user.user_id, "team_id": team_id} for team_id in favorite_team_ids]
        if favorite_rows:
            await self._rest.upsert("user_favorite_teams", favorite_rows, user)

        return await self.current_profile(user)

    async def _get_single(
        self,
        table: str,
        query: str,
        user: AuthenticatedUser,
    ) -> dict[str, Any]:
        rows = await self._rest.get_many(table, f"{query}&limit=1", user)
        if not rows:
            raise ProfileStorageError(f"{table} row was not found.")
        return rows[0]

    def _completed(self, command: ProfileUpdateCommand) -> bool:
        return bool(command.display_name and (command.home_city_id or command.favorite_team_ids))
