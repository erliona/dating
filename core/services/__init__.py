"""Core business logic services - platform independent."""

from .user_service import UserService
from .profile_service import ProfileService
from .matching_service import MatchingService

__all__ = [
    "UserService",
    "ProfileService",
    "MatchingService",
]
