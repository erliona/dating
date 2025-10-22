"""Notification service main entry point.

This microservice handles push notifications to users via the Telegram bot.
It receives notification requests from other services and forwards them to the bot.
"""

import logging
import os
from typing import Any, Dict

from aiohttp import ClientError, ClientSession, ClientTimeout, web

from core.utils.logging import configure_logging
# from core.middleware.jwt_middleware import jwt_middleware

logger = logging.getLogger(__name__)

# Bot service URL for sending notifications
BOT_URL = os.getenv("BOT_URL", "http://telegram-bot:8080")


async def send_match_notification(request: web.Request) -> web.Response:
    """Send notification about a new match.

    POST /api/notifications/send_match
    Body: {
        "user_id": int,  # Telegram user ID
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

        # Call bot HTTP endpoint to send notification
        async with ClientSession(timeout=ClientTimeout(total=10)) as session:
            try:
                async with session.post(
                    f"{BOT_URL}/notifications/match",
                    json={"user_id": user_id, "match_data": match_data},
                ) as response:
                    if response.status == 200:
                        logger.info(
                            "Match notification sent successfully",
                            extra={
                                "event_type": "match_notification_sent",
                                "user_id": user_id,
                                "match_id": match_data.get("id"),
                            },
                        )
                        return web.json_response(
                            {"status": "sent", "user_id": user_id, "notification_type": "match"}
                        )
                    else:
                        logger.error(
                            f"Bot returned error status: {response.status}",
                            extra={
                                "event_type": "bot_error",
                                "status": response.status,
                                "user_id": user_id,
                            },
                        )
                        return web.json_response(
                            {"error": "Failed to send notification", "status": response.status},
                            status=500,
                        )
            except ClientError as e:
                logger.error(
                    f"Failed to call bot endpoint: {e}",
                    exc_info=True,
                    extra={"event_type": "bot_connection_error", "user_id": user_id},
                )
                return web.json_response(
                    {"error": "Failed to connect to bot service"}, status=503
                )

    except Exception as e:
        logger.error(
            f"Error queueing match notification: {e}",
            exc_info=True,
            extra={"event_type": "match_notification_error"},
        )
        return web.json_response({"error": "Internal server error"}, status=500)


async def send_message_notification(request: web.Request) -> web.Response:
    """Send notification about a new message.

    POST /api/notifications/send_message
    Body: {
        "user_id": int,  # Telegram user ID
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

        # Call bot HTTP endpoint to send notification
        async with ClientSession(timeout=ClientTimeout(total=10)) as session:
            try:
                async with session.post(
                    f"{BOT_URL}/notifications/message",
                    json={"user_id": user_id, "message_data": message_data},
                ) as response:
                    if response.status == 200:
                        logger.info(
                            "Message notification sent successfully",
                            extra={
                                "event_type": "message_notification_sent",
                                "user_id": user_id,
                            },
                        )
                        return web.json_response(
                            {"status": "sent", "user_id": user_id, "notification_type": "message"}
                        )
                    else:
                        logger.error(
                            f"Bot returned error status: {response.status}",
                            extra={
                                "event_type": "bot_error",
                                "status": response.status,
                                "user_id": user_id,
                            },
                        )
                        return web.json_response(
                            {"error": "Failed to send notification", "status": response.status},
                            status=500,
                        )
            except ClientError as e:
                logger.error(
                    f"Failed to call bot endpoint: {e}",
                    exc_info=True,
                    extra={"event_type": "bot_connection_error", "user_id": user_id},
                )
                return web.json_response(
                    {"error": "Failed to connect to bot service"}, status=503
                )

    except Exception as e:
        logger.error(
            f"Error queueing message notification: {e}",
            exc_info=True,
            extra={"event_type": "message_notification_error"},
        )
        return web.json_response({"error": "Internal server error"}, status=500)


async def send_like_notification(request: web.Request) -> web.Response:
    """Send notification about receiving a like.

    POST /api/notifications/send_like
    Body: {
        "user_id": int,  # Telegram user ID
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

        # Call bot HTTP endpoint to send notification
        async with ClientSession(timeout=ClientTimeout(total=10)) as session:
            try:
                async with session.post(
                    f"{BOT_URL}/notifications/like",
                    json={"user_id": user_id, "like_data": like_data},
                ) as response:
                    if response.status == 200:
                        logger.info(
                            "Like notification sent successfully",
                            extra={
                                "event_type": "like_notification_sent",
                                "user_id": user_id,
                            },
                        )
                        return web.json_response(
                            {"status": "sent", "user_id": user_id, "notification_type": "like"}
                        )
                    else:
                        logger.error(
                            f"Bot returned error status: {response.status}",
                            extra={
                                "event_type": "bot_error",
                                "status": response.status,
                                "user_id": user_id,
                            },
                        )
                        return web.json_response(
                            {"error": "Failed to send notification", "status": response.status},
                            status=500,
                        )
            except ClientError as e:
                logger.error(
                    f"Failed to call bot endpoint: {e}",
                    exc_info=True,
                    extra={"event_type": "bot_connection_error", "user_id": user_id},
                )
                return web.json_response(
                    {"error": "Failed to connect to bot service"}, status=503
                )

    except Exception as e:
        logger.error(
            f"Error queueing like notification: {e}",
            exc_info=True,
            extra={"event_type": "like_notification_error"},
        )
        return web.json_response({"error": "Internal server error"}, status=500)


async def health_check(request: web.Request) -> web.Response:
    """Health check endpoint.

    GET /health
    """
    return web.json_response({"status": "healthy"})


def create_app() -> web.Application:
    """Create and configure the aiohttp application."""
    app = web.Application()
    
    # Add JWT middleware - temporarily disabled
    # app.middlewares.append(jwt_middleware)

    # Register routes
    app.router.add_post("/api/notifications/send_match", send_match_notification)
    app.router.add_post("/api/notifications/send_message", send_message_notification)
    app.router.add_post("/api/notifications/send_like", send_like_notification)
    app.router.add_get("/health", health_check)

    return app


if __name__ == "__main__":
    # Configure logging
    configure_logging("notification-service", os.getenv("LOG_LEVEL", "INFO"))

    logger.info(
        "Starting notification service",
        extra={"event_type": "service_start"},
    )

    # Create and run app
    app = create_app()
    port = int(os.getenv("PORT", "8084"))

    logger.info(
        f"Notification service listening on port {port}",
        extra={"event_type": "service_ready", "port": port},
    )

    web.run_app(app, host="0.0.0.0", port=port)
