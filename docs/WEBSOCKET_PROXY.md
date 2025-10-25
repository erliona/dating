# WebSocket Proxy Documentation

## Overview

This document outlines the WebSocket proxy implementation for the Dating Platform, including real-time messaging, connection management, and event handling.

## Architecture

### WebSocket Flow
```
Client (Telegram Mini App) 
    ↓ WebSocket Connection
Traefik (SSL Termination)
    ↓ WebSocket Proxy
API Gateway (WebSocket Handler)
    ↓ WebSocket Forwarding
Chat Service (WebSocket Server)
    ↓ Event Processing
Message Queue (RabbitMQ)
    ↓ Event Distribution
Other Services (Notification, Discovery)
```

## WebSocket Proxy Implementation

### Gateway WebSocket Handler
```python
# gateway/websocket.py
import asyncio
import json
import logging
from aiohttp import web, WSMsgType
from aiohttp.web import WebSocketResponse

class WebSocketProxy:
    def __init__(self):
        self.active_connections = {}
        self.connection_id_counter = 0
        self.logger = logging.getLogger(__name__)
    
    async def handle_websocket(self, request):
        """Handle WebSocket connection from client."""
        ws = WebSocketResponse()
        await ws.prepare(request)
        
        # Generate unique connection ID
        connection_id = f"conn_{self.connection_id_counter}"
        self.connection_id_counter += 1
        
        # Store connection
        self.active_connections[connection_id] = {
            'ws': ws,
            'user_id': None,
            'conversation_id': None,
            'connected_at': asyncio.get_event_loop().time()
        }
        
        self.logger.info(f"WebSocket connection established: {connection_id}")
        
        try:
            # Forward to chat service
            await self.forward_to_chat_service(connection_id, ws, request)
        except Exception as e:
            self.logger.error(f"WebSocket error: {e}")
        finally:
            # Cleanup connection
            if connection_id in self.active_connections:
                del self.active_connections[connection_id]
            self.logger.info(f"WebSocket connection closed: {connection_id}")
        
        return ws
    
    async def forward_to_chat_service(self, connection_id, client_ws, request):
        """Forward WebSocket connection to chat service."""
        # Extract authentication from query parameters or headers
        auth_token = request.query.get('token') or request.headers.get('Authorization', '').replace('Bearer ', '')
        conversation_id = request.query.get('conversation_id')
        
        # Connect to chat service WebSocket
        chat_service_url = f"ws://chat-service:8084/ws?token={auth_token}"
        if conversation_id:
            chat_service_url += f"&conversation_id={conversation_id}"
        
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(chat_service_url) as chat_ws:
                # Update connection info
                self.active_connections[connection_id]['chat_ws'] = chat_ws
                
                # Start bidirectional forwarding
                await asyncio.gather(
                    self.forward_client_to_chat(connection_id, client_ws, chat_ws),
                    self.forward_chat_to_client(connection_id, client_ws, chat_ws)
                )
    
    async def forward_client_to_chat(self, connection_id, client_ws, chat_ws):
        """Forward messages from client to chat service."""
        try:
            async for msg in client_ws:
                if msg.type == WSMsgType.TEXT:
                    # Parse and validate message
                    try:
                        data = json.loads(msg.data)
                        await self.validate_client_message(data)
                        
                        # Forward to chat service
                        await chat_ws.send_str(msg.data)
                        self.logger.debug(f"Forwarded client message: {data}")
                    except json.JSONDecodeError:
                        await client_ws.send_str(json.dumps({
                            'type': 'error',
                            'code': 'invalid_json',
                            'message': 'Invalid JSON format'
                        }))
                    except ValidationError as e:
                        await client_ws.send_str(json.dumps({
                            'type': 'error',
                            'code': 'validation_error',
                            'message': str(e)
                        }))
                
                elif msg.type == WSMsgType.BINARY:
                    # Forward binary data
                    await chat_ws.send_bytes(msg.data)
                
                elif msg.type == WSMsgType.ERROR:
                    self.logger.error(f"WebSocket error: {client_ws.exception()}")
                    break
                
                elif msg.type == WSMsgType.CLOSE:
                    break
        
        except Exception as e:
            self.logger.error(f"Error forwarding client to chat: {e}")
    
    async def forward_chat_to_client(self, connection_id, client_ws, chat_ws):
        """Forward messages from chat service to client."""
        try:
            async for msg in chat_ws:
                if msg.type == WSMsgType.TEXT:
                    # Parse and validate message
                    try:
                        data = json.loads(msg.data)
                        await self.validate_chat_message(data)
                        
                        # Forward to client
                        await client_ws.send_str(msg.data)
                        self.logger.debug(f"Forwarded chat message: {data}")
                    except json.JSONDecodeError:
                        self.logger.error("Invalid JSON from chat service")
                    except ValidationError as e:
                        self.logger.error(f"Chat message validation error: {e}")
                
                elif msg.type == WSMsgType.BINARY:
                    # Forward binary data
                    await client_ws.send_bytes(msg.data)
                
                elif msg.type == WSMsgType.ERROR:
                    self.logger.error(f"Chat service WebSocket error: {chat_ws.exception()}")
                    break
                
                elif msg.type == WSMsgType.CLOSE:
                    break
        
        except Exception as e:
            self.logger.error(f"Error forwarding chat to client: {e}")
    
    async def validate_client_message(self, data):
        """Validate message from client."""
        required_fields = ['type']
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")
        
        # Validate message type
        valid_types = ['message.send', 'read.set', 'typing.set', 'ping']
        if data['type'] not in valid_types:
            raise ValidationError(f"Invalid message type: {data['type']}")
        
        # Type-specific validation
        if data['type'] == 'message.send':
            if 'conversation_id' not in data or 'text' not in data:
                raise ValidationError("Missing conversation_id or text for message.send")
        
        elif data['type'] == 'read.set':
            if 'conversation_id' not in data or 'up_to_message_id' not in data:
                raise ValidationError("Missing conversation_id or up_to_message_id for read.set")
    
    async def validate_chat_message(self, data):
        """Validate message from chat service."""
        required_fields = ['type']
        for field in required_fields:
            if field not in data:
                raise ValidationError(f"Missing required field: {field}")
        
        # Validate message type
        valid_types = ['message.created', 'message.read', 'conversation.typing', 'conversation.blocked', 'pong']
        if data['type'] not in valid_types:
            raise ValidationError(f"Invalid message type: {data['type']}")

# WebSocket routes
async def websocket_handler(request):
    """WebSocket handler for chat connections."""
    proxy = WebSocketProxy()
    return await proxy.handle_websocket(request)

# Register WebSocket route
app.router.add_get('/v1/chat/ws', websocket_handler)
```

