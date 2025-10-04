"""User service - core business logic for user management."""

from datetime import datetime, timezone
from typing import Optional

from ..interfaces import IUserRepository
from ..models import User


class UserService:
    """Service for user management - platform independent.

    This service contains all business logic related to users,
    independent of any platform (Telegram, mobile, etc.).
    """

    def __init__(self, user_repository: IUserRepository):
        """Initialize service with repository interface."""
        self.user_repository = user_repository

    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID."""
        return await self.user_repository.get_user(user_id)

    async def create_user(
        self,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        language_code: Optional[str] = None,
        is_premium: bool = False,
    ) -> User:
        """Create new user.

        Business logic:
        - Set default values
        - Set creation timestamp
        - Validate username format (if provided)
        """
        # Username validation
        if username:
            username = username.strip()
            if not username or len(username) > 255:
                raise ValueError("Invalid username length")

        user = User(
            id=0,  # Will be set by repository
            username=username,
            first_name=first_name,
            language_code=language_code,
            is_premium=is_premium,
            is_banned=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )

        return await self.user_repository.create_user(user)

    async def update_user(
        self,
        user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        language_code: Optional[str] = None,
        is_premium: Optional[bool] = None,
    ) -> Optional[User]:
        """Update user information."""
        user = await self.user_repository.get_user(user_id)
        if not user:
            return None

        # Update fields if provided
        if username is not None:
            user.username = username.strip() if username else None
        if first_name is not None:
            user.first_name = first_name
        if language_code is not None:
            user.language_code = language_code
        if is_premium is not None:
            user.is_premium = is_premium

        user.updated_at = datetime.now(timezone.utc)

        return await self.user_repository.update_user(user)

    async def ban_user(self, user_id: int) -> bool:
        """Ban user.

        Business logic:
        - Mark user as banned
        - Update timestamp
        """
        user = await self.user_repository.get_user(user_id)
        if not user:
            return False

        user.is_banned = True
        user.updated_at = datetime.now(timezone.utc)

        await self.user_repository.update_user(user)
        return True

    async def unban_user(self, user_id: int) -> bool:
        """Unban user."""
        user = await self.user_repository.get_user(user_id)
        if not user:
            return False

        user.is_banned = False
        user.updated_at = datetime.now(timezone.utc)

        await self.user_repository.update_user(user)
        return True

    async def delete_user(self, user_id: int) -> bool:
        """Delete user.

        Business logic:
        - Check if user exists
        - Perform deletion
        """
        return await self.user_repository.delete_user(user_id)
