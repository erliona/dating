# API Gateway Routing Strategy

## Overview

The API Gateway uses a simplified `/v1/*` routing strategy with WebSocket support for real-time communication.

## Routing Rules

### 1. Primary Routes (v1 only)
- `/v1/auth/*` → auth-service:8081
- `/v1/profiles/*` → profile-service:8082  
- `/v1/discovery/*` → discovery-service:8083
- `/v1/media/*` → media-service:8084
- `/v1/chat/*` → chat-service:8085 (WebSocket support)
- `/v1/admin/*` → admin-service:8086
- `/v1/notifications/*` → notification-service:8087

### 2. Health & Metrics
- `/health` → api-gateway health check
- `/metrics` → Prometheus metrics

### 3. WebSocket Support
- `/chat/ws` → chat-service WebSocket endpoint
- Automatic upgrade detection and bidirectional proxy

## Removed Complexity

### Legacy Routes (REMOVED)
- ❌ `/api/*` routes (redirected to v1)
- ❌ Legacy redirect functions
- ❌ 8 route_api_* functions
- ❌ Complex path stripping logic

### Simplified Functions (7 total)
- ✅ `route_auth`
- ✅ `route_profile` 
- ✅ `route_discovery`
- ✅ `route_media`
- ✅ `route_chat` (with WebSocket)
- ✅ `route_admin`
- ✅ `route_notifications`

## WebSocket Proxy Implementation

```python
async def proxy_websocket(request, target_url, path_override=None):
    """Handle WebSocket upgrade and bidirectional proxy."""
    # 1. Detect WebSocket upgrade
    # 2. Establish connection to target service
    # 3. Proxy messages bidirectionally
    # 4. Handle connection cleanup
```

## Benefits

1. **Simplified**: 7 route functions vs 13+ legacy functions
2. **Consistent**: All routes use `/v1/*` pattern
3. **WebSocket Ready**: Real-time chat support
4. **Maintainable**: Clear separation of concerns
5. **Performance**: Reduced complexity = better performance

## Migration Path

1. Update all frontend calls to use `/v1/*` endpoints
2. Remove legacy `/api/*` routes
3. Add WebSocket proxy for chat
4. Update Traefik configuration
5. Test all endpoints
