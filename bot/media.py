"""Media handling utilities for photo uploads.

Epic B2: Photo upload, validation, EXIF cleaning, storage.
"""

import base64
import hashlib
import logging
import os
import re
from io import BytesIO
from pathlib import Path
from typing import Optional

logger = logging.getLogger(__name__)

# Photo constraints
MAX_PHOTO_SIZE = 5 * 1024 * 1024  # 5MB
MAX_PHOTOS_PER_USER = 3
ALLOWED_MIME_TYPES = ["image/jpeg", "image/jpg", "image/png", "image/webp"]


class PhotoValidationError(Exception):
    """Raised when photo validation fails."""

    pass


def validate_photo_size(data: bytes) -> tuple[bool, Optional[str]]:
    """Validate photo file size.

    Args:
        data: Photo bytes

    Returns:
        Tuple of (is_valid, error_message)
    """
    if len(data) > MAX_PHOTO_SIZE:
        return (
            False,
            f"Photo size exceeds maximum of {MAX_PHOTO_SIZE // 1024 // 1024}MB",
        )

    if len(data) == 0:
        return False, "Photo data is empty"

    return True, None


def detect_mime_type(data: bytes) -> str:
    """Detect MIME type from photo data.

    Args:
        data: Photo bytes

    Returns:
        MIME type string
    """
    # Check magic bytes
    if data.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    elif data.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    elif data.startswith(b"RIFF") and data[8:12] == b"WEBP":
        return "image/webp"
    else:
        return "application/octet-stream"


def validate_mime_type(mime_type: str) -> tuple[bool, Optional[str]]:
    """Validate photo MIME type.

    Args:
        mime_type: MIME type string

    Returns:
        Tuple of (is_valid, error_message)
    """
    if mime_type not in ALLOWED_MIME_TYPES:
        return (
            False,
            f"Invalid file type. Allowed types: {', '.join(ALLOWED_MIME_TYPES)}",
        )

    return True, None


def decode_base64_photo(base64_data: str) -> tuple[Optional[bytes], Optional[str]]:
    """Decode base64-encoded photo data.

    Args:
        base64_data: Base64-encoded string (may include data URI prefix)

    Returns:
        Tuple of (decoded_bytes, error_message)
    """
    try:
        # Remove data URI prefix if present (e.g., "data:image/jpeg;base64,")
        if base64_data.startswith("data:"):
            base64_data = base64_data.split(",", 1)[1]

        # Decode base64
        photo_bytes = base64.b64decode(base64_data)
        return photo_bytes, None

    except Exception as e:
        logger.warning(
            "Failed to decode base64 photo",
            exc_info=True,
            extra={"event_type": "photo_decode_failed"},
        )
        return None, f"Failed to decode photo data: {str(e)}"


def remove_exif_data(photo_bytes: bytes) -> bytes:
    """Remove EXIF metadata from photo using Pillow.

    Strips all EXIF metadata including GPS coordinates, camera info, etc.
    This protects user privacy by removing location and device information.

    Args:
        photo_bytes: Original photo bytes

    Returns:
        Photo bytes with EXIF removed
    """
    try:
        from PIL import Image

        # Open image from bytes
        image = Image.open(BytesIO(photo_bytes))

        # Create a new image without EXIF data
        # Get image data and create new image
        data = list(image.getdata())
        image_without_exif = Image.new(image.mode, image.size)
        image_without_exif.putdata(data)

        # Save to bytes
        output = BytesIO()
        # Preserve original format
        format_name = image.format or "JPEG"

        # Save without EXIF
        if format_name == "JPEG":
            image_without_exif.save(output, format="JPEG", quality=95)
        elif format_name == "PNG":
            image_without_exif.save(output, format="PNG", optimize=True)
        elif format_name == "WEBP":
            image_without_exif.save(output, format="WEBP", quality=95)
        else:
            # Default to JPEG
            image_without_exif.save(output, format="JPEG", quality=95)

        result_bytes = output.getvalue()

        logger.info(
            "EXIF data removed successfully",
            extra={
                "event_type": "exif_removal_success",
                "original_size": len(photo_bytes),
                "cleaned_size": len(result_bytes),
            },
        )

        return result_bytes

    except Exception as e:
        logger.warning(
            f"Failed to remove EXIF data: {e}",
            exc_info=True,
            extra={"event_type": "exif_removal_failed"},
        )
        # Return original bytes if EXIF removal fails
        return photo_bytes


