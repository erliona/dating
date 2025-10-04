"""Database repository for profile operations.

Epic B1: Profile CRUD operations with PostgreSQL.
Epic C: Discovery, interactions, matches, and favorites.
"""

import logging
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from .cache import get_cache
from .db import Favorite, Interaction, Match, Photo, Profile, User

logger = logging.getLogger(__name__)
cache = get_cache()


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
        is_premium: bool = False,
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
        result = await self.session.execute(select(User).where(User.tg_id == tg_id))
        user = result.scalar_one_or_none()

        if user:
            # Update existing user
            user.username = username
            user.first_name = first_name
            user.language_code = language_code
            user.is_premium = is_premium
            user.updated_at = datetime.now(timezone.utc)

            logger.info(
                "User updated",
                extra={
                    "event_type": "user_updated",
                    "user_id": user.id,
                    "tg_id": tg_id,
                },
            )
        else:
            # Create new user
            user = User(
                tg_id=tg_id,
                username=username,
                first_name=first_name,
                language_code=language_code,
                is_premium=is_premium,
            )
            self.session.add(user)
            await self.session.flush()

            logger.info(
                "User created",
                extra={
                    "event_type": "user_created",
                    "user_id": user.id,
                    "tg_id": tg_id,
                },
            )

        return user

    async def get_user_by_tg_id(self, tg_id: int) -> Optional[User]:
        """Get user by Telegram ID.

        Args:
            tg_id: Telegram user ID

        Returns:
            User object or None
        """
        result = await self.session.execute(select(User).where(User.tg_id == tg_id))
        return result.scalar_one_or_none()

    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by internal user ID.

        Args:
            user_id: Internal user ID

        Returns:
            User object or None
        """
        result = await self.session.execute(select(User).where(User.id == user_id))
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
            is_complete=profile_data.get("is_complete", False),
        )

        self.session.add(profile)
        await self.session.flush()

        logger.info(
            "Profile created",
            extra={
                "event_type": "profile_created",
                "user_id": user_id,
                "profile_id": profile.id,
            },
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

    async def update_profile(
        self, user_id: int, profile_data: dict
    ) -> Optional[Profile]:
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
        for field in [
            "name",
            "birth_date",
            "gender",
            "orientation",
            "goal",
            "bio",
            "interests",
            "height_cm",
            "education",
            "has_children",
            "wants_children",
            "smoking",
            "drinking",
            "country",
            "city",
            "geohash",
            "latitude",
            "longitude",
            "hide_distance",
            "hide_online",
            "hide_age",
            "allow_messages_from",
            "is_complete",
        ]:
            if field in profile_data:
                setattr(profile, field, profile_data[field])

        profile.updated_at = datetime.now(timezone.utc)

        logger.info(
            "Profile updated",
            extra={
                "event_type": "profile_updated",
                "user_id": user_id,
                "profile_id": profile.id,
            },
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
        height: Optional[int] = None,
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
            height=height,
        )

        self.session.add(photo)
        await self.session.flush()

        logger.info(
            "Photo added",
            extra={
                "event_type": "photo_added",
                "user_id": user_id,
                "photo_id": photo.id,
            },
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
            select(Photo).where(Photo.user_id == user_id).order_by(Photo.sort_order)
        )
        return list(result.scalars().all())

    async def get_photos_for_users(self, user_ids: list[int]) -> dict[int, list[Photo]]:
        """Get photos for multiple users in a single query.

        This is optimized to avoid N+1 query problems when fetching
        photos for many profiles at once.

        Args:
            user_ids: List of internal user IDs

        Returns:
            Dictionary mapping user_id to list of Photo objects
        """
        if not user_ids:
            return {}

        result = await self.session.execute(
            select(Photo)
            .where(Photo.user_id.in_(user_ids))
            .order_by(Photo.user_id, Photo.sort_order)
        )
        photos = result.scalars().all()

        # Group photos by user_id
        photos_by_user = {}
        for photo in photos:
            if photo.user_id not in photos_by_user:
                photos_by_user[photo.user_id] = []
            photos_by_user[photo.user_id].append(photo)

        return photos_by_user

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
            extra={
                "event_type": "photo_deleted",
                "user_id": user_id,
                "photo_id": photo_id,
            },
        )

        return True

    async def find_candidates(
        self,
        user_id: int,
        limit: int = 10,
        cursor: Optional[int] = None,
        age_min: Optional[int] = None,
        age_max: Optional[int] = None,
        max_distance_km: Optional[float] = None,
        goal: Optional[str] = None,
        height_min: Optional[int] = None,
        height_max: Optional[int] = None,
        has_children: Optional[bool] = None,
        smoking: Optional[bool] = None,
        drinking: Optional[bool] = None,
        education: Optional[str] = None,
        verified_only: bool = False,
    ) -> tuple[list[Profile], Optional[int]]:
        """Find candidate profiles for discovery with filters and pagination.

        Args:
            user_id: Current user's ID
            limit: Maximum number of candidates to return
            cursor: Profile ID cursor for pagination
            age_min: Minimum age filter
            age_max: Maximum age filter
            max_distance_km: Maximum distance in kilometers
            goal: Relationship goal filter
            height_min: Minimum height in cm
            height_max: Maximum height in cm
            has_children: Has children filter
            smoking: Smoking filter
            drinking: Drinking filter
            education: Education level filter
            verified_only: Only show verified profiles

        Returns:
            Tuple of (list of Profile objects, next cursor)
        """
        # Get current user's profile and interactions
        current_profile = await self.get_profile_by_user_id(user_id)
        if not current_profile:
            return [], None

        # Get IDs of users already interacted with or matched
        interactions_result = await self.session.execute(
            select(Interaction.target_id).where(Interaction.user_id == user_id)
        )
        interacted_ids = set(interactions_result.scalars().all())

        # Build query
        query = select(Profile).where(
            Profile.user_id != user_id,
            Profile.is_visible == True,
            Profile.is_complete == True,
            Profile.user_id.not_in(interacted_ids) if interacted_ids else True,
        )

        # Apply mutual orientation filters
        # Filter 1: Current user's preference for candidate's gender
        if current_profile.orientation != "any":
            query = query.where(Profile.gender == current_profile.orientation)

        # Filter 2: Candidate's preference for current user's gender (mutual compatibility)
        # Candidates who want "any" gender should see everyone
        # Otherwise, they should only see people matching their orientation
        query = query.where(
            or_(
                Profile.orientation == "any",
                Profile.orientation == current_profile.gender,
            )
        )

        # Age filter based on birth_date
        if age_min is not None:
            max_birth_date = date.today().replace(year=date.today().year - age_min)
            query = query.where(Profile.birth_date <= max_birth_date)

        if age_max is not None:
            min_birth_date = date.today().replace(year=date.today().year - age_max)
            query = query.where(Profile.birth_date >= min_birth_date)

        # Other filters
        if goal:
            query = query.where(Profile.goal == goal)

        if height_min is not None:
            query = query.where(Profile.height_cm >= height_min)

        if height_max is not None:
            query = query.where(Profile.height_cm <= height_max)

        if has_children is not None:
            query = query.where(Profile.has_children == has_children)

        if smoking is not None:
            query = query.where(Profile.smoking == smoking)

        if drinking is not None:
            query = query.where(Profile.drinking == drinking)

        if education:
            query = query.where(Profile.education == education)

        # Cursor-based pagination
        if cursor:
            query = query.where(Profile.id > cursor)

        # Order by ID for consistent pagination
        query = query.order_by(Profile.id).limit(limit + 1)

        result = await self.session.execute(query)
        profiles = list(result.scalars().all())

        # Determine next cursor
        next_cursor = None
        if len(profiles) > limit:
            profiles = profiles[:limit]
            next_cursor = profiles[-1].id

        logger.info(
            "Candidates found",
            extra={
                "event_type": "candidates_found",
                "user_id": user_id,
                "count": len(profiles),
                "next_cursor": next_cursor,
            },
        )

        return profiles, next_cursor

    async def create_interaction(
        self, user_id: int, target_id: int, interaction_type: str
    ) -> Interaction:
        """Create or update an interaction (like, superlike, pass).

        Idempotent - updating same interaction updates timestamp.

        Args:
            user_id: User performing the interaction
            target_id: Target user ID
            interaction_type: Type of interaction (like, superlike, pass)

        Returns:
            Interaction object
        """
        # Check if interaction already exists
        result = await self.session.execute(
            select(Interaction).where(
                Interaction.user_id == user_id, Interaction.target_id == target_id
            )
        )
        interaction = result.scalar_one_or_none()

        if interaction:
            # Update existing interaction
            interaction.interaction_type = interaction_type
            interaction.updated_at = datetime.now(timezone.utc)
            logger.info(
                "Interaction updated",
                extra={
                    "event_type": "interaction_updated",
                    "user_id": user_id,
                    "target_id": target_id,
                    "type": interaction_type,
                },
            )
        else:
            # Create new interaction
            interaction = Interaction(
                user_id=user_id, target_id=target_id, interaction_type=interaction_type
            )
            self.session.add(interaction)
            await self.session.flush()

            logger.info(
                "Interaction created",
                extra={
                    "event_type": "interaction_created",
                    "user_id": user_id,
                    "target_id": target_id,
                    "type": interaction_type,
                },
            )

        return interaction

    async def check_mutual_like(self, user_id: int, target_id: int) -> bool:
        """Check if two users have mutually liked each other.

        Args:
            user_id: First user ID
            target_id: Second user ID

        Returns:
            True if mutual like exists
        """
        # Check if target has liked user back
        result = await self.session.execute(
            select(Interaction).where(
                Interaction.user_id == target_id,
                Interaction.target_id == user_id,
                Interaction.interaction_type.in_(["like", "superlike"]),
            )
        )
        return result.scalar_one_or_none() is not None

    async def create_match(self, user1_id: int, user2_id: int) -> Match:
        """Create a match between two users.

        Idempotent - returns existing match if already exists.
        Normalizes user IDs so user1_id < user2_id.
        Handles race conditions by catching unique constraint violations.

        Args:
            user1_id: First user ID
            user2_id: Second user ID

        Returns:
            Match object
        """
        from sqlalchemy.exc import IntegrityError

        # Normalize user IDs (user1_id should be less than user2_id)
        if user1_id > user2_id:
            user1_id, user2_id = user2_id, user1_id

        # Check if match already exists
        result = await self.session.execute(
            select(Match).where(Match.user1_id == user1_id, Match.user2_id == user2_id)
        )
        match = result.scalar_one_or_none()

        if match:
            logger.info(
                "Match already exists",
                extra={
                    "event_type": "match_exists",
                    "user1_id": user1_id,
                    "user2_id": user2_id,
                    "match_id": match.id,
                },
            )
            return match

        # Create new match
        match = Match(user1_id=user1_id, user2_id=user2_id)
        self.session.add(match)

        try:
            await self.session.flush()
        except IntegrityError:
            # Race condition: another transaction created the match
            # Roll back and fetch the existing match
            await self.session.rollback()
            result = await self.session.execute(
                select(Match).where(
                    Match.user1_id == user1_id, Match.user2_id == user2_id
                )
            )
            match = result.scalar_one_or_none()

            if match:
                logger.info(
                    "Match already exists (race condition)",
                    extra={
                        "event_type": "match_race_condition",
                        "user1_id": user1_id,
                        "user2_id": user2_id,
                        "match_id": match.id,
                    },
                )
                return match
            else:
                # Unexpected: constraint violation but match still not found
                raise

        # Invalidate match cache for both users
        cache.delete_pattern(f"matches:{user1_id}:")
        cache.delete_pattern(f"matches:{user2_id}:")

        logger.info(
            "Match created",
            extra={
                "event_type": "match_created",
                "user1_id": user1_id,
                "user2_id": user2_id,
                "match_id": match.id,
            },
        )

        return match

    async def get_matches(
        self, user_id: int, limit: int = 20, cursor: Optional[int] = None
    ) -> tuple[list[tuple[Match, Profile]], Optional[int]]:
        """Get user's matches with profiles.

        Args:
            user_id: User ID
            limit: Maximum number of matches to return
            cursor: Match ID cursor for pagination

        Returns:
            Tuple of (list of (Match, Profile) tuples, next cursor)
        """
        # Try cache first
        cache_key = f"matches:{user_id}:{cursor or 0}:{limit}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        # Build query for matches involving this user
        query = select(Match).where(
            or_(Match.user1_id == user_id, Match.user2_id == user_id)
        )

        if cursor:
            query = query.where(Match.id < cursor)

        query = query.order_by(Match.created_at.desc()).limit(limit + 1)

        result = await self.session.execute(query)
        matches = list(result.scalars().all())

        # Determine next cursor
        next_cursor = None
        if len(matches) > limit:
            matches = matches[:limit]
            next_cursor = matches[-1].id

        # Get profiles for matched users
        matches_with_profiles = []
        for match in matches:
            other_user_id = (
                match.user2_id if match.user1_id == user_id else match.user1_id
            )
            profile = await self.get_profile_by_user_id(other_user_id)
            if profile:
                matches_with_profiles.append((match, profile))

        # Cache result for 3 minutes
        cache.set(cache_key, (matches_with_profiles, next_cursor), ttl=180)

        logger.info(
            "Matches retrieved",
            extra={
                "event_type": "matches_retrieved",
                "user_id": user_id,
                "count": len(matches_with_profiles),
            },
        )

        return matches_with_profiles, next_cursor

    async def add_favorite(self, user_id: int, target_id: int) -> Favorite:
        """Add a profile to favorites.

        Idempotent - returns existing favorite if already exists.

        Args:
            user_id: User adding to favorites
            target_id: Target profile user ID

        Returns:
            Favorite object
        """
        # Check if favorite already exists
        result = await self.session.execute(
            select(Favorite).where(
                Favorite.user_id == user_id, Favorite.target_id == target_id
            )
        )
        favorite = result.scalar_one_or_none()

        if favorite:
            logger.info(
                "Favorite already exists",
                extra={
                    "event_type": "favorite_exists",
                    "user_id": user_id,
                    "target_id": target_id,
                },
            )
            return favorite

        # Create new favorite
        favorite = Favorite(user_id=user_id, target_id=target_id)
        self.session.add(favorite)
        await self.session.flush()

        # Invalidate favorites cache
        cache.delete_pattern(f"favorites:{user_id}:")

        logger.info(
            "Favorite added",
            extra={
                "event_type": "favorite_added",
                "user_id": user_id,
                "target_id": target_id,
                "favorite_id": favorite.id,
            },
        )

        return favorite

    async def remove_favorite(self, user_id: int, target_id: int) -> bool:
        """Remove a profile from favorites.

        Args:
            user_id: User removing from favorites
            target_id: Target profile user ID

        Returns:
            True if removed, False if not found
        """
        result = await self.session.execute(
            delete(Favorite).where(
                Favorite.user_id == user_id, Favorite.target_id == target_id
            )
        )

        removed = result.rowcount > 0

        if removed:
            # Invalidate favorites cache
            cache.delete_pattern(f"favorites:{user_id}:")

            logger.info(
                "Favorite removed",
                extra={
                    "event_type": "favorite_removed",
                    "user_id": user_id,
                    "target_id": target_id,
                },
            )

        return removed

    async def get_favorites(
        self, user_id: int, limit: int = 20, cursor: Optional[int] = None
    ) -> tuple[list[tuple[Favorite, Profile]], Optional[int]]:
        """Get user's favorites with profiles.

        Args:
            user_id: User ID
            limit: Maximum number of favorites to return
            cursor: Favorite ID cursor for pagination

        Returns:
            Tuple of (list of (Favorite, Profile) tuples, next cursor)
        """
        # Try cache first
        cache_key = f"favorites:{user_id}:{cursor or 0}:{limit}"
        cached = cache.get(cache_key)
        if cached is not None:
            return cached

        # Build query
        query = select(Favorite).where(Favorite.user_id == user_id)

        if cursor:
            query = query.where(Favorite.id < cursor)

        query = query.order_by(Favorite.created_at.desc()).limit(limit + 1)

        result = await self.session.execute(query)
        favorites = list(result.scalars().all())

        # Determine next cursor
        next_cursor = None
        if len(favorites) > limit:
            favorites = favorites[:limit]
            next_cursor = favorites[-1].id

        # Get profiles
        favorites_with_profiles = []
        for favorite in favorites:
            profile = await self.get_profile_by_user_id(favorite.target_id)
            if profile:
                favorites_with_profiles.append((favorite, profile))

        # Cache result for 5 minutes
        cache.set(cache_key, (favorites_with_profiles, next_cursor), ttl=300)

        logger.info(
            "Favorites retrieved",
            extra={
                "event_type": "favorites_retrieved",
                "user_id": user_id,
                "count": len(favorites_with_profiles),
            },
        )

        return favorites_with_profiles, next_cursor
