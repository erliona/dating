from __future__ import annotations

"""Auth service main entry point.

This microservice handles authentication and JWT token management,
independent of any specific platform.
"""

import logging

from aiohttp import web

from core.utils.logging import configure_logging
from core.middleware.metrics_middleware import metrics_middleware, add_metrics_route
from core.middleware.rate_limiting import auth_rate_limiting_middleware
from core.utils.security import (
    RateLimiter,
    ValidationError,
    generate_jwt_token,
    generate_token_pair,
    validate_jwt_token,
    validate_telegram_webapp_init_data,
)
from core.middleware.security_metrics import (
    record_auth_attempt,
    record_auth_failure,
    record_security_event
)
from core.middleware.audit_logging import audit_log, log_security_event
from core.metrics.business_metrics import (
    JWT_TOKENS_CREATED,
    JWT_TOKENS_VALIDATED,
    JWT_TOKENS_EXPIRED,
    TELEGRAM_AUTH_SUCCESS,
    TELEGRAM_AUTH_FAILED,
    JWT_VALIDATION_FAILED
)

logger = logging.getLogger(__name__)


async def validate_telegram_init_data(request: web.Request) -> web.Response:
    """Validate Telegram WebApp initData and generate JWT token.

    POST /auth/validate
    Body: {
        "init_data": "telegram_init_data_string",
        "bot_token": "bot_token"
    }
    """
    try:
        data = await request.json()
        init_data = data.get("init_data")
        bot_token = data.get("bot_token")

        if not init_data or not bot_token:
            return web.json_response(
                {"error": "Missing init_data or bot_token"}, status=400
            )

        # Validate initData
        user_data = validate_telegram_webapp_init_data(init_data, bot_token)

        # Generate JWT token pair (access + refresh)
        user_id = user_data.get("user", {}).get("id")
        jwt_secret = request.app["config"].get("jwt_secret")
        tokens = generate_token_pair(user_id, jwt_secret)

        # Record successful authentication
        record_auth_attempt(
            service="auth-service",
            result="success",
            method="telegram_webapp",
            user_id=str(user_id)
        )
        
        # Record JWT token creation
        JWT_TOKENS_CREATED.labels(
            service='auth-service',
            token_type='access'
        ).inc()
        
        JWT_TOKENS_CREATED.labels(
            service='auth-service',
            token_type='refresh'
        ).inc()
        
        # Record Telegram auth success
        TELEGRAM_AUTH_SUCCESS.labels(
            service='auth-service'
        ).inc()
        
        record_security_event(
            event_type="user_login",
            service="auth-service",
            severity="info",
            user_id=str(user_id),
            method="telegram_webapp"
        )
        
        # Audit log successful login
        audit_log(
            operation="user_login",
            user_id=str(user_id),
            service="auth-service",
            details={
                "method": "telegram_webapp",
                "username": user_data.get("user", {}).get("username"),
                "user_data": {
                    "id": user_data.get("user", {}).get("id"),
                    "first_name": user_data.get("user", {}).get("first_name"),
                    "last_name": user_data.get("user", {}).get("last_name"),
                }
            },
            request=request
        )

        return web.json_response(
            {
                "access_token": tokens["access_token"],
                "refresh_token": tokens["refresh_token"],
                "user_id": user_id,
                "username": user_data.get("user", {}).get("username"),
                "expires_in": 3600,  # 1 hour in seconds
            }
        )

    except ValidationError as e:
        logger.warning(f"Validation failed: {e}")
        
        # Record failed authentication
        record_auth_attempt(
            service="auth-service",
            result="failure",
            method="telegram_webapp",
            reason=str(e)
        )
        
        # Record Telegram auth failure
        TELEGRAM_AUTH_FAILED.labels(
            service='auth-service',
            reason=str(e.code) if hasattr(e, 'code') else 'validation_error'
        ).inc()
        
        record_auth_failure(
            service="auth-service",
            reason="validation_failed",
            user_id="unknown",
            error=str(e)
        )
        
        # Audit log failed authentication attempt
        log_security_event(
            event_type="authentication_failure",
            user_id="unknown",
            service="auth-service",
            severity="WARNING",
            details={
                "method": "telegram_webapp",
                "error": str(e),
                "reason": "validation_failed"
            },
            request=request
        )
        
        return web.json_response({"error": str(e)}, status=401)

    except Exception as e:
        logger.error(f"Error validating init_data: {e}")
        
        # Record authentication error
        record_auth_attempt(
            service="auth-service",
            result="error",
            method="telegram_webapp",
            reason="internal_error"
        )
        
        return web.json_response({"error": "Internal server error"}, status=500)


