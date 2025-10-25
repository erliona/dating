"""
Standardized error handling utilities.

Provides consistent error formats, HTTP status codes, and error categorization
across all microservices.
"""

import logging
import traceback
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class ErrorCode(Enum):
    """Standardized error codes for the dating platform."""

    # Authentication & Authorization (1000-1999)
    AUTHENTICATION_REQUIRED = "AUTH_001"
    INVALID_TOKEN = "AUTH_002"
    TOKEN_EXPIRED = "AUTH_003"
    INSUFFICIENT_PERMISSIONS = "AUTH_004"
    INVALID_CREDENTIALS = "AUTH_005"
    ACCOUNT_LOCKED = "AUTH_006"
    ACCOUNT_SUSPENDED = "AUTH_007"

    # Validation Errors (2000-2999)
    VALIDATION_ERROR = "VAL_001"
    REQUIRED_FIELD_MISSING = "VAL_002"
    INVALID_FORMAT = "VAL_003"
    VALUE_TOO_LONG = "VAL_004"
    VALUE_TOO_SHORT = "VAL_005"
    INVALID_RANGE = "VAL_006"
    DUPLICATE_VALUE = "VAL_007"
    INVALID_EMAIL = "VAL_008"
    INVALID_PHONE = "VAL_009"
    INVALID_DATE = "VAL_010"
    INVALID_AGE = "VAL_011"
    INVALID_LOCATION = "VAL_012"

    # Business Logic Errors (3000-3999)
    RESOURCE_NOT_FOUND = "BIZ_001"
    RESOURCE_ALREADY_EXISTS = "BIZ_002"
    OPERATION_NOT_ALLOWED = "BIZ_003"
    QUOTA_EXCEEDED = "BIZ_004"
    FEATURE_NOT_AVAILABLE = "BIZ_005"
    USER_NOT_ELIGIBLE = "BIZ_006"
    MATCH_NOT_FOUND = "BIZ_007"
    CONVERSATION_NOT_FOUND = "BIZ_008"
    MESSAGE_NOT_FOUND = "BIZ_009"
    PROFILE_INCOMPLETE = "BIZ_010"
    VERIFICATION_REQUIRED = "BIZ_011"

    # External Service Errors (4000-4999)
    EXTERNAL_SERVICE_ERROR = "EXT_001"
    DATABASE_ERROR = "EXT_002"
    STORAGE_ERROR = "EXT_003"
    EMAIL_SERVICE_ERROR = "EXT_004"
    SMS_SERVICE_ERROR = "EXT_005"
    PAYMENT_SERVICE_ERROR = "EXT_006"
    TELEGRAM_API_ERROR = "EXT_007"
    GEOCODING_ERROR = "EXT_008"
    IMAGE_PROCESSING_ERROR = "EXT_009"

    # Rate Limiting (5000-5999)
    RATE_LIMIT_EXCEEDED = "RATE_001"
    TOO_MANY_REQUESTS = "RATE_002"
    DAILY_LIMIT_EXCEEDED = "RATE_003"
    HOURLY_LIMIT_EXCEEDED = "RATE_004"

    # System Errors (6000-6999)
    INTERNAL_SERVER_ERROR = "SYS_001"
    SERVICE_UNAVAILABLE = "SYS_002"
    TIMEOUT_ERROR = "SYS_003"
    CONFIGURATION_ERROR = "SYS_004"
    MAINTENANCE_MODE = "SYS_005"
    UPGRADE_REQUIRED = "SYS_006"


@dataclass
class ErrorDetails:
    """Detailed error information."""

    field: str | None = None
    value: Any | None = None
    constraint: str | None = None
    suggestion: str | None = None
    documentation_url: str | None = None


