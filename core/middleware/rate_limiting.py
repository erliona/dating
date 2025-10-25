from __future__ import annotations

"""Rate limiting middleware for protecting endpoints from abuse."""

import logging

from aiohttp import web

from core.middleware.security_metrics import record_rate_limit_hit
from core.utils.security import RateLimiter

logger = logging.getLogger(__name__)

# Global rate limiter instance
_rate_limiter = RateLimiter(
    max_requests=10, window_seconds=60
)  # 10 requests per minute


@web.middleware
async def rate_limiting_middleware(request: web.Request, handler) -> web.Response:
    """
    Rate limiting middleware.

    Limits requests per user to prevent abuse and brute force attacks.
    """

    # Skip rate limiting for health checks and metrics
    if request.path.startswith("/health") or request.path.startswith("/metrics"):
        return await handler(request)

    # Get user identifier for rate limiting
    user_id = None

    # Try to get user_id from JWT payload if available
    if "jwt_payload" in request:
        user_id = request["jwt_payload"].get("user_id")

    # For auth endpoints, use IP address as fallback
    if not user_id:
        # Get client IP from headers (considering proxies)
        user_id = (
            request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
            or request.headers.get("X-Real-IP", "")
            or request.remote
            or "unknown"
        )
        # Convert IP to integer for consistent hashing
        try:
            user_id = hash(user_id) % (2**31)  # Convert to 32-bit integer
        except Exception:
            user_id = 0

    # Check rate limit
    if not _rate_limiter.is_allowed(user_id):
        logger.warning(
            f"Rate limit exceeded for user {user_id} on {request.path}",
            extra={
                "event_type": "rate_limit_exceeded",
                "user_id": user_id,
                "path": request.path,
                "ip": request.remote,
            },
        )

        # Record rate limit hit
        record_rate_limit_hit(
            service=request.app.get("service_name", "unknown"),
            endpoint=request.path,
            user_id=str(user_id),
            method=request.method,
        )

        return web.json_response(
            {
                "error": "Rate limit exceeded. Please try again later.",
                "retry_after": 60,
            },
            status=429,
            headers={"Retry-After": "60"},
        )

    return await handler(request)


@web.middleware
async def auth_rate_limiting_middleware(request: web.Request, handler) -> web.Response:
    """
    Stricter rate limiting for authentication endpoints.

    More restrictive limits for auth endpoints to prevent brute force attacks.
    """

    # Only apply to auth endpoints
    if not request.path.startswith("/auth/"):
        return await handler(request)

    # Skip health checks
    if request.path.startswith("/auth/health"):
        return await handler(request)

    # Use IP address for auth rate limiting
    client_ip = (
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or request.headers.get("X-Real-IP", "")
        or request.remote
        or "unknown"
    )

    # Convert IP to integer for consistent hashing
    try:
        user_id = hash(client_ip) % (2**31)
    except Exception:
        user_id = 0

    # Stricter rate limiting for auth endpoints: 5 requests per 5 minutes
    auth_limiter = RateLimiter(max_requests=5, window_seconds=300)

    if not auth_limiter.is_allowed(user_id):
        logger.warning(
            f"Auth rate limit exceeded for IP {client_ip} on {request.path}",
            extra={
                "event_type": "auth_rate_limit_exceeded",
                "ip": client_ip,
                "path": request.path,
                "user_agent": request.headers.get("User-Agent", "unknown"),
            },
        )
        return web.json_response(
            {
                "error": "Too many authentication attempts. Please try again later.",
                "retry_after": 300,
            },
            status=429,
            headers={"Retry-After": "300"},
        )

    return await handler(request)
