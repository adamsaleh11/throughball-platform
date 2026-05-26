from typing import Any, Optional
import time

import httpx
import jwt
from jwt import PyJWKClient

from app.core.config import get_settings


class AuthValidationError(Exception):
    pass


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
