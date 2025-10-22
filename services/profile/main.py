"""Profile service main entry point.

This microservice handles user profile management by communicating with Data Service.
No direct database connections - all data operations go through Data Service.
"""

import logging
import aiohttp

from aiohttp import web
from core.utils.logging import configure_logging
from core.utils.health import create_health_checker, enhanced_health_check
from core.utils.metrics import setup_metrics_middleware
from core.middleware.jwt_middleware import jwt_middleware
from core.middleware.request_logging import request_logging_middleware
from core.middleware.metrics_middleware import metrics_middleware

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
                return web.json_response(result, status=201)
                
    except Exception as e:
        logger.error(f"Error creating profile: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def health_check(request: web.Request) -> web.Response:
    """Enhanced health check endpoint."""
    return await enhanced_health_check(request)


def create_app(config: dict) -> web.Application:
    """Create and configure the profile service application."""
    app = web.Application()
    app["config"] = config
    app["service_name"] = "profile-service"
    
    # Store Data Service URL
    app["data_service_url"] = config["data_service_url"]
    
    # Setup health checker with dependencies
    dependencies = {
        "data-service": config["data_service_url"]
    }
    health_checker = create_health_checker("profile-service", dependencies)
    app["health_checker"] = health_checker
    
    # Setup metrics collection
    setup_metrics_middleware(app, "profile-service")
    
    # Add middleware (order matters!)
    app.middlewares.append(request_logging_middleware)  # First - for request tracing
    app.middlewares.append(metrics_middleware)          # Second - for metrics
    app.middlewares.append(jwt_middleware)              # Third - for authentication

    # Add routes
    app.router.add_get("/profiles/{user_id}", get_profile)
    app.router.add_post("/profiles", create_profile)
    app.router.add_get("/health", health_check)

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
