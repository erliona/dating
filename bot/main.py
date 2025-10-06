"""Minimal bot entry point - infrastructure only.

Bot role (minimalist):
- Welcome message with WebApp button (/start)
- Notification management (/notifications)
- Push notifications (matches, messages, likes)

All user interactions happen in WebApp which communicates directly with API Gateway.
"""

import asyncio
import logging
import os
from typing import Any, Dict

from aiogram import Bot, Dispatcher, Router
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import KeyboardButton, Message, ReplyKeyboardMarkup, WebAppInfo

from core.utils.logging import configure_logging

from .api_client import APIGatewayClient
from .config import load_config

# Create router for handlers
router = Router()

# Bot instance for notifications (set during initialization)
_bot_instance: Bot = None


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


@router.message(Command("notifications"))
async def toggle_notifications(message: Message) -> None:
    """Toggle notifications on/off for the user.

    In future implementation, this would update user preferences in the database.
    For now, it provides user feedback about notification management.
    """
    logger = logging.getLogger(__name__)

    logger.info(
        "Notification toggle requested",
        extra={
            "event_type": "notification_toggle",
            "user_id": message.from_user.id,
        },
    )

    await message.answer(
        "🔔 Управление уведомлениями\n\n"
        "Настройки уведомлений можно изменить в Mini App в разделе 'Настройки'.\n\n"
        "Вы можете получать уведомления о:\n"
        "• Новых матчах 💕\n"
        "• Новых сообщениях 💬\n"
        "• Лайках ❤️"
    )


# Notification handlers for API Gateway
async def send_match_notification(user_id: int, match_data: Dict[str, Any]) -> bool:
    """Send notification about a new match.

    Args:
        user_id: Telegram user ID
        match_data: Match information (name, photo, etc.)

    Returns:
        True if notification was sent successfully
    """
    logger = logging.getLogger(__name__)

    if not _bot_instance:
        logger.error("Bot instance not initialized")
        return False

    try:
        match_name = match_data.get("name", "Someone")
        match_id = match_data.get("id", "")

        message_text = f"💕 У вас новый матч!\n\n{match_name} тоже лайкнул(а) вас!"

        await _bot_instance.send_message(chat_id=user_id, text=message_text)

        logger.info(
            "Match notification sent",
            extra={
                "event_type": "match_notification_sent",
                "user_id": user_id,
                "match_id": match_id,
            },
        )
        return True

    except Exception as e:
        logger.error(
            f"Failed to send match notification: {e}",
            exc_info=True,
            extra={
                "event_type": "match_notification_failed",
                "user_id": user_id,
            },
        )
        return False


async def send_message_notification(user_id: int, message_data: Dict[str, Any]) -> bool:
    """Send notification about a new message.

    Args:
        user_id: Telegram user ID
        message_data: Message information (sender, preview, etc.)

    Returns:
        True if notification was sent successfully
    """
    logger = logging.getLogger(__name__)

    if not _bot_instance:
        logger.error("Bot instance not initialized")
        return False

    try:
        sender_name = message_data.get("sender_name", "Someone")
        message_preview = message_data.get("preview", "...")

        message_text = f"💬 Новое сообщение от {sender_name}\n\n{message_preview}"

        await _bot_instance.send_message(chat_id=user_id, text=message_text)

        logger.info(
            "Message notification sent",
            extra={
                "event_type": "message_notification_sent",
                "user_id": user_id,
            },
        )
        return True

    except Exception as e:
        logger.error(
            f"Failed to send message notification: {e}",
            exc_info=True,
            extra={
                "event_type": "message_notification_failed",
                "user_id": user_id,
            },
        )
        return False


async def send_like_notification(user_id: int, like_data: Dict[str, Any]) -> bool:
    """Send notification about receiving a like.

    Args:
        user_id: Telegram user ID
        like_data: Like information (sender name, etc.)

    Returns:
        True if notification was sent successfully
    """
    logger = logging.getLogger(__name__)

    if not _bot_instance:
        logger.error("Bot instance not initialized")
        return False

    try:
        liker_name = like_data.get("name", "Someone")

        message_text = f"❤️ {liker_name} лайкнул(а) вас!"

        await _bot_instance.send_message(chat_id=user_id, text=message_text)

        logger.info(
            "Like notification sent",
            extra={
                "event_type": "like_notification_sent",
                "user_id": user_id,
            },
        )
        return True

    except Exception as e:
        logger.error(
            f"Failed to send like notification: {e}",
            exc_info=True,
            extra={
                "event_type": "like_notification_failed",
                "user_id": user_id,
            },
        )
        return False


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

        # Store bot instance globally for notification handlers
        global _bot_instance
        _bot_instance = bot

        dp = Dispatcher(storage=MemoryStorage())

        # Initialize API Gateway client (thin client architecture)
        api_client = None
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
        logger.info("Starting bot polling", extra={"event_type": "services_start"})

        # Bot now uses thin client architecture through API Gateway
        # The bot/api.py server now also uses API Gateway instead of direct DB access

        # Start API server for WebApp (requires API Gateway)
        api_server_task = None
        if api_client:
            from .api import run_api_server

            # Get API server configuration
            api_host = os.getenv("API_HOST", "0.0.0.0")
            api_port = int(os.getenv("API_PORT", "8080"))

            # Use API Gateway client for WebApp endpoints
            api_server_task = run_api_server(
                config,
                api_client=api_client,
                host=api_host,
                port=api_port,
            )
            logger.info(
                "Starting bot API server (thin client mode)",
                extra={"event_type": "api_server_start", "mode": "thin_client"},
            )
        else:
            logger.warning(
                "Bot API server not started - API Gateway URL is required",
                extra={"event_type": "api_server_not_started"},
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
