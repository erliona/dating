"""Database models and repository helpers for the dating bot."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, Boolean, DateTime, String, Text, and_, func, or_, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

if TYPE_CHECKING:  # pragma: no cover - only for type checking
    from .main import Profile


LOGGER = logging.getLogger(__name__)


class Base(DeclarativeBase):
    """Base class for ORM models."""


INTERESTS_TYPE = MutableList.as_mutable(
    JSONB().with_variant(SQLITE_JSON(), "sqlite")
)


class ProfileModel(Base):
    """ORM representation of a user profile."""

    __tablename__ = "profiles"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    name: Mapped[str] = mapped_column(String(255))
    age: Mapped[int]
    gender: Mapped[str] = mapped_column(String(16))
    preference: Mapped[str] = mapped_column(String(16))
    bio: Mapped[Optional[str]] = mapped_column(Text(), default=None)
    location: Mapped[Optional[str]] = mapped_column(String(255), default=None)
    interests: Mapped[list[str]] = mapped_column(
        INTERESTS_TYPE, default=list, nullable=False
    )
    goal: Mapped[Optional[str]] = mapped_column(String(32), default=None)
    photo_file_id: Mapped[Optional[str]] = mapped_column(String(255), default=None)
    photo_url: Mapped[Optional[str]] = mapped_column(Text(), default=None)

    def to_profile(self) -> "Profile":
        from .main import Profile

        return Profile(
            user_id=self.user_id,
            name=self.name,
            age=self.age,
            gender=self.gender,
            preference=self.preference,
            bio=self.bio,
            location=self.location,
            interests=list(self.interests or []),
            goal=self.goal,
            photo_file_id=self.photo_file_id,
            photo_url=self.photo_url,
        )

    def update_from_profile(self, profile: "Profile") -> None:
        self.name = profile.name
        self.age = profile.age
        self.gender = profile.gender
        self.preference = profile.preference
        self.bio = profile.bio
        self.location = profile.location
        self.interests = list(profile.interests)
        self.goal = profile.goal
        self.photo_file_id = profile.photo_file_id
        self.photo_url = profile.photo_url

    @classmethod
    def from_profile(cls, profile: "Profile") -> "ProfileModel":
        instance = cls(
            user_id=profile.user_id,
            name=profile.name,
            age=profile.age,
            gender=profile.gender,
            preference=profile.preference,
            bio=profile.bio,
            location=profile.location,
            interests=list(profile.interests),
            goal=profile.goal,
            photo_file_id=profile.photo_file_id,
            photo_url=profile.photo_url,
        )
        return instance


class UserSettingsModel(Base):
    """ORM representation of user settings."""

    __tablename__ = "user_settings"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True)
    lang: Mapped[str] = mapped_column(String(10), default="ru", server_default="ru")
    show_location: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    show_age: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    notify_matches: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    notify_messages: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), server_default=func.now(), onupdate=func.now())


class UserInteractionModel(Base):
    """ORM representation of user interactions (likes/dislikes)."""

    __tablename__ = "user_interactions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    from_user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    to_user_id: Mapped[int] = mapped_column(BigInteger, index=True)
    action: Mapped[str] = mapped_column(String(16))  # 'like' or 'dislike'
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), server_default=func.now())


class MatchModel(Base):
    """ORM representation of matches between users."""

    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user1_id: Mapped[int] = mapped_column(BigInteger, index=True)
    user2_id: Mapped[int] = mapped_column(BigInteger, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), server_default=func.now())


class ProfileRepository:
    """Persistence layer backed by PostgreSQL."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def upsert(self, profile: "Profile") -> None:
        async with self._session_factory() as session:
            try:
                instance = await session.scalar(
                    select(ProfileModel).where(ProfileModel.user_id == profile.user_id)
                )
                if instance:
                    instance.update_from_profile(profile)
                else:
                    session.add(ProfileModel.from_profile(profile))
                await session.commit()
                LOGGER.info(
                    "Profile for user_id=%s has been saved successfully", profile.user_id
                )
            except Exception:
                await session.rollback()
                LOGGER.exception(
                    "Failed to save profile for user_id=%s", profile.user_id
                )
                raise

    async def get(self, user_id: int) -> Optional["Profile"]:
        async with self._session_factory() as session:
            instance = await session.scalar(
                select(ProfileModel).where(ProfileModel.user_id == user_id)
            )
            return instance.to_profile() if instance else None

    async def delete(self, user_id: int) -> bool:
        """Delete a profile by user_id. Returns True if deleted, False if not found."""
        async with self._session_factory() as session:
            async with session.begin():
                instance = await session.scalar(
                    select(ProfileModel).where(ProfileModel.user_id == user_id)
                )
                if instance:
                    await session.delete(instance)
                    LOGGER.info("Profile for user_id=%s has been deleted", user_id)
                    return True
                return False

    async def find_mutual_match(self, profile: "Profile") -> Optional["Profile"]:
        async with self._session_factory() as session:
            stmt = (
                select(ProfileModel)
                .where(ProfileModel.user_id != profile.user_id)
            )
            
            # Filter by mutual compatibility to reduce candidates
            if profile.preference != "any":
                stmt = stmt.where(ProfileModel.gender == profile.preference)
            
            # Also check if the candidate would be interested in this profile
            if profile.gender != "other":
                stmt = stmt.where(
                    (ProfileModel.preference == profile.gender) | (ProfileModel.preference == "any")
                )
            else:
                stmt = stmt.where(
                    (ProfileModel.preference == "other") | (ProfileModel.preference == "any")
                )
            
            # Limit to first match for performance
            stmt = stmt.limit(1)
            
            result = await session.scalar(stmt)
            return result.to_profile() if result else None


