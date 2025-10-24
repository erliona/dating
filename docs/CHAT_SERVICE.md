# Chat Service Documentation

## Overview

The Chat Service handles real-time messaging between matched users, including message history, read receipts, user blocking, and reporting functionality.

## Endpoints

### 1. WebSocket Connection
**WS** `/chat/connect`

Establish real-time WebSocket connection for live messaging.

**Query Parameters:**
- `token` (required): JWT authentication token

**WebSocket Messages:**
```json
// Send message
{
  "type": "message",
  "conversation_id": 123,
  "content": "Hello!",
  "content_type": "text"
}

// Receive message
{
  "type": "message",
  "message_id": 456,
  "sender_id": 789,
  "content": "Hi there!",
  "content_type": "text",
  "sent_at": "2024-01-24T10:30:00Z"
}

// Read receipt
{
  "type": "read",
  "message_id": 456,
  "read_at": "2024-01-24T10:31:00Z"
}
```

### 2. Get Conversations
**GET** `/chat/conversations`

Retrieve user's conversations.

**Query Parameters:**
- `user_id` (required): User ID
- `limit` (optional): Number of conversations (default: 20)
- `offset` (optional): Pagination offset

**Response:**
```json
{
  "conversations": [
    {
      "id": 123,
      "user_id": 456,
      "other_user_id": 789,
      "other_user_name": "Alice",
      "other_user_photo": "photo.jpg",
      "last_message": "Hey! How are you?",
      "last_message_sender": 789,
      "unread_count": 2,
      "updated_at": "2024-01-24T10:30:00Z",
      "created_at": "2024-01-24T09:00:00Z"
    }
  ],
  "total": 1
}
```

### 3. Get Messages
**GET** `/chat/conversations/{conversation_id}/messages`

Retrieve messages from a specific conversation.

**Path Parameters:**
- `conversation_id` (required): Conversation ID

**Query Parameters:**
- `limit` (optional): Number of messages (default: 50)
- `offset` (optional): Pagination offset

**Response:**
```json
{
  "messages": [
    {
      "id": 456,
      "conversation_id": 123,
      "sender_id": 789,
      "content": "Hello!",
      "content_type": "text",
      "created_at": "2024-01-24T10:30:00Z",
      "read_at": "2024-01-24T10:31:00Z"
    }
  ],
  "total": 1
}
```

### 4. Send Message
**POST** `/chat/messages`

Send a new message.

**Request Body:**
```json
{
  "conversation_id": 123,
  "user_id": 456,
  "content": "Hello!",
  "content_type": "text"
}
```

**Response:**
```json
{
  "message_id": 789,
  "sent_at": "2024-01-24T10:30:00Z"
}
```

### 5. Mark Message as Read
**PUT** `/chat/messages/{message_id}/read`

Mark a message as read.

**Path Parameters:**
- `message_id` (required): Message ID

**Headers:**
- `Authorization: Bearer <jwt_token>`

**Response:**
```json
{
  "success": true,
  "read_at": "2024-01-24T10:31:00Z"
}
```

### 6. Block Conversation
**POST** `/chat/conversations/{conversation_id}/block`

Block a conversation/user.

**Path Parameters:**
- `conversation_id` (required): Conversation ID

**Headers:**
- `Authorization: Bearer <jwt_token>`

**Response:**
```json
{
  "success": true,
  "blocked_at": "2024-01-24T10:30:00Z"
}
```

### 7. Report Conversation
**POST** `/chat/conversations/{conversation_id}/report`

Report a conversation/user.

**Path Parameters:**
- `conversation_id` (required): Conversation ID

**Headers:**
- `Authorization: Bearer <jwt_token>`

**Request Body:**
```json
{
  "report_type": "spam",
  "reason": "Sending unwanted messages"
}
```

**Response:**
```json
{
  "success": true,
  "report_id": "report_123",
  "reported_at": "2024-01-24T10:30:00Z"
}
```

## WebSocket Implementation

### Connection Management
```python
async def websocket_handler(request: web.Request):
    """WebSocket connection handler."""
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    
    try:
        async for msg in ws:
            if msg.type == web.WSMsgType.TEXT:
                # Handle incoming message
                await handle_websocket_message(ws, msg.data)
            elif msg.type == web.WSMsgType.ERROR:
                logger.error(f"WebSocket error: {ws.exception()}")
    except Exception as e:
        logger.error(f"WebSocket handler error: {e}")
    finally:
        logger.info("WebSocket connection closed")
    
    return ws
```

### Message Types
- **message**: Text message
- **read**: Read receipt
- **typing**: Typing indicator
- **online**: User online status
- **offline**: User offline status

### Real-time Features
- **Live Messaging**: Instant message delivery
- **Read Receipts**: Message read status
- **Typing Indicators**: Show when user is typing
- **Online Status**: User presence
- **Message History**: Persistent message storage

## Security Features

### Authentication
- **JWT Token**: Required for all endpoints
- **User Validation**: Verify user ownership
- **Conversation Access**: Check user permissions

### Privacy Protection
- **Message Encryption**: End-to-end encryption (planned)
- **Data Retention**: Automatic cleanup of old messages
- **Block/Report**: User safety features
- **Audit Logging**: Track all user interactions

### Rate Limiting
- **Message Rate**: 10 messages per minute per user
- **Connection Limit**: 5 WebSocket connections per user
- **Report Limit**: 5 reports per day per user

