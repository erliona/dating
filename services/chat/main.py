"""Chat service main entry point.

This microservice handles real-time messaging between matched users.
"""

import logging

from aiohttp import web

from core.utils.logging import configure_logging

logger = logging.getLogger(__name__)


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

        # TODO: Implement conversation retrieval
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

        # TODO: Implement message retrieval
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
            return web.json_response(
                {"error": "conversation_id, user_id, and text are required"}, status=400
            )

        # TODO: Implement message sending
        return web.json_response(
            {"message_id": 1, "sent_at": "2024-01-01T00:00:00Z"}, status=201
        )

    except Exception as e:
        logger.error(f"Error sending message: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def health_check(request: web.Request) -> web.Response:
    """Health check endpoint."""
    return web.json_response({"status": "healthy", "service": "chat"})


def create_app(config: dict) -> web.Application:
    """Create and configure the chat service application."""
    app = web.Application()
    app["config"] = config

    # Add routes
    app.router.add_get("/chat/connect", websocket_handler)
    app.router.add_get("/chat/conversations", get_conversations)
    app.router.add_get("/chat/messages/{conversation_id}", get_messages)
    app.router.add_post("/chat/messages", send_message)
    app.router.add_get("/health", health_check)

    return app


if __name__ == "__main__":
    import os

    # Configure structured logging
    configure_logging("chat-service", os.getenv("LOG_LEVEL", "INFO"))

    config = {
        "host": os.getenv("CHAT_SERVICE_HOST", "0.0.0.0"),
        "port": int(os.getenv("CHAT_SERVICE_PORT", 8085)),
    }

    logger.info(
        "Starting chat-service",
        extra={"event_type": "service_start", "port": config["port"]},
    )

    app = create_app(config)
    web.run_app(app, host=config["host"], port=config["port"])