@dataclass
class StandardError:
    """Standardized error format."""

    error: str
    message: str
    code: str
    status_code: int
    timestamp: str
    request_id: str | None = None
    details: ErrorDetails | None = None
    retry_after: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON response."""
        result = asdict(self)
        # Remove None values
        return {k: v for k, v in result.items() if v is not None}


class DatingPlatformError(Exception):
    """Base exception for dating platform errors."""

    def __init__(
        self,
        error_code: ErrorCode,
        message: str,
        status_code: int = 400,
        details: ErrorDetails | None = None,
        request_id: str | None = None,
        retry_after: int | None = None,
    ):
        self.error_code = error_code
        self.message = message
        self.status_code = status_code
        self.details = details
        self.request_id = request_id
        self.retry_after = retry_after
        super().__init__(message)


class ValidationError(DatingPlatformError):
    """Validation error."""

    def __init__(self, message: str, field: str | None = None, **kwargs):
        super().__init__(
            ErrorCode.VALIDATION_ERROR,
            message,
            status_code=422,
            details=ErrorDetails(field=field) if field else None,
            **kwargs,
        )


class AuthenticationError(DatingPlatformError):
    """Authentication error."""

    def __init__(self, message: str = "Authentication required", **kwargs):
        super().__init__(
            ErrorCode.AUTHENTICATION_REQUIRED, message, status_code=401, **kwargs
        )


class AuthorizationError(DatingPlatformError):
    """Authorization error."""

    def __init__(self, message: str = "Insufficient permissions", **kwargs):
        super().__init__(
            ErrorCode.INSUFFICIENT_PERMISSIONS, message, status_code=403, **kwargs
        )


class ResourceNotFoundError(DatingPlatformError):
    """Resource not found error."""

    def __init__(self, resource: str = "Resource", **kwargs):
        super().__init__(
            ErrorCode.RESOURCE_NOT_FOUND,
            f"{resource} not found",
            status_code=404,
            **kwargs,
        )


class BusinessLogicError(DatingPlatformError):
    """Business logic error."""

    def __init__(self, error_code: ErrorCode, message: str, **kwargs):
        super().__init__(error_code, message, status_code=400, **kwargs)


class ExternalServiceError(DatingPlatformError):
    """External service error."""

    def __init__(self, service: str, message: str, **kwargs):
        super().__init__(
            ErrorCode.EXTERNAL_SERVICE_ERROR,
            f"{service} error: {message}",
            status_code=502,
            **kwargs,
        )


class RateLimitError(DatingPlatformError):
    """Rate limit error."""

    def __init__(
        self, message: str = "Rate limit exceeded", retry_after: int = 60, **kwargs
    ):
        super().__init__(
            ErrorCode.RATE_LIMIT_EXCEEDED,
            message,
            status_code=429,
            retry_after=retry_after,
            **kwargs,
        )


class SystemError(DatingPlatformError):
    """System error."""

    def __init__(self, message: str = "Internal server error", **kwargs):
        super().__init__(
            ErrorCode.INTERNAL_SERVER_ERROR, message, status_code=500, **kwargs
        )


def create_standard_error(
    error_code: ErrorCode,
    message: str,
    status_code: int = 400,
    request_id: str | None = None,
    details: ErrorDetails | None = None,
    retry_after: int | None = None,
) -> StandardError:
    """Create a standardized error response."""
    return StandardError(
        error=error_code.value,
        message=message,
        code=error_code.value,
        status_code=status_code,
        timestamp=datetime.now(UTC).isoformat(),
        request_id=request_id,
        details=details,
        retry_after=retry_after,
    )


def handle_exception(
    exception: Exception, request_id: str | None = None, service_name: str = "unknown"
) -> StandardError:
    """Handle any exception and convert to standard error format."""

    # Log the exception
    logger.error(
        f"Exception in {service_name}: {str(exception)}",
        exc_info=True,
        extra={"request_id": request_id},
    )

    # Handle known exceptions
    if isinstance(exception, DatingPlatformError):
        return create_standard_error(
            exception.error_code,
            exception.message,
            exception.status_code,
            request_id,
            exception.details,
            exception.retry_after,
        )

    # Handle specific exception types
    if isinstance(exception, ValueError):
        return create_standard_error(
            ErrorCode.VALIDATION_ERROR,
            f"Invalid value: {str(exception)}",
            422,
            request_id,
        )

    if isinstance(exception, KeyError):
        return create_standard_error(
            ErrorCode.REQUIRED_FIELD_MISSING,
            f"Missing required field: {str(exception)}",
            422,
            request_id,
        )

    if isinstance(exception, PermissionError):
        return create_standard_error(
            ErrorCode.INSUFFICIENT_PERMISSIONS,
            "Insufficient permissions",
            403,
            request_id,
        )

    if isinstance(exception, FileNotFoundError):
        return create_standard_error(
            ErrorCode.RESOURCE_NOT_FOUND,
            f"Resource not found: {str(exception)}",
            404,
            request_id,
        )

    if isinstance(exception, TimeoutError):
        return create_standard_error(
            ErrorCode.TIMEOUT_ERROR, "Request timeout", 408, request_id
        )

    # Handle database errors
    if "database" in str(exception).lower() or "sql" in str(exception).lower():
        return create_standard_error(
            ErrorCode.DATABASE_ERROR, "Database operation failed", 502, request_id
        )

    # Handle network errors
    if "connection" in str(exception).lower() or "network" in str(exception).lower():
        return create_standard_error(
            ErrorCode.EXTERNAL_SERVICE_ERROR,
            "External service unavailable",
            502,
            request_id,
        )

    # Default to internal server error
    return create_standard_error(
        ErrorCode.INTERNAL_SERVER_ERROR, "An unexpected error occurred", 500, request_id
    )


def get_error_response(
    error: StandardError, include_traceback: bool = False
) -> dict[str, Any]:
    """Get error response dictionary."""
    response = error.to_dict()

    if include_traceback:
        response["traceback"] = traceback.format_exc()

    return response


def log_error(
    error: StandardError,
    service_name: str,
    request_id: str | None = None,
    user_id: str | None = None,
    additional_context: dict[str, Any] | None = None,
):
    """Log error with structured logging."""
    log_data = {
        "error_code": error.error,
        "message": error.message,
        "status_code": error.status_code,
        "service": service_name,
        "timestamp": error.timestamp,
    }

    if request_id:
        log_data["request_id"] = request_id

    if user_id:
        log_data["user_id"] = user_id

    if additional_context:
        log_data.update(additional_context)

    if error.status_code >= 500:
        logger.error("Server error occurred", extra=log_data)
    elif error.status_code >= 400:
        logger.warning("Client error occurred", extra=log_data)
    else:
        logger.info("Error occurred", extra=log_data)


# Common error responses
AUTHENTICATION_REQUIRED = create_standard_error(
    ErrorCode.AUTHENTICATION_REQUIRED, "Authentication required", 401
)

INVALID_TOKEN = create_standard_error(
    ErrorCode.INVALID_TOKEN, "Invalid or expired token", 401
)

INSUFFICIENT_PERMISSIONS = create_standard_error(
    ErrorCode.INSUFFICIENT_PERMISSIONS, "Insufficient permissions", 403
)

RESOURCE_NOT_FOUND = create_standard_error(
    ErrorCode.RESOURCE_NOT_FOUND, "Resource not found", 404
)

VALIDATION_ERROR = create_standard_error(
    ErrorCode.VALIDATION_ERROR, "Validation error", 422
)

RATE_LIMIT_EXCEEDED = create_standard_error(
    ErrorCode.RATE_LIMIT_EXCEEDED, "Rate limit exceeded", 429, retry_after=60
)

INTERNAL_SERVER_ERROR = create_standard_error(
    ErrorCode.INTERNAL_SERVER_ERROR, "Internal server error", 500
)

SERVICE_UNAVAILABLE = create_standard_error(
    ErrorCode.SERVICE_UNAVAILABLE, "Service temporarily unavailable", 503
)
