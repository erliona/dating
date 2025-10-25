from __future__ import annotations

"""Security-specific metrics for monitoring authentication and security events."""

import logging

from prometheus_client import Counter, Gauge, Histogram

logger = logging.getLogger(__name__)

# Security metrics
SECURITY_EVENTS = Counter(
    "security_events_total",
    "Total number of security events",
    ["event_type", "service", "severity"],
)

AUTH_ATTEMPTS = Counter(
    "auth_attempts_total",
    "Total authentication attempts",
    ["service", "result", "method"],
)

AUTH_FAILURES = Counter(
    "auth_failures_total",
    "Total authentication failures",
    ["service", "reason", "user_id"],
)

RATE_LIMIT_HITS = Counter(
    "rate_limit_hits_total", "Total rate limit hits", ["service", "endpoint", "user_id"]
)

JWT_VALIDATIONS = Counter(
    "jwt_validations_total",
    "Total JWT token validations",
    ["service", "result", "token_type"],
)

FILE_UPLOADS = Counter(
    "file_uploads_total", "Total file uploads", ["service", "result", "file_type"]
)

SUSPICIOUS_ACTIVITY = Counter(
    "suspicious_activity_total",
    "Total suspicious activity events",
    ["service", "activity_type", "severity"],
)

SECURITY_RESPONSE_TIME = Histogram(
    "security_response_time_seconds",
    "Time spent on security operations",
    ["service", "operation"],
    buckets=[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
)

ACTIVE_SESSIONS = Gauge(
    "active_sessions_total", "Number of active user sessions", ["service"]
)

FAILED_LOGIN_ATTEMPTS = Gauge(
    "failed_login_attempts_total",
    "Number of failed login attempts in the last hour",
    ["service", "user_id"],
)


def record_security_event(
    event_type: str, service: str, severity: str = "info", **labels
):
    """Record a security event."""
    SECURITY_EVENTS.labels(
        event_type=event_type, service=service, severity=severity
    ).inc()

    logger.info(
        f"Security event: {event_type}",
        extra={
            "event_type": "security_event",
            "security_event_type": event_type,
            "service": service,
            "severity": severity,
            **labels,
        },
    )


def record_auth_attempt(service: str, result: str, method: str = "unknown", **labels):
    """Record an authentication attempt."""
    AUTH_ATTEMPTS.labels(service=service, result=result, method=method).inc()

    if result == "failure":
        record_security_event("auth_failure", service, "warning", **labels)


def record_auth_failure(service: str, reason: str, user_id: str = "unknown", **labels):
    """Record an authentication failure."""
    AUTH_FAILURES.labels(service=service, reason=reason, user_id=str(user_id)).inc()

    record_security_event(
        "auth_failure", service, "warning", reason=reason, user_id=user_id, **labels
    )


def record_rate_limit_hit(
    service: str, endpoint: str, user_id: str = "unknown", **labels
):
    """Record a rate limit hit."""
    RATE_LIMIT_HITS.labels(
        service=service, endpoint=endpoint, user_id=str(user_id)
    ).inc()

    record_security_event(
        "rate_limit_hit",
        service,
        "warning",
        endpoint=endpoint,
        user_id=user_id,
        **labels,
    )


def record_jwt_validation(
    service: str, result: str, token_type: str = "access", **labels
):
    """Record a JWT validation attempt."""
    JWT_VALIDATIONS.labels(service=service, result=result, token_type=token_type).inc()

    if result == "failure":
        record_security_event(
            "jwt_validation_failure",
            service,
            "warning",
            token_type=token_type,
            **labels,
        )


def record_file_upload(service: str, result: str, file_type: str = "unknown", **labels):
    """Record a file upload attempt."""
    FILE_UPLOADS.labels(service=service, result=result, file_type=file_type).inc()

    if result == "failure":
        record_security_event(
            "file_upload_failure", service, "warning", file_type=file_type, **labels
        )
    elif result == "blocked":
        record_security_event(
            "file_upload_blocked", service, "warning", file_type=file_type, **labels
        )


def record_suspicious_activity(
    service: str, activity_type: str, severity: str = "medium", **labels
):
    """Record suspicious activity."""
    SUSPICIOUS_ACTIVITY.labels(
        service=service, activity_type=activity_type, severity=severity
    ).inc()

    record_security_event(
        "suspicious_activity", service, severity, activity_type=activity_type, **labels
    )


def update_active_sessions(service: str, count: int):
    """Update the number of active sessions."""
    ACTIVE_SESSIONS.labels(service=service).set(count)


def update_failed_login_attempts(service: str, user_id: str, count: int):
    """Update the number of failed login attempts for a user."""
    FAILED_LOGIN_ATTEMPTS.labels(service=service, user_id=str(user_id)).set(count)
