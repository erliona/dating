"""Telegram adapter - connects core logic to Telegram platform.

This module implements platform-specific features for Telegram,
including bot handlers, WebApp integration, and Telegram notifications.
"""

from .repository import TelegramUserRepository, TelegramProfileRepository
from .notification import TelegramNotificationService
from .storage import TelegramStorageService

__all__ = [
    "TelegramUserRepository",
    "TelegramProfileRepository",
    "TelegramNotificationService",
    "TelegramStorageService",
]
