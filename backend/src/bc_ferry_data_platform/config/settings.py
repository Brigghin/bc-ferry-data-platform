"""Settings for Pydantic Settings."""

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    """Settings for the application, including database configuration."""
    database_url: str

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        extra="ignore",
    )


settings = Settings() # pyright: ignore[reportCallIssue]  # pylint: disable=no-value-for-parameter
