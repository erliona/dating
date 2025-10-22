"""Prometheus metrics middleware for request tracking."""

import logging
import time
from typing import Callable

from aiohttp import web

logger = logging.getLogger(__name__)


@web.middleware
async def metrics_middleware(request: web.Request, handler: Callable) -> web.Response:
    """
    Metrics collection middleware.
    
    Records request metrics for Prometheus.
    """
    # Get metrics collector from app
    metrics_collector = request.app.get('metrics_collector')
    
    if not metrics_collector:
        # No metrics collection configured
        return await handler(request)
    
    # Start timing
    start_time = time.time()
    
    # Increment active connections
    metrics_collector.increment_active_connections()
    
    try:
        # Process request
        response = await handler(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Record metrics
        metrics_collector.record_request(
            method=request.method,
            endpoint=request.path,
            status_code=response.status,
            duration=duration
        )
        
        return response
        
    except Exception as e:
        # Calculate duration for failed requests
        duration = time.time() - start_time
        
        # Record failed request metrics
        metrics_collector.record_request(
            method=request.method,
            endpoint=request.path,
            status_code=500,  # Internal server error
            duration=duration
        )
        
        # Re-raise the exception
        raise
        
    finally:
        # Decrement active connections
        metrics_collector.decrement_active_connections()
