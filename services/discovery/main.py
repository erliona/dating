"""Discovery service main entry point.

This microservice handles matching algorithm and candidate discovery.
"""

import logging
import aiohttp
import asyncio

from aiohttp import web
from core.utils.logging import configure_logging
from core.middleware.standard_stack import setup_standard_middleware_stack
from core.middleware.metrics_middleware import add_metrics_route
from core.resilience.circuit_breaker import data_service_breaker
from core.resilience.retry import retry_data_service
from core.messaging.publisher import EventPublisher
from core.metrics.business_metrics import (
    record_interaction, record_swipe, update_active_users, 
    update_users_by_region, update_matches_current
)
from core.middleware.correlation import create_headers_with_correlation, log_correlation_propagation
from core.exceptions import ValidationError, CircuitBreakerError, ExternalServiceError

logger = logging.getLogger(__name__)

# Initialize event publisher
event_publisher = None


@retry_data_service()
async def _call_data_service(url: str, method: str = "GET", data: dict = None, params: dict = None, request: web.Request = None):
    """Helper to call Data Service with retry logic and correlation ID propagation."""
    headers = {}
    
    # Add correlation headers if request is provided
    if request:
        headers = create_headers_with_correlation(request)
        log_correlation_propagation(
            correlation_id=request.get('correlation_id', 'unknown'),
            from_service='discovery-service',
            to_service='data-service',
            operation=f"{method} {url}",
            request=request
        )
    
    async with aiohttp.ClientSession() as session:
        async with session.request(method, url, json=data, params=params, headers=headers) as resp:
            if resp.status >= 400:
                raise ExternalServiceError(
                    service='data-service',
                    message=f"HTTP {resp.status}: {await resp.text()}",
                    details={'url': url, 'method': method, 'status': resp.status}
                )
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
            raise ValidationError("user_id is required")

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
        
        # Get user profile and preferences for smart matching
        profile_url = f"{data_service_url}/data/profiles/{user_id}"
        profile_result = await data_service_breaker.call(
            _call_data_service,
            profile_url,
            "GET",
            None,
            None,
            request,
            fallback=lambda *args: {}
        )
        
        preferences_url = f"{data_service_url}/data/user-preferences/{user_id}"
        preferences_result = await data_service_breaker.call(
            _call_data_service,
            preferences_url,
            "GET",
            None,
            None,
            request,
            fallback=lambda *args: {}
        )
        
        # Get user's previous interactions to avoid showing same people
        interactions_url = f"{data_service_url}/data/interactions/{user_id}"
        interactions_result = await data_service_breaker.call(
            _call_data_service,
            interactions_url,
            "GET",
            None,
            None,
            request,
            fallback=lambda *args: {"interactions": []}
        )
        
        seen_user_ids = [interaction['target_id'] for interaction in interactions_result.get('interactions', [])]
        params['exclude_user_ids'] = seen_user_ids + [user_id]  # Exclude self and already seen
        
        # Add smart filters based on user preferences
        profile = profile_result.get('profile', {})
        preferences = preferences_result.get('preferences', {})
        
        if preferences.get('preferred_gender'):
            params['gender'] = preferences['preferred_gender']
        elif profile.get('orientation'):
            params['gender'] = profile['orientation']
            
        if preferences.get('min_age'):
            params['age_min'] = preferences['min_age']
        if preferences.get('max_age'):
            params['age_max'] = preferences['max_age']
        if preferences.get('max_distance_km'):
            params['max_distance_km'] = preferences['max_distance_km']
        else:
            params['max_distance_km'] = 50  # Default radius
        
        # Get more candidates for better filtering
        params['limit'] = limit * 2
        
        # Use circuit breaker + retry with correlation ID propagation
        result = await data_service_breaker.call(
            _call_data_service,
            f"{data_service_url}/data/candidates",
            "GET",
            None,
            params,
            request,  # Pass request for correlation ID
            fallback=lambda *args: {"candidates": [], "cursor": None}
        )
        
        if "error" in result:
            raise ExternalServiceError(
                service='data-service',
                message=result.get("error", "Unknown error"),
                details=result
            )
        
        candidates = result.get("candidates", [])
        
        # If we have less than 5 candidates, expand search radius
        if len(candidates) < 5:
            expanded_params = params.copy()
            expanded_params['max_distance_km'] = min(expanded_params.get('max_distance_km', 50) * 2, 200)
            expanded_params['exclude_user_ids'] = seen_user_ids + [user_id]  # Don't include already fetched
            
            expanded_result = await data_service_breaker.call(
                _call_data_service,
                f"{data_service_url}/data/candidates",
                "GET",
                None,
                expanded_params,
                request,
                fallback=lambda *args: {"candidates": []}
            )
            
            additional_candidates = expanded_result.get("candidates", [])
            
            # Merge and deduplicate
            existing_ids = {c['id'] for c in candidates}
            for candidate in additional_candidates:
                if candidate['id'] not in existing_ids:
                    candidates.append(candidate)
                    existing_ids.add(candidate['id'])
        
        # Smart sorting: verified first, then by distance, then by interests match, then random
        def sort_key(candidate):
            verified_bonus = 1000 if candidate.get('is_verified', False) else 0
            distance_penalty = candidate.get('distance', 999) * 10
            
            # Interest matching bonus
            interest_bonus = 0
            if profile.get('interests') and candidate.get('interests'):
                common_interests = set(profile['interests']) & set(candidate['interests'])
                interest_bonus = len(common_interests) * 50
            
            # Random factor for variety
            random_factor = hash(str(candidate['id'])) % 100
            
            return verified_bonus - distance_penalty + interest_bonus + random_factor
        
        candidates.sort(key=sort_key, reverse=True)
        
        # Limit to requested number
        candidates = candidates[:limit]
        
        # Record metrics
        record_interaction()
        update_active_users()
        
        return web.json_response({
            'candidates': candidates,
            'total': len(candidates),
            'cursor': result.get('cursor'),
            'search_radius_km': params.get('max_distance_km', 50)
        })

    except ValueError as e:
        raise ValidationError("Invalid parameters", details={"error": str(e)})
    except Exception as e:
        logger.error(f"Error getting candidates: {e}", exc_info=True)
        raise


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
            raise ValidationError("user_id and target_id are required")

        data_service_url = request.app["data_service_url"]
        
        interaction_data = {
            "user_id": user_id,
            "target_id": target_id,
            "interaction_type": interaction_type,
        }
        
        # Use circuit breaker + retry with correlation ID propagation
        result = await data_service_breaker.call(
            _call_data_service,
            f"{data_service_url}/data/interactions",
            "POST",
            interaction_data,
            None,
            request,  # Pass request for correlation ID
            fallback=lambda *args: {"error": "Service temporarily unavailable"}
        )
        
        if "error" in result:
            if result["error"] == "Service temporarily unavailable":
                raise CircuitBreakerError("data-service")
            raise ExternalServiceError(
                service='data-service',
                message=result.get("error", "Unknown error"),
                details=result
            )
        
        # Record metrics
        record_interaction('discovery-service', interaction_type)
        record_swipe('discovery-service', interaction_type)
        
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
            
            # Record match metric
            record_interaction('discovery-service', 'match')
        
        return web.json_response(result)

    except Exception as e:
        logger.error(f"Error liking profile: {e}", exc_info=True)
        raise


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


