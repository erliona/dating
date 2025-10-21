"""HTTP API server for photo uploads.

Provides endpoints for uploading photos with JWT authentication,
progress tracking, and image optimization.
"""

import asyncio
import hashlib
import json
import logging
from datetime import datetime, timedelta
from io import BytesIO
from typing import Optional

import jwt
from aiohttp import web
from aiohttp_cors import ResourceOptions
from aiohttp_cors import setup as cors_setup
from PIL import Image

from .config import BotConfig
from .media import (
    MAX_PHOTO_SIZE,
    MAX_PHOTOS_PER_USER,
    PhotoValidationError,
    detect_mime_type,
    validate_mime_type,
    validate_photo_size,
)
from .security import RateLimiter
from .validation import calculate_age

logger = logging.getLogger(__name__)

# Image optimization settings
MAX_IMAGE_DIMENSION = 1200  # Maximum width/height in pixels
JPEG_QUALITY = 85  # JPEG compression quality (0-100)
WEBP_QUALITY = 80  # WebP compression quality (0-100)


class AuthenticationError(Exception):
    """Raised when authentication fails."""

    pass


class RateLimitError(Exception):
    """Raised when rate limit is exceeded."""

    pass


def error_response(code: str, message: str, status: int = 400) -> web.Response:
    """Create standardized error response.

    Args:
        code: Error code (e.g., 'not_found', 'validation_error')
        message: Human-readable error message
        status: HTTP status code

    Returns:
        JSON response with standardized error format
    """
    return web.json_response({"error": {"code": code, "message": message}}, status=status)


def create_jwt_token(user_id: int, jwt_secret: str, expires_in: int = 3600) -> str:
    """Create JWT token for user authentication.

    Args:
        user_id: User ID
        jwt_secret: Secret key for signing
        expires_in: Token expiration time in seconds (default 1 hour)

    Returns:
        JWT token string
    """
    from datetime import timezone

    now = datetime.now(timezone.utc)
    payload = {
        "user_id": user_id,
        "exp": now + timedelta(seconds=expires_in),
        "iat": now,
    }
    return jwt.encode(payload, jwt_secret, algorithm="HS256")


