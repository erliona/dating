"""Tests for bot configuration module."""

import os

import pytest

from bot.config import load_config


class TestConfigJWTSecret:
    """Tests for JWT secret configuration."""
    
    def test_jwt_secret_from_env(self, monkeypatch):
        """Test JWT secret is loaded from environment."""
        monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
        monkeypatch.setenv("POSTGRES_USER", "test_user")
        monkeypatch.setenv("POSTGRES_PASSWORD", "test_pass")
        monkeypatch.setenv("POSTGRES_DB", "test_db")
        monkeypatch.setenv("JWT_SECRET", "my_test_secret_key")
        
        config = load_config()
        
        assert config.jwt_secret == "my_test_secret_key"
    
    def test_jwt_secret_generated_if_missing(self, monkeypatch, caplog):
        """Test JWT secret is generated if not provided."""
        monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
        monkeypatch.setenv("POSTGRES_USER", "test_user")
        monkeypatch.setenv("POSTGRES_PASSWORD", "test_pass")
        monkeypatch.setenv("POSTGRES_DB", "test_db")
        
        # Remove JWT_SECRET if set
        monkeypatch.delenv("JWT_SECRET", raising=False)
        
        config = load_config()
        
        # Should have generated a secret
        assert config.jwt_secret is not None
        assert len(config.jwt_secret) > 0
        
        # Should have logged a warning
        assert "JWT_SECRET not set" in caplog.text
    
    def test_jwt_secret_in_config_dataclass(self, monkeypatch):
        """Test JWT secret is included in BotConfig."""
        monkeypatch.setenv("BOT_TOKEN", "123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
        monkeypatch.setenv("POSTGRES_USER", "test_user")
        monkeypatch.setenv("POSTGRES_PASSWORD", "test_pass")
        monkeypatch.setenv("POSTGRES_DB", "test_db")
        monkeypatch.setenv("JWT_SECRET", "test_secret")
        
        config = load_config()
        
        # Verify jwt_secret is accessible as attribute
        assert hasattr(config, 'jwt_secret')
        assert config.jwt_secret == "test_secret"
