"""Application settings, read from environment variables (and the repo-root .env)."""

from functools import lru_cache
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# backend/app/core/config.py -> parents[3] is the repo root.
# In Docker this file won't exist; real env vars are used instead.
_ROOT_ENV_FILE = Path(__file__).resolve().parents[3] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=_ROOT_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",  # .env also holds POSTGRES_* vars used by docker compose
    )

    # Defaults match docker-compose.dev.yml so a fresh clone works out of the box.
    database_url: str = "postgresql+psycopg://organizy:organizy@127.0.0.1:5432/organizy"
    test_database_url: str = (
        "postgresql+psycopg://organizy:organizy@127.0.0.1:5432/organizy_test"
    )

    # Env var TZ (case-insensitive match). Must be a valid IANA zone name.
    tz: str = "Africa/Algiers"

    @field_validator("tz")
    @classmethod
    def _valid_timezone(cls, value: str) -> str:
        try:
            ZoneInfo(value)
        except (ZoneInfoNotFoundError, ValueError) as exc:
            raise ValueError(f"Unknown time zone: {value!r}") from exc
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
