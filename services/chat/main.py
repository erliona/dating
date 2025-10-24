from __future__ import annotations

"""Chat service main entry point.

This microservice handles real-time messaging between matched users.
"""

import logging
import asyncio

from aiohttp import web

from core.utils.logging import configure_logging
from core.middleware.standard_stack import setup_standard_middleware_stack
from core.middleware.metrics_middleware import add_metrics_route
from core.messaging.publisher import EventPublisher
from core.metrics.business_metrics import record_message_sent, record_conversation_started
from core.exceptions import ValidationError, ExternalServiceError
from core.resilience.retry import retry_data_service
from core.resilience.circuit_breaker import data_service_breaker

logger = logging.getLogger(__name__)

# Initialize event publisher
event_publisher = None

# Data service URL
DATA_SERVICE_URL = "http://data-service:8088"


@retry_data_service()
async def _call_data_service(url: str, method: str = "GET", data: dict = None, request: web.Request = None):
    """Helper to call Data Service with retry logic and correlation ID propagation."""
    import aiohttp
    from core.middleware.correlation import create_headers_with_correlation, log_correlation_propagation
    
    headers = {}
    
    # Add correlation headers if request is provided
    if request:
        headers = create_headers_with_correlation(request)
        log_correlation_propagation(
            correlation_id=request.get('correlation_id', 'unknown'),
            from_service='chat-service',
            to_service='data-service',
            operation=f"{method} {url}",
            request=request
        )
    
    async with aiohttp.ClientSession() as session:
        async with session.request(method, url, json=data, headers=headers) as resp:
            if resp.status >= 400:
                raise ExternalServiceError(f"Data service error: {resp.status}")
            return await resp.json()


async def websocket_handler(request: web.Request):
    """WebSocket connection handler.

    WS /chat/connect
    """
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    logger.info("WebSocket connection established")

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                # Echo message back for now
                await ws.send_json({"type": "message", "data": msg.data})
            elif msg.type == web.WSMsgType.ERROR:
                logger.error(f"WebSocket error: {ws.exception()}")
    except Exception as e:
        logger.error(f"WebSocket handler error: {e}")
    finally:
        logger.info("WebSocket connection closed")

    return ws