## Chat Service WebSocket Server

### WebSocket Server Implementation
```python
# services/chat/websocket.py
import asyncio
import json
import logging
from aiohttp import web, WSMsgType
from aiohttp.web import WebSocketResponse

class ChatWebSocketServer:
    def __init__(self):
        self.connections = {}
        self.user_connections = {}
        self.conversation_connections = {}
        self.logger = logging.getLogger(__name__)
    
    async def handle_websocket(self, request):
        """Handle WebSocket connection from gateway."""
        ws = WebSocketResponse()
        await ws.prepare(request)
        
        # Authenticate user
        user_id = await self.authenticate_user(request)
        if not user_id:
            await ws.send_str(json.dumps({
                'type': 'error',
                'code': 'authentication_failed',
                'message': 'Invalid authentication token'
            }))
            await ws.close()
            return ws
        
        # Get conversation ID
        conversation_id = request.query.get('conversation_id')
        
        # Register connection
        connection_id = f"chat_{user_id}_{asyncio.get_event_loop().time()}"
        self.connections[connection_id] = {
            'ws': ws,
            'user_id': user_id,
            'conversation_id': conversation_id,
            'connected_at': asyncio.get_event_loop().time()
        }
        
        # Add to user connections
        if user_id not in self.user_connections:
            self.user_connections[user_id] = []
        self.user_connections[user_id].append(connection_id)
        
        # Add to conversation connections
        if conversation_id:
            if conversation_id not in self.conversation_connections:
                self.conversation_connections[conversation_id] = []
            self.conversation_connections[conversation_id].append(connection_id)
        
        self.logger.info(f"Chat WebSocket connected: {connection_id} (user: {user_id})")
        
        try:
            # Start heartbeat
            heartbeat_task = asyncio.create_task(self.heartbeat(connection_id, ws))
            
            # Handle messages
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    await self.handle_message(connection_id, msg.data)
                elif msg.type == WSMsgType.BINARY:
                    await self.handle_binary_message(connection_id, msg.data)
                elif msg.type == WSMsgType.ERROR:
                    self.logger.error(f"WebSocket error: {ws.exception()}")
                    break
                elif msg.type == WSMsgType.CLOSE:
                    break
            
            # Cancel heartbeat
            heartbeat_task.cancel()
            
        except Exception as e:
            self.logger.error(f"WebSocket error: {e}")
        finally:
            # Cleanup connection
            await self.cleanup_connection(connection_id)
        
        return ws
    
    async def handle_message(self, connection_id, message_data):
        """Handle incoming message."""
        try:
            data = json.loads(message_data)
            message_type = data.get('type')
            
            if message_type == 'message.send':
                await self.handle_send_message(connection_id, data)
            elif message_type == 'read.set':
                await self.handle_read_state(connection_id, data)
            elif message_type == 'typing.set':
                await self.handle_typing_state(connection_id, data)
            elif message_type == 'ping':
                await self.send_pong(connection_id)
            else:
                await self.send_error(connection_id, 'invalid_message_type', f"Unknown message type: {message_type}")
        
        except json.JSONDecodeError:
            await self.send_error(connection_id, 'invalid_json', 'Invalid JSON format')
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
            await self.send_error(connection_id, 'processing_error', str(e))
    
    async def handle_send_message(self, connection_id, data):
        """Handle message sending."""
        connection = self.connections[connection_id]
        user_id = connection['user_id']
        conversation_id = data['conversation_id']
        text = data['text']
        idempotency_key = data.get('idempotency_key')
        
        # Validate conversation access
        if not await self.validate_conversation_access(user_id, conversation_id):
            await self.send_error(connection_id, 'access_denied', 'No access to conversation')
            return
        
        # Send message to database
        message_id = await self.save_message(conversation_id, user_id, text, idempotency_key)
        
        # Broadcast to conversation participants
        await self.broadcast_to_conversation(conversation_id, {
            'type': 'message.created',
            'conversation_id': conversation_id,
            'message': {
                'id': message_id,
                'sender_id': user_id,
                'text': text,
                'created_at': asyncio.get_event_loop().time()
            }
        })
    
    async def handle_read_state(self, connection_id, data):
        """Handle read state update."""
        connection = self.connections[connection_id]
        user_id = connection['user_id']
        conversation_id = data['conversation_id']
        up_to_message_id = data['up_to_message_id']
        
        # Update read state in database
        await self.update_read_state(conversation_id, user_id, up_to_message_id)
        
        # Broadcast to conversation participants
        await self.broadcast_to_conversation(conversation_id, {
            'type': 'message.read',
            'conversation_id': conversation_id,
            'user_id': user_id,
            'up_to_message_id': up_to_message_id,
            'read_at': asyncio.get_event_loop().time()
        })
    
    async def handle_typing_state(self, connection_id, data):
        """Handle typing state update."""
        connection = self.connections[connection_id]
        user_id = connection['user_id']
        conversation_id = data['conversation_id']
        state = data['state']  # 'on' or 'off'
        
        # Broadcast typing state to other participants
        await self.broadcast_to_conversation(conversation_id, {
            'type': 'conversation.typing',
            'conversation_id': conversation_id,
            'user_id': user_id,
            'state': state
        }, exclude_user=user_id)
    
    async def broadcast_to_conversation(self, conversation_id, message, exclude_user=None):
        """Broadcast message to all participants in conversation."""
        if conversation_id not in self.conversation_connections:
            return
        
        for connection_id in self.conversation_connections[conversation_id]:
            connection = self.connections.get(connection_id)
            if not connection:
                continue
            
            # Skip excluded user
            if exclude_user and connection['user_id'] == exclude_user:
                continue
            
            try:
                await connection['ws'].send_str(json.dumps(message))
            except Exception as e:
                self.logger.error(f"Error broadcasting to {connection_id}: {e}")
    
    async def heartbeat(self, connection_id, ws):
        """Send heartbeat to keep connection alive."""
        while True:
            try:
                await asyncio.sleep(30)  # Send ping every 30 seconds
                await ws.send_str(json.dumps({'type': 'ping'}))
            except Exception:
                break
    
    async def send_pong(self, connection_id):
        """Send pong response."""
        connection = self.connections.get(connection_id)
        if connection:
            await connection['ws'].send_str(json.dumps({'type': 'pong'}))
    
    async def send_error(self, connection_id, code, message):
        """Send error message."""
        connection = self.connections.get(connection_id)
        if connection:
            await connection['ws'].send_str(json.dumps({
                'type': 'error',
                'code': code,
                'message': message
            }))
    
    async def cleanup_connection(self, connection_id):
        """Cleanup connection resources."""
        if connection_id in self.connections:
            connection = self.connections[connection_id]
            user_id = connection['user_id']
            conversation_id = connection['conversation_id']
            
            # Remove from user connections
            if user_id in self.user_connections:
                self.user_connections[user_id].remove(connection_id)
                if not self.user_connections[user_id]:
                    del self.user_connections[user_id]
            
            # Remove from conversation connections
            if conversation_id and conversation_id in self.conversation_connections:
                self.conversation_connections[conversation_id].remove(connection_id)
                if not self.conversation_connections[conversation_id]:
                    del self.conversation_connections[conversation_id]
            
            # Remove from main connections
            del self.connections[connection_id]
            
            self.logger.info(f"Cleaned up connection: {connection_id}")

# WebSocket routes
async def chat_websocket_handler(request):
    """WebSocket handler for chat service."""
    server = ChatWebSocketServer()
    return await server.handle_websocket(request)

# Register WebSocket route
app.router.add_get('/ws', chat_websocket_handler)
```

