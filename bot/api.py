"""Bot API utilities for authentication and image processing."""

import io
from datetime import datetime, timedelta, UTC
from typing import Any

import jwt
from PIL import Image

from core.utils.errors import AuthenticationError


def create_jwt_token(user_id: int, secret: str, expires_in: int = 3600) -> str:
    """Create a JWT token for the given user.

    Args:
        user_id: The user ID
        secret: The JWT secret key
        expires_in: Token expiration time in seconds

    Returns:
        The JWT token string
    """
    now = datetime.now(UTC)
    payload = {
        "user_id": user_id,
        "iat": now,
        "exp": now + timedelta(seconds=expires_in),
    }

    return jwt.encode(payload, secret, algorithm="HS256")


def verify_jwt_token(token: str, secret: str) -> dict[str, Any]:
    """Verify and decode a JWT token.

    Args:
        token: The JWT token string
        secret: The JWT secret key

    Returns:
        The decoded token payload

    Raises:
        AuthenticationError: If token is invalid or expired
    """
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthenticationError("Token has expired") from None
    except jwt.InvalidTokenError:
        raise AuthenticationError("Invalid token") from None


async def authenticate_request(request, secret: str) -> int:
    """Authenticate a request using JWT token.

    Args:
        request: The request object with headers attribute
        secret: The JWT secret key

    Returns:
        The authenticated user ID

    Raises:
        AuthenticationError: If authentication fails
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise AuthenticationError("Missing Authorization header")

    if not auth_header.startswith("Bearer "):
        raise AuthenticationError("Invalid Authorization header format")

    token = auth_header[7:]  # Remove "Bearer " prefix
    payload = verify_jwt_token(token, secret)

    return payload["user_id"]


def optimize_image(
    image_bytes: bytes, format: str = "JPEG", quality: int = 85
) -> bytes:
    """Optimize an image for web use.

    Args:
        image_bytes: The original image bytes
        format: The output format (JPEG, PNG, WEBP)
        quality: The compression quality (1-100)

    Returns:
        The optimized image bytes
    """
    image = Image.open(io.BytesIO(image_bytes))

    # Convert to RGB if necessary
    if image.mode in ("RGBA", "LA", "P"):
        background = Image.new("RGB", image.size, (255, 255, 255))
        if image.mode == "P":
            image = image.convert("RGBA")
        background.paste(
            image, mask=image.split()[-1] if image.mode == "RGBA" else None
        )
        image = background
    elif image.mode != "RGB":
        image = image.convert("RGB")

    # Resize if too large
    max_size = 1200
    if max(image.size) > max_size:
        ratio = max_size / max(image.size)
        new_size = (int(image.size[0] * ratio), int(image.size[1] * ratio))
        image = image.resize(new_size, Image.Resampling.LANCZOS)

    # Save in the specified format
    output = io.BytesIO()
    image.save(output, format=format, quality=quality, optimize=True)
    return output.getvalue()


def calculate_nsfw_score(image_bytes: bytes) -> float:
    """Calculate NSFW score for an image.

    Args:
        image_bytes: The image bytes

    Returns:
        NSFW score between 0.0 (safe) and 1.0 (explicit)
    """
    # This is a placeholder implementation
    # In a real implementation, you would use a proper NSFW detection model
    # like NudeNet or similar

    try:
        image = Image.open(io.BytesIO(image_bytes))

        # Basic heuristics (not real NSFW detection)
        # This is just for testing purposes
        width, height = image.size
        aspect_ratio = width / height

        # Very basic heuristic: square images are more likely to be safe
        if 0.8 <= aspect_ratio <= 1.2:
            return 0.8  # Likely safe (high score for safe content)
        else:
            return 0.6  # Slightly higher risk

    except Exception:
        return 0.5  # Unknown content


# HTTP Handler functions for testing
async def health_check_handler(request):
    """Health check handler for testing."""
    from aiohttp import web

    return web.json_response({"status": "ok", "message": "Service is healthy"})


async def generate_token_handler(request):
    """Generate token handler for testing."""

    from aiohttp import web

    try:
        data = await request.json()
        user_id = data.get("user_id")

        if not user_id:
            return web.json_response({"error": "Missing user_id"}, status=400)

        # Get JWT secret from environment or request
        jwt_secret = "test-secret"  # In real app, get from config

        token = create_jwt_token(user_id, jwt_secret)

        return web.json_response({"token": token, "expires_in": 3600})  # 1 hour

    except Exception as e:
        return web.json_response({"error": str(e)}, status=500)


def create_app(config=None, api_client=None):
    """Create aiohttp app for testing."""
    from aiohttp import web

    app = web.Application()

    # Add routes
    app.router.add_get("/health", health_check_handler)
    app.router.add_post("/generate-token", generate_token_handler)
    app.router.add_get("/check-profile", check_profile_handler)

    # Store config and API client in app
    if config:
        app["config"] = config
    if api_client:
        app["api_client"] = api_client

    return app


async def check_profile_handler(request):
    """Check profile handler for testing."""
    from aiohttp import web

    user_id = request.query.get("user_id")

    if not user_id:
        return web.json_response(
            {
                "error": {
                    "code": "validation_error",
                    "message": "Missing user_id parameter",
                }
            },
            status=400,
        )

    try:
        user_id_int = int(user_id)
    except ValueError:
        return web.json_response(
            {
                "error": {
                    "code": "validation_error",
                    "message": "Invalid user_id format - must be integer",
                }
            },
            status=400,
        )

    # Use API client if available, otherwise mock
    api_client = request.app.get("api_client")
    if api_client:
        result = await api_client.check_profile(user_id_int)
        return web.json_response(result)
    else:
        # Mock profile check - in real app, check database
        # For testing, assume profile exists if user_id > 0
        if user_id_int > 0:
            return web.json_response({"has_profile": True, "user_id": user_id_int})
        else:
            return web.json_response({"has_profile": False, "user_id": user_id_int})
