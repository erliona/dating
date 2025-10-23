"""Profile service main entry point.

This microservice handles user profile management by communicating with Data Service.
No direct database connections - all data operations go through Data Service.
"""

import logging
import aiohttp
import asyncio

from aiohttp import web
from core.utils.logging import configure_logging
from core.utils.validation import validate_profile_data
from core.middleware.standard_stack import setup_standard_middleware_stack
from core.middleware.metrics_middleware import add_metrics_route
from core.middleware.audit_logging import audit_log, log_data_access
from core.middleware.correlation import create_headers_with_correlation, log_correlation_propagation
from core.resilience.circuit_breaker import data_service_breaker
from core.resilience.retry import retry_data_service
from core.metrics.business_metrics import (
    record_profile_created, record_profile_updated, record_profile_deleted,
    update_users_total, update_matches_total, update_messages_total
)
from core.exceptions import ValidationError, CircuitBreakerError, ExternalServiceError, NotFoundError

logger = logging.getLogger(__name__)


@retry_data_service()
async def _call_data_service(url: str, method: str = "GET", data: dict = None, request: web.Request = None):
    """Helper to call Data Service with retry logic and correlation ID propagation."""
    headers = {}
    
    # Add correlation headers if request is provided
    if request:
        headers = create_headers_with_correlation(request)
        log_correlation_propagation(
            correlation_id=request.get('correlation_id', 'unknown'),
            from_service='profile-service',
            to_service='data-service',
            operation=f"{method} {url}",
            request=request
        )
    
    async with aiohttp.ClientSession() as session:
        async with session.request(method, url, json=data, headers=headers) as resp:
            if resp.status >= 400:
                raise ExternalServiceError(
                    service='data-service',
                    message=f"HTTP {resp.status}: {await resp.text()}",
                    details={'url': url, 'method': method, 'status': resp.status}
                )
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
        
        # Audit log profile access
        log_data_access(
            operation="read",
            resource_type="profile",
            resource_id=str(user_id),
            user_id=str(user_id),
            service="profile-service",
            details={"profile_found": True}
        )
        
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
        raw_data = await request.json()
        
        # SECURITY: Validate and sanitize input data
        try:
            profile_data = validate_profile_data(raw_data)
        except ValidationError as e:
            logger.warning(f"Profile validation failed: {e}")
            return web.json_response({"error": str(e)}, status=400)
        
        data_service_url = request.app["data_service_url"]
        
        # Use circuit breaker + retry with correlation ID propagation
        result = await data_service_breaker.call(
            _call_data_service,
            f"{data_service_url}/data/profiles",
            "POST",
            profile_data,
            request,  # Pass request for correlation ID
            fallback=lambda *args: {"error": "Service temporarily unavailable"}
        )
        
        if "error" in result:
            if result["error"] == "Service temporarily unavailable":
                raise CircuitBreakerError("data-service")
            if "already exists" in result.get("error", ""):
                from core.exceptions import ConflictError
                raise ConflictError("Profile already exists", details=result)
            raise ExternalServiceError(
                service='data-service',
                message=result.get("error", "Unknown error"),
                details=result
            )
        
        # Record business metrics
        record_profile_created('profile-service')
        
        # Audit log profile creation
        audit_log(
            operation="profile_create",
            user_id=str(user_id),
            service="profile-service",
            details={
                "profile_data": {
                    "name": profile_data.get("name"),
                    "age": profile_data.get("age"),
                    "bio": profile_data.get("bio", "")[:100] + "..." if len(profile_data.get("bio", "")) > 100 else profile_data.get("bio", "")
                }
            },
            request=request
        )
        
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


async def sync_metrics_periodically():
    """Background task to sync business metrics with database."""
    while True:
        try:
            # This would typically call data-service to get current stats
            # For now, we'll just log that the sync is running
            logger.debug("Syncing profile metrics...")
            
            # TODO: Implement actual metrics sync with data-service
            # result = await _call_data_service(f"{data_service_url}/data/profiles-count")
            # total_users = result.get("count", 0)
            # update_users_total('profile-service', total_users)
            
            await asyncio.sleep(300)  # Update every 5 minutes
        except Exception as e:
            logger.error(f"Failed to sync profile metrics: {e}")
            await asyncio.sleep(60)


async def sync_metrics_on_startup(app):
    """Sync business metrics with database on application startup."""
    try:
        data_service_url = app["data_service_url"]
        
        # Use circuit breaker + retry
        result = await data_service_breaker.call(
            _call_data_service,
            f"{data_service_url}/data/profiles-count",
            None,
            None,
            None,  # No request context for startup
            fallback=lambda *args: {"count": 0}
        )
        
        total_users = result.get("count", 0)
        
        # Set the metric to the current count
        update_users_total('profile-service', total_users)
        
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
    
    # Setup standard middleware stack
    setup_standard_middleware_stack(app, "profile-service", use_auth=True, use_audit=True)
    
    # Add metrics endpoint
    add_metrics_route(app, "profile-service")

    # Add routes
    app.router.add_get("/profiles/{user_id}", get_profile)
    app.router.add_post("/profiles", create_profile)
    app.router.add_get("/health", health_check)
    app.router.add_post("/sync-metrics", sync_metrics)
    
    # Sync metrics on startup and start background task
    app.on_startup.append(sync_metrics_on_startup)
    app.on_startup.append(lambda app: asyncio.create_task(sync_metrics_periodically()))

    return app


if __name__ == "__main__":
    import os

    # Configure structured logging
    configure_logging("profile-service", os.getenv("LOG_LEVEL", "INFO"))

    config = {
        "jwt_secret": os.getenv("JWT_SECRET"),  # SECURITY: No default value
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
