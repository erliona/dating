"""Notification service main entry point.

This microservice handles push notifications to users via the Telegram bot.
It receives notification requests from other services and forwards them to the bot.
"""

import logging
import os
from typing import Any, Dict

from aiohttp import ClientError, ClientSession, ClientTimeout, web

from core.utils.logging import configure_logging
from core.middleware.jwt_middleware import jwt_middleware
from core.middleware.request_logging import request_logging_middleware, user_context_middleware
from core.middleware.metrics_middleware import metrics_middleware, add_metrics_route
from core.resilience.circuit_breaker import bot_service_breaker
from core.resilience.retry import retry_notification
from core.messaging.subscriber import EventSubscriber

logger = logging.getLogger(__name__)

# Bot service URL for sending notifications
BOT_URL = os.getenv("BOT_URL", "http://telegram-bot:8080")

# Initialize event subscriber
event_subscriber = None


@retry_notification()
async def _call_bot(url: str, data: dict):
    """Call Bot with retry."""
    async with ClientSession(timeout=ClientTimeout(total=10)) as session:
        async with session.post(url, json=data) as resp:
            resp.raise_for_status()
            return await resp.json()


async def handle_match_event(data: dict, correlation_id: str = None):
    """Handle match.created event."""
    logger.info(
        "Processing match event",
        extra={"correlation_id": correlation_id, "data": data}
    )
    
    user_id_1 = data.get("user_id_1")
    user_id_2 = data.get("user_id_2")
    
    if not user_id_1 or not user_id_2:
        logger.error("Invalid match event data: missing user IDs")
        return
    
    # Send notifications to both users
    await send_match_notification(user_id_1, {"matched_user_id": user_id_2})
    await send_match_notification(user_id_2, {"matched_user_id": user_id_1})


async def handle_message_event(data: dict, correlation_id: str = None):
    """Handle message.sent event."""
    logger.info(
        "Processing message event",
        extra={"correlation_id": correlation_id, "data": data}
    )
    
    conversation_id = data.get("conversation_id")
    sender_id = data.get("sender_id")
    text = data.get("text")
    
    if not conversation_id or not sender_id:
        logger.error("Invalid message event data: missing required fields")
        return
    
    # For now, just log the message event
    # In a real implementation, you would:
    # 1. Get the recipient user ID from the conversation
    # 2. Send a push notification to the recipient
    logger.info(f"Message sent in conversation {conversation_id} by user {sender_id}")


async def send_match_notification(user_id: int, match_data: dict):
    """Send match notification to user."""
    try:
        # Use circuit breaker + retry
        result = await bot_service_breaker.call(
            _call_bot,
            f"{BOT_URL}/notifications/match",
            {"user_id": user_id, "match_data": match_data},
            fallback=lambda *args: {"status": "queued"}
        )
        
        if result.get("status") == "queued":
            logger.warning(f"Match notification queued for user {user_id}")
        else:
            logger.info(f"Match notification sent to user {user_id}")
            
    except Exception as e:
        logger.error(f"Error sending match notification to user {user_id}: {e}")


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


async def on_startup(app):
    """Startup handler."""
    global event_subscriber
    rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://dating:dating@rabbitmq:5672/")
    
    if rabbitmq_url:
        event_subscriber = EventSubscriber(rabbitmq_url, "notification-service")
        await event_subscriber.connect()
        
        # Register event handlers
        event_subscriber.register_handler("match.created", handle_match_event)
        event_subscriber.register_handler("message.sent", handle_message_event)
        
        # Start consuming
        await event_subscriber.start_consuming()
        logger.info("Notification service started consuming events")


async def on_shutdown(app):
    """Shutdown handler."""
    global event_subscriber
    if event_subscriber:
        await event_subscriber.close()
        logger.info("Event subscriber closed")


def create_app() -> web.Application:
    """Create and configure the aiohttp application."""
    app = web.Application()
    
    # Add middleware
    app.middlewares.append(user_context_middleware)
    app.middlewares.append(request_logging_middleware)
    app.middlewares.append(metrics_middleware)
    app.middlewares.append(jwt_middleware)
    
    # Add metrics endpoint
    add_metrics_route(app, "notification-service")

    # Register routes
    app.router.add_post("/api/notifications/send_match", send_match_notification)
    app.router.add_post("/api/notifications/send_message", send_message_notification)
    app.router.add_post("/api/notifications/send_like", send_like_notification)
    app.router.add_get("/health", health_check)
    
    # Add startup/shutdown handlers
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

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