## Traefik WebSocket Configuration

### WebSocket Routing
```yaml
# docker-compose.yml
services:
  api-gateway:
    labels:
      - "traefik.http.routers.chat-ws.rule=Host(`dating.serge.cc`) && PathPrefix(`/v1/chat/ws`)"
      - "traefik.http.routers.chat-ws.entrypoints=websecure"
      - "traefik.http.routers.chat-ws.tls.certresolver=letsencrypt"
      - "traefik.http.services.chat-ws.loadbalancer.server.port=8080"
      - "traefik.http.middlewares.chat-ws-headers.headers.customrequestheaders.X-Forwarded-Proto=https"
      - "traefik.http.routers.chat-ws.middlewares=chat-ws-headers"
```

### WebSocket Middleware
```yaml
# WebSocket-specific middleware
labels:
  - "traefik.http.middlewares.chat-ws-headers.headers.customrequestheaders.X-Forwarded-Proto=https"
  - "traefik.http.middlewares.chat-ws-headers.headers.customrequestheaders.X-Real-IP={remote}"
  - "traefik.http.middlewares.chat-ws-headers.headers.customrequestheaders.X-Forwarded-For={remote}"
```

## Client Integration

### Frontend WebSocket Client
```javascript
// webapp/src/composables/useWebSocket.js
import { ref, onMounted, onUnmounted } from 'vue'

export function useWebSocket(url, options = {}) {
  const socket = ref(null)
  const isConnected = ref(false)
  const messages = ref([])
  const error = ref(null)
  
  const connect = () => {
    try {
      // Add authentication token to URL
      const token = localStorage.getItem('jwt_token')
      const wsUrl = `${url}?token=${token}`
      
      socket.value = new WebSocket(wsUrl)
      
      socket.value.onopen = () => {
        isConnected.value = true
        error.value = null
        console.log('WebSocket connected')
      }
      
      socket.value.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          messages.value.push(data)
          
          // Handle different message types
          if (data.type === 'message.created') {
            // Handle new message
            handleNewMessage(data)
          } else if (data.type === 'message.read') {
            // Handle read state update
            handleReadState(data)
          } else if (data.type === 'conversation.typing') {
            // Handle typing indicator
            handleTypingState(data)
          }
        } catch (err) {
          console.error('Error parsing WebSocket message:', err)
        }
      }
      
      socket.value.onclose = () => {
        isConnected.value = false
        console.log('WebSocket disconnected')
      }
      
      socket.value.onerror = (err) => {
        error.value = err
        console.error('WebSocket error:', err)
      }
      
    } catch (err) {
      error.value = err
      console.error('Error creating WebSocket:', err)
    }
  }
  
  const disconnect = () => {
    if (socket.value) {
      socket.value.close()
      socket.value = null
    }
  }
  
  const sendMessage = (message) => {
    if (socket.value && isConnected.value) {
      socket.value.send(JSON.stringify(message))
    }
  }
  
  const sendChatMessage = (conversationId, text, idempotencyKey) => {
    sendMessage({
      type: 'message.send',
      conversation_id: conversationId,
      text: text,
      idempotency_key: idempotencyKey
    })
  }
  
  const setReadState = (conversationId, upToMessageId) => {
    sendMessage({
      type: 'read.set',
      conversation_id: conversationId,
      up_to_message_id: upToMessageId
    })
  }
  
  const setTypingState = (conversationId, state) => {
    sendMessage({
      type: 'typing.set',
      conversation_id: conversationId,
      state: state
    })
  }
  
  const handleNewMessage = (data) => {
    // Emit event or update store
    console.log('New message:', data.message)
  }
  
  const handleReadState = (data) => {
    // Update read state in store
    console.log('Read state updated:', data)
  }
  
  const handleTypingState = (data) => {
    // Update typing indicator
    console.log('Typing state:', data)
  }
  
  onMounted(() => {
    connect()
  })
  
  onUnmounted(() => {
    disconnect()
  })
  
  return {
    socket,
    isConnected,
    messages,
    error,
    connect,
    disconnect,
    sendMessage,
    sendChatMessage,
    setReadState,
    setTypingState
  }
}
```

