from __future__ import annotations

"""Dating bot package - infrastructure only."""

from .config import BotConfig, load_config

__all__ = [
    "BotConfig",
    "load_config",
]
