"""Minimal bot entry point - infrastructure only."""

import asyncio
import logging
import os

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, WebAppInfo
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from .config import load_config
from .geo import process_location_data
from .repository import ProfileRepository
from .validation import validate_profile_data
from core.utils.logging import configure_logging

# Create router for handlers
router = Router()


@router.message(Command("start"))
async def start_handler(message: Message) -> None:
    """Send welcome message with WebApp button."""
    config = load_config()
    
    if not config.webapp_url:
        await message.answer(
            "⚠️ WebApp is not configured. "
            "Please set WEBAPP_URL environment variable."
        )
        return
    
    # Create keyboard with WebApp button
    keyboard = ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="🚀 Открыть Mini App",
                    web_app=WebAppInfo(url=config.webapp_url),
                )
            ]
        ],
        resize_keyboard=True,
    )
    
    await message.answer(
        "👋 Добро пожаловать в Dating Mini App!\n\n"
        "Нажмите кнопку ниже, чтобы открыть приложение и создать свою анкету.",
        reply_markup=keyboard,
    )


@router.message(lambda m: m.web_app_data is not None)
async def handle_webapp_data(message: Message, dispatcher: Dispatcher) -> None:
    """Handle data received from WebApp.
    
    This handler processes profile data submitted from the Mini App,
    including validation and database storage.
    """
    logger = logging.getLogger(__name__)
    
    if not message.web_app_data:
        await message.answer("❌ No WebApp data received")
        return
    
    try:
        # Parse WebApp data
        data = json.loads(message.web_app_data.data)
        action = data.get("action")
        
        logger.info(
            f"WebApp data received: {action}",
            extra={"event_type": "webapp_data_received", "user_id": message.from_user.id}
        )
        
        # Get database session from dispatcher workflow_data
        session_maker = dispatcher.workflow_data.get("session_maker")
        if not session_maker:
            logger.error("Database not configured")
            await message.answer("❌ Database not configured")
            return
        
        async with session_maker() as session:
            repository = ProfileRepository(session)
            
            if action == "create_profile":
                await handle_create_profile(message, data, repository, session, logger)
            else:
                await message.answer(f"❌ Unknown action: {action}")
    
    except json.JSONDecodeError:
        logger.error("Failed to parse WebApp data", exc_info=True)
        await message.answer("❌ Invalid data format")
    except Exception as exc:
        logger.error(f"Error processing WebApp data: {exc}", exc_info=True)
        await message.answer("❌ Failed to process data")


async def handle_create_profile(
    message: Message,
    data: dict,
    repository: ProfileRepository,
    session: AsyncSession,
    logger: logging.Logger
) -> None:
    """Handle profile creation.
    
    Note: Photos are not sent via sendData() due to the 4KB size limit.
    Photos should be uploaded separately via HTTP API in a future update.
    """
    profile_data = data.get("profile", {})
    
    # Validate profile data
    is_valid, error = validate_profile_data(profile_data)
    if not is_valid:
        await message.answer(f"❌ Validation error: {error}")
        return
    
    try:
        # Create or update user
        user = await repository.create_or_update_user(
            tg_id=message.from_user.id,
            username=message.from_user.username,
            first_name=message.from_user.first_name,
            language_code=message.from_user.language_code,
            is_premium=message.from_user.is_premium or False
        )
        
        # Check if profile already exists
        existing_profile = await repository.get_profile_by_user_id(user.id)
        if existing_profile:
            await message.answer("❌ У вас уже есть профиль!")
            return
        
        # Process location data
        location = process_location_data(
            latitude=profile_data.get("latitude"),
            longitude=profile_data.get("longitude"),
            country=profile_data.get("country"),
            city=profile_data.get("city")
        )
        
        # Add location to profile data
        profile_data.update(location)
        
        # Convert birth_date string to date object if needed
        if "birth_date" in profile_data and isinstance(profile_data["birth_date"], str):
            profile_data["birth_date"] = datetime.strptime(
                profile_data["birth_date"], "%Y-%m-%d"
            ).date()
        
        # Mark profile as complete when all required fields are present
        # Photos are uploaded separately via HTTP API and don't affect completion
        profile_data["is_complete"] = True
        
        # Create profile
        profile = await repository.create_profile(user.id, profile_data)
        
        # Commit the transaction (both user and profile creation)
        await session.commit()
        
        logger.info(
            "Profile created successfully",
            extra={
                "event_type": "profile_created",
                "user_id": message.from_user.id,
                "profile_id": profile.id
            }
        )
        
        # Note: Photos are uploaded via HTTP API (see bot/api.py upload_photo_handler)
        # The photo_count reflects photos already uploaded to the server
        photo_count = profile_data.get("photo_count", 0)
        photo_status = f"📸 Фото: {photo_count}" if photo_count > 0 else "📸 Фото: не загружены"
        
        await message.answer(
            "✅ Профиль создан!\n\n"
            f"Имя: {profile.name}\n"
            f"Возраст: {profile.birth_date}\n"
            f"Пол: {profile.gender}\n"
            f"Цель: {profile.goal}\n"
            f"Город: {profile.city or 'не указан'}\n"
            f"{photo_status}"
        )
    except Exception as e:
        # Rollback transaction on any error
        await session.rollback()
        logger.error(
            f"Failed to create profile: {e}",
            exc_info=True,
            extra={
                "event_type": "profile_creation_failed",
                "user_id": message.from_user.id
            }
        )
        await message.answer("❌ Не удалось создать профиль. Попробуйте позже.")


