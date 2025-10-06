# Bot Minimalist Architecture Refactoring

## Overview

This refactoring simplifies the Telegram bot to a minimalist architecture where the bot only handles infrastructure concerns (commands, notifications), while all user interactions happen in the WebApp which communicates directly with the API Gateway.

## Changes Summary

### Bot Simplification

**Before:** 509 lines with complex handlers for WebApp data, location updates, profile creation/updates  
**After:** 409 lines focused on core bot functionality

### Removed Handlers

The following handlers were removed from `bot/main.py`:
- `handle_webapp_data()` - WebApp data processing moved to WebApp itself
- `handle_location()` - Location updates moved to WebApp
- `handle_create_profile()` - Profile creation moved to WebApp
- `handle_update_profile()` - Profile updates moved to WebApp

### New Bot Role (Minimalist)

The bot now focuses on three core responsibilities:

1. **Welcome Message** (`/start` command)
   - Shows WebApp button to open the mini app
   - Simple entry point for users

2. **Notification Management** (`/notifications` command)
   - Allows users to manage notification preferences
   - Provides information about available notifications

3. **Push Notifications**
   - `send_match_notification()` - Notify about new matches
   - `send_message_notification()` - Notify about new messages
   - `send_like_notification()` - Notify about received likes

### WebApp Takes Over All Interactions

The WebApp now handles ALL user interactions through direct API Gateway calls:
- Profile creation and editing
- Photo uploads
- Candidate browsing (swipe)
- Likes/dislikes
- Match list viewing
- Chat with matches
- Search filter settings
- Geolocation

## New Notification Service

### Service Architecture

Created a new microservice: `services/notification/`

**Endpoints:**
- `POST /api/notifications/send_match` - Queue match notification
- `POST /api/notifications/send_message` - Queue message notification
- `POST /api/notifications/send_like` - Queue like notification
- `GET /health` - Health check

**Port:** 8087 (configurable via `NOTIFICATION_SERVICE_PORT`)

### API Gateway Updates

Updated `gateway/main.py` to route notification requests:
- Added `route_api_notifications()` handler
- Added `/api/notifications/*` route
- Added notification service to health check response
- Default URL: `http://notification-service:8087`

### Docker Compose Updates

Added notification service to `docker-compose.yml`:
```yaml
notification-service:
  build:
    context: .
    dockerfile: services/notification/Dockerfile
  depends_on:
    - telegram-bot
  environment:
    BOT_URL: http://telegram-bot:8080
    PORT: 8087
  ports:
    - "8087:8087"
```

## Testing Updates

### Test Changes

Updated `tests/e2e/test_main.py`:
- Replaced `TestHandleWebappData` class with `TestNotificationsHandler`
- Replaced `TestHandleCreateProfile` class with `TestNotificationSenders`
- All 19 tests passing

### New Test Coverage

- `/notifications` command handler
- `send_match_notification()` - success, failure, no bot
- `send_message_notification()` - success, failure, no bot
- `send_like_notification()` - success, failure, no bot

## Benefits

### 1. Architectural Clarity

✅ **Separation of Concerns**: Bot handles only Telegram infrastructure  
✅ **Direct Communication**: WebApp talks directly to API Gateway  
✅ **Simplified Flow**: No data passing through bot handlers  
✅ **Microservices Pattern**: Each service has a clear, focused responsibility

### 2. Scalability

✅ **Independent Scaling**: Notification service can scale independently  
✅ **Load Distribution**: Bot no longer processes WebApp data  
✅ **Async Processing**: Notifications can be queued and processed asynchronously

### 3. Development Velocity

✅ **Faster Iteration**: WebApp changes don't require bot updates  
✅ **Clear APIs**: Well-defined microservice endpoints  
✅ **Easier Testing**: Simpler bot logic, focused tests

### 4. Security

✅ **Reduced Attack Surface**: Bot doesn't process user data  
✅ **Centralized Validation**: All validation happens in microservices  
✅ **API Gateway Control**: Single point for auth, rate limiting, logging

## Migration Guide

### For Developers

No changes needed to existing code. The refactoring is backward compatible:
- `bot/api.py` still provides HTTP API for WebApp
- `bot/validation.py` and `bot/api_client.py` remain available for other code
- All microservices continue to work as before

### For Deployment

1. **Update environment variables** (optional):
   ```bash
   NOTIFICATION_SERVICE_PORT=8087
   NOTIFICATION_SERVICE_URL=http://notification-service:8087
   ```

2. **Deploy services**:
   ```bash
   docker compose up -d --build
   ```

3. **Verify services**:
   ```bash
   curl http://localhost:8080/health  # Check notification service in routes
   curl http://localhost:8087/health  # Check notification service directly
   ```

## Architecture Diagram

```
┌─────────────────┐
│   Telegram      │
│   WebApp        │
│   (Frontend)    │
└────────┬────────┘
         │
         │ HTTP (direct)
         ↓
    ┌─────────────────┐
    │  API Gateway    │◄────┐
    │   (Port 8080)   │     │
    └────────┬────────┘     │
             │              │
      Routes to services    │
             │              │
    ┌────────┴─────────────────────────┐
    │                                  │
    ↓                                  ↓
┌──────────────┐              ┌──────────────────┐
│ Profile      │              │ Notification     │
│ Discovery    │              │ Service          │
│ Chat         │              │ (Port 8087)      │
│ Media        │              └────────┬─────────┘
│ Services     │                       │
└──────────────┘                       │ Calls
                                       ↓
                              ┌──────────────────┐
                              │  Telegram Bot    │
                              │  (Port 8080)     │
                              │  - /start        │
                              │  - /notifications│
                              │  - Push notify   │
                              └──────────────────┘
```

## Future Enhancements

### Phase 2 (Optional)

- [ ] Implement message queue (RabbitMQ/Redis) for notification delivery
- [ ] Add notification preferences storage in database
- [ ] Add retry logic for failed notifications
- [ ] Add notification analytics and tracking

### Phase 3 (Optional)

- [ ] Add WebSocket support for real-time notifications
- [ ] Add notification templates with i18n support
- [ ] Add notification batching and throttling
- [ ] Add rich notifications with buttons and media

## Files Changed

### Modified Files
- `bot/main.py` (409 lines, -100 lines)
- `tests/e2e/test_main.py` (updated tests)
- `gateway/main.py` (added notification routes)
- `docker-compose.yml` (added notification service)

### New Files
- `services/notification/__init__.py`
- `services/notification/main.py`
- `services/notification/Dockerfile`
- `BOT_MINIMALIST_REFACTORING.md` (this file)

## Backward Compatibility

✅ **Fully Backward Compatible**
- Bot API server (`bot/api.py`) unchanged
- WebApp functionality unchanged
- All existing microservices unchanged
- Database schema unchanged
- Tests updated and passing (19/19)

## Related Documentation

- [REFACTORING_SUMMARY.md](REFACTORING_SUMMARY.md) - Thin Client Architecture
- [THIN_CLIENT_ARCHITECTURE.md](docs/THIN_CLIENT_ARCHITECTURE.md) - Bot API client refactoring
- [README.md](README.md) - Main project documentation
- [ROADMAP.md](ROADMAP.md) - Future development plans
