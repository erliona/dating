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
    with pytest.raises(RuntimeError, match="BOT_DATABASE_URL") as exc_info:
        load_config()
    
    # Verify the error message contains helpful hints
    error_msg = str(exc_info.value)
    assert "Example:" in error_msg
    assert "postgresql+asyncpg" in error_msg


def test_load_config_validates_database_url(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "test-token")
    monkeypatch.setenv("BOT_DATABASE_URL", "not-a-valid-url")

    with pytest.raises(RuntimeError, match="connection string") as exc_info:
        load_config()
    
    # Verify the error message shows expected format
    error_msg = str(exc_info.value)
    assert "Expected format:" in error_msg
    assert "Received:" in error_msg


def test_load_config_only_accepts_postgres(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BOT_TOKEN", "test-token")
    monkeypatch.setenv("BOT_DATABASE_URL", "sqlite+aiosqlite:///test.db")

    with pytest.raises(RuntimeError, match="Only PostgreSQL") as exc_info:
        load_config()
    
    # Verify the error shows the current driver
    error_msg = str(exc_info.value)
    assert "Current driver:" in error_msg
