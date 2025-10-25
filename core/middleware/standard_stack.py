"""Standard middleware stack configuration for all microservices."""

from __future__ import annotations

from aiohttp import web

from core.middleware.audit_logging import audit_logging_middleware
from core.middleware.correlation import correlation_middleware
from core.middleware.error_handling import error_handling_middleware
from core.middleware.jwt_middleware import admin_jwt_middleware, jwt_middleware
from core.middleware.metrics_middleware import metrics_middleware
from core.middleware.request_logging import (
    request_logging_middleware,
    user_context_middleware,
)
from core.middleware.service_rate_limiters import service_rate_limiting_middleware
from core.middleware.tracing import tracing_middleware


def setup_standard_middleware_stack(
    app: web.Application,
    service_name: str,
    use_auth: bool = True,
    use_audit: bool = True,
) -> None:
    """
    Setup the standard middleware stack for a microservice.

    Args:
        app: aiohttp Application instance
        service_name: Name of the service (for metrics and logging)
        use_auth: Whether to include JWT authentication middleware
        use_audit: Whether to include audit logging middleware
    """
    # Set service name for metrics and logging
    app["service_name"] = service_name

    # Standard middleware order (order matters!):

    # 1. Error handler - must be first to catch all exceptions
    app.middlewares.append(error_handling_middleware)

    # 2. Distributed tracing - extract/generate trace context
    app.middlewares.append(tracing_middleware)

    # 3. Correlation ID - generate/forward correlation IDs
    app.middlewares.append(correlation_middleware)

    # 4. User context - extract user information from JWT
    app.middlewares.append(user_context_middleware)

    # 5. Request logging - log all requests with context
    app.middlewares.append(request_logging_middleware)

    # 6. Rate limiting - protect against abuse
    app.middlewares.append(service_rate_limiting_middleware)

    # 7. Metrics collection - collect HTTP metrics
    app.middlewares.append(metrics_middleware)

    # 8. Audit logging - log critical operations (optional)
    if use_audit:
        app.middlewares.append(audit_logging_middleware)

    # 9. JWT authentication - validate tokens (optional, must be last)
    if use_auth:
        app.middlewares.append(jwt_middleware)


def setup_admin_middleware_stack(app: web.Application, service_name: str) -> None:
    """
    Setup middleware stack for admin services with admin JWT middleware.

    Args:
        app: aiohttp Application instance
        service_name: Name of the service
    """
    # Set service name
    app["service_name"] = service_name

    # Admin middleware order:

    # 1. Error handler
    app.middlewares.append(error_handling_middleware)

    # 2. Distributed tracing
    app.middlewares.append(tracing_middleware)

    # 3. Correlation ID
    app.middlewares.append(correlation_middleware)

    # 4. User context
    app.middlewares.append(user_context_middleware)

    # 5. Request logging
    app.middlewares.append(request_logging_middleware)

    # 6. Metrics collection
    app.middlewares.append(metrics_middleware)

    # 7. Audit logging
    app.middlewares.append(audit_logging_middleware)

    # 8. Admin JWT authentication
    app.middlewares.append(admin_jwt_middleware)


def setup_auth_service_middleware_stack(
    app: web.Application, service_name: str
) -> None:
    """
    Setup middleware stack for auth service (no JWT middleware needed).

    Args:
        app: aiohttp Application instance
        service_name: Name of the service
    """
    # Set service name
    app["service_name"] = service_name

    # Auth service middleware order (no JWT middleware):

    # 1. Error handler
    app.middlewares.append(error_handling_middleware)

    # 2. Distributed tracing
    app.middlewares.append(tracing_middleware)

    # 3. Correlation ID
    app.middlewares.append(correlation_middleware)

    # 4. User context (may not have user info for auth endpoints)
    app.middlewares.append(user_context_middleware)

    # 5. Request logging
    app.middlewares.append(request_logging_middleware)

    # 6. Metrics collection
    app.middlewares.append(metrics_middleware)

    # 7. Audit logging (important for auth events)
    app.middlewares.append(audit_logging_middleware)
