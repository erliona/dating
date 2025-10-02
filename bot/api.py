"""HTTP API server for photo uploads.

Provides endpoints for uploading photos with JWT authentication,
progress tracking, and image optimization.
"""

import asyncio
import base64
import hashlib
import json
import logging
from datetime import datetime, timedelta
from io import BytesIO
from typing import Optional

import jwt
from aiohttp import web
from aiohttp_cors import ResourceOptions, setup as cors_setup
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from .config import BotConfig
from .media import (
    MAX_PHOTO_SIZE,
    MAX_PHOTOS_PER_USER,
    PhotoValidationError,
    detect_mime_type,
    validate_mime_type,
    validate_photo_size,
)
from .repository import ProfileRepository

logger = logging.getLogger(__name__)

# Image optimization settings
MAX_IMAGE_DIMENSION = 1200  # Maximum width/height in pixels
JPEG_QUALITY = 85  # JPEG compression quality (0-100)
WEBP_QUALITY = 80  # WebP compression quality (0-100)


class AuthenticationError(Exception):
    """Raised when authentication fails."""
    pass


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
        "iat": now
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
    try:
        # Open image
        image = Image.open(BytesIO(image_bytes))
        
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
                extra={"event_type": "image_resized"}
            )
        
        # Save optimized image
        output = BytesIO()
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
            extra={"event_type": "image_optimized", "reduction_percent": reduction}
        )
        
        return optimized_bytes
    
    except Exception as e:
        logger.error(f"Image optimization failed: {e}", exc_info=True)
        # Return original if optimization fails
        return image_bytes


def calculate_nsfw_score(image_bytes: bytes) -> float:
    """Calculate NSFW score for image using NudeNet ML model.
    
    Uses NudeNet classifier to detect NSFW content.
    The model classifies images into categories and returns a safety score.
    
    Args:
        image_bytes: Image bytes
        
    Returns:
        Safety score (0.0 = unsafe, 1.0 = safe)
    """
    try:
        from nudenet import NudeClassifier
        from PIL import Image
        import io
        
        # Initialize classifier (cached after first use)
        if not hasattr(calculate_nsfw_score, '_classifier'):
            logger.info("Initializing NudeNet classifier", extra={"event_type": "nsfw_model_init"})
            calculate_nsfw_score._classifier = NudeClassifier()
        
        # Convert bytes to PIL Image for NudeNet
        image = Image.open(io.BytesIO(image_bytes))
        
        # Save to temporary file (NudeNet requires file path)
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
            image.save(tmp.name, format='JPEG')
            tmp_path = tmp.name
        
        try:
            # Classify image
            result = calculate_nsfw_score._classifier.classify(tmp_path)
            
            # Result format: {image_path: {'safe': probability, 'unsafe': probability}}
            classification = result.get(tmp_path, {})
            
            # Get safe probability (higher is better)
            safe_prob = classification.get('safe', 0.5)
            unsafe_prob = classification.get('unsafe', 0.5)
            
            # Calculate safety score (0.0 = unsafe, 1.0 = safe)
            safety_score = safe_prob / (safe_prob + unsafe_prob) if (safe_prob + unsafe_prob) > 0 else 0.5
            
            logger.info(
                f"NSFW detection completed: safe={safe_prob:.3f}, unsafe={unsafe_prob:.3f}, score={safety_score:.3f}",
                extra={
                    "event_type": "nsfw_detection_complete",
                    "safe_probability": safe_prob,
                    "unsafe_probability": unsafe_prob,
                    "safety_score": safety_score
                }
            )
            
            return safety_score
            
        finally:
            # Clean up temporary file
            import os
            try:
                os.unlink(tmp_path)
            except:
                pass
    
    except ImportError:
        logger.warning(
            "NudeNet not available, falling back to permissive mode",
            extra={"event_type": "nsfw_detection_fallback"}
        )
        # Fallback to permissive if NudeNet not installed
        return 1.0
    
    except Exception as e:
        logger.error(
            f"NSFW detection failed: {e}",
            exc_info=True,
            extra={"event_type": "nsfw_detection_error"}
        )
        # On error, be permissive
        return 1.0


