from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "throughball-platform-api"
    log_level: str = "INFO"
    api_cors_origins: str = "http://localhost:3000"
    supabase_url: str = ""
    supabase_anon_key: str = ""
    supabase_jwks_url: str = ""
    next_public_supabase_url: str = ""
    next_public_supabase_anon_key: str = ""

    model_config = SettingsConfigDict(env_file=".env.local", extra="ignore")

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.api_cors_origins.split(",") if origin.strip()]

    @property
    def effective_supabase_url(self) -> str:
        return self.supabase_url or self.next_public_supabase_url

    @property
    def effective_supabase_anon_key(self) -> str:
        return self.supabase_anon_key or self.next_public_supabase_anon_key


@lru_cache
def get_settings() -> Settings:
    return Settings()
