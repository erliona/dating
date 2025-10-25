from __future__ import annotations

"""Media service main entry point.

This microservice handles photo/video upload, validation, and optimization.
"""

import logging
import os
import mimetypes
import hashlib
import uuid
from pathlib import Path
from typing import Optional

from aiohttp import web

from core.utils.logging import configure_logging
from core.middleware.jwt_middleware import jwt_middleware
from core.middleware.request_logging import request_logging_middleware, user_context_middleware
from core.middleware.metrics_middleware import metrics_middleware, add_metrics_route
from core.middleware.security_metrics import record_file_upload, record_suspicious_activity
from core.middleware.audit_logging import audit_log, log_security_event
from core.metrics.business_metrics import NSFW_DETECTION_TOTAL, NSFW_BLOCKED_TOTAL
from .minio_client import minio_client
from .image_processor import image_processor
from core.middleware.error_handling import setup_error_handling

logger = logging.getLogger(__name__)


async def queue_for_moderation(
    content_type: str,
    content_id: str,
    user_id: str,
    reason: str = "upload",
    priority: int = 1
) -> None:
    """Queue content for moderation via data service."""
    try:
        import aiohttp
        
        data_service_url = os.getenv("DATA_SERVICE_URL", "http://data-service:8088")
        url = f"{data_service_url}/moderation/queue"
        
        payload = {
            "content_type": content_type,
            "content_id": content_id,
            "user_id": user_id,
            "reason": reason,
            "priority": priority
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                if response.status not in [200, 201]:
                    error_text = await response.text()
                    logger.error(f"Failed to queue moderation: {response.status} - {error_text}")
                    raise Exception(f"Moderation queue failed: {response.status}")
                    
    except Exception as e:
        logger.error(f"Error queuing for moderation: {e}")
        raise

# Security configuration
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
ALLOWED_MIME_TYPES = {
    'image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp'
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_FILENAME_LENGTH = 255


def validate_file_extension(filename: str) -> bool:
    """Validate file extension."""
    if not filename:
        return False
    
    ext = Path(filename).suffix.lower()
    return ext in ALLOWED_EXTENSIONS


def validate_mime_type(content_type: str) -> bool:
    """Validate MIME type."""
    if not content_type:
        return False
    
    # Extract main MIME type (ignore parameters like charset)
    main_type = content_type.split(';')[0].strip().lower()
    return main_type in ALLOWED_MIME_TYPES


def validate_file_size(size: int) -> bool:
    """Validate file size."""
    return 0 < size <= MAX_FILE_SIZE


def sanitize_filename(filename: str) -> str:
    """Sanitize filename to prevent path traversal."""
    if not filename:
        return "upload"
    
    # Remove path separators and dangerous characters
    filename = os.path.basename(filename)
    filename = "".join(c for c in filename if c.isalnum() or c in "._-")
    
    # Limit length
    if len(filename) > MAX_FILENAME_LENGTH:
        name, ext = os.path.splitext(filename)
        filename = name[:MAX_FILENAME_LENGTH - len(ext)] + ext
    
    return filename or "upload"


def detect_nsfw_content(filepath: Path) -> bool:
    """Basic NSFW detection (placeholder for real implementation)."""
    # TODO: Implement real NSFW detection using ML model
    # For now, just check file size and basic properties
    try:
        if filepath.stat().st_size == 0:
            return True  # Empty files are suspicious
        return False
    except Exception:
        return True  # If we can't check, assume it's suspicious


def calculate_file_hash(filepath: Path) -> str:
    """Calculate SHA-256 hash of file for deduplication."""
    sha256_hash = hashlib.sha256()
    try:
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception:
        return ""


async def upload_media(request: web.Request) -> web.Response:
    """Upload media file with security validation.

    POST /media/upload
    Content-Type: multipart/form-data
    """
    try:
        reader = await request.multipart()
        field = await reader.next()

        if not field or field.name != "file":
            return web.json_response({"error": "No file provided"}, status=400)

        # SECURITY: Validate filename
        original_filename = field.filename or "upload"
        if not validate_file_extension(original_filename):
            logger.warning(f"Invalid file extension: {original_filename}")
            record_file_upload(
                service="media-service",
                result="blocked",
                file_type=Path(original_filename).suffix.lower(),
                reason="invalid_extension",
                user_id=str(request.get("user_id", "unknown"))
            )
            return web.json_response({"error": "Invalid file type"}, status=400)

        # SECURITY: Validate MIME type
        content_type = field.headers.get('Content-Type', '')
        if not validate_mime_type(content_type):
            logger.warning(f"Invalid MIME type: {content_type}")
            record_file_upload(
                service="media-service",
                result="blocked",
                file_type=Path(original_filename).suffix.lower(),
                reason="invalid_mime_type",
                user_id=str(request.get("user_id", "unknown"))
            )
            return web.json_response({"error": "Invalid file type"}, status=400)

        # SECURITY: Generate secure filename
        file_id = str(uuid.uuid4())
        sanitized_filename = sanitize_filename(original_filename)
        ext = Path(sanitized_filename).suffix or ".jpg"
        object_name = f"{file_id}{ext}"

        # Read file data
        file_data = b""
        size = 0
        while True:
            chunk = await field.read_chunk()
            if not chunk:
                break
            file_data += chunk
            size += len(chunk)
            
        # SECURITY: Check file size during upload
        if not validate_file_size(size):
            logger.warning(f"File too large: {size} bytes")
            record_file_upload(
                service="media-service",
                result="blocked",
                file_type=ext,
                reason="file_too_large",
                user_id=str(request.get("user_id", "unknown")),
                file_size=size
            )
            return web.json_response({"error": "File too large"}, status=413)

        # SECURITY: Validate image format and size
        if not image_processor.validate_image(file_data):
            logger.warning(f"Invalid image: {original_filename}")
            record_file_upload(
                service="media-service",
                result="blocked",
                file_type=ext,
                reason="invalid_image",
                user_id=str(request.get("user_id", "unknown")),
                file_size=size
            )
            return web.json_response({"error": "Invalid image format or size"}, status=400)

        # SECURITY: NSFW detection using image processor
        if image_processor.detect_nsfw_content(file_data):
            logger.warning(f"Potential NSFW content detected: {original_filename}")
            record_file_upload(
                service="media-service",
                result="blocked",
                file_type=ext,
                reason="nsfw_detected",
                user_id=str(request.get("user_id", "unknown")),
                file_size=size
            )
            return web.json_response({"error": "Content not allowed"}, status=400)

        # Extract EXIF data for logging (before stripping)
        exif_data = image_processor.extract_exif_data(file_data)
        if exif_data:
            logger.info(f"EXIF data extracted: {list(exif_data.keys())}")

        # Process image with enhanced pipeline
        try:
            processed_data, thumbnail_data = image_processor.process_image(file_data, create_thumbnail=True)
            
            # Get image info
            image_info = image_processor.get_image_info(processed_data)
            logger.info(f"Processed image: {image_info}")
            
            # Upload to MinIO
            await minio_client.upload_file(
                bucket="photos",
                object_name=object_name,
                file_data=processed_data,
                content_type="image/jpeg"  # Always JPEG after processing
            )
            
            # Upload thumbnail if created
            if thumbnail_data:
                thumbnail_name = f"thumb_{file_id}{ext}"
                await minio_client.upload_file(
                    bucket="thumbnails",
                    object_name=thumbnail_name,
                    file_data=thumbnail_data,
                    content_type="image/jpeg"
                )
            
        except Exception as e:
            logger.error(f"Image processing failed: {e}")
            return web.json_response({"error": "Image processing failed"}, status=500)

        # Calculate file hash for deduplication
        file_hash = hashlib.sha256(processed_data).hexdigest()

        # Record NSFW detection for safe files
        NSFW_DETECTION_TOTAL.labels(
            service='media-service',
            result='safe'
        ).inc()
        
        # Record successful file upload
        record_file_upload(
            service="media-service",
            result="success",
            file_type=ext,
            user_id=str(request.get("user_id", "unknown")),
            file_size=size,
            file_id=file_id
        )
        
        # Audit log file upload
        audit_log(
            operation="file_upload",
            user_id=str(request.get("user_id", "unknown")),
            service="media-service",
            details={
                "file_id": file_id,
                "filename": sanitized_filename,
                "file_size": size,
                "file_type": ext,
                "file_hash": file_hash,
                "content_type": content_type
            },
            request=request
        )

        # Auto-queue for moderation
        try:
            await queue_for_moderation(
                content_type="photo",
                content_id=file_id,
                user_id=str(request.get("user_id", "unknown")),
                reason="upload",
                priority=1
            )
            logger.info(f"Photo {file_id} queued for moderation")
        except Exception as e:
            logger.error(f"Failed to queue photo for moderation: {e}")
            # Don't fail the upload if moderation queueing fails

        logger.info(
            f"File uploaded successfully",
            extra={
                "event_type": "file_uploaded",
                "file_id": file_id,
                "size": size,
                "hash": file_hash,
                "user_id": request.get("user_id")
            }
        )

        return web.json_response(
            {
                "file_id": file_id,
                "filename": sanitized_filename,
                "size": size,
                "hash": file_hash,
                "url": f"/media/{file_id}",
            },
            status=201,
        )

    except Exception as e:
        logger.error(f"Error uploading media: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def get_media(request: web.Request) -> web.Response:
    """Get media file with security validation.

    GET /media/{file_id}
    """
    try:
        file_id = request.match_info["file_id"]
        
        # SECURITY: Validate file_id format (UUID)
        try:
            uuid.UUID(file_id)
        except ValueError:
            logger.warning(f"Invalid file_id format: {file_id}")
            return web.json_response({"error": "Invalid file ID"}, status=400)

        # Find file with allowed extensions only
        for ext in ALLOWED_EXTENSIONS:
            object_name = f"{file_id}{ext}"
            
            # Check if file exists in MinIO
            if await minio_client.file_exists("photos", object_name):
                try:
                    # Download file from MinIO
                    file_data = await minio_client.download_file("photos", object_name)
                    
                    # Set appropriate headers
                    headers = {
                        'Content-Type': mimetypes.guess_type(object_name)[0] or 'application/octet-stream',
                        'Cache-Control': 'public, max-age=3600',  # Cache for 1 hour
                        'X-Content-Type-Options': 'nosniff',
                    }
                    
                    return web.Response(body=file_data, headers=headers)
                    
                except Exception as e:
                    logger.error(f"Error downloading from MinIO: {e}")
                    return web.json_response({"error": "Failed to retrieve file"}, status=500)

        return web.json_response({"error": "File not found"}, status=404)

    except Exception as e:
        logger.error(f"Error getting media: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def delete_media(request: web.Request) -> web.Response:
    """Delete media file with security validation.

    DELETE /media/{file_id}
    """
    try:
        file_id = request.match_info["file_id"]
        
        # SECURITY: Validate file_id format (UUID)
        try:
            uuid.UUID(file_id)
        except ValueError:
            logger.warning(f"Invalid file_id format: {file_id}")
            return web.json_response({"error": "Invalid file ID"}, status=400)

        # Find and delete file with allowed extensions only
        deleted = False
        for ext in ALLOWED_EXTENSIONS:
            object_name = f"{file_id}{ext}"
            thumbnail_name = f"thumb_{file_id}{ext}"
            
            # Delete main file from MinIO
            if await minio_client.file_exists("photos", object_name):
                await minio_client.delete_file("photos", object_name)
                deleted = True
                
            # Delete thumbnail from MinIO
            if await minio_client.file_exists("thumbnails", thumbnail_name):
                await minio_client.delete_file("thumbnails", thumbnail_name)
                
            if deleted:
                logger.info(
                    f"File deleted successfully",
                    extra={
                        "event_type": "file_deleted",
                        "file_id": file_id,
                        "user_id": request.get("user_id")
                    }
                )
                break

        if not deleted:
            return web.json_response({"error": "File not found"}, status=404)

        return web.json_response({"success": True})

    except Exception as e:
        logger.error(f"Error deleting media: {e}", exc_info=True)
        return web.json_response({"error": "Internal server error"}, status=500)


async def health_check(request: web.Request) -> web.Response:
    """Health check endpoint."""
    return web.json_response({"status": "healthy", "service": "media"})


def create_app(config: dict) -> web.Application:
    """Create and configure the media service application."""
    app = web.Application()
    
    # Setup error handling
    setup_error_handling(app, \"media-service")
    app["config"] = config
    
    # Add middleware
    # Setup standard middleware stack
    from core.middleware.standard_stack import setup_standard_middleware_stack
    setup_standard_middleware_stack(app, "media-service", use_auth=True, use_audit=True)
    
    # Add metrics endpoint
    add_metrics_route(app, "media-service")

    # Add routes
    app.router.add_post("/media/upload", upload_media)
    app.router.add_get("/media/{file_id}", get_media)
    app.router.add_delete("/media/{file_id}", delete_media)
    app.router.add_get("/health", health_check)

    return app


if __name__ == "__main__":
    # Configure structured logging
    configure_logging("media-service", os.getenv("LOG_LEVEL", "INFO"))

    config = {
        "jwt_secret": os.getenv("JWT_SECRET"),  # SECURITY: No default value
        "storage_path": os.getenv("PHOTO_STORAGE_PATH", "/app/photos"),
        "host": os.getenv("MEDIA_SERVICE_HOST", "0.0.0.0"),
        "port": int(os.getenv("MEDIA_SERVICE_PORT", 8084)),
    }

    logger.info(
        "Starting media-service",
        extra={"event_type": "service_start", "port": config["port"]},
    )

    app = create_app(config)
    web.run_app(app, host=config["host"], port=config["port"])
