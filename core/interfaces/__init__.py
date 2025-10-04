"""Core interfaces - contracts for platform adapters."""

from .repository import IUserRepository, IProfileRepository
from .notification import INotificationService
from .storage import IStorageService

__all__ = [
    "IUserRepository",
    "IProfileRepository",
    "INotificationService",
    "IStorageService",
]
