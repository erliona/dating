"""Core user domain models - platform independent."""

from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from typing import List, Optional

from .enums import Education, Gender, Goal, Orientation


@dataclass
class User:
    """Core user entity - platform agnostic.

    This represents a user in the system, independent of any platform (Telegram, mobile, etc.).
    Platform-specific IDs should be stored in adapters.
    """

    id: int
    username: Optional[str] = None
    first_name: Optional[str] = None
    language_code: Optional[str] = None
    is_premium: bool = False
    is_banned: bool = False
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class UserProfile:
    """User profile with dating information - platform agnostic."""

    user_id: int
    name: str
    birth_date: date
    gender: Gender
    orientation: Orientation
    city: str

    # Optional fields
    bio: Optional[str] = None
    goal: Optional[Goal] = None
    education: Optional[Education] = None
    work: Optional[str] = None
    company: Optional[str] = None
    school: Optional[str] = None
    height: Optional[int] = None

    # Interests and lifestyle
    interests: List[str] = field(default_factory=list)
    languages: List[str] = field(default_factory=list)

    # Location (using geohash for privacy)
    geohash: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    # Photo URLs (stored separately in media service)
    photos: List[str] = field(default_factory=list)

    # Metadata
    is_verified: bool = False
    is_visible: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def age(self) -> int:
        """Calculate age from birth date."""
        today = date.today()
        return (
            today.year
            - self.birth_date.year
            - ((today.month, today.day) < (self.birth_date.month, self.birth_date.day))
        )


@dataclass
class UserSettings:
    """User preference settings - platform agnostic."""

    user_id: int

    # Discovery preferences
    min_age: int = 18
    max_age: int = 99
    max_distance: int = 50  # km
    show_me: Orientation = Orientation.ANY

    # Privacy settings
    show_online: bool = True
    show_distance: bool = True
    show_age: bool = True

    # Notification preferences (platform adapters will handle actual notifications)
    notify_matches: bool = True
    notify_messages: bool = True
    notify_likes: bool = True

    # Content preferences
    nsfw_filter: bool = True

    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