async def main() -> None:
    """Bootstrap the bot and API server."""
    configure_logging('telegram-bot', os.getenv('LOG_LEVEL', 'INFO'))
    logger = logging.getLogger(__name__)
    logger.info("Bot initialization started", extra={"event_type": "startup"})
    
    try:
        config = load_config()
        logger.info(
            "Configuration loaded successfully",
            extra={
                "event_type": "config_loaded",
                "webapp_url": config.webapp_url,
                "database_configured": bool(config.database_url),
            }
        )
    except Exception as exc:
        logger.error(
            f"Failed to load configuration: {exc}",
            exc_info=True,
            extra={"event_type": "config_error"}
        )
        raise
    
    try:
        # Validate token format before creating Bot instance
        if not config.token or len(config.token) < 5:
            logger.error(
                "Invalid BOT_TOKEN: token is empty or too short",
                extra={"event_type": "invalid_token"}
            )
            raise ValueError("BOT_TOKEN is not properly configured")
        
        logger.info("Creating bot instance...", extra={"event_type": "bot_creation_start"})
        bot = Bot(token=config.token)
        
        # Try to get bot info to validate token early
        try:
            bot_info = await bot.get_me()
            logger.info(
                f"Bot authenticated successfully: @{bot_info.username}",
                extra={
                    "event_type": "bot_authenticated",
                    "bot_username": bot_info.username,
                    "bot_id": bot_info.id
                }
            )
        except Exception as e:
            logger.error(
                f"Failed to authenticate with Telegram: {e}",
                exc_info=True,
                extra={"event_type": "telegram_auth_failed"}
            )
            raise ValueError(
                "Failed to authenticate with Telegram API. "
                "Please check your BOT_TOKEN is valid and Telegram API is accessible."
            ) from e
        
        logger.info("Bot instance created", extra={"event_type": "bot_created"})
        
        dp = Dispatcher(storage=MemoryStorage())
        
        # Initialize database if configured
        async_session_maker = None
        if config.database_url:
            engine = create_async_engine(config.database_url, echo=False)
            async_session_maker = sessionmaker(
                engine, class_=AsyncSession, expire_on_commit=False
            )
            # Store session maker in dispatcher workflow_data (aiogram 3.x pattern)
            dp.workflow_data["session_maker"] = async_session_maker
            logger.info("Database connection initialized", extra={"event_type": "db_initialized"})
        else:
            logger.warning(
                "Database URL not configured - profile creation will not work",
                extra={"event_type": "db_not_configured"}
            )
        
        dp.include_router(router)
        logger.info(
            "Dispatcher initialized with MemoryStorage",
            extra={"event_type": "dispatcher_initialized"}
        )
        
        # Start both bot and API server concurrently
        logger.info("Starting bot and API server", extra={"event_type": "services_start"})
        
        # Import API module
        from .api import run_api_server
        import os
        
        # Get API server configuration
        api_host = os.getenv("API_HOST", "0.0.0.0")
        api_port = int(os.getenv("API_PORT", "8080"))
        
        # Prepare API server coroutine
        async def noop():
            """No-op coroutine for when API server is not needed."""
            pass
        
        api_server_task = run_api_server(config, async_session_maker, api_host, api_port) if async_session_maker else noop()
        
        # Run both services concurrently
        await asyncio.gather(
            dp.start_polling(bot),
            api_server_task
        )
    except Exception as exc:
        logger.error(
            f"Error during bot execution: {exc}",
            exc_info=True,
            extra={"event_type": "bot_error"}
        )
        raise
    finally:
        logger.info("Shutting down bot", extra={"event_type": "shutdown"})
        try:
            await bot.session.close()
        except Exception:
            pass


if __name__ == "__main__":
    asyncio.run(main())