def verify_jwt_token(token: str, jwt_secret: str) -> dict:
    """Verify and decode JWT token.

    Args:
        token: JWT token string
        jwt_secret: Secret key for verification

    Returns:
        Decoded payload dictionary

    Raises:
        AuthenticationError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, jwt_secret, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired")
    except jwt.InvalidTokenError as e:
        raise AuthenticationError(f"Invalid token: {str(e)}")


def optimize_image(image_bytes: bytes, format: str = "JPEG") -> bytes:
    """Optimize image by resizing and compressing.

    Args:
        image_bytes: Original image bytes
        format: Output format (JPEG, PNG, WEBP)

    Returns:
        Optimized image bytes
    """
    input_buffer = BytesIO(image_bytes)
    output = BytesIO()

    try:
        # Open image
        image = Image.open(input_buffer)

        # Convert RGBA to RGB for JPEG
        if format == "JPEG" and image.mode in ("RGBA", "LA", "P"):
            # Create white background
            background = Image.new("RGB", image.size, (255, 255, 255))
            if image.mode == "P":
                image = image.convert("RGBA")
            background.paste(image, mask=image.split()[-1] if image.mode == "RGBA" else None)
            image = background
        elif image.mode not in ("RGB", "L"):
            image = image.convert("RGB")

        # Resize if needed
        width, height = image.size
        if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
            # Calculate new size maintaining aspect ratio
            if width > height:
                new_width = MAX_IMAGE_DIMENSION
                new_height = int(height * (MAX_IMAGE_DIMENSION / width))
            else:
                new_height = MAX_IMAGE_DIMENSION
                new_width = int(width * (MAX_IMAGE_DIMENSION / height))

            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            logger.info(
                f"Resized image from {width}x{height} to {new_width}x{new_height}",
                extra={"event_type": "image_resized"},
            )

        # Save optimized image
        if format == "JPEG":
            image.save(output, format="JPEG", quality=JPEG_QUALITY, optimize=True)
        elif format == "WEBP":
            image.save(output, format="WEBP", quality=WEBP_QUALITY)
        elif format == "PNG":
            image.save(output, format="PNG", optimize=True)
        else:
            image.save(output, format=format)

        optimized_bytes = output.getvalue()

        original_size = len(image_bytes)
        optimized_size = len(optimized_bytes)
        reduction = (1 - optimized_size / original_size) * 100

        logger.info(
            f"Optimized image: {original_size} -> {optimized_size} bytes ({reduction:.1f}% reduction)",
            extra={"event_type": "image_optimized", "reduction_percent": reduction},
        )

        return optimized_bytes

    except Exception as e:
        logger.error(f"Image optimization failed: {e}", exc_info=True)
        # Return original if optimization fails
        return image_bytes

    finally:
        # Ensure BytesIO objects are properly closed
        input_buffer.close()
        output.close()


def calculate_nsfw_score(image_bytes: bytes, classifier=None) -> float:
    """Calculate NSFW score for image using NudeNet ML model.

    Uses NudeNet classifier to detect NSFW content.
    The model classifies images into categories and returns a safety score.

    Args:
        image_bytes: Image bytes
        classifier: Optional NudeClassifier instance (from app state)

    Returns:
        Safety score (0.0 = unsafe, 1.0 = safe)
    """
    # If no classifier provided, use fallback
    if classifier is None:
        logger.warning(
            "NudeNet not available, falling back to permissive mode",
            extra={"event_type": "nsfw_detection_fallback"},
        )
        return 1.0

    try:
        import io

        from PIL import Image

        # Convert bytes to PIL Image for NudeNet
        image = Image.open(io.BytesIO(image_bytes))

        # Save to temporary file (NudeNet requires file path)
        import tempfile

        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            image.save(tmp.name, format="JPEG")
            tmp_path = tmp.name

        try:
            # Classify image
            result = classifier.classify(tmp_path)

            # Result format: {image_path: {'safe': probability, 'unsafe': probability}}
            classification = result.get(tmp_path, {})

            # Get safe probability (higher is better)
            safe_prob = classification.get("safe", 0.5)
            unsafe_prob = classification.get("unsafe", 0.5)

            # Calculate safety score (0.0 = unsafe, 1.0 = safe)
            safety_score = (
                safe_prob / (safe_prob + unsafe_prob) if (safe_prob + unsafe_prob) > 0 else 0.5
            )

            logger.info(
                f"NSFW detection completed: safe={safe_prob:.3f}, unsafe={unsafe_prob:.3f}, score={safety_score:.3f}",
                extra={
                    "event_type": "nsfw_detection_complete",
                    "safe_probability": safe_prob,
                    "unsafe_probability": unsafe_prob,
                    "safety_score": safety_score,
                },
            )

            return safety_score

        finally:
            # Clean up temporary file
            import os

            try:
                os.unlink(tmp_path)
            except OSError:
                pass

    except Exception as e:
        logger.error(
            f"NSFW detection failed: {e}",
            exc_info=True,
            extra={"event_type": "nsfw_detection_error"},
        )
        # On error, be permissive
        return 1.0


async def authenticate_request(
    request: web.Request, jwt_secret: str, check_rate_limit: bool = True
) -> int:
    """Authenticate request and extract user ID.

    Args:
        request: aiohttp request
        jwt_secret: JWT secret key
        check_rate_limit: Whether to check rate limit (default: True)

    Returns:
        User ID

    Raises:
        AuthenticationError: If authentication fails
        RateLimitError: If rate limit exceeded
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        logger.warning(
            "Authentication failed: Missing Authorization header",
            extra={
                "event_type": "auth_failed",
                "reason": "missing_header",
                "ip": request.remote,
                "path": request.path,
            },
        )
        raise AuthenticationError("Missing Authorization header")

    # Ensure proper Bearer token format
    if not auth_header.startswith("Bearer "):
        logger.warning(
            "Authentication failed: Invalid Authorization header format",
            extra={
                "event_type": "auth_failed",
                "reason": "invalid_format",
                "ip": request.remote,
                "path": request.path,
            },
        )
        raise AuthenticationError("Invalid Authorization header format")

    # Validate token is not empty after "Bearer "
    token = auth_header[7:].strip()  # Remove "Bearer " prefix and strip whitespace
    if not token:
        logger.warning(
            "Authentication failed: Empty token",
            extra={
                "event_type": "auth_failed",
                "reason": "empty_token",
                "ip": request.remote,
                "path": request.path,
            },
        )
        raise AuthenticationError("Empty token in Authorization header")

    try:
        payload = verify_jwt_token(token, jwt_secret)
        user_id = payload["user_id"]
    except AuthenticationError as e:
        logger.warning(
            f"Authentication failed: {e}",
            extra={
                "event_type": "auth_failed",
                "reason": "invalid_token",
                "ip": request.remote,
                "path": request.path,
            },
        )
        raise

    # Check rate limit if enabled
    if check_rate_limit:
        rate_limiter = request.app.get("rate_limiter")
        if rate_limiter and not rate_limiter.is_allowed(user_id):
            logger.warning(
                f"Rate limit exceeded for user {user_id}",
                extra={
                    "event_type": "rate_limit_exceeded",
                    "user_id": user_id,
                    "ip": request.remote,
                    "path": request.path,
                },
            )
            raise RateLimitError(f"Rate limit exceeded for user {user_id}")

    return user_id


