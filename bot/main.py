from __future__ import annotations

"""Minimal bot entry point - notifications only.

Bot role:
- Receive notification requests from notification service
- Send push notifications to users (matches, messages, likes)

All user interactions happen in WebApp which communicates directly with API Gateway.
The bot no longer has any command handlers or HTTP API server.
"""

import asyncio
import logging
import os
from typing import Any, Dict

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message
from aiogram.filters import CommandStart
from aiohttp import web

from core.utils.logging import configure_logging

from .config import load_config

# Bot instance for notifications (set during initialization)
_bot_instance: Bot = None
_dp_instance: Dispatcher = None


# Command handlers
async def start_command_handler(message: Message) -> None:
    """Handle /start command."""
    logger = logging.getLogger(__name__)
    
    # Get WebApp URL from config
    webapp_url = os.getenv("WEBAPP_URL", "https://dating.serge.cc")
    
    # Create inline keyboard with WebApp button
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="🚀 Открыть Mini App",
            web_app=WebAppInfo(url=webapp_url)
        )]
    ])
    
    welcome_text = (
        "👋 Добро пожаловать в Dating App!\n\n"
        "🎯 Найди свою половинку\n"
        "💕 Общайся с интересными людьми\n"
        "📍 Встречайся рядом с тобой\n\n"
        "Нажми кнопку ниже, чтобы начать:"
    )
    
    await message.answer(welcome_text, reply_markup=keyboard)
    
    logger.info(
        f"Start command handled for user {message.from_user.id}",
        extra={"event_type": "start_command", "user_id": message.from_user.id}
    )


# HTTP handlers for receiving notification requests from notification service
async def send_match_notification_handler(request: web.Request) -> web.Response:
    """HTTP endpoint to send match notification.

    POST /notifications/match
    Body: {
        "user_id": int,
        "match_data": {
            "id": int,
            "name": str,
            "photo_url": str (optional)
        }
    }
    """
    try:
        data = await request.json()
        user_id = data.get("user_id")
        match_data = data.get("match_data", {})

        if not user_id:
            return web.json_response({"error": "user_id is required"}, status=400)

        success = await send_match_notification(user_id, match_data)

        if success:
            return web.json_response({"status": "sent", "user_id": user_id})
        else:
            return web.json_response({"error": "Failed to send notification"}, status=500)
    except Exception as e:
        logging.error(f"Error handling match notification request: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def send_message_notification_handler(request: web.Request) -> web.Response:
    """HTTP endpoint to send message notification.

    POST /notifications/message
    Body: {
        "user_id": int,
        "message_data": {
            "sender_name": str,
            "preview": str,
            "conversation_id": int (optional)
        }
    }
    """
    try:
        data = await request.json()
        user_id = data.get("user_id")
        message_data = data.get("message_data", {})

        if not user_id:
            return web.json_response({"error": "user_id is required"}, status=400)

        success = await send_message_notification(user_id, message_data)

        if success:
            return web.json_response({"status": "sent", "user_id": user_id})
        else:
            return web.json_response({"error": "Failed to send notification"}, status=500)
    except Exception as e:
        logging.error(f"Error handling message notification request: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def send_like_notification_handler(request: web.Request) -> web.Response:
    """HTTP endpoint to send like notification.

    POST /notifications/like
    Body: {
        "user_id": int,
        "like_data": {
            "name": str,
            "photo_url": str (optional)
        }
    }
    """
    try:
        data = await request.json()
        user_id = data.get("user_id")
        like_data = data.get("like_data", {})

        if not user_id:
            return web.json_response({"error": "user_id is required"}, status=400)

        success = await send_like_notification(user_id, like_data)

        if success:
            return web.json_response({"status": "sent", "user_id": user_id})
        else:
            return web.json_response({"error": "Failed to send notification"}, status=500)
    except Exception as e:
        logging.error(f"Error handling like notification request: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def health_check_handler(request: web.Request) -> web.Response:
    """Health check endpoint."""
    return web.json_response({"status": "ok", "service": "telegram-bot"})


# Internal notification sending functions
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


def create_notification_app() -> web.Application:
    """Create HTTP server for receiving notification requests."""
    app = web.Application()

    # Register notification endpoints
    app.router.add_post("/notifications/match", send_match_notification_handler)
    app.router.add_post("/notifications/message", send_message_notification_handler)
    app.router.add_post("/notifications/like", send_like_notification_handler)
    app.router.add_get("/health", health_check_handler)

    return app


async def run_notification_server(host: str = "0.0.0.0", port: int = 8080):
    """Run HTTP server for notification requests."""
    logger = logging.getLogger(__name__)

    app = create_notification_app()
    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, host, port)
    await site.start()

    logger.info(
        f"Notification HTTP server started on {host}:{port}",
        extra={"event_type": "notification_server_started", "host": host, "port": port},
    )

    # Keep running
    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()


async def run_bot_with_commands(host: str = "0.0.0.0", port: int = 8080):
    """Run both HTTP server for notifications and polling for commands."""
    logger = logging.getLogger(__name__)

    # Start HTTP server for notifications
    app = create_notification_app()
    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, host, port)
    await site.start()

    logger.info(
        f"Notification HTTP server started on {host}:{port}",
        extra={"event_type": "notification_server_started", "host": host, "port": port},
    )

    # Start polling for commands
    logger.info("Starting polling for commands", extra={"event_type": "polling_start"})
    
    try:
        # Run both HTTP server and polling concurrently
        await asyncio.gather(
            _dp_instance.start_polling(_bot_instance),
            asyncio.Event().wait()  # Keep HTTP server running
        )
    finally:
        await runner.cleanup()


async def main() -> None:
    """Bootstrap the bot notification server."""
    configure_logging("telegram-bot", os.getenv("LOG_LEVEL", "INFO"))
    logger = logging.getLogger(__name__)
    logger.info("Bot initialization started", extra={"event_type": "startup"})

    try:
        config = load_config()
        logger.info(
            "Configuration loaded successfully",
            extra={
                "event_type": "config_loaded",
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

        # Create dispatcher and register command handlers
        dp = Dispatcher(storage=MemoryStorage())
        dp.message.register(start_command_handler, CommandStart())
        
        # Store instances globally
        global _bot_instance, _dp_instance
        _bot_instance = bot
        _dp_instance = dp
        
        logger.info("Dispatcher created and handlers registered", extra={"event_type": "dispatcher_created"})

        # Start notification HTTP server
        notification_host = os.getenv("API_HOST", "0.0.0.0")
        notification_port = int(os.getenv("API_PORT", "8080"))

        logger.info(
            "Starting notification HTTP server",
            extra={"event_type": "server_start"},
        )

        # Run both notification server and polling for commands
        await run_bot_with_commands(notification_host, notification_port)

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