async def get_conversations(request: web.Request) -> web.Response:
    """Get user conversations.

    GET /chat/conversations
    Query params: user_id
    """
    try:
        user_id = int(request.query.get("user_id", 0))

        if not user_id:
            return web.json_response({"error": "user_id is required"}, status=400)

        return web.json_response({"conversations": [], "count": 0})

    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def get_messages(request: web.Request) -> web.Response:
    """Get messages for a conversation.

    GET /chat/messages/{conversation_id}
    """
    try:
        conversation_id = int(request.match_info["conversation_id"])

        return web.json_response({"messages": [], "count": 0})

    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def send_message(request: web.Request) -> web.Response:
    """Send a message.

    POST /chat/messages
    Body: {"conversation_id": int, "user_id": int, "text": str}
    """
    try:
        data = await request.json()
        conversation_id = data.get("conversation_id")
        user_id = data.get("user_id")
        text = data.get("text")

        if not all([conversation_id, user_id, text]):
            raise ValidationError("conversation_id, user_id, and text are required")

        # Record business metrics
        record_message_sent('chat-service')
        
        # Publish message.sent event
        if event_publisher:
            correlation_id = request.get("correlation_id")
            await event_publisher.publish_event(
                "message.sent",
                {
                    "conversation_id": conversation_id,
                    "sender_id": user_id,
                    "text": text,
                    "sent_at": "2024-01-01T00:00:00Z"
                },
                correlation_id=correlation_id
            )
        
        return web.json_response(
            {"message_id": 1, "sent_at": "2024-01-01T00:00:00Z"}, status=201
        )

    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def mark_message_read(request: web.Request) -> web.Response:
    """Mark a message as read.
    
    PUT /chat/messages/{message_id}/read
    """
    try:
        message_id = request.match_info.get("message_id")
        user_id = request.get("user_id")  # From JWT middleware
        
        if not message_id:
            return web.json_response({"error": "message_id is required"}, status=400)
        
        if not user_id:
            return web.json_response({"error": "Authentication required"}, status=401)
        
        # Call data service to mark message as read
        from services.chat.main import _call_data_service, DATA_SERVICE_URL
        result = await _call_data_service(
            f"{DATA_SERVICE_URL}/data/chat/messages/{message_id}/read",
            "PUT",
            {"user_id": user_id},
            request
        )
        
        # Record metrics
        record_message_sent('chat-service')
        
        return web.json_response(result)
        
    except ValidationError as e:
        logger.warning(f"Validation error in mark_message_read: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except ExternalServiceError as e:
        logger.error(f"Data service error in mark_message_read: {e}")
        return web.json_response({"error": "Failed to mark message as read"}, status=500)
    except Exception as e:
        logger.error(f"Unexpected error in mark_message_read: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def block_conversation(request: web.Request) -> web.Response:
    """Block a conversation/user.
    
    POST /chat/conversations/{conversation_id}/block
    """
    try:
        conversation_id = request.match_info.get("conversation_id")
        user_id = request.get("user_id")  # From JWT middleware
        
        if not conversation_id:
            return web.json_response({"error": "conversation_id is required"}, status=400)
        
        if not user_id:
            return web.json_response({"error": "Authentication required"}, status=401)
        
        # Call data service to block conversation
        from services.chat.main import _call_data_service, DATA_SERVICE_URL
        result = await _call_data_service(
            f"{DATA_SERVICE_URL}/data/chat/conversations/{conversation_id}/block",
            "POST",
            {"user_id": user_id},
            request
        )
        
        # Publish block event
        if event_publisher:
            await event_publisher.publish_block_event(
                user_id=user_id,
                conversation_id=conversation_id
            )
        
        return web.json_response(result)
        
    except ValidationError as e:
        logger.warning(f"Validation error in block_conversation: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except ExternalServiceError as e:
        logger.error(f"Data service error in block_conversation: {e}")
        return web.json_response({"error": "Failed to block conversation"}, status=500)
    except Exception as e:
        logger.error(f"Unexpected error in block_conversation: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def report_conversation(request: web.Request) -> web.Response:
    """Report a conversation/user.
    
    POST /chat/conversations/{conversation_id}/report
    Body: {"report_type": str, "reason": str}
    """
    try:
        conversation_id = request.match_info.get("conversation_id")
        user_id = request.get("user_id")  # From JWT middleware
        data = await request.json()
        
        if not conversation_id:
            return web.json_response({"error": "conversation_id is required"}, status=400)
        
        if not user_id:
            return web.json_response({"error": "Authentication required"}, status=401)
        
        report_type = data.get("report_type")
        reason = data.get("reason")
        
        if not report_type or not reason:
            return web.json_response({"error": "report_type and reason are required"}, status=400)
        
        # Call data service to report conversation
        from services.chat.main import _call_data_service, DATA_SERVICE_URL
        result = await _call_data_service(
            f"{DATA_SERVICE_URL}/data/chat/conversations/{conversation_id}/report",
            "POST",
            {
                "user_id": user_id,
                "report_type": report_type,
                "reason": reason
            },
            request
        )
        
        # Publish report event
        if event_publisher:
            await event_publisher.publish_report_event(
                user_id=user_id,
                conversation_id=conversation_id,
                report_type=report_type,
                reason=reason
            )
        
        return web.json_response(result)
        
    except ValidationError as e:
        logger.warning(f"Validation error in report_conversation: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except ExternalServiceError as e:
        logger.error(f"Data service error in report_conversation: {e}")
        return web.json_response({"error": "Failed to report conversation"}, status=500)
    except Exception as e:
        logger.error(f"Unexpected error in report_conversation: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def health_check(request: web.Request) -> web.Response:
    """Health check endpoint."""
    return web.json_response({"status": "healthy", "service": "chat"})


async def on_startup(app):
    """Startup handler."""
    global event_publisher
    rabbitmq_url = app["config"].get("rabbitmq_url")
    if rabbitmq_url:
        event_publisher = EventPublisher(rabbitmq_url)
        await event_publisher.connect()
        logger.info("Event publisher initialized")


async def on_shutdown(app):
    """Shutdown handler."""
    global event_publisher
    if event_publisher:
        await event_publisher.close()
        logger.info("Event publisher closed")


def create_app(config: dict) -> web.Application:
    """Create and configure the chat service application."""
    app = web.Application()
    app["config"] = config
    
    # Setup standard middleware stack
    setup_standard_middleware_stack(app, "chat-service", use_auth=True, use_audit=True)
    
    # Add metrics endpoint
    add_metrics_route(app, "chat-service")

    # Add routes
    app.router.add_get("/chat/connect", websocket_handler)
    app.router.add_get("/chat/conversations", get_conversations)
    app.router.add_get("/chat/conversations/{conversation_id}/messages", get_messages)  # Fixed route
    app.router.add_post("/chat/messages", send_message)
    app.router.add_put("/chat/messages/{message_id}/read", mark_message_read)  # Mark as read
    app.router.add_post("/chat/conversations/{conversation_id}/block", block_conversation)  # Block user
    app.router.add_post("/chat/conversations/{conversation_id}/report", report_conversation)  # Report user
    app.router.add_get("/health", health_check)
    
    # Add startup/shutdown handlers
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    return app


if __name__ == "__main__":
    import os

    # Configure structured logging
    configure_logging("chat-service", os.getenv("LOG_LEVEL", "INFO"))

    config = {
        "jwt_secret": os.getenv("JWT_SECRET"),  # SECURITY: No default value
        "rabbitmq_url": os.getenv("RABBITMQ_URL", "amqp://dating:dating@rabbitmq:5672/"),
        "host": os.getenv("CHAT_SERVICE_HOST", "0.0.0.0"),
        "port": int(os.getenv("CHAT_SERVICE_PORT", 8085)),
    }

    logger.info(
        "Starting chat-service",
        extra={"event_type": "service_start", "port": config["port"]},
    )

    app = create_app(config)
    web.run_app(app, host=config["host"], port=config["port"])
