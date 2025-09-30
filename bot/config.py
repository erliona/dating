"""Configuration helpers for the dating bot."""

from __future__ import annotations

import os
from dataclasses import dataclass

from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError


@dataclass(slots=True)
class BotConfig:
    """Settings required to run the bot."""

    token: str
    database_url: str
    webapp_url: str


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
    if not token.strip():
        raise RuntimeError("BOT_TOKEN cannot be empty or whitespace")

    webapp_url = os.getenv("WEBAPP_URL")
    if webapp_url is None:
        raise RuntimeError("WEBAPP_URL environment variable is required to start the bot")

    webapp_url = webapp_url.strip()
    if not webapp_url:
        raise RuntimeError("WEBAPP_URL cannot be empty or whitespace")
    
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