def calculate_nsfw_score(photo_bytes: bytes) -> float:
    """Calculate NSFW score for photo using NudeNet ML model.

    Uses NudeNet classifier to detect NSFW content.
    The model classifies images into categories and returns a safety score.

    Args:
        photo_bytes: Photo bytes

    Returns:
        Safety score (0.0 = unsafe, 1.0 = safe)
    """
    try:
        import tempfile

        from nudenet import NudeClassifier
        from PIL import Image

        # Initialize classifier (cached after first use)
        if not hasattr(calculate_nsfw_score, "_classifier"):
            logger.info(
                "Initializing NudeNet classifier",
                extra={"event_type": "nsfw_model_init"},
            )
            calculate_nsfw_score._classifier = NudeClassifier()

        # Convert bytes to PIL Image for NudeNet
        image = Image.open(BytesIO(photo_bytes))

        # Save to temporary file (NudeNet requires file path)
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            image.save(tmp.name, format="JPEG")
            tmp_path = tmp.name

        try:
            # Classify image
            result = calculate_nsfw_score._classifier.classify(tmp_path)

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
            try:
                os.unlink(tmp_path)
            except:
                pass

    except ImportError:
        logger.warning(
            "NudeNet not available, falling back to permissive mode",
            extra={"event_type": "nsfw_detection_fallback"},
        )
        # Fallback to permissive if NudeNet not installed
        return 1.0

    except Exception as e:
        logger.error(
            f"NSFW detection failed: {e}",
            exc_info=True,
            extra={"event_type": "nsfw_detection_error"},
        )
        # On error, be permissive
        return 1.0


def generate_photo_filename(user_id: int, photo_hash: str, mime_type: str) -> str:
    """Generate unique filename for photo.

    Args:
        user_id: User ID
        photo_hash: Hash of photo content
        mime_type: MIME type

    Returns:
        Filename string
    """
    # Get file extension from MIME type
    ext_map = {
        "image/jpeg": "jpg",
        "image/jpg": "jpg",
        "image/png": "png",
        "image/webp": "webp",
    }
    ext = ext_map.get(mime_type, "jpg")

    return f"{user_id}_{photo_hash[:16]}.{ext}"


def save_photo_to_storage(
    photo_bytes: bytes, user_id: int, storage_path: str = "/tmp/dating_photos"
) -> str:
    """Save photo to local storage (mini-CDN).

    Args:
        photo_bytes: Photo bytes
        user_id: User ID
        storage_path: Base storage path

    Returns:
        Photo URL/path
    """
    # Calculate hash of photo content
    photo_hash = hashlib.sha256(photo_bytes).hexdigest()

    # Detect MIME type
    mime_type = detect_mime_type(photo_bytes)

    # Generate filename
    filename = generate_photo_filename(user_id, photo_hash, mime_type)

    # Create storage directory if not exists
    storage_dir = Path(storage_path)
    storage_dir.mkdir(parents=True, exist_ok=True)

    # Save file
    file_path = storage_dir / filename
    with open(file_path, "wb") as f:
        f.write(photo_bytes)

    logger.info(
        "Photo saved to storage",
        extra={
            "event_type": "photo_saved",
            "user_id": user_id,
            "photo_filename": filename,
            "size": len(photo_bytes),
        },
    )

    # Return URL (in production, this would be a CDN URL)
    return f"/photos/{filename}"


def validate_and_process_photo(
    base64_data: str, user_id: int, storage_path: str = "/tmp/dating_photos"
) -> dict:
    """Validate and process photo upload.

    This is the main function that orchestrates photo validation,
    EXIF removal, NSFW detection, and storage.

    Args:
        base64_data: Base64-encoded photo
        user_id: User ID
        storage_path: Storage path for photos

    Returns:
        Dictionary with photo metadata

    Raises:
        PhotoValidationError: If validation fails
    """
    # Decode base64
    photo_bytes, error = decode_base64_photo(base64_data)
    if error:
        raise PhotoValidationError(error)

    # Validate size
    is_valid, error = validate_photo_size(photo_bytes)
    if not is_valid:
        raise PhotoValidationError(error)

    # Detect and validate MIME type
    mime_type = detect_mime_type(photo_bytes)
    is_valid, error = validate_mime_type(mime_type)
    if not is_valid:
        raise PhotoValidationError(error)

    # Remove EXIF data
    photo_bytes = remove_exif_data(photo_bytes)

    # Calculate NSFW score
    safe_score = calculate_nsfw_score(photo_bytes)

    if safe_score < 0.7:
        raise PhotoValidationError("Photo contains inappropriate content")

    # Save to storage
    url = save_photo_to_storage(photo_bytes, user_id, storage_path)

    return {
        "url": url,
        "file_size": len(photo_bytes),
        "mime_type": mime_type,
        "safe_score": safe_score,
    }