async def sync_discovery_metrics():
    """Background task to sync discovery metrics with database."""
    while True:
        try:
            # This would typically call data-service to get current stats
            # For now, we'll just log that the sync is running
            logger.debug("Syncing discovery metrics...")
            
            # TODO: Implement actual metrics sync with data-service
            # stats = await get_discovery_stats()
            # update_active_users('discovery-service', stats['active_users_24h'])
            # for region, count in stats['users_by_region'].items():
            #     update_users_by_region('discovery-service', region, count)
            
            await asyncio.sleep(300)  # Update every 5 minutes
        except Exception as e:
            logger.error(f"Failed to sync discovery metrics: {e}")
            await asyncio.sleep(60)


async def on_startup(app):
    """Startup handler."""
    global event_publisher
    rabbitmq_url = app["config"].get("rabbitmq_url")
    if rabbitmq_url:
        event_publisher = EventPublisher(rabbitmq_url)
        await event_publisher.connect()
        logger.info("Event publisher initialized")
    
    # Start metrics sync background task
    app['metrics_sync_task'] = asyncio.create_task(sync_discovery_metrics())
    logger.info("Metrics sync task started")


async def on_shutdown(app):
    """Shutdown handler."""
    global event_publisher
    
    # Cancel metrics sync task
    if 'metrics_sync_task' in app:
        app['metrics_sync_task'].cancel()
        try:
            await app['metrics_sync_task']
        except asyncio.CancelledError:
            pass
        logger.info("Metrics sync task cancelled")
    
    if event_publisher:
        await event_publisher.close()
        logger.info("Event publisher closed")


def create_app(config: dict) -> web.Application:
    """Create and configure the discovery service application."""
    app = web.Application()
    app["config"] = config
    app["data_service_url"] = config["data_service_url"]
    
    # Setup standard middleware stack
    setup_standard_middleware_stack(app, "discovery-service", use_auth=True, use_audit=True)
    
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
