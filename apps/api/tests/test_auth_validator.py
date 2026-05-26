import asyncio

from app.core.auth import SupabaseJwtValidator
from app.core.config import get_settings


class FakeResponse:
    def raise_for_status(self) -> None:
        return None

    def json(self) -> dict[str, str]:
        return {"id": "00000000-0000-0000-0000-000000000001"}


class FakeClient:
    def __init__(self, *args, **kwargs) -> None:
        self.requests = []

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    async def get(self, url: str, headers: dict[str, str]):
        self.requests.append({"url": url, "headers": headers})
        return FakeResponse()


def test_validator_uses_supabase_auth_when_jwks_is_not_configured(monkeypatch) -> None:
    get_settings.cache_clear()
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_ANON_KEY", "anon-key")
    monkeypatch.delenv("SUPABASE_JWKS_URL", raising=False)
    monkeypatch.setattr("app.core.auth.httpx.AsyncClient", FakeClient)

    validator = SupabaseJwtValidator()
    user = asyncio.run(validator.validate("access-token"))

    assert user == {
        "user_id": "00000000-0000-0000-0000-000000000001",
        "access_token": "access-token",
    }
    get_settings.cache_clear()
