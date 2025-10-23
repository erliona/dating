"""Correlation ID middleware for request tracing."""
import uuid
import logging
from aiohttp import web

logger = logging.getLogger(__name__)

CORRELATION_ID_HEADER = "X-Correlation-ID"


@web.middleware
async def correlation_middleware(request: web.Request, handler):
    """Generate or extract correlation ID for request tracing."""
    # Try to get correlation ID from header
    correlation_id = request.headers.get(CORRELATION_ID_HEADER)
    
    # Generate new ID if not present
    if not correlation_id:
        correlation_id = str(uuid.uuid4())
        logger.debug(
            f"Generated new correlation ID: {correlation_id}",
            extra={"correlation_id": correlation_id}
        )
    
    # Store in request
    request["correlation_id"] = correlation_id
    
    # Add to response headers
    response = await handler(request)
    response.headers[CORRELATION_ID_HEADER] = correlation_id
    
    return response


def get_correlation_id(request: web.Request) -> str:
    """Get correlation ID from request."""
    return request.get("correlation_id", "unknown")
