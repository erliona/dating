"""Prometheus metrics utilities for application services."""

import logging
import time
from typing import Dict, Optional

from aiohttp import web

logger = logging.getLogger(__name__)

# Prometheus metrics (will be imported when prometheus_client is available)
try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Dummy classes for when prometheus_client is not available
    class Counter:
        def __init__(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    
    class Histogram:
        def __init__(self, *args, **kwargs): pass
        def observe(self, *args, **kwargs): pass
        def time(self): return self
        def __enter__(self): return self
        def __exit__(self, *args): pass
    
    class Gauge:
        def __init__(self, *args, **kwargs): pass
        def set(self, *args, **kwargs): pass
        def inc(self, *args, **kwargs): pass
        def dec(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self


# Application metrics
REQUEST_COUNT = Counter(
    'http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status_code', 'service']
)

REQUEST_DURATION = Histogram(
    'http_request_duration_seconds',
    'HTTP request duration in seconds',
    ['method', 'endpoint', 'service']
)

ACTIVE_CONNECTIONS = Gauge(
    'http_active_connections',
    'Number of active HTTP connections',
    ['service']
)

BUSINESS_EVENTS = Counter(
    'business_events_total',
    'Total business events',
    ['event_type', 'service']
)

DATABASE_OPERATIONS = Counter(
    'database_operations_total',
    'Total database operations',
    ['operation', 'table', 'service']
)

DATABASE_DURATION = Histogram(
    'database_operation_duration_seconds',
    'Database operation duration in seconds',
    ['operation', 'table', 'service']
)

# Service-specific metrics
USER_REGISTRATIONS = Counter(
    'user_registrations_total',
    'Total user registrations',
    ['service']
)

USER_LOGINS = Counter(
    'user_logins_total',
    'Total user logins',
    ['service']
)

MATCHES_CREATED = Counter(
    'matches_created_total',
    'Total matches created',
    ['service']
)

MESSAGES_SENT = Counter(
    'messages_sent_total',
    'Total messages sent',
    ['service']
)

PHOTOS_UPLOADED = Counter(
    'photos_uploaded_total',
    'Total photos uploaded',
    ['service']
)

NOTIFICATIONS_SENT = Counter(
    'notifications_sent_total',
    'Total notifications sent',
    ['notification_type', 'service']
)


class MetricsCollector:
    """Metrics collector for application services."""
    
    def __init__(self, service_name: str):
        self.service_name = service_name
        self.active_connections = 0
    
    def record_request(self, method: str, endpoint: str, status_code: int, duration: float):
        """Record HTTP request metrics."""
        if not PROMETHEUS_AVAILABLE:
            return
            
        REQUEST_COUNT.labels(
            method=method,
            endpoint=endpoint,
            status_code=status_code,
            service=self.service_name
        ).inc()
        
        REQUEST_DURATION.labels(
            method=method,
            endpoint=endpoint,
            service=self.service_name
        ).observe(duration)
    
    def record_business_event(self, event_type: str):
        """Record business event."""
        if not PROMETHEUS_AVAILABLE:
            return
            
        BUSINESS_EVENTS.labels(
            event_type=event_type,
            service=self.service_name
        ).inc()
    
    def record_database_operation(self, operation: str, table: str, duration: float):
        """Record database operation metrics."""
        if not PROMETHEUS_AVAILABLE:
            return
            
        DATABASE_OPERATIONS.labels(
            operation=operation,
            table=table,
            service=self.service_name
        ).inc()
        
        DATABASE_DURATION.labels(
            operation=operation,
            table=table,
            service=self.service_name
        ).observe(duration)
    
    def increment_active_connections(self):
        """Increment active connections counter."""
        if not PROMETHEUS_AVAILABLE:
            return
            
        self.active_connections += 1
        ACTIVE_CONNECTIONS.labels(service=self.service_name).set(self.active_connections)
    
    def decrement_active_connections(self):
        """Decrement active connections counter."""
        if not PROMETHEUS_AVAILABLE:
            return
            
        self.active_connections = max(0, self.active_connections - 1)
        ACTIVE_CONNECTIONS.labels(service=self.service_name).set(self.active_connections)
    
    def record_user_registration(self):
        """Record user registration."""
        if not PROMETHEUS_AVAILABLE:
            return
            
        USER_REGISTRATIONS.labels(service=self.service_name).inc()
    
    def record_user_login(self):
        """Record user login."""
        if not PROMETHEUS_AVAILABLE:
            return
            
        USER_LOGINS.labels(service=self.service_name).inc()
    
    def record_match_created(self):
        """Record match creation."""
        if not PROMETHEUS_AVAILABLE:
            return
            
        MATCHES_CREATED.labels(service=self.service_name).inc()
    
    def record_message_sent(self):
        """Record message sent."""
        if not PROMETHEUS_AVAILABLE:
            return
            
        MESSAGES_SENT.labels(service=self.service_name).inc()
    
    def record_photo_uploaded(self):
        """Record photo upload."""
        if not PROMETHEUS_AVAILABLE:
            return
            
        PHOTOS_UPLOADED.labels(service=self.service_name).inc()
    
    def record_notification_sent(self, notification_type: str):
        """Record notification sent."""
        if not PROMETHEUS_AVAILABLE:
            return
            
        NOTIFICATIONS_SENT.labels(
            notification_type=notification_type,
            service=self.service_name
        ).inc()


def create_metrics_collector(service_name: str) -> MetricsCollector:
    """Create a metrics collector instance."""
    return MetricsCollector(service_name)


async def metrics_endpoint(request: web.Request) -> web.Response:
    """Prometheus metrics endpoint."""
    if not PROMETHEUS_AVAILABLE:
        return web.json_response({
            "error": "Prometheus client not available",
            "message": "Install prometheus_client package to enable metrics"
        }, status=503)
    
    metrics_data = generate_latest()
    return web.Response(
        body=metrics_data,
        content_type=CONTENT_TYPE_LATEST
    )


def setup_metrics_middleware(app: web.Application, service_name: str):
    """Setup metrics collection middleware."""
    if not PROMETHEUS_AVAILABLE:
        logger.warning("Prometheus client not available, metrics disabled")
        return
    
    metrics_collector = create_metrics_collector(service_name)
    app['metrics_collector'] = metrics_collector
    
    # Add metrics endpoint
    app.router.add_get('/metrics', metrics_endpoint)
    
    logger.info(f"Metrics collection enabled for {service_name}")