async def upload_photo_handler(request: web.Request) -> web.Response:
    """Handle photo upload with progress tracking.

    NOTE: This handler is deprecated in thin client mode.
    WebApp should upload directly to API Gateway /api/photos/upload endpoint instead.

    Expects multipart/form-data with:
    - photo: Image file
    - slot_index: Photo slot (0, 1, or 2)

    Returns JSON with:
    - url: Photo URL
    - file_size: File size in bytes
    - optimized_size: Optimized size in bytes
    - safe_score: NSFW safety score
    """
    # In thin client mode, uploads should go directly to API Gateway
    return error_response(
        "deprecated",
        "Photo upload through bot/api.py is deprecated. Use API Gateway /api/photos/upload endpoint instead.",
        501,  # Not Implemented
    )


def add_rate_limit_handler(handler_func):
    """Decorator to add rate limit error handling to API handlers.

    This decorator wraps handlers to catch RateLimitError and return
    a standardized 429 response.
    """

    async def wrapper(request: web.Request) -> web.Response:
        try:
            return await handler_func(request)
        except RateLimitError as e:
            logger.warning(
                f"Rate limit exceeded: {e}",
                extra={"event_type": "rate_limit_error", "endpoint": request.path},
            )
            return error_response(
                "rate_limit_exceeded", "Too many requests. Please try again later.", 429
            )

    return wrapper


async def generate_token_handler(request: web.Request) -> web.Response:
    """Generate JWT token for user (for testing).

    In production, this would be called after profile creation.
    """
    config: BotConfig = request.app["config"]

    try:
        data = await request.json()
        user_id = data.get("user_id")

        if not user_id:
            return error_response("validation_error", "user_id required")

        token = create_jwt_token(user_id, config.jwt_secret)

        return web.json_response({"token": token, "expires_in": 3600})

    except Exception as e:
        logger.error(f"Token generation failed: {e}", exc_info=True)
        return error_response("internal_error", "Internal server error", 500)


