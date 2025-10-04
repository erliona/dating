# Microservices API Reference

This document describes the API endpoints for all microservices in the dating application.

## Table of Contents

- [API Gateway](#api-gateway)
- [Auth Service](#auth-service)
- [Profile Service](#profile-service)
- [Discovery Service](#discovery-service)
- [Media Service](#media-service)
- [Chat Service](#chat-service)

---

## API Gateway

**Base URL**: `http://localhost:8080` (development) or `https://your-domain.com` (production)

The API Gateway routes requests to appropriate microservices. All requests should go through the gateway.

### Health Check

```http
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "service": "api-gateway",
  "routes": {
    "auth": "http://auth-service:8081",
    "profile": "http://profile-service:8082",
    "discovery": "http://discovery-service:8083",
    "media": "http://media-service:8084",
    "chat": "http://chat-service:8085"
  }
}
```

### Routing Rules

The gateway routes requests based on path prefix:

- `/auth/*` → Auth Service (port 8081)
- `/profiles/*` → Profile Service (port 8082)
- `/discovery/*` → Discovery Service (port 8083)
- `/media/*` → Media Service (port 8084)
- `/chat/*` → Chat Service (port 8085)

---

## Auth Service

**Base URL**: `http://localhost:8081` (direct) or via gateway at `/auth`

Handles authentication and JWT token management.

### Validate Telegram InitData

Validates Telegram WebApp initData and generates JWT token.

```http
POST /auth/validate
Content-Type: application/json
```

**Request Body**:
```json
{
  "init_data": "telegram_init_data_string",
  "bot_token": "bot_token_string"
}
```

**Response** (200 OK):
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": 123456789,
  "username": "john_doe"
}
```

**Error Responses**:
- `400 Bad Request`: Missing init_data or bot_token
- `401 Unauthorized`: Invalid init_data
- `500 Internal Server Error`: Server error

### Verify Token

Verifies a JWT token.

```http
GET /auth/verify
Authorization: Bearer <token>
```

**Response** (200 OK):
```json
{
  "valid": true,
  "user_id": 123456789
}
```

**Error Responses**:
- `401 Unauthorized`: Missing, invalid, or expired token
- `500 Internal Server Error`: Server error

### Refresh Token

Generates a new JWT token from an existing valid token.

```http
POST /auth/refresh
Authorization: Bearer <old_token>
```

**Response** (200 OK):
```json
{
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user_id": 123456789
}
```

**Error Responses**:
- `401 Unauthorized`: Missing, invalid, or expired token
- `500 Internal Server Error`: Server error

### Health Check

```http
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "service": "auth"
}
```

---

## Profile Service

**Base URL**: `http://localhost:8082` (direct) or via gateway at `/profiles`

Manages user profiles and settings.

### Get Profile

Retrieves a user profile by ID.

```http
GET /profiles/{user_id}
```

**Path Parameters**:
- `user_id` (integer): User ID

**Response** (200 OK):
```json
{
  "user_id": 123456789,
  "name": "John Doe",
  "age": 28,
  "gender": "male",
  "city": "Moscow",
  "bio": "Software engineer, love hiking and photography",
  "photos": [
    "photo1.jpg",
    "photo2.jpg"
  ]
}
```

**Error Responses**:
- `404 Not Found`: Profile not found
- `500 Internal Server Error`: Server error

### Create Profile

Creates a new user profile.

```http
POST /profiles
Content-Type: application/json
```

**Request Body**:
```json
{
  "user_id": 123456789,
  "name": "John Doe",
  "birth_date": "1995-05-15",
  "gender": "male",
  "orientation": "heterosexual",
  "city": "Moscow",
  "bio": "Software engineer, love hiking and photography"
}
```

**Response** (201 Created):
```json
{
  "user_id": 123456789,
  "name": "John Doe",
  "created": true
}
```

**Error Responses**:
- `400 Bad Request`: Invalid data or validation failed
- `500 Internal Server Error`: Server error

### Health Check

```http
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "service": "profile"
}
```

---

## Discovery Service

**Base URL**: `http://localhost:8083` (direct) or via gateway at `/discovery`

Handles matching algorithm and candidate discovery.

### Get Candidates

Retrieves candidate profiles for a user.

```http
GET /discovery/candidates?user_id={user_id}&limit={limit}
```

**Query Parameters**:
- `user_id` (integer, required): User ID
- `limit` (integer, optional): Number of candidates to return (default: 10)

**Response** (200 OK):
```json
{
  "candidates": [
    {
      "user_id": 987654321,
      "name": "Jane Smith",
      "age": 26,
      "city": "Moscow",
      "photos": ["photo1.jpg"],
      "compatibility_score": 0.85
    }
  ],
  "count": 1
}
```

**Error Responses**:
- `400 Bad Request`: Missing user_id
- `500 Internal Server Error`: Server error

### Like Profile

Records a like action.

```http
POST /discovery/like
Content-Type: application/json
```

**Request Body**:
```json
{
  "user_id": 123456789,
  "target_id": 987654321
}
```

**Response** (200 OK):
```json
{
  "success": true,
  "matched": false
}
```

If both users liked each other:
```json
{
  "success": true,
  "matched": true
}
```

**Error Responses**:
- `400 Bad Request`: Missing user_id or target_id
- `500 Internal Server Error`: Server error

### Get Matches

Retrieves all matches for a user.

```http
GET /discovery/matches?user_id={user_id}
```

**Query Parameters**:
- `user_id` (integer, required): User ID

**Response** (200 OK):
```json
{
  "matches": [
    {
      "user_id": 987654321,
      "name": "Jane Smith",
      "age": 26,
      "city": "Moscow",
      "matched_at": "2024-01-15T10:30:00Z"
    }
  ],
  "count": 1
}
```

**Error Responses**:
- `400 Bad Request`: Missing user_id
- `500 Internal Server Error`: Server error

### Health Check

```http
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "service": "discovery"
}
```

---

## Media Service

**Base URL**: `http://localhost:8084` (direct) or via gateway at `/media`

Handles photo/video upload and serving.

### Upload Media

Uploads a media file (photo/video).

```http
POST /media/upload
Content-Type: multipart/form-data
```

**Form Data**:
- `file`: The file to upload

**Response** (201 Created):
```json
{
  "file_id": "550e8400-e29b-41d4-a716-446655440000",
  "filename": "photo.jpg",
  "size": 245678,
  "url": "/media/550e8400-e29b-41d4-a716-446655440000"
}
```

**Error Responses**:
- `400 Bad Request`: No file provided
- `500 Internal Server Error`: Server error

### Get Media

Retrieves a media file.

```http
GET /media/{file_id}
```

**Path Parameters**:
- `file_id` (string): File ID from upload response

**Response**:
- Binary file data with appropriate Content-Type header

**Error Responses**:
- `404 Not Found`: File not found
- `500 Internal Server Error`: Server error

### Delete Media

Deletes a media file.

```http
DELETE /media/{file_id}
```

**Path Parameters**:
- `file_id` (string): File ID

**Response** (200 OK):
```json
{
  "success": true
}
```

**Error Responses**:
- `404 Not Found`: File not found
- `500 Internal Server Error`: Server error

### Health Check

```http
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "service": "media"
}
```

---

## Chat Service

**Base URL**: `http://localhost:8085` (direct) or via gateway at `/chat`

Handles real-time messaging via WebSocket.

### WebSocket Connection

Establishes a WebSocket connection for real-time messaging.

```
WS /chat/connect
```

**Connection**:
```javascript
const ws = new WebSocket('ws://localhost:8085/chat/connect');

ws.onopen = () => {
  console.log('Connected to chat');
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Message received:', data);
};

// Send message
ws.send(JSON.stringify({
  type: 'message',
  conversation_id: 1,
  user_id: 123456789,
  text: 'Hello!'
}));
```

**Message Format** (received):
```json
{
  "type": "message",
  "data": {
    "message_id": 1,
    "conversation_id": 1,
    "user_id": 987654321,
    "text": "Hi there!",
    "sent_at": "2024-01-15T10:30:00Z"
  }
}
```

### Get Conversations

Retrieves all conversations for a user.

```http
GET /chat/conversations?user_id={user_id}
```

**Query Parameters**:
- `user_id` (integer, required): User ID

**Response** (200 OK):
```json
{
  "conversations": [
    {
      "conversation_id": 1,
      "participant_id": 987654321,
      "participant_name": "Jane Smith",
      "last_message": "Hello!",
      "last_message_at": "2024-01-15T10:30:00Z",
      "unread_count": 2
    }
  ],
  "count": 1
}
```

**Error Responses**:
- `400 Bad Request`: Missing user_id
- `500 Internal Server Error`: Server error

### Get Messages

Retrieves messages for a conversation.

```http
GET /chat/messages/{conversation_id}
```

**Path Parameters**:
- `conversation_id` (integer): Conversation ID

**Response** (200 OK):
```json
{
  "messages": [
    {
      "message_id": 1,
      "user_id": 123456789,
      "text": "Hello!",
      "sent_at": "2024-01-15T10:30:00Z",
      "read": true
    },
    {
      "message_id": 2,
      "user_id": 987654321,
      "text": "Hi there!",
      "sent_at": "2024-01-15T10:31:00Z",
      "read": false
    }
  ],
  "count": 2
}
```

**Error Responses**:
- `500 Internal Server Error`: Server error

### Send Message

Sends a message in a conversation.

```http
POST /chat/messages
Content-Type: application/json
```

**Request Body**:
```json
{
  "conversation_id": 1,
  "user_id": 123456789,
  "text": "Hello!"
}
```

**Response** (201 Created):
```json
{
  "message_id": 1,
  "sent_at": "2024-01-15T10:30:00Z"
}
```

**Error Responses**:
- `400 Bad Request`: Missing required fields
- `500 Internal Server Error`: Server error

### Health Check

```http
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "service": "chat"
}
```

---

## Authentication Flow

For protected endpoints, use JWT authentication:

1. **Get JWT token**:
   ```http
   POST /auth/validate
   {
     "init_data": "telegram_init_data",
     "bot_token": "bot_token"
   }
   ```

2. **Use token in requests**:
   ```http
   GET /profiles/123456789
   Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

3. **Refresh token when expired**:
   ```http
   POST /auth/refresh
   Authorization: Bearer <old_token>
   ```

---

## Error Responses

All services follow a standard error response format:

```json
{
  "error": "Error message describing what went wrong"
}
```

### Common HTTP Status Codes

- `200 OK`: Request succeeded
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `401 Unauthorized`: Authentication required or failed
- `404 Not Found`: Resource not found
- `500 Internal Server Error`: Server-side error
- `503 Service Unavailable`: Service temporarily unavailable

---

## Rate Limiting

Rate limiting is applied at the API Gateway level:

- **Default**: 100 requests per minute per IP
- **Authenticated**: 1000 requests per minute per user

When rate limit is exceeded:

```json
{
  "error": "Rate limit exceeded. Please try again later.",
  "retry_after": 60
}
```

**Response Code**: `429 Too Many Requests`

---

## Testing with cURL

### Auth Service

```bash
# Validate initData
curl -X POST http://localhost:8081/auth/validate \
  -H "Content-Type: application/json" \
  -d '{"init_data":"telegram_data","bot_token":"token"}'

# Verify token
curl http://localhost:8081/auth/verify \
  -H "Authorization: Bearer <token>"
```

### Profile Service

```bash
# Get profile
curl http://localhost:8082/profiles/123456789

# Create profile
curl -X POST http://localhost:8082/profiles \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123456789,
    "name": "John Doe",
    "birth_date": "1995-05-15",
    "gender": "male",
    "orientation": "heterosexual",
    "city": "Moscow"
  }'
```

### Discovery Service

```bash
# Get candidates
curl "http://localhost:8083/discovery/candidates?user_id=123456789&limit=5"

# Like profile
curl -X POST http://localhost:8083/discovery/like \
  -H "Content-Type: application/json" \
  -d '{"user_id": 123456789, "target_id": 987654321}'
```

### Media Service

```bash
# Upload photo
curl -X POST http://localhost:8084/media/upload \
  -F "file=@photo.jpg"

# Get photo
curl http://localhost:8084/media/550e8400-e29b-41d4-a716-446655440000 \
  -o downloaded_photo.jpg
```

### Chat Service

```bash
# Get conversations
curl "http://localhost:8085/chat/conversations?user_id=123456789"

# Send message
curl -X POST http://localhost:8085/chat/messages \
  -H "Content-Type: application/json" \
  -d '{
    "conversation_id": 1,
    "user_id": 123456789,
    "text": "Hello!"
  }'
```

---

## WebSocket Client Examples

### JavaScript (Browser)

```javascript
// Connect to chat
const ws = new WebSocket('ws://localhost:8085/chat/connect');

ws.onopen = () => {
  console.log('Connected');
  
  // Send message
  ws.send(JSON.stringify({
    type: 'message',
    conversation_id: 1,
    user_id: 123456789,
    text: 'Hello!'
  }));
};

ws.onmessage = (event) => {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};

ws.onclose = () => {
  console.log('Disconnected');
};
```

### Python

```python
import asyncio
import websockets
import json

async def chat():
    uri = "ws://localhost:8085/chat/connect"
    async with websockets.connect(uri) as websocket:
        # Send message
        await websocket.send(json.dumps({
            "type": "message",
            "conversation_id": 1,
            "user_id": 123456789,
            "text": "Hello!"
        }))
        
        # Receive message
        response = await websocket.recv()
        print(json.loads(response))

asyncio.run(chat())
```

---

## Monitoring Endpoints

All services expose a `/health` endpoint for monitoring:

```bash
# Check all services
for port in 8080 8081 8082 8083 8084 8085; do
  echo "Port $port:"
  curl -s http://localhost:$port/health | jq
done
```

---

## Additional Resources

- [Microservices Deployment Guide](./MICROSERVICES_DEPLOYMENT.md)
- [Architecture Migration Guide](./ARCHITECTURE_MIGRATION_GUIDE.md)
- [Getting Started](./GETTING_STARTED.md)
