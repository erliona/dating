"""Tests for bot configuration module."""

from __future__ import annotations

import pytest

from bot.config import BotConfig, load_config


@pytest.mark.usefixtures("clean_env")
class TestBotConfig:
    """Test suite for configuration loading and validation."""

    def test_load_config_success(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test successful configuration loading with all required variables."""
        monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF-test-token")
        monkeypatch.setenv(
            "BOT_DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/dating"
        )
        monkeypatch.setenv("WEBAPP_URL", "https://example.com/webapp")

        config = load_config()

        assert isinstance(config, BotConfig)
        assert config.token == "123456:ABC-DEF-test-token"
        assert "postgresql+asyncpg://user:***@localhost:5432/dating" in config.database_url
        assert config.webapp_url == "https://example.com/webapp"

    def test_load_config_without_webapp_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test configuration works without optional WEBAPP_URL."""
        monkeypatch.setenv("BOT_TOKEN", "test-token")
        monkeypatch.setenv(
            "BOT_DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/dating"
        )

        config = load_config()

        assert config.webapp_url is None

    def test_load_config_requires_bot_token(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that BOT_TOKEN is required."""
        monkeypatch.setenv(
            "BOT_DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/dating"
        )

        with pytest.raises(RuntimeError, match="BOT_TOKEN environment variable is required"):
            load_config()

    def test_load_config_rejects_empty_bot_token(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that empty BOT_TOKEN is rejected."""
        monkeypatch.setenv("BOT_TOKEN", "   ")
        monkeypatch.setenv(
            "BOT_DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/dating"
        )

        with pytest.raises(RuntimeError, match="BOT_TOKEN cannot be empty"):
            load_config()

    def test_load_config_requires_database_url(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that BOT_DATABASE_URL is required."""
        monkeypatch.setenv("BOT_TOKEN", "test-token")

        with pytest.raises(RuntimeError, match="BOT_DATABASE_URL environment variable is required"):
            load_config()

    def test_load_config_validates_database_url_format(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that malformed database URLs are rejected."""
        monkeypatch.setenv("BOT_TOKEN", "test-token")
        monkeypatch.setenv("BOT_DATABASE_URL", "not-a-valid-url")

        with pytest.raises(RuntimeError, match="must be a valid SQLAlchemy connection string"):
            load_config()

    def test_load_config_only_accepts_postgresql(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that only PostgreSQL databases are accepted."""
        monkeypatch.setenv("BOT_TOKEN", "test-token")
        monkeypatch.setenv("BOT_DATABASE_URL", "sqlite:///dating.db")

        with pytest.raises(RuntimeError, match="Only PostgreSQL databases are supported"):
            load_config()

    def test_load_config_requires_database_host(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that database URL must include a host."""
        monkeypatch.setenv("BOT_TOKEN", "test-token")
        monkeypatch.setenv("BOT_DATABASE_URL", "postgresql+asyncpg:///dating")

        with pytest.raises(RuntimeError, match="must include a database host"):
            load_config()

    def test_load_config_requires_database_name(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that database URL must include a database name."""
        monkeypatch.setenv("BOT_TOKEN", "test-token")
        monkeypatch.setenv("BOT_DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/")

        with pytest.raises(RuntimeError, match="must include a database name"):
            load_config()

    def test_load_config_rejects_empty_webapp_url(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that whitespace-only WEBAPP_URL is rejected."""
        monkeypatch.setenv("BOT_TOKEN", "test-token")
        monkeypatch.setenv(
            "BOT_DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/dating"
        )
        monkeypatch.setenv("WEBAPP_URL", "   ")

        with pytest.raises(RuntimeError, match="WEBAPP_URL cannot be empty"):
            load_config()

    def test_load_config_uses_database_url_fallback(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that DATABASE_URL is used as fallback if BOT_DATABASE_URL is not set."""
        monkeypatch.setenv("BOT_TOKEN", "test-token")
        monkeypatch.setenv(
            "DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/dating"
        )

        config = load_config()

        assert "postgresql+asyncpg://" in config.database_url

    def test_load_config_requires_https_for_webapp_url(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that WEBAPP_URL must use HTTPS for non-localhost URLs."""
        monkeypatch.setenv("BOT_TOKEN", "test-token")
        monkeypatch.setenv(
            "BOT_DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/dating"
        )
        monkeypatch.setenv("WEBAPP_URL", "http://example.com/webapp")

        with pytest.raises(RuntimeError, match="must use HTTPS protocol"):
            load_config()

    def test_load_config_allows_http_for_localhost(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that HTTP is allowed for localhost development."""
        monkeypatch.setenv("BOT_TOKEN", "test-token")
        monkeypatch.setenv(
            "BOT_DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/dating"
        )
        monkeypatch.setenv("WEBAPP_URL", "http://localhost:8080")

        config = load_config()

        assert config.webapp_url == "http://localhost:8080"

    def test_load_config_allows_http_for_127_0_0_1(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that HTTP is allowed for 127.0.0.1 development."""
        monkeypatch.setenv("BOT_TOKEN", "test-token")
        monkeypatch.setenv(
            "BOT_DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/dating"
        )
        monkeypatch.setenv("WEBAPP_URL", "http://127.0.0.1:8080")

        config = load_config()

        assert config.webapp_url == "http://127.0.0.1:8080"

    def test_load_config_accepts_https_webapp_url(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that HTTPS webapp URLs are accepted."""
        monkeypatch.setenv("BOT_TOKEN", "test-token")
        monkeypatch.setenv(
            "BOT_DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/dating"
        )
        monkeypatch.setenv("WEBAPP_URL", "https://my-domain.com")

        config = load_config()

        assert config.webapp_url == "https://my-domain.com"

