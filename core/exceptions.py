from __future__ import annotations

"""Custom exceptions for the dating application microservices."""

from typing import Any


class ServiceError(Exception):
    """Base exception for all service errors."""

    def __init__(
        self,
        message: str,
        code: str,
        status: int = 500,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.code = code
        self.status = status
        self.details = details or {}
        super().__init__(self.message)


class ValidationError(ServiceError):
    """Raised when input validation fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, "VALIDATION_ERROR", 400, details)


class NotFoundError(ServiceError):
    """Raised when a requested resource is not found."""

    def __init__(self, resource: str, resource_id: str):
        super().__init__(f"{resource} not found: {resource_id}", "NOT_FOUND", 404)


class UnauthorizedError(ServiceError):
    """Raised when authentication fails."""

    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, "UNAUTHORIZED", 401)


class ForbiddenError(ServiceError):
    """Raised when access is forbidden."""

    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, "FORBIDDEN", 403)


class ConflictError(ServiceError):
    """Raised when there's a conflict with the current state."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(message, "CONFLICT", 409, details)


class CircuitBreakerError(ServiceError):
    """Raised when a circuit breaker is open."""

    def __init__(self, service: str):
        super().__init__(f"Service unavailable: {service}", "SERVICE_UNAVAILABLE", 503)


class ExternalServiceError(ServiceError):
    """Raised when an external service call fails."""

    def __init__(
        self, service: str, message: str, details: dict[str, Any] | None = None
    ):
        super().__init__(
            f"External service error ({service}): {message}",
            "EXTERNAL_SERVICE_ERROR",
            502,
            details,
        )


class DatabaseError(ServiceError):
    """Raised when a database operation fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(f"Database error: {message}", "DATABASE_ERROR", 500, details)


class RateLimitError(ServiceError):
    """Raised when rate limit is exceeded."""

    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, "RATE_LIMIT_EXCEEDED", 429)


class FileUploadError(ServiceError):
    """Raised when file upload fails."""

    def __init__(self, message: str, details: dict[str, Any] | None = None):
        super().__init__(
            f"File upload error: {message}", "FILE_UPLOAD_ERROR", 400, details
        )


class NSFWContentError(ServiceError):
    """Raised when NSFW content is detected."""

    def __init__(self, message: str = "NSFW content detected"):
        super().__init__(message, "NSFW_CONTENT_DETECTED", 400)
