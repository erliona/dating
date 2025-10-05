"""Admin service main entry point.

This microservice handles admin panel functionality including:
- User management
- Profile management
- Photo moderation
- System statistics
- Settings management
"""

import hashlib
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Optional

from aiohttp import web
from sqlalchemy import and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from bot.db import Admin, Base, Favorite, Interaction, Match, Photo, Profile, User
from core.utils.logging import configure_logging

logger = logging.getLogger(__name__)


def hash_password(password: str) -> str:
    """Hash password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    return hash_password(password) == password_hash


async def create_session_token(admin_id: int, secret: str) -> str:
    """Create a simple session token."""
    import secrets

    token = secrets.token_urlsafe(32)
    # In production, store this in Redis/database with expiry
    return token


async def verify_session_token(token: str, secret: str) -> Optional[int]:
    """Verify session token and return admin_id."""
    # In production, verify against Redis/database
    # For now, this is a placeholder
    return None


async def login_handler(request: web.Request) -> web.Response:
    """Admin login endpoint."""
    try:
        data = await request.json()
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            return web.json_response(
                {"error": "Username and password required"}, status=400
            )

        session_maker = request.app["session_maker"]
        async with session_maker() as session:
            # Find admin user
            result = await session.execute(
                select(Admin).where(Admin.username == username)
            )
            admin = result.scalar_one_or_none()

            if not admin or not verify_password(password, admin.password_hash):
                return web.json_response({"error": "Invalid credentials"}, status=401)

            if not admin.is_active:
                return web.json_response({"error": "Account is disabled"}, status=403)

            # Update last login
            admin.last_login = datetime.now(timezone.utc)
            await session.commit()

            # Create session token
            token = await create_session_token(
                admin.id, request.app["config"]["jwt_secret"]
            )

            return web.json_response(
                {
                    "token": token,
                    "admin": {
                        "id": admin.id,
                        "username": admin.username,
                        "full_name": admin.full_name,
                        "is_super_admin": admin.is_super_admin,
                    },
                }
            )

    except Exception as e:
        logger.error(f"Login error: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def get_stats_handler(request: web.Request) -> web.Response:
    """Get system statistics for dashboard."""
    try:
        session_maker = request.app["session_maker"]
        async with session_maker() as session:
            # Total users
            total_users_result = await session.execute(select(func.count(User.id)))
            total_users = total_users_result.scalar()

            # Active users (created in last 30 days)
            thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)
            active_users_result = await session.execute(
                select(func.count(User.id)).where(User.created_at >= thirty_days_ago)
            )
            active_users = active_users_result.scalar()

            # Total profiles
            total_profiles_result = await session.execute(
                select(func.count(Profile.id))
            )
            total_profiles = total_profiles_result.scalar()

            # Complete profiles
            complete_profiles_result = await session.execute(
                select(func.count(Profile.id)).where(Profile.is_complete)
            )
            complete_profiles = complete_profiles_result.scalar()

            # Total photos
            total_photos_result = await session.execute(select(func.count(Photo.id)))
            total_photos = total_photos_result.scalar()

            # Verified photos
            verified_photos_result = await session.execute(
                select(func.count(Photo.id)).where(Photo.is_verified)
            )
            verified_photos = verified_photos_result.scalar()

            # Total matches
            total_matches_result = await session.execute(select(func.count(Match.id)))
            total_matches = total_matches_result.scalar()

            # Total interactions
            total_interactions_result = await session.execute(
                select(func.count(Interaction.id))
            )
            total_interactions = total_interactions_result.scalar()

            # Banned users
            banned_users_result = await session.execute(
                select(func.count(User.id)).where(User.is_banned == True)
            )
            banned_users = banned_users_result.scalar()

            return web.json_response(
                {
                    "users": {
                        "total": total_users,
                        "active": active_users,
                        "banned": banned_users,
                    },
                    "profiles": {
                        "total": total_profiles,
                        "complete": complete_profiles,
                    },
                    "photos": {
                        "total": total_photos,
                        "verified": verified_photos,
                        "pending": total_photos - verified_photos,
                    },
                    "matches": total_matches,
                    "interactions": total_interactions,
                }
            )

    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def list_users_handler(request: web.Request) -> web.Response:
    """List users with pagination."""
    try:
        page = int(request.query.get("page", "1"))
        per_page = min(int(request.query.get("per_page", "20")), 100)
        search = request.query.get("search", "")

        offset = (page - 1) * per_page

        session_maker = request.app["session_maker"]
        async with session_maker() as session:
            # Build query
            query = select(User).order_by(User.created_at.desc())

            if search:
                query = query.where(
                    or_(
                        User.username.ilike(f"%{search}%"),
                        User.first_name.ilike(f"%{search}%"),
                    )
                )

            # Count total
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await session.execute(count_query)
            total = total_result.scalar()

            # Get page
            query = query.offset(offset).limit(per_page)
            result = await session.execute(query)
            users = result.scalars().all()

            users_data = []
            for user in users:
                users_data.append(
                    {
                        "id": user.id,
                        "tg_id": user.tg_id,
                        "username": user.username,
                        "first_name": user.first_name,
                        "is_premium": user.is_premium,
                        "is_banned": user.is_banned,
                        "created_at": user.created_at.isoformat(),
                    }
                )

            return web.json_response(
                {
                    "users": users_data,
                    "total": total,
                    "page": page,
                    "per_page": per_page,
                    "pages": (total + per_page - 1) // per_page,
                }
            )

    except Exception as e:
        logger.error(f"Error listing users: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def get_user_handler(request: web.Request) -> web.Response:
    """Get detailed user information."""
    try:
        user_id = int(request.match_info["user_id"])

        session_maker = request.app["session_maker"]
        async with session_maker() as session:
            # Get user
            user_result = await session.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one_or_none()

            if not user:
                return web.json_response({"error": "User not found"}, status=404)

            # Get profile
            profile_result = await session.execute(
                select(Profile).where(Profile.user_id == user_id)
            )
            profile = profile_result.scalar_one_or_none()

            # Get photos
            photos_result = await session.execute(
                select(Photo).where(Photo.user_id == user_id).order_by(Photo.sort_order)
            )
            photos = photos_result.scalars().all()

            # Get interaction stats
            likes_given_result = await session.execute(
                select(func.count(Interaction.id)).where(
                    and_(
                        Interaction.user_id == user_id,
                        Interaction.interaction_type == "like",
                    )
                )
            )
            likes_given = likes_given_result.scalar()

            likes_received_result = await session.execute(
                select(func.count(Interaction.id)).where(
                    and_(
                        Interaction.target_id == user_id,
                        Interaction.interaction_type == "like",
                    )
                )
            )
            likes_received = likes_received_result.scalar()

            # Get matches count
            matches_result = await session.execute(
                select(func.count(Match.id)).where(
                    or_(Match.user1_id == user_id, Match.user2_id == user_id)
                )
            )
            matches_count = matches_result.scalar()

            user_data = {
                "id": user.id,
                "tg_id": user.tg_id,
                "username": user.username,
                "first_name": user.first_name,
                "language_code": user.language_code,
                "is_premium": user.is_premium,
                "is_banned": user.is_banned,
                "created_at": user.created_at.isoformat(),
                "updated_at": user.updated_at.isoformat(),
                "stats": {
                    "likes_given": likes_given,
                    "likes_received": likes_received,
                    "matches": matches_count,
                },
            }

            if profile:
                user_data["profile"] = {
                    "id": profile.id,
                    "name": profile.name,
                    "birth_date": profile.birth_date.isoformat(),
                    "gender": profile.gender,
                    "orientation": profile.orientation,
                    "goal": profile.goal,
                    "bio": profile.bio,
                    "city": profile.city,
                    "interests": profile.interests or [],
                    "height_cm": profile.height_cm,
                    "education": profile.education,
                    "is_visible": profile.is_visible,
                    "is_complete": profile.is_complete,
                }

            if photos:
                user_data["photos"] = [
                    {
                        "id": photo.id,
                        "url": photo.url,
                        "sort_order": photo.sort_order,
                        "is_verified": photo.is_verified,
                        "safe_score": photo.safe_score,
                        "created_at": photo.created_at.isoformat(),
                    }
                    for photo in photos
                ]

            return web.json_response(user_data)

    except ValueError:
        return web.json_response({"error": "Invalid user ID"}, status=400)
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def update_user_handler(request: web.Request) -> web.Response:
    """Update user information."""
    try:
        user_id = int(request.match_info["user_id"])
        data = await request.json()

        session_maker = request.app["session_maker"]
        async with session_maker() as session:
            user_result = await session.execute(select(User).where(User.id == user_id))
            user = user_result.scalar_one_or_none()

            if not user:
                return web.json_response({"error": "User not found"}, status=404)

            # Update allowed fields
            if "is_banned" in data:
                user.is_banned = bool(data["is_banned"])
            if "is_premium" in data:
                user.is_premium = bool(data["is_premium"])

            user.updated_at = datetime.now(timezone.utc)
            await session.commit()

            return web.json_response(
                {
                    "id": user.id,
                    "is_banned": user.is_banned,
                    "is_premium": user.is_premium,
                    "updated_at": user.updated_at.isoformat(),
                }
            )

    except ValueError:
        return web.json_response({"error": "Invalid user ID"}, status=400)
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def list_photos_handler(request: web.Request) -> web.Response:
    """List photos for moderation."""
    try:
        page = int(request.query.get("page", "1"))
        per_page = min(int(request.query.get("per_page", "20")), 100)
        verified_only = request.query.get("verified") == "true"
        unverified_only = request.query.get("unverified") == "true"

        offset = (page - 1) * per_page

        session_maker = request.app["session_maker"]
        async with session_maker() as session:
            query = select(Photo).order_by(Photo.created_at.desc())

            if verified_only:
                query = query.where(Photo.is_verified)
            elif unverified_only:
                query = query.where(~Photo.is_verified)

            # Count total
            count_query = select(func.count()).select_from(query.subquery())
            total_result = await session.execute(count_query)
            total = total_result.scalar()

            # Get page
            query = query.offset(offset).limit(per_page)
            result = await session.execute(query)
            photos = result.scalars().all()

            photos_data = []
            for photo in photos:
                photos_data.append(
                    {
                        "id": photo.id,
                        "user_id": photo.user_id,
                        "url": photo.url,
                        "sort_order": photo.sort_order,
                        "is_verified": photo.is_verified,
                        "safe_score": photo.safe_score,
                        "created_at": photo.created_at.isoformat(),
                    }
                )

            return web.json_response(
                {
                    "photos": photos_data,
                    "total": total,
                    "page": page,
                    "per_page": per_page,
                    "pages": (total + per_page - 1) // per_page,
                }
            )

    except Exception as e:
        logger.error(f"Error listing photos: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def update_photo_handler(request: web.Request) -> web.Response:
    """Update photo (verify/reject)."""
    try:
        photo_id = int(request.match_info["photo_id"])
        data = await request.json()

        session_maker = request.app["session_maker"]
        async with session_maker() as session:
            photo_result = await session.execute(
                select(Photo).where(Photo.id == photo_id)
            )
            photo = photo_result.scalar_one_or_none()

            if not photo:
                return web.json_response({"error": "Photo not found"}, status=404)

            if "is_verified" in data:
                photo.is_verified = bool(data["is_verified"])

            await session.commit()

            return web.json_response({"id": photo.id, "is_verified": photo.is_verified})

    except ValueError:
        return web.json_response({"error": "Invalid photo ID"}, status=400)
    except Exception as e:
        logger.error(f"Error updating photo: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def delete_photo_handler(request: web.Request) -> web.Response:
    """Delete a photo."""
    try:
        photo_id = int(request.match_info["photo_id"])

        session_maker = request.app["session_maker"]
        async with session_maker() as session:
            photo_result = await session.execute(
                select(Photo).where(Photo.id == photo_id)
            )
            photo = photo_result.scalar_one_or_none()

            if not photo:
                return web.json_response({"error": "Photo not found"}, status=404)

            await session.delete(photo)
            await session.commit()

            return web.json_response({"success": True})

    except ValueError:
        return web.json_response({"error": "Invalid photo ID"}, status=400)
    except Exception as e:
        logger.error(f"Error deleting photo: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def health_check(request: web.Request) -> web.Response:
    """Health check endpoint."""
    return web.json_response({"status": "healthy", "service": "admin"})


def create_app(config: dict) -> web.Application:
    """Create and configure the admin service application."""
    app = web.Application()
    app["config"] = config

    # Create database session maker
    engine = create_async_engine(config["database_url"], echo=False)
    app["session_maker"] = async_sessionmaker(engine, expire_on_commit=False)

    # Add routes
    app.router.add_post("/admin/login", login_handler)
    app.router.add_get("/admin/stats", get_stats_handler)
    app.router.add_get("/admin/users", list_users_handler)
    app.router.add_get("/admin/users/{user_id}", get_user_handler)
    app.router.add_put("/admin/users/{user_id}", update_user_handler)
    app.router.add_get("/admin/photos", list_photos_handler)
    app.router.add_put("/admin/photos/{photo_id}", update_photo_handler)
    app.router.add_delete("/admin/photos/{photo_id}", delete_photo_handler)
    app.router.add_get("/health", health_check)

    # Serve static files for admin panel
    app.router.add_static(
        "/admin-panel/",
        path=os.path.join(os.path.dirname(__file__), "static"),
        name="static",
    )

    return app


if __name__ == "__main__":
    # Configure structured logging
    configure_logging("admin-service", os.getenv("LOG_LEVEL", "INFO"))

    config = {
        "jwt_secret": os.getenv("JWT_SECRET", "your-secret-key"),
        "database_url": os.getenv(
            "DATABASE_URL", "postgresql+asyncpg://dating:dating@localhost:5432/dating"
        ),
        "host": os.getenv("ADMIN_SERVICE_HOST", "0.0.0.0"),
        "port": int(os.getenv("ADMIN_SERVICE_PORT", 8086)),
    }

    logger.info(
        "Starting admin-service",
        extra={"event_type": "service_start", "port": config["port"]},
    )

    app = create_app(config)
    web.run_app(app, host=config["host"], port=config["port"])
