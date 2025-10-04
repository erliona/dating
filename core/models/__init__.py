"""Core domain models - platform independent."""

from .enums import Education, Gender, Goal, Orientation
from .user import User, UserProfile, UserSettings

__all__ = [
    "User",
    "UserProfile",
    "UserSettings",
    "Gender",
    "Orientation",
    "Goal",
    "Education",
]
