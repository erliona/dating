# Observability Guide

This document describes the comprehensive observability system implemented across all microservices in the dating application.

## Overview

The observability system provides:
- **Distributed Tracing**: W3C Trace Context support for request flow tracking
- **Structured Logging**: JSON-formatted logs with correlation IDs and trace context
- **Metrics Collection**: Prometheus metrics for HTTP requests, business events, and system health
- **Error Handling**: Unified error responses with proper HTTP status codes
- **Correlation IDs**: Request tracing across service boundaries

## Architecture

### Middleware Stack

All services use a standardized middleware stack in the following order:

1. **Error Handler** - Catches and formats all exceptions
2. **Distributed Tracing** - W3C Trace Context support
3. **Correlation ID** - Request correlation across services
4. **User Context** - Extract user information from JWT
5. **Request Logging** - Structured request/response logging
6. **Metrics Collection** - HTTP and business metrics
7. **Audit Logging** - Critical operation logging
8. **JWT Authentication** - Token validation (where applicable)

### Trace Context

The system implements W3C Trace Context standard:

- **Trace ID**: Unique identifier for the entire request flow
- **Span ID**: Unique identifier for each service operation
- **Parent Span ID**: Links child operations to parent operations

Headers used:
- `traceparent`: W3C standard format
- `X-Trace-ID`: Custom trace ID header
- `X-Span-ID`: Custom span ID header
- `X-Parent-Span-ID`: Custom parent span ID header

### Correlation IDs

Every request gets a correlation ID that flows through all services:

- **X-Correlation-ID**: Primary correlation header
- **X-Request-ID**: Unique request identifier within each service

## Logging

### Structured Logging

All logs are in JSON format with the following standard fields:

```json
{
  "timestamp": "2025-01-23T10:30:00Z",
  "level": "INFO",
  "logger": "services.profile.main",
  "message": "Request completed: POST /profiles -> 201",
  "module": "main",
  "function": "create_profile",
  "line": 142,
  "user_id": "12345",
  "event_type": "request_completed",
  "service_name": "profile-service",
  "request_id": "abc123",
  "correlation_id": "def456",
  "trace_id": "ghi789",
  "span_id": "jkl012",
  "parent_span_id": "mno345",
  "duration_ms": 150,
  "status_code": 201,
  "method": "POST",
  "path": "/profiles",
  "remote_addr": "192.168.1.100",
  "user_agent": "Mozilla/5.0..."
}
```

### Log Levels

- **DEBUG**: Detailed trace information, correlation propagation
- **INFO**: Request/response logging, business events
- **WARNING**: Service errors, circuit breaker events
- **ERROR**: Unexpected errors with full context

### Event Types

Standard event types for filtering and analysis:

- `request_started`: Request begins processing
- `request_completed`: Request completed successfully
- `request_failed`: Request failed with error
- `trace_start`: Trace context created
- `trace_complete`: Trace context completed
- `trace_propagation`: Trace propagated to another service
- `correlation_propagation`: Correlation ID propagated
- `circuit_fallback`: Circuit breaker used fallback
- `profile_create`: Profile creation event
- `interaction_created`: User interaction event
- `message_sent`: Message sent event

## Metrics

### HTTP Metrics

Standard HTTP metrics collected by all services:

- `http_requests_total`: Total HTTP requests by method, endpoint, status, service
- `http_request_duration_seconds`: Request duration histogram
- `http_requests_active`: Currently active requests

### Business Metrics

Centralized business metrics in `core.metrics.business_metrics`:

**Counters (Events):**
- `profile_created_total`: Profile creation events
- `profile_updated_total`: Profile update events
- `profile_deleted_total`: Profile deletion events
- `interaction_created_total`: User interactions (likes, dislikes, matches)
- `swipes_total`: Swipe events (likes + dislikes)
- `message_sent_total`: Messages sent
- `conversation_started_total`: Conversations started

**Gauges (Current State):**
- `active_users_total`: Users active in last 24h
- `users_by_region`: Users by geographic region
- `matches_current`: Current number of matches
- `conversations_active`: Active conversations

### Circuit Breaker Metrics

Resilience metrics for service-to-service calls:

- `circuit_breaker_calls_total`: Circuit breaker calls by service, target, state, result
- `circuit_breaker_state`: Current circuit breaker state (0=closed, 1=open, 2=half_open)

### Security Metrics

Security-related metrics:

