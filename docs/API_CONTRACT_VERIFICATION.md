# API Contract Verification

## Bot ↔ Profile Service Contract

### POST /profiles/ (Create Profile)

**Bot Request:**
```json
{
  "telegram_id": 12345,
  "username": "johndoe",
  "first_name": "John",
  "language_code": "en",
  "is_premium": false,
  "name": "John Doe",
  "birth_date": "1990-01-01",
  "gender": "male",
  "orientation": "female",
  "goal": "relationship",
  "bio": "Hello world",
  "city": "Moscow",
  "country": "Russia",
  "latitude": 55.7558,
  "longitude": 37.6173,
  "geohash": "ucfv0j",
  "interests": ["travel", "music"],
  "height_cm": 180,
  "education": "university",
  "has_children": false,
  "wants_children": true,
  "smoking": false,
  "drinking": false,
  "hide_age": false,
  "hide_distance": false,
  "hide_online": false,
  "is_complete": true
}
```

**Service Response (Success):**
```json
{
  "user_id": 1,
  "name": "John Doe",
  "gender": "male",
  "city": "Moscow",
  "goal": "relationship",
  "created": true
}
```

**Error Responses:**

| Status | Error Code | Message | When |
|--------|-----------|---------|------|
| 400 | `validation_error` | Missing required field | Required field missing |
| 409 | `conflict` | Profile already exists for this user | Duplicate profile |
| 500 | `internal_error` | Internal server error | Server error |

✅ **Status**: Contracts match. Bot sends all required fields, service accepts them.

### GET /profiles/{user_id}

**Bot Request:**
```
GET /profiles/123
```

**Service Response (Success):**
```json
{
  "user_id": 123,
  "name": "John Doe",
  "age": 33,
  "gender": "male",
  "city": "Moscow",
  "bio": "Hello world",
  "photos": []
}
```

**Error Responses:**

| Status | Error Code | Message | When |
|--------|-----------|---------|------|
| 404 | `not_found` | Profile not found | Profile doesn't exist |
| 500 | `internal_error` | Internal server error | Server error |

✅ **Status**: Contract verified. Bot handles 404 by returning None.

## API Gateway Health Check

### GET /health

**Response:**
```json
{
  "status": "healthy",
  "service": "api-gateway",
  "routes": {
    "auth": "http://auth-service:8081",
    "profile": "http://profile-service:8082",
    "discovery": "http://discovery-service:8083",
    "media": "http://media-service:8084",
    "chat": "http://chat-service:8085",
    "admin": "http://admin-service:8086"
  }
}
```

✅ **Status**: Gateway has `/health` endpoint. Bot can use `api_client.health_check()`.

## Authentication

### Current State
- Bot creates profiles with `telegram_id`
- Profile service creates/updates user based on `telegram_id`
- No JWT required for profile creation from bot (service trusts internal network)

### For WebApp Endpoints
- WebApp uses JWT tokens
- JWT generated via `/api/auth/token`
- JWT validated in bot/api.py handlers

✅ **Status**: Auth contracts clear. Internal requests (bot→gateway) trust network, external requests (webapp→api) use JWT.

## Rate Limits

### API Gateway Client
- Default timeout: 30 seconds
- Max retries: 3 attempts
- Retry backoff: 1s, 2s, 4s (exponential)
- Only 5xx and network errors trigger retries
- 4xx errors fail immediately

### Profile Service
- No explicit rate limits in service code
- Rate limiting should be implemented at API Gateway level

⚠️ **Recommendation**: Add rate limiting to API Gateway (e.g., 100 req/min per client).

## Error Code Standards

### Standard Error Response Format
```json
{
  "error": {
    "code": "error_code",
    "message": "Human readable message"
  }
}
```

### Common Error Codes

| Code | Status | Meaning | Retry? |
|------|--------|---------|--------|
| `validation_error` | 400 | Invalid request data | ❌ No |
| `not_found` | 404 | Resource not found | ❌ No |
| `conflict` | 409 | Resource already exists | ❌ No |
| `unauthorized` | 401 | Missing/invalid auth | ❌ No |
| `server_error` | 500 | Internal server error | ✅ Yes |
| `service_unavailable` | 503 | Service temporarily down | ✅ Yes |
| `gateway_timeout` | 504 | Gateway timeout | ✅ Yes |

✅ **Status**: Bot API client follows this standard with `APIGatewayError`.

## Idempotency

### Profile Creation
- Bot generates idempotency key: `profile-create-{telegram_id}`
- Sent in `Idempotency-Key` header
- Profile service should check for duplicate operations

⚠️ **TODO**: Profile service needs to implement idempotency key checking.

### Implementation Recommendation
```python
# In profile service
idempotency_key = request.headers.get("Idempotency-Key")
if idempotency_key:
    # Check if operation with this key already completed
    cached_response = await check_idempotency_cache(idempotency_key)
    if cached_response:
        return cached_response
    
# Proceed with operation
result = await create_profile(...)

# Cache result with idempotency key
if idempotency_key:
    await cache_idempotency_result(idempotency_key, result)
```

## Timeouts

### Bot API Client
- Total timeout: 30 seconds (configurable)
- Connect timeout: 10 seconds
- Read timeout: 20 seconds (implicit)

### Recommendations
- Profile operations: 5-10 seconds
- Discovery operations: 10-15 seconds
- Photo uploads: 30-60 seconds

## Service Discovery

### Current Approach
- API Gateway URL: `http://api-gateway:8080` (hardcoded in config)
- Gateway routes to services: `http://profile-service:8082`, etc.

### Health Checks
- Bot can check Gateway health: `GET /health`
- Services should also expose health checks
- Gateway health endpoint lists all service URLs

✅ **Status**: Service discovery working. Bot configured via `API_GATEWAY_URL` env var.

## Summary

| Aspect | Status | Notes |
|--------|--------|-------|
| DTOs/Schemas | ✅ Verified | Bot and service contracts match |
| Error Codes | ✅ Standardized | Consistent format across services |
| Authentication | ✅ Verified | Internal trust, external JWT |
| Rate Limits | ⚠️ TODO | Should be added to Gateway |
| Idempotency | ⚠️ Partial | Client sends keys, service should check |
| Timeouts | ✅ Configured | 30s default, configurable |
| Health Checks | ✅ Available | Gateway has /health endpoint |
| Retries | ✅ Implemented | 3 retries with exponential backoff |
| Error Handling | ✅ Proper | 4xx immediate fail, 5xx retry |

## Next Steps

1. **Add rate limiting to API Gateway** - Prevent abuse
2. **Implement idempotency checking in Profile Service** - Prevent duplicate creates
3. **Add health checks to all microservices** - Improve observability
4. **Add `/api/*` routes to Gateway** - Support WebApp endpoints
5. **Add request/response validation schemas** - Use Pydantic or similar
