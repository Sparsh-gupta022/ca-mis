"""
Application configuration.

Settings are loaded from environment variables (via a .env file in local
development). Nothing sensitive is hardcoded here — see .env.example for
the variables this application expects.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # --- App metadata ---
    app_name: str = "HSDG & Associates MIS"
    api_v1_prefix: str = "/api/v1"
    environment: str = "development"
    debug: bool = True

    # --- Database ---
    # Full SQLAlchemy connection string. The default below is a placeholder
    # for local development only (matches .env.example) — it is not a real
    # credential. Always override via a local, untracked .env file.
    database_url: str = "postgresql+psycopg2://postgres:postgres@localhost:5432/hsdg_mis"

    # --- CORS ---
    # Comma-separated list of allowed origins for the (future) React frontend.
    cors_origins: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Cached settings accessor so we parse the environment only once."""
    return Settings()


settings = get_settings()
