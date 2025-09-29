"""Configuration helpers for the dating bot."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class BotConfig:
    """Settings required to run the bot."""

    token: str
    webapp_url: str | None = None
    storage_path: str | None = None


DEFAULT_STORAGE_PATH = Path(__file__).resolve().parent.parent / "data" / "profiles.json"


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
    storage_path = os.getenv("BOT_STORAGE_PATH")
    if not storage_path:
        storage_path = str(DEFAULT_STORAGE_PATH)

    return BotConfig(token=token, webapp_url=webapp_url, storage_path=storage_path)