async def check_profile_handler(request: web.Request) -> web.Response:
    """Check if user has a profile in the database.

    Requires authentication via init_data parameter or Authorization header.
    Users can only check their own profile.

    Expects query parameter:
    - user_id: Telegram user ID (must match authenticated user)

    Returns JSON with:
    - has_profile: Boolean indicating if profile exists
    - user_id: The user ID checked
    """
    config: BotConfig = request.app["config"]
    api_client = request.app["api_client"]

    try:
        # Get user_id from query parameter
        user_id_str = request.query.get("user_id")
        if not user_id_str:
            return error_response("validation_error", "user_id query parameter required")

        try:
            requested_user_id = int(user_id_str)
        except ValueError:
            return error_response("validation_error", "user_id must be a valid integer")

        # Authenticate using init_data from Telegram WebApp
        # The init_data contains user information signed by Telegram
        init_data = request.query.get("init_data")

        if not init_data:
            return error_response(
                "unauthorized", "init_data parameter required for authentication", 401
            )

        # Verify init_data signature using cryptographic validation
        from bot.security import ValidationError, validate_webapp_init_data

        try:
            validated_data = validate_webapp_init_data(
                init_data, config.token, max_age_seconds=3600
            )

            # Extract authenticated user ID from validated data
            user_data = validated_data.get("user", {})
            if not isinstance(user_data, dict):
                logger.warning("init_data user data is not a dictionary")
                return error_response("unauthorized", "Unauthorized: invalid init_data", 401)

            authenticated_user_id = user_data.get("id")
            if not authenticated_user_id:
                logger.warning("init_data user missing id field")
                return error_response("unauthorized", "Unauthorized: invalid init_data", 401)

            # Verify that requested user_id matches authenticated user_id
            if authenticated_user_id != requested_user_id:
                return error_response("unauthorized", "Can only check own profile", 403)
        except ValidationError as e:
            # If init_data validation fails, reject the request
            logger.warning(f"init_data validation failed: {e}")
            return error_response("unauthorized", "Unauthorized: invalid init_data", 401)

        # Check profile via API Gateway
        try:
            from .api_client import APIGatewayError

            result = await api_client.check_profile(requested_user_id)

            return web.json_response(result)

        except APIGatewayError as e:
            logger.error(f"API Gateway error: {e}", exc_info=True)
            return web.json_response(
                {"error": {"code": "gateway_error", "message": str(e)}},
                status=e.status_code,
            )

    except Exception as e:
        logger.error(f"Profile check failed: {e}", exc_info=True)
        return error_response("internal_error", "Internal server error", 500)


async def get_profile_handler(request: web.Request) -> web.Response:
    """Get user's profile data.

    Requires JWT authentication.

    Returns JSON with profile data including:
    - name, bio, city, birth_date
    - gender, orientation, goal
    - photos
    - location data
    """
    config: BotConfig = request.app["config"]
    api_client = request.app["api_client"]

    try:
        # Authenticate
        user_id = await authenticate_request(request, config.jwt_secret)

        # Get profile from API Gateway
        try:
            from .api_client import APIGatewayError

            result = await api_client.get_profile(user_id)

            if not result:
                return error_response("not_found", "Profile not found", 404)

            # Return the profile data from API Gateway
            return web.json_response({"profile": result})

        except APIGatewayError as e:
            if e.status_code == 404:
                return error_response("not_found", "Profile not found", 404)
            logger.error(f"API Gateway error: {e}", exc_info=True)
            return error_response("gateway_error", str(e), e.status_code)

    except AuthenticationError as e:
        return error_response("invalid_init_data", str(e), 401)
    except Exception as e:
        logger.error(f"Get profile failed: {e}", exc_info=True)
        return error_response("internal_error", "Internal server error", 500)


async def update_profile_handler(request: web.Request) -> web.Response:
    """Update user's profile data.

    Requires JWT authentication.

    Accepts JSON body with fields to update:
    - name, bio, city
    - height_cm, education, has_children, wants_children
    - smoking, drinking, interests
    - hide_age, hide_distance, hide_online
    """
    config: BotConfig = request.app["config"]
    api_client = request.app["api_client"]

    try:
        # Authenticate
        user_id = await authenticate_request(request, config.jwt_secret)

        # Parse request body
        try:
            data = await request.json()
        except json.JSONDecodeError:
            return web.json_response({"error": "Invalid JSON"}, status=400)

        # Update profile via API Gateway
        try:
            from .api_client import APIGatewayError

            result = await api_client.update_profile(user_id, data)

            logger.info(
                "Profile updated via API",
                extra={"event_type": "profile_updated_api", "user_id": user_id},
            )

            return web.json_response({"success": True, "message": "Profile updated successfully"})

        except APIGatewayError as e:
            if e.status_code == 404:
                return error_response("not_found", "Profile not found", 404)
            logger.error(f"API Gateway error: {e}", exc_info=True)
            return error_response("gateway_error", str(e), e.status_code)

    except AuthenticationError as e:
        return error_response("invalid_init_data", str(e), 401)
    except Exception as e:
        logger.error(f"Update profile failed: {e}", exc_info=True)
        return error_response("internal_error", "Internal server error", 500)


