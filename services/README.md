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

1. **Phase 1** ✅ Complete: Core logic extracted to independent modules
2. **Phase 2** ✅ Complete: Services deployed as separate containers sharing database
3. **Phase 3** 📋 TODO: Database per service with event-driven synchronization
4. **Phase 4** ✅ Complete: Full microservices with API gateway and service mesh

## Getting Started

### Local Development

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run a service:**
   ```bash
   # Auth Service
   python -m services.auth.main
   
   # Profile Service
   python -m services.profile.main
   
   # Discovery Service
   python -m services.discovery.main
   
   # Media Service
   python -m services.media.main
   
   # Chat Service
   python -m services.chat.main
   ```

3. **Run API Gateway:**
   ```bash
   python -m gateway.main
   ```

### Docker Deployment

Deploy all services with Docker Compose:

```bash
# Build and start all services
docker compose -f docker-compose.microservices.yml up -d

# Check service status
docker compose -f docker-compose.microservices.yml ps

# View logs
docker compose -f docker-compose.microservices.yml logs -f

# Stop all services
docker compose -f docker-compose.microservices.yml down
```

### Quick Test

Test services are running:

```bash
# Test all health endpoints
for port in 8080 8081 8082 8083 8084 8085; do
  curl http://localhost:$port/health
done
```

## Documentation

- [Microservices API Reference](../docs/MICROSERVICES_API.md) - Complete API documentation
- [Deployment Guide](../docs/MICROSERVICES_DEPLOYMENT.md) - Deployment instructions
- [Architecture Guide](../docs/ARCHITECTURE_MIGRATION_GUIDE.md) - Architecture overview

## Development

### Adding a New Service

1. Create service directory: `services/new-service/`
2. Add `__init__.py` and `main.py`
3. Implement health check endpoint: `/health`
4. Create Dockerfile: `services/new-service/Dockerfile`
5. Add to `docker-compose.microservices.yml`
6. Update API Gateway routing in `gateway/main.py`
7. Document API endpoints in `docs/MICROSERVICES_API.md`

### Service Template

```python
# services/new-service/main.py
import logging
from aiohttp import web

logger = logging.getLogger(__name__)

async def health_check(request: web.Request) -> web.Response:
    return web.json_response({'status': 'healthy', 'service': 'new-service'})

async def example_endpoint(request: web.Request) -> web.Response:
    return web.json_response({'message': 'Hello from new service'})

def create_app(config: dict) -> web.Application:
    app = web.Application()
    app['config'] = config
    
    app.router.add_get('/health', health_check)
    app.router.add_get('/example', example_endpoint)
    
    return app

if __name__ == '__main__':
    import os
    
    logging.basicConfig(level=logging.INFO)
    
    config = {
        'host': os.getenv('NEW_SERVICE_HOST', '0.0.0.0'),
        'port': int(os.getenv('NEW_SERVICE_PORT', 8086))
    }
    
    app = create_app(config)
    web.run_app(app, host=config['host'], port=config['port'])
```

## Testing

Run tests for services:

```bash
# Run all tests
pytest tests/services/

# Run specific service tests
pytest tests/services/test_auth.py
pytest tests/services/test_profile.py

# With coverage
pytest tests/services/ --cov=services --cov-report=html
```

## Troubleshooting

### Service Won't Start

1. Check logs: `docker compose -f docker-compose.microservices.yml logs service-name`
2. Verify environment variables are set
3. Check port is not already in use: `lsof -i :PORT`
4. Ensure database is running and accessible

### Service Communication Issues

1. Check network: `docker network inspect dating_default`
2. Test connectivity: `docker compose exec api-gateway ping auth-service`
3. Verify service URLs in environment variables

### Database Connection Issues

1. Check database is running: `docker compose ps db`
2. Test connection: `docker compose exec db psql -U dating -d dating -c "SELECT 1"`
3. Verify DATABASE_URL format: `postgresql+asyncpg://user:pass@host:port/db`

## Contributing

When contributing to services:

1. Maintain backward compatibility
2. Add health check endpoints
3. Include comprehensive error handling
4. Document all API endpoints
5. Add unit tests
6. Update documentation
