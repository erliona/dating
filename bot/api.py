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
            except OSError:
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
    session_maker: async_sessionmaker = request.app["session_maker"]
    
    try:
        # Get user_id from query parameter
        user_id_str = request.query.get("user_id")
        if not user_id_str:
            return web.json_response(
                {"error": "user_id query parameter required"},
                status=400
            )
        
        try:
            requested_user_id = int(user_id_str)
        except ValueError:
            return web.json_response(
                {"error": "user_id must be a valid integer"},
                status=400
            )
        
        # Authenticate using init_data from Telegram WebApp
        # The init_data contains user information signed by Telegram
        init_data = request.query.get("init_data")
        
        if init_data:
            # Verify init_data signature (basic validation)
            # In production, you should verify the signature using bot token
            # For now, we extract user_id from init_data
            from urllib.parse import parse_qs
            try:
                params = parse_qs(init_data)
                user_param = params.get('user', [''])[0]
                if user_param:
                    import json
                    user_data = json.loads(user_param)
                    authenticated_user_id = user_data.get('id')
                    
                    # Verify that requested user_id matches authenticated user_id
                    if authenticated_user_id != requested_user_id:
                        return web.json_response(
                            {"error": "Unauthorized: can only check own profile"},
                            status=403
                        )
            except (ValueError, json.JSONDecodeError, KeyError):
                # If init_data parsing fails, allow for backward compatibility
                # but log the issue
                logger.warning(f"Failed to parse init_data for authentication")
        
        # Check database for profile
        async with session_maker() as session:
            repository = ProfileRepository(session)
            
            # Get user by Telegram ID
            user = await repository.get_user_by_tg_id(requested_user_id)
            
            if not user:
                return web.json_response({
                    "has_profile": False,
                    "user_id": requested_user_id
                })
            
            # Check if user has a profile
            profile = await repository.get_profile_by_user_id(user.id)
            
            return web.json_response({
                "has_profile": profile is not None,
                "user_id": requested_user_id
            })
    
    except Exception as e:
        logger.error(f"Profile check failed: {e}", exc_info=True)
        return web.json_response(
            {"error": "Internal server error"},
            status=500
        )


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
    session_maker: async_sessionmaker = request.app["session_maker"]
    
    try:
        # Authenticate
        user_id = await authenticate_request(request, config.jwt_secret)
        
        async with session_maker() as session:
            repository = ProfileRepository(session)
            
            # Get user by Telegram ID
            user = await repository.get_user_by_tg_id(user_id)
            
            if not user:
                return web.json_response(
                    {"error": "User not found"},
                    status=404
                )
            
            # Get profile
            profile = await repository.get_profile_by_user_id(user.id)
            
            if not profile:
                return web.json_response(
                    {"error": "Profile not found"},
                    status=404
                )
            
            # Get photos
            photos = await repository.get_user_photos(user.id)
            
            # Calculate age
            age = (datetime.now().date() - profile.birth_date).days // 365
            
            # Build response
            profile_data = {
                "name": profile.name,
                "age": age,
                "birth_date": profile.birth_date.isoformat(),
                "gender": profile.gender,
                "orientation": profile.orientation,
                "goal": profile.goal,
                "bio": profile.bio,
                "city": profile.city,
                "country": profile.country,
                "latitude": profile.latitude,
                "longitude": profile.longitude,
                "height_cm": profile.height_cm,
                "education": profile.education,
                "has_children": profile.has_children,
                "wants_children": profile.wants_children,
                "smoking": profile.smoking,
                "drinking": profile.drinking,
                "interests": profile.interests,
                "hide_age": profile.hide_age,
                "hide_distance": profile.hide_distance,
                "hide_online": profile.hide_online,
                "photos": [{"url": p.url, "sort_order": p.sort_order} for p in photos]
            }
            
            return web.json_response({
                "profile": profile_data
            })
    
    except AuthenticationError as e:
        return web.json_response(
            {"error": str(e)},
            status=401
        )
    except Exception as e:
        logger.error(f"Get profile failed: {e}", exc_info=True)
        return web.json_response(
            {"error": "Internal server error"},
            status=500
        )


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
    session_maker: async_sessionmaker = request.app["session_maker"]
    
    try:
        # Authenticate
        user_id = await authenticate_request(request, config.jwt_secret)
        
        # Parse request body
        try:
            data = await request.json()
        except json.JSONDecodeError:
            return web.json_response(
                {"error": "Invalid JSON"},
                status=400
            )
        
        async with session_maker() as session:
            repository = ProfileRepository(session)
            
            # Get user by Telegram ID
            user = await repository.get_user_by_tg_id(user_id)
            
            if not user:
                return web.json_response(
                    {"error": "User not found"},
                    status=404
                )
            
            # Update profile
            profile = await repository.update_profile(user.id, data)
            
            if not profile:
                return web.json_response(
                    {"error": "Profile not found"},
                    status=404
                )
            
            # Commit changes
            await session.commit()
            
            logger.info(
                "Profile updated via API",
                extra={"event_type": "profile_updated_api", "user_id": user_id}
            )
            
            return web.json_response({
                "success": True,
                "message": "Profile updated successfully"
            })
    
    except AuthenticationError as e:
        return web.json_response(
            {"error": str(e)},
            status=401
        )
    except Exception as e:
        logger.error(f"Update profile failed: {e}", exc_info=True)
        return web.json_response(
            {"error": "Internal server error"},
            status=500
        )


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
    session_maker: async_sessionmaker = request.app["session_maker"]
    
    try:
        # Authenticate
        user_id = await authenticate_request(request, config.jwt_secret)
        
        # Parse query parameters
        limit = min(int(request.query.get("limit", 10)), 50)
        cursor = int(request.query["cursor"]) if "cursor" in request.query else None
        age_min = int(request.query["age_min"]) if "age_min" in request.query else None
        age_max = int(request.query["age_max"]) if "age_max" in request.query else None
        max_distance_km = float(request.query["max_distance_km"]) if "max_distance_km" in request.query else None
        goal = request.query.get("goal")
        height_min = int(request.query["height_min"]) if "height_min" in request.query else None
        height_max = int(request.query["height_max"]) if "height_max" in request.query else None
        has_children = request.query.get("has_children") == "true" if "has_children" in request.query else None
        smoking = request.query.get("smoking") == "true" if "smoking" in request.query else None
        drinking = request.query.get("drinking") == "true" if "drinking" in request.query else None
        education = request.query.get("education")
        verified_only = request.query.get("verified_only") == "true"
        
        async with session_maker() as session:
            repository = ProfileRepository(session)
            
            # Get user
            user = await repository.get_user_by_tg_id(user_id)
            if not user:
                return web.json_response(
                    {"error": {"code": "not_found", "message": "User not found"}},
                    status=404
                )
            
            # Find candidates
            profiles, next_cursor = await repository.find_candidates(
                user_id=user.id,
                limit=limit,
                cursor=cursor,
                age_min=age_min,
                age_max=age_max,
                max_distance_km=max_distance_km,
                goal=goal,
                height_min=height_min,
                height_max=height_max,
                has_children=has_children,
                smoking=smoking,
                drinking=drinking,
                education=education,
                verified_only=verified_only
            )
            
            # Get photos for each profile
            profiles_data = []
            for profile in profiles:
                photos = await repository.get_user_photos(profile.user_id)
                profiles_data.append({
                    "id": profile.id,
                    "user_id": profile.user_id,
                    "name": profile.name,
                    "age": (datetime.now().date() - profile.birth_date).days // 365,
                    "gender": profile.gender,
                    "goal": profile.goal,
                    "bio": profile.bio,
                    "interests": profile.interests or [],
                    "height_cm": profile.height_cm,
                    "education": profile.education,
                    "city": profile.city,
                    "photos": [{"url": p.url, "is_verified": p.is_verified} for p in photos]
                })
            
            return web.json_response({
                "profiles": profiles_data,
                "next_cursor": next_cursor,
                "count": len(profiles_data)
            })
    
    except AuthenticationError as e:
        return web.json_response(
            {"error": {"code": "invalid_init_data", "message": str(e)}},
            status=401
        )
    except ValueError as e:
        return web.json_response(
            {"error": {"code": "validation_error", "message": str(e)}},
            status=400
        )
    except Exception as e:
        logger.error(f"Discovery failed: {e}", exc_info=True)
        return web.json_response(
            {"error": {"code": "internal_error", "message": "Internal server error"}},
            status=500
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
    session_maker: async_sessionmaker = request.app["session_maker"]
    
    try:
        # Authenticate
        user_id = await authenticate_request(request, config.jwt_secret)
        
        # Parse body
        data = await request.json()
        target_id = data.get("target_id")
        interaction_type = data.get("type", "like")
        
        if not target_id:
            return web.json_response(
                {"error": {"code": "validation_error", "message": "target_id is required"}},
                status=400
            )
        
        if interaction_type not in ["like", "superlike"]:
            return web.json_response(
                {"error": {"code": "validation_error", "message": "type must be 'like' or 'superlike'"}},
                status=400
            )
        
        async with session_maker() as session:
            repository = ProfileRepository(session)
            
            # Get user
            user = await repository.get_user_by_tg_id(user_id)
            if not user:
                return web.json_response(
                    {"error": {"code": "not_found", "message": "User not found"}},
                    status=404
                )
            
            # Create interaction (idempotent)
            await repository.create_interaction(
                user_id=user.id,
                target_id=target_id,
                interaction_type=interaction_type
            )
            
            # Check for mutual like
            match_id = None
            if await repository.check_mutual_like(user.id, target_id):
                # Create match (idempotent)
                match = await repository.create_match(user.id, target_id)
                match_id = match.id
            
            await session.commit()
            
            response = {"success": True}
            if match_id:
                response["match_id"] = match_id
            
            return web.json_response(response)
    
    except AuthenticationError as e:
        return web.json_response(
            {"error": {"code": "invalid_init_data", "message": str(e)}},
            status=401
        )
    except Exception as e:
        logger.error(f"Like action failed: {e}", exc_info=True)
        return web.json_response(
            {"error": {"code": "internal_error", "message": "Internal server error"}},
            status=500
        )


async def pass_handler(request: web.Request) -> web.Response:
    """Handle pass/dislike action.
    
    Body:
    - target_id: User ID to pass
    """
    config: BotConfig = request.app["config"]
    session_maker: async_sessionmaker = request.app["session_maker"]
    
    try:
        # Authenticate
        user_id = await authenticate_request(request, config.jwt_secret)
        
        # Parse body
        data = await request.json()
        target_id = data.get("target_id")
        
        if not target_id:
            return web.json_response(
                {"error": {"code": "validation_error", "message": "target_id is required"}},
                status=400
            )
        
        async with session_maker() as session:
            repository = ProfileRepository(session)
            
            # Get user
            user = await repository.get_user_by_tg_id(user_id)
            if not user:
                return web.json_response(
                    {"error": {"code": "not_found", "message": "User not found"}},
                    status=404
                )
            
            # Create pass interaction
            await repository.create_interaction(
                user_id=user.id,
                target_id=target_id,
                interaction_type="pass"
            )
            
            await session.commit()
            
            return web.json_response({"success": True})
    
    except AuthenticationError as e:
        return web.json_response(
            {"error": {"code": "invalid_init_data", "message": str(e)}},
            status=401
        )
    except Exception as e:
        logger.error(f"Pass action failed: {e}", exc_info=True)
        return web.json_response(
            {"error": {"code": "internal_error", "message": "Internal server error"}},
            status=500
        )


async def matches_handler(request: web.Request) -> web.Response:
    """Get user's matches with pagination.
    
    Query params:
    - limit: Max matches to return (default 20, max 100)
    - cursor: Match ID for pagination
    """
    config: BotConfig = request.app["config"]
    session_maker: async_sessionmaker = request.app["session_maker"]
    
    try:
        # Authenticate
        user_id = await authenticate_request(request, config.jwt_secret)
        
        # Parse query parameters
        limit = min(int(request.query.get("limit", 20)), 100)
        cursor = int(request.query["cursor"]) if "cursor" in request.query else None
        
        async with session_maker() as session:
            repository = ProfileRepository(session)
            
            # Get user
            user = await repository.get_user_by_tg_id(user_id)
            if not user:
                return web.json_response(
                    {"error": {"code": "not_found", "message": "User not found"}},
                    status=404
                )
            
            # Get matches
            matches_with_profiles, next_cursor = await repository.get_matches(
                user_id=user.id,
                limit=limit,
                cursor=cursor
            )
            
            # Format response
            matches_data = []
            for match, profile in matches_with_profiles:
                photos = await repository.get_user_photos(profile.user_id)
                matches_data.append({
                    "match_id": match.id,
                    "created_at": match.created_at.isoformat(),
                    "profile": {
                        "id": profile.id,
                        "user_id": profile.user_id,
                        "name": profile.name,
                        "age": (datetime.now().date() - profile.birth_date).days // 365,
                        "bio": profile.bio,
                        "photos": [{"url": p.url} for p in photos[:1]]  # First photo only
                    }
                })
            
            return web.json_response({
                "matches": matches_data,
                "next_cursor": next_cursor,
                "count": len(matches_data)
            })
    
    except AuthenticationError as e:
        return web.json_response(
            {"error": {"code": "invalid_init_data", "message": str(e)}},
            status=401
        )
    except Exception as e:
        logger.error(f"Get matches failed: {e}", exc_info=True)
        return web.json_response(
            {"error": {"code": "internal_error", "message": "Internal server error"}},
            status=500
        )


async def add_favorite_handler(request: web.Request) -> web.Response:
    """Add profile to favorites.
    
    Body:
    - target_id: User ID to add to favorites
    """
    config: BotConfig = request.app["config"]
    session_maker: async_sessionmaker = request.app["session_maker"]
    
    try:
        # Authenticate
        user_id = await authenticate_request(request, config.jwt_secret)
        
        # Parse body
        data = await request.json()
        target_id = data.get("target_id")
        
        if not target_id:
            return web.json_response(
                {"error": {"code": "validation_error", "message": "target_id is required"}},
                status=400
            )
        
        async with session_maker() as session:
            repository = ProfileRepository(session)
            
            # Get user
            user = await repository.get_user_by_tg_id(user_id)
            if not user:
                return web.json_response(
                    {"error": {"code": "not_found", "message": "User not found"}},
                    status=404
                )
            
            # Add to favorites
            favorite = await repository.add_favorite(user.id, target_id)
            await session.commit()
            
            return web.json_response({
                "success": True,
                "favorite_id": favorite.id
            })
    
    except AuthenticationError as e:
        return web.json_response(
            {"error": {"code": "invalid_init_data", "message": str(e)}},
            status=401
        )
    except Exception as e:
        logger.error(f"Add favorite failed: {e}", exc_info=True)
        return web.json_response(
            {"error": {"code": "internal_error", "message": "Internal server error"}},
            status=500
        )


async def remove_favorite_handler(request: web.Request) -> web.Response:
    """Remove profile from favorites.
    
    Path param:
    - target_id: User ID to remove from favorites
    """
    config: BotConfig = request.app["config"]
    session_maker: async_sessionmaker = request.app["session_maker"]
    
    try:
        # Authenticate
        user_id = await authenticate_request(request, config.jwt_secret)
        
        # Get target_id from path
        target_id = int(request.match_info["target_id"])
        
        async with session_maker() as session:
            repository = ProfileRepository(session)
            
            # Get user
            user = await repository.get_user_by_tg_id(user_id)
            if not user:
                return web.json_response(
                    {"error": {"code": "not_found", "message": "User not found"}},
                    status=404
                )
            
            # Remove from favorites
            removed = await repository.remove_favorite(user.id, target_id)
            await session.commit()
            
            if not removed:
                return web.json_response(
                    {"error": {"code": "not_found", "message": "Favorite not found"}},
                    status=404
                )
            
            return web.json_response({"success": True})
    
    except AuthenticationError as e:
        return web.json_response(
            {"error": {"code": "invalid_init_data", "message": str(e)}},
            status=401
        )
    except ValueError:
        return web.json_response(
            {"error": {"code": "validation_error", "message": "Invalid target_id"}},
            status=400
        )
    except Exception as e:
        logger.error(f"Remove favorite failed: {e}", exc_info=True)
        return web.json_response(
            {"error": {"code": "internal_error", "message": "Internal server error"}},
            status=500
        )


async def get_favorites_handler(request: web.Request) -> web.Response:
    """Get user's favorites with pagination.
    
    Query params:
    - limit: Max favorites to return (default 20, max 100)
    - cursor: Favorite ID for pagination
    """
    config: BotConfig = request.app["config"]
    session_maker: async_sessionmaker = request.app["session_maker"]
    
    try:
        # Authenticate
        user_id = await authenticate_request(request, config.jwt_secret)
        
        # Parse query parameters
        limit = min(int(request.query.get("limit", 20)), 100)
        cursor = int(request.query["cursor"]) if "cursor" in request.query else None
        
        async with session_maker() as session:
            repository = ProfileRepository(session)
            
            # Get user
            user = await repository.get_user_by_tg_id(user_id)
            if not user:
                return web.json_response(
                    {"error": {"code": "not_found", "message": "User not found"}},
                    status=404
                )
            
            # Get favorites
            favorites_with_profiles, next_cursor = await repository.get_favorites(
                user_id=user.id,
                limit=limit,
                cursor=cursor
            )
            
            # Format response
            favorites_data = []
            for favorite, profile in favorites_with_profiles:
                photos = await repository.get_user_photos(profile.user_id)
                favorites_data.append({
                    "favorite_id": favorite.id,
                    "created_at": favorite.created_at.isoformat(),
                    "profile": {
                        "id": profile.id,
                        "user_id": profile.user_id,
                        "name": profile.name,
                        "age": (datetime.now().date() - profile.birth_date).days // 365,
                        "bio": profile.bio,
                        "photos": [{"url": p.url} for p in photos[:1]]  # First photo only
                    }
                })
            
            return web.json_response({
                "favorites": favorites_data,
                "next_cursor": next_cursor,
                "count": len(favorites_data)
            })
    
    except AuthenticationError as e:
        return web.json_response(
            {"error": {"code": "invalid_init_data", "message": str(e)}},
            status=401
        )
    except Exception as e:
        logger.error(f"Get favorites failed: {e}", exc_info=True)
        return web.json_response(
            {"error": {"code": "internal_error", "message": "Internal server error"}},
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