async def discover_handler(request: web.Request) -> web.Response:
    """Get candidate profiles for discovery with filters and pagination.

    Query params:
    - limit: Max candidates to return (default 10, max 50)
    - cursor: Profile ID for pagination
    - age_min, age_max: Age filters
    - max_distance_km: Distance filter
    - goal: Relationship goal
    - height_min, height_max: Height filters
    - has_children, smoking, drinking: Boolean filters
    - education: Education level
    - verified_only: Only verified profiles
    """
    config: BotConfig = request.app["config"]
    api_client = request.app["api_client"]

    try:
        # Authenticate
        user_id = await authenticate_request(request, config.jwt_secret)

        # Parse query parameters
        limit = min(int(request.query.get("limit", 10)), 50)
        cursor = int(request.query["cursor"]) if "cursor" in request.query else None
        age_min = int(request.query["age_min"]) if "age_min" in request.query else None
        age_max = int(request.query["age_max"]) if "age_max" in request.query else None
        max_distance_km = (
            float(request.query["max_distance_km"]) if "max_distance_km" in request.query else None
        )
        goal = request.query.get("goal")
        height_min = int(request.query["height_min"]) if "height_min" in request.query else None
        height_max = int(request.query["height_max"]) if "height_max" in request.query else None
        has_children = (
            request.query.get("has_children") == "true" if "has_children" in request.query else None
        )
        smoking = request.query.get("smoking") == "true" if "smoking" in request.query else None
        drinking = request.query.get("drinking") == "true" if "drinking" in request.query else None
        education = request.query.get("education")
        verified_only = request.query.get("verified_only") == "true"

        # Build filters dict
        try:
            from .api_client import APIGatewayError

            filters = {"limit": limit}
            if cursor:
                filters["cursor"] = cursor
            if age_min is not None:
                filters["age_min"] = age_min
            if age_max is not None:
                filters["age_max"] = age_max
            if max_distance_km is not None:
                filters["max_distance_km"] = max_distance_km
            if goal:
                filters["goal"] = goal
            if height_min is not None:
                filters["height_min"] = height_min
            if height_max is not None:
                filters["height_max"] = height_max
            if has_children is not None:
                filters["has_children"] = has_children
            if smoking is not None:
                filters["smoking"] = smoking
            if drinking is not None:
                filters["drinking"] = drinking
            if education:
                filters["education"] = education
            if verified_only:
                filters["verified_only"] = verified_only

            # Get candidates from API Gateway
            result = await api_client.find_candidates(user_id, filters)

            return web.json_response(result)

        except APIGatewayError as e:
            logger.error(f"API Gateway error: {e}", exc_info=True)
            return web.json_response(
                {"error": {"code": "gateway_error", "message": str(e)}},
                status=e.status_code,
            )

    except AuthenticationError as e:
        return web.json_response(
            {"error": {"code": "invalid_init_data", "message": str(e)}}, status=401
        )
    except ValueError as e:
        return web.json_response(
            {"error": {"code": "validation_error", "message": str(e)}}, status=400
        )
    except Exception as e:
        logger.error(f"Discovery failed: {e}", exc_info=True)
        return web.json_response(
            {"error": {"code": "internal_error", "message": "Internal server error"}},
            status=500,
        )


