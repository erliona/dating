# Chat API Protocol Specification

**Version**: 1.0  
**Last Updated**: 2025-01-24

## Overview

This document defines the complete Chat API protocol for the dating platform, including idempotency, read-state semantics, pagination, WebSocket events, and database schema.

## 1. Idempotency for Message Sending

### Headers
- `Idempotency-Key: <uuid>` (REQUIRED for POST messages)
- `Authorization: Bearer <jwt_token>`

### Database Schema
```sql
-- Unique constraint for idempotency
ALTER TABLE messages ADD CONSTRAINT unique_idempotency 
UNIQUE (conversation_id, sender_id, idempotency_key);

-- TTL for idempotency keys (24 hours)
ALTER TABLE messages ADD COLUMN idempotency_expires_at TIMESTAMP;
```

### Response Codes
- `201 Created` + `Location: /chat/messages/{message_id}` - First insertion
- `200 OK` - Idempotent replay (returns same message_id)
- `422 Unprocessable Entity` - Validation error
- `409 Conflict` - Duplicate idempotency key (should not happen with proper handling)

### Example
```http
POST /chat/conversations/c1/messages
Idempotency-Key: 550e8400-e29b-41d4-a716-446655440000
Content-Type: application/json

{
  "content": "Hello!",
  "content_type": "text"
}

# Response (201)
Location: /chat/messages/m123
{
  "message_id": "m123",
  "conversation_id": "c1",
  "sender_id": "u42",
  "content": "Hello!",
  "content_type": "text",
  "created_at": "2025-01-24T10:30:00Z"
}
```

## 2. Read-State Semantics

### Request Format
```http
PUT /chat/conversations/{conversation_id}/read-state
Content-Type: application/json

{
  "up_to_message_id": "m123"
}
```

### Database Schema
```sql
CREATE TABLE participant_read_state (
  conversation_id UUID NOT NULL,
  user_id UUID NOT NULL,
  last_read_message_id UUID NOT NULL,
  last_read_at TIMESTAMP NOT NULL DEFAULT NOW(),
  PRIMARY KEY (conversation_id, user_id),
  FOREIGN KEY (conversation_id) REFERENCES conversations(id),
  FOREIGN KEY (last_read_message_id) REFERENCES messages(id)
);
```

### Response Codes
- `204 No Content` - Success (always idempotent)
- `404 Not Found` - Conversation or message not found
- `422 Unprocessable Entity` - Message doesn't belong to conversation

### Server Logic
1. Validate `up_to_message_id` exists in conversation
2. Update or insert `participant_read_state`
3. Server automatically sets `read_at` on all messages up to `up_to_message_id`
4. Return `204` (no body)

## 3. Pagination

### Messages Pagination
```http
GET /chat/conversations/{id}/messages?before_id=m123&limit=50
GET /chat/conversations/{id}/messages?after_id=m456&limit=50
```

**Parameters:**
- `before_id` - Get messages before this ID (exclusive)
- `after_id` - Get messages after this ID (exclusive)  
- `limit` - Max 50 messages (default: 50)

**Order:** `ASC` by `(created_at, id)` for stable pagination

**Response Headers:**
```http
Link: </chat/conversations/c1/messages?before_id=m100&limit=50>; rel="next"
X-Has-More: true
```

### Conversations Pagination
```http
GET /chat/conversations?cursor=eyJ0aW1lIjoiMjAyNS0wMS0yNFQxMDozMDowMFoifQ&limit=20&with_unread_only=true&sort=last_message_at.desc
```

**Parameters:**
- `cursor` - Opaque token based on `(last_message_at, id)`
- `limit` - Max 20 conversations (default: 20)
- `with_unread_only` - Filter conversations with unread messages
- `sort` - `last_message_at.desc` (default)

## 4. WebSocket Contract

### Connection
```javascript
// URL with optional conversation context
const ws = new WebSocket('wss://api.dating.serge.cc/chat/ws?conversation_id=c1');

// Authentication via query param or header
ws.send(JSON.stringify({
  type: 'auth',
  token: 'jwt_token_here'
}));
```

### Server → Client Events

#### Message Created
```json
{
  "type": "message.created",
  "conversation_id": "c1",
  "message": {
    "id": "m123",
    "sender_id": "u42",
    "content": "Hello!",
    "content_type": "text",
    "created_at": "2025-01-24T10:30:00Z"
  }
}
```

#### Message Read
```json
{
  "type": "message.read",
  "conversation_id": "c1",
  "user_id": "u42",
  "up_to_message_id": "m123",
  "read_at": "2025-01-24T10:31:00Z"
}
```

#### Typing Indicator
```json
{
  "type": "conversation.typing",
  "conversation_id": "c1",
  "user_id": "u99",
  "state": "on"
}
```

#### User Blocked
```json
{
  "type": "conversation.blocked",
  "conversation_id": "c1",
  "by_user_id": "u42",
  "target_user_id": "u99"
}
```

### Client → Server Events

#### Send Message
```json
{
  "type": "message.send",
  "conversation_id": "c1",
  "idempotency_key": "550e8400-e29b-41d4-a716-446655440000",
  "content": "Hello!",
  "content_type": "text"
}
```

#### Set Read State
```json
{
  "type": "read.set",
  "conversation_id": "c1",
  "up_to_message_id": "m123"
}
```

#### Typing Indicator
```json
{
  "type": "typing.set",
  "conversation_id": "c1",
  "state": "on"
}
```

