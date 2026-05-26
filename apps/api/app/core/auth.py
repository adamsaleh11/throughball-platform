import time
from typing import Any, Optional

import httpx
import jwt
from jwt import PyJWKClient

from app.core.config import get_settings


class AuthValidationError(Exception):
    pass


class ProfileStorageError(Exception):
    def __init__(self, message: str, status_code: int = 503) -> None:
        super().__init__(message)
        self.status_code = status_code


class SupabaseJwtValidator:
    def __init__(self) -> None:
        self._jwks_client: Optional[PyJWKClient] = None
        self._jwks_url = ""
        self._last_configured_at = 0.0

    async def validate(self, token: str) -> dict[str, str]:
        settings = get_settings()
        if not settings.supabase_jwks_url:
            return await self._validate_with_supabase_auth(token)

        try:
            signing_key = self._get_jwks_client(settings.supabase_jwks_url).get_signing_key_from_jwt(
                token
            )
            claims: dict[str, Any] = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256"],
                audience="authenticated",
                options={"verify_exp": True},
            )
        except Exception:
            return await self._validate_with_supabase_auth(token)

        subject = claims.get("sub")
        if not subject:
            raise AuthValidationError("Invalid bearer token.")

        return {"user_id": str(subject), "access_token": token}

    async def _validate_with_supabase_auth(self, token: str) -> dict[str, str]:
        settings = get_settings()
        supabase_url = settings.effective_supabase_url.rstrip("/")
        supabase_anon_key = settings.effective_supabase_anon_key
        if not supabase_url or not supabase_anon_key:
            raise AuthValidationError("Supabase URL and anon key are not configured.")

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{supabase_url}/auth/v1/user",
                    headers={
                        "apikey": supabase_anon_key,
                        "authorization": f"Bearer {token}",
                    },
                )
            response.raise_for_status()
            user = response.json()
        except Exception as exc:
            raise AuthValidationError("Invalid bearer token.") from exc

        user_id = user.get("id")
        if not user_id:
            raise AuthValidationError("Invalid bearer token.")

        return {"user_id": str(user_id), "access_token": token}

    def _get_jwks_client(self, jwks_url: str) -> PyJWKClient:
        now = time.monotonic()
        if self._jwks_client is None or self._jwks_url != jwks_url or now - self._last_configured_at > 300:
            self._jwks_client = PyJWKClient(jwks_url)
            self._jwks_url = jwks_url
            self._last_configured_at = now
        return self._jwks_client


class SupabaseProfileService:
    def __init__(self) -> None:
        settings = get_settings()
        self.supabase_url = settings.effective_supabase_url.rstrip("/")
        self.supabase_anon_key = settings.effective_supabase_anon_key

    async def get_profile(self, user_id: str, access_token: str) -> dict[str, Any]:
        profile = await self._get_single("profiles", f"id=eq.{user_id}", access_token)
        preferences = await self._get_single("user_preferences", f"user_id=eq.{user_id}", access_token)
        favorites = await self._get_many(
            "user_favorite_teams",
            f"user_id=eq.{user_id}&select=team_id",
            access_token,
        )

        return {
            "profile": profile,
            "preferences": {
                **preferences,
                "favorite_team_ids": [row["team_id"] for row in favorites],
            },
        }

    async def update_profile(
        self,
        user_id: str,
        access_token: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        profile_payload = {
            "display_name": payload["display_name"],
            "avatar_url": payload["avatar_url"],
            "profile_completed": payload["profile_completed"],
        }
        preferences_payload = {
            "user_id": user_id,
            "home_city_id": payload["home_city_id"],
            "preferred_match_tags": payload["preferred_match_tags"],
        }

        await self._patch("profiles", f"id=eq.{user_id}", profile_payload, access_token)
        await self._upsert("user_preferences", preferences_payload, access_token)
        await self._delete("user_favorite_teams", f"user_id=eq.{user_id}", access_token)
        favorite_rows = [
            {"user_id": user_id, "team_id": team_id} for team_id in payload["favorite_team_ids"]
        ]
        if favorite_rows:
            await self._upsert("user_favorite_teams", favorite_rows, access_token)

        return await self.get_profile(user_id, access_token)

    def _headers(self, access_token: str) -> dict[str, str]:
        if not self.supabase_url or not self.supabase_anon_key:
            raise RuntimeError("Supabase URL and anon key are required for profile APIs.")
        return {
            "apikey": self.supabase_anon_key,
            "authorization": f"Bearer {access_token}",
            "content-type": "application/json",
        }

    async def _get_single(self, table: str, query: str, access_token: str) -> dict[str, Any]:
        rows = await self._get_many(table, f"{query}&limit=1", access_token)
        if not rows:
            raise RuntimeError(f"{table} row was not found.")
        return rows[0]

    async def _get_many(self, table: str, query: str, access_token: str) -> list[dict[str, Any]]:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.get(
                f"{self.supabase_url}/rest/v1/{table}?{query}",
                headers=self._headers(access_token),
            )
        self._raise_for_storage_error(response, table)
        data = response.json()
        return data if isinstance(data, list) else [data]

    async def _patch(
        self,
        table: str,
        query: str,
        payload: dict[str, Any],
        access_token: str,
    ) -> None:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.patch(
                f"{self.supabase_url}/rest/v1/{table}?{query}",
                headers={**self._headers(access_token), "prefer": "return=minimal"},
                json=payload,
            )
        self._raise_for_storage_error(response, table)

    async def _upsert(self, table: str, payload: Any, access_token: str) -> None:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(
                f"{self.supabase_url}/rest/v1/{table}",
                headers={
                    **self._headers(access_token),
                    "prefer": "resolution=merge-duplicates,return=minimal",
                },
                json=payload,
            )
        self._raise_for_storage_error(response, table)

    async def _delete(self, table: str, query: str, access_token: str) -> None:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.delete(
                f"{self.supabase_url}/rest/v1/{table}?{query}",
                headers={**self._headers(access_token), "prefer": "return=minimal"},
            )
        self._raise_for_storage_error(response, table)

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