async def like_handler(request: web.Request) -> web.Response:
    """Handle like/superlike action.

    Body:
    - target_id: User ID to like
    - type: "like" or "superlike" (default "like")

    Returns:
    - match_id: If mutual match created
    """
    config: BotConfig = request.app["config"]
    api_client = request.app["api_client"]

    try:
        # Authenticate
        user_id = await authenticate_request(request, config.jwt_secret)

        # Parse body
        data = await request.json()
        target_id = data.get("target_id")
        interaction_type = data.get("type", "like")

        if not target_id:
            return web.json_response(
                {
                    "error": {
                        "code": "validation_error",
                        "message": "target_id is required",
                    }
                },
                status=400,
            )

        if interaction_type not in ["like", "superlike"]:
            return web.json_response(
                {
                    "error": {
                        "code": "validation_error",
                        "message": "type must be 'like' or 'superlike'",
                    }
                },
                status=400,
            )

        # Create interaction via API Gateway
        try:
            from .api_client import APIGatewayError

            result = await api_client.create_interaction(user_id, target_id, interaction_type)

            return web.json_response(result)

        except APIGatewayError as e:
            if e.status_code == 404:
                return web.json_response(
                    {
                        "error": {
                            "code": "not_found",
                            "message": "Target user not found",
                        }
                    },
                    status=404,
                )
            logger.error(f"API Gateway error: {e}", exc_info=True)
            return web.json_response(
                {"error": {"code": "gateway_error", "message": str(e)}},
                status=e.status_code,
            )

    except AuthenticationError as e:
        return web.json_response(
            {"error": {"code": "invalid_init_data", "message": str(e)}}, status=401
        )
    except Exception as e:
        logger.error(f"Like action failed: {e}", exc_info=True)
        return web.json_response(
            {"error": {"code": "internal_error", "message": "Internal server error"}},
            status=500,
        )


async def pass_handler(request: web.Request) -> web.Response:
    """Handle pass/dislike action.

    Body:
    - target_id: User ID to pass
    """
    config: BotConfig = request.app["config"]
    api_client = request.app["api_client"]

    try:
        # Authenticate
        user_id = await authenticate_request(request, config.jwt_secret)

        # Parse body
        data = await request.json()
        target_id = data.get("target_id")

        if not target_id:
            return web.json_response(
                {
                    "error": {
                        "code": "validation_error",
                        "message": "target_id is required",
                    }
                },
                status=400,
            )

        # Create pass interaction via API Gateway
        try:
            from .api_client import APIGatewayError

            result = await api_client.create_interaction(user_id, target_id, "pass")

            return web.json_response(result)

        except APIGatewayError as e:
            if e.status_code == 404:
                return web.json_response(
                    {
                        "error": {
                            "code": "not_found",
                            "message": "Target user not found",
                        }
                    },
                    status=404,
                )
            logger.error(f"API Gateway error: {e}", exc_info=True)
            return web.json_response(
                {"error": {"code": "gateway_error", "message": str(e)}},
                status=e.status_code,
            )

    except AuthenticationError as e:
        return web.json_response(
            {"error": {"code": "invalid_init_data", "message": str(e)}}, status=401
        )
    except Exception as e:
        logger.error(f"Pass action failed: {e}", exc_info=True)
        return web.json_response(
            {"error": {"code": "internal_error", "message": "Internal server error"}},
            status=500,
        )


async def matches_handler(request: web.Request) -> web.Response:
    """Get user's matches with pagination.

    Query params:
    - limit: Max matches to return (default 20, max 100)
    - cursor: Match ID for pagination
    """
    config: BotConfig = request.app["config"]
    api_client = request.app["api_client"]

    try:
        # Authenticate
        user_id = await authenticate_request(request, config.jwt_secret)

        # Parse query parameters
        limit = min(int(request.query.get("limit", 20)), 100)
        cursor = int(request.query["cursor"]) if "cursor" in request.query else None

        # Get matches via API Gateway
        try:
            from .api_client import APIGatewayError

            result = await api_client.get_matches(user_id, limit, cursor)

            return web.json_response(result)

        except APIGatewayError as e:
            logger.error(f"API Gateway error: {e}", exc_info=True)
            return web.json_response(
                {"error": {"code": "gateway_error", "message": str(e)}},
                status=e.status_code,
            )

    except AuthenticationError as e:
        return web.json_response(
            {"error": {"code": "invalid_init_data", "message": str(e)}}, status=401
        )
    except Exception as e:
        logger.error(f"Get matches failed: {e}", exc_info=True)
        return web.json_response(
            {"error": {"code": "internal_error", "message": "Internal server error"}},
            status=500,
        )