class UserSettingsRepository:
    """Repository for user settings."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def get(self, user_id: int) -> Optional[UserSettingsModel]:
        """Get user settings by user_id."""
        async with self._session_factory() as session:
            result = await session.scalar(
                select(UserSettingsModel).where(UserSettingsModel.user_id == user_id)
            )
            return result

    async def upsert(self, user_id: int, **settings) -> UserSettingsModel:
        """Create or update user settings."""
        async with self._session_factory() as session:
            try:
                instance = await session.scalar(
                    select(UserSettingsModel).where(UserSettingsModel.user_id == user_id)
                )
                if instance:
                    for key, value in settings.items():
                        if hasattr(instance, key):
                            setattr(instance, key, value)
                    instance.updated_at = func.now()
                else:
                    instance = UserSettingsModel(user_id=user_id, **settings)
                    session.add(instance)
                await session.commit()
                await session.refresh(instance)
                LOGGER.info("Settings for user_id=%s saved successfully", user_id)
                return instance
            except Exception:
                await session.rollback()
                LOGGER.exception("Failed to save settings for user_id=%s", user_id)
                raise


class InteractionRepository:
    """Repository for user interactions (likes/dislikes)."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def create(self, from_user_id: int, to_user_id: int, action: str) -> UserInteractionModel:
        """Create or update an interaction."""
        async with self._session_factory() as session:
            try:
                # Check if interaction already exists
                existing = await session.scalar(
                    select(UserInteractionModel).where(
                        and_(
                            UserInteractionModel.from_user_id == from_user_id,
                            UserInteractionModel.to_user_id == to_user_id
                        )
                    )
                )
                
                if existing:
                    # Update existing interaction
                    existing.action = action
                    existing.created_at = func.now()
                    interaction = existing
                else:
                    # Create new interaction
                    interaction = UserInteractionModel(
                        from_user_id=from_user_id,
                        to_user_id=to_user_id,
                        action=action
                    )
                    session.add(interaction)
                
                await session.commit()
                await session.refresh(interaction)
                LOGGER.info(
                    "Interaction created: user %s %s user %s",
                    from_user_id, action, to_user_id
                )
                return interaction
            except Exception:
                await session.rollback()
                LOGGER.exception(
                    "Failed to create interaction from %s to %s",
                    from_user_id, to_user_id
                )
                raise

    async def get_interaction(self, from_user_id: int, to_user_id: int) -> Optional[UserInteractionModel]:
        """Get an interaction between two users."""
        async with self._session_factory() as session:
            result = await session.scalar(
                select(UserInteractionModel).where(
                    and_(
                        UserInteractionModel.from_user_id == from_user_id,
                        UserInteractionModel.to_user_id == to_user_id
                    )
                )
            )
            return result

    async def check_mutual_like(self, user1_id: int, user2_id: int) -> bool:
        """Check if both users liked each other."""
        async with self._session_factory() as session:
            like1 = await session.scalar(
                select(UserInteractionModel).where(
                    and_(
                        UserInteractionModel.from_user_id == user1_id,
                        UserInteractionModel.to_user_id == user2_id,
                        UserInteractionModel.action == "like"
                    )
                )
            )
            
            like2 = await session.scalar(
                select(UserInteractionModel).where(
                    and_(
                        UserInteractionModel.from_user_id == user2_id,
                        UserInteractionModel.to_user_id == user1_id,
                        UserInteractionModel.action == "like"
                    )
                )
            )
            
            return like1 is not None and like2 is not None

    async def get_liked_users(self, user_id: int) -> list[int]:
        """Get list of user IDs that this user has liked."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(UserInteractionModel.to_user_id).where(
                    and_(
                        UserInteractionModel.from_user_id == user_id,
                        UserInteractionModel.action == "like"
                    )
                )
            )
            return [row[0] for row in result]

    async def get_disliked_users(self, user_id: int) -> list[int]:
        """Get list of user IDs that this user has disliked."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(UserInteractionModel.to_user_id).where(
                    and_(
                        UserInteractionModel.from_user_id == user_id,
                        UserInteractionModel.action == "dislike"
                    )
                )
            )
            return [row[0] for row in result]


