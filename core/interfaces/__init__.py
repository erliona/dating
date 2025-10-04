"""Core interfaces - contracts for platform adapters."""

from .notification import INotificationService
from .repository import IProfileRepository, IUserRepository
from .storage import IStorageService

__all__ = [
    "IUserRepository",
    "IProfileRepository",
    "INotificationService",
    "IStorageService",
]