async def add_favorite_handler(request: web.Request) -> web.Response:
    """Add profile to favorites.

    Body:
    - target_id: User ID to add to favorites
    """
    config: BotConfig = request.app["config"]
    api_client = request.app["api_client"]

    try:
        # Authenticate
        user_id = await authenticate_request(request, config.jwt_secret)

        # Parse body
        data = await request.json()
        target_id = data.get("target_id")

        if not target_id:
            return web.json_response(
                {
                    "error": {
                        "code": "validation_error",
                        "message": "target_id is required",
                    }
                },
                status=400,
            )

        # Add to favorites via API Gateway
        try:
            from .api_client import APIGatewayError

            result = await api_client.add_favorite(user_id, target_id)

            return web.json_response(result)

        except APIGatewayError as e:
            logger.error(f"API Gateway error: {e}", exc_info=True)
            return web.json_response(
                {"error": {"code": "gateway_error", "message": str(e)}},
                status=e.status_code,
            )

    except AuthenticationError as e:
        return web.json_response(
            {"error": {"code": "invalid_init_data", "message": str(e)}}, status=401
        )
    except Exception as e:
        logger.error(f"Add favorite failed: {e}", exc_info=True)
        return web.json_response(
            {"error": {"code": "internal_error", "message": "Internal server error"}},
            status=500,
        )


async def remove_favorite_handler(request: web.Request) -> web.Response:
    """Remove profile from favorites.

    Path param:
    - target_id: User ID to remove from favorites
    """
    config: BotConfig = request.app["config"]
    api_client = request.app["api_client"]

    try:
        # Authenticate
        user_id = await authenticate_request(request, config.jwt_secret)

        # Get target_id from path
        target_id = int(request.match_info["target_id"])

        # Remove from favorites via API Gateway
        try:
            from .api_client import APIGatewayError

            result = await api_client.remove_favorite(user_id, target_id)

            return web.json_response(result)

        except APIGatewayError as e:
            if e.status_code == 404:
                return web.json_response(
                    {"error": {"code": "not_found", "message": "Favorite not found"}},
                    status=404,
                )
            logger.error(f"API Gateway error: {e}", exc_info=True)
            return web.json_response(
                {"error": {"code": "gateway_error", "message": str(e)}},
                status=e.status_code,
            )

    except AuthenticationError as e:
        return web.json_response(
            {"error": {"code": "invalid_init_data", "message": str(e)}}, status=401
        )
    except ValueError:
        return web.json_response(
            {"error": {"code": "validation_error", "message": "Invalid target_id"}},
            status=400,
        )
    except Exception as e:
        logger.error(f"Remove favorite failed: {e}", exc_info=True)
        return web.json_response(
            {"error": {"code": "internal_error", "message": "Internal server error"}},
            status=500,
        )


async def get_favorites_handler(request: web.Request) -> web.Response:
    """Get user's favorites with pagination.

    Query params:
    - limit: Max favorites to return (default 20, max 100)
    - cursor: Favorite ID for pagination
    """
    config: BotConfig = request.app["config"]
    api_client = request.app["api_client"]

    try:
        # Authenticate
        user_id = await authenticate_request(request, config.jwt_secret)

        # Parse query parameters
        limit = min(int(request.query.get("limit", 20)), 100)
        cursor = int(request.query["cursor"]) if "cursor" in request.query else None

        # Get favorites via API Gateway
        try:
            from .api_client import APIGatewayError

            result = await api_client.get_favorites(user_id, limit, cursor)

            return web.json_response(result)

        except APIGatewayError as e:
            logger.error(f"API Gateway error: {e}", exc_info=True)
            return web.json_response(
                {"error": {"code": "gateway_error", "message": str(e)}},
                status=e.status_code,
            )

    except AuthenticationError as e:
        return web.json_response(
            {"error": {"code": "invalid_init_data", "message": str(e)}}, status=401
        )
    except Exception as e:
        logger.error(f"Get favorites failed: {e}", exc_info=True)
        return web.json_response(
            {"error": {"code": "internal_error", "message": "Internal server error"}},
            status=500,
        )


