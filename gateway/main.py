"""API Gateway main entry point.

This service routes requests to appropriate microservices.
"""

import logging
import os

from aiohttp import ClientSession, ClientTimeout, web
from aiohttp_cors import ResourceOptions, setup as cors_setup

from core.utils.logging import configure_logging

logger = logging.getLogger(__name__)


async def proxy_request(request: web.Request, target_url: str, path_override: str = None) -> web.Response:
    """Proxy request to target microservice.
    
    Args:
        request: Original request
        target_url: Base URL of target service
        path_override: Optional path to use instead of request.path
    """
    # Configure timeout: 30s total, 10s connect
    timeout = ClientTimeout(total=30, connect=10)

    try:
        async with ClientSession(timeout=timeout) as session:
            # Build target URL
            path = path_override or request.path
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
        logger.error(f"Error proxying request to {target_url}: {e}", exc_info=True)
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


async def route_admin(request: web.Request) -> web.Response:
    """Route to admin service."""
    admin_url = request.app["config"]["admin_service_url"]
    return await proxy_request(request, admin_url)


async def route_notifications(request: web.Request) -> web.Response:
    """Route to notification service."""
    notification_url = request.app["config"]["notification_service_url"]
    return await proxy_request(request, notification_url)


async def route_api_auth(request: web.Request) -> web.Response:
    """Route /api/auth/* to auth service, stripping /api prefix."""
    auth_url = request.app["config"]["auth_service_url"]
    # Strip /api prefix from path
    new_path = request.path.replace("/api/auth", "/auth", 1)
    return await proxy_request(request, auth_url, path_override=new_path)


async def route_api_profile(request: web.Request) -> web.Response:
    """Route /api/profile/* to profile service, mapping to /profiles/*."""
    profile_url = request.app["config"]["profile_service_url"]
    # Map /api/profile to /profiles
    new_path = request.path.replace("/api/profile", "/profiles", 1)
    return await proxy_request(request, profile_url, path_override=new_path)


async def route_api_discovery(request: web.Request) -> web.Response:
    """Route /api/discover, /api/like, /api/pass, /api/matches, /api/favorites to discovery service."""
    discovery_url = request.app["config"]["discovery_service_url"]
    # Map /api/* to /discovery/*
    path = request.path
    if path.startswith("/api/discover"):
        new_path = path.replace("/api/discover", "/discovery/discover", 1)
    elif path.startswith("/api/like"):
        new_path = path.replace("/api/like", "/discovery/like", 1)
    elif path.startswith("/api/pass"):
        new_path = path.replace("/api/pass", "/discovery/pass", 1)
    elif path.startswith("/api/matches"):
        new_path = path.replace("/api/matches", "/discovery/matches", 1)
    elif path.startswith("/api/favorites"):
        new_path = path.replace("/api/favorites", "/discovery/favorites", 1)
    else:
        new_path = path.replace("/api/", "/discovery/", 1)
    
    return await proxy_request(request, discovery_url, path_override=new_path)


async def route_api_media(request: web.Request) -> web.Response:
    """Route /api/photos/* to media service, mapping to /media/*."""
    media_url = request.app["config"]["media_service_url"]
    # Map /api/photos to /media
    new_path = request.path.replace("/api/photos", "/media", 1)
    return await proxy_request(request, media_url, path_override=new_path)


async def route_api_notifications(request: web.Request) -> web.Response:
    """Route /api/notifications/* to notification service."""
    notification_url = request.app["config"]["notification_service_url"]
    # Keep the /api/notifications path as-is
    return await proxy_request(request, notification_url)


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
                "admin": request.app["config"]["admin_service_url"],
                "notification": request.app["config"]["notification_service_url"],
            },
        }
    )


def create_app(config: dict) -> web.Application:
    """Create and configure the API gateway application."""
    app = web.Application()
    app["config"] = config

    # Setup CORS for WebApp/frontend access
    # Allow requests from the configured WebApp domain
    webapp_domain = config.get("webapp_domain", "*")
    cors = cors_setup(
        app,
        defaults={
            webapp_domain: ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers=("Content-Type", "Authorization", "X-Requested-With"),
                allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            )
        },
    )
    logger.info(f"CORS configured for domain: {webapp_domain}")

    # Add routing rules for direct service access (internal/microservice-to-microservice)
    app.router.add_route("*", "/auth/{tail:.*}", route_auth)
    app.router.add_route("*", "/profiles/{tail:.*}", route_profile)
    app.router.add_route("*", "/discovery/{tail:.*}", route_discovery)
    app.router.add_route("*", "/media/{tail:.*}", route_media)
    app.router.add_route("*", "/chat/{tail:.*}", route_chat)
    app.router.add_route("*", "/admin/{tail:.*}", route_admin)
    app.router.add_route("*", "/admin-panel/{tail:.*}", route_admin)
    app.router.add_route("*", "/notifications/{tail:.*}", route_notifications)
    
    # Add unified /api/* routes for frontend/WebApp (public API)
    # These provide a consistent API prefix for all public endpoints
    # Routes are ordered from most specific to least specific
    
    # Auth endpoints
    cors.add(app.router.add_route("*", "/api/auth/token", route_api_auth))
    cors.add(app.router.add_route("*", "/api/auth/{tail:.*}", route_api_auth))
    
    # Profile endpoints
    cors.add(app.router.add_route("*", "/api/profile/check", route_api_profile))
    cors.add(app.router.add_route("*", "/api/profile/{tail:.*}", route_api_profile))
    cors.add(app.router.add_route("*", "/api/profile", route_api_profile))
    
    # Discovery endpoints (like, pass, matches, favorites, discover)
    cors.add(app.router.add_route("*", "/api/discover", route_api_discovery))
    cors.add(app.router.add_route("*", "/api/like", route_api_discovery))
    cors.add(app.router.add_route("*", "/api/pass", route_api_discovery))
    cors.add(app.router.add_route("*", "/api/matches", route_api_discovery))
    cors.add(app.router.add_route("*", "/api/favorites/{tail:.*}", route_api_discovery))
    cors.add(app.router.add_route("*", "/api/favorites", route_api_discovery))
    
    # Media/photos endpoints
    cors.add(app.router.add_route("*", "/api/photos/upload", route_api_media))
    cors.add(app.router.add_route("*", "/api/photos/{tail:.*}", route_api_media))
    
    # Notification endpoints
    cors.add(app.router.add_route("*", "/api/notifications/{tail:.*}", route_api_notifications))
    
    # Health check
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
        "admin_service_url": os.getenv(
            "ADMIN_SERVICE_URL", "http://admin-service:8086"
        ),
        "notification_service_url": os.getenv(
            "NOTIFICATION_SERVICE_URL", "http://notification-service:8087"
        ),
        "webapp_domain": os.getenv("WEBAPP_DOMAIN", "*"),  # CORS: Allow all origins by default
        "host": os.getenv("GATEWAY_HOST", "0.0.0.0"),
        "port": int(os.getenv("GATEWAY_PORT", 8080)),
    }

    logger.info(
        "Starting api-gateway",
        extra={"event_type": "service_start", "port": config["port"]},
    )

    app = create_app(config)
    web.run_app(app, host=config["host"], port=config["port"])