## Event Types

### Client to Server Events
```javascript
// Message sending
{
  "type": "message.send",
  "conversation_id": "conv_123",
  "text": "Hello!",
  "idempotency_key": "uuid-123"
}

// Read state update
{
  "type": "read.set",
  "conversation_id": "conv_123",
  "up_to_message_id": "msg_456"
}

// Typing indicator
{
  "type": "typing.set",
  "conversation_id": "conv_123",
  "state": "on"  // or "off"
}

// Heartbeat
{
  "type": "ping"
}
```

### Server to Client Events
```javascript
// New message
{
  "type": "message.created",
  "conversation_id": "conv_123",
  "message": {
    "id": "msg_456",
    "sender_id": "user_789",
    "text": "Hello!",
    "created_at": 1640995200
  }
}

// Read state update
{
  "type": "message.read",
  "conversation_id": "conv_123",
  "user_id": "user_789",
  "up_to_message_id": "msg_456",
  "read_at": 1640995200
}

// Typing indicator
{
  "type": "conversation.typing",
  "conversation_id": "conv_123",
  "user_id": "user_789",
  "state": "on"
}

// Conversation blocked
{
  "type": "conversation.blocked",
  "conversation_id": "conv_123",
  "by_user_id": "user_789",
  "target_user_id": "user_101"
}

// Heartbeat response
{
  "type": "pong"
}

// Error
{
  "type": "error",
  "code": "validation_error",
  "message": "Invalid message format"
}
```