async def health_check_handler(request: web.Request) -> web.Response:
    """Health check endpoint."""
    return web.json_response({"status": "ok"})


def create_app(config: BotConfig, api_client) -> web.Application:
    """Create aiohttp application.

    Args:
        config: Bot configuration
        api_client: APIGatewayClient for thin client mode (required)

    Returns:
        aiohttp Application
    """
    if not api_client:
        raise ValueError("api_client is required - bot/api.py only supports thin client mode")

    app = web.Application()

    # Store config and dependencies
    app["config"] = config
    app["api_client"] = api_client

    logger.info("Bot API server running in thin client mode (using API Gateway)")

    # Initialize rate limiter
    rate_limiter = RateLimiter(max_requests=20, window_seconds=60)
    app["rate_limiter"] = rate_limiter
    logger.info(
        "Rate limiter initialized",
        extra={
            "event_type": "rate_limiter_init",
            "max_requests": 20,
            "window_seconds": 60,
        },
    )

    # Initialize NSFW classifier (if available)
    try:
        from nudenet import NudeClassifier

        logger.info("Initializing NudeNet classifier", extra={"event_type": "nsfw_model_init"})
        app["nsfw_classifier"] = NudeClassifier()
    except ImportError:
        logger.warning("NudeNet not available, NSFW detection will use fallback mode")
        app["nsfw_classifier"] = None
    except Exception as e:
        logger.warning(f"Failed to initialize NSFW classifier: {e}", exc_info=True)
        logger.warning("NSFW detection will use fallback mode")
        app["nsfw_classifier"] = None

    # Setup CORS
    cors = cors_setup(
        app,
        defaults={
            "*": ResourceOptions(
                allow_credentials=True,
                expose_headers="*",
                allow_headers="*",
                allow_methods="*",
            )
        },
    )

    # Add routes
    routes = [
        web.get("/health", health_check_handler),
        web.get("/api/profile/check", check_profile_handler),
        web.get("/api/profile", get_profile_handler),
        web.patch("/api/profile", update_profile_handler),
        web.post("/api/photos/upload", upload_photo_handler),
        web.post("/api/auth/token", generate_token_handler),
        # Discovery and interactions
        web.get("/api/discover", discover_handler),
        web.post("/api/like", like_handler),
        web.post("/api/pass", pass_handler),
        web.get("/api/matches", matches_handler),
        # Favorites
        web.post("/api/favorites", add_favorite_handler),
        web.delete("/api/favorites/{target_id}", remove_favorite_handler),
        web.get("/api/favorites", get_favorites_handler),
    ]

    for route in routes:
        cors.add(app.router.add_route(route.method, route.path, route.handler))

    # Add static file serving for photos (if not using CDN)
    if not config.photo_cdn_url:
        app.router.add_static("/photos/", config.photo_storage_path, show_index=False)
        logger.info(f"Static photo serving enabled at /photos/ from {config.photo_storage_path}")
    else:
        logger.info(f"Using CDN for photos: {config.photo_cdn_url}")

    logger.info("HTTP API server created")

    return app


async def run_api_server(
    config: BotConfig,
    api_client,
    host: str = "0.0.0.0",
    port: int = 8080,
):
    """Run HTTP API server.

    Args:
        config: Bot configuration
        api_client: APIGatewayClient for thin client mode (required)
        host: Server host
        port: Server port
    """
    app = create_app(config, api_client)
    runner = web.AppRunner(app)
    await runner.setup()

    site = web.TCPSite(runner, host, port)
    await site.start()

    logger.info(f"HTTP API server started on {host}:{port}")

    # Keep running
    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()
