from __future__ import annotations

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
    DateTime,
    Float,
    Index,
    Integer,
    JSON,
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
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False, index=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    language_code: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    is_premium: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_banned: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


class Profile(Base):
    """Profile table - stores user dating profile information."""

    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True, index=True)

    # Basic information
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    birth_date: Mapped[date] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(String(20), nullable=False)
    orientation: Mapped[str] = mapped_column(String(20), nullable=False)
    goal: Mapped[str] = mapped_column(String(50), nullable=False)
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # Interests - stored as array
    interests: Mapped[Optional[list[str]]] = mapped_column(ARRAY(String(50)), nullable=True)

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
    geohash: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, index=True)
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
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Constraints
    __table_args__ = (
        CheckConstraint("birth_date <= CURRENT_DATE", name="birth_date_not_future"),
        CheckConstraint(
            "height_cm IS NULL OR (height_cm >= 100 AND height_cm <= 250)",
            name="height_cm_range",
        ),
        CheckConstraint("gender IN ('male', 'female', 'other')", name="valid_gender"),
        CheckConstraint("orientation IN ('male', 'female', 'any')", name="valid_orientation"),
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
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        CheckConstraint("sort_order >= 0 AND sort_order <= 2", name="sort_order_range"),
        CheckConstraint("safe_score >= 0.0 AND safe_score <= 1.0", name="safe_score_range"),
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
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
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
        DateTime(timezone=True), server_default=func.now(), nullable=False
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
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("user_id", "target_id", name="unique_user_favorite"),
        Index("idx_favorites_user_id", "user_id"),
        Index("idx_favorites_target_id", "target_id"),
    )


class Admin(Base):
    """Admin table - stores admin users with authentication."""

    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(
        String(255), unique=True, nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_super_admin: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    last_login: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )


# New models for MVP features

class Conversation(Base):
    """Conversation table - stores chat conversations between matched users."""

    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    match_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    user1_id: Mapped[int] = mapped_column(Integer, nullable=False)
    user2_id: Mapped[int] = mapped_column(Integer, nullable=False)
    last_message_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    unread_count_user1: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unread_count_user2: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    blocked_by_user_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("user1_id < user2_id", name="user1_less_than_user2"),
        Index("idx_conversations_user1", "user1_id"),
        Index("idx_conversations_user2", "user2_id"),
        Index("idx_conversations_match_id", "match_id"),
    )


class Message(Base):
    """Message table - stores chat messages."""

    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    conversation_id: Mapped[int] = mapped_column(Integer, nullable=False)
    sender_id: Mapped[int] = mapped_column(Integer, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    content_type: Mapped[str] = mapped_column(String(20), default="text", nullable=False)
    media_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "content_type IN ('text', 'photo', 'voice', 'system')",
            name="valid_content_type",
        ),
        Index("idx_messages_conversation_id", "conversation_id"),
        Index("idx_messages_sender_id", "sender_id"),
        Index("idx_messages_created_at", "created_at"),
    )


class Notification(Base):
    """Notification table - stores push notifications."""

    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    notification_type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    data: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_sent: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "notification_type IN ('new_match', 'new_message', 'new_like', 'verification_complete', 'verification_rejected')",
            name="valid_notification_type",
        ),
        Index("idx_notifications_user_id", "user_id"),
        Index("idx_notifications_type", "notification_type"),
        Index("idx_notifications_created_at", "created_at"),
    )


class Report(Base):
    """Report table - stores user reports for moderation."""

    __tablename__ = "reports"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    reporter_id: Mapped[int] = mapped_column(Integer, nullable=False)
    reported_user_id: Mapped[int] = mapped_column(Integer, nullable=False)
    report_type: Mapped[str] = mapped_column(String(50), nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    context: Mapped[str] = mapped_column(String(20), default="profile", nullable=False)
    context_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False)
    admin_notes: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resolved_by_admin_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    resolved_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    action_taken: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint(
            "report_type IN ('spam', 'inappropriate_content', 'fake_profile', 'harassment', 'underage', 'other')",
            name="valid_report_type",
        ),
        CheckConstraint(
            "context IN ('profile', 'chat', 'photo')",
            name="valid_context",
        ),
        CheckConstraint(
            "status IN ('pending', 'investigating', 'resolved', 'dismissed')",
            name="valid_status",
        ),
        CheckConstraint(
            "action_taken IN ('warned', 'banned_1d', 'banned_7d', 'banned_permanent', 'profile_hidden', 'photo_removed', 'no_action')",
            name="valid_action_taken",
        ),
        UniqueConstraint("reporter_id", "reported_user_id", "context", "context_id", name="unique_report"),
        Index("idx_reports_reporter_id", "reporter_id"),
        Index("idx_reports_reported_user_id", "reported_user_id"),
        Index("idx_reports_status", "status"),
        Index("idx_reports_created_at", "created_at"),
    )


class UserPreferences(Base):
    """User preferences table - stores user search preferences."""

    __tablename__ = "user_preferences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    min_age: Mapped[int] = mapped_column(Integer, default=18, nullable=False)
    max_age: Mapped[int] = mapped_column(Integer, default=55, nullable=False)
    preferred_gender: Mapped[str] = mapped_column(String(20), default="any", nullable=False)
    max_distance_km: Mapped[int] = mapped_column(Integer, default=50, nullable=False)
    show_verified_only: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    show_active_only: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("min_age >= 18 AND min_age <= 100", name="valid_min_age"),
        CheckConstraint("max_age >= 18 AND max_age <= 100", name="valid_max_age"),
        CheckConstraint("min_age <= max_age", name="min_age_less_than_max_age"),
        CheckConstraint("max_distance_km >= 1 AND max_distance_km <= 1000", name="valid_max_distance"),
        CheckConstraint("preferred_gender IN ('male', 'female', 'any')", name="valid_preferred_gender"),
        Index("idx_user_preferences_user_id", "user_id"),
    )


class UserActivity(Base):
    """User activity table - tracks user activity and statistics."""

    __tablename__ = "user_activity"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    last_active_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    last_location_update_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    total_swipes: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_likes_given: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_likes_received: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_matches: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    daily_superlikes_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    last_superlike_reset_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        CheckConstraint("total_swipes >= 0", name="valid_total_swipes"),
        CheckConstraint("total_likes_given >= 0", name="valid_likes_given"),
        CheckConstraint("total_likes_received >= 0", name="valid_likes_received"),
        CheckConstraint("total_matches >= 0", name="valid_total_matches"),
        CheckConstraint("daily_superlikes_used >= 0 AND daily_superlikes_used <= 5", name="valid_daily_superlikes"),
        Index("idx_user_activity_user_id", "user_id"),
        Index("idx_user_activity_last_active", "last_active_at"),
    )


class Like(Base):
    """Like table - tracks who liked whom (separate from interactions for 'who liked you' feature)."""

    __tablename__ = "likes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    liker_id: Mapped[int] = mapped_column(Integer, nullable=False)
    liked_id: Mapped[int] = mapped_column(Integer, nullable=False)
    like_type: Mapped[str] = mapped_column(String(20), default="like", nullable=False)
    is_viewed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    __table_args__ = (
        CheckConstraint(
            "like_type IN ('like', 'superlike')",
            name="valid_like_type",
        ),
        UniqueConstraint("liker_id", "liked_id", name="unique_like_pair"),
        Index("idx_likes_liker_id", "liker_id"),
        Index("idx_likes_liked_id", "liked_id"),
        Index("idx_likes_created_at", "created_at"),
    )