- `security_events_total`: Security events by type
- `auth_attempts_total`: Authentication attempts
- `auth_failures_total`: Authentication failures
- `jwt_validations_total`: JWT token validations
- `rate_limit_hits_total`: Rate limit violations

## Error Handling

### Custom Exceptions

All services use standardized exceptions from `core.exceptions`:

- `ServiceError`: Base exception for all service errors
- `ValidationError`: Input validation failures (400)
- `NotFoundError`: Resource not found (404)
- `UnauthorizedError`: Authentication failures (401)
- `ForbiddenError`: Authorization failures (403)
- `ConflictError`: Resource conflicts (409)
- `CircuitBreakerError`: Service unavailable (503)
- `ExternalServiceError`: External service failures (502)
- `DatabaseError`: Database operation failures (500)
- `RateLimitError`: Rate limit exceeded (429)

### Error Response Format

All errors return standardized JSON responses:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "user_id is required",
    "details": {
      "field": "user_id",
      "value": null
    }
  }
}
```

## Inter-Service Communication

### Correlation ID Propagation

All inter-service calls automatically propagate correlation IDs:

```python
from core.middleware.correlation import create_headers_with_correlation

async def _call_data_service(url, method="GET", data=None, request=None):
    headers = create_headers_with_correlation(request)
    # ... make HTTP call with headers
```

### Trace Context Propagation

Distributed tracing across service boundaries:

```python
from core.middleware.tracing import create_headers_with_trace

async def _call_data_service(url, method="GET", data=None, request=None):
    headers = create_headers_with_trace(request)
    # ... make HTTP call with headers
```

## Monitoring Integration

### Prometheus

All services expose metrics at `/metrics` endpoint:

- Scraped by Prometheus every 30 seconds
- Metrics stored with 15-day retention
- Alerting rules for critical metrics

### Grafana Dashboards

Standard dashboards available:

1. **System Health Dashboard**: Service status, HTTP metrics, error rates
2. **Business Metrics Dashboard**: User activity, matches, messages
3. **API Performance Dashboard**: Request rates, response times, error rates
4. **Database & Infrastructure**: Database metrics, system resources
5. **Security & Authentication**: Auth events, security violations

### Loki

Structured logs collected by Loki:

- Log aggregation from all services
- Correlation ID-based log correlation
- Trace context for distributed request tracking
- 30-day log retention

## Best Practices

### Adding New Metrics

1. Define metrics in `core.metrics.business_metrics`
2. Use appropriate metric type (Counter for events, Gauge for state)
3. Include service name in labels
4. Update Grafana dashboards

### Error Handling

1. Use specific exception types from `core.exceptions`
2. Include relevant details in error responses
3. Log errors with full context (correlation_id, trace_id, user_id)
4. Don't expose sensitive information in error messages

### Logging

1. Use structured logging with standard fields
2. Include correlation_id and trace_id in all logs
3. Use appropriate log levels
4. Include relevant context (user_id, service, operation)

### Tracing

1. Propagate trace context in all inter-service calls
2. Create child spans for outgoing calls
3. Log trace propagation events
4. Use W3C Trace Context standard

## Troubleshooting

### Common Issues

1. **Missing correlation IDs**: Check middleware order, ensure correlation_middleware is included
2. **Broken traces**: Verify trace context propagation in inter-service calls
3. **Missing metrics**: Check metric definitions and service labels
4. **Log format issues**: Verify JsonFormatter configuration

### Debugging

1. Use correlation_id to trace requests across services
2. Use trace_id to follow distributed request flow
3. Check circuit breaker states for service failures
4. Monitor error rates and response times in Grafana

## Configuration

### Environment Variables

- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `SERVICE_NAME`: Service name for metrics and logging
- `JWT_SECRET`: JWT secret for authentication
- `RABBITMQ_URL`: RabbitMQ connection for event publishing

### Service Configuration

Each service should configure:

```python
from core.middleware.standard_stack import setup_standard_middleware_stack

# Setup standard middleware stack
setup_standard_middleware_stack(app, "service-name", use_auth=True, use_audit=True)
```

## Future Enhancements

1. **OpenTelemetry Integration**: Full OpenTelemetry support
2. **Custom Dashboards**: Service-specific dashboards
3. **Log Analytics**: Advanced log analysis and alerting
4. **Performance Profiling**: Request performance analysis
5. **SLA Monitoring**: Service level agreement tracking
