"""Configuration helpers for the dating bot."""

from __future__ import annotations

import os
import re
from dataclasses import dataclass

from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


@dataclass(slots=True)
class BotConfig:
    """Settings required to run the bot."""

    token: str
    database_url: str
    webapp_url: str | None = None


def load_config() -> BotConfig:
    """Load configuration values from environment variables.

    Returns:
        BotConfig: Populated configuration instance.

    Raises:
        RuntimeError: If the bot token is missing or configuration is invalid.
    """

    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN environment variable is required to start the bot")
    
    # Validate token format (basic check)
    token = token.strip()
    if not token:
        raise RuntimeError("BOT_TOKEN cannot be empty or whitespace")
    
    # Check for common placeholder patterns
    placeholder_patterns = [
        "your-",
        "replace-",
        "insert-",
        "paste-",
        "add-",
        "enter-",
        "example",
        "placeholder",
        "token-here",
        "bot-token",
        "from-botfather",
    ]
    token_lower = token.lower()
    if any(pattern in token_lower for pattern in placeholder_patterns):
        raise RuntimeError(
            "BOT_TOKEN appears to be a placeholder value. "
            "Please set a real Telegram bot token from @BotFather. "
            "Valid tokens have the format: <numeric_id>:<alphanumeric_hash> "
            "(example: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz-1234567)"
        )
    
    # Validate Telegram bot token format: <numeric_id>:<alphanumeric_hash>
    # Bot tokens are typically in the format: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz
    if not re.match(r'^\d+:[A-Za-z0-9_-]+$', token):
        raise RuntimeError(
            "BOT_TOKEN has invalid format. "
            "Telegram bot tokens must match the format: <numeric_id>:<alphanumeric_hash> "
            "(example: 123456789:ABCdefGHIjklMNOpqrsTUVwxyz-1234567). "
            "Get a valid token from @BotFather on Telegram."
        )

    webapp_url = os.getenv("WEBAPP_URL")
    if webapp_url and not webapp_url.strip():
        raise RuntimeError("WEBAPP_URL cannot be empty if set; unset it or provide a valid URL")
    
    # Validate WEBAPP_URL uses HTTPS for production security
    if webapp_url:
        webapp_url = webapp_url.strip()
        # Allow localhost and 127.0.0.1 for development/testing
        is_local = any(x in webapp_url.lower() for x in ["localhost", "127.0.0.1"])
        # Check protocol case-insensitively
        webapp_url_lower = webapp_url.lower()
        if not webapp_url_lower.startswith("https://") and not is_local:
            raise RuntimeError(
                "WEBAPP_URL must use HTTPS protocol for security. "
                "Only localhost URLs are allowed to use HTTP for local development."
            )
        
        # Normalize protocol to lowercase for consistency
        # Replace the protocol part (everything before ://) with lowercase version
        if "://" in webapp_url:
            protocol, rest = webapp_url.split("://", 1)
            webapp_url = protocol.lower() + "://" + rest
    
    database_url_raw = os.getenv("BOT_DATABASE_URL") or os.getenv("DATABASE_URL")
    if not database_url_raw:
        raise RuntimeError(
            "BOT_DATABASE_URL environment variable is required to start the bot"
        )

    try:
        database_url = make_url(database_url_raw)
    except ArgumentError as exc:  # pragma: no cover - simple configuration guard
        raise RuntimeError(
            "BOT_DATABASE_URL must be a valid SQLAlchemy connection string"
        ) from exc

    if not database_url.drivername.startswith("postgresql"):
        raise RuntimeError(
            "Only PostgreSQL databases are supported; "
            "set BOT_DATABASE_URL to a postgresql+asyncpg URL"
        )
    
    # Validate database URL has required components
    if not database_url.host:
        raise RuntimeError("BOT_DATABASE_URL must include a database host")
    
    if not database_url.database:
        raise RuntimeError("BOT_DATABASE_URL must include a database name")

    return BotConfig(
        token=token, database_url=str(database_url), webapp_url=webapp_url
    )
