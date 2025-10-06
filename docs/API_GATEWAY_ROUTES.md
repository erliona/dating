# API Gateway Routes

## Overview

The API Gateway provides a unified entry point for all frontend and backend requests. It supports two routing patterns:

1. **Direct Service Routes** (`/profiles/*`, `/discovery/*`, etc.) - For internal microservice-to-microservice communication
2. **Unified API Routes** (`/api/*`) - For frontend/WebApp public API access

## Public API Routes (`/api/*`)

All frontend requests should use the `/api/*` prefix for a consistent, unified API interface.

### Authentication (`/api/auth/*`)

Routes to: **Auth Service** (port 8081)

| Method | Endpoint | Maps To | Description |
|--------|----------|---------|-------------|
| POST | `/api/auth/token` | `/auth/token` | Generate JWT token |
| * | `/api/auth/*` | `/auth/*` | Other auth operations |

**Example:**
```bash
# Frontend request
POST https://your-domain.com/api/auth/token

# Gateway forwards to
POST http://auth-service:8081/auth/token
```

### Profile (`/api/profile/*`)

Routes to: **Profile Service** (port 8082)

| Method | Endpoint | Maps To | Description |
|--------|----------|---------|-------------|
| GET | `/api/profile/check` | `/profiles/check` | Check if profile exists |
| GET | `/api/profile` | `/profiles` | Get user profile |
| PATCH | `/api/profile` | `/profiles` | Update user profile |
| * | `/api/profile/*` | `/profiles/*` | Other profile operations |

**Example:**
```bash
# Frontend request
GET https://your-domain.com/api/profile/check?user_id=123

# Gateway forwards to
GET http://profile-service:8082/profiles/check?user_id=123
```

### Discovery & Matching (`/api/discover`, `/api/like`, `/api/pass`, `/api/matches`)

Routes to: **Discovery Service** (port 8083)

| Method | Endpoint | Maps To | Description |
|--------|----------|---------|-------------|
| GET | `/api/discover` | `/discovery/discover` | Get discovery cards |
| POST | `/api/like` | `/discovery/like` | Like a profile |
| POST | `/api/pass` | `/discovery/pass` | Pass on a profile |
| GET | `/api/matches` | `/discovery/matches` | Get user's matches |
| GET | `/api/favorites` | `/discovery/favorites` | Get favorites list |
| POST | `/api/favorites` | `/discovery/favorites` | Add to favorites |
| DELETE | `/api/favorites/{id}` | `/discovery/favorites/{id}` | Remove from favorites |

**Example:**
```bash
# Frontend request
POST https://your-domain.com/api/like
Content-Type: application/json
{"target_id": 456}

# Gateway forwards to
POST http://discovery-service:8083/discovery/like
Content-Type: application/json
{"target_id": 456}
```

### Media & Photos (`/api/photos/*`)

Routes to: **Media Service** (port 8084)

| Method | Endpoint | Maps To | Description |
|--------|----------|---------|-------------|
| POST | `/api/photos/upload` | `/media/upload` | Upload photo |
| GET | `/api/photos/{id}` | `/media/{id}` | Get photo |
| DELETE | `/api/photos/{id}` | `/media/{id}` | Delete photo |

**Example:**
```bash
# Frontend request
POST https://your-domain.com/api/photos/upload
Content-Type: multipart/form-data

# Gateway forwards to
POST http://media-service:8084/media/upload
Content-Type: multipart/form-data
```

## Internal Service Routes

These routes are for internal microservice-to-microservice communication and should not be exposed externally.

| Prefix | Service | Port | Description |
|--------|---------|------|-------------|
| `/auth/*` | Auth Service | 8081 | Direct auth access |
| `/profiles/*` | Profile Service | 8082 | Direct profile access |
| `/discovery/*` | Discovery Service | 8083 | Direct discovery access |
| `/media/*` | Media Service | 8084 | Direct media access |
| `/chat/*` | Chat Service | 8085 | Direct chat access |
| `/admin/*` | Admin Service | 8086 | Direct admin access |

