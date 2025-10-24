# Error Handling Guide

This document describes the comprehensive error handling system implemented across all microservices in the dating application.

## Overview

The error handling system provides:
- **Standardized Exceptions**: Custom exception types for different error scenarios
- **Unified Error Responses**: Consistent JSON error format across all services
- **Structured Error Logging**: Detailed error context with correlation IDs and trace information
- **HTTP Status Code Mapping**: Proper HTTP status codes for different error types
- **Error Recovery**: Circuit breaker patterns and retry mechanisms

## Exception Hierarchy

### Base Exception

#### ServiceError

**Base class for all service errors**

```python
class ServiceError(Exception):
    def __init__(self, message: str, code: str, status: int = 500, details: dict = None):
        self.message = message
        self.code = code
        self.status = status
        self.details = details or {}
```

**Properties**:
- `message`: Human-readable error message
- `code`: Machine-readable error code
- `status`: HTTP status code
- `details`: Additional error context

### Specific Exceptions

#### ValidationError

**HTTP Status**: 400 Bad Request  
**Use Case**: Input validation failures

```python
class ValidationError(ServiceError):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "VALIDATION_ERROR", 400, details)
```

**Example**:
```python
raise ValidationError("user_id is required", {"field": "user_id", "value": None})
```

#### NotFoundError

**HTTP Status**: 404 Not Found  
**Use Case**: Resource not found

```python
class NotFoundError(ServiceError):
    def __init__(self, resource: str, resource_id: str):
        super().__init__(f"{resource} not found: {resource_id}", "NOT_FOUND", 404)
```

**Example**:
```python
raise NotFoundError("profile", "12345")
```

#### UnauthorizedError

**HTTP Status**: 401 Unauthorized  
**Use Case**: Authentication failures

```python
class UnauthorizedError(ServiceError):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(message, "UNAUTHORIZED", 401)
```

**Example**:
```python
raise UnauthorizedError("Invalid or expired token")
```

#### ForbiddenError

**HTTP Status**: 403 Forbidden  
**Use Case**: Authorization failures

```python
class ForbiddenError(ServiceError):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(message, "FORBIDDEN", 403)
```

**Example**:
```python
raise ForbiddenError("Insufficient permissions to access this resource")
```

#### ConflictError

**HTTP Status**: 409 Conflict  
**Use Case**: Resource conflicts

```python
class ConflictError(ServiceError):
    def __init__(self, message: str, details: dict = None):
        super().__init__(message, "CONFLICT", 409, details)
```

**Example**:
```python
raise ConflictError("Profile already exists", {"user_id": "12345"})
```

#### CircuitBreakerError

**HTTP Status**: 503 Service Unavailable  
**Use Case**: Circuit breaker is open

```python
class CircuitBreakerError(ServiceError):
    def __init__(self, service: str):
        super().__init__(f"Service unavailable: {service}", "SERVICE_UNAVAILABLE", 503)
```

**Example**:
```python
raise CircuitBreakerError("data-service")
```

#### ExternalServiceError

**HTTP Status**: 502 Bad Gateway  
**Use Case**: External service failures

```python
class ExternalServiceError(ServiceError):
    def __init__(self, service: str, message: str, details: dict = None):
        super().__init__(f"External service error ({service}): {message}", "EXTERNAL_SERVICE_ERROR", 502, details)
```

**Example**:
```python
raise ExternalServiceError("data-service", "HTTP 500: Internal Server Error", {"url": "/data/profiles", "status": 500})
```

#### DatabaseError

**HTTP Status**: 500 Internal Server Error  
**Use Case**: Database operation failures

```python
class DatabaseError(ServiceError):
    def __init__(self, message: str, details: dict = None):
        super().__init__(f"Database error: {message}", "DATABASE_ERROR", 500, details)
```

**Example**:
```python
raise DatabaseError("Connection timeout", {"operation": "SELECT", "table": "profiles"})
```

#### RateLimitError

**HTTP Status**: 429 Too Many Requests  
**Use Case**: Rate limit exceeded

```python
class RateLimitError(ServiceError):
    def __init__(self, message: str = "Rate limit exceeded"):
        super().__init__(message, "RATE_LIMIT_EXCEEDED", 429)
```

**Example**:
```python
raise RateLimitError("Too many requests per minute")
```

#### FileUploadError

**HTTP Status**: 400 Bad Request  
**Use Case**: File upload failures

