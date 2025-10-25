from __future__ import annotations

"""Profile service main entry point.

This microservice handles user profile management by communicating with Data Service.
No direct database connections - all data operations go through Data Service.
"""

import asyncio
import logging

import aiohttp
from aiohttp import web

from core.exceptions import CircuitBreakerError, ExternalServiceError, ValidationError
from core.metrics.business_metrics import (
    record_profile_created,
    record_profile_updated,
    update_users_total,
)
from core.middleware.audit_logging import audit_log, log_data_access
from core.middleware.correlation import (
    create_headers_with_correlation,
    log_correlation_propagation,
)
from core.middleware.error_handling import setup_error_handling
from core.middleware.metrics_middleware import add_metrics_route
from core.middleware.standard_stack import setup_standard_middleware_stack
from core.resilience.circuit_breaker import data_service_breaker
from core.resilience.retry import retry_data_service
from core.utils.logging import configure_logging
from core.utils.validation import validate_profile_data

logger = logging.getLogger(__name__)


async def queue_for_moderation(
    content_type: str,
    content_id: str,
    user_id: str,
    reason: str = "profile_update",
    priority: int = 1,
) -> None:
    """Queue content for moderation via data service."""
    try:
        data_service_url = os.getenv("data_service_url", "http://data-service:8088")
        url = f"{data_service_url}/moderation/queue"

        payload = {
            "content_type": content_type,
            "content_id": content_id,
            "user_id": user_id,
            "reason": reason,
            "priority": priority,
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status not in [200, 201]:
                    error_text = await response.text()
                    logger.error(
                        f"Failed to queue moderation: {response.status} - {error_text}"
                    )
                    raise Exception(f"Moderation queue failed: {response.status}")

    except Exception as e:
        logger.error(f"Error queuing for moderation: {e}")
        raise


@retry_data_service()
async def _call_data_service(
    url: str, method: str = "GET", data: dict = None, request: web.Request = None
):
    """Helper to call Data Service with retry logic and correlation ID propagation."""
    headers = {}

    # Add correlation headers if request is provided
    if request:
        headers = create_headers_with_correlation(request)
        log_correlation_propagation(
            correlation_id=request.get("correlation_id", "unknown"),
            from_service="profile-service",
            to_service="data-service",
            operation=f"{method} {url}",
            request=request,
        )

    async with aiohttp.ClientSession() as session:
        async with session.request(method, url, json=data, headers=headers) as resp:
            if resp.status >= 400:
                raise ExternalServiceError(
                    service="data-service",
                    message=f"HTTP {resp.status}: {await resp.text()}",
                    details={"url": url, "method": method, "status": resp.status},
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
            fallback=lambda *args: {"error": "Service temporarily unavailable"},
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
            details={"profile_found": True},
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
            fallback=lambda *args: {"error": "Service temporarily unavailable"},
        )

        if "error" in result:
            if result["error"] == "Service temporarily unavailable":
                raise CircuitBreakerError("data-service")
            if "already exists" in result.get("error", ""):
                from core.exceptions import ConflictError

                raise ConflictError("Profile already exists", details=result)
            raise ExternalServiceError(
                service="data-service",
                message=result.get("error", "Unknown error"),
                details=result,
            )

        # Record business metrics
        record_profile_created("profile-service")

        # Extract user_id from profile_data for audit log
        user_id = profile_data.get("user_id")

        # Audit log profile creation
        audit_log(
            operation="profile_create",
            user_id=str(user_id),
            service="profile-service",
            details={
                "profile_data": {
                    "name": profile_data.get("name"),
                    "age": profile_data.get("age"),
                    "bio": (
                        profile_data.get("bio", "")[:100] + "..."
                        if len(profile_data.get("bio", "")) > 100
                        else profile_data.get("bio", "")
                    ),
                }
            },
            request=request,
        )

        return web.json_response(result, status=201)

    except Exception as e:
        logger.error(f"Error creating profile: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def health_check(request: web.Request) -> web.Response:
    """Health check endpoint."""
    return web.json_response({"status": "healthy", "service": "profile"})


async def get_current_profile(request: web.Request) -> web.Response:
    """Get current user's profile (JWT-based).

    GET /profile
    Headers: Authorization: Bearer <jwt_token>
    """
    try:
        user_id = request.get("user_id")
        if not user_id:
            return web.json_response({"error": "Authentication required"}, status=401)

        # Call data service
        data_service_url = request.app["data_service_url"]
        result = await _call_data_service(
            f"{data_service_url}/data/profiles/{user_id}", "GET", request=request
        )

        # Record metrics
        record_profile_created(service="profile-service")

        # Log audit
        audit_log(
            service="profile-service",
            operation="get_current_profile",
            user_id=str(user_id),
            request=request,
        )

        return web.json_response(result)

    except ExternalServiceError as e:
        logger.error(f"Data service error in get_current_profile: {e}")
        return web.json_response({"error": "Profile not found"}, status=404)
    except Exception as e:
        logger.error(f"Unexpected error in get_current_profile: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def update_current_profile(request: web.Request) -> web.Response:
    """Update current user's profile (JWT-based).

    PUT /profile
    Headers: Authorization: Bearer <jwt_token>
    Body: { profile data }
    """
    try:
        user_id = request.get("user_id")
        if not user_id:
            return web.json_response({"error": "Authentication required"}, status=401)

        data = await request.json()

        # Validate profile data
        if not validate_profile_data(data):
            return web.json_response({"error": "Invalid profile data"}, status=400)

        # Call data service
        data_service_url = request.app["data_service_url"]
        result = await _call_data_service(
            f"{data_service_url}/data/profiles/{user_id}", "PUT", data, request
        )

        # Record metrics
        record_profile_updated(service="profile-service")

        # Log audit
        audit_log(
            service="profile-service",
            operation="update_current_profile",
            user_id=str(user_id),
            details={"fields_updated": list(data.keys())},
            request=request,
        )

        # Auto-queue for moderation
        try:
            await queue_for_moderation(
                content_type="profile",
                content_id=str(user_id),
                user_id=str(user_id),
                reason="profile_update",
                priority=1,
            )
            logger.info(f"Profile {user_id} queued for moderation")
        except Exception as e:
            logger.error(f"Failed to queue profile for moderation: {e}")
            # Don't fail the profile update if moderation queueing fails

        return web.json_response(result)

    except ValidationError as e:
        logger.warning(f"Validation error in update_current_profile: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except ExternalServiceError as e:
        logger.error(f"Data service error in update_current_profile: {e}")
        return web.json_response({"error": "Profile update failed"}, status=500)
    except Exception as e:
        logger.error(f"Unexpected error in update_current_profile: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def update_profile_progress(request: web.Request) -> web.Response:
    """Partial update of profile during onboarding.

    PATCH /profiles/progress
    """
    try:
        data = await request.json()
        user_id = request.get("user_id")

        if not user_id:
            return web.json_response({"error": "User ID required"}, status=400)

        # Validate required fields for progress update
        if not data.get("user_id"):
            return web.json_response({"error": "user_id required"}, status=400)

        data_service_url = request.app["data_service_url"]

        # Use circuit breaker + retry with correlation ID propagation
        result = await data_service_breaker.call(
            _call_data_service,
            f"{data_service_url}/data/profiles/progress",
            "PATCH",
            data,
            request,  # Pass request for correlation ID
            fallback=lambda *args: {"error": "Service temporarily unavailable"},
        )

        if "error" in result:
            if result["error"] == "Service temporarily unavailable":
                raise CircuitBreakerError("data-service")
            raise ExternalServiceError(
                service="data-service",
                message=result.get("error", "Unknown error"),
                details=result,
            )

        # Record business metrics
        record_profile_updated("profile-service")

        # Audit log profile progress update
        audit_log(
            operation="profile_progress_update",
            user_id=str(user_id),
            service="profile-service",
            details={
                "current_step": data.get("current_step"),
                "fields_updated": list(data.keys()),
            },
            request=request,
        )

        return web.json_response(
            {"status": "success", "current_step": data.get("current_step")}
        )

    except Exception as e:
        logger.error(f"Error updating profile progress: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def sync_metrics(request: web.Request) -> web.Response:
    """Sync business metrics with database data."""
    try:
        data_service_url = request.app["data_service_url"]

        # Use circuit breaker + retry
        result = await data_service_breaker.call(
            _call_data_service,
            f"{data_service_url}/data/profiles-count",
            fallback=lambda *args: {"count": 0},
        )

        total_users = result.get("count", 0)

        # Set the metric to the current count
        update_users_total(service="profile-service", count=total_users)

        return web.json_response(
            {
                "status": "success",
                "users_total": total_users,
                "message": "Metrics synchronized",
            }
        )

    except Exception as e:
        logger.error(f"Error syncing metrics: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def get_notification_preferences_handler(request: web.Request) -> web.Response:
    """Get user's notification preferences.

    GET /settings/notifications/preferences
    """
    try:
        user_id = request.get("user_id")
        if not user_id:
            return web.json_response({"error": "Authentication required"}, status=401)

        # Call data service
        data_service_url = request.app["data_service_url"]
        result = await _call_data_service(
            f"{data_service_url}/data/notification-preferences/{user_id}",
            "GET",
            None,
            None,
            request,
        )

        return web.json_response(result)

    except ValidationError as e:
        logger.warning(f"Validation error in get_notification_preferences: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except ExternalServiceError as e:
        logger.error(f"Data service error in get_notification_preferences: {e}")
        return web.json_response(
            {"error": "Failed to get notification preferences"}, status=500
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_notification_preferences: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def update_notification_preferences_handler(request: web.Request) -> web.Response:
    """Update user's notification preferences.

    PUT /settings/notifications/preferences
    Body: { notification preferences }
    """
    try:
        user_id = request.get("user_id")
        if not user_id:
            return web.json_response({"error": "Authentication required"}, status=401)

        data = await request.json()

        # Validate notification preferences data
        if not validate_notification_preferences_data(data):
            return web.json_response(
                {"error": "Invalid notification preferences data"}, status=400
            )

        # Call data service
        data_service_url = request.app["data_service_url"]
        result = await _call_data_service(
            f"{data_service_url}/data/notification-preferences/{user_id}",
            "PUT",
            data,
            None,
            request,
        )

        # Record metrics
        record_profile_updated(service="profile-service")

        # Log audit
        audit_log(
            service="profile-service",
            operation="update_notification_preferences",
            user_id=str(user_id),
            details={"preferences_updated": list(data.keys())},
            request=request,
        )

        return web.json_response(result)

    except ValidationError as e:
        logger.warning(f"Validation error in update_notification_preferences: {e}")
        return web.json_response({"error": str(e)}, status=400)
    except ExternalServiceError as e:
        logger.error(f"Data service error in update_notification_preferences: {e}")
        return web.json_response(
            {"error": "Failed to update notification preferences"}, status=500
        )
    except Exception as e:
        logger.error(f"Unexpected error in update_notification_preferences: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


def validate_notification_preferences_data(data: dict) -> bool:
    """Validate notification preferences data."""
    valid_boolean_fields = [
        "push_enabled",
        "email_enabled",
        "telegram_enabled",
        "new_matches",
        "new_messages",
        "super_likes",
        "likes",
        "profile_views",
        "verification_updates",
        "marketing",
        "reminders",
    ]

    valid_time_fields = ["quiet_hours_start", "quiet_hours_end"]
    valid_string_fields = ["timezone"]

    # Check boolean fields
    for field in valid_boolean_fields:
        if field in data and not isinstance(data[field], bool):
            return False

    # Check time fields
    for field in valid_time_fields:
        if field in data and data[field] is not None:
            if not isinstance(data[field], str):
                return False
            # Basic time format validation (HH:MM)
            try:
                from datetime import datetime

                datetime.strptime(data[field], "%H:%M")
            except ValueError:
                return False

    # Check string fields
    for field in valid_string_fields:
        if field in data and not isinstance(data[field], str):
            return False

    return True


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

        # Direct call without circuit breaker for now
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{data_service_url}/data/profiles-count") as resp:
                if resp.status == 200:
                    result = await resp.json()
                    total_users = result.get("count", 0)

                    # Set the metric to the current count
                    update_users_total("profile-service", total_users)

                    logger.info(
                        f"Metrics synchronized on startup: users_total={total_users}"
                    )
                else:
                    logger.warning(f"Failed to get profiles count: {resp.status}")
                    update_users_total("profile-service", 0)

    except Exception as e:
        logger.error(f"Error syncing metrics on startup: {e}")
        # Set to 0 as fallback
        update_users_total("profile-service", 0)


def create_app(config: dict) -> web.Application:
    """Create and configure the profile service application."""
    app = web.Application()
    app["config"] = config

    # Store Data Service URL
    app["data_service_url"] = config["data_service_url"]

    # Setup error handling
    setup_error_handling(app, "profile-service")

    # Business metrics are imported from middleware

    # Setup standard middleware stack
    setup_standard_middleware_stack(
        app, "profile-service", use_auth=True, use_audit=True
    )

    # Add metrics endpoint
    add_metrics_route(app, "profile-service")

    # Add routes
    app.router.add_get("/profiles/{user_id}", get_profile)
    app.router.add_get("/profile", get_current_profile)  # JWT-based, no user_id in path
    app.router.add_put("/profile", update_current_profile)  # JWT-based profile update
    app.router.add_post("/profiles", create_profile)
    app.router.add_patch("/profiles/progress", update_profile_progress)

    # Settings endpoints
    from .settings import (
        get_notification_settings,
        get_user_preferences,
        update_notification_settings,
        update_user_preferences,
    )

    app.router.add_get("/settings/preferences", get_user_preferences)
    app.router.add_put("/settings/preferences", update_user_preferences)
    app.router.add_get("/settings/notifications", get_notification_settings)
    app.router.add_put("/settings/notifications", update_notification_settings)
    app.router.add_get(
        "/settings/notifications/preferences", get_notification_preferences_handler
    )
    app.router.add_put(
        "/settings/notifications/preferences", update_notification_preferences_handler
    )

    # Verification endpoints
    from .verification import request_verification

    app.router.add_post("/profile/verification/request", request_verification)
    app.router.add_get("/health", health_check)
    app.router.add_post("/sync-metrics", sync_metrics)

    # Sync metrics on startup and start background task
    app.on_startup.append(sync_metrics_on_startup)
    # Temporarily disabled background task to debug HTTP server issue
    # app.on_startup.append(lambda app: asyncio.create_task(sync_metrics_periodically()))

    return app


if __name__ == "__main__":
    import os

    # Configure structured logging
    configure_logging("profile-service", os.getenv("LOG_LEVEL", "INFO"))

    config = {
        "jwt_secret": os.getenv("JWT_SECRET"),  # SECURITY: No default value
        "data_service_url": os.getenv("data_service_url", "http://data-service:8088"),
        "host": os.getenv("PROFILE_SERVICE_HOST", "0.0.0.0"),
        "port": int(os.getenv("PROFILE_SERVICE_PORT", 8082)),
    }

    logger.info(
        "Starting profile-service",
        extra={"event_type": "service_start", "port": config["port"]},
    )

    app = create_app(config)
    web.run_app(app, host=str(config["host"]), port=int(str(config["port"])))
