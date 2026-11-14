"""Settings for Pydantic Settings."""

from pathlib import Path

from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Settings for the application, including database configuration."""
    database_url: str

    model_config = SettingsConfigDict(
        env_file=BASE_DIR.parent / ".env.local",
        extra="ignore",
    )

    @field_validator("database_url")
    @classmethod
    def use_psycopg_driver(cls, value: str) -> str:
        """Use the installed psycopg driver for standard Postgres URLs."""
        for prefix in ("postgresql://", "postgres://"):
            if value.startswith(prefix):
                return "postgresql+psycopg://" + value[len(prefix):]
        return value


settings = Settings() # pyright: ignore[reportCallIssue]  # pylint: disable=no-value-for-parameter
