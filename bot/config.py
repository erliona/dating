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
    webapp_url: str | None = None


def load_config() -> BotConfig:
    """Load configuration values from environment variables.

    Returns:
        BotConfig: Populated configuration instance.

    Raises:
        RuntimeError: If the bot token is missing.
    """

    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN environment variable is required to start the bot")

    webapp_url = os.getenv("WEBAPP_URL")
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

    return BotConfig(
        token=token, database_url=str(database_url), webapp_url=webapp_url
    )
