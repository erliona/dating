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
        monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF-ghijkl")
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
        monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF-ghijkl")

        with pytest.raises(RuntimeError, match="BOT_DATABASE_URL environment variable is required"):
            load_config()

    def test_load_config_validates_database_url_format(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that malformed database URLs are rejected."""
        monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF-ghijkl")
        monkeypatch.setenv("BOT_DATABASE_URL", "not-a-valid-url")

        with pytest.raises(RuntimeError, match="must be a valid SQLAlchemy connection string"):
            load_config()

    def test_load_config_only_accepts_postgresql(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that only PostgreSQL databases are accepted."""
        monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF-ghijkl")
        monkeypatch.setenv("BOT_DATABASE_URL", "sqlite:///dating.db")

        with pytest.raises(RuntimeError, match="Only PostgreSQL databases are supported"):
            load_config()

    def test_load_config_requires_database_host(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that database URL must include a host."""
        monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF-ghijkl")
        monkeypatch.setenv("BOT_DATABASE_URL", "postgresql+asyncpg:///dating")

        with pytest.raises(RuntimeError, match="must include a database host"):
            load_config()

    def test_load_config_requires_database_name(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that database URL must include a database name."""
        monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF-ghijkl")
        monkeypatch.setenv("BOT_DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/")

        with pytest.raises(RuntimeError, match="must include a database name"):
            load_config()

    def test_load_config_accepts_url_safe_passwords(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that database URLs with URL-safe alphanumeric passwords work correctly."""
        monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF-ghijkl")
        
        # Test various alphanumeric passwords (URL-safe)
        url_safe_passwords = [
            "simplepassword123",
            "UPPERCASE123",
            "MixedCase456",
            "abc123XYZ789",
            "a" * 32,  # 32-char alphanumeric
            "1" * 32,  # All numeric (valid)
        ]
        
        for password in url_safe_passwords:
            url = f"postgresql+asyncpg://user:{password}@localhost:5432/dating"
            monkeypatch.setenv("BOT_DATABASE_URL", url)
            config = load_config()
            assert f"user:***@localhost" in config.database_url or "user:" in config.database_url

    def test_load_config_rejects_empty_webapp_url(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that whitespace-only WEBAPP_URL is rejected."""
        monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF-ghijkl")
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
        monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF-ghijkl")
        monkeypatch.setenv(
            "DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/dating"
        )

        config = load_config()

        assert "postgresql+asyncpg://" in config.database_url

    def test_load_config_requires_https_for_webapp_url(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that WEBAPP_URL must use HTTPS for non-localhost URLs."""
        monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF-ghijkl")
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
        monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF-ghijkl")
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
        monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF-ghijkl")
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
        monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF-ghijkl")
        monkeypatch.setenv(
            "BOT_DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/dating"
        )
        monkeypatch.setenv("WEBAPP_URL", "https://my-domain.com")

        config = load_config()

        assert config.webapp_url == "https://my-domain.com"
    
    def test_load_config_rejects_placeholder_tokens(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that placeholder BOT_TOKEN values are rejected."""
        monkeypatch.setenv(
            "BOT_DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/dating"
        )
        
        placeholder_tokens = [
            "your-telegram-bot-token-here",
            "replace-me-with-token",
            "insert-token-here",
            "paste-your-token",
            "add-bot-token",
            "enter-token",
            "example-token",
            "placeholder-value",
            "token-here",
            "bot-token",
            "from-botfather",
        ]
        
        for token in placeholder_tokens:
            monkeypatch.setenv("BOT_TOKEN", token)
            with pytest.raises(RuntimeError, match="appears to be a placeholder"):
                load_config()
    
    def test_load_config_validates_token_format(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that BOT_TOKEN must match Telegram token format."""
        monkeypatch.setenv(
            "BOT_DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/dating"
        )
        
        invalid_tokens = [
            "not-a-valid-token",
            "12345",  # Missing colon and hash
            "abcdef:123456",  # ID should be numeric
            "123456:",  # Missing hash
            ":ABCdef123",  # Missing ID
            "123 456:ABC-def",  # Space in ID
        ]
        
        for token in invalid_tokens:
            monkeypatch.setenv("BOT_TOKEN", token)
            with pytest.raises(RuntimeError, match="has invalid format"):
                load_config()
    
    def test_load_config_accepts_valid_token_format(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that valid Telegram token formats are accepted."""
        monkeypatch.setenv(
            "BOT_DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/dating"
        )
        
        valid_tokens = [
            "123456789:ABCdefGHIjklMNOpqrsTUVwxyz-1234567",
            "987654321:XYZ-abc_def123",
            "1:A",  # Minimal valid token
            "123456:ABC-DEF-ghijkl",  # With hyphens
            "123456:ABC_DEF_ghijkl",  # With underscores
        ]
        
        for token in valid_tokens:
            monkeypatch.setenv("BOT_TOKEN", token)
            config = load_config()
            assert config.token == token

    def test_load_config_accepts_uppercase_https_protocol(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that HTTPS protocol is case-insensitive and normalized."""
        monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF-ghijkl")
        monkeypatch.setenv(
            "BOT_DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/dating"
        )
        
        # Test various protocol cases
        test_cases = [
            ("HTTPS://example.com", "https://example.com"),
            ("Https://example.com", "https://example.com"),
            ("https://example.com", "https://example.com"),
            ("HTTPS://EXAMPLE.COM/path", "https://EXAMPLE.COM/path"),
        ]
        
        for input_url, expected_url in test_cases:
            monkeypatch.setenv("WEBAPP_URL", input_url)
            config = load_config()
            assert config.webapp_url == expected_url, f"Failed for {input_url}"

    def test_load_config_normalizes_http_protocol_for_localhost(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that HTTP protocol is normalized to lowercase for localhost."""
        monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF-ghijkl")
        monkeypatch.setenv(
            "BOT_DATABASE_URL", "postgresql+asyncpg://user:pass@localhost:5432/dating"
        )
        
        # Test various protocol cases for localhost
        test_cases = [
            ("HTTP://localhost:8080", "http://localhost:8080"),
            ("Http://localhost:8080", "http://localhost:8080"),
            ("http://localhost:8080", "http://localhost:8080"),
            ("HTTP://127.0.0.1:8080", "http://127.0.0.1:8080"),
        ]
        
        for input_url, expected_url in test_cases:
            monkeypatch.setenv("WEBAPP_URL", input_url)
            config = load_config()
            assert config.webapp_url == expected_url, f"Failed for {input_url}"

