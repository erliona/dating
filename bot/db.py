"""Database models for Dating Mini App."""

from datetime import date, datetime
from enum import Enum
from typing import Optional

from sqlalchemy import (
    ARRAY,
    BigInteger,
    Boolean,
    CheckConstraint,
    Date,
    Float,
    Index,
    Integer,
    SmallInteger,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class Gender(str, Enum):
    """Gender enum."""

    MALE = "male"
    FEMALE = "female"
    OTHER = "other"


class Orientation(str, Enum):
    """Orientation enum."""

    MALE = "male"
    FEMALE = "female"
    ANY = "any"


class Goal(str, Enum):
    """Relationship goal enum."""

    FRIENDSHIP = "friendship"
    DATING = "dating"
    RELATIONSHIP = "relationship"
    NETWORKING = "networking"
    SERIOUS = "serious"
    CASUAL = "casual"


class Education(str, Enum):
    """Education level enum."""

    HIGH_SCHOOL = "high_school"
    BACHELOR = "bachelor"
    MASTER = "master"
    PHD = "phd"
    OTHER = "other"


class User(Base):
    """User table - stores Telegram user data."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    tg_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, nullable=False, index=True
    )
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    language_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )


class Profile(Base):
    """Profile table - stores user dating profile information."""

    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer, nullable=False, unique=True, index=True
    )

    # Basic information
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(String(20), nullable=False)
    orientation: Mapped[str] = mapped_column(String(20), nullable=False)
    goal: Mapped[str] = mapped_column(String(50), nullable=False)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Interests - stored as array
    interests: Mapped[Optional[list[str]]] = mapped_column(
        ARRAY(String(50)), nullable=True
    )

    # Optional profile details
    height_cm: Mapped[Optional[int]] = mapped_column(SmallInteger, nullable=True)
    education: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    has_children: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    wants_children: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    smoking: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)
    drinking: Mapped[Optional[bool]] = mapped_column(Boolean, nullable=True)

    # Location - geohash for privacy
    country: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    geohash: Mapped[Optional[str]] = mapped_column(
        String(20), nullable=True, index=True
    )
    latitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    longitude: Mapped[Optional[float]] = mapped_column(Float, nullable=True)

    # Privacy settings
    hide_distance: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    hide_online: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    hide_age: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    allow_messages_from: Mapped[str] = mapped_column(
        String(20), default="matches", nullable=False
    )  # "matches" or "anyone"

    # Profile status
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_complete: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("birth_date <= CURRENT_DATE", name="birth_date_not_future"),
        CheckConstraint(
            "height_cm IS NULL OR (height_cm >= 100 AND height_cm <= 250)",
            name="height_cm_range",
        ),
        CheckConstraint("gender IN ('male', 'female', 'other')", name="valid_gender"),
        CheckConstraint(
            "orientation IN ('male', 'female', 'any')", name="valid_orientation"
        ),
        CheckConstraint(
            "goal IN ('friendship', 'dating', 'relationship', 'networking', 'serious', 'casual')",
            name="valid_goal",
        ),
        CheckConstraint(
            "allow_messages_from IN ('matches', 'anyone')",
            name="valid_allow_messages_from",
        ),
        Index("idx_profiles_geohash", "geohash"),
        Index("idx_profiles_user_id", "user_id"),
    )


class Photo(Base):
    """Photo table - stores user profile photos."""

    __tablename__ = "photos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    sort_order: Mapped[int] = mapped_column(SmallInteger, default=0, nullable=False)

    # NSFW detection score (0.0 = safe, 1.0 = explicit)
    safe_score: Mapped[float] = mapped_column(Float, default=1.0, nullable=False)

    # File metadata
    file_size: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    mime_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    width: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    height: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Status
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    __table_args__ = (
        CheckConstraint("sort_order >= 0 AND sort_order <= 2", name="sort_order_range"),
        CheckConstraint(
            "safe_score >= 0.0 AND safe_score <= 1.0", name="safe_score_range"
        ),
        Index("idx_photos_user_id_sort", "user_id", "sort_order"),
    )


class InteractionType(str, Enum):
    """Interaction type enum."""

    LIKE = "like"
    SUPERLIKE = "superlike"
    PASS = "pass"


class Interaction(Base):
    """Interaction table - stores likes, superlikes, and passes."""

    __tablename__ = "interactions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    target_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    interaction_type: Mapped[str] = mapped_column(String(20), nullable=False)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("user_id", "target_id", name="unique_user_target_interaction"),
        CheckConstraint(
            "interaction_type IN ('like', 'superlike', 'pass')",
            name="valid_interaction_type",
        ),
        Index("idx_interactions_user_id", "user_id"),
        Index("idx_interactions_target_id", "target_id"),
        Index("idx_interactions_user_target", "user_id", "target_id"),
    )


class Match(Base):
    """Match table - stores mutual matches between users."""

    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user1_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    user2_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("user1_id", "user2_id", name="unique_match_pair"),
        CheckConstraint("user1_id < user2_id", name="user1_less_than_user2"),
        Index("idx_matches_user1", "user1_id"),
        Index("idx_matches_user2", "user2_id"),
    )


class Favorite(Base):
    """Favorite table - stores user's favorite profiles."""

    __tablename__ = "favorites"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)
    target_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("user_id", "target_id", name="unique_user_favorite"),
        Index("idx_favorites_user_id", "user_id"),
        Index("idx_favorites_target_id", "target_id"),
    )