## Monitoring and Metrics

### WebSocket Metrics
```python
# gateway/websocket_metrics.py
from prometheus_client import Counter, Histogram, Gauge

# Connection metrics
websocket_connections_total = Counter('websocket_connections_total', 'Total WebSocket connections')
websocket_connections_active = Gauge('websocket_connections_active', 'Active WebSocket connections')
websocket_messages_total = Counter('websocket_messages_total', 'Total WebSocket messages', ['direction', 'type'])
websocket_connection_duration = Histogram('websocket_connection_duration_seconds', 'WebSocket connection duration')
websocket_message_size = Histogram('websocket_message_size_bytes', 'WebSocket message size in bytes')
```

### Health Checks
```python
# gateway/websocket_health.py
async def websocket_health_check():
    """Check WebSocket service health."""
    try:
        # Test connection to chat service
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect('ws://chat-service:8084/ws') as ws:
                await ws.send_str(json.dumps({'type': 'ping'}))
                response = await ws.receive()
                if response.data == json.dumps({'type': 'pong'}):
                    return True
        return False
    except Exception:
        return False
```

## Security Considerations

### Authentication
- JWT token validation on WebSocket connection
- User authentication before message processing
- Conversation access validation

### Rate Limiting
- Per-user message rate limiting
- Connection rate limiting
- Message size limits

### Data Validation
- Message format validation
- Content filtering
- Malicious payload detection

## Performance Optimization

### Connection Pooling
- Reuse WebSocket connections
- Connection lifecycle management
- Automatic reconnection

### Message Batching
- Batch multiple messages
- Reduce WebSocket overhead
- Optimize network usage

### Caching
- Cache user connections
- Cache conversation participants
- Reduce database queries

## Troubleshooting

### Common Issues
1. **Connection Drops**
   - Check network connectivity
   - Verify authentication tokens
   - Monitor service health

2. **Message Loss**
   - Check message validation
   - Verify database connectivity
   - Monitor error logs

3. **Performance Issues**
   - Monitor connection counts
   - Check message rates
   - Analyze resource usage

### Debugging Tools
```bash
# Test WebSocket connection
wscat -c wss://dating.serge.cc/v1/chat/ws?token=your_jwt_token

# Monitor WebSocket logs
docker compose logs -f api-gateway | grep -i websocket

# Check connection metrics
curl http://localhost:8080/metrics | grep websocket
```

## Conclusion

The WebSocket proxy provides real-time communication capabilities for the Dating Platform. Key benefits:

- **Real-time Messaging**: Instant message delivery
- **Typing Indicators**: Live typing status
- **Read Receipts**: Message read confirmation
- **Connection Management**: Robust connection handling
- **Security**: Authentication and validation
- **Performance**: Optimized for high throughput
- **Monitoring**: Comprehensive metrics and logging