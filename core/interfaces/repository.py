"""Repository interfaces for data access - platform agnostic."""

from abc import ABC, abstractmethod
from typing import Optional, List

from ..models import User, UserProfile, UserSettings


class IUserRepository(ABC):
    """Interface for user data access."""
    
    @abstractmethod
    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user by internal ID."""
        pass
    
    @abstractmethod
    async def create_user(self, user: User) -> User:
        """Create new user."""
        pass
    
    @abstractmethod
    async def update_user(self, user: User) -> User:
        """Update existing user."""
        pass
    
    @abstractmethod
    async def delete_user(self, user_id: int) -> bool:
        """Delete user."""
        pass


class IProfileRepository(ABC):
    """Interface for profile data access."""
    
    @abstractmethod
    async def get_profile(self, user_id: int) -> Optional[UserProfile]:
        """Get user profile."""
        pass
    
    @abstractmethod
    async def create_profile(self, profile: UserProfile) -> UserProfile:
        """Create new profile."""
        pass
    
    @abstractmethod
    async def update_profile(self, profile: UserProfile) -> UserProfile:
        """Update existing profile."""
        pass
    
    @abstractmethod
    async def delete_profile(self, user_id: int) -> bool:
        """Delete profile."""
        pass
    
    @abstractmethod
    async def search_profiles(
        self,
        user_id: int,
        settings: UserSettings,
        limit: int = 10,
        offset: int = 0
    ) -> List[UserProfile]:
        """Search profiles based on user settings."""
        pass
