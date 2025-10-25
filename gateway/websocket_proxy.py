"""WebSocket proxy implementation for API Gateway."""

import asyncio
import logging

from aiohttp import WSMsgType, web

logger = logging.getLogger(__name__)


async def proxy_websocket(
    request: web.Request, target_url: str, path_override: str | None = None
) -> web.Response:
    """
    Handle WebSocket upgrade and bidirectional proxy.

    Args:
        request: Original WebSocket request
        target_url: Base URL of target service
        path_override: Optional path to use instead of request.path

    Returns:
        WebSocket response or error response
    """
    try:
        # Build target WebSocket URL
        path = path_override or request.path
        target_ws_url = f"{target_url}{path}".replace("http://", "ws://").replace(
            "https://", "wss://"
        )

        logger.info(f"Proxying WebSocket: {request.url} -> {target_ws_url}")

        # Create WebSocket connection to target service
        async with request.app["http_session"].ws_connect(
            target_ws_url, headers=dict(request.headers), timeout=30
        ) as target_ws:

            # Create WebSocket response for client
            ws = web.WebSocketResponse()
            await ws.prepare(request)

            # Start bidirectional proxy
            async def proxy_to_target():
                """Proxy messages from client to target service."""
                try:
                    async for msg in ws:
                        if msg.type == WSMsgType.TEXT:
                            await target_ws.send_str(msg.data)
                        elif msg.type == WSMsgType.BINARY:
                            await target_ws.send_bytes(msg.data)
                        elif msg.type == WSMsgType.ERROR:
                            logger.error(f"WebSocket client error: {ws.exception()}")
                            break
                except Exception as e:
                    logger.error(f"Error proxying to target: {e}")
                finally:
                    await target_ws.close()

            async def proxy_to_client():
                """Proxy messages from target service to client."""
                try:
                    async for msg in target_ws:
                        if msg.type == WSMsgType.TEXT:
                            await ws.send_str(msg.data)
                        elif msg.type == WSMsgType.BINARY:
                            await ws.send_bytes(msg.data)
                        elif msg.type == WSMsgType.ERROR:
                            logger.error(
                                f"WebSocket target error: {target_ws.exception()}"
                            )
                            break
                except Exception as e:
                    logger.error(f"Error proxying to client: {e}")
                finally:
                    await ws.close()

            # Run both proxy directions concurrently
            await asyncio.gather(
                proxy_to_target(), proxy_to_client(), return_exceptions=True
            )

            return ws  # type: ignore[return-value]

    except Exception as e:
        logger.error(f"WebSocket proxy error: {e}")
        return web.json_response({"error": "WebSocket connection failed"}, status=500)


def is_websocket_request(request: web.Request) -> bool:
    """Check if request is a WebSocket upgrade request."""
    return (
        request.headers.get("Upgrade", "").lower() == "websocket"
        and request.headers.get("Connection", "").lower() == "upgrade"
    )
