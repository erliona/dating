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
from core.middleware.metrics_middleware import metrics_middleware, add_metrics_route

# Business metrics
users_total = Counter('users_total', 'Total number of users')
matches_total = Counter('matches_total', 'Total number of matches')
messages_total = Counter('messages_total', 'Total number of messages')

logger = logging.getLogger(__name__)


async def get_profile(request: web.Request) -> web.Response:
    """Get user profile.

    GET /profiles/{user_id}
    """
    try:
        user_id = int(request.match_info["user_id"])
        data_service_url = request.app["data_service_url"]
        
        # Forward request to Data Service
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{data_service_url}/data/profiles/{user_id}") as response:
                if response.status == 404:
                    return web.json_response({"error": "Profile not found"}, status=404)
                
                if response.status != 200:
                    return web.json_response({"error": "Data service error"}, status=response.status)
                
                profile_data = await response.json()
                return web.json_response(profile_data)
                
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
        
        # Forward request to Data Service
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{data_service_url}/data/profiles",
                json=profile_data
            ) as response:
                if response.status == 409:
                    return web.json_response({"error": "Profile already exists for this user"}, status=409)
                
                if response.status != 201:
                    error_data = await response.json()
                    return web.json_response(error_data, status=response.status)
                
                result = await response.json()
                # Increment business metrics
                users_total.inc()
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
        
        # Get total users count from Data Service
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{data_service_url}/data/profiles/count") as response:
                if response.status == 200:
                    count_data = await response.json()
                    total_users = count_data.get("count", 0)
                    
                    # Set the metric to the current count
                    users_total._value._value = total_users
                    
                    return web.json_response({
                        "status": "success",
                        "users_total": total_users,
                        "message": "Metrics synchronized"
                    })
                else:
                    return web.json_response({"error": "Failed to get user count"}, status=500)
                    
    except Exception as e:
        logger.error(f"Error syncing metrics: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


def create_app(config: dict) -> web.Application:
    """Create and configure the profile service application."""
    app = web.Application()
    app["config"] = config
    
    # Store Data Service URL
    app["data_service_url"] = config["data_service_url"]
    
    # Add middleware
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