async def verify_token(request: web.Request) -> web.Response:
    """Verify JWT token.

    GET /auth/verify
    Header: Authorization: Bearer <token>
    """
    try:
        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return web.json_response(
                {"error": "Missing or invalid Authorization header"}, status=401
            )

        token = auth_header.split(" ")[1]
        jwt_secret = request.app["config"].get("jwt_secret")

        payload = validate_jwt_token(token, jwt_secret)

        return web.json_response({"valid": True, "user_id": payload.get("user_id")})

    except ValidationError as e:
        logger.warning(f"Token validation failed: {e}")
        return web.json_response({"error": str(e)}, status=401)

    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


async def refresh_token(request: web.Request) -> web.Response:
    """Refresh JWT access token using refresh token.

    POST /auth/refresh
    Body: {"refresh_token": "refresh_token_string"}
    """
    try:
        data = await request.json()
        refresh_token_str = data.get("refresh_token")

        if not refresh_token_str:
            return web.json_response(
                {"error": "refresh_token is required"}, status=400
            )

        jwt_secret = request.app["config"].get("jwt_secret")

        # Verify refresh token
        payload = validate_jwt_token(refresh_token_str, jwt_secret, "refresh")

        # Generate new access token
        user_id = payload.get("user_id")
        new_access_token = generate_jwt_token(user_id, jwt_secret, token_type="access")

        # Audit log token refresh
        audit_log(
            operation="token_refresh",
            user_id=str(user_id),
            service="auth-service",
            details={
                "token_type": "refresh_to_access",
                "expires_in": 3600
            },
            request=request
        )

        return web.json_response({
            "access_token": new_access_token,
            "user_id": user_id,
            "expires_in": 3600,  # 1 hour in seconds
        })

    except ValidationError as e:
        logger.warning(f"Token refresh failed: {e}")
        return web.json_response({"error": str(e)}, status=401)

    except Exception as e:
        logger.error(f"Error refreshing token: {e}")
        return web.json_response({"error": "Internal server error"}, status=500)


# SECURITY: Test endpoint removed for production security
# This endpoint was a critical security vulnerability allowing anyone
# to generate valid JWT tokens for any user_id without authentication


async def health_check(request: web.Request) -> web.Response:
    """Health check endpoint."""
    return web.json_response({"status": "healthy", "service": "auth"})


def create_app(config: dict) -> web.Application:
    """Create and configure the auth service application."""
    app = web.Application()
    app["config"] = config

    # Add middleware
    # Setup auth service middleware stack (no JWT middleware needed)
    from core.middleware.standard_stack import setup_auth_service_middleware_stack
    setup_auth_service_middleware_stack(app, "auth-service")
    
    # Add rate limiting for auth endpoints
    app.middlewares.append(auth_rate_limiting_middleware)

    # Add routes
    app.router.add_post("/auth/validate", validate_telegram_init_data)
    app.router.add_get("/auth/verify", verify_token)
    app.router.add_post("/auth/refresh", refresh_token)
    # SECURITY: Removed /auth/test endpoint - was a critical vulnerability
    app.router.add_get("/health", health_check)
    
    # Add metrics endpoint
    add_metrics_route(app, "auth-service")

    return app


if __name__ == "__main__":
    import os

    # Configure structured logging
    configure_logging("auth-service", os.getenv("LOG_LEVEL", "INFO"))

    # SECURITY: JWT_SECRET is required - no default value for security
    jwt_secret = os.getenv("JWT_SECRET")
    if not jwt_secret:
        logger.error("JWT_SECRET environment variable is required for security")
        raise RuntimeError(
            "JWT_SECRET environment variable is required. "
            "Generate a strong secret with: python -c \"import secrets; print(secrets.token_urlsafe(32))\""
        )
    
    config = {
        "jwt_secret": jwt_secret,
        "host": os.getenv("AUTH_SERVICE_HOST", "0.0.0.0"),
        "port": int(os.getenv("AUTH_SERVICE_PORT", 8081)),
    }

    logger.info(
        "Starting auth-service",
        extra={"event_type": "service_start", "port": config["port"]},
    )

    app = create_app(config)
    web.run_app(app, host=config["host"], port=config["port"])
