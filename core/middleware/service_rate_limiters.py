"""
Service-specific rate limiting configurations.

Different services have different rate limiting requirements based on their usage patterns.
"""

import logging

from aiohttp import web

from core.middleware.security_metrics import record_rate_limit_hit
from core.utils.security import RateLimiter

logger = logging.getLogger(__name__)

# Service-specific rate limiters
SERVICE_RATE_LIMITERS = {
    "auth-service": RateLimiter(max_requests=10, window_seconds=60),  # 10 req/min
    "profile-service": RateLimiter(max_requests=50, window_seconds=60),  # 50 req/min
    "discovery-service": RateLimiter(max_requests=50, window_seconds=60),  # 50 req/min
    "chat-service": RateLimiter(max_requests=50, window_seconds=60),  # 50 req/min
    "media-service": RateLimiter(max_requests=20, window_seconds=60),  # 20 req/min
    "admin-service": RateLimiter(max_requests=30, window_seconds=60),  # 30 req/min
    "notification-service": RateLimiter(
        max_requests=50, window_seconds=60
    ),  # 50 req/min
    "data-service": RateLimiter(
        max_requests=100, window_seconds=60
    ),  # 100 req/min (internal)
}

# Endpoint-specific rate limiters for sensitive operations
ENDPOINT_RATE_LIMITERS = {
    # Auth endpoints - stricter limits
    "/auth/validate": RateLimiter(max_requests=5, window_seconds=60),  # 5 req/min
    "/auth/refresh": RateLimiter(max_requests=10, window_seconds=60),  # 10 req/min
    # Media endpoints - file upload limits
    "/media/upload": RateLimiter(max_requests=5, window_seconds=60),  # 5 uploads/min
    "/media/upload/photo": RateLimiter(
        max_requests=3, window_seconds=60
    ),  # 3 photos/min
    # Discovery endpoints - swipe limits
    "/discovery/swipe": RateLimiter(
        max_requests=30, window_seconds=60
    ),  # 30 swipes/min
    # Chat endpoints - message limits
    "/chat/messages": RateLimiter(
        max_requests=20, window_seconds=60
    ),  # 20 messages/min
    "/chat/conversations/{id}/messages": RateLimiter(
        max_requests=20, window_seconds=60
    ),
    # Admin endpoints - moderation limits
    "/admin/moderation": RateLimiter(
        max_requests=10, window_seconds=60
    ),  # 10 actions/min
    # Report endpoints - abuse prevention
    "/reports": RateLimiter(max_requests=5, window_seconds=60),  # 5 reports/min
    "/discovery/report": RateLimiter(max_requests=5, window_seconds=60),
    "/chat/reports": RateLimiter(max_requests=5, window_seconds=60),
}


def get_rate_limiter_for_service(service_name: str) -> RateLimiter:
    """Get rate limiter for a specific service."""
    return SERVICE_RATE_LIMITERS.get(
        service_name, RateLimiter(max_requests=50, window_seconds=60)
    )


def get_rate_limiter_for_endpoint(endpoint: str) -> RateLimiter:
    """Get rate limiter for a specific endpoint."""
    # Try exact match first
    if endpoint in ENDPOINT_RATE_LIMITERS:
        return ENDPOINT_RATE_LIMITERS[endpoint]

    # Try pattern matching for parameterized endpoints
    for pattern, limiter in ENDPOINT_RATE_LIMITERS.items():
        if "{" in pattern and _matches_pattern(endpoint, pattern):
            return limiter

    return None  # type: ignore[return-value]


def _matches_pattern(endpoint: str, pattern: str) -> bool:
    """Check if endpoint matches a parameterized pattern."""
    # Simple pattern matching for {id} parameters
    import re

    pattern_regex = pattern.replace("{id}", r"[^/]+").replace("{user_id}", r"[^/]+")
    return bool(re.match(pattern_regex, endpoint))


@web.middleware
async def service_rate_limiting_middleware(
    request: web.Request, handler
) -> web.Response:
    """
    Service-specific rate limiting middleware.

    Applies different rate limits based on service and endpoint.
    """

    # Skip rate limiting for health checks and metrics
    if request.path.startswith("/health") or request.path.startswith("/metrics"):
        return await handler(request)

    # Get service name from app
    service_name = request.app.get("service_name", "unknown")

    # Get user identifier for rate limiting
    user_id = _get_user_identifier(request)

    # Check endpoint-specific rate limiting first
    endpoint_limiter = get_rate_limiter_for_endpoint(request.path)
    if endpoint_limiter:
        if not endpoint_limiter.is_allowed(user_id):
            logger.warning(
                f"Endpoint rate limit exceeded for {user_id} on {request.path}",
                extra={
                    "service": service_name,
                    "endpoint": request.path,
                    "user_id": user_id,
                    "rate_limit": f"{endpoint_limiter.max_requests}/{endpoint_limiter.window_seconds}s",
                },
            )
            record_rate_limit_hit(service_name, request.path, str(user_id))

            return web.json_response(
                {
                    "error": "RATE_001",
                    "message": f"Rate limit exceeded for {request.path}",
                    "code": "RATE_001",
                    "status_code": 429,
                    "timestamp": None,  # Will be set by error middleware
                    "retry_after": endpoint_limiter.window_seconds,
                },
                status=429,
                headers={"Retry-After": str(endpoint_limiter.window_seconds)},
            )

    # Check service-level rate limiting
    service_limiter = get_rate_limiter_for_service(service_name)
    if not service_limiter.is_allowed(user_id):
        logger.warning(
            f"Service rate limit exceeded for {user_id} on {service_name}",
            extra={
                "service": service_name,
                "endpoint": request.path,
                "user_id": user_id,
                "rate_limit": f"{service_limiter.max_requests}/{service_limiter.window_seconds}s",
            },
        )
        record_rate_limit_hit(service_name, request.path, str(user_id))

        return web.json_response(
            {
                "error": "RATE_001",
                "message": f"Rate limit exceeded for {service_name}",
                "code": "RATE_001",
                "status_code": 429,
                "timestamp": None,  # Will be set by error middleware
                "retry_after": service_limiter.window_seconds,
            },
            status=429,
            headers={"Retry-After": str(service_limiter.window_seconds)},
        )

    return await handler(request)


