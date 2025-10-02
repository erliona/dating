"""Minimal bot entry point - infrastructure only."""

import asyncio
import json
import logging
import sys
from datetime import datetime

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

# Create router for handlers
router = Router()


class JsonFormatter(logging.Formatter):
    """JSON formatter for structured logging."""
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON."""
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields if present
        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id
        if hasattr(record, "event_type"):
            log_data["event_type"] = record.event_type
        
        return json.dumps(log_data)


def configure_logging():
    """Configure JSON logging for structured logs."""
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(logging.INFO)

    # Configure aiogram loggers to reduce noise
    logging.getLogger("aiogram").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)


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
    """Handle profile creation."""
    profile_data = data.get("profile", {})
    
    # Validate profile data
    is_valid, error = validate_profile_data(profile_data)
    if not is_valid:
        await message.answer(f"❌ Validation error: {error}")
        return
    
    # Create or update user
    user = await repository.create_or_update_user(
        tg_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        language_code=message.from_user.language_code,
        is_premium=message.from_user.is_premium or False
    )
    
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
    
    # Mark profile as complete if all required data is present
    profile_data["is_complete"] = True
    
    # Create profile
    profile = await repository.create_profile(user.id, profile_data)
    await session.commit()
    
    logger.info(
        "Profile created successfully",
        extra={
            "event_type": "profile_created",
            "user_id": message.from_user.id,
            "profile_id": profile.id
        }
    )
    
    await message.answer(
        "✅ Профиль создан!\n\n"
        f"Имя: {profile.name}\n"
        f"Возраст: {profile.birth_date}\n"
        f"Пол: {profile.gender}\n"
        f"Цель: {profile.goal}\n"
        f"Город: {profile.city or 'не указан'}"
    )


async def main() -> None:
    """Bootstrap the bot."""
    configure_logging()
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
        bot = Bot(token=config.token)
        logger.info("Bot instance created", extra={"event_type": "bot_created"})
        
        dp = Dispatcher(storage=MemoryStorage())
        
        # Initialize database if configured
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
        
        logger.info("Starting polling", extra={"event_type": "polling_start"})
        await dp.start_polling(bot)
    except Exception as exc:
        logger.error(
            f"Error during bot execution: {exc}",
            exc_info=True,
            extra={"event_type": "bot_error"}
        )
        raise
    finally:
        logger.info("Shutting down bot", extra={"event_type": "shutdown"})


if __name__ == "__main__":
    asyncio.run(main())