## Health Check

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health` | Gateway health status and service URLs |

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

## Gateway Configuration

### Environment Variables

```bash
# Service URLs (internal Docker network)
AUTH_SERVICE_URL=http://auth-service:8081
PROFILE_SERVICE_URL=http://profile-service:8082
DISCOVERY_SERVICE_URL=http://discovery-service:8083
MEDIA_SERVICE_URL=http://media-service:8084
CHAT_SERVICE_URL=http://chat-service:8085
ADMIN_SERVICE_URL=http://admin-service:8086

# Gateway settings
GATEWAY_HOST=0.0.0.0
GATEWAY_PORT=8080
```

### Timeouts

- **Total timeout**: 30 seconds
- **Connect timeout**: 10 seconds

## Migration from bot/api.py

### Before (bot/api.py endpoints)
```javascript
// WebApp called bot API server directly
const API_BASE_URL = window.location.protocol + '//' + window.location.hostname + ':8080';
fetch(`${API_BASE_URL}/api/profile`);  // → bot/api.py → Database
```

### After (API Gateway routes)
```javascript
// WebApp calls API Gateway which routes to microservices
const API_BASE_URL = window.location.protocol + '//' + window.location.hostname + ':8080';
fetch(`${API_BASE_URL}/api/profile`);  // → API Gateway → Profile Service → Database
```

### Benefits

1. **Single Entry Point**: All requests through port 8080 (API Gateway)
2. **Unified API**: Consistent `/api/*` prefix for all public endpoints
3. **Service Isolation**: Frontend doesn't need to know about individual microservices
4. **Scalability**: Can add rate limiting, auth, caching at Gateway level
5. **Flexibility**: Can change backend service locations without frontend changes

## Examples

### Complete Request Flow

```
Frontend Request:
  POST https://your-domain.com/api/profile
  Authorization: Bearer jwt_token
  Content-Type: application/json
  {"name": "John", "bio": "Hello"}

↓

API Gateway (port 8080):
  - Receives request at /api/profile
  - Maps to /profiles
  - Forwards to Profile Service

↓

Profile Service (port 8082):
  - Receives at /profiles
  - Validates request
  - Updates database
  - Returns response

↓

API Gateway:
  - Forwards response back to frontend

↓

Frontend:
  - Receives response
  - Updates UI
```

### WebApp Configuration

The WebApp is already configured to use the API Gateway:

```javascript
// webapp/js/app.js
const API_BASE_URL = window.location.protocol + '//' + window.location.hostname + ':8080';

// All these now work through API Gateway
fetch(`${API_BASE_URL}/api/profile`);          // ✅ Works
fetch(`${API_BASE_URL}/api/photos/upload`);    // ✅ Works
fetch(`${API_BASE_URL}/api/like`);             // ✅ Works
fetch(`${API_BASE_URL}/api/matches`);          // ✅ Works
```

## Testing

### Health Check
```bash
curl http://localhost:8080/health
```

### Profile Check
```bash
curl -H "Authorization: Bearer YOUR_JWT" \
     http://localhost:8080/api/profile/check?user_id=123
```

### Upload Photo
```bash
curl -X POST \
     -H "Authorization: Bearer YOUR_JWT" \
     -F "photo=@/path/to/image.jpg" \
     http://localhost:8080/api/photos/upload
```

## Security Considerations

1. **Rate Limiting**: Should be implemented at Gateway level
2. **Authentication**: JWT validation can be done at Gateway or service level
3. **CORS**: Configure CORS headers at Gateway for WebApp access
4. **TLS**: Use HTTPS in production (Traefik handles SSL termination)
5. **Internal Network**: Microservices should only be accessible via Gateway

## Performance

- Gateway adds ~1-2ms latency
- Uses connection pooling for backend requests
- Configurable timeouts prevent hanging requests
- Can implement caching at Gateway level if needed

## Troubleshooting

### Request not reaching service

1. Check Gateway logs: `docker logs api-gateway`
2. Verify service is running: `docker ps | grep service-name`
3. Check Gateway can reach service: `docker exec api-gateway curl http://profile-service:8082/health`

### Timeout errors

1. Check service response time
2. Increase Gateway timeout if needed
3. Check for network issues between containers

### 503 Service Unavailable

1. Service might be down
2. Service URL might be misconfigured
3. Check Gateway configuration: `docker exec api-gateway env | grep SERVICE_URL`