def _get_user_identifier(request: web.Request) -> int:
    """Get user identifier for rate limiting."""
    # Try to get user_id from JWT payload if available
    if "jwt_payload" in request:
        user_id = request["jwt_payload"].get("user_id")
        if user_id:
            return int(user_id)

    # For unauthenticated requests, use IP address
    client_ip = (
        request.headers.get("X-Forwarded-For", "").split(",")[0].strip()
        or request.headers.get("X-Real-IP", "")
        or request.remote
        or "unknown"
    )

    # Convert IP to integer for consistent hashing
    try:
        return hash(client_ip) % (2**31)  # Convert to 32-bit integer
    except Exception:
        return 0


# Specialized rate limiters for specific use cases
class AuthRateLimiter:
    """Specialized rate limiter for authentication endpoints."""

    def __init__(self):
        self.login_limiter = RateLimiter(
            max_requests=5, window_seconds=60
        )  # 5 login attempts/min
        self.refresh_limiter = RateLimiter(
            max_requests=10, window_seconds=60
        )  # 10 refresh/min
        self.validate_limiter = RateLimiter(
            max_requests=5, window_seconds=60
        )  # 5 validate/min

    def is_login_allowed(self, user_id: int) -> bool:
        return self.login_limiter.is_allowed(user_id)

    def is_refresh_allowed(self, user_id: int) -> bool:
        return self.refresh_limiter.is_allowed(user_id)

    def is_validate_allowed(self, user_id: int) -> bool:
        return self.validate_limiter.is_allowed(user_id)


class MediaRateLimiter:
    """Specialized rate limiter for media upload endpoints."""

    def __init__(self):
        self.upload_limiter = RateLimiter(
            max_requests=3, window_seconds=60
        )  # 3 uploads/min
        self.photo_limiter = RateLimiter(
            max_requests=2, window_seconds=60
        )  # 2 photos/min
        self.video_limiter = RateLimiter(
            max_requests=1, window_seconds=60
        )  # 1 video/min

    def is_upload_allowed(self, user_id: int) -> bool:
        return self.upload_limiter.is_allowed(user_id)

    def is_photo_allowed(self, user_id: int) -> bool:
        return self.photo_limiter.is_allowed(user_id)

    def is_video_allowed(self, user_id: int) -> bool:
        return self.video_limiter.is_allowed(user_id)


class DiscoveryRateLimiter:
    """Specialized rate limiter for discovery endpoints."""

    def __init__(self):
        self.swipe_limiter = RateLimiter(
            max_requests=30, window_seconds=60
        )  # 30 swipes/min
        self.super_like_limiter = RateLimiter(
            max_requests=5, window_seconds=60
        )  # 5 super likes/min
        self.undo_limiter = RateLimiter(
            max_requests=3, window_seconds=300
        )  # 3 undos/5min

    def is_swipe_allowed(self, user_id: int) -> bool:
        return self.swipe_limiter.is_allowed(user_id)

    def is_super_like_allowed(self, user_id: int) -> bool:
        return self.super_like_limiter.is_allowed(user_id)

    def is_undo_allowed(self, user_id: int) -> bool:
        return self.undo_limiter.is_allowed(user_id)


class ChatRateLimiter:
    """Specialized rate limiter for chat endpoints."""

    def __init__(self):
        self.message_limiter = RateLimiter(
            max_requests=20, window_seconds=60
        )  # 20 messages/min
        self.typing_limiter = RateLimiter(
            max_requests=10, window_seconds=60
        )  # 10 typing events/min
        self.read_limiter = RateLimiter(
            max_requests=50, window_seconds=60
        )  # 50 read updates/min

    def is_message_allowed(self, user_id: int) -> bool:
        return self.message_limiter.is_allowed(user_id)

    def is_typing_allowed(self, user_id: int) -> bool:
        return self.typing_limiter.is_allowed(user_id)

    def is_read_allowed(self, user_id: int) -> bool:
        return self.read_limiter.is_allowed(user_id)


# Global instances for use across services
auth_rate_limiter = AuthRateLimiter()
media_rate_limiter = MediaRateLimiter()
discovery_rate_limiter = DiscoveryRateLimiter()
chat_rate_limiter = ChatRateLimiter()
