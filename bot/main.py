"""Minimal bot entry point - infrastructure only."""

import asyncio
import json
import logging
import os

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, WebAppInfo

from core.utils.logging import configure_logging

from .api_client import APIGatewayClient
from .config import load_config
from .geo import process_location_data
from .validation import validate_profile_data

# Create router for handlers
router = Router()


@router.message(Command("start"))
async def start_handler(message: Message) -> None:
    """Send welcome message with WebApp button."""
    config = load_config()

    if not config.webapp_url:
        await message.answer(
            "⚠️ WebApp is not configured. " "Please set WEBAPP_URL environment variable."
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
    including validation and API Gateway communication.
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
            extra={
                "event_type": "webapp_data_received",
                "user_id": message.from_user.id,
            },
        )

        # Get API client from dispatcher workflow_data
        api_client = dispatcher.workflow_data.get("api_client")
        if not api_client:
            logger.error("API client not configured")
            await message.answer("❌ API Gateway not configured")
            return

        if action == "create_profile":
            await handle_create_profile(message, data, api_client, logger)
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
    api_client: APIGatewayClient,
    logger: logging.Logger,
) -> None:
    """Handle profile creation via API Gateway.

    Note: Photos are not sent via sendData() due to the 4KB size limit.
    Photos should be uploaded separately via HTTP API.
    """
    profile_data = data.get("profile", {})

    # Validate profile data
    is_valid, error = validate_profile_data(profile_data)
    if not is_valid:
        await message.answer(f"❌ Validation error: {error}")
        return

    try:
        # Add Telegram user info to profile data
        profile_data["telegram_id"] = message.from_user.id
        profile_data["username"] = message.from_user.username
        profile_data["first_name"] = message.from_user.first_name
        profile_data["language_code"] = message.from_user.language_code
        profile_data["is_premium"] = message.from_user.is_premium or False

        # Process location data
        location = process_location_data(
            latitude=profile_data.get("latitude"),
            longitude=profile_data.get("longitude"),
            country=profile_data.get("country"),
            city=profile_data.get("city"),
        )

        # Add location to profile data
        profile_data.update(location)

        # Convert birth_date string to ISO format if needed
        if "birth_date" in profile_data and isinstance(profile_data["birth_date"], str):
            # Keep as string for API - service will handle conversion
            pass

        # Mark profile as complete when all required fields are present
        # Photos are uploaded separately via HTTP API and don't affect completion
        profile_data["is_complete"] = True

        # Create profile via API Gateway
        result = await api_client.create_profile(profile_data)

        logger.info(
            "Profile created successfully via API Gateway",
            extra={
                "event_type": "profile_created",
                "user_id": message.from_user.id,
            },
        )

        # Note: Photos are uploaded via HTTP API (see bot/api.py upload_photo_handler)
        # The photo_count reflects photos already uploaded to the server
        photo_count = profile_data.get("photo_count", 0)
        photo_status = (
            f"📸 Фото: {photo_count}" if photo_count > 0 else "📸 Фото: не загружены"
        )

        # Extract profile info from result
        profile_name = result.get("name", profile_data.get("name", ""))
        profile_gender = result.get("gender", profile_data.get("gender", ""))
        profile_goal = result.get("goal", profile_data.get("goal", ""))
        profile_city = result.get("city", profile_data.get("city", "не указан"))
        profile_birth_date = profile_data.get("birth_date", "")

        await message.answer(
            "✅ Профиль создан!\n\n"
            f"Имя: {profile_name}\n"
            f"Возраст: {profile_birth_date}\n"
            f"Пол: {profile_gender}\n"
            f"Цель: {profile_goal}\n"
            f"Город: {profile_city}\n"
            f"{photo_status}"
        )
    except Exception as e:
        logger.error(
            f"Failed to create profile via API Gateway: {e}",
            exc_info=True,
            extra={
                "event_type": "profile_creation_failed",
                "user_id": message.from_user.id,
            },
        )
        await message.answer("❌ Не удалось создать профиль. Попробуйте позже.")


