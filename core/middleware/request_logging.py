"""Request logging middleware for structured logging and tracing."""

import logging
import time
import uuid
from typing import Callable

from aiohttp import web

logger = logging.getLogger(__name__)


@web.middleware
async def request_logging_middleware(request: web.Request, handler: Callable) -> web.Response:
    """
    Request logging middleware.
    
    Adds request_id for tracing, logs request/response details,
    and measures request duration.
    """
    # Generate unique request ID
    request_id = str(uuid.uuid4())
    request['request_id'] = request_id
    
    # Start timing
    start_time = time.time()
    
    # Log request
    logger.info(
        f"Request started: {request.method} {request.path}",
        extra={
            "event_type": "request_started",
            "request_id": request_id,
            "method": request.method,
            "path": request.path,
            "user_agent": request.headers.get("User-Agent", ""),
            "remote": request.remote,
        }
    )
    
    try:
        # Process request
        response = await handler(request)
        
        # Calculate duration
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log successful response
        logger.info(
            f"Request completed: {request.method} {request.path} -> {response.status}",
            extra={
                "event_type": "request_completed",
                "request_id": request_id,
                "method": request.method,
                "path": request.path,
                "status_code": response.status,
                "duration_ms": duration_ms,
            }
        )
        
        # Add request_id to response headers for debugging
        response.headers['X-Request-ID'] = request_id
        
        return response
        
    except Exception as e:
        # Calculate duration for failed requests
        duration_ms = int((time.time() - start_time) * 1000)
        
        # Log failed request
        logger.error(
            f"Request failed: {request.method} {request.path} -> {type(e).__name__}: {e}",
            exc_info=True,
            extra={
                "event_type": "request_failed",
                "request_id": request_id,
                "method": request.method,
                "path": request.path,
                "duration_ms": duration_ms,
                "error_type": type(e).__name__,
                "error_message": str(e),
            }
        )
        
        # Re-raise the exception
        raise
