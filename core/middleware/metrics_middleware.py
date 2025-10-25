from __future__ import annotations

"""Prometheus metrics middleware for application services."""

import time
from collections.abc import Callable

from aiohttp import web
from prometheus_client import Counter, Gauge, Histogram, generate_latest

# Prometheus metrics
REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total HTTP requests",
    ["method", "endpoint", "status_code", "service"],
)

REQUEST_DURATION = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "endpoint", "service"],
    buckets=(
        0.01,
        0.025,
        0.05,
        0.075,
        0.1,
        0.25,
        0.5,
        0.75,
        1.0,
        2.5,
        5.0,
        7.5,
        10.0,
        float("inf"),
    ),
)

ACTIVE_REQUESTS = Gauge(
    "http_requests_active", "Number of active HTTP requests", ["service"]
)

# Business metrics moved to core.metrics.business_metrics
# Import them if needed for backward compatibility


@web.middleware
async def metrics_middleware(request: web.Request, handler: Callable) -> web.Response:
    """
    Middleware for Prometheus metrics collection.

    Collects request metrics: count, duration, active requests.
    """
    service_name = request.app.get("service_name", "unknown")

    # Increment active requests
    ACTIVE_REQUESTS.labels(service=service_name).inc()

    # Start timing
    start_time = time.time()

    try:
        # Process request
        response = await handler(request)

        # Calculate duration
        duration = time.time() - start_time

        # Record metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.path,
            status_code=response.status,
            service=service_name,
        ).inc()

        REQUEST_DURATION.labels(
            method=request.method, endpoint=request.path, service=service_name
        ).observe(duration)

        return response

    except Exception:
        # Calculate duration for failed requests
        duration = time.time() - start_time

        # Record error metrics
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.path,
            status_code=500,
            service=service_name,
        ).inc()

        REQUEST_DURATION.labels(
            method=request.method, endpoint=request.path, service=service_name
        ).observe(duration)

        # Re-raise the exception
        raise

    finally:
        # Decrement active requests
        ACTIVE_REQUESTS.labels(service=service_name).dec()


async def metrics_handler(request: web.Request) -> web.Response:
    """Handler for /metrics endpoint."""
    metrics_data = generate_latest()
    return web.Response(body=metrics_data, content_type="text/plain; version=0.0.4")


def add_metrics_route(app: web.Application, service_name: str) -> None:
    """Add metrics endpoint to application."""
    app["service_name"] = service_name
    app.router.add_get("/metrics", metrics_handler)
