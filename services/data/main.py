"""Data Service main entry point.

This service provides centralized database access for all other microservices.
All database operations go through this service to maintain consistency.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import date

from aiohttp import web
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from core.utils.logging import configure_logging

logger = logging.getLogger(__name__)


class DataService:
    """Encapsulates all direct database operations for other microservices."""
    
    def __init__(self, session: AsyncSession):
        """Initialize with database session."""
        self.session = session
    
    # Profile operations
    async def get_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user profile by user_id."""
        from bot.repository import ProfileRepository
        
        repository = ProfileRepository(self.session)
        profile = await repository.get_profile_by_user_id(user_id)
        
        if not profile:
            return None
            
        return {
            "user_id": profile.user_id,
            "name": profile.name,
            "birth_date": profile.birth_date.isoformat() if profile.birth_date else None,
            "gender": profile.gender,
            "city": profile.city,
            "bio": profile.bio,
            "interests": profile.interests,
            "goal": profile.goal,
            "orientation": profile.orientation,
            "height_cm": profile.height_cm,
            "education": profile.education,
            "has_children": profile.has_children,
            "wants_children": profile.wants_children,
            "smoking": profile.smoking,
            "drinking": profile.drinking,
            "country": profile.country,
            "geohash": profile.geohash,
            "latitude": profile.latitude,
            "longitude": profile.longitude,
            "hide_distance": profile.hide_distance,
            "hide_online": profile.hide_online,
            "hide_age": profile.hide_age,
            "allow_messages_from": profile.allow_messages_from,
            "is_visible": profile.is_visible,
            "is_complete": profile.is_complete,
            "created_at": profile.created_at.isoformat() if profile.created_at else None,
            "updated_at": profile.updated_at.isoformat() if profile.updated_at else None,
        }
    
    async def create_profile(self, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create new user profile."""
        from bot.repository import ProfileRepository
        
        repository = ProfileRepository(self.session)
        
        # Get or create user from Telegram ID
        telegram_id = profile_data.get("user_id")
        if telegram_id:
            user = await repository.create_or_update_user(
                tg_id=telegram_id,
                username=profile_data.get("username"),
                first_name=profile_data.get("first_name"),
                language_code=profile_data.get("language_code"),
                is_premium=profile_data.get("is_premium", False),
            )
            user_id = user.id
        else:
            raise ValueError("user_id (Telegram ID) is required")
        
        # Check if profile already exists
        existing_profile = await repository.get_profile_by_user_id(user_id)
        if existing_profile:
            raise ValueError("Profile already exists for this user")
        
        # Parse birth_date
        birth_date_str = profile_data.get("birth_date")
        birth_date = None
        if birth_date_str is not None:
            if isinstance(birth_date_str, str):
                birth_date = date.fromisoformat(birth_date_str)
            else:
                birth_date = birth_date_str
        else:
            raise ValueError("birth_date is required")
        
        # Prepare profile data
        profile_payload = {
            "name": profile_data["name"],
            "birth_date": birth_date,
            "gender": profile_data["gender"],
            "orientation": profile_data["orientation"],
            "goal": profile_data.get("goal"),
            "bio": profile_data.get("bio"),
            "interests": profile_data.get("interests", []),
            "height_cm": profile_data.get("height_cm"),
            "education": profile_data.get("education"),
            "has_children": profile_data.get("has_children"),
            "wants_children": profile_data.get("wants_children"),
            "smoking": profile_data.get("smoking"),
            "drinking": profile_data.get("drinking"),
            "country": profile_data.get("country"),
            "city": profile_data.get("city"),
            "geohash": profile_data.get("geohash"),
            "latitude": profile_data.get("latitude"),
            "longitude": profile_data.get("longitude"),
            "hide_distance": profile_data.get("hide_distance", False),
            "hide_online": profile_data.get("hide_online", False),
            "hide_age": profile_data.get("hide_age", False),
            "allow_messages_from": profile_data.get("allow_messages_from", "matches"),
            "is_complete": profile_data.get("is_complete", True),
        }
        
        # Create profile
        profile = await repository.create_profile(user_id, profile_payload)
        await self.session.commit()
        
        return {
            "user_id": profile.user_id,
            "name": profile.name,
            "gender": profile.gender,
            "city": profile.city,
            "goal": profile.goal,
            "created": True,
        }
    
    async def update_profile(self, user_id: int, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user profile."""
        from bot.repository import ProfileRepository
        
        repository = ProfileRepository(self.session)
        profile = await repository.get_profile_by_user_id(user_id)
        
        if not profile:
            raise ValueError("Profile not found")
        
        # Update profile fields
        for field, value in profile_data.items():
            if hasattr(profile, field):
                setattr(profile, field, value)
        
        await self.session.commit()
        
        return {
            "user_id": profile.user_id,
            "name": profile.name,
            "gender": profile.gender,
            "city": profile.city,
            "goal": profile.goal,
            "updated": True,
        }
    
    async def delete_profile(self, user_id: int) -> bool:
        """Delete user profile."""
        from bot.repository import ProfileRepository
        
        repository = ProfileRepository(self.session)
        profile = await repository.get_profile_by_user_id(user_id)
        
        if not profile:
            return False
        
        await repository.delete_profile(user_id)
        await self.session.commit()
        
        return True
    
    # User operations
    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID."""
        from bot.repository import ProfileRepository
        
        repository = ProfileRepository(self.session)
        user = await repository.get_user_by_id(user_id)
        
        if not user:
            return None
            
        return {
            "id": user.id,
            "tg_id": user.tg_id,
            "username": user.username,
            "first_name": user.first_name,
            "language_code": user.language_code,
            "is_premium": user.is_premium,
            "is_banned": user.is_banned,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        }
    
    async def list_users(self, page: int = 1, per_page: int = 20, search: str = "") -> Dict[str, Any]:
        """List users with pagination."""
        from bot.repository import ProfileRepository
        from sqlalchemy import func, or_
        
        repository = ProfileRepository(self.session)
        users, total = await repository.list_users(page, per_page, search)
        
        users_data = []
        for user in users:
            users_data.append({
                "id": user.id,
                "tg_id": user.tg_id,
                "username": user.username,
                "first_name": user.first_name,
                "is_premium": user.is_premium,
                "is_banned": user.is_banned,
                "created_at": user.created_at.isoformat() if user.created_at else None,
            })
        
        return {
            "users": users_data,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page,
        }
    
    async def update_user(self, user_id: int, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update user information."""
        from bot.repository import ProfileRepository
        
        repository = ProfileRepository(self.session)
        user = await repository.get_user_by_id(user_id)
        
        if not user:
            raise ValueError("User not found")
        
        # Update allowed fields
        if "is_banned" in user_data:
            user.is_banned = bool(user_data["is_banned"])
        if "is_premium" in user_data:
            user.is_premium = bool(user_data["is_premium"])
        
        await self.session.commit()
        
        return {
            "id": user.id,
            "is_banned": user.is_banned,
            "is_premium": user.is_premium,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None,
        }
    
    # Statistics operations
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics."""
        from bot.repository import ProfileRepository
        from sqlalchemy import func
        from datetime import datetime, timedelta, timezone
        
        repository = ProfileRepository(self.session)
        stats = await repository.get_system_stats()
        
        return stats
    
    # Photo operations
    async def list_photos(self, page: int = 1, per_page: int = 20, verified_only: bool = False, unverified_only: bool = False) -> Dict[str, Any]:
        """List photos for moderation."""
        from bot.repository import ProfileRepository
        
        repository = ProfileRepository(self.session)
        photos, total = await repository.list_photos(page, per_page, verified_only, unverified_only)
        
        photos_data = []
        for photo in photos:
            photos_data.append({
                "id": photo.id,
                "user_id": photo.user_id,
                "url": photo.url,
                "sort_order": photo.sort_order,
                "is_verified": photo.is_verified,
                "safe_score": photo.safe_score,
                "created_at": photo.created_at.isoformat() if photo.created_at else None,
            })
        
        return {
            "photos": photos_data,
            "total": total,
            "page": page,
            "per_page": per_page,
            "pages": (total + per_page - 1) // per_page,
        }
    
    async def update_photo(self, photo_id: int, photo_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update photo (verify/reject)."""
        from bot.repository import ProfileRepository
        
        repository = ProfileRepository(self.session)
        photo = await repository.get_photo_by_id(photo_id)
        
        if not photo:
            raise ValueError("Photo not found")
        
        if "is_verified" in photo_data:
            photo.is_verified = bool(photo_data["is_verified"])
        
        await self.session.commit()
        
        return {
            "id": photo.id,
            "is_verified": photo.is_verified,
        }
    
    async def delete_photo(self, photo_id: int) -> bool:
        """Delete a photo."""
        from bot.repository import ProfileRepository
        
        repository = ProfileRepository(self.session)
        photo = await repository.get_photo_by_id(photo_id)
        
        if not photo:
            return False
        
        await repository.delete_photo(photo_id)
        await self.session.commit()
        
        return True
    
    # Discovery operations
    async def find_candidates(self, user_id: int, limit: int = 10, cursor: int = None, **filters) -> Dict[str, Any]:
        """Find candidate profiles for discovery."""
        from bot.repository import ProfileRepository
        
        repository = ProfileRepository(self.session)
        profiles, next_cursor = await repository.find_candidates(
            user_id=user_id,
            limit=limit,
            cursor=cursor,
            **filters
        )
        
        candidates_data = []
        for profile in profiles:
            candidates_data.append({
                "id": profile.id,
                "user_id": profile.user_id,
                "name": profile.name,
                "age": profile.age,
                "gender": profile.gender,
                "orientation": profile.orientation,
                "city": profile.city,
                "bio": profile.bio,
                "goal": profile.goal,
                "education": profile.education,
                "work": profile.work,
                "height_cm": profile.height_cm,
                "photos": [photo.url for photo in profile.photos] if hasattr(profile, 'photos') else [],
                "is_verified": profile.is_verified,
                "created_at": profile.created_at.isoformat() if profile.created_at else None,
            })
        
        return {
            "candidates": candidates_data,
            "count": len(candidates_data),
            "next_cursor": next_cursor,
        }
    
    async def create_interaction(self, user_id: int, target_id: int, interaction_type: str) -> Dict[str, Any]:
        """Create or update an interaction (like, superlike, pass)."""
        from bot.repository import ProfileRepository
        
        repository = ProfileRepository(self.session)
        interaction = await repository.create_interaction(user_id, target_id, interaction_type)
        
        # Check if this creates a match
        is_match = False
        if interaction_type == "like":
            is_match = await repository.check_mutual_like(user_id, target_id)
            if is_match:
                await repository.create_match(user_id, target_id)
        
        await self.session.commit()
        
        return {
            "success": True,
            "matched": is_match,
            "interaction_id": interaction.id,
            "interaction_type": interaction.interaction_type,
        }
    
    async def get_matches(self, user_id: int, limit: int = 20, cursor: int = None) -> Dict[str, Any]:
        """Get user's matches with profiles."""
        from bot.repository import ProfileRepository
        
        repository = ProfileRepository(self.session)
        matches, next_cursor = await repository.get_matches(user_id, limit, cursor)
        
        matches_data = []
        for match, profile in matches:
            matches_data.append({
                "match_id": match.id,
                "user_id": profile.user_id,
                "name": profile.name,
                "age": profile.age,
                "gender": profile.gender,
                "city": profile.city,
                "bio": profile.bio,
                "photos": [photo.url for photo in profile.photos] if hasattr(profile, 'photos') else [],
                "is_verified": profile.is_verified,
                "matched_at": match.created_at.isoformat() if match.created_at else None,
            })
        
        return {
            "matches": matches_data,
            "count": len(matches_data),
            "next_cursor": next_cursor,
        }


# API Handlers
async def get_profile_handler(request: web.Request) -> web.Response:
    """Get user profile.
    
    GET /data/profiles/{user_id}
    """
    try:
        user_id = int(request.match_info["user_id"])
        session_maker = request.app["session_maker"]
        
        async with session_maker() as session:
            data_service = DataService(session)
            profile = await data_service.get_profile(user_id)
        
        if not profile:
            return web.json_response({"error": "Profile not found"}, status=404)
        
        return web.json_response(profile)
        
    except ValueError:
        return web.json_response({"error": "Invalid user_id"}, status=400)
    except Exception as e:
        logger.error(f"Error getting profile: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def create_profile_handler(request: web.Request) -> web.Response:
    """Create user profile.
    
    POST /data/profiles
    """
    try:
        profile_data = await request.json()
        session_maker = request.app["session_maker"]
        
        async with session_maker() as session:
            data_service = DataService(session)
            result = await data_service.create_profile(profile_data)
        
        return web.json_response(result, status=201)
        
    except ValueError as e:
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error creating profile: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def update_profile_handler(request: web.Request) -> web.Response:
    """Update user profile.
    
    PUT /data/profiles/{user_id}
    """
    try:
        user_id = int(request.match_info["user_id"])
        profile_data = await request.json()
        session_maker = request.app["session_maker"]
        
        async with session_maker() as session:
            data_service = DataService(session)
            result = await data_service.update_profile(user_id, profile_data)
        
        return web.json_response(result)
        
    except ValueError as e:
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error updating profile: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


# User API Handlers
async def get_user_handler(request: web.Request) -> web.Response:
    """Get user by ID.
    
    GET /data/users/{user_id}
    """
    try:
        user_id = int(request.match_info["user_id"])
        session_maker = request.app["session_maker"]
        
        async with session_maker() as session:
            data_service = DataService(session)
            user = await data_service.get_user(user_id)
        
        if not user:
            return web.json_response({"error": "User not found"}, status=404)
        
        return web.json_response(user)
        
    except ValueError:
        return web.json_response({"error": "Invalid user_id"}, status=400)
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def list_users_handler(request: web.Request) -> web.Response:
    """List users with pagination.
    
    GET /data/users?page=1&per_page=20&search=
    """
    try:
        page = int(request.query.get("page", "1"))
        per_page = min(int(request.query.get("per_page", "20")), 100)
        search = request.query.get("search", "")
        
        session_maker = request.app["session_maker"]
        
        async with session_maker() as session:
            data_service = DataService(session)
            result = await data_service.list_users(page, per_page, search)
        
        return web.json_response(result)
        
    except ValueError:
        return web.json_response({"error": "Invalid parameters"}, status=400)
    except Exception as e:
        logger.error(f"Error listing users: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def update_user_handler(request: web.Request) -> web.Response:
    """Update user information.
    
    PUT /data/users/{user_id}
    """
    try:
        user_id = int(request.match_info["user_id"])
        user_data = await request.json()
        session_maker = request.app["session_maker"]
        
        async with session_maker() as session:
            data_service = DataService(session)
            result = await data_service.update_user(user_id, user_data)
        
        return web.json_response(result)
        
    except ValueError as e:
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


# Statistics API Handlers
async def get_stats_handler(request: web.Request) -> web.Response:
    """Get system statistics.
    
    GET /data/stats
    """
    try:
        session_maker = request.app["session_maker"]
        
        async with session_maker() as session:
            data_service = DataService(session)
            stats = await data_service.get_system_stats()
        
        return web.json_response(stats)
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


# Photo API Handlers
async def list_photos_handler(request: web.Request) -> web.Response:
    """List photos for moderation.
    
    GET /data/photos?page=1&per_page=20&verified=true&unverified=true
    """
    try:
        page = int(request.query.get("page", "1"))
        per_page = min(int(request.query.get("per_page", "20")), 100)
        verified_only = request.query.get("verified") == "true"
        unverified_only = request.query.get("unverified") == "true"
        
        session_maker = request.app["session_maker"]
        
        async with session_maker() as session:
            data_service = DataService(session)
            result = await data_service.list_photos(page, per_page, verified_only, unverified_only)
        
        return web.json_response(result)
        
    except ValueError:
        return web.json_response({"error": "Invalid parameters"}, status=400)
    except Exception as e:
        logger.error(f"Error listing photos: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def update_photo_handler(request: web.Request) -> web.Response:
    """Update photo (verify/reject).
    
    PUT /data/photos/{photo_id}
    """
    try:
        photo_id = int(request.match_info["photo_id"])
        photo_data = await request.json()
        session_maker = request.app["session_maker"]
        
        async with session_maker() as session:
            data_service = DataService(session)
            result = await data_service.update_photo(photo_id, photo_data)
        
        return web.json_response(result)
        
    except ValueError as e:
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error updating photo: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def delete_photo_handler(request: web.Request) -> web.Response:
    """Delete a photo.
    
    DELETE /data/photos/{photo_id}
    """
    try:
        photo_id = int(request.match_info["photo_id"])
        session_maker = request.app["session_maker"]
        
        async with session_maker() as session:
            data_service = DataService(session)
            success = await data_service.delete_photo(photo_id)
        
        if not success:
            return web.json_response({"error": "Photo not found"}, status=404)
        
        return web.json_response({"success": True})
        
    except ValueError:
        return web.json_response({"error": "Invalid photo_id"}, status=400)
    except Exception as e:
        logger.error(f"Error deleting photo: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


# Discovery API Handlers
async def find_candidates_handler(request: web.Request) -> web.Response:
    """Find candidate profiles for discovery.
    
    GET /data/candidates?user_id=123&limit=10&cursor=456
    """
    try:
        user_id = int(request.query.get("user_id", 0))
        limit = int(request.query.get("limit", 10))
        cursor = request.query.get("cursor")
        
        if cursor:
            cursor = int(cursor)
        
        if not user_id:
            return web.json_response({"error": "user_id is required"}, status=400)
        
        # Extract filters from query parameters
        filters = {}
        if request.query.get("age_min"):
            filters["age_min"] = int(request.query.get("age_min"))
        if request.query.get("age_max"):
            filters["age_max"] = int(request.query.get("age_max"))
        if request.query.get("max_distance_km"):
            filters["max_distance_km"] = float(request.query.get("max_distance_km"))
        if request.query.get("goal"):
            filters["goal"] = request.query.get("goal")
        if request.query.get("height_min"):
            filters["height_min"] = int(request.query.get("height_min"))
        if request.query.get("height_max"):
            filters["height_max"] = int(request.query.get("height_max"))
        if request.query.get("has_children"):
            filters["has_children"] = request.query.get("has_children").lower() == "true"
        if request.query.get("smoking"):
            filters["smoking"] = request.query.get("smoking").lower() == "true"
        if request.query.get("drinking"):
            filters["drinking"] = request.query.get("drinking").lower() == "true"
        if request.query.get("education"):
            filters["education"] = request.query.get("education")
        if request.query.get("verified_only"):
            filters["verified_only"] = request.query.get("verified_only").lower() == "true"
        
        session_maker = request.app["session_maker"]
        
        async with session_maker() as session:
            data_service = DataService(session)
            result = await data_service.find_candidates(user_id, limit, cursor, **filters)
        
        return web.json_response(result)

    except ValueError as e:
        return web.json_response({"error": "Invalid parameters"}, status=400)
    except Exception as e:
        logger.error(f"Error finding candidates: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def create_interaction_handler(request: web.Request) -> web.Response:
    """Create or update an interaction (like, superlike, pass).
    
    POST /data/interactions
    """
    try:
        data = await request.json()
        user_id = data.get("user_id")
        target_id = data.get("target_id")
        interaction_type = data.get("interaction_type", "like")
        
        if not user_id or not target_id:
            return web.json_response(
                {"error": "user_id and target_id are required"}, status=400
            )
        
        if interaction_type not in ["like", "superlike", "pass"]:
            return web.json_response(
                {"error": "interaction_type must be 'like', 'superlike', or 'pass'"}, status=400
            )
        
        session_maker = request.app["session_maker"]
        
        async with session_maker() as session:
            data_service = DataService(session)
            result = await data_service.create_interaction(user_id, target_id, interaction_type)
        
        return web.json_response(result)

    except Exception as e:
        logger.error(f"Error creating interaction: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def get_matches_handler(request: web.Request) -> web.Response:
    """Get user's matches with profiles.
    
    GET /data/matches?user_id=123&limit=20&cursor=456
    """
    try:
        user_id = int(request.query.get("user_id", 0))
        limit = int(request.query.get("limit", 20))
        cursor = request.query.get("cursor")
        
        if cursor:
            cursor = int(cursor)
        
        if not user_id:
            return web.json_response({"error": "user_id is required"}, status=400)
        
        session_maker = request.app["session_maker"]
        
        async with session_maker() as session:
            data_service = DataService(session)
            result = await data_service.get_matches(user_id, limit, cursor)
        
        return web.json_response(result)

    except ValueError as e:
        return web.json_response({"error": "Invalid parameters"}, status=400)
    except Exception as e:
        logger.error(f"Error getting matches: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def health_handler(request: web.Request) -> web.Response:
    """Health check endpoint."""
    return web.json_response({"status": "healthy", "service": "data-service"})


def create_app(config: dict) -> web.Application:
    """Create and configure the Data Service application."""
    app = web.Application()
    app["config"] = config

    # Initialize database engine and session maker
    engine = create_async_engine(config["database_url"])
    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    # Store session maker for creating data service instances
    app["session_maker"] = async_session_maker
    
    # Add routes
    app.router.add_get("/health", health_handler)
    
    # Profile routes
    app.router.add_get("/data/profiles/{user_id}", get_profile_handler)
    app.router.add_post("/data/profiles", create_profile_handler)
    app.router.add_put("/data/profiles/{user_id}", update_profile_handler)
    
    # User routes
    app.router.add_get("/data/users/{user_id}", get_user_handler)
    app.router.add_get("/data/users", list_users_handler)
    app.router.add_put("/data/users/{user_id}", update_user_handler)
    
    # Statistics routes
    app.router.add_get("/data/stats", get_stats_handler)
    
    # Photo routes
    app.router.add_get("/data/photos", list_photos_handler)
    app.router.add_put("/data/photos/{photo_id}", update_photo_handler)
    app.router.add_delete("/data/photos/{photo_id}", delete_photo_handler)
    
    # Discovery routes
    app.router.add_get("/data/candidates", find_candidates_handler)
    app.router.add_post("/data/interactions", create_interaction_handler)
    app.router.add_get("/data/matches", get_matches_handler)

    return app


async def main():
    """Main entry point for Data Service."""
    
    # Configure logging
    configure_logging("data-service")
    logger.info("Starting Data Service")
    
    # Load configuration
    import os
    config = {
        "database_url": os.getenv("DATABASE_URL", "postgresql+asyncpg://dating:dating@db:5432/dating"),
        "data_service_host": os.getenv("DATA_SERVICE_HOST", "0.0.0.0"),
        "data_service_port": int(os.getenv("DATA_SERVICE_PORT", "8088")),
    }
    
    # Create and run the aiohttp application
    app = create_app(config)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, config["data_service_host"], config["data_service_port"])
    
    await site.start()
    
    logger.info(f"Data Service started on {config['data_service_host']}:{config['data_service_port']}")
    
    # Keep running
    try:
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        logger.info("Data Service shutting down")
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())