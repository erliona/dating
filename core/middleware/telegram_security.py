"""Telegram security middleware for origin validation and bot token verification."""

import hmac
import logging
import os

from aiohttp import web

logger = logging.getLogger(__name__)


class TelegramSecurityError(Exception):
    """Telegram security validation error."""

    pass


def validate_telegram_origin(request: web.Request) -> bool:
    """
    Validate that request comes from Telegram WebApp.

    Checks:
    1. Origin header matches web.telegram.org
    2. Referer header matches web.telegram.org
    3. User-Agent contains TelegramBot

    Args:
        request: HTTP request object

    Returns:
        True if origin is valid, False otherwise
    """
    origin = request.headers.get("Origin", "")
    referer = request.headers.get("Referer", "")
    user_agent = request.headers.get("User-Agent", "")

    # Check Origin header
    if not origin.startswith("https://web.telegram.org"):
        logger.warning(f"Invalid Origin header: {origin}")
        return False

    # Check Referer header (optional but recommended)
    if referer and not referer.startswith("https://web.telegram.org"):
        logger.warning(f"Invalid Referer header: {referer}")
        return False

    # Check User-Agent (should contain TelegramBot)
    if "TelegramBot" not in user_agent:
        logger.warning(f"Invalid User-Agent: {user_agent}")
        return False

    return True


def validate_telegram_bot_secret(request: web.Request) -> bool:
    """
    Validate X-Telegram-Bot-Api-Secret-Token header.

    This header is sent by Telegram to verify the request authenticity.

    Args:
        request: HTTP request object

    Returns:
        True if secret token is valid, False otherwise
    """
    secret_token = request.headers.get("X-Telegram-Bot-Api-Secret-Token")
    expected_secret = os.getenv("TELEGRAM_BOT_SECRET_TOKEN")

    if not expected_secret:
        logger.error("TELEGRAM_BOT_SECRET_TOKEN not configured")
        return False

    if not secret_token:
        logger.warning("Missing X-Telegram-Bot-Api-Secret-Token header")
        return False

    # Use constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(secret_token, expected_secret):
        logger.warning("Invalid X-Telegram-Bot-Api-Secret-Token")
        return False

    return True


async def telegram_security_middleware(request: web.Request, handler):
    """
    Middleware to validate Telegram WebApp requests.

    Validates:
    1. Origin header (web.telegram.org)
    2. X-Telegram-Bot-Api-Secret-Token header
    3. Request path (only /auth/validate for Telegram auth)
    """
    # Skip validation for health checks and metrics
    if request.path in ["/health", "/metrics"]:
        return await handler(request)

    # Only apply to auth endpoints
    if not request.path.startswith("/auth/"):
        return await handler(request)

    try:
        # Validate origin
        if not validate_telegram_origin(request):
            logger.warning(
                f"Invalid Telegram origin: {request.remote} -> {request.path}",
                extra={
                    "event_type": "telegram_security_failure",
                    "remote_addr": request.remote,
                    "path": request.path,
                    "origin": request.headers.get("Origin"),
                    "referer": request.headers.get("Referer"),
                    "user_agent": request.headers.get("User-Agent"),
                },
            )
            return web.json_response(
                {"error": "Invalid origin", "code": "INVALID_ORIGIN"}, status=403
            )

        # Validate bot secret token
        if not validate_telegram_bot_secret(request):
            logger.warning(
                f"Invalid Telegram bot secret: {request.remote} -> {request.path}",
                extra={
                    "event_type": "telegram_security_failure",
                    "remote_addr": request.remote,
                    "path": request.path,
                    "secret_token_present": bool(
                        request.headers.get("X-Telegram-Bot-Api-Secret-Token")
                    ),
                },
            )
            return web.json_response(
                {"error": "Invalid bot secret", "code": "INVALID_BOT_SECRET"},
                status=403,
            )

        # Log successful validation
        logger.info(
            f"Telegram security validation passed: {request.remote} -> {request.path}",
            extra={
                "event_type": "telegram_security_success",
                "remote_addr": request.remote,
                "path": request.path,
            },
        )

        return await handler(request)

    except Exception as e:
        logger.error(
            f"Telegram security middleware error: {e}",
            extra={
                "event_type": "telegram_security_error",
                "error": str(e),
                "remote_addr": request.remote,
                "path": request.path,
            },
        )
        return web.json_response(
            {"error": "Security validation failed", "code": "SECURITY_ERROR"},
            status=500,
        )


def create_telegram_bot_secret() -> str:
    """
    Create a secure random secret token for Telegram bot.

    Returns:
        Base64-encoded random secret token
    """
    import secrets

    return secrets.token_urlsafe(32)


# Security metrics
TELEGRAM_ORIGIN_VALIDATIONS = 0
TELEGRAM_ORIGIN_FAILURES = 0
TELEGRAM_BOT_SECRET_VALIDATIONS = 0
TELEGRAM_BOT_SECRET_FAILURES = 0


def record_telegram_origin_validation(success: bool):
    """Record Telegram origin validation metrics."""
    global TELEGRAM_ORIGIN_VALIDATIONS, TELEGRAM_ORIGIN_FAILURES
    if success:
        TELEGRAM_ORIGIN_VALIDATIONS += 1
    else:
        TELEGRAM_ORIGIN_FAILURES += 1


def record_telegram_bot_secret_validation(success: bool):
    """Record Telegram bot secret validation metrics."""
    global TELEGRAM_BOT_SECRET_VALIDATIONS, TELEGRAM_BOT_SECRET_FAILURES
    if success:
        TELEGRAM_BOT_SECRET_VALIDATIONS += 1
    else:
        TELEGRAM_BOT_SECRET_FAILURES += 1
