"""Profile service - core business logic for user profiles."""

from typing import Optional, List
from datetime import datetime, date, timezone

from ..models import UserProfile, UserSettings, Gender, Orientation, Goal, Education
from ..interfaces import IProfileRepository


class ProfileService:
    """Service for profile management - platform independent.
    
    This service contains all business logic related to user profiles,
    independent of any platform (Telegram, mobile, etc.).
    """
    
    def __init__(self, profile_repository: IProfileRepository):
        """Initialize service with repository interface."""
        self.profile_repository = profile_repository
    
    async def get_profile(self, user_id: int) -> Optional[UserProfile]:
        """Get user profile."""
        return await self.profile_repository.get_profile(user_id)
    
    async def create_profile(
        self,
        user_id: int,
        name: str,
        birth_date: date,
        gender: Gender,
        orientation: Orientation,
        city: str,
        bio: Optional[str] = None,
        **kwargs
    ) -> UserProfile:
        """Create new user profile.
        
        Business logic:
        - Validate required fields
        - Validate age (must be 18+)
        - Set default values
        - Set creation timestamp
        """
        # Validate name
        name = name.strip()
        if not name or len(name) < 2:
            raise ValueError("Name must be at least 2 characters")
        if len(name) > 100:
            raise ValueError("Name must not exceed 100 characters")
        
        # Validate age
        age = self._calculate_age(birth_date)
        if age < 18:
            raise ValueError("User must be at least 18 years old")
        if age > 100:
            raise ValueError("Invalid birth date")
        
        # Validate city
        city = city.strip()
        if not city:
            raise ValueError("City is required")
        
        # Create profile
        profile = UserProfile(
            user_id=user_id,
            name=name,
            birth_date=birth_date,
            gender=gender,
            orientation=orientation,
            city=city,
            bio=bio.strip() if bio else None,
            goal=kwargs.get('goal'),
            education=kwargs.get('education'),
            work=kwargs.get('work'),
            company=kwargs.get('company'),
            school=kwargs.get('school'),
            height=kwargs.get('height'),
            interests=kwargs.get('interests', []),
            languages=kwargs.get('languages', []),
            geohash=kwargs.get('geohash'),
            latitude=kwargs.get('latitude'),
            longitude=kwargs.get('longitude'),
            photos=kwargs.get('photos', []),
            is_verified=False,
            is_visible=True,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        
        return await self.profile_repository.create_profile(profile)
    
    async def update_profile(
        self,
        user_id: int,
        **updates
    ) -> Optional[UserProfile]:
        """Update user profile.
        
        Business logic:
        - Validate updated fields
        - Update timestamp
        """
        profile = await self.profile_repository.get_profile(user_id)
        if not profile:
            return None
        
        # Update fields if provided
        if 'name' in updates:
            name = updates['name'].strip()
            if not name or len(name) < 2:
                raise ValueError("Name must be at least 2 characters")
            profile.name = name
        
        if 'birth_date' in updates:
            age = self._calculate_age(updates['birth_date'])
            if age < 18:
                raise ValueError("User must be at least 18 years old")
            profile.birth_date = updates['birth_date']
        
        if 'bio' in updates:
            profile.bio = updates['bio'].strip() if updates['bio'] else None
        
        # Update other fields
        for field in ['gender', 'orientation', 'city', 'goal', 'education', 
                      'work', 'company', 'school', 'height', 'interests', 
                      'languages', 'geohash', 'latitude', 'longitude']:
            if field in updates:
                setattr(profile, field, updates[field])
        
        profile.updated_at = datetime.now(timezone.utc)
        
        return await self.profile_repository.update_profile(profile)
    
    async def add_photo(self, user_id: int, photo_url: str) -> Optional[UserProfile]:
        """Add photo to user profile.
        
        Business logic:
        - Validate photo count (max 6)
        - Add photo to list
        """
        profile = await self.profile_repository.get_profile(user_id)
        if not profile:
            return None
        
        if len(profile.photos) >= 6:
            raise ValueError("Maximum 6 photos allowed")
        
        if photo_url not in profile.photos:
            profile.photos.append(photo_url)
            profile.updated_at = datetime.now(timezone.utc)
            return await self.profile_repository.update_profile(profile)
        
        return profile
    
    async def remove_photo(self, user_id: int, photo_url: str) -> Optional[UserProfile]:
        """Remove photo from user profile."""
        profile = await self.profile_repository.get_profile(user_id)
        if not profile:
            return None
        
        if photo_url in profile.photos:
            profile.photos.remove(photo_url)
            profile.updated_at = datetime.now(timezone.utc)
            return await self.profile_repository.update_profile(profile)
        
        return profile
    
    async def set_visibility(self, user_id: int, is_visible: bool) -> Optional[UserProfile]:
        """Set profile visibility."""
        profile = await self.profile_repository.get_profile(user_id)
        if not profile:
            return None
        
        profile.is_visible = is_visible
        profile.updated_at = datetime.now(timezone.utc)
        
        return await self.profile_repository.update_profile(profile)
    
    async def delete_profile(self, user_id: int) -> bool:
        """Delete user profile."""
        return await self.profile_repository.delete_profile(user_id)
    
    def _calculate_age(self, birth_date: date) -> int:
        """Calculate age from birth date."""
        today = date.today()
        return today.year - birth_date.year - (
            (today.month, today.day) < (birth_date.month, birth_date.day)
        )
