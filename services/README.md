# Microservices Architecture

This directory contains microservice implementations for the dating application.

## Services

### 1. Auth Service (`auth/`)
Handles authentication, JWT token management, and session management.

**Responsibilities:**
- Validate Telegram WebApp initData
- Generate and validate JWT tokens
- Session management
- Rate limiting

**Endpoints:**
- `POST /auth/validate` - Validate Telegram initData
- `POST /auth/token` - Generate JWT token
- `POST /auth/refresh` - Refresh JWT token
- `GET /auth/verify` - Verify JWT token

### 2. Profile Service (`profile/`)
Manages user profiles and settings.

**Responsibilities:**
- Create/update/delete user profiles
- Manage user photos
- User settings management
- Profile visibility

**Endpoints:**
- `GET /profiles/{user_id}` - Get user profile
- `POST /profiles` - Create profile
- `PUT /profiles/{user_id}` - Update profile
- `DELETE /profiles/{user_id}` - Delete profile
- `GET /profiles/{user_id}/photos` - Get photos
- `POST /profiles/{user_id}/photos` - Upload photo

### 3. Discovery Service (`discovery/`)
Handles matching algorithm and candidate discovery.

**Responsibilities:**
- Generate candidate recommendations
- Apply filters based on user preferences
- Calculate compatibility scores
- Track user interactions (likes, passes)

**Endpoints:**
- `GET /discovery/candidates` - Get candidate profiles
- `POST /discovery/like` - Like a profile
- `POST /discovery/pass` - Pass on a profile
- `POST /discovery/superlike` - Send super like
- `GET /discovery/matches` - Get matches

### 4. Chat Service (`chat/`)
Manages real-time messaging between matched users.

**Responsibilities:**
- WebSocket connections
- Message storage and retrieval
- Read receipts
- Typing indicators
- Presence status

**Endpoints:**
- `WS /chat/connect` - WebSocket connection
- `GET /chat/conversations` - Get user conversations
- `GET /chat/messages/{conversation_id}` - Get messages
- `POST /chat/messages` - Send message

### 5. Media Service (`media/`)
Handles photo/video upload, validation, and optimization.

**Responsibilities:**
- File upload and validation
- NSFW detection
- Image optimization and resizing
- CDN integration
- File storage management

**Endpoints:**
- `POST /media/upload` - Upload file
- `GET /media/{file_id}` - Get file
- `DELETE /media/{file_id}` - Delete file
- `GET /media/user/{user_id}` - Get user files

## Communication

Services communicate via:
- HTTP REST APIs for synchronous operations
- Message queue (RabbitMQ/Redis) for asynchronous events
- Shared PostgreSQL database (in transition phase)

## Deployment

Each service can be deployed independently using Docker containers.
See `docker-compose.microservices.yml` for orchestration.

## Migration Strategy

The application is transitioning from monolithic to microservices:

1. **Phase 1** (Current): Core logic extracted to independent modules
2. **Phase 2**: Services deployed as separate containers sharing database
3. **Phase 3**: Database per service with event-driven synchronization
4. **Phase 4**: Full microservices with API gateway and service mesh
