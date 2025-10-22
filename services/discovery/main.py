"""Discovery service main entry point.

This microservice handles matching algorithm and candidate discovery.
"""

import logging
import aiohttp

from aiohttp import web
from core.utils.logging import configure_logging
from core.middleware.jwt_middleware import jwt_middleware

logger = logging.getLogger(__name__)


async def get_candidates(request: web.Request) -> web.Response:
    """Get candidate profiles for matching.

    GET /discovery/candidates
    Query params: user_id, limit, cursor, filters...
    """
    try:
        user_id = int(request.query.get("user_id", 0))
        limit = int(request.query.get("limit", 10))

        if not user_id:
            return web.json_response({"error": "user_id is required"}, status=400)

        data_service_url = request.app["data_service_url"]
        
        # Build query parameters for Data Service
        params = {
            "user_id": user_id,
            "limit": limit,
        }
        
        # Add cursor if provided
        if request.query.get("cursor"):
            params["cursor"] = request.query.get("cursor")
        
        # Add filters
        filter_params = [
            "age_min", "age_max", "max_distance_km", "goal", "height_min", 
            "height_max", "has_children", "smoking", "drinking", "education", "verified_only"
        ]
        for param in filter_params:
            if request.query.get(param):
                params[param] = request.query.get(param)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{data_service_url}/data/candidates", params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    return web.json_response(result)
                else:
                    logger.error(f"Data service returned status {response.status}")
                    return web.json_response({"error": "Failed to get candidates"}, status=500)

    except ValueError as e:
        return web.json_response({"error": "Invalid parameters"}, status=400)
    except Exception as e:
        logger.error(f"Error getting candidates: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def like_profile(request: web.Request) -> web.Response:
    """Like a profile.

    POST /discovery/like
    Body: {"user_id": int, "target_id": int, "interaction_type": str}
    """
    try:
        data = await request.json()
        user_id = data.get("user_id")
        target_id = data.get("target_id")
        interaction_type = data.get("interaction_type", "like")

        if not user_id or not target_id:
            return web.json_response(
                {"error": "user_id and target_id are required"}, status=400
            )

        data_service_url = request.app["data_service_url"]
        
        interaction_data = {
            "user_id": user_id,
            "target_id": target_id,
            "interaction_type": interaction_type,
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{data_service_url}/data/interactions", json=interaction_data) as response:
                if response.status == 200:
                    result = await response.json()
                    return web.json_response(result)
                else:
                    logger.error(f"Data service returned status {response.status}")
                    return web.json_response({"error": "Failed to create interaction"}, status=500)

    except Exception as e:
        logger.error(f"Error liking profile: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def get_matches(request: web.Request) -> web.Response:
    """Get user matches.

    GET /discovery/matches
    Query params: user_id, limit, cursor
    """
    try:
        user_id = int(request.query.get("user_id", 0))
        limit = int(request.query.get("limit", 20))

        if not user_id:
            return web.json_response({"error": "user_id is required"}, status=400)

        data_service_url = request.app["data_service_url"]
        
        # Build query parameters for Data Service
        params = {
            "user_id": user_id,
            "limit": limit,
        }
        
        # Add cursor if provided
        if request.query.get("cursor"):
            params["cursor"] = request.query.get("cursor")
        
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{data_service_url}/data/matches", params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    return web.json_response(result)
                else:
                    logger.error(f"Data service returned status {response.status}")
                    return web.json_response({"error": "Failed to get matches"}, status=500)

    except ValueError as e:
        return web.json_response({"error": "Invalid parameters"}, status=400)
    except Exception as e:
        logger.error(f"Error getting matches: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def health_check(request: web.Request) -> web.Response:
    """Health check endpoint."""
    return web.json_response({"status": "healthy", "service": "discovery"})


def create_app(config: dict) -> web.Application:
    """Create and configure the discovery service application."""
    app = web.Application()
    app["config"] = config
    app["data_service_url"] = config["data_service_url"]
    
    # Add JWT middleware - temporarily disabled
    # app.middlewares.append(jwt_middleware)

    # Add routes
    app.router.add_get("/discovery/candidates", get_candidates)
    app.router.add_post("/discovery/like", like_profile)
    app.router.add_get("/discovery/matches", get_matches)
    app.router.add_get("/health", health_check)

    return app


if __name__ == "__main__":
    import os

    # Configure structured logging
    configure_logging("discovery-service", os.getenv("LOG_LEVEL", "INFO"))

    config = {
        "jwt_secret": os.getenv("JWT_SECRET", "your-secret-key"),
        "data_service_url": os.getenv("DATA_SERVICE_URL", "http://data-service:8088"),
        "host": os.getenv("DISCOVERY_SERVICE_HOST", "0.0.0.0"),
        "port": int(os.getenv("DISCOVERY_SERVICE_PORT", 8083)),
    }

    logger.info(
        "Starting discovery-service",
        extra={"event_type": "service_start", "port": config["port"]},
    )

    app = create_app(config)
    web.run_app(app, host=config["host"], port=config["port"])
