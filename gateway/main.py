from __future__ import annotations

"""API Gateway main entry point.

This service routes requests to appropriate microservices.
"""

import logging
import os

from aiohttp import ClientSession, ClientTimeout, web
from aiohttp_cors import ResourceOptions
from aiohttp_cors import setup as cors_setup

from core.utils.logging import configure_logging
from core.middleware.request_logging import request_logging_middleware, user_context_middleware
from core.middleware.metrics_middleware import metrics_middleware, add_metrics_route
from core.middleware.versioning import versioning_middleware
from core.middleware.correlation import correlation_middleware

logger = logging.getLogger(__name__)


async def proxy_request(
    request: web.Request, target_url: str, path_override: str = None
) -> web.Response:
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

            # Prepare headers
            headers = {
                k: v
                for k, v in request.headers.items()
                if k.lower() not in ["host", "connection"]
            }
            
            # Add correlation ID if present
            correlation_id = request.get("correlation_id")
            if correlation_id:
                headers["X-Correlation-ID"] = correlation_id
            
            # Forward request
            async with session.request(
                method=request.method,
                url=full_url,
                headers=headers,
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
    # Strip /v1/auth prefix from path for internal routing
    new_path = request.path.replace("/v1/auth", "", 1)
    if not new_path:
        new_path = "/"
    logger.info(f"Routing auth request: {request.path} -> {new_path} (target: {auth_url})")
    return await proxy_request(request, auth_url, path_override=new_path)


async def route_profile(request: web.Request) -> web.Response:
    """Route to profile service."""
    profile_url = request.app["config"]["profile_service_url"]
    # Strip /v1 prefix from path for internal routing
    new_path = request.path.replace("/v1/profile", "/profile", 1)
    return await proxy_request(request, profile_url, path_override=new_path)


async def route_discovery(request: web.Request) -> web.Response:
    """Route to discovery service."""
    discovery_url = request.app["config"]["discovery_service_url"]
    # Strip /v1 prefix from path for internal routing
    new_path = request.path.replace("/v1/discovery", "/discovery", 1)
    return await proxy_request(request, discovery_url, path_override=new_path)


async def route_media(request: web.Request) -> web.Response:
    """Route to media service."""
    media_url = request.app["config"]["media_service_url"]
    # Strip /v1 prefix from path for internal routing
    new_path = request.path.replace("/v1/media", "/media", 1)
    return await proxy_request(request, media_url, path_override=new_path)


async def route_chat(request: web.Request) -> web.Response:
    """Route to chat service."""
    chat_url = request.app["config"]["chat_service_url"]
    # Strip /v1 prefix from path for internal routing
    new_path = request.path.replace("/v1/chat", "/chat", 1)
    return await proxy_request(request, chat_url, path_override=new_path)


async def route_admin(request: web.Request) -> web.Response:
    """Route to admin service."""
    admin_url = request.app["config"]["admin_service_url"]
    # Strip /v1 prefix from path for internal routing
    new_path = request.path.replace("/v1/admin", "/admin", 1)
    return await proxy_request(request, admin_url, path_override=new_path)


async def route_notifications(request: web.Request) -> web.Response:
    """Route to notification service."""
    notification_url = request.app["config"]["notification_service_url"]
    # Strip /v1 prefix from path for internal routing
    new_path = request.path.replace("/v1/notifications", "/notifications", 1)
    return await proxy_request(request, notification_url, path_override=new_path)


async def route_api_auth(request: web.Request) -> web.Response:
    """Route /api/auth/* to auth service, stripping /api prefix."""
    auth_url = request.app["config"]["auth_service_url"]
    # Strip /api/v1 prefix from path
    new_path = request.path.replace("/api/v1/auth", "/auth", 1)
    return await proxy_request(request, auth_url, path_override=new_path)


async def route_api_profile(request: web.Request) -> web.Response:
    """Route /api/profile/* to profile service, mapping to /profiles/*."""
    profile_url = request.app["config"]["profile_service_url"]
    # Map /api/v1/profile to /profiles
    new_path = request.path.replace("/api/v1/profile", "/profiles", 1)
    return await proxy_request(request, profile_url, path_override=new_path)


async def route_api_profiles(request: web.Request) -> web.Response:
    """Route /api/profiles/* to profile service, mapping to /profiles/*."""
    profile_url = request.app["config"]["profile_service_url"]
    # Map /api/v1/profiles to /profiles
    new_path = request.path.replace("/api/v1/profiles", "/profiles", 1)
    return await proxy_request(request, profile_url, path_override=new_path)


async def route_api_discovery(request: web.Request) -> web.Response:
    """Route /api/discover, /api/like, /api/pass, /api/matches, /api/favorites to discovery service."""
    discovery_url = request.app["config"]["discovery_service_url"]
    # Map /api/v1/* to /discovery/*
    path = request.path
    if path.startswith("/api/v1/discover"):
        new_path = path.replace("/api/v1/discover", "/discovery/discover", 1)
    elif path.startswith("/api/v1/like"):
        new_path = path.replace("/api/v1/like", "/discovery/like", 1)
    elif path.startswith("/api/v1/pass"):
        new_path = path.replace("/api/v1/pass", "/discovery/pass", 1)
    elif path.startswith("/api/v1/matches"):
        new_path = path.replace("/api/v1/matches", "/discovery/matches", 1)
    elif path.startswith("/api/v1/favorites"):
        new_path = path.replace("/api/v1/favorites", "/discovery/favorites", 1)
    else:
        new_path = path.replace("/api/v1/", "/discovery/", 1)

    return await proxy_request(request, discovery_url, path_override=new_path)


async def route_api_media(request: web.Request) -> web.Response:
    """Route /api/photos/* to media service, mapping to /media/*."""
    media_url = request.app["config"]["media_service_url"]
    # Map /api/v1/photos to /media
    new_path = request.path.replace("/api/v1/photos", "/media", 1)
    return await proxy_request(request, media_url, path_override=new_path)


async def route_api_notifications(request: web.Request) -> web.Response:
    """Route /api/notifications/* to notification service."""
    notification_url = request.app["config"]["notification_service_url"]
    # Map /api/v1/notifications to /notifications
    new_path = request.path.replace("/api/v1/notifications", "/notifications", 1)
    return await proxy_request(request, notification_url, path_override=new_path)


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
    
    # Add middleware for request logging and user context
    app.middlewares.append(correlation_middleware)
    app.middlewares.append(versioning_middleware)
    app.middlewares.append(user_context_middleware)
    app.middlewares.append(request_logging_middleware)
    app.middlewares.append(metrics_middleware)
    
    # Add metrics endpoint
    add_metrics_route(app, "api-gateway")

    # Setup CORS for WebApp/frontend access
    # SECURITY: Restrict CORS to specific domains only
    webapp_domain = config.get("webapp_domain")
    if not webapp_domain:
        logger.error("webapp_domain not configured - CORS will be disabled for security")
        # In production, we should fail if webapp_domain is not set
        # For now, we'll use a restrictive default
        webapp_domain = "https://localhost:3000"  # Development only
    
    cors = cors_setup(
        app,
        defaults={
            webapp_domain: ResourceOptions(
                allow_credentials=True,
                expose_headers=("Content-Type", "Authorization", "X-Requested-With"),
                allow_headers=("Content-Type", "Authorization", "X-Requested-With"),
                allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
            )
        },
    )
    logger.info(f"CORS configured for domain: {webapp_domain}")

    # Helper function to add CORS-enabled routes for all methods
    # aiohttp_cors doesn't support "*" method, so we register each method individually
    # Note: OPTIONS is handled automatically by aiohttp_cors, no need to add it explicitly
    def add_cors_route(path: str, handler):
        """Add a route with CORS support for all HTTP methods."""
        for method in ["GET", "POST", "PUT", "PATCH", "DELETE"]:
            cors.add(app.router.add_route(method, path, handler))

    # Add routing rules for direct service access (internal/microservice-to-microservice)
    # Versioned routes (v1) - use proper route syntax
    # Add specific routes first, then catch-all routes
    app.router.add_get("/v1/auth/health", route_auth)
    app.router.add_route("*", r"/v1/auth/{tail:.*}", route_auth)
    app.router.add_route("*", r"/v1/profile/{tail:.*}", route_profile)
    app.router.add_route("*", r"/v1/profiles/{tail:.*}", route_profile)
    app.router.add_route("*", r"/v1/discovery/{tail:.*}", route_discovery)
    app.router.add_route("*", r"/v1/media/{tail:.*}", route_media)
    app.router.add_route("*", r"/v1/chat/{tail:.*}", route_chat)
    app.router.add_route("*", r"/v1/admin/{tail:.*}", route_admin)
    app.router.add_route("*", r"/v1/notifications/{tail:.*}", route_notifications)
    
    # Legacy routes (redirect to v1)
    async def redirect_to_v1(request: web.Request) -> web.Response:
        """Redirect legacy routes to v1."""
        new_path = f"/v1{request.path}"
        logger.warning(
            f"Legacy route redirected: {request.path} -> {new_path}",
            extra={"event_type": "legacy_redirect"}
        )
        return web.HTTPMovedPermanently(location=new_path)
    
    app.router.add_route("*", "/auth/{tail:.*}", redirect_to_v1)
    app.router.add_route("*", "/profiles/{tail:.*}", redirect_to_v1)
    app.router.add_route("*", "/discovery/{tail:.*}", redirect_to_v1)
    app.router.add_route("*", "/media/{tail:.*}", redirect_to_v1)
    app.router.add_route("*", "/chat/{tail:.*}", redirect_to_v1)
    app.router.add_route("*", "/admin/{tail:.*}", redirect_to_v1)
    app.router.add_route("*", "/admin-panel/{tail:.*}", route_admin)  # Keep admin-panel as is
    app.router.add_route("*", "/notifications/{tail:.*}", redirect_to_v1)

    # Add unified /api/* routes for frontend/WebApp (public API)
    # These provide a consistent API prefix for all public endpoints
    # Routes are ordered from most specific to least specific

    # Versioned API routes (v1)
    # Auth endpoints
    add_cors_route("/api/v1/auth/token", route_api_auth)
    add_cors_route("/api/v1/auth/{tail:.*}", route_api_auth)

    # Profile endpoints
    add_cors_route("/api/v1/profile/check", route_api_profile)
    add_cors_route("/api/v1/profile/{tail:.*}", route_api_profile)
    add_cors_route("/api/v1/profile", route_api_profile)
    add_cors_route("/api/v1/profiles/{tail:.*}", route_api_profiles)
    add_cors_route("/api/v1/profiles", route_api_profiles)

    # Discovery endpoints (like, pass, matches, favorites, discover)
    add_cors_route("/api/v1/discover", route_api_discovery)
    add_cors_route("/api/v1/like", route_api_discovery)
    add_cors_route("/api/v1/pass", route_api_discovery)
    add_cors_route("/api/v1/matches", route_api_discovery)
    add_cors_route("/api/v1/favorites/{tail:.*}", route_api_discovery)
    add_cors_route("/api/v1/favorites", route_api_discovery)

    # Media/photos endpoints
    add_cors_route("/api/v1/photos/upload", route_api_media)
    add_cors_route("/api/v1/photos/{tail:.*}", route_api_media)

    # Legacy API routes (redirect to v1)
    async def redirect_api_to_v1(request: web.Request) -> web.Response:
        """Redirect legacy API routes to v1."""
        new_path = f"/api/v1{request.path[4:]}"  # Remove /api and add /api/v1
        logger.warning(
            f"Legacy API route redirected: {request.path} -> {new_path}",
            extra={"event_type": "legacy_api_redirect"}
        )
        return web.HTTPMovedPermanently(location=new_path)
    
    # Legacy auth endpoints
    add_cors_route("/api/auth/token", redirect_api_to_v1)
    add_cors_route("/api/auth/{tail:.*}", redirect_api_to_v1)

    # Legacy profile endpoints
    add_cors_route("/api/profile/check", redirect_api_to_v1)
    add_cors_route("/api/profile/{tail:.*}", redirect_api_to_v1)
    add_cors_route("/api/profile", redirect_api_to_v1)
    add_cors_route("/api/profiles/{tail:.*}", redirect_api_to_v1)
    add_cors_route("/api/profiles", redirect_api_to_v1)

    # Legacy discovery endpoints
    add_cors_route("/api/discover", redirect_api_to_v1)
    add_cors_route("/api/like", redirect_api_to_v1)
    add_cors_route("/api/pass", redirect_api_to_v1)
    add_cors_route("/api/matches", redirect_api_to_v1)
    add_cors_route("/api/favorites/{tail:.*}", redirect_api_to_v1)
    add_cors_route("/api/favorites", redirect_api_to_v1)

    # Legacy media/photos endpoints
    add_cors_route("/api/photos/upload", redirect_api_to_v1)
    add_cors_route("/api/photos/{tail:.*}", redirect_api_to_v1)

    # Notification endpoints
    add_cors_route("/api/notifications/{tail:.*}", route_api_notifications)

    # Health check
    app.router.add_get("/health", health_check)
    app.router.add_get("/api/health", health_check)

    # Debug: Log all registered routes
    logger.info("Registered routes:")
    for route in app.router.routes():
        logger.info(f"  {route.method} {route.resource.canonical}")

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
        "webapp_domain": os.getenv(
            "WEBAPP_DOMAIN"
        ),  # SECURITY: No default - must be explicitly configured
        "host": os.getenv("GATEWAY_HOST", "0.0.0.0"),
        "port": int(os.getenv("GATEWAY_PORT", 8080)),
    }

    logger.info(
        "Starting api-gateway",
        extra={"event_type": "service_start", "port": config["port"]},
    )

    app = create_app(config)
    web.run_app(app, host=config["host"], port=config["port"])