async def authenticate_request(request: web.Request, jwt_secret: str) -> int:
    """Authenticate request and extract user ID.
    
    Args:
        request: aiohttp request
        jwt_secret: JWT secret key
        
    Returns:
        User ID
        
    Raises:
        AuthenticationError: If authentication fails
    """
    auth_header = request.headers.get("Authorization")
    if not auth_header:
        raise AuthenticationError("Missing Authorization header")
    
    if not auth_header.startswith("Bearer "):
        raise AuthenticationError("Invalid Authorization header format")
    
    token = auth_header[7:]  # Remove "Bearer " prefix
    payload = verify_jwt_token(token, jwt_secret)
    
    return payload["user_id"]


async def upload_photo_handler(request: web.Request) -> web.Response:
    """Handle photo upload with progress tracking.
    
    Expects multipart/form-data with:
    - photo: Image file
    - slot_index: Photo slot (0, 1, or 2)
    
    Returns JSON with:
    - url: Photo URL
    - file_size: File size in bytes
    - optimized_size: Optimized size in bytes
    - safe_score: NSFW safety score
    """
    config: BotConfig = request.app["config"]
    session_maker: async_sessionmaker = request.app["session_maker"]
    
    try:
        # Authenticate
        user_id = await authenticate_request(request, config.jwt_secret)
        
        # Parse multipart form data
        reader = await request.multipart()
        photo_data = None
        slot_index = None
        
        async for field in reader:
            if field.name == "photo":
                # Read photo data
                photo_data = await field.read()
            elif field.name == "slot_index":
                slot_index_str = await field.read()
                slot_index = int(slot_index_str.decode("utf-8"))
        
        if not photo_data:
            return web.json_response(
                {"error": "No photo data provided"},
                status=400
            )
        
        if slot_index is None or slot_index < 0 or slot_index >= MAX_PHOTOS_PER_USER:
            return web.json_response(
                {"error": f"Invalid slot_index. Must be 0-{MAX_PHOTOS_PER_USER - 1}"},
                status=400
            )
        
        # Validate photo size
        is_valid, error = validate_photo_size(photo_data)
        if not is_valid:
            return web.json_response({"error": error}, status=400)
        
        # Detect and validate MIME type
        mime_type = detect_mime_type(photo_data)
        is_valid, error = validate_mime_type(mime_type)
        if not is_valid:
            return web.json_response({"error": error}, status=400)
        
        # Optimize image
        format_map = {
            "image/jpeg": "JPEG",
            "image/jpg": "JPEG",
            "image/png": "PNG",
            "image/webp": "WEBP"
        }
        output_format = format_map.get(mime_type, "JPEG")
        optimized_data = optimize_image(photo_data, output_format)
        
        # Calculate NSFW score
        safe_score = calculate_nsfw_score(optimized_data)
        if safe_score < config.nsfw_threshold:
            logger.warning(
                f"Photo rejected: NSFW score {safe_score:.3f} below threshold {config.nsfw_threshold}",
                extra={
                    "event_type": "photo_rejected_nsfw",
                    "user_id": user_id,
                    "safe_score": safe_score,
                    "threshold": config.nsfw_threshold
                }
            )
            return web.json_response(
                {"error": "Photo contains inappropriate content"},
                status=400
            )
        
        # Save photo to storage
        photo_hash = hashlib.sha256(optimized_data).hexdigest()
        ext_map = {"JPEG": "jpg", "PNG": "png", "WEBP": "webp"}
        ext = ext_map.get(output_format, "jpg")
        filename = f"{user_id}_{slot_index}_{photo_hash[:16]}.{ext}"
        
        # Save to configured storage path
        import os
        storage_path = config.photo_storage_path
        os.makedirs(storage_path, exist_ok=True)
        file_path = os.path.join(storage_path, filename)
        with open(file_path, "wb") as f:
            f.write(optimized_data)
        
        # Generate photo URL (use CDN if configured, otherwise local path)
        if config.photo_cdn_url:
            photo_url = f"{config.photo_cdn_url}/{filename}"
        else:
            photo_url = f"/photos/{filename}"
        
        logger.info(
            "Photo uploaded successfully",
            extra={
                "event_type": "photo_uploaded",
                "user_id": user_id,
                "slot_index": slot_index,
                "filename": filename,
                "original_size": len(photo_data),
                "optimized_size": len(optimized_data),
                "safe_score": safe_score
            }
        )
        
        return web.json_response({
            "url": photo_url,
            "file_size": len(photo_data),
            "optimized_size": len(optimized_data),
            "safe_score": safe_score,
            "message": "Photo uploaded successfully"
        })
    
    except AuthenticationError as e:
        return web.json_response({"error": str(e)}, status=401)
    except PhotoValidationError as e:
        return web.json_response({"error": str(e)}, status=400)
    except Exception as e:
        logger.error(f"Photo upload failed: {e}", exc_info=True)
        return web.json_response(
            {"error": "Internal server error"},
            status=500
        )


