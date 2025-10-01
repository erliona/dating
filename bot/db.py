"""Database models and repository helpers for the dating bot."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, Boolean, DateTime, String, Text, and_, func, or_, select
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.exc import DBAPIError, IntegrityError, OperationalError, SQLAlchemyError
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
    age_min: Mapped[Optional[int]] = mapped_column(default=None)
    age_max: Mapped[Optional[int]] = mapped_column(default=None)
    max_distance: Mapped[Optional[int]] = mapped_column(default=None)
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
        """Save or update a profile in the database.
        
        Args:
            profile: Profile object to save or update.
            
        Raises:
            IntegrityError: If there's a constraint violation.
            OperationalError: If there's a database connection issue.
            SQLAlchemyError: For other database-related errors.
        """
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
            except IntegrityError as exc:
                await session.rollback()
                LOGGER.error(
                    "Integrity constraint violation when saving profile for user_id=%s: %s",
                    profile.user_id, exc
                )
                raise
            except OperationalError as exc:
                await session.rollback()
                LOGGER.error(
                    "Database connection error when saving profile for user_id=%s: %s",
                    profile.user_id, exc
                )
                raise
            except SQLAlchemyError as exc:
                await session.rollback()
                LOGGER.exception(
                    "Database error when saving profile for user_id=%s: %s",
                    profile.user_id, exc
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

    async def find_best_matches(self, profile: "Profile", limit: int = 10) -> list["Profile"]:
        """Find best matching profiles based on compatibility score.
        
        Args:
            profile: Profile to find matches for.
            limit: Maximum number of matches to return.
            
        Returns:
            List of Profile objects sorted by compatibility (best first).
        """
        async with self._session_factory() as session:
            stmt = (
                select(ProfileModel)
                .where(ProfileModel.user_id != profile.user_id)
            )
            
            # Filter by mutual compatibility
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
            
            result = await session.execute(stmt)
            candidates = [model.to_profile() for model in result.scalars().all()]
            
            # Score and sort candidates
            if not candidates:
                return []
            
            scored_candidates = [
                (candidate, self._calculate_match_score(profile, candidate))
                for candidate in candidates
            ]
            scored_candidates.sort(key=lambda x: x[1], reverse=True)
            
            return [candidate for candidate, score in scored_candidates[:limit]]

    @staticmethod
    def _calculate_match_score(profile1: "Profile", profile2: "Profile") -> float:
        """Calculate compatibility score between two profiles.
        
        Args:
            profile1: First profile.
            profile2: Second profile.
            
        Returns:
            Score from 0.0 to 1.0, where 1.0 is perfect match.
        """
        score = 0.0
        max_score = 0.0
        
        # Interest similarity (weight: 0.4)
        max_score += 0.4
        if profile1.interests and profile2.interests:
            common_interests = set(profile1.interests) & set(profile2.interests)
            all_interests = set(profile1.interests) | set(profile2.interests)
            if all_interests:
                interest_score = len(common_interests) / len(all_interests)
                score += interest_score * 0.4
        
        # Location match (weight: 0.3)
        max_score += 0.3
        if profile1.location and profile2.location:
            # Exact match gets full score
            if profile1.location.lower() == profile2.location.lower():
                score += 0.3
            # Partial match (same word in location) gets partial score
            elif any(word in profile2.location.lower() 
                    for word in profile1.location.lower().split()):
                score += 0.15
        
        # Goal alignment (weight: 0.2)
        max_score += 0.2
        if profile1.goal and profile2.goal:
            if profile1.goal == profile2.goal:
                score += 0.2
            # Related goals get partial score
            elif {profile1.goal, profile2.goal} <= {"serious", "casual"}:
                score += 0.1
            elif {profile1.goal, profile2.goal} <= {"friendship", "networking"}:
                score += 0.1
        
        # Age compatibility (weight: 0.1)
        max_score += 0.1
        age_diff = abs(profile1.age - profile2.age)
        if age_diff <= 3:
            score += 0.1
        elif age_diff <= 5:
            score += 0.07
        elif age_diff <= 10:
            score += 0.03
        
        # Normalize to 0-1 range if max_score is not zero
        return score / max_score if max_score > 0 else 0.0


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
        """Create or update user settings.
        
        Args:
            user_id: User ID to save settings for.
            **settings: Settings key-value pairs to save.
            
        Returns:
            Updated UserSettingsModel instance.
            
        Raises:
            IntegrityError: If there's a constraint violation.
            OperationalError: If there's a database connection issue.
            SQLAlchemyError: For other database-related errors.
        """
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
            except IntegrityError as exc:
                await session.rollback()
                LOGGER.error(
                    "Integrity constraint violation when saving settings for user_id=%s: %s",
                    user_id, exc
                )
                raise
            except OperationalError as exc:
                await session.rollback()
                LOGGER.error(
                    "Database connection error when saving settings for user_id=%s: %s",
                    user_id, exc
                )
                raise
            except SQLAlchemyError as exc:
                await session.rollback()
                LOGGER.exception(
                    "Database error when saving settings for user_id=%s: %s",
                    user_id, exc
                )
                raise


class InteractionRepository:
    """Repository for user interactions (likes/dislikes)."""

    def __init__(self, session_factory: async_sessionmaker[AsyncSession]):
        self._session_factory = session_factory

    async def create(self, from_user_id: int, to_user_id: int, action: str) -> UserInteractionModel:
        """Create or update an interaction.
        
        Args:
            from_user_id: User ID who initiated the interaction.
            to_user_id: User ID who is the target of the interaction.
            action: Type of interaction ('like' or 'dislike').
            
        Returns:
            Created or updated UserInteractionModel instance.
            
        Raises:
            IntegrityError: If there's a constraint violation.
            OperationalError: If there's a database connection issue.
            SQLAlchemyError: For other database-related errors.
        """
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
            except IntegrityError as exc:
                await session.rollback()
                LOGGER.error(
                    "Integrity constraint violation when creating interaction from %s to %s: %s",
                    from_user_id, to_user_id, exc
                )
                raise
            except OperationalError as exc:
                await session.rollback()
                LOGGER.error(
                    "Database connection error when creating interaction from %s to %s: %s",
                    from_user_id, to_user_id, exc
                )
                raise
            except SQLAlchemyError as exc:
                await session.rollback()
                LOGGER.exception(
                    "Database error when creating interaction from %s to %s: %s",
                    from_user_id, to_user_id, exc
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
        """Check if both users liked each other.
        
        Optimized to use a single query with COUNT instead of two separate queries.
        """
        async with self._session_factory() as session:
            # Use a single query to count both likes
            stmt = select(func.count()).select_from(UserInteractionModel).where(
                or_(
                    and_(
                        UserInteractionModel.from_user_id == user1_id,
                        UserInteractionModel.to_user_id == user2_id,
                        UserInteractionModel.action == "like"
                    ),
                    and_(
                        UserInteractionModel.from_user_id == user2_id,
                        UserInteractionModel.to_user_id == user1_id,
                        UserInteractionModel.action == "like"
                    )
                )
            )
            count = await session.scalar(stmt)
            # Both users must have liked each other (count == 2)
            return count == 2

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
        """Create a match between two users. Ensures user1_id < user2_id.
        
        Args:
            user1_id: First user ID.
            user2_id: Second user ID.
            
        Returns:
            Created or existing MatchModel instance.
            
        Raises:
            IntegrityError: If there's a constraint violation.
            OperationalError: If there's a database connection issue.
            SQLAlchemyError: For other database-related errors.
        """
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
            except IntegrityError as exc:
                await session.rollback()
                LOGGER.error(
                    "Integrity constraint violation when creating match between %s and %s: %s",
                    user1_id, user2_id, exc
                )
                raise
            except OperationalError as exc:
                await session.rollback()
                LOGGER.error(
                    "Database connection error when creating match between %s and %s: %s",
                    user1_id, user2_id, exc
                )
                raise
            except SQLAlchemyError as exc:
                await session.rollback()
                LOGGER.exception(
                    "Database error when creating match between %s and %s: %s",
                    user1_id, user2_id, exc
                )
                raise

    async def get_matches(self, user_id: int) -> list[int]:
        """Get list of user IDs that matched with this user.
        
        Optimized to use SQL CASE expression instead of Python loop.
        """
        async with self._session_factory() as session:
            from sqlalchemy import case
            
            # Use CASE to select the other user's ID directly in SQL
            other_user_id = case(
                (MatchModel.user1_id == user_id, MatchModel.user2_id),
                else_=MatchModel.user1_id
            )
            
            stmt = select(other_user_id).where(
                or_(
                    MatchModel.user1_id == user_id,
                    MatchModel.user2_id == user_id
                )
            )
            
            result = await session.execute(stmt)
            return [row[0] for row in result]

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

    async def get_user_stats(self, user_id: int) -> dict[str, int]:
        """Get statistics for a user.
        
        Args:
            user_id: User ID to get stats for.
            
        Returns:
            Dictionary with stats: matches_count, likes_sent, likes_received, dislikes_sent.
        """
        async with self._session_factory() as session:
            # Count matches
            matches_stmt = select(func.count()).select_from(MatchModel).where(
                or_(
                    MatchModel.user1_id == user_id,
                    MatchModel.user2_id == user_id
                )
            )
            matches_count = await session.scalar(matches_stmt) or 0
            
            # Count likes sent
            likes_sent_stmt = select(func.count()).select_from(UserInteractionModel).where(
                and_(
                    UserInteractionModel.from_user_id == user_id,
                    UserInteractionModel.action == "like"
                )
            )
            likes_sent = await session.scalar(likes_sent_stmt) or 0
            
            # Count likes received
            likes_received_stmt = select(func.count()).select_from(UserInteractionModel).where(
                and_(
                    UserInteractionModel.to_user_id == user_id,
                    UserInteractionModel.action == "like"
                )
            )
            likes_received = await session.scalar(likes_received_stmt) or 0
            
            # Count dislikes sent
            dislikes_sent_stmt = select(func.count()).select_from(UserInteractionModel).where(
                and_(
                    UserInteractionModel.from_user_id == user_id,
                    UserInteractionModel.action == "dislike"
                )
            )
            dislikes_sent = await session.scalar(dislikes_sent_stmt) or 0
            
            return {
                "matches_count": matches_count,
                "likes_sent": likes_sent,
                "likes_received": likes_received,
                "dislikes_sent": dislikes_sent,
            }

