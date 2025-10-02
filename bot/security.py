"""Security module for Telegram WebApp data validation and JWT management.

Epic A2: Server-side validation of initData + JWT
"""

import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any, Optional
from urllib.parse import parse_qsl, unquote

import jwt

logger = logging.getLogger(__name__)

# JWT Configuration
JWT_ALGORITHM = "HS256"
JWT_TTL_HOURS = 24  # JWT expires after 24 hours


class ValidationError(Exception):
    """Raised when validation fails."""
    pass


def validate_webapp_init_data(
    init_data: str,
    bot_token: str,
    max_age_seconds: int = 3600
) -> dict[str, Any]:
    """Validate Telegram WebApp initData using HMAC-SHA256.
    
    This implements the validation algorithm from Telegram documentation:
    https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    
    Args:
        init_data: The initData string from Telegram WebApp
        bot_token: The bot token from BotFather
        max_age_seconds: Maximum age of the data in seconds (default: 1 hour)
    
    Returns:
        Dictionary containing parsed and validated data
    
    Raises:
        ValidationError: If validation fails for any reason
    
    Example:
        >>> data = validate_webapp_init_data(init_data, bot_token)
        >>> user_id = data['user']['id']
    """
    if not init_data:
        logger.warning("Empty initData received", extra={"event_type": "auth_failed"})
        raise ValidationError("initData is empty")
    
    if not bot_token:
        raise ValidationError("bot_token is required")
    
    # Parse the init data
    try:
        data_dict = dict(parse_qsl(init_data, keep_blank_values=True))
    except Exception as exc:
        logger.warning(
            "Failed to parse initData",
            exc_info=True,
            extra={"event_type": "auth_failed"}
        )
        raise ValidationError(f"Failed to parse initData: {exc}") from exc
    
    # Extract hash from the data
    received_hash = data_dict.pop('hash', None)
    if not received_hash:
        logger.warning(
            "Missing hash in initData",
            extra={"event_type": "auth_failed"}
        )
        raise ValidationError("Missing hash in initData")
    
    # Check auth_date
    auth_date_str = data_dict.get('auth_date')
    if not auth_date_str:
        logger.warning(
            "Missing auth_date in initData",
            extra={"event_type": "auth_failed"}
        )
        raise ValidationError("Missing auth_date in initData")
    
    try:
        auth_date = int(auth_date_str)
    except ValueError as exc:
        logger.warning(
            "Invalid auth_date format",
            extra={"event_type": "auth_failed", "auth_date": auth_date_str}
        )
        raise ValidationError("Invalid auth_date format") from exc
    
    # Check if data is not too old (TTL check)
    current_time = int(time.time())
    data_age = current_time - auth_date
    
    if data_age > max_age_seconds:
        logger.warning(
            "initData is too old",
            extra={
                "event_type": "auth_failed",
                "data_age_seconds": data_age,
                "max_age_seconds": max_age_seconds
            }
        )
        raise ValidationError(
            f"initData is too old (age: {data_age}s, max: {max_age_seconds}s)"
        )
    
    if data_age < 0:
        logger.warning(
            "auth_date is in the future",
            extra={"event_type": "auth_failed", "data_age_seconds": data_age}
        )
        raise ValidationError("auth_date is in the future")
    
    # Prepare data check string
    # Sort keys and create data_check_string
    data_check_pairs = [f"{k}={v}" for k, v in sorted(data_dict.items())]
    data_check_string = '\n'.join(data_check_pairs)
    
    # Calculate secret key: HMAC-SHA256 of bot token with constant string
    secret_key = hmac.new(
        key="WebAppData".encode(),
        msg=bot_token.encode(),
        digestmod=hashlib.sha256
    ).digest()
    
    # Calculate hash: HMAC-SHA256 of data_check_string with secret_key
    calculated_hash = hmac.new(
        key=secret_key,
        msg=data_check_string.encode(),
        digestmod=hashlib.sha256
    ).hexdigest()
    
    # Timing-safe comparison to prevent timing attacks
    if not hmac.compare_digest(calculated_hash, received_hash):
        logger.warning(
            "HMAC validation failed",
            extra={
                "event_type": "auth_failed",
                "reason": "hash_mismatch"
            }
        )
        raise ValidationError("HMAC validation failed")
    
    # Parse user data if present
    validated_data = data_dict.copy()
    
    if 'user' in validated_data:
        try:
            validated_data['user'] = json.loads(unquote(validated_data['user']))
        except (json.JSONDecodeError, ValueError) as exc:
            logger.warning(
                "Failed to parse user data",
                exc_info=True,
                extra={"event_type": "auth_warning"}
            )
            # Don't fail validation, just keep the raw string
    
    # Parse other JSON fields if present
    for field in ['receiver', 'chat', 'chat_type', 'chat_instance']:
        if field in validated_data:
            try:
                validated_data[field] = json.loads(unquote(validated_data[field]))
            except (json.JSONDecodeError, ValueError):
                # Keep raw value if parsing fails
                pass
    
    logger.info(
        "initData validated successfully",
        extra={
            "event_type": "auth_success",
            "user_id": validated_data.get('user', {}).get('id') if isinstance(
                validated_data.get('user'), dict
            ) else None,
            "data_age_seconds": data_age
        }
    )
    
    return validated_data


