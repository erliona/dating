"""
Standardized error handling middleware.

Provides consistent error responses across all microservices.
"""

import logging
from collections.abc import Callable
from typing import Any

from aiohttp import web
from aiohttp.web import Request, Response, middleware

from core.utils.errors import (
    DatingPlatformError,
    StandardError,
    get_error_response,
    handle_exception,
    log_error,
)

logger = logging.getLogger(__name__)


@middleware
async def error_handling_middleware(request: Request, handler: Callable) -> Response:
    """Standardized error handling middleware."""
    try:
        return await handler(request)
    except DatingPlatformError as e:
        # Handle known platform errors
        error = StandardError(
            error=e.error_code.value,
            message=e.message,
            code=e.error_code.value,
            status_code=e.status_code,
            timestamp=(
                str(e.timestamp) if hasattr(e, "timestamp") and e.timestamp else ""
            ),
            request_id=request.get("request_id"),
            details=e.details,
            retry_after=e.retry_after,
        )

        # Log the error
        log_error(
            error,
            service_name=request.app.get("service_name", "unknown"),
            request_id=request.get("request_id"),
            user_id=request.get("user_id"),
        )

        return web.json_response(
            get_error_response(error),
            status=e.status_code,
            headers=_get_error_headers(error),
        )

    except Exception as e:
        # Handle unexpected errors
        error = handle_exception(
            e,
            request_id=request.get("request_id"),
            service_name=request.app.get("service_name", "unknown"),
        )

        # Log the error
        log_error(
            error,
            service_name=request.app.get("service_name", "unknown"),
            request_id=request.get("request_id"),
            user_id=request.get("user_id"),
        )

        return web.json_response(
            get_error_response(error),
            status=error.status_code,
            headers=_get_error_headers(error),
        )


def _get_error_headers(error: StandardError) -> dict:
    """Get error-specific headers."""
    headers = {"Content-Type": "application/json"}

    if error.retry_after:
        headers["Retry-After"] = str(error.retry_after)

    return headers


def setup_error_handling(app: web.Application, service_name: str):
    """Setup error handling for the application."""
    app["service_name"] = service_name
    app.middlewares.append(error_handling_middleware)

    # Add global exception handler
    app.on_response_prepare.append(_log_response)  # type: ignore[arg-type]
    app.on_cleanup.append(_cleanup_handler)


async def _log_response(request: Request, response: Response):
    """Log response details."""
    if response.status >= 400:
        logger.warning(
            f"HTTP {response.status} response",
            extra={
                "method": request.method,
                "path": request.path,
                "status": response.status,
                "request_id": request.get("request_id"),
                "user_id": request.get("user_id"),
            },
        )


async def _cleanup_handler(app: web.Application):
    """Cleanup handler for the application."""
    logger.info(f"Cleaning up {app.get('service_name', 'unknown')} service")


# Error response helpers
def create_error_response(
    error_code: str,
    message: str,
    status_code: int = 400,
    details: dict = None,
    request_id: str = None,
) -> web.Response:
    """Create a standardized error response."""
    error_data = {
        "error": error_code,
        "message": message,
        "code": error_code,
        "status_code": status_code,
        "timestamp": None,  # Will be set by middleware
        "request_id": request_id,
    }

    if details:
        error_data["details"] = details

    return web.json_response(error_data, status=status_code)


def validation_error_response(
    message: str, field: str = None, value: Any = None, request_id: str = None
) -> web.Response:
    """Create a validation error response."""
    details = None
    if field:
        details = {"field": field}
        if value is not None:
            details["value"] = value

    return create_error_response("VAL_001", message, 422, details, request_id)


def authentication_error_response(
    message: str = "Authentication required", request_id: str = None
) -> web.Response:
    """Create an authentication error response."""
    return create_error_response("AUTH_001", message, 401, None, request_id)


def authorization_error_response(
    message: str = "Insufficient permissions", request_id: str = None
) -> web.Response:
    """Create an authorization error response."""
    return create_error_response("AUTH_004", message, 403, None, request_id)


def not_found_error_response(
    resource: str = "Resource", request_id: str = None
) -> web.Response:
    """Create a not found error response."""
    return create_error_response(
        "BIZ_001", f"{resource} not found", 404, None, request_id
    )


def rate_limit_error_response(
    message: str = "Rate limit exceeded", retry_after: int = 60, request_id: str = None
) -> web.Response:
    """Create a rate limit error response."""
    return create_error_response("RATE_001", message, 429, None, request_id)


def internal_error_response(
    message: str = "Internal server error", request_id: str = None
) -> web.Response:
    """Create an internal server error response."""
    return create_error_response("SYS_001", message, 500, None, request_id)
