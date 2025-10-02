"""Database repository for profile operations.

Epic B1: Profile CRUD operations with PostgreSQL.
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .db import Photo, Profile, User

logger = logging.getLogger(__name__)


class ProfileRepository:
    """Repository for profile database operations."""
    
    def __init__(self, session: AsyncSession):
        """Initialize repository with database session.
        
        Args:
            session: SQLAlchemy async session
        """
        self.session = session
    
    async def create_or_update_user(
        self,
        tg_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        language_code: Optional[str] = None,
        is_premium: bool = False
    ) -> User:
        """Create or update user record.
        
        Args:
            tg_id: Telegram user ID
            username: Telegram username
            first_name: User's first name
            language_code: User's language code
            is_premium: Whether user has Telegram Premium
            
        Returns:
            User object
        """
        # Try to find existing user
        result = await self.session.execute(
            select(User).where(User.tg_id == tg_id)
        )
        user = result.scalar_one_or_none()
        
        if user:
            # Update existing user
            user.username = username
            user.first_name = first_name
            user.language_code = language_code
            user.is_premium = is_premium
            user.updated_at = datetime.utcnow()
            
            logger.info(
                "User updated",
                extra={"event_type": "user_updated", "user_id": user.id, "tg_id": tg_id}
            )
        else:
            # Create new user
            user = User(
                tg_id=tg_id,
                username=username,
                first_name=first_name,
                language_code=language_code,
                is_premium=is_premium
            )
            self.session.add(user)
            await self.session.flush()
            
            logger.info(
                "User created",
                extra={"event_type": "user_created", "user_id": user.id, "tg_id": tg_id}
            )
        
        return user
    
    async def get_user_by_tg_id(self, tg_id: int) -> Optional[User]:
        """Get user by Telegram ID.
        
        Args:
            tg_id: Telegram user ID
            
        Returns:
            User object or None
        """
        result = await self.session.execute(
            select(User).where(User.tg_id == tg_id)
        )
        return result.scalar_one_or_none()
    
    async def create_profile(self, user_id: int, profile_data: dict) -> Profile:
        """Create a new profile.
        
        Args:
            user_id: Internal user ID
            profile_data: Dictionary containing profile data
            
        Returns:
            Created Profile object
        """
        profile = Profile(
            user_id=user_id,
            name=profile_data["name"],
            birth_date=profile_data["birth_date"],
            gender=profile_data["gender"],
            orientation=profile_data["orientation"],
            goal=profile_data["goal"],
            bio=profile_data.get("bio"),
            interests=profile_data.get("interests"),
            height_cm=profile_data.get("height_cm"),
            education=profile_data.get("education"),
            has_children=profile_data.get("has_children"),
            wants_children=profile_data.get("wants_children"),
            smoking=profile_data.get("smoking"),
            drinking=profile_data.get("drinking"),
            country=profile_data.get("country"),
            city=profile_data.get("city"),
            geohash=profile_data.get("geohash"),
            latitude=profile_data.get("latitude"),
            longitude=profile_data.get("longitude"),
            hide_distance=profile_data.get("hide_distance", False),
            hide_online=profile_data.get("hide_online", False),
            hide_age=profile_data.get("hide_age", False),
            allow_messages_from=profile_data.get("allow_messages_from", "matches"),
            is_complete=profile_data.get("is_complete", False)
        )
        
        self.session.add(profile)
        await self.session.flush()
        
        logger.info(
            "Profile created",
            extra={"event_type": "profile_created", "user_id": user_id, "profile_id": profile.id}
        )
        
        return profile
    
    async def get_profile_by_user_id(self, user_id: int) -> Optional[Profile]:
        """Get profile by user ID.
        
        Args:
            user_id: Internal user ID
            
        Returns:
            Profile object or None
        """
        result = await self.session.execute(
            select(Profile).where(Profile.user_id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def update_profile(self, user_id: int, profile_data: dict) -> Optional[Profile]:
        """Update existing profile.
        
        Args:
            user_id: Internal user ID
            profile_data: Dictionary containing profile data to update
            
        Returns:
            Updated Profile object or None if not found
        """
        profile = await self.get_profile_by_user_id(user_id)
        
        if not profile:
            return None
        
        # Update fields if provided
        for field in ["name", "birth_date", "gender", "orientation", "goal", "bio",
                     "interests", "height_cm", "education", "has_children", 
                     "wants_children", "smoking", "drinking", "country", "city",
                     "geohash", "latitude", "longitude", "hide_distance", 
                     "hide_online", "hide_age", "allow_messages_from", "is_complete"]:
            if field in profile_data:
                setattr(profile, field, profile_data[field])
        
        profile.updated_at = datetime.utcnow()
        
        logger.info(
            "Profile updated",
            extra={"event_type": "profile_updated", "user_id": user_id, "profile_id": profile.id}
        )
        
        return profile
    
    async def add_photo(
        self,
        user_id: int,
        url: str,
        sort_order: int = 0,
        safe_score: float = 1.0,
        file_size: Optional[int] = None,
        mime_type: Optional[str] = None,
        width: Optional[int] = None,
        height: Optional[int] = None
    ) -> Photo:
        """Add a photo to user's profile.
        
        Args:
            user_id: Internal user ID
            url: Photo URL
            sort_order: Display order (0-2)
            safe_score: NSFW safety score (0.0-1.0)
            file_size: File size in bytes
            mime_type: MIME type
            width: Image width
            height: Image height
            
        Returns:
            Created Photo object
        """
        photo = Photo(
            user_id=user_id,
            url=url,
            sort_order=sort_order,
            safe_score=safe_score,
            file_size=file_size,
            mime_type=mime_type,
            width=width,
            height=height
        )
        
        self.session.add(photo)
        await self.session.flush()
        
        logger.info(
            "Photo added",
            extra={"event_type": "photo_added", "user_id": user_id, "photo_id": photo.id}
        )
        
        return photo
    
    async def get_user_photos(self, user_id: int) -> list[Photo]:
        """Get all photos for a user.
        
        Args:
            user_id: Internal user ID
            
        Returns:
            List of Photo objects ordered by sort_order
        """
        result = await self.session.execute(
            select(Photo)
            .where(Photo.user_id == user_id)
            .order_by(Photo.sort_order)
        )
        return list(result.scalars().all())
    
    async def delete_photo(self, photo_id: int, user_id: int) -> bool:
        """Delete a photo.
        
        Args:
            photo_id: Photo ID
            user_id: User ID (for authorization check)
            
        Returns:
            True if deleted, False if not found
        """
        result = await self.session.execute(
            select(Photo).where(Photo.id == photo_id, Photo.user_id == user_id)
        )
        photo = result.scalar_one_or_none()
        
        if not photo:
            return False
        
        await self.session.delete(photo)
        
        logger.info(
            "Photo deleted",
            extra={"event_type": "photo_deleted", "user_id": user_id, "photo_id": photo_id}
        )
        
        return True