def generate_jwt_token(
    user_id: int,
    secret_key: str,
    additional_claims: Optional[dict[str, Any]] = None
) -> str:
    """Generate a JWT token for authenticated user.
    
    Args:
        user_id: Telegram user ID
        secret_key: Secret key for signing the JWT
        additional_claims: Optional additional claims to include in the token
    
    Returns:
        JWT token string
    
    Example:
        >>> token = generate_jwt_token(123456, "secret", {"role": "user"})
    """
    now = datetime.now(timezone.utc)
    expiration = now + timedelta(hours=JWT_TTL_HOURS)
    
    payload = {
        "user_id": user_id,
        "iat": int(now.timestamp()),  # Issued at
        "exp": int(expiration.timestamp()),  # Expiration time
        "nbf": int(now.timestamp()),  # Not before
    }
    
    # Add additional claims if provided
    if additional_claims:
        payload.update(additional_claims)
    
    token = jwt.encode(payload, secret_key, algorithm=JWT_ALGORITHM)
    
    logger.info(
        "JWT token generated",
        extra={
            "event_type": "jwt_generated",
            "user_id": user_id,
            "expires_at": expiration.isoformat(),
            "ttl_hours": JWT_TTL_HOURS
        }
    )
    
    return token


def validate_jwt_token(token: str, secret_key: str) -> dict[str, Any]:
    """Validate and decode a JWT token.
    
    Args:
        token: JWT token string
        secret_key: Secret key used for signing
    
    Returns:
        Decoded token payload
    
    Raises:
        ValidationError: If token is invalid or expired
    
    Example:
        >>> payload = validate_jwt_token(token, "secret")
        >>> user_id = payload["user_id"]
    """
    try:
        payload = jwt.decode(
            token,
            secret_key,
            algorithms=[JWT_ALGORITHM],
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_nbf": True,
                "verify_iat": True,
                "require": ["user_id", "iat", "exp"]
            }
        )
        
        logger.info(
            "JWT token validated",
            extra={
                "event_type": "jwt_validated",
                "user_id": payload.get("user_id")
            }
        )
        
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning(
            "JWT token expired",
            extra={"event_type": "jwt_validation_failed", "reason": "expired"}
        )
        raise ValidationError("Token has expired")
    
    except jwt.InvalidTokenError as exc:
        logger.warning(
            "Invalid JWT token",
            exc_info=True,
            extra={"event_type": "jwt_validation_failed", "reason": "invalid"}
        )
        raise ValidationError(f"Invalid token: {exc}") from exc


def refresh_session(
    init_data: str,
    bot_token: str,
    secret_key: str,
    max_age_seconds: int = 3600
) -> tuple[dict[str, Any], str]:
    """Refresh user session by validating initData and generating new JWT.
    
    This is called when the app is restarted or when the JWT has expired.
    
    Args:
        init_data: Fresh initData from Telegram WebApp
        bot_token: Bot token for HMAC validation
        secret_key: Secret key for JWT signing
        max_age_seconds: Maximum age of initData
    
    Returns:
        Tuple of (validated_data, jwt_token)
    
    Raises:
        ValidationError: If validation fails
    
    Example:
        >>> data, token = refresh_session(init_data, bot_token, secret_key)
    """
    # Validate initData
    validated_data = validate_webapp_init_data(init_data, bot_token, max_age_seconds)
    
    # Extract user ID
    user_data = validated_data.get('user', {})
    if isinstance(user_data, dict):
        user_id = user_data.get('id')
    else:
        raise ValidationError("Missing user data in initData")
    
    if not user_id:
        raise ValidationError("Missing user ID in initData")
    
    # Generate JWT token
    jwt_token = generate_jwt_token(
        user_id=user_id,
        secret_key=secret_key,
        additional_claims={
            "username": user_data.get("username"),
            "first_name": user_data.get("first_name"),
            "language_code": user_data.get("language_code")
        }
    )
    
    logger.info(
        "Session refreshed",
        extra={
            "event_type": "session_refreshed",
            "user_id": user_id
        }
    )
    
    return validated_data, jwt_token