### Error Format
```json
{
  "type": "error",
  "code": "invalid_request",
  "message": "Content is required",
  "details": {
    "field": "content"
  },
  "request_id": "req_123"
}
```

## 5. Blocks and Reports

### Blocks Resource
```http
# Block user
POST /chat/blocks
{
  "target_user_id": "u99"
}
# Response: 201 Created + Location: /chat/blocks/u99

# Unblock user  
DELETE /chat/blocks/u99
# Response: 204 No Content
```

**Side Effects:**
- Mark existing conversations as `blocked=true`
- Send `conversation.blocked` event to both participants
- Hide blocked user from discovery

### Reports Resource
```http
POST /chat/reports
{
  "conversation_id": "c1",
  "message_id": "m7",  // Optional
  "reason": "spam",
  "comment": "Inappropriate content"  // Optional
}
# Response: 202 Accepted (async moderation)
```

**Database Schema:**
```sql
CREATE TABLE chat_reports (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  reporter_id UUID NOT NULL,
  conversation_id UUID NOT NULL,
  message_id UUID NULL,
  reason VARCHAR(50) NOT NULL,
  comment TEXT,
  status VARCHAR(20) DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT NOW(),
  reviewed_at TIMESTAMP NULL,
  reviewed_by UUID NULL
);
```

## 6. HTTP Status Codes

| Code | Usage | Body |
|------|-------|------|
| `201` | Resource created | Resource data |
| `202` | Async operation | Operation ID |
| `204` | Idempotent update/delete | Empty |
| `400` | Bad request | Error details |
| `401` | Unauthorized | Error message |
| `404` | Not found | Error message |
| `422` | Validation error | Field errors |
| `429` | Rate limited | Retry info |

## 7. Error Response Format

```json
{
  "error": {
    "code": "validation_error",
    "message": "Invalid input data",
    "details": {
      "field": "content",
      "reason": "Content is required"
    },
    "request_id": "req_123"
  }
}
```

## 8. Rate Limiting

| Endpoint | Limit | Window |
|----------|-------|--------|
| `POST /chat/conversations/{id}/messages` | 10/sec | Per user |
| `POST /chat/reports` | 5/day | Per user |
| `POST /chat/blocks` | 10/day | Per user |
| WebSocket events | 50/sec | Per connection |

## 9. Database Schema

### Messages Table
```sql
CREATE TABLE messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  conversation_id UUID NOT NULL,
  sender_id UUID NOT NULL,
  content TEXT NOT NULL,
  content_type VARCHAR(20) DEFAULT 'text',
  idempotency_key UUID,
  idempotency_expires_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW(),
  read_at TIMESTAMP NULL,
  UNIQUE(conversation_id, sender_id, idempotency_key)
);

-- Indexes for pagination
CREATE INDEX idx_messages_conversation_time 
ON messages (conversation_id, created_at DESC, id DESC);
```

### Participant Read State
```sql
CREATE TABLE participant_read_state (
  conversation_id UUID NOT NULL,
  user_id UUID NOT NULL,
  last_read_message_id UUID NOT NULL,
  last_read_at TIMESTAMP DEFAULT NOW(),
  PRIMARY KEY (conversation_id, user_id)
);
```

### Blocks Table
```sql
CREATE TABLE chat_blocks (
  blocker_id UUID NOT NULL,
  target_user_id UUID NOT NULL,
  created_at TIMESTAMP DEFAULT NOW(),
  PRIMARY KEY (blocker_id, target_user_id)
);
```

## 10. OpenAPI Specification

### POST /chat/conversations/{id}/messages
```yaml
post:
  summary: Send a new message
  parameters:
    - in: path
      name: id
      required: true
      schema: { type: string }
    - in: header
      name: Idempotency-Key
      required: true
      schema: { type: string, format: uuid }
  requestBody:
    required: true
    content:
      application/json:
        schema:
          type: object
          properties:
            content: { type: string, maxLength: 4000 }
            content_type: { type: string, enum: ["text", "image", "file"] }
          required: [content]
  responses:
    "201":
      description: Created
      headers:
        Location:
          schema: { type: string }
    "200": 
      description: Idempotent replay
    "422": 
      description: Validation error
```

### PUT /chat/conversations/{id}/read-state
```yaml
put:
  summary: Set read state up to a message
  parameters:
    - in: path
      name: id
      required: true
      schema: { type: string }
  requestBody:
    required: true
    content:
      application/json:
        schema:
          type: object
          properties:
            up_to_message_id: { type: string }
          required: [up_to_message_id]
  responses:
    "204": 
      description: No Content
    "404": 
      description: Conversation or message not found
    "422": 
      description: Message doesn't belong to conversation
```

## 11. Security Considerations

1. **Content Filtering**: All messages pass through content moderation
2. **Media Validation**: Attachments validated for type, size, and content
3. **Rate Limiting**: Per-user limits to prevent spam
4. **Authentication**: JWT required for all endpoints
5. **Authorization**: Users can only access their own conversations
6. **Idempotency**: Prevents duplicate message sending
7. **Audit Logging**: All actions logged for moderation

## 12. Performance Optimizations

1. **Database Indexes**: Optimized for pagination queries
2. **Connection Pooling**: 20 connections per service
3. **Caching**: Read-state cached in Redis (optional)
4. **WebSocket Scaling**: Horizontal scaling with message queues
5. **Pagination**: Cursor-based for consistent results

---

**Implementation Status**: ✅ Complete  
**Testing**: ✅ Unit tests for all endpoints  
**Documentation**: ✅ This specification  
**OpenAPI**: ✅ Generated from code
