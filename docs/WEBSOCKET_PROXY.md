# WebSocket Proxy Implementation

## Overview

The API Gateway now supports WebSocket proxying for real-time communication, specifically for chat functionality.

## Implementation

### WebSocket Detection
```python
def is_websocket_request(request: web.Request) -> bool:
    """Check if request is a WebSocket upgrade request."""
    return (
        request.headers.get('Upgrade', '').lower() == 'websocket' and
        request.headers.get('Connection', '').lower() == 'upgrade'
    )
```

### Bidirectional Proxy
```python
async def proxy_websocket(request, target_url, path_override=None):
    """Handle WebSocket upgrade and bidirectional proxy."""
    # 1. Detect WebSocket upgrade
    # 2. Establish connection to target service
    # 3. Proxy messages bidirectionally
    # 4. Handle connection cleanup
```

## Usage

### Frontend Connection
```javascript
// useWebSocket.js
const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
const host = window.location.host
const wsUrl = `${protocol}//${host}/v1/chat/ws?token=${token}`
const ws = new WebSocket(wsUrl)
```

### Backend Routing
```python
# gateway/main.py
async def route_chat(request: web.Request) -> web.Response:
    """Route chat requests to chat-service with WebSocket support."""
    target_url = request.app["config"]["chat_service_url"]
    
    # Check if this is a WebSocket request
    if is_websocket_request(request):
        return await proxy_websocket(request, target_url)
    
    # Regular HTTP request
    return await proxy_request(request, target_url)
```

## Features

1. **Automatic Detection**: Detects WebSocket upgrade requests
2. **Bidirectional Proxy**: Proxies messages in both directions
3. **Error Handling**: Graceful connection cleanup
4. **Security**: Supports JWT token authentication
5. **Production Ready**: Supports both HTTP and HTTPS

## Benefits

- **Real-time Communication**: WebSocket support for chat
- **Transparent Proxy**: No changes needed in chat-service
- **Secure**: Token-based authentication
- **Scalable**: Can proxy to multiple chat-service instances

## Testing

```bash
# Test WebSocket connection
wscat -c ws://localhost:8080/v1/chat/ws

# Test with authentication
wscat -c "ws://localhost:8080/v1/chat/ws?token=your_jwt_token"
```
