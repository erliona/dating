"""Profile service main entry point.

This microservice handles user profile management using core services.
"""

import logging

from aiohttp import web
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from adapters.telegram.repository import TelegramProfileRepository
from core.services import ProfileService
from core.utils.logging import configure_logging

logger = logging.getLogger(__name__)


async def get_profile(request: web.Request) -> web.Response:
    """Get user profile.

    GET /profiles/{user_id}
    """
    user_id = int(request.match_info["user_id"])

    profile_service: ProfileService = request.app["profile_service"]
    profile = await profile_service.get_profile(user_id)

    if not profile:
        return web.json_response({"error": "Profile not found"}, status=404)

    return web.json_response(
        {
            "user_id": profile.user_id,
            "name": profile.name,
            "age": profile.age,
            "gender": profile.gender.value,
            "city": profile.city,
            "bio": profile.bio,
            "photos": profile.photos,
        }
    )


async def create_profile(request: web.Request) -> web.Response:
    """Create user profile.

    POST /profiles/

    Accepts comprehensive profile data from bot or other clients.
    """
    data = await request.json()

    try:
        from datetime import date

        # Get or create session
        session_maker = request.app["session_maker"]

        async with session_maker() as session:
            from bot.repository import ProfileRepository

            repository = ProfileRepository(session)

            # Handle Telegram user creation if telegram_id is provided
            telegram_id = data.get("telegram_id")
            if telegram_id:
                user = await repository.create_or_update_user(
                    tg_id=telegram_id,
                    username=data.get("username"),
                    first_name=data.get("first_name"),
                    language_code=data.get("language_code"),
                    is_premium=data.get("is_premium", False),
                )
                user_id = user.id
            else:
                # Use provided user_id
                user_id = data.get("user_id")
                if not user_id:
                    return web.json_response(
                        {"error": "Either user_id or telegram_id is required"},
                        status=400,
                    )

            # Check if profile already exists
            existing_profile = await repository.get_profile_by_user_id(user_id)
            if existing_profile:
                return web.json_response(
                    {"error": "Profile already exists for this user"}, status=409
                )

            # Parse birth_date
            birth_date_str = data.get("birth_date")
            birth_date = None
            if birth_date_str is not None:
                if isinstance(birth_date_str, str):
                    try:
                        birth_date = date.fromisoformat(birth_date_str)
                    except ValueError:
                        return web.json_response(
                            {
                                "error": "Invalid birth_date format. Expected ISO format (YYYY-MM-DD)."
                            },
                            status=400,
                        )
                else:
                    birth_date = birth_date_str
            else:
                return web.json_response(
                    {"error": "birth_date is required."}, status=400
                )

            # Prepare profile data
            profile_data = {
                "name": data["name"],
                "birth_date": birth_date,
                "gender": data["gender"],
                "orientation": data["orientation"],
                "goal": data.get("goal"),
                "bio": data.get("bio"),
                "interests": data.get("interests", []),
                "height_cm": data.get("height_cm"),
                "education": data.get("education"),
                "has_children": data.get("has_children"),
                "wants_children": data.get("wants_children"),
                "smoking": data.get("smoking"),
                "drinking": data.get("drinking"),
                "country": data.get("country"),
                "city": data.get("city"),
                "geohash": data.get("geohash"),
                "latitude": data.get("latitude"),
                "longitude": data.get("longitude"),
                "hide_distance": data.get("hide_distance", False),
                "hide_online": data.get("hide_online", False),
                "hide_age": data.get("hide_age", False),
                "allow_messages_from": data.get("allow_messages_from", "matches"),
                "is_complete": data.get("is_complete", True),
            }

            # Create profile
            profile = await repository.create_profile(user_id, profile_data)

            # Commit the transaction
            await session.commit()

            logger.info(
                f"Profile created for user {user_id}",
                extra={
                    "event_type": "profile_created",
                    "user_id": user_id,
                    "profile_id": profile.id,
                },
            )

            return web.json_response(
                {
                    "user_id": profile.user_id,
                    "name": profile.name,
                    "gender": profile.gender,
                    "city": profile.city,
                    "goal": profile.goal,
                    "created": True,
                },
                status=201,
            )

    except KeyError as e:
        return web.json_response({"error": f"Missing required field: {e}"}, status=400)
    except ValueError as e:
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"Error creating profile: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def health_check(request: web.Request) -> web.Response:
    """Health check endpoint."""
    return web.json_response({"status": "healthy", "service": "profile"})


def create_app(config: dict) -> web.Application:
    """Create and configure the profile service application."""
    app = web.Application()
    app["config"] = config

    # Initialize database and services
    engine = create_async_engine(config["database_url"])
    async_session_maker = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )

    # Create profile service with Telegram adapter
    async def get_session():
        async with async_session_maker() as session:
            return session

    # Store in app context (simplified - in production use dependency injection)
    app["engine"] = engine
    app["session_maker"] = async_session_maker

    # Add routes
    app.router.add_get("/profiles/{user_id}", get_profile)
    app.router.add_post("/profiles", create_profile)
    app.router.add_get("/health", health_check)

    return app


if __name__ == "__main__":
    import os

    # Configure structured logging
    configure_logging("profile-service", os.getenv("LOG_LEVEL", "INFO"))

    config = {
        "database_url": os.getenv(
            "DATABASE_URL", "postgresql+asyncpg://dating:dating@localhost/dating"
        ),
        "host": os.getenv("PROFILE_SERVICE_HOST", "0.0.0.0"),
        "port": int(os.getenv("PROFILE_SERVICE_PORT", 8082)),
    }

    logger.info(
        "Starting profile-service",
        extra={"event_type": "service_start", "port": config["port"]},
    )

    app = create_app(config)
    web.run_app(app, host=config["host"], port=config["port"])
