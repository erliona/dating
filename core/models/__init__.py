"""Core domain models - platform independent."""

from .user import User, UserProfile, UserSettings
from .enums import Gender, Orientation, Goal, Education

__all__ = [
    "User",
    "UserProfile", 
    "UserSettings",
    "Gender",
    "Orientation",
    "Goal",
    "Education",
]