```python
class FileUploadError(ServiceError):
    def __init__(self, message: str, details: dict = None):
        super().__init__(f"File upload error: {message}", "FILE_UPLOAD_ERROR", 400, details)
```

**Example**:
```python
raise FileUploadError("File too large", {"max_size": "10MB", "actual_size": "15MB"})
```

#### NSFWContentError

**HTTP Status**: 400 Bad Request  
**Use Case**: NSFW content detected

```python
class NSFWContentError(ServiceError):
    def __init__(self, message: str = "NSFW content detected"):
        super().__init__(message, "NSFW_CONTENT_DETECTED", 400)
```

**Example**:
```python
raise NSFWContentError("Image contains inappropriate content")
```

## Error Response Format

All errors return standardized JSON responses:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "user_id is required",
    "details": {
      "field": "user_id",
      "value": null,
      "constraints": ["required", "integer"]
    }
  }
}
```

### Response Fields

- **code**: Machine-readable error code for programmatic handling
- **message**: Human-readable error message
- **details**: Additional context (optional)

## Error Handler Middleware

The `error_handler_middleware` automatically catches and formats all exceptions:

```python
@web.middleware
async def error_handler_middleware(request: web.Request, handler) -> web.Response:
    try:
        return await handler(request)
    except ServiceError as e:
        # Log service errors with context
        logger.warning(f"Service error: {e.code}", extra={
            "error_code": e.code,
            "error_message": e.message,
            "status_code": e.status,
            "details": e.details,
            "request_id": request.get("request_id"),
            "correlation_id": request.get("correlation_id")
        })
        
        return web.json_response({
            "error": {
                "code": e.code,
                "message": e.message,
                "details": e.details
            }
        }, status=e.status)
    except Exception as e:
        # Log unexpected errors
        logger.error(f"Unexpected error: {e}", exc_info=True, extra={
            "request_id": request.get("request_id"),
            "correlation_id": request.get("correlation_id")
        })
        
        return web.json_response({
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "An unexpected error occurred"
            }
        }, status=500)
```

## Error Logging

### Structured Error Logging

All errors are logged with comprehensive context:

```json
{
  "timestamp": "2025-01-23T10:30:00Z",
  "level": "WARNING",
  "logger": "services.profile.main",
  "message": "Service error: VALIDATION_ERROR",
  "error_code": "VALIDATION_ERROR",
  "error_message": "user_id is required",
  "status_code": 400,
  "details": {"field": "user_id", "value": null},
  "request_id": "abc123",
  "correlation_id": "def456",
  "trace_id": "ghi789",
  "span_id": "jkl012",
  "user_id": "12345",
  "service": "profile-service",
  "path": "/profiles",
  "method": "POST"
}
```

### Error Context Fields

- **error_code**: Machine-readable error code
- **error_message**: Human-readable error message
- **status_code**: HTTP status code
- **details**: Additional error context
- **request_id**: Unique request identifier
- **correlation_id**: Request correlation ID
- **trace_id**: Distributed trace ID
- **span_id**: Current span ID
- **user_id**: User identifier (if available)
- **service**: Service name
- **path**: Request path
- **method**: HTTP method

## Best Practices

### Exception Usage

1. **Use Specific Exceptions**: Choose the most specific exception type for the error scenario
2. **Include Context**: Provide relevant details in the exception
3. **Don't Expose Sensitive Data**: Avoid including sensitive information in error messages
4. **Use Consistent Error Codes**: Use standardized error codes across services

### Error Handling

1. **Catch Specific Exceptions**: Handle specific exception types when possible
2. **Log Before Re-raising**: Log errors with context before re-raising
3. **Provide Fallbacks**: Use circuit breakers and fallbacks for external service calls
4. **Validate Input Early**: Validate input data early to provide clear error messages

### Error Responses

1. **Consistent Format**: Use the standardized error response format
2. **Appropriate Status Codes**: Use correct HTTP status codes
3. **Helpful Messages**: Provide clear, actionable error messages
4. **Include Details**: Add relevant context in the details field

### Error Recovery

1. **Circuit Breakers**: Use circuit breakers for external service calls
2. **Retry Logic**: Implement retry logic for transient failures
3. **Graceful Degradation**: Provide fallback functionality when possible
4. **Health Checks**: Implement health checks for service dependencies

## Common Error Scenarios

### Input Validation

```python
async def create_profile(request: web.Request) -> web.Response:
    try:
        data = await request.json()
        user_id = data.get("user_id")
        
        if not user_id:
            raise ValidationError("user_id is required", {"field": "user_id"})
        
        if not isinstance(user_id, int):
            raise ValidationError("user_id must be an integer", {"field": "user_id", "value": user_id})
        
        # ... rest of the function
    except ValidationError:
        raise  # Re-raise to be handled by middleware
    except Exception as e:
        logger.error(f"Unexpected error in create_profile: {e}", exc_info=True)
        raise
