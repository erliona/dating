from __future__ import annotations

"""Distributed tracing middleware for W3C Trace Context support."""

import logging
import uuid

from aiohttp import web

logger = logging.getLogger(__name__)

# W3C Trace Context headers
TRACEPARENT_HEADER = "traceparent"
TRACESTATE_HEADER = "tracestate"

# Custom headers for internal tracing
TRACE_ID_HEADER = "X-Trace-ID"
SPAN_ID_HEADER = "X-Span-ID"
PARENT_SPAN_ID_HEADER = "X-Parent-Span-ID"


class TraceContext:
    """Trace context for distributed tracing."""

    def __init__(self, trace_id: str, span_id: str, parent_span_id: str | None = None):
        self.trace_id = trace_id
        self.span_id = span_id
        self.parent_span_id = parent_span_id

    def to_headers(self) -> dict[str, str]:
        """Convert trace context to HTTP headers."""
        headers = {
            TRACE_ID_HEADER: self.trace_id,
            SPAN_ID_HEADER: self.span_id,
        }

        if self.parent_span_id:
            headers[PARENT_SPAN_ID_HEADER] = self.parent_span_id

        # W3C Trace Context format: 00-{trace_id}-{span_id}-{trace_flags}
        traceparent = f"00-{self.trace_id}-{self.span_id}-01"
        headers[TRACEPARENT_HEADER] = traceparent

        return headers

    @classmethod
    def from_headers(cls, headers: dict[str, str]) -> TraceContext:
        """Create trace context from HTTP headers."""
        # Try to get from custom headers first
        trace_id = headers.get(TRACE_ID_HEADER)
        span_id = headers.get(SPAN_ID_HEADER)
        parent_span_id = headers.get(PARENT_SPAN_ID_HEADER)

        # Fallback to W3C Trace Context
        if not trace_id or not span_id:
            traceparent = headers.get(TRACEPARENT_HEADER)
            if traceparent:
                parts = traceparent.split("-")
                if len(parts) >= 3:
                    trace_id = parts[1]
                    span_id = parts[2]

        # Generate new IDs if not found
        if not trace_id:
            trace_id = str(uuid.uuid4()).replace("-", "")
        if not span_id:
            span_id = str(uuid.uuid4()).replace("-", "")[:16]

        return cls(trace_id, span_id, parent_span_id)

    def create_child_span(self) -> TraceContext:
        """Create a child span context."""
        new_span_id = str(uuid.uuid4()).replace("-", "")[:16]
        return TraceContext(self.trace_id, new_span_id, self.span_id)


@web.middleware
async def tracing_middleware(request: web.Request, handler):
    """
    Middleware for distributed tracing with W3C Trace Context support.

    Extracts or generates trace context and adds it to request and logs.
    """
    # Extract or generate trace context
    trace_context = TraceContext.from_headers(dict(request.headers))

    # Store in request for use by other middleware and handlers
    request["trace_context"] = trace_context
    request["trace_id"] = trace_context.trace_id
    request["span_id"] = trace_context.span_id
    request["parent_span_id"] = trace_context.parent_span_id

    # Log trace context
    logger.debug(
        f"Trace context: {trace_context.trace_id} -> {trace_context.span_id}",
        extra={
            "event_type": "trace_start",
            "trace_id": trace_context.trace_id,
            "span_id": trace_context.span_id,
            "parent_span_id": trace_context.parent_span_id,
            "service": request.app.get("service_name", "unknown"),
            "path": request.path,
            "method": request.method,
        },
    )

    # Process request
    response = await handler(request)

    # Add trace context to response headers
    trace_headers = trace_context.to_headers()
    for header, value in trace_headers.items():
        response.headers[header] = value

    # Log trace completion
    logger.debug(
        f"Trace completed: {trace_context.trace_id} -> {trace_context.span_id}",
        extra={
            "event_type": "trace_complete",
            "trace_id": trace_context.trace_id,
            "span_id": trace_context.span_id,
            "parent_span_id": trace_context.parent_span_id,
            "service": request.app.get("service_name", "unknown"),
            "path": request.path,
            "method": request.method,
            "status_code": response.status,
        },
    )

    return response


def get_trace_context(request: web.Request) -> TraceContext | None:
    """Get trace context from request."""
    return request.get("trace_context")


def create_headers_with_trace(
    request: web.Request, additional_headers: dict[str, str] | None = None
) -> dict[str, str]:
    """
    Create headers for inter-service calls with trace context propagation.

    Args:
        request: Current request object
        additional_headers: Additional headers to include

    Returns:
        Dictionary of headers with trace context
    """
    headers = {}

    # Add trace context headers
    trace_context = get_trace_context(request)
    if trace_context:
        # Create child span for the outgoing call
        child_context = trace_context.create_child_span()
        headers.update(child_context.to_headers())

    # Add additional headers
    if additional_headers:
        headers.update(additional_headers)

    return headers


def log_trace_propagation(
    trace_id: str,
    span_id: str,
    from_service: str,
    to_service: str,
    operation: str,
    request: web.Request,
) -> None:
    """
    Log trace propagation for distributed tracing.

    Args:
        trace_id: The trace ID being propagated
        span_id: The span ID for this operation
        from_service: Source service name
        to_service: Target service name
        operation: Operation being performed
        request: Current request object
    """
    logger.info(
        f"Trace propagation: {from_service} -> {to_service}",
        extra={
            "event_type": "trace_propagation",
            "trace_id": trace_id,
            "span_id": span_id,
            "from_service": from_service,
            "to_service": to_service,
            "operation": operation,
            "request_id": request.get("request_id"),
            "correlation_id": request.get("correlation_id"),
            "user_id": request.get("user_id"),
            "path": request.path,
            "method": request.method,
        },
    )
