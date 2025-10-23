"""Profile service main entry point.

This microservice handles user profile management by communicating with Data Service.
No direct database connections - all data operations go through Data Service.
"""

import logging
import aiohttp
from prometheus_client import Counter, Histogram

from aiohttp import web
from core.utils.logging import configure_logging
from core.middleware.jwt_middleware import jwt_middleware
from core.middleware.request_logging import request_logging_middleware, user_context_middleware
from core.middleware.metrics_middleware import metrics_middleware, add_metrics_route, USERS_TOTAL, MATCHES_TOTAL, MESSAGES_TOTAL
from core.middleware.correlation import correlation_middleware
from core.resilience.circuit_breaker import data_service_breaker
from core.resilience.retry import retry_data_service

# Business metrics - imported from middleware
users_total = USERS_TOTAL
matches_total = MATCHES_TOTAL
messages_total = MESSAGES_TOTAL

logger = logging.getLogger(__name__)


@retry_data_service()
async def _call_data_service(url: str, method: str = "GET", data: dict = None, correlation_id: str = None):
    """Helper to call Data Service with retry logic."""
    headers = {}
    if correlation_id:
        headers["X-Correlation-ID"] = correlation_id
    
    async with aiohttp.ClientSession() as session:
        async with session.request(method, url, json=data, headers=headers) as resp:
            resp.raise_for_status()
            return await resp.json()


async def get_profile(request: web.Request) -> web.Response:
    """Get user profile.

    GET /profiles/{user_id}
    """
    try:
        user_id = int(request.match_info["user_id"])
        data_service_url = request.app["data_service_url"]
        
        # Use circuit breaker + retry
        correlation_id = request.get("correlation_id")
        result = await data_service_breaker.call(
            _call_data_service,
            f"{data_service_url}/data/profiles/{user_id}",
            "GET",
            None,
            correlation_id,
            fallback=lambda *args: {"error": "Service temporarily unavailable"}
        )
        
        if "error" in result:
            if result["error"] == "Service temporarily unavailable":
                return web.json_response(result, status=503)
            return web.json_response(result, status=404)
        
        return web.json_response(result)
                
    except ValueError:
        return web.json_response({"error": "Invalid user_id"}, status=400)
    except Exception as e:
        logger.error(f"Error getting profile: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def create_profile(request: web.Request) -> web.Response:
    """Create user profile.

    POST /profiles/

    Accepts comprehensive profile data from bot or other clients.
    """
    try:
        profile_data = await request.json()
        data_service_url = request.app["data_service_url"]
        
        # Use circuit breaker + retry
        result = await data_service_breaker.call(
            _call_data_service,
            f"{data_service_url}/data/profiles",
            "POST",
            profile_data,
            fallback=lambda *args: {"error": "Service temporarily unavailable"}
        )
        
        if "error" in result:
            if result["error"] == "Service temporarily unavailable":
                return web.json_response(result, status=503)
            if "already exists" in result.get("error", ""):
                return web.json_response(result, status=409)
            return web.json_response(result, status=400)
        
        # Increment business metrics
        users_total.labels(service='profile-service').inc()
        return web.json_response(result, status=201)
                
    except Exception as e:
        logger.error(f"Error creating profile: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def health_check(request: web.Request) -> web.Response:
    """Health check endpoint."""
    return web.json_response({"status": "healthy", "service": "profile"})


async def sync_metrics(request: web.Request) -> web.Response:
    """Sync business metrics with database data."""
    try:
        data_service_url = request.app["data_service_url"]
        
        # Use circuit breaker + retry
        result = await data_service_breaker.call(
            _call_data_service,
            f"{data_service_url}/data/profiles-count",
            fallback=lambda *args: {"count": 0}
        )
        
        total_users = result.get("count", 0)
        
        # Set the metric to the current count
        users_total.labels(service='profile-service').set(total_users)
        
        return web.json_response({
            "status": "success",
            "users_total": total_users,
            "message": "Metrics synchronized"
        })
                    
    except Exception as e:
        logger.error(f"Error syncing metrics: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def sync_metrics_on_startup(app):
    """Sync business metrics with database on application startup."""
    try:
        data_service_url = app["data_service_url"]
        
        # Use circuit breaker + retry
        result = await data_service_breaker.call(
            _call_data_service,
            f"{data_service_url}/data/profiles-count",
            fallback=lambda *args: {"count": 0}
        )
        
        total_users = result.get("count", 0)
        
        # Set the metric to the current count
        users_total.labels(service='profile-service').set(total_users)
        
        logger.info(f"Metrics synchronized on startup: users_total={total_users}")
                    
    except Exception as e:
        logger.error(f"Error syncing metrics on startup: {e}")


def create_app(config: dict) -> web.Application:
    """Create and configure the profile service application."""
    app = web.Application()
    app["config"] = config
    
    # Store Data Service URL
    app["data_service_url"] = config["data_service_url"]
    
    # Business metrics are imported from middleware
    
    # Add middleware
    app.middlewares.append(correlation_middleware)
    app.middlewares.append(user_context_middleware)
    app.middlewares.append(request_logging_middleware)
    app.middlewares.append(metrics_middleware)
    app.middlewares.append(jwt_middleware)
    
    # Add metrics endpoint
    add_metrics_route(app, "profile-service")

    # Add routes
    app.router.add_get("/profiles/{user_id}", get_profile)
    app.router.add_post("/profiles", create_profile)
    app.router.add_get("/health", health_check)
    app.router.add_post("/sync-metrics", sync_metrics)
    
    # Sync metrics on startup
    app.on_startup.append(sync_metrics_on_startup)

    return app


if __name__ == "__main__":
    import os

    # Configure structured logging
    configure_logging("profile-service", os.getenv("LOG_LEVEL", "INFO"))

    config = {
        "jwt_secret": os.getenv("JWT_SECRET", "your-secret-key"),
        "data_service_url": os.getenv("DATA_SERVICE_URL", "http://data-service:8088"),
        "host": os.getenv("PROFILE_SERVICE_HOST", "0.0.0.0"),
        "port": int(os.getenv("PROFILE_SERVICE_PORT", 8082)),
    }

    logger.info(
        "Starting profile-service",
        extra={"event_type": "service_start", "port": config["port"]},
    )

    app = create_app(config)
    web.run_app(app, host=config["host"], port=config["port"])
