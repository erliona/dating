# Thin Client Architecture - Bot Refactoring

## Overview

The Telegram bot has been refactored from a monolithic design with direct database access to a **thin client architecture** that communicates exclusively through the API Gateway and microservices.

## Architecture Changes

### Before (Monolithic)
```
┌─────────────────┐
│  Telegram Bot   │
└────────┬────────┘
         │ Direct DB Access
         │
    ┌────▼─────────┐
    │ PostgreSQL   │
    └──────────────┘
```

Problems with this approach:
- ❌ Bot has direct database access (coupling)
- ❌ Business logic duplicated in bot
- ❌ Difficult to scale independently
- ❌ No centralized data validation
- ❌ Inconsistent with microservices architecture

### After (Thin Client)
```
┌─────────────────┐
│  Telegram Bot   │ ← Thin Client (no DB access)
└────────┬────────┘
         │ HTTP/REST API
┌────────▼────────┐
│  API Gateway    │ ← Single entry point
└────────┬────────┘
         │
    ┌────┴──────────────────┐
    │    Microservices      │
    ├───────────────────────┤
    │ • Profile Service     │ ← Business logic
    │ • Auth Service        │
    │ • Discovery Service   │
    │ • Media Service       │
    └───────┬───────────────┘
            │
    ┌───────▼────────┐
    │ PostgreSQL     │
    └────────────────┘
```

Benefits:
- ✅ Single point of entry through API Gateway
- ✅ Microservices handle all business logic
- ✅ Bot focuses only on Telegram integration
- ✅ Simplified scaling and maintenance
- ✅ Consistent request processing
- ✅ Centralized authentication and authorization

## Implementation Details

### 1. API Gateway Client

Created `bot/api_client.py` - HTTP client for communicating with microservices:

```python
from bot.api_client import APIGatewayClient

# Initialize client
client = APIGatewayClient(gateway_url="http://api-gateway:8080")

# Create profile
result = await client.create_profile(profile_data)

# Get profile
profile = await client.get_profile(user_id)

# Find candidates
candidates = await client.find_candidates(user_id, filters)
```

### 2. Configuration Changes

Updated `bot/config.py`:

**Before:**
```python
@dataclass
class BotConfig:
    token: str
    database_url: str  # Direct DB access
```

**After:**
```python
@dataclass
class BotConfig:
    token: str
    api_gateway_url: str  # API Gateway URL (required)
    database_url: str | None = None  # Optional for backward compatibility
```

**Environment Variables:**
- `API_GATEWAY_URL` - **Required** URL of API Gateway (e.g., `http://api-gateway:8080`)
- `DATABASE_URL` - Optional, only used by `bot/api.py` for backward compatibility with WebApp

### 3. Bot Handler Changes

Updated `bot/main.py` to use API Gateway client instead of direct database access:

**Before:**
```python
async with session_maker() as session:
    repository = ProfileRepository(session)
    user = await repository.create_or_update_user(...)
    profile = await repository.create_profile(user.id, profile_data)
    await session.commit()
```

**After:**
```python
# Profile data includes telegram_id
profile_data["telegram_id"] = message.from_user.id
result = await api_client.create_profile(profile_data)
```

### 4. Microservice Updates

Updated `services/profile/main.py` to handle comprehensive profile creation from bot:

```python
async def create_profile(request: web.Request) -> web.Response:
    """Create user profile.
    
    Accepts:
    - telegram_id: Create/update user from Telegram data
    - All profile fields
    - Geolocation data
    """
    data = await request.json()
    
    # Handle Telegram user creation
    if data.get("telegram_id"):
        user = await repository.create_or_update_user(
            tg_id=data["telegram_id"],
            username=data.get("username"),
            ...
        )
    
    # Create profile with all fields
    profile = await repository.create_profile(user.id, profile_data)
    ...
```

## API Client Methods

The `APIGatewayClient` provides methods for all bot operations:

### Profile Management
- `create_profile(profile_data)` - Create new profile
- `get_profile(user_id)` - Get profile by ID
- `update_profile(user_id, profile_data)` - Update profile
- `delete_profile(user_id)` - Delete profile

### Media Operations
- `upload_photo(user_id, photo_data, filename)` - Upload photo
- `get_photo(file_id)` - Get photo metadata
- `delete_photo(file_id)` - Delete photo

### Discovery
- `find_candidates(user_id, filters)` - Find candidate profiles
- `create_interaction(user_id, target_id, type)` - Create like/pass
- `get_matches(user_id, limit, cursor)` - Get user's matches

### Authentication
- `authenticate(telegram_id, username)` - Get JWT token
- `validate_token(token)` - Validate JWT token

## Testing

All tests have been updated to use the thin client architecture:

```python
# Mock API client instead of database repository
api_client = MagicMock()
api_client.create_profile = AsyncMock(return_value={...})

await handle_create_profile(message, data, api_client, logger)

api_client.create_profile.assert_called_once()
```

Run tests:
```bash
pytest tests/test_main.py -v
```

## Migration Guide

### For Developers

1. **Update environment variables:**
   ```bash
   # Add to .env
   API_GATEWAY_URL=http://api-gateway:8080
   ```

2. **Update code using ProfileRepository:**
   ```python
   # Old way (direct DB)
   repository = ProfileRepository(session)
   profile = await repository.create_profile(...)
   
   # New way (API Gateway)
   api_client = APIGatewayClient(gateway_url)
   profile = await api_client.create_profile(...)
   ```

3. **Update tests:**
   - Replace `ProfileRepository` mocks with `APIGatewayClient` mocks
   - Update assertions to check API calls instead of DB operations

### For Deployment

1. **Docker Compose:**
   - API_GATEWAY_URL is already configured in `docker-compose.yml`
   - Bot automatically uses API Gateway URL from environment

2. **Kubernetes/Cloud:**
   - Set `API_GATEWAY_URL` environment variable
   - Point to your API Gateway service
   - Example: `http://api-gateway-service:8080`

## Backward Compatibility

The `bot/api.py` file (HTTP API for WebApp) still uses direct database access for backward compatibility. This will be migrated to use API Gateway client in a future update.

Current setup:
- ✅ Bot handlers (`bot/main.py`) - Use API Gateway (thin client)
- ⚠️ Bot API server (`bot/api.py`) - Uses direct DB (for WebApp)

Future work:
- Migrate `bot/api.py` to also use API Gateway client
- Complete thin client architecture for all bot components

## Benefits Realized

1. **Separation of Concerns:** Bot focuses on Telegram integration only
2. **Centralized Logic:** All business logic in microservices
3. **Easy Scaling:** Bot and services scale independently
4. **Consistent Data:** Single source of truth through microservices
5. **Simplified Testing:** Mock HTTP calls instead of database
6. **Future-Proof:** Easy to add new clients (mobile apps, web, etc.)

## Performance Considerations

- HTTP overhead is minimal (~1-2ms) compared to direct DB access
- API Gateway can cache frequently accessed data
- Connection pooling in HTTP client reduces latency
- Microservices can be scaled independently based on load

## Security Improvements

- No direct database credentials in bot configuration
- All requests go through API Gateway (single point of control)
- JWT tokens for authentication
- API Gateway can enforce rate limiting and access control

## References

- [API Gateway Documentation](../gateway/main.py)
- [API Client Implementation](../bot/api_client.py)
- [Profile Service](../services/profile/main.py)
- [Configuration Guide](../bot/config.py)