class MatchRepository:
    """Repository for matches."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def create(self, user1_id: int, user2_id: int) -> MatchModel:
        """Create a match between two users. Ensures user1_id < user2_id."""
        # Normalize order
        if user1_id > user2_id:
            user1_id, user2_id = user2_id, user1_id
        
        async with self._session_factory() as session:
            try:
                # Check if match already exists
                existing = await session.scalar(
                    select(MatchModel).where(
                        and_(
                            MatchModel.user1_id == user1_id,
                            MatchModel.user2_id == user2_id
                        )
                    )
                )
                
                if existing:
                    return existing
                
                # Create new match
                match = MatchModel(user1_id=user1_id, user2_id=user2_id)
                session.add(match)
                await session.commit()
                await session.refresh(match)
                LOGGER.info("Match created between users %s and %s", user1_id, user2_id)
                return match
            except Exception:
                await session.rollback()
                LOGGER.exception(
                    "Failed to create match between %s and %s",
                    user1_id, user2_id
                )
                raise

    async def get_matches(self, user_id: int) -> list[int]:
        """Get list of user IDs that matched with this user."""
        async with self._session_factory() as session:
            result = await session.execute(
                select(MatchModel).where(
                    or_(
                        MatchModel.user1_id == user_id,
                        MatchModel.user2_id == user_id
                    )
                )
            )
            matches = result.scalars().all()
            
            # Extract the other user's ID from each match
            matched_users = []
            for match in matches:
                if match.user1_id == user_id:
                    matched_users.append(match.user2_id)
                else:
                    matched_users.append(match.user1_id)
            
            return matched_users

    async def is_matched(self, user1_id: int, user2_id: int) -> bool:
        """Check if two users are matched."""
        # Normalize order
        if user1_id > user2_id:
            user1_id, user2_id = user2_id, user1_id
        
        async with self._session_factory() as session:
            result = await session.scalar(
                select(MatchModel).where(
                    and_(
                        MatchModel.user1_id == user1_id,
                        MatchModel.user2_id == user2_id
                    )
                )
            )
            return result is not None
