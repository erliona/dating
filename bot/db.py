"""Database models and repository helpers for the dating bot."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Optional

from sqlalchemy import BigInteger, String, Text, select
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

    async def find_mutual_match(self, profile: "Profile") -> Optional["Profile"]:
        async with self._session_factory() as session:
            stmt = select(ProfileModel).where(ProfileModel.user_id != profile.user_id)
            if profile.preference != "any":
                stmt = stmt.where(ProfileModel.gender == profile.preference)
            candidates = await session.scalars(stmt)
            for candidate in candidates:
                candidate_profile = candidate.to_profile()
                if self._is_compatible(profile, candidate_profile) and self._is_compatible(
                    candidate_profile, profile
                ):
                    return candidate_profile
            return None

    @staticmethod
    def _is_compatible(profile: "Profile", other: "Profile") -> bool:
        return other.gender == profile.preference or profile.preference == "any"
