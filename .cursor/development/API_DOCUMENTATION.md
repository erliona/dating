# 📚 API Documentation

## 📋 Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [API Gateway](#api-gateway)
- [Microservices APIs](#microservices-apis)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Examples](#examples)

---

## 🎯 Overview

The Dating application provides a comprehensive REST API through an API Gateway that routes requests to appropriate microservices. All APIs follow RESTful conventions and return JSON responses.

### Base URLs

- **Production**: `https://dating.serge.cc`
- **Local Development**: `http://localhost:8080`

### Content Type

All API requests and responses use `application/json` content type.

---

## 🔐 Authentication

### Telegram WebApp Authentication

The application uses Telegram WebApp's built-in authentication system.

#### Authentication Flow

1. **Get JWT Token**
   ```http
   POST /auth/validate
   Content-Type: application/json
   
   {
     "init_data": "telegram_webapp_init_data_string",
     "bot_token": "bot_token"
   }
   ```

   **Response**:
   ```json
   {
     "token": "jwt_token_here",
     "user_id": 123456789,
     "username": "user_username"
   }
   ```

2. **Use JWT Token**
   Include the JWT token in the `Authorization` header:
   ```http
   Authorization: Bearer <jwt_token>
   ```

#### Token Verification

```http
GET /auth/verify
Authorization: Bearer <jwt_token>
```

**Response**:
```json
{
  "valid": true,
  "user_id": 123456789
}
```

#### Token Refresh

```http
POST /auth/refresh
Authorization: Bearer <old_jwt_token>
```

**Response**:
```json
{
  "token": "new_jwt_token",
  "user_id": 123456789
}
```

---

## 🌐 API Gateway

The API Gateway (`api-gateway:8080`) routes requests to appropriate microservices.

### Routing Rules

| Path Pattern | Target Service | Description |
|--------------|----------------|-------------|
| `/auth/*` | Auth Service | Authentication endpoints |
| `/profiles/*` | Profile Service | Profile management |
| `/discovery/*` | Discovery Service | Matching and discovery |
| `/media/*` | Media Service | File upload/download |
| `/chat/*` | Chat Service | Real-time messaging |
| `/admin/*` | Admin Service | Administrative functions |
| `/api/profiles/*` | WebApp | Next.js API routes |

### CORS Configuration

The API Gateway handles CORS for all services:
- **Allowed Origins**: Configured per environment
- **Allowed Methods**: GET, POST, PUT, DELETE, OPTIONS
- **Allowed Headers**: Content-Type, Authorization, X-Requested-With

---

## 🔧 Microservices APIs

### Auth Service (`auth-service:8081`)

#### Validate Telegram InitData
```http
POST /auth/validate
Content-Type: application/json

{
  "init_data": "string",
  "bot_token": "string"
}
```

**Response**:
```json
{
  "token": "string",
  "user_id": 123456789,
  "username": "string"
}
```

**Errors**:
- `400` - Missing init_data or bot_token
- `401` - Invalid init_data
- `500` - Internal server error

#### Verify Token
```http
GET /auth/verify
Authorization: Bearer <token>
```

**Response**:
```json
{
  "valid": true,
  "user_id": 123456789
}
```

#### Refresh Token
```http
POST /auth/refresh
Authorization: Bearer <token>
```

**Response**:
```json
{
  "token": "string",
  "user_id": 123456789
}
```

### Profile Service (`profile-service:8082`)

#### Get Profile
```http
GET /profiles/{user_id}
Authorization: Bearer <token>
```

**Response**:
```json
{
  "user_id": 123456789,
  "name": "John Doe",
  "birth_date": "1990-01-01",
  "gender": "male",
  "city": "Moscow",
  "bio": "Looking for someone special",
  "interests": ["music", "travel"],
  "goal": "relationship",
  "orientation": "straight",
  "height_cm": 180,
  "education": "university",
  "work": "Software Engineer",
  "is_verified": true,
  "created_at": "2024-01-01T00:00:00Z"
}
```

#### Create Profile
```http
POST /profiles
Authorization: Bearer <token>
Content-Type: application/json

{
  "name": "John Doe",
  "birth_date": "1990-01-01",
  "gender": "male",
  "city": "Moscow",
  "bio": "Looking for someone special",
  "interests": ["music", "travel"],
  "goal": "relationship",
  "orientation": "straight",
  "height_cm": 180,
  "education": "university",
  "work": "Software Engineer"
}
```

**Response**:
```json
{
  "user_id": 123456789,
  "name": "John Doe",
  "created_at": "2024-01-01T00:00:00Z"
}
```

**Errors**:
- `400` - Invalid profile data
- `409` - Profile already exists
- `500` - Internal server error

### Discovery Service (`discovery-service:8083`)

#### Get Candidates
```http
GET /discovery/candidates?user_id=123456789&limit=10&cursor=0
Authorization: Bearer <token>
```

**Query Parameters**:
- `user_id` (required) - User ID
- `limit` (optional) - Number of candidates (default: 10)
- `cursor` (optional) - Pagination cursor
- `age_min` (optional) - Minimum age filter
- `age_max` (optional) - Maximum age filter
- `max_distance_km` (optional) - Maximum distance in km
- `goal` (optional) - Relationship goal filter
- `height_min` (optional) - Minimum height filter
- `height_max` (optional) - Maximum height filter
- `has_children` (optional) - Children filter
- `smoking` (optional) - Smoking preference filter
- `drinking` (optional) - Drinking preference filter
- `education` (optional) - Education level filter
- `verified_only` (optional) - Only verified profiles

**Response**:
```json
{
  "candidates": [
    {
      "id": 1,
      "user_id": 987654321,
      "name": "Jane Doe",
      "age": 25,
      "gender": "female",
      "orientation": "straight",
      "city": "Moscow",
      "bio": "Love traveling and music",
      "goal": "relationship",
      "education": "university",
      "work": "Designer",
      "height_cm": 165,
      "photos": ["https://example.com/photo1.jpg"],
      "is_verified": true,
      "created_at": "2024-01-01T00:00:00Z"
    }
  ],
  "count": 1,
  "next_cursor": 10
}
```

#### Like Profile
```http
POST /discovery/like
Authorization: Bearer <token>
Content-Type: application/json

{
  "user_id": 123456789,
  "target_id": 987654321,
  "interaction_type": "like"
}
```

**Interaction Types**:
- `like` - Like a profile
- `superlike` - Super like a profile
- `pass` - Pass on a profile

**Response**:
```json
{
  "success": true,
  "matched": false,
  "interaction_id": 1,
  "interaction_type": "like"
}
```

#### Get Matches
```http
GET /discovery/matches?user_id=123456789&limit=20&cursor=0
Authorization: Bearer <token>
```

**Response**:
```json
{
  "matches": [
    {
      "match_id": 1,
      "user_id": 987654321,
      "name": "Jane Doe",
      "age": 25,
      "gender": "female",
      "city": "Moscow",
      "bio": "Love traveling and music",
      "photos": ["https://example.com/photo1.jpg"],
      "is_verified": true,
      "matched_at": "2024-01-01T00:00:00Z"
    }
  ],
  "count": 1,
  "next_cursor": 20
}
```

### Media Service (`media-service:8084`)

#### Upload Media
```http
POST /media/upload
Content-Type: multipart/form-data

file: <binary_file_data>
```

**Response**:
```json
{
  "file_id": "uuid-string",
  "filename": "original_filename.jpg",
  "size": 1024000,
  "url": "/media/uuid-string"
}
```

#### Get Media
```http
GET /media/{file_id}
```

**Response**: Binary file data

#### Delete Media
```http
DELETE /media/{file_id}
Authorization: Bearer <token>
```

**Response**:
```json
{
  "success": true
}
```

### Chat Service (`chat-service:8085`)

#### WebSocket Connection
```javascript
const ws = new WebSocket('ws://localhost:8085/chat/connect');

ws.onopen = function() {
  console.log('Connected to chat');
};

ws.onmessage = function(event) {
  const message = JSON.parse(event.data);
  console.log('Received:', message);
};

ws.send(JSON.stringify({
  type: 'message',
  data: 'Hello!'
}));
```

#### Get Conversations
```http
GET /chat/conversations?user_id=123456789
Authorization: Bearer <token>
```

**Response**:
```json
{
  "conversations": [
    {
      "id": 1,
      "user_id": 123456789,
      "match_id": 1,
      "last_message": "Hello!",
      "last_message_at": "2024-01-01T00:00:00Z",
      "unread_count": 2
    }
  ],
  "count": 1
}
```

#### Get Messages
```http
GET /chat/messages/{conversation_id}
Authorization: Bearer <token>
```

**Response**:
```json
{
  "messages": [
    {
      "id": 1,
      "conversation_id": 1,
      "user_id": 123456789,
      "text": "Hello!",
      "sent_at": "2024-01-01T00:00:00Z"
    }
  ],
  "count": 1
}
```

#### Send Message
```http
POST /chat/messages
Authorization: Bearer <token>
Content-Type: application/json

{
  "conversation_id": 1,
  "user_id": 123456789,
  "text": "Hello!"
}
```

**Response**:
```json
{
  "message_id": 1,
  "sent_at": "2024-01-01T00:00:00Z"
}
```

### Admin Service (`admin-service:8087`)

#### Admin Login
```http
POST /admin/login
Content-Type: application/json

{
  "username": "admin",
  "password": "admin123"
}
```

**Response**:
```json
{
  "token": "admin_session_token",
  "admin_id": 1,
  "username": "admin"
}
```

#### Get System Statistics
```http
GET /admin/stats
Authorization: Bearer <admin_token>
```

**Response**:
```json
{
  "total_users": 1000,
  "active_users_30d": 500,
  "total_profiles": 800,
  "total_photos": 2000,
  "total_matches": 300,
  "blocked_users": 10
}
```

#### List Users
```http
GET /admin/users?limit=20&offset=0&search=john
Authorization: Bearer <admin_token>
```

**Response**:
```json
{
  "users": [
    {
      "id": 1,
      "telegram_id": 123456789,
      "username": "john_doe",
      "is_active": true,
      "is_blocked": false,
      "created_at": "2024-01-01T00:00:00Z",
      "last_seen": "2024-01-01T00:00:00Z"
    }
  ],
  "count": 1,
  "total": 1000
}
```

#### List Photos for Moderation
```http
GET /admin/photos?status=pending&limit=20&offset=0
Authorization: Bearer <admin_token>
```

**Response**:
```json
{
  "photos": [
    {
      "id": 1,
      "user_id": 123456789,
      "url": "https://example.com/photo1.jpg",
      "status": "pending",
      "nsfw_score": 0.1,
      "uploaded_at": "2024-01-01T00:00:00Z"
    }
  ],
  "count": 1,
  "total": 100
}
```

#### Update Photo Status
```http
PUT /admin/photos/{photo_id}
Authorization: Bearer <admin_token>
Content-Type: application/json

{
  "status": "approved"
}
```

**Photo Statuses**:
- `pending` - Awaiting moderation
- `approved` - Approved for use
- `rejected` - Rejected (inappropriate content)

### Data Service (`data-service:8088`)

The Data Service provides internal APIs for other microservices. These endpoints are not directly accessible from external clients.

#### Internal Endpoints

- `GET /data/profiles/{user_id}` - Get user profile
- `POST /data/profiles` - Create user profile
- `PUT /data/profiles/{user_id}` - Update user profile
- `GET /data/users` - List users
- `GET /data/stats` - System statistics
- `GET /data/photos` - List photos
- `PUT /data/photos/{photo_id}` - Update photo
- `DELETE /data/photos/{photo_id}` - Delete photo
- `GET /data/candidates` - Find candidates
- `POST /data/interactions` - Create interaction
- `GET /data/matches` - Get matches

---

## ❌ Error Handling

### Error Response Format

All API errors follow a consistent format:

```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": {
    "field": "Additional error details"
  }
}
```

### HTTP Status Codes

| Status Code | Description |
|-------------|-------------|
| `200` | Success |
| `201` | Created |
| `400` | Bad Request - Invalid input data |
| `401` | Unauthorized - Invalid or missing token |
| `403` | Forbidden - Insufficient permissions |
| `404` | Not Found - Resource not found |
| `409` | Conflict - Resource already exists |
| `422` | Unprocessable Entity - Validation error |
| `429` | Too Many Requests - Rate limit exceeded |
| `500` | Internal Server Error |
| `503` | Service Unavailable |

### Common Error Codes

| Error Code | Description |
|------------|-------------|
| `INVALID_TOKEN` | JWT token is invalid or expired |
| `MISSING_AUTH` | Authorization header is missing |
| `VALIDATION_ERROR` | Input data validation failed |
| `PROFILE_NOT_FOUND` | User profile not found |
| `PROFILE_EXISTS` | Profile already exists for user |
| `PHOTO_NOT_FOUND` | Photo not found |
| `INVALID_FILE` | Invalid file format or size |
| `RATE_LIMITED` | Rate limit exceeded |

---

## 🚦 Rate Limiting

### Rate Limits

| Endpoint | Limit | Window |
|----------|-------|--------|
| `/auth/validate` | 10 requests | 1 minute |
| `/auth/refresh` | 5 requests | 1 minute |
| `/profiles/*` | 100 requests | 1 minute |
| `/discovery/*` | 200 requests | 1 minute |
| `/media/upload` | 10 requests | 1 minute |
| `/chat/*` | 500 requests | 1 minute |
| `/admin/*` | 50 requests | 1 minute |

### Rate Limit Headers

```http
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1640995200
```

### Rate Limit Exceeded Response

```json
{
  "error": "Rate limit exceeded",
  "code": "RATE_LIMITED",
  "retry_after": 60
}
```

---

## 📝 Examples

### Complete Authentication Flow

```javascript
// 1. Get JWT token from Telegram WebApp
const response = await fetch('/auth/validate', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    init_data: window.Telegram.WebApp.initData,
    bot_token: 'your_bot_token'
  })
});

const { token } = await response.json();

// 2. Use token for authenticated requests
const profileResponse = await fetch('/profiles/123456789', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

const profile = await profileResponse.json();
```

### Profile Creation

```javascript
const profileData = {
  name: "John Doe",
  birth_date: "1990-01-01",
  gender: "male",
  city: "Moscow",
  bio: "Looking for someone special",
  interests: ["music", "travel"],
  goal: "relationship",
  orientation: "straight",
  height_cm: 180,
  education: "university",
  work: "Software Engineer"
};

const response = await fetch('/profiles', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify(profileData)
});

const result = await response.json();
```

### Discovery and Matching

```javascript
// Get candidates
const candidatesResponse = await fetch('/discovery/candidates?user_id=123456789&limit=10', {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

const { candidates } = await candidatesResponse.json();

// Like a profile
const likeResponse = await fetch('/discovery/like', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`
  },
  body: JSON.stringify({
    user_id: 123456789,
    target_id: 987654321,
    interaction_type: "like"
  })
});

const { matched } = await likeResponse.json();
```

### File Upload

```javascript
const formData = new FormData();
formData.append('file', fileInput.files[0]);

const response = await fetch('/media/upload', {
  method: 'POST',
  body: formData
});

const { file_id, url } = await response.json();
```

---

*Last updated: January 2025*
