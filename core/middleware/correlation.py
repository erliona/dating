"""Correlation ID middleware for request tracing and propagation."""
import uuid
import logging
from typing import Dict, Optional
from aiohttp import web

logger = logging.getLogger(__name__)

CORRELATION_ID_HEADER = "X-Correlation-ID"
REQUEST_ID_HEADER = "X-Request-ID"


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
            extra={
                "correlation_id": correlation_id,
                "service": request.app.get('service_name', 'unknown'),
                "path": request.path,
                "method": request.method
            }
        )
    else:
        logger.debug(
            f"Using existing correlation ID: {correlation_id}",
            extra={
                "correlation_id": correlation_id,
                "service": request.app.get('service_name', 'unknown'),
                "path": request.path,
                "method": request.method
            }
        )
    
    # Store in request
    request["correlation_id"] = correlation_id
    
    # Process request
    response = await handler(request)
    
    # Add correlation ID to response headers
    response.headers[CORRELATION_ID_HEADER] = correlation_id
    
    return response


def get_correlation_id(request: web.Request) -> str:
    """Get correlation ID from request."""
    return request.get("correlation_id", "unknown")


def create_headers_with_correlation(request: web.Request, additional_headers: Optional[Dict[str, str]] = None) -> Dict[str, str]:
    """
    Create headers for inter-service calls with correlation ID propagation.
    
    Args:
        request: Current request object
        additional_headers: Additional headers to include
        
    Returns:
        Dictionary of headers with correlation ID
    """
    headers = {}
    
    # Add correlation ID
    correlation_id = get_correlation_id(request)
    if correlation_id != "unknown":
        headers[CORRELATION_ID_HEADER] = correlation_id
    
    # Add request ID if available
    request_id = request.get("request_id")
    if request_id:
        headers[REQUEST_ID_HEADER] = request_id
    
    # Add additional headers
    if additional_headers:
        headers.update(additional_headers)
    
    return headers


def log_correlation_propagation(
    correlation_id: str,
    from_service: str,
    to_service: str,
    operation: str,
    request: web.Request
) -> None:
    """
    Log correlation ID propagation for tracing.
    
    Args:
        correlation_id: The correlation ID being propagated
        from_service: Source service name
        to_service: Target service name
        operation: Operation being performed
        request: Current request object
    """
    logger.info(
        f"Correlation ID propagation: {from_service} -> {to_service}",
        extra={
            "event_type": "correlation_propagation",
            "correlation_id": correlation_id,
            "from_service": from_service,
            "to_service": to_service,
            "operation": operation,
            "request_id": request.get("request_id"),
            "user_id": request.get("user_id"),
            "path": request.path,
            "method": request.method
        }
    )