```

### Resource Not Found

```python
async def get_profile(request: web.Request) -> web.Response:
    try:
        user_id = request.match_info["user_id"]
        
        # Call data service
        result = await _call_data_service(f"{data_service_url}/data/profiles/{user_id}")
        
        if not result:
            raise NotFoundError("profile", user_id)
        
        return web.json_response(result)
    except NotFoundError:
        raise  # Re-raise to be handled by middleware
    except Exception as e:
        logger.error(f"Unexpected error in get_profile: {e}", exc_info=True)
        raise
```

### External Service Failures

```python
async def _call_data_service(url: str, method: str = "GET", data: dict = None, request: web.Request = None):
    try:
        headers = create_headers_with_correlation(request)
        
        async with aiohttp.ClientSession() as session:
            async with session.request(method, url, json=data, headers=headers) as resp:
                if resp.status >= 400:
                    raise ExternalServiceError(
                        service='data-service',
                        message=f"HTTP {resp.status}: {await resp.text()}",
                        details={'url': url, 'method': method, 'status': resp.status}
                    )
                return await resp.json()
    except aiohttp.ClientError as e:
        raise ExternalServiceError(
            service='data-service',
            message=f"Connection error: {str(e)}",
            details={'url': url, 'method': method}
        )
```

### Circuit Breaker Usage

```python
async def create_profile(request: web.Request) -> web.Response:
    try:
        # Use circuit breaker for external service call
        result = await data_service_breaker.call(
            _call_data_service,
            f"{data_service_url}/data/profiles",
            "POST",
            profile_data,
            request,
            fallback=lambda *args: {"error": "Service temporarily unavailable"}
        )
        
        if "error" in result:
            if result["error"] == "Service temporarily unavailable":
                raise CircuitBreakerError("data-service")
            raise ExternalServiceError(
                service='data-service',
                message=result.get("error", "Unknown error"),
                details=result
            )
        
        return web.json_response(result)
    except (CircuitBreakerError, ExternalServiceError):
        raise  # Re-raise to be handled by middleware
    except Exception as e:
        logger.error(f"Unexpected error in create_profile: {e}", exc_info=True)
        raise
```

## Error Monitoring

### Metrics

Error rates are tracked through Prometheus metrics:

- `http_requests_total{status_code="4xx"}`: Client error rate
- `http_requests_total{status_code="5xx"}`: Server error rate
- `circuit_breaker_calls_total{result="failure"}`: Circuit breaker failures

### Alerts

Configure alerts for critical error scenarios:

- High error rates (>5% for 5xx errors)
- Circuit breaker open
- Service unavailable
- Authentication failures

### Log Analysis

Use correlation IDs to trace error flows:

1. Find error in logs using correlation ID
2. Trace request flow across services
3. Identify root cause of the error
4. Check related errors in the same trace

## Troubleshooting

### Common Issues

1. **Missing Error Context**: Ensure error handler middleware is included
2. **Incorrect Status Codes**: Verify exception types and status codes
3. **Missing Error Details**: Include relevant context in exception details
4. **Sensitive Data Exposure**: Review error messages for sensitive information

### Debugging

1. **Check Logs**: Look for error logs with correlation ID
2. **Trace Requests**: Use correlation ID to trace request flow
3. **Verify Middleware**: Ensure error handler middleware is properly configured
4. **Test Error Scenarios**: Create test cases for different error conditions

## Migration Guide

### From Generic Exceptions

**Before**:
```python
try:
    # ... some operation
except Exception as e:
    return web.json_response({"error": str(e)}, status=500)
```

**After**:
```python
try:
    # ... some operation
except ValidationError as e:
    raise  # Let middleware handle it
except Exception as e:
    logger.error(f"Unexpected error: {e}", exc_info=True)
    raise
```

### From Custom Error Responses

**Before**:
```python
return web.json_response({"error": "User not found"}, status=404)
```

**After**:
```python
raise NotFoundError("user", user_id)
```

### Adding New Exception Types

1. Define new exception class in `core.exceptions`
2. Add appropriate HTTP status code
3. Update error handler middleware if needed
4. Add tests for the new exception type
5. Update documentation