async def generate_token_handler(request: web.Request) -> web.Response:
    """Generate JWT token for user (for testing).
    
    In production, this would be called after profile creation.
    """
    config: BotConfig = request.app["config"]
    
    try:
        data = await request.json()
        user_id = data.get("user_id")
        
        if not user_id:
            return web.json_response(
                {"error": "user_id required"},
                status=400
            )
        
        token = create_jwt_token(user_id, config.jwt_secret)
        
        return web.json_response({
            "token": token,
            "expires_in": 3600
        })
    
    except Exception as e:
        logger.error(f"Token generation failed: {e}", exc_info=True)
        return web.json_response(
            {"error": "Internal server error"},
            status=500
        )


async def health_check_handler(request: web.Request) -> web.Response:
    """Health check endpoint."""
    return web.json_response({"status": "ok"})


def create_app(config: BotConfig, session_maker: async_sessionmaker) -> web.Application:
    """Create aiohttp application.
    
    Args:
        config: Bot configuration
        session_maker: SQLAlchemy session maker
        
    Returns:
        aiohttp Application
    """
    app = web.Application()
    
    # Store config and session maker
    app["config"] = config
    app["session_maker"] = session_maker
    
    # Setup CORS
    cors = cors_setup(app, defaults={
        "*": ResourceOptions(
            allow_credentials=True,
            expose_headers="*",
            allow_headers="*",
            allow_methods="*"
        )
    })
    
    # Add routes
    routes = [
        web.get("/health", health_check_handler),
        web.post("/api/photos/upload", upload_photo_handler),
        web.post("/api/auth/token", generate_token_handler),
    ]
    
    for route in routes:
        cors.add(app.router.add_route(route.method, route.path, route.handler))
    
    # Add static file serving for photos (if not using CDN)
    if not config.photo_cdn_url:
        app.router.add_static('/photos/', config.photo_storage_path, show_index=False)
        logger.info(f"Static photo serving enabled at /photos/ from {config.photo_storage_path}")
    else:
        logger.info(f"Using CDN for photos: {config.photo_cdn_url}")
    
    logger.info("HTTP API server created")
    
    return app


async def run_api_server(
    config: BotConfig,
    session_maker: async_sessionmaker,
    host: str = "0.0.0.0",
    port: int = 8080
):
    """Run HTTP API server.
    
    Args:
        config: Bot configuration
        session_maker: SQLAlchemy session maker
        host: Server host
        port: Server port
    """
    app = create_app(config, session_maker)
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
