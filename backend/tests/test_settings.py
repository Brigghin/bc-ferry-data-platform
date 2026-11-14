"""Tests for database settings and Neon URL compatibility."""

import pytest

from bc_ferry_data_platform.config.settings import BASE_DIR, Settings


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("postgresql://user:pass@localhost/db", "postgresql+psycopg://user:pass@localhost/db"),
        ("postgres://user:pass@localhost/db", "postgresql+psycopg://user:pass@localhost/db"),
        ("postgresql+psycopg://localhost/db", "postgresql+psycopg://localhost/db"),
        ("sqlite://", "sqlite://"),
    ],
)
def test_database_url_driver(monkeypatch, url: str, expected: str) -> None:
    """Keep explicit drivers and select psycopg for plain PostgreSQL URLs."""
    monkeypatch.setenv("DATABASE_URL", url)
    assert Settings(_env_file=None).database_url == expected


def test_environment_and_local_file_precedence(monkeypatch, tmp_path) -> None:
    """Environment variables override the Neon dotenv."""
    monkeypatch.delenv("DATABASE_URL", raising=False)
    neon_env = tmp_path / ".env.local"
    neon_env.write_text("DATABASE_URL=sqlite:///neon.db\n", encoding="utf-8")

    assert Settings(_env_file=neon_env).database_url == "sqlite:///neon.db"
    monkeypatch.setenv("DATABASE_URL", "sqlite:///environment.db")
    assert Settings(_env_file=neon_env).database_url == "sqlite:///environment.db"


def test_default_dotenv_is_neon_file() -> None:
    """Do not load the old backend-local database configuration."""
    assert Settings.model_config["env_file"] == BASE_DIR.parent / ".env.local"
