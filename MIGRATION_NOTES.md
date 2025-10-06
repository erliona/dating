# Migration Notes: Database Removal from Bot

## Summary

All direct database access has been successfully removed from the bot directory (`bot/api.py` and `bot/main.py`). The bot now exclusively uses the API Gateway client for all operations.

## Test Updates Required

The following tests in `tests/integration/test_api.py` need to be updated to reflect the new thin client architecture:

### 1. Upload Photo Handler Tests

These tests are now failing with HTTP 501 (Not Implemented) because `upload_photo_handler` has been deprecated:

- `test_upload_photo_authentication_required`
- `test_upload_photo_no_data`
- `test_upload_photo_invalid_slot_index`
- `test_upload_photo_too_large`
- `test_upload_photo_invalid_mime_type`

**Recommended Action**: Either skip these tests or update them to test the API Gateway `/api/photos/upload` endpoint instead. Photo uploads should now go directly through the media service via API Gateway.

### 2. Create App Tests

The test `test_create_app_without_cdn` expects `session_maker` in the app, which has been removed:

```python
assert "session_maker" in app  # This assertion fails
```

**Recommended Action**: Update the test to expect `api_client` instead:

```python
# Old test (no longer valid)
app = create_app(config, session_maker=mock_session_maker)
assert "session_maker" in app

# New test (thin client mode)
app = create_app(config, api_client=mock_api_client)
assert "api_client" in app
```

### 3. Check Profile Handler Tests

These tests mock `ProfileRepository` which is no longer used:

- `test_check_profile_exists`
- `test_check_profile_not_exists`
- `test_check_profile_missing_user_id`
- `test_check_profile_invalid_user_id`

**Recommended Action**: Update tests to mock `APIGatewayClient` instead of `ProfileRepository`:

```python
# Old approach (no longer valid)
with patch("bot.api.ProfileRepository", return_value=mock_repository):
    ...

# New approach (thin client mode)
with patch("bot.api_client.APIGatewayClient.check_profile", return_value={"has_profile": True}):
    ...
```

## Architecture Changes

### Before (Legacy Mode)
```
bot/api.py → ProfileRepository → Database
```

### After (Thin Client Mode)
```
bot/api.py → APIGatewayClient → API Gateway → Microservices → Database
```

## Benefits

1. **Zero Direct Database Access**: Bot directory has no database dependencies
2. **Consistent Architecture**: All operations go through API Gateway
3. **Better Scalability**: Bot and services scale independently
4. **Simplified Deployment**: Bot doesn't need database credentials
5. **Centralized Control**: All access control and validation in one place

## Breaking Changes

### 1. API Server Requires API Gateway

The bot API server (`bot/api.py`) now requires an `api_client` parameter and will not start without it:

```python
# This will raise ValueError
app = create_app(config)  # Missing api_client

# Correct usage
api_client = APIGatewayClient(gateway_url)
app = create_app(config, api_client)
```

### 2. Photo Upload Endpoint Deprecated

The `/api/photos/upload` endpoint in `bot/api.py` now returns HTTP 501. Clients should upload directly to API Gateway:

```
Old: POST http://bot-api:8080/api/photos/upload
New: POST http://api-gateway:8080/api/photos/upload
```

### 3. No Legacy Database Mode

The legacy database mode has been completely removed from `bot/main.py`. The `DATABASE_URL` environment variable is no longer used by the bot.

## Environment Variables

### Required
- `API_GATEWAY_URL`: URL of the API Gateway (e.g., `http://api-gateway:8080`)
- `BOT_TOKEN`: Telegram bot token

### No Longer Used
- `DATABASE_URL`: Not used by bot anymore (microservices still need it)

## Migration Checklist for Deployments

- [ ] Set `API_GATEWAY_URL` environment variable
- [ ] Ensure API Gateway is running and accessible
- [ ] Update WebApp to upload photos directly to API Gateway
- [ ] Remove `DATABASE_URL` from bot configuration (optional, ignored anyway)
- [ ] Update monitoring/alerts if checking for database connections from bot
- [ ] Update tests as described above

## Rollback Plan

If issues arise, the changes can be reverted:

```bash
git revert dbe1fe2  # Revert "Remove all direct database access from bot directory"
git revert 8ecbe73  # Revert "Add API client support to all bot/api.py handlers"
```

However, this would restore the old direct database access architecture, which is not recommended.

## Next Steps

1. Update integration tests as described above
2. Test all endpoints with API Gateway in staging environment
3. Update deployment documentation
4. Consider removing `bot/repository.py` if no longer needed elsewhere
5. Implement proper photo upload through media service
