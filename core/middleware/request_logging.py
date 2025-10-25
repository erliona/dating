from __future__ import annotations

"""Request logging middleware for tracing and performance monitoring."""

import logging
import time
import uuid
from collections.abc import Callable

from aiohttp import web

logger = logging.getLogger(__name__)


@web.middleware
async def request_logging_middleware(
    request: web.Request, handler: Callable
) -> web.Response:
    """
    Middleware for request logging and tracing.

    Adds request_id, logs request/response, measures performance.
    """
    # Generate unique request ID
    request_id = str(uuid.uuid4())[:8]
    request["request_id"] = request_id

    # Start timing
    start_time = time.time()

    # Get correlation_id from request (set by correlation_middleware)
    correlation_id = request.get("correlation_id", "")

    # Log request
    logger.info(
        f"Request started: {request.method} {request.path}",
        extra={
            "event_type": "request_started",
            "request_id": request_id,
            "correlation_id": correlation_id,
            "method": request.method,
            "path": request.path,
            "user_agent": request.headers.get("User-Agent", ""),
            "remote_addr": request.remote,
            "service": request.app.get("service_name", "unknown"),
        },
    )

    try:
        # Process request
        response = await handler(request)

        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)

        # Log successful response
        logger.info(
            f"Request completed: {request.method} {request.path} -> {response.status}",
            extra={
                "event_type": "request_completed",
                "request_id": request_id,
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.path,
                "status_code": response.status,
                "duration_ms": duration_ms,
                "user_id": request.get("user_id"),
                "service": request.app.get("service_name", "unknown"),
            },
        )

        # Add request_id and correlation_id to response headers
        response.headers["X-Request-ID"] = request_id
        if correlation_id:
            response.headers["X-Correlation-ID"] = correlation_id

        return response

    except Exception as e:
        # Calculate duration for failed requests
        duration_ms = int((time.time() - start_time) * 1000)

        # Log error
        logger.error(
            f"Request failed: {request.method} {request.path} -> {type(e).__name__}: {e}",
            exc_info=True,
            extra={
                "event_type": "request_failed",
                "request_id": request_id,
                "correlation_id": correlation_id,
                "method": request.method,
                "path": request.path,
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
                "error_message": str(e),
                "user_id": request.get("user_id"),
                "service": request.app.get("service_name", "unknown"),
            },
        )

        # Re-raise the exception
        raise


@web.middleware
async def user_context_middleware(
    request: web.Request, handler: Callable
) -> web.Response:
    """
    Middleware to add user context to logs.

    Extracts user_id from JWT token and adds to request context.
    """
    # Try to extract user_id from JWT token
    user_id = None
    auth_header = request.headers.get("Authorization")

    if auth_header and auth_header.startswith("Bearer "):
        try:
            # Import here to avoid circular imports
            import os

            from core.utils.security import validate_jwt_token

            token = auth_header.split(" ")[1]
            jwt_secret = os.getenv("JWT_SECRET")

            if jwt_secret:
                payload = validate_jwt_token(token, jwt_secret)
                user_id = payload.get("user_id")
                request["user_id"] = user_id

        except Exception:
            # JWT validation failed, but that's handled by jwt_middleware
            pass

    # Add user context to request
    request["user_id"] = user_id

    # Process request
    response = await handler(request)

    return response
