"""Telegram adapter - connects core logic to Telegram platform.

This module implements platform-specific features for Telegram,
including bot handlers, WebApp integration, and Telegram notifications.
"""

from .notification import TelegramNotificationService
from .repository import TelegramProfileRepository, TelegramUserRepository
from .storage import TelegramStorageService

__all__ = [
    "TelegramUserRepository",
    "TelegramProfileRepository",
    "TelegramNotificationService",
    "TelegramStorageService",
]
