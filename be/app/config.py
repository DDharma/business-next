from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parent.parent / ".env"),
        extra="ignore",
        case_sensitive=False,
    )

    supabase_url: str
    supabase_key: str
    db_password: str | None = None

    lm_studio_url: str = "http://localhost:1234/v1"
    lm_studio_model: str = "google/gemma-3-4b"

    cors_origins: list[str] = ["http://localhost:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()  # type: ignore[call-arg]
