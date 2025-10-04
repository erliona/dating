"""Telegram-specific repository implementations.

These adapters connect the core repository interfaces to the existing
bot database models and repository.
"""

from datetime import date
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from bot.repository import ProfileRepository as BotProfileRepository
from core.interfaces import IProfileRepository, IUserRepository
from core.models import User, UserProfile, UserSettings
from core.models.enums import Education, Gender, Goal, Orientation


class TelegramUserRepository(IUserRepository):
    """Telegram implementation of user repository.

    Bridges between core User model and Telegram-specific storage.
    """

    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session
        self.bot_repo = BotProfileRepository(session)

    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user by internal ID."""
        # Map from bot's user model to core User model
        bot_user = await self.bot_repo.get_user(user_id)
        if not bot_user:
            return None

        return User(
            id=bot_user.id,
            username=bot_user.username,
            first_name=bot_user.first_name,
            language_code=bot_user.language_code,
            is_premium=bot_user.is_premium,
            is_banned=bot_user.is_banned,
            created_at=bot_user.created_at,
            updated_at=bot_user.updated_at,
        )

    async def create_user(self, user: User) -> User:
        """Create new user."""
        # This is handled by bot's existing logic
        # For now, raise NotImplementedError as users are created via Telegram
        raise NotImplementedError("User creation is handled by Telegram adapter")

    async def update_user(self, user: User) -> User:
        """Update existing user."""
        # Update via bot repository
        bot_user = await self.bot_repo.get_user(user.id)
        if not bot_user:
            raise ValueError(f"User {user.id} not found")

        bot_user.username = user.username
        bot_user.first_name = user.first_name
        bot_user.language_code = user.language_code
        bot_user.is_premium = user.is_premium
        bot_user.is_banned = user.is_banned
        bot_user.updated_at = user.updated_at

        await self.session.commit()
        return user

    async def delete_user(self, user_id: int) -> bool:
        """Delete user."""
        return await self.bot_repo.delete_user(user_id)


class TelegramProfileRepository(IProfileRepository):
    """Telegram implementation of profile repository.

    Bridges between core UserProfile model and Telegram-specific storage.
    """

    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session
        self.bot_repo = BotProfileRepository(session)

    async def get_profile(self, user_id: int) -> Optional[UserProfile]:
        """Get user profile."""
        bot_profile = await self.bot_repo.get_profile_by_user_id(user_id)
        if not bot_profile:
            return None

        # Convert bot profile to core UserProfile
        return self._bot_profile_to_core(bot_profile)

    async def create_profile(self, profile: UserProfile) -> UserProfile:
        """Create new profile."""
        # Create via bot repository
        profile_dict = {
            "user_id": profile.user_id,
            "name": profile.name,
            "birth_date": profile.birth_date,
            "gender": profile.gender.value,
            "orientation": profile.orientation.value,
            "city": profile.city,
            "bio": profile.bio,
            "goal": profile.goal.value if profile.goal else None,
            "education": profile.education.value if profile.education else None,
            "work": profile.work,
            "company": profile.company,
            "school": profile.school,
            "height": profile.height,
            "interests": profile.interests,
            "languages": profile.languages,
            "geohash": profile.geohash,
            "latitude": profile.latitude,
            "longitude": profile.longitude,
            "photos": profile.photos,
        }

        bot_profile = await self.bot_repo.create_profile(**profile_dict)
        return self._bot_profile_to_core(bot_profile)

    async def update_profile(self, profile: UserProfile) -> UserProfile:
        """Update existing profile."""
        profile_dict = {
            "name": profile.name,
            "birth_date": profile.birth_date,
            "gender": profile.gender.value,
            "orientation": profile.orientation.value,
            "city": profile.city,
            "bio": profile.bio,
            "goal": profile.goal.value if profile.goal else None,
            "education": profile.education.value if profile.education else None,
            "work": profile.work,
            "company": profile.company,
            "school": profile.school,
            "height": profile.height,
            "interests": profile.interests,
            "languages": profile.languages,
            "geohash": profile.geohash,
            "latitude": profile.latitude,
            "longitude": profile.longitude,
            "photos": profile.photos,
            "is_visible": profile.is_visible,
        }

        bot_profile = await self.bot_repo.update_profile(profile.user_id, profile_dict)
        return self._bot_profile_to_core(bot_profile)

    async def delete_profile(self, user_id: int) -> bool:
        """Delete profile."""
        return await self.bot_repo.delete_profile(user_id)

    async def search_profiles(
        self, user_id: int, settings: UserSettings, limit: int = 10, offset: int = 0
    ) -> List[UserProfile]:
        """Search profiles based on user settings."""
        # Use bot's existing search logic
        bot_profiles = await self.bot_repo.find_candidates(
            user_id=user_id,
            min_age=settings.min_age,
            max_age=settings.max_age,
            orientation=settings.show_me.value,
            max_distance=settings.max_distance,
            limit=limit,
        )

        return [self._bot_profile_to_core(p) for p in bot_profiles]

    def _bot_profile_to_core(self, bot_profile) -> UserProfile:
        """Convert bot profile model to core UserProfile."""
        return UserProfile(
            user_id=bot_profile.user_id,
            name=bot_profile.name,
            birth_date=bot_profile.birth_date,
            gender=Gender(bot_profile.gender),
            orientation=Orientation(bot_profile.orientation),
            city=bot_profile.city,
            bio=bot_profile.bio,
            goal=Goal(bot_profile.goal) if bot_profile.goal else None,
            education=(
                Education(bot_profile.education) if bot_profile.education else None
            ),
            work=bot_profile.work,
            company=bot_profile.company,
            school=bot_profile.school,
            height=bot_profile.height,
            interests=bot_profile.interests or [],
            languages=bot_profile.languages or [],
            geohash=bot_profile.geohash,
            latitude=bot_profile.latitude,
            longitude=bot_profile.longitude,
            photos=bot_profile.photos or [],
            is_verified=bot_profile.is_verified,
            is_visible=bot_profile.is_visible,
            created_at=bot_profile.created_at,
            updated_at=bot_profile.updated_at,
        )
