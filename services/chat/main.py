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

    WS /chat/ws?conversation_id=123
    """
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    # Get conversation_id from query params
    conversation_id = request.query.get("conversation_id")
    user_id = request.get("user_id")  # From JWT middleware
    
    if not user_id:
        await ws.close(code=1008, message="Authentication required")
        return ws
    
    logger.info(f"WebSocket connection established for user {user_id}, conversation {conversation_id}")

    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                try:
                    data = msg.json()
                    event_type = data.get("type")
                    
                    if event_type == "message":
                        # Handle message creation
                        await handle_message_event(ws, data, user_id, conversation_id)
                    elif event_type == "typing":
                        # Handle typing indicator
                        await handle_typing_event(ws, data, user_id, conversation_id)
                    elif event_type == "read":
                        # Handle read receipt
                        await handle_read_event(ws, data, user_id, conversation_id)
                    else:
                        await ws.send_json({"type": "error", "message": "Unknown event type"})
                        
                except Exception as e:
                    logger.error(f"WebSocket message error: {e}")
                    await ws.send_json({"type": "error", "message": "Invalid message format"})
                    
            elif msg.type == web.WSMsgType.ERROR:
                logger.error(f"WebSocket error: {ws.exception()}")
    except Exception as e:
        logger.error(f"WebSocket handler error: {e}")
    finally:
        logger.info("WebSocket connection closed")

    return ws


async def handle_message_event(ws, data, user_id, conversation_id):
    """Handle message creation event."""
    content = data.get("content")
    content_type = data.get("content_type", "text")
    
    if not content:
        await ws.send_json({"type": "error", "message": "Content is required"})
        return
    
    # Create message via data service
    try:
        result = await _call_data_service(
            f"{DATA_SERVICE_URL}/data/chat/conversations/{conversation_id}/messages",
            "POST",
            {
                "sender_id": user_id,
                "content": content,
                "content_type": content_type
            }
        )
        
        # Broadcast to all participants
        await ws.send_json({
            "type": "message.created",
            "message_id": result.get("message_id"),
            "sender_id": user_id,
            "content": content,
            "content_type": content_type,
            "created_at": result.get("created_at")
        })
        
    except Exception as e:
        logger.error(f"Failed to create message: {e}")
        await ws.send_json({"type": "error", "message": "Failed to send message"})


async def handle_typing_event(ws, data, user_id, conversation_id):
    """Handle typing indicator event."""
    is_typing = data.get("is_typing", False)
    
    # Broadcast typing indicator
    await ws.send_json({
        "type": "conversation.typing",
        "user_id": user_id,
        "is_typing": is_typing
    })


async def handle_read_event(ws, data, user_id, conversation_id):
    """Handle read receipt event."""
    up_to_message_id = data.get("up_to_message_id")
    
    if not up_to_message_id:
        await ws.send_json({"type": "error", "message": "up_to_message_id is required"})
        return
    
    try:
        # Update read state
        await _call_data_service(
            f"{DATA_SERVICE_URL}/data/chat/conversations/{conversation_id}/read-state",
            "PUT",
            {
                "user_id": user_id,
                "up_to_message_id": up_to_message_id
            }
        )
        
        # Broadcast read receipt
        await ws.send_json({
            "type": "message.read",
            "user_id": user_id,
            "up_to_message_id": up_to_message_id
        })
        
    except Exception as e:
        logger.error(f"Failed to update read state: {e}")
        await ws.send_json({"type": "error", "message": "Failed to mark as read"})


async def get_conversations(request: web.Request) -> web.Response:
    """Get user conversations.

    GET /chat/conversations
    Query params: user_id, limit, cursor, with_unread_only, sort
    """
    try:
        user_id = int(request.query.get("user_id", 0))
        limit = int(request.query.get("limit", 20))
        with_unread_only = request.query.get("with_unread_only", "false").lower() == "true"
        sort = request.query.get("sort", "last_message_at.desc")

        if not user_id:
            return web.json_response({"error": "user_id is required"}, status=400)

        # Build query parameters for Data Service
        params = {
            "user_id": user_id,
            "limit": limit,
            "with_unread_only": with_unread_only,
            "sort": sort
        }
        
        # Add cursor if provided
        if request.query.get("cursor"):
            params["cursor"] = request.query.get("cursor")
        
        # Get conversations from Data Service
        result = await _call_data_service(
            f"{DATA_SERVICE_URL}/data/chat/conversations",
            "GET",
            params=params,
            request=request
        )
        
        # Record business metrics
        record_conversation_started('chat-service')
        
        return web.json_response(result)

    except Exception as e:
        logger.error(f"Error getting conversations: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def get_messages(request: web.Request) -> web.Response:
    """Get messages for a conversation.

    GET /chat/conversations/{conversation_id}/messages
    Query params: before_id, after_id, limit
    """
    try:
        conversation_id = int(request.match_info["conversation_id"])
        before_id = request.query.get("before_id")
        after_id = request.query.get("after_id")
        limit = int(request.query.get("limit", 50))

        # Build query parameters for Data Service
        params = {
            "conversation_id": conversation_id,
            "limit": limit
        }
        
        if before_id:
            params["before_id"] = before_id
        if after_id:
            params["after_id"] = after_id
        
        # Get messages from Data Service
        result = await _call_data_service(
            f"{DATA_SERVICE_URL}/data/chat/conversations/{conversation_id}/messages",
            "GET",
            params=params,
            request=request
        )
        
        return web.json_response(result)

    except Exception as e:
        logger.error(f"Error getting messages: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def send_message(request: web.Request) -> web.Response:
    """Send a message.

    POST /chat/conversations/{conversation_id}/messages
    Headers: Idempotency-Key (optional)
    Body: {"content": str, "content_type": str}
    """
    try:
        conversation_id = request.match_info.get("conversation_id")
        user_id = request.get("user_id")  # From JWT middleware
        data = await request.json()
        
        if not conversation_id:
            return web.json_response({"error": "conversation_id is required"}, status=400)
        
        if not user_id:
            return web.json_response({"error": "Authentication required"}, status=401)
        
        content = data.get("content")
        content_type = data.get("content_type", "text")
        
        if not content:
            return web.json_response({"error": "content is required"}, status=400)
        
        # Check for idempotency key
        idempotency_key = request.headers.get("Idempotency-Key")
        
        # Call data service to send message
        result = await _call_data_service(
            f"{DATA_SERVICE_URL}/data/chat/conversations/{conversation_id}/messages",
            "POST",
            {
                "sender_id": user_id,
                "content": content,
                "content_type": content_type,
                "idempotency_key": idempotency_key
            },
            request
        )
        
        # Record business metrics
        record_message_sent('chat-service')
        
        # Publish message.sent event
        if event_publisher:
            await event_publisher.publish_event(
                "message.sent",
                {
                    "conversation_id": conversation_id,
                    "sender_id": user_id,
                    "content": content,
                    "content_type": content_type,
                    "message_id": result.get("message_id"),
                    "sent_at": result.get("created_at")
                }
            )
        
        return web.json_response(result, status=201)

    except ValidationError as e:
        logger.warning(f"Validation error in send_message: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except ExternalServiceError as e:
        logger.error(f"Data service error in send_message: {e}")
        return web.json_response({"error": "Failed to send message"}, status=500)
    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def update_read_state(request: web.Request) -> web.Response:
    """Update read state for a conversation.
    
    PUT /chat/conversations/{conversation_id}/read-state
    Body: {"up_to_message_id": "123"}
    """
    try:
        conversation_id = request.match_info.get("conversation_id")
        user_id = request.get("user_id")  # From JWT middleware
        data = await request.json()
        
        if not conversation_id:
            return web.json_response({"error": "conversation_id is required"}, status=400)
        
        if not user_id:
            return web.json_response({"error": "Authentication required"}, status=401)
        
        up_to_message_id = data.get("up_to_message_id")
        if not up_to_message_id:
            return web.json_response({"error": "up_to_message_id is required"}, status=400)
        
        # Call data service to update read state
        result = await _call_data_service(
            f"{DATA_SERVICE_URL}/data/chat/conversations/{conversation_id}/read-state",
            "PUT",
            {
                "user_id": user_id,
                "up_to_message_id": up_to_message_id
            },
            request
        )
        
        # Publish read receipt event
        if event_publisher:
            await event_publisher.publish_event(
                "message.read",
                {
                    "conversation_id": conversation_id,
                    "user_id": user_id,
                    "up_to_message_id": up_to_message_id
                }
            )
        
        return web.json_response(result, status=204)
        
    except ValidationError as e:
        logger.warning(f"Validation error in update_read_state: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except ExternalServiceError as e:
        logger.error(f"Data service error in update_read_state: {e}")
        return web.json_response({"error": "Failed to update read state"}, status=500)
    except Exception as e:
        logger.error(f"Unexpected error in update_read_state: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def block_user(request: web.Request) -> web.Response:
    """Block a user.
    
    POST /chat/blocks
    Body: {"target_user_id": "123"}
    """
    try:
        user_id = request.get("user_id")  # From JWT middleware
        data = await request.json()
        
        if not user_id:
            return web.json_response({"error": "Authentication required"}, status=401)
        
        target_user_id = data.get("target_user_id")
        if not target_user_id:
            return web.json_response({"error": "target_user_id is required"}, status=400)
        
        # Call data service to block user
        result = await _call_data_service(
            f"{DATA_SERVICE_URL}/data/chat/blocks",
            "POST",
            {
                "blocker_id": user_id,
                "blocked_id": target_user_id
            },
            request
        )
        
        # Publish block event
        if event_publisher:
            await event_publisher.publish_event(
                "user.blocked",
                {
                    "blocker_id": user_id,
                    "blocked_id": target_user_id
                }
            )
        
        return web.json_response(result, status=201)
        
    except ValidationError as e:
        logger.warning(f"Validation error in block_user: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except ExternalServiceError as e:
        logger.error(f"Data service error in block_user: {e}")
        return web.json_response({"error": "Failed to block user"}, status=500)
    except Exception as e:
        logger.error(f"Unexpected error in block_user: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def unblock_user(request: web.Request) -> web.Response:
    """Unblock a user.
    
    DELETE /chat/blocks/{target_user_id}
    """
    try:
        target_user_id = request.match_info.get("target_user_id")
        user_id = request.get("user_id")  # From JWT middleware
        
        if not target_user_id:
            return web.json_response({"error": "target_user_id is required"}, status=400)
        
        if not user_id:
            return web.json_response({"error": "Authentication required"}, status=401)
        
        # Call data service to unblock user
        result = await _call_data_service(
            f"{DATA_SERVICE_URL}/data/chat/blocks/{target_user_id}",
            "DELETE",
            {"blocker_id": user_id},
            request
        )
        
        return web.json_response(result, status=204)
        
    except ValidationError as e:
        logger.warning(f"Validation error in unblock_user: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except ExternalServiceError as e:
        logger.error(f"Data service error in unblock_user: {e}")
        return web.json_response({"error": "Failed to unblock user"}, status=500)
    except Exception as e:
        logger.error(f"Unexpected error in unblock_user: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def create_report(request: web.Request) -> web.Response:
    """Create a report.
    
    POST /chat/reports
    Body: {"conversation_id": "123", "message_id": "456", "reason": "spam"}
    """
    try:
        user_id = request.get("user_id")  # From JWT middleware
        data = await request.json()
        
        if not user_id:
            return web.json_response({"error": "Authentication required"}, status=401)
        
        conversation_id = data.get("conversation_id")
        message_id = data.get("message_id")  # Optional
        reason = data.get("reason")
        
        if not conversation_id or not reason:
            return web.json_response({"error": "conversation_id and reason are required"}, status=400)
        
        # Call data service to create report
        result = await _call_data_service(
            f"{DATA_SERVICE_URL}/data/chat/reports",
            "POST",
            {
                "reporter_id": user_id,
                "conversation_id": conversation_id,
                "message_id": message_id,
                "reason": reason
            },
            request
        )
        
        # Publish report event
        if event_publisher:
            await event_publisher.publish_event(
                "report.created",
                {
                    "report_id": result.get("report_id"),
                    "reporter_id": user_id,
                    "conversation_id": conversation_id,
                    "message_id": message_id,
                    "reason": reason
                }
            )
        
        return web.json_response(result, status=202)  # Async moderation
        
    except ValidationError as e:
        logger.warning(f"Validation error in create_report: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except ExternalServiceError as e:
        logger.error(f"Data service error in create_report: {e}")
        return web.json_response({"error": "Failed to create report"}, status=500)
    except Exception as e:
        logger.error(f"Unexpected error in create_report: {e}")
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
    app.router.add_get("/chat/ws", websocket_handler)  # Fixed: resource-based path
    app.router.add_get("/chat/conversations", get_conversations)
    app.router.add_get("/chat/conversations/{conversation_id}/messages", get_messages)  # Fixed route
    app.router.add_post("/chat/conversations/{conversation_id}/messages", send_message)  # Fixed: messages belong to conversations
    app.router.add_put("/chat/conversations/{conversation_id}/read-state", update_read_state)  # Fixed: read-state per conversation
    app.router.add_post("/chat/blocks", block_user)  # Fixed: blocks are user-to-user relationships
    app.router.add_delete("/chat/blocks/{target_user_id}", unblock_user)  # Unblock user
    app.router.add_post("/chat/reports", create_report)  # Fixed: reports are separate resources
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
