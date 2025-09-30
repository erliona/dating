from __future__ import annotations

import pytest

from bot.config import BotConfig, load_config


@pytest.fixture(autouse=True)
def clear_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in ("BOT_TOKEN", "BOT_DATABASE_URL", "DATABASE_URL", "WEBAPP_URL"):
        monkeypatch.delenv(key, raising=False)


def test_load_config_success(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "test-token")
    monkeypatch.setenv(
        "BOT_DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/dating"
    )
    monkeypatch.setenv("WEBAPP_URL", "https://example.com")

    config = load_config()

    assert isinstance(config, BotConfig)
    assert config.token == "test-token"
    assert config.database_url == "postgresql+asyncpg://user:***@localhost:5432/dating"
    assert config.webapp_url == "https://example.com"


def test_load_config_requires_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(
        "BOT_DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/dating"
    )
    with pytest.raises(RuntimeError, match="BOT_TOKEN"):
        load_config()


def test_load_config_requires_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "test-token")
    monkeypatch.setenv("WEBAPP_URL", "https://example.com")
    with pytest.raises(RuntimeError, match="BOT_DATABASE_URL"):
        load_config()


def test_load_config_validates_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "test-token")
    monkeypatch.setenv("BOT_DATABASE_URL", "not-a-valid-url")
    monkeypatch.setenv("WEBAPP_URL", "https://example.com")

    with pytest.raises(RuntimeError, match="connection string"):
        load_config()


def test_load_config_only_accepts_postgres(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "test-token")
    monkeypatch.setenv("BOT_DATABASE_URL", "sqlite+aiosqlite:///test.db")
    monkeypatch.setenv("WEBAPP_URL", "https://example.com")

    with pytest.raises(RuntimeError, match="Only PostgreSQL"):
        load_config()


def test_load_config_rejects_empty_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "   ")
    monkeypatch.setenv(
        "BOT_DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/dating"
    )
    
    with pytest.raises(RuntimeError, match="BOT_TOKEN cannot be empty"):
        load_config()


def test_load_config_rejects_empty_webapp_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "test-token")
    monkeypatch.setenv(
        "BOT_DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/dating"
    )
    monkeypatch.setenv("WEBAPP_URL", "   ")

    with pytest.raises(RuntimeError, match="WEBAPP_URL cannot be empty or whitespace"):
        load_config()


def test_load_config_requires_webapp_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "test-token")
    monkeypatch.setenv(
        "BOT_DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/dating"
    )

    with pytest.raises(
        RuntimeError, match="WEBAPP_URL environment variable is required"
    ):
        load_config()


def test_load_config_requires_database_host(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "test-token")
    monkeypatch.setenv("BOT_DATABASE_URL", "postgresql+asyncpg:///dating")
    monkeypatch.setenv("WEBAPP_URL", "https://example.com")

    with pytest.raises(RuntimeError, match="database host"):
        load_config()


def test_load_config_requires_database_name(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "test-token")
    monkeypatch.setenv("BOT_DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/")
    monkeypatch.setenv("WEBAPP_URL", "https://example.com")

    with pytest.raises(RuntimeError, match="database name"):
        load_config()

