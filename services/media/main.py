"""Media service main entry point.

This microservice handles photo/video upload, validation, and optimization.
"""

import logging
import os
import mimetypes
import hashlib
from pathlib import Path
from typing import Optional

from aiohttp import web

from core.utils.logging import configure_logging
from core.middleware.jwt_middleware import jwt_middleware
from core.middleware.request_logging import request_logging_middleware, user_context_middleware
from core.middleware.metrics_middleware import metrics_middleware, add_metrics_route
from core.middleware.security_metrics import record_file_upload, record_suspicious_activity

logger = logging.getLogger(__name__)

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

        # Get storage path from config
        storage_path = request.app["config"].get("storage_path", "/app/photos")
        storage_path = Path(storage_path).resolve()  # SECURITY: Resolve to absolute path
        storage_path.mkdir(parents=True, exist_ok=True)

        # SECURITY: Generate secure filename
        import uuid
        file_id = str(uuid.uuid4())
        sanitized_filename = sanitize_filename(original_filename)
        ext = Path(sanitized_filename).suffix or ".jpg"
        filepath = storage_path / f"{file_id}{ext}"

        # SECURITY: Validate filepath is within storage directory
        try:
            filepath.resolve().relative_to(storage_path.resolve())
        except ValueError:
            logger.error(f"Path traversal attempt: {filepath}")
            return web.json_response({"error": "Invalid file path"}, status=400)

        # Save file with size validation
        size = 0
        with open(filepath, "wb") as f:
            while True:
                chunk = await field.read_chunk()
                if not chunk:
                    break
                
                size += len(chunk)
                
        # SECURITY: Check file size during upload
        if not validate_file_size(size):
            f.close()
            filepath.unlink(missing_ok=True)  # Clean up partial file
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
                
                f.write(chunk)

        # SECURITY: Additional validation after upload
        if not validate_file_size(size):
            filepath.unlink(missing_ok=True)
            return web.json_response({"error": "File too large"}, status=413)

        # SECURITY: NSFW detection
        if detect_nsfw_content(filepath):
            filepath.unlink(missing_ok=True)
            logger.warning(f"NSFW content detected in file: {file_id}")
            record_file_upload(
                service="media-service",
                result="blocked",
                file_type=ext,
                reason="nsfw_content",
                user_id=str(request.get("user_id", "unknown"))
            )
            record_suspicious_activity(
                service="media-service",
                activity_type="nsfw_upload_attempt",
                severity="high",
                user_id=str(request.get("user_id", "unknown")),
                file_id=file_id
            )
            return web.json_response({"error": "Content not allowed"}, status=400)

        # Calculate file hash for deduplication
        file_hash = calculate_file_hash(filepath)

        # Record successful file upload
        record_file_upload(
            service="media-service",
            result="success",
            file_type=ext,
            user_id=str(request.get("user_id", "unknown")),
            file_size=size,
            file_id=file_id
        )

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
        import uuid
        try:
            uuid.UUID(file_id)
        except ValueError:
            logger.warning(f"Invalid file_id format: {file_id}")
            return web.json_response({"error": "Invalid file ID"}, status=400)

        storage_path = request.app["config"].get("storage_path", "/app/photos")
        storage_path = Path(storage_path).resolve()  # SECURITY: Resolve to absolute path

        # Find file with allowed extensions only
        for ext in ALLOWED_EXTENSIONS:
            filepath = storage_path / f"{file_id}{ext}"
            
            # SECURITY: Validate filepath is within storage directory
            try:
                filepath.resolve().relative_to(storage_path.resolve())
            except ValueError:
                logger.error(f"Path traversal attempt: {filepath}")
                return web.json_response({"error": "Invalid file path"}, status=400)
            
            if filepath.exists() and filepath.is_file():
                # SECURITY: Set appropriate headers
                headers = {
                    'Content-Type': mimetypes.guess_type(str(filepath))[0] or 'application/octet-stream',
                    'Cache-Control': 'public, max-age=3600',  # Cache for 1 hour
                    'X-Content-Type-Options': 'nosniff',
                }
                return web.FileResponse(filepath, headers=headers)

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
        import uuid
        try:
            uuid.UUID(file_id)
        except ValueError:
            logger.warning(f"Invalid file_id format: {file_id}")
            return web.json_response({"error": "Invalid file ID"}, status=400)

        storage_path = request.app["config"].get("storage_path", "/app/photos")
        storage_path = Path(storage_path).resolve()  # SECURITY: Resolve to absolute path

        # Find and delete file with allowed extensions only
        deleted = False
        for ext in ALLOWED_EXTENSIONS:
            filepath = storage_path / f"{file_id}{ext}"
            
            # SECURITY: Validate filepath is within storage directory
            try:
                filepath.resolve().relative_to(storage_path.resolve())
            except ValueError:
                logger.error(f"Path traversal attempt: {filepath}")
                return web.json_response({"error": "Invalid file path"}, status=400)
            
            if filepath.exists() and filepath.is_file():
                filepath.unlink()
                deleted = True
                
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
    app["config"] = config
    
    # Add middleware
    app.middlewares.append(user_context_middleware)
    app.middlewares.append(request_logging_middleware)
    app.middlewares.append(metrics_middleware)
    app.middlewares.append(jwt_middleware)
    
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
        "jwt_secret": os.getenv("JWT_SECRET", "your-secret-key"),
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