## Event Publishing

### Message Events
```python
# Message sent event
await event_publisher.publish_event(
    "message.sent",
    {
        "conversation_id": conversation_id,
        "sender_id": user_id,
        "content": content,
        "sent_at": timestamp
    }
)

# Message read event
await event_publisher.publish_event(
    "message.read",
    {
        "message_id": message_id,
        "reader_id": user_id,
        "read_at": timestamp
    }
)
```

### Block/Report Events
```python
# Block event
await event_publisher.publish_block_event(
    user_id=user_id,
    conversation_id=conversation_id
)

# Report event
await event_publisher.publish_report_event(
    user_id=user_id,
    conversation_id=conversation_id,
    report_type=report_type,
    reason=reason
)
```

## Database Schema

### Messages Table
```sql
CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    conversation_id INTEGER NOT NULL,
    sender_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    content_type VARCHAR(20) DEFAULT 'text',
    created_at TIMESTAMP DEFAULT NOW(),
    read_at TIMESTAMP NULL,
    FOREIGN KEY (conversation_id) REFERENCES conversations(id),
    FOREIGN KEY (sender_id) REFERENCES users(id)
);
```

### Conversations Table
```sql
CREATE TABLE conversations (
    id SERIAL PRIMARY KEY,
    user1_id INTEGER NOT NULL,
    user2_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (user1_id) REFERENCES users(id),
    FOREIGN KEY (user2_id) REFERENCES users(id),
    UNIQUE(user1_id, user2_id)
);
```

### Blocked Users Table
```sql
CREATE TABLE blocked_users (
    id SERIAL PRIMARY KEY,
    blocker_id INTEGER NOT NULL,
    blocked_id INTEGER NOT NULL,
    blocked_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (blocker_id) REFERENCES users(id),
    FOREIGN KEY (blocked_id) REFERENCES users(id),
    UNIQUE(blocker_id, blocked_id)
);
```

### Reports Table
```sql
CREATE TABLE reports (
    id SERIAL PRIMARY KEY,
    reporter_id INTEGER NOT NULL,
    reported_id INTEGER NOT NULL,
    conversation_id INTEGER NULL,
    report_type VARCHAR(50) NOT NULL,
    reason TEXT NOT NULL,
    status VARCHAR(20) DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT NOW(),
    FOREIGN KEY (reporter_id) REFERENCES users(id),
    FOREIGN KEY (reported_id) REFERENCES users(id),
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);
```

## Performance Optimization

### Database Indexes
```sql
-- Message queries
CREATE INDEX idx_messages_conversation ON messages(conversation_id, created_at DESC);
CREATE INDEX idx_messages_sender ON messages(sender_id, created_at DESC);

-- Conversation queries
CREATE INDEX idx_conversations_user1 ON conversations(user1_id, updated_at DESC);
CREATE INDEX idx_conversations_user2 ON conversations(user2_id, updated_at DESC);

-- Block/Report queries
CREATE INDEX idx_blocked_users_blocker ON blocked_users(blocker_id);
CREATE INDEX idx_reports_reporter ON reports(reporter_id);
CREATE INDEX idx_reports_reported ON reports(reported_id);
```

### Caching Strategy
- **Active Conversations**: 15-minute TTL for active conversations
- **Message History**: 1-hour TTL for recent messages
- **User Status**: 5-minute TTL for online status
- **Blocked Users**: 30-minute TTL for blocked user lists

### WebSocket Optimization
- **Connection Pooling**: Reuse WebSocket connections
- **Message Batching**: Batch multiple messages
- **Compression**: Gzip WebSocket messages
- **Heartbeat**: Keep connections alive

## Error Handling

### Common Errors
- **400 Bad Request**: Missing required parameters
- **401 Unauthorized**: Invalid or missing JWT token
- **403 Forbidden**: User not authorized for conversation
- **404 Not Found**: Conversation or message not found
- **500 Internal Server Error**: Service unavailable

### Error Response Format
```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": {
    "field": "validation error"
  },
  "timestamp": "2024-01-24T10:30:00Z"
}
```

## Testing

### Unit Tests
- **Endpoint Testing**: All endpoints with various inputs
- **WebSocket Testing**: Connection and message handling
- **Authentication Testing**: JWT validation
- **Error Handling**: Edge cases and failures

### Integration Tests
- **Data Service Integration**: Database operations
- **Event Publishing**: Message queue integration
- **WebSocket Communication**: Real-time messaging
- **End-to-End**: Complete user flows

## Monitoring & Analytics

### Key Metrics
- **Message Rate**: Messages per minute
- **Active Conversations**: Number of active chats
- **WebSocket Connections**: Active connections
- **Block/Report Rate**: Safety metrics

### Alerts
- **High Error Rate**: >5% error rate
- **Slow Response**: >2s response time
- **WebSocket Failures**: >10% connection failures
- **High Report Rate**: >20 reports per hour

## Future Enhancements

### Planned Features
- **Message Encryption**: End-to-end encryption
- **File Sharing**: Image and document sharing
- **Voice Messages**: Audio message support
- **Video Calls**: Video chat integration
- **Message Reactions**: Emoji reactions
- **Message Threading**: Reply to specific messages

### Performance Improvements
- **Message Search**: Full-text search
- **Message Archiving**: Long-term storage
- **Push Notifications**: Mobile notifications
- **Message Scheduling**: Send later feature
- **Message Templates**: Quick replies
