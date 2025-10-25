from __future__ import annotations

"""Unified error handler middleware for consistent error responses."""

import logging
from typing import Any

from aiohttp import web

from core.exceptions import ServiceError

logger = logging.getLogger(__name__)


@web.middleware
async def error_handler_middleware(request: web.Request, handler) -> web.Response:
    """
    Global error handler for consistent error responses.

    This middleware catches all exceptions and converts them to standardized
    JSON error responses with proper HTTP status codes.
    """
    try:
        return await handler(request)
    except ServiceError as e:
        # Log service errors with context
        logger.warning(
            f"Service error: {e.code}",
            extra={
                "error_code": e.code,
                "error_message": e.message,
                "status_code": e.status,
                "details": e.details,
                "request_id": request.get("request_id"),
                "correlation_id": request.get("correlation_id"),
                "user_id": request.get("user_id"),
                "path": request.path,
                "method": request.method,
                "service": request.app.get("service_name", "unknown"),
            },
        )

        return web.json_response(
            {"error": {"code": e.code, "message": e.message, "details": e.details}},
            status=e.status,
        )

    except web.HTTPException as e:
        # Handle aiohttp HTTP exceptions
        logger.warning(
            f"HTTP error: {e.status}",
            extra={
                "error_code": "HTTP_ERROR",
                "error_message": e.text,
                "status_code": e.status,
                "request_id": request.get("request_id"),
                "correlation_id": request.get("correlation_id"),
                "path": request.path,
                "method": request.method,
                "service": request.app.get("service_name", "unknown"),
            },
        )

        return web.json_response(
            {
                "error": {
                    "code": "HTTP_ERROR",
                    "message": e.text or "HTTP error occurred",
                }
            },
            status=e.status,
        )

    except Exception as e:
        # Log unexpected errors with full context
        logger.error(
            f"Unexpected error: {e}",
            exc_info=True,
            extra={
                "error_code": "INTERNAL_ERROR",
                "error_message": str(e),
                "error_type": type(e).__name__,
                "request_id": request.get("request_id"),
                "correlation_id": request.get("correlation_id"),
                "user_id": request.get("user_id"),
                "path": request.path,
                "method": request.method,
                "service": request.app.get("service_name", "unknown"),
            },
        )

        return web.json_response(
            {
                "error": {
                    "code": "INTERNAL_ERROR",
                    "message": "An unexpected error occurred",
                }
            },
            status=500,
        )


def create_error_response(
    code: str, message: str, status: int = 500, details: dict[str, Any] = None
) -> web.Response:
    """
    Helper function to create standardized error responses.

    Args:
        code: Error code
        message: Error message
        status: HTTP status code
        details: Additional error details

    Returns:
        aiohttp web.Response with error JSON
    """
    return web.json_response(
        {"error": {"code": code, "message": message, "details": details or {}}},
        status=status,
    )