async def main() -> None:
    """Bootstrap the bot and API server."""
    configure_logging("telegram-bot", os.getenv("LOG_LEVEL", "INFO"))
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
            },
        )
    except Exception as exc:
        logger.error(
            f"Failed to load configuration: {exc}",
            exc_info=True,
            extra={"event_type": "config_error"},
        )
        raise

    try:
        # Validate token format before creating Bot instance
        if not config.token or len(config.token) < 5:
            logger.error(
                "Invalid BOT_TOKEN: token is empty or too short",
                extra={"event_type": "invalid_token"},
            )
            raise ValueError("BOT_TOKEN is not properly configured")

        logger.info(
            "Creating bot instance...", extra={"event_type": "bot_creation_start"}
        )
        bot = Bot(token=config.token)

        # Try to get bot info to validate token early
        try:
            bot_info = await bot.get_me()
            logger.info(
                f"Bot authenticated successfully: @{bot_info.username}",
                extra={
                    "event_type": "bot_authenticated",
                    "bot_username": bot_info.username,
                    "bot_id": bot_info.id,
                },
            )
        except Exception as e:
            logger.error(
                f"Failed to authenticate with Telegram: {e}",
                exc_info=True,
                extra={"event_type": "telegram_auth_failed"},
            )
            raise ValueError(
                "Failed to authenticate with Telegram API. "
                "Please check your BOT_TOKEN is valid and Telegram API is accessible."
            ) from e

        logger.info("Bot instance created", extra={"event_type": "bot_created"})

        dp = Dispatcher(storage=MemoryStorage())

        # Initialize API Gateway client (thin client architecture)
        if config.api_gateway_url:
            api_client = APIGatewayClient(config.api_gateway_url)
            # Store API client in dispatcher workflow_data (aiogram 3.x pattern)
            dp.workflow_data["api_client"] = api_client
            logger.info(
                "API Gateway client initialized",
                extra={
                    "event_type": "api_client_initialized",
                    "gateway_url": config.api_gateway_url,
                },
            )
        else:
            logger.warning(
                "API Gateway URL not configured - profile creation will not work",
                extra={"event_type": "api_gateway_not_configured"},
            )

        dp.include_router(router)
        logger.info(
            "Dispatcher initialized with MemoryStorage",
            extra={"event_type": "dispatcher_initialized"},
        )

        # Start both bot and API server concurrently
        logger.info(
            "Starting bot polling", extra={"event_type": "services_start"}
        )

        # Bot now uses thin client architecture through API Gateway
        # The bot/api.py server is kept for backward compatibility with WebApp
        # but should eventually also use API Gateway client

        # For now, we can optionally run the API server if database_url is provided
        # This allows gradual migration
        api_server_task = None
        if config.database_url:
            from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
            from sqlalchemy.orm import sessionmaker

            from .api import run_api_server

            # Initialize database for bot/api.py backward compatibility
            engine = create_async_engine(config.database_url, echo=False)
            async_session_maker = sessionmaker(
                engine, class_=AsyncSession, expire_on_commit=False
            )

            # Get API server configuration
            api_host = os.getenv("API_HOST", "0.0.0.0")
            api_port = int(os.getenv("API_PORT", "8080"))

            api_server_task = run_api_server(config, async_session_maker, api_host, api_port)
            logger.info(
                "Starting bot API server for backward compatibility",
                extra={"event_type": "api_server_start"},
            )

        # Run bot polling (and optionally API server)
        if api_server_task:
            await asyncio.gather(dp.start_polling(bot), api_server_task)
        else:
            await dp.start_polling(bot)
    except Exception as exc:
        logger.error(
            f"Error during bot execution: {exc}",
            exc_info=True,
            extra={"event_type": "bot_error"},
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
