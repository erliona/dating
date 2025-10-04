"""API Gateway main entry point.

This service routes requests to appropriate microservices.
"""

import logging
import os

from aiohttp import ClientSession, web

from core.utils.logging import configure_logging

logger = logging.getLogger(__name__)


async def proxy_request(request: web.Request, target_url: str) -> web.Response:
    """Proxy request to target microservice."""
    try:
        async with ClientSession() as session:
            # Build target URL
            path = request.path
            query_string = request.query_string
            full_url = f"{target_url}{path}"
            if query_string:
                full_url = f"{full_url}?{query_string}"

            # Forward request
            async with session.request(
                method=request.method,
                url=full_url,
                headers={
                    k: v
                    for k, v in request.headers.items()
                    if k.lower() not in ["host", "connection"]
                },
                data=(
                    await request.read()
                    if request.method in ["POST", "PUT", "PATCH"]
                    else None
                ),
            ) as resp:
                # Return response
                body = await resp.read()
                return web.Response(
                    body=body,
                    status=resp.status,
                    headers={
                        k: v
                        for k, v in resp.headers.items()
                        if k.lower() not in ["transfer-encoding", "connection"]
                    },
                )
    except Exception as e:
        logger.error(f"Error proxying request to {target_url}: {e}")
        return web.json_response({"error": "Service unavailable"}, status=503)


async def route_auth(request: web.Request) -> web.Response:
    """Route to auth service."""
    auth_url = request.app["config"]["auth_service_url"]
    return await proxy_request(request, auth_url)


async def route_profile(request: web.Request) -> web.Response:
    """Route to profile service."""
    profile_url = request.app["config"]["profile_service_url"]
    return await proxy_request(request, profile_url)


async def route_discovery(request: web.Request) -> web.Response:
    """Route to discovery service."""
    discovery_url = request.app["config"]["discovery_service_url"]
    return await proxy_request(request, discovery_url)


async def route_media(request: web.Request) -> web.Response:
    """Route to media service."""
    media_url = request.app["config"]["media_service_url"]
    return await proxy_request(request, media_url)


async def route_chat(request: web.Request) -> web.Response:
    """Route to chat service."""
    chat_url = request.app["config"]["chat_service_url"]
    return await proxy_request(request, chat_url)


async def health_check(request: web.Request) -> web.Response:
    """Health check endpoint."""
    return web.json_response(
        {
            "status": "healthy",
            "service": "api-gateway",
            "routes": {
                "auth": request.app["config"]["auth_service_url"],
                "profile": request.app["config"]["profile_service_url"],
                "discovery": request.app["config"]["discovery_service_url"],
                "media": request.app["config"]["media_service_url"],
                "chat": request.app["config"]["chat_service_url"],
            },
        }
    )


def create_app(config: dict) -> web.Application:
    """Create and configure the API gateway application."""
    app = web.Application()
    app["config"] = config

    # Add routing rules
    app.router.add_route("*", "/auth/{tail:.*}", route_auth)
    app.router.add_route("*", "/profiles/{tail:.*}", route_profile)
    app.router.add_route("*", "/discovery/{tail:.*}", route_discovery)
    app.router.add_route("*", "/media/{tail:.*}", route_media)
    app.router.add_route("*", "/chat/{tail:.*}", route_chat)
    app.router.add_get("/health", health_check)

    return app


if __name__ == "__main__":
    # Configure structured logging
    configure_logging("api-gateway", os.getenv("LOG_LEVEL", "INFO"))

    config = {
        "auth_service_url": os.getenv("AUTH_SERVICE_URL", "http://auth-service:8081"),
        "profile_service_url": os.getenv(
            "PROFILE_SERVICE_URL", "http://profile-service:8082"
        ),
        "discovery_service_url": os.getenv(
            "DISCOVERY_SERVICE_URL", "http://discovery-service:8083"
        ),
        "media_service_url": os.getenv(
            "MEDIA_SERVICE_URL", "http://media-service:8084"
        ),
        "chat_service_url": os.getenv("CHAT_SERVICE_URL", "http://chat-service:8085"),
        "host": os.getenv("GATEWAY_HOST", "0.0.0.0"),
        "port": int(os.getenv("GATEWAY_PORT", 8080)),
    }

    logger.info(
        "Starting api-gateway",
        extra={"event_type": "service_start", "port": config["port"]},
    )

    app = create_app(config)
    web.run_app(app, host=config["host"], port=config["port"])
