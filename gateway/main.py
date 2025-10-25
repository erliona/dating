from __future__ import annotations

"""API Gateway main entry point - Simplified v1-only routing.

This service routes requests to appropriate microservices with WebSocket support.
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
from .websocket_proxy import proxy_websocket, is_websocket_request

logger = logging.getLogger(__name__)


async def proxy_request(
    request: web.Request, target_url: str, path_override: str = None
) -> web.Response:
    """Proxy request to target microservice."""
    timeout = ClientTimeout(total=30, connect=10)

    try:
        async with ClientSession(timeout=timeout) as session:
            # Build target URL - strip /v1/{service}/ prefix
            if path_override:
                path = path_override
            else:
                # Extract path after /v1/{service}/
                path_parts = request.path.split('/')
                if len(path_parts) >= 4 and path_parts[1] == 'v1':
                    # Remove /v1/{service} prefix
                    path = '/' + '/'.join(path_parts[3:])
                else:
                    path = request.path
            
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

            # Make request
            async with session.request(
                method=request.method,
                url=full_url,
                headers=headers,
                data=await request.read() if request.can_read_body else None,
            ) as response:
                # Read response body
                body = await response.read()
                
                # Create response
                return web.Response(
                    body=body,
                    status=response.status,
                    headers=dict(response.headers)
                )

    except Exception as e:
        logger.error(f"Proxy error: {e}")
        return web.json_response({"error": "Service unavailable"}, status=503)


# ==================== ROUTING FUNCTIONS ====================

async def route_auth(request: web.Request) -> web.Response:
    """Route auth requests to auth-service."""
    target_url = request.app["config"]["auth_service_url"]
    return await proxy_request(request, target_url)


async def route_profile(request: web.Request) -> web.Response:
    """Route profile requests to profile-service."""
    target_url = request.app["config"]["profile_service_url"]
    return await proxy_request(request, target_url)


async def route_discovery(request: web.Request) -> web.Response:
    """Route discovery requests to discovery-service."""
    target_url = request.app["config"]["discovery_service_url"]
    return await proxy_request(request, target_url)


async def route_media(request: web.Request) -> web.Response:
    """Route media requests to media-service."""
    target_url = request.app["config"]["media_service_url"]
    return await proxy_request(request, target_url)


async def route_chat(request: web.Request) -> web.Response:
    """Route chat requests to chat-service with WebSocket support."""
    target_url = request.app["config"]["chat_service_url"]
    
    # Check if this is a WebSocket request
    if is_websocket_request(request):
        return await proxy_websocket(request, target_url)
    
    # Regular HTTP request
    return await proxy_request(request, target_url)


async def route_admin(request: web.Request) -> web.Response:
    """Route admin requests to admin-service."""
    target_url = request.app["config"]["admin_service_url"]
    return await proxy_request(request, target_url)


async def route_notifications(request: web.Request) -> web.Response:
    """Route notification requests to notification-service."""
    target_url = request.app["config"]["notification_service_url"]
    return await proxy_request(request, target_url)


# ==================== HEALTH & METRICS ====================

async def health_check(request: web.Request) -> web.Response:
    """Health check endpoint."""
    return web.json_response({
        "status": "healthy",
        "service": "api-gateway",
        "version": "2.0.0"
    })


# ==================== APPLICATION SETUP ====================

def create_app(config: dict) -> web.Application:
    """Create and configure the API Gateway application."""
    app = web.Application()
    app["config"] = config
    
    # Create HTTP session for WebSocket connections
    app["http_session"] = ClientSession()
    
    # Add middleware
    app.middlewares.append(request_logging_middleware)
    app.middlewares.append(user_context_middleware)
    app.middlewares.append(metrics_middleware)
    app.middlewares.append(versioning_middleware)
    app.middlewares.append(correlation_middleware)
    
    # Setup CORS
    # Configure CORS with multiple origins
    allowed_origins = [
        "https://web.telegram.org",
        "https://telegram.org",
        f"https://{os.getenv('DOMAIN', 'localhost')}",
        f"http://{os.getenv('DOMAIN', 'localhost')}",
        "http://localhost:3000",  # Development
        "http://localhost:5173",  # Vite dev server
    ]
    
    # Add additional origins from environment
    extra_origins = os.getenv('CORS_ORIGINS', '').split(',')
    allowed_origins.extend([origin.strip() for origin in extra_origins if origin.strip()])
    
    cors = cors_setup(app, defaults={
        "*": ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods="*",
            allow_origins=allowed_origins
        )
    })
    
    # Add metrics endpoint
    add_metrics_route(app, "api-gateway")
    
    # ==================== ROUTES ====================
    
    # Health check
    app.router.add_get("/health", health_check)
    
    # v1 API routes
    app.router.add_route("*", r"/v1/auth/{tail:.*}", route_auth)
    app.router.add_route("*", r"/v1/profiles/{tail:.*}", route_profile)
    app.router.add_route("*", r"/v1/discovery/{tail:.*}", route_discovery)
    app.router.add_route("*", r"/v1/media/{tail:.*}", route_media)
    app.router.add_route("*", r"/v1/chat/{tail:.*}", route_chat)
    app.router.add_route("*", r"/v1/admin/{tail:.*}", route_admin)
    app.router.add_route("*", r"/v1/notifications/{tail:.*}", route_notifications)
    
    # Add CORS to all routes
    for route in app.router.routes():
        cors.add(route)
    
    return app


async def cleanup_session(app: web.Application):
    """Cleanup HTTP session on app shutdown."""
    if "http_session" in app:
        await app["http_session"].close()


if __name__ == "__main__":
    # Configure structured logging
    configure_logging("api-gateway", os.getenv("LOG_LEVEL", "INFO"))

    config = {
        "auth_service_url": os.getenv("AUTH_SERVICE_URL", "http://auth-service:8081"),
        "profile_service_url": os.getenv("PROFILE_SERVICE_URL", "http://profile-service:8082"),
        "discovery_service_url": os.getenv("DISCOVERY_SERVICE_URL", "http://discovery-service:8083"),
        "media_service_url": os.getenv("MEDIA_SERVICE_URL", "http://media-service:8084"),
        "chat_service_url": os.getenv("CHAT_SERVICE_URL", "http://chat-service:8085"),
        "admin_service_url": os.getenv("ADMIN_SERVICE_URL", "http://admin-service:8086"),
        "notification_service_url": os.getenv("NOTIFICATION_SERVICE_URL", "http://notification-service:8087"),
    }

    logger.info(
        "Starting API Gateway v2.0",
        extra={"event_type": "service_start", "config": config},
    )

    app = create_app(config)
    
    # Add cleanup handler
    app.on_cleanup.append(cleanup_session)
    
    web.run_app(app, host=config.get("host", "0.0.0.0"), port=config.get("port", 8080))
