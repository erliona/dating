"""Discovery service main entry point.

This microservice handles matching algorithm and candidate discovery.
"""

import logging
import aiohttp
from prometheus_client import Counter

from aiohttp import web
from core.utils.logging import configure_logging
from core.middleware.jwt_middleware import jwt_middleware
from core.middleware.request_logging import request_logging_middleware, user_context_middleware
from core.middleware.metrics_middleware import metrics_middleware, add_metrics_route
from core.resilience.circuit_breaker import data_service_breaker
from core.resilience.retry import retry_data_service
from core.messaging.publisher import EventPublisher

# Business metrics - create only if not already registered
try:
    matches_total = Counter('matches_total', 'Total number of matches')
except ValueError:
    # Metric already exists, get it from registry
    from prometheus_client import REGISTRY
    matches_total = REGISTRY._names_to_collectors['matches_total']

logger = logging.getLogger(__name__)

# Initialize event publisher
event_publisher = None


@retry_data_service()
async def _call_data_service(url: str, method: str = "GET", data: dict = None, params: dict = None):
    """Helper to call Data Service with retry logic."""
    async with aiohttp.ClientSession() as session:
        async with session.request(method, url, json=data, params=params) as resp:
            resp.raise_for_status()
            return await resp.json()


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
        
        # Use circuit breaker + retry
        result = await data_service_breaker.call(
            _call_data_service,
            f"{data_service_url}/data/candidates",
            "GET",
            None,
            params,
            fallback=lambda *args: {"candidates": [], "cursor": None}
        )
        
        if "error" in result:
            return web.json_response(result, status=500)
        
        return web.json_response(result)

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
        
        # Use circuit breaker + retry
        result = await data_service_breaker.call(
            _call_data_service,
            f"{data_service_url}/data/interactions",
            "POST",
            interaction_data,
            fallback=lambda *args: {"error": "Service temporarily unavailable"}
        )
        
        if "error" in result:
            if result["error"] == "Service temporarily unavailable":
                return web.json_response(result, status=503)
            return web.json_response(result, status=500)
        
        # Check if it's a match and publish event
        if result.get("is_match") and event_publisher:
            correlation_id = request.get("correlation_id")
            await event_publisher.publish_event(
                "match.created",
                {
                    "user_id_1": user_id,
                    "user_id_2": target_id,
                    "matched_at": result.get("created_at"),
                    "interaction_type": interaction_type
                },
                correlation_id=correlation_id
            )
        
        return web.json_response(result)

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
        
        # Use circuit breaker + retry
        result = await data_service_breaker.call(
            _call_data_service,
            f"{data_service_url}/data/matches",
            "GET",
            None,
            params,
            fallback=lambda *args: {"matches": [], "cursor": None}
        )
        
        if "error" in result:
            return web.json_response(result, status=500)
        
        # Increment business metrics for each match
        if result and "matches" in result:
            matches_total.inc(len(result["matches"]))
        
        return web.json_response(result)

    except ValueError as e:
        return web.json_response({"error": "Invalid parameters"}, status=400)
    except Exception as e:
        logger.error(f"Error getting matches: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def health_check(request: web.Request) -> web.Response:
    """Health check endpoint."""
    return web.json_response({"status": "healthy", "service": "discovery"})


async def on_startup(app):
    """Startup handler."""
    global event_publisher
    rabbitmq_url = app["config"].get("rabbitmq_url")
    if rabbitmq_url:
        event_publisher = EventPublisher(rabbitmq_url)
        await event_publisher.connect()
        logger.info("Event publisher initialized")


async def on_shutdown(app):
    """Shutdown handler."""
    global event_publisher
    if event_publisher:
        await event_publisher.close()
        logger.info("Event publisher closed")


def create_app(config: dict) -> web.Application:
    """Create and configure the discovery service application."""
    app = web.Application()
    app["config"] = config
    app["data_service_url"] = config["data_service_url"]
    
    # Add middleware
    app.middlewares.append(user_context_middleware)
    app.middlewares.append(request_logging_middleware)
    app.middlewares.append(metrics_middleware)
    app.middlewares.append(jwt_middleware)
    
    # Add metrics endpoint
    add_metrics_route(app, "discovery-service")

    # Add routes
    app.router.add_get("/discovery/candidates", get_candidates)
    app.router.add_post("/discovery/like", like_profile)
    app.router.add_get("/discovery/matches", get_matches)
    app.router.add_get("/health", health_check)
    
    # Add startup/shutdown handlers
    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)

    return app


if __name__ == "__main__":
    import os

    # Configure structured logging
    configure_logging("discovery-service", os.getenv("LOG_LEVEL", "INFO"))

    config = {
        "jwt_secret": os.getenv("JWT_SECRET"),  # SECURITY: No default value
        "data_service_url": os.getenv("DATA_SERVICE_URL", "http://data-service:8088"),
        "rabbitmq_url": os.getenv("RABBITMQ_URL", "amqp://dating:dating@rabbitmq:5672/"),
        "host": os.getenv("DISCOVERY_SERVICE_HOST", "0.0.0.0"),
        "port": int(os.getenv("DISCOVERY_SERVICE_PORT", 8083)),
    }

    logger.info(
        "Starting discovery-service",
        extra={"event_type": "service_start", "port": config["port"]},
    )

    app = create_app(config)
    web.run_app(app, host=config["host"], port=config["port"])
