# API Versioning Strategy

## Overview

This document outlines the API versioning strategy for the Dating Platform, including current v1 implementation and future v2 planning.

## Versioning Approach

### URL Path Versioning
- **Current**: `/v1/{service}/{resource}/{action}`
- **Future**: `/v2/{service}/{resource}/{action}`
- **Benefits**: Clear versioning, easy to deprecate, client control

### Header Versioning (Alternative)
- **Accept**: `application/vnd.dating.v1+json`
- **API-Version**: `v1`
- **Benefits**: Clean URLs, content negotiation

## Current API v1

### Authentication Service
```
POST /v1/auth/validate
POST /v1/auth/refresh
GET  /v1/auth/verify
```

### Profile Service
```
GET    /v1/profiles/me
PUT    /v1/profiles/me
PATCH  /v1/profiles/progress
POST   /v1/profiles/verification/request
GET    /v1/settings/preferences
PUT    /v1/settings/preferences
GET    /v1/settings/notifications
PUT    /v1/settings/notifications
```

### Discovery Service
```
GET  /v1/discovery/candidates
POST /v1/discovery/swipe
GET  /v1/discovery/matches
GET  /v1/discovery/likes
POST /v1/discovery/block/{user_id}
POST /v1/discovery/report/{user_id}
```

### Chat Service
```
GET  /v1/chat/conversations
POST /v1/chat/conversations/{id}/messages
GET  /v1/chat/conversations/{id}/messages
PUT  /v1/chat/conversations/{id}/read-state
POST /v1/chat/blocks
DELETE /v1/chat/blocks/{target_user_id}
POST /v1/chat/reports
GET  /v1/chat/ws  # WebSocket
```

### Media Service
```
POST /v1/media/upload
GET  /v1/media/{id}
DELETE /v1/media/{id}
```

### Admin Service
```
GET  /v1/admin/users
GET  /v1/admin/photos
GET  /v1/admin/verifications
GET  /v1/admin/reports
POST /v1/admin/moderation/{id}/approve
POST /v1/admin/moderation/{id}/reject
```

## Planned API v2

### Breaking Changes

#### 1. Authentication
**v1**: `POST /v1/auth/validate`
**v2**: `POST /v2/auth/telegram/validate`
- **Reason**: More explicit about authentication method
- **Migration**: Update client to use new endpoint

#### 2. Profile Management
**v1**: `GET /v1/profiles/me`
**v2**: `GET /v2/profiles/current`
- **Reason**: More RESTful resource naming
- **Migration**: Update client to use new endpoint

#### 3. Discovery API
**v1**: `POST /v1/discovery/swipe`
**v2**: `POST /v2/discovery/interactions`
- **Reason**: More generic, supports multiple interaction types
- **Body Change**:
  ```json
  // v1
  { "target_user_id": "u123", "action": "like" }
  
  // v2
  { "target_user_id": "u123", "interaction_type": "like", "metadata": {} }
  ```

#### 4. Chat API
**v1**: `POST /v1/chat/conversations/{id}/messages`
**v2**: `POST /v2/conversations/{id}/messages`
- **Reason**: Remove service prefix, more RESTful
- **Migration**: Update client to use new endpoint

#### 5. Media API
**v1**: `POST /v1/media/upload`
**v2**: `POST /v2/assets/upload`
- **Reason**: More generic naming for future asset types
- **Migration**: Update client to use new endpoint

### New Features in v2

#### 1. Enhanced Error Responses
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input data",
    "details": {
      "field": "age",
      "reason": "must be between 18 and 100"
    },
    "request_id": "req_123",
    "timestamp": "2025-01-24T10:30:00Z"
  }
}
```

#### 2. Pagination Standardization
```json
{
  "data": [...],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 150,
    "has_next": true,
    "has_prev": false,
    "next_cursor": "eyJpZCI6MTIzfQ==",
    "prev_cursor": null
  }
}
```

#### 3. Field Selection
```
GET /v2/profiles/current?fields=name,age,photos
GET /v2/discovery/candidates?fields=id,name,age,photos,location
```

#### 4. Bulk Operations
```
POST /v2/discovery/interactions/bulk
{
  "interactions": [
    { "target_user_id": "u123", "interaction_type": "like" },
    { "target_user_id": "u124", "interaction_type": "pass" }
  ]
}
```

#### 5. Real-time Subscriptions
```
GET /v2/subscriptions/events
# Server-Sent Events for real-time updates
```

#### 6. Advanced Filtering
```
GET /v2/discovery/candidates?filter[age][min]=25&filter[age][max]=35&filter[interests][contains]=music
```

#### 7. GraphQL Support
```
POST /v2/graphql
{
  "query": "query { profiles { id name age photos { url } } }"
}
```

## Migration Strategy

### Phase 1: Parallel Support (3 months)
- Deploy v2 alongside v1
- Update documentation
- Create migration guides
- Monitor usage metrics

### Phase 2: Client Migration (6 months)
- Update all clients to use v2
- Provide migration tools
- Support both versions
- Monitor deprecation warnings

### Phase 3: v1 Deprecation (9 months)
- Announce v1 deprecation
- 6-month deprecation notice
- Gradual sunset of v1 endpoints
- Final removal of v1

## Version Detection

### Client Detection
```javascript
// Frontend version detection
const apiVersion = localStorage.getItem('api_version') || 'v1';
const baseURL = `https://api.dating.serge.cc/${apiVersion}`;
```

### Server Detection
```python
# Gateway version routing
async def route_request(request):
    version = request.match_info.get('version', 'v1')
    if version == 'v2':
        return await route_v2(request)
    else:
        return await route_v1(request)
```

## Backward Compatibility

### v1 Support Timeline
- **Current**: Full v1 support
- **v2 Launch**: v1 + v2 parallel support
- **v1 Deprecation**: 6-month notice period
- **v1 Sunset**: Complete removal

### Breaking Change Policy
- **Major versions**: Breaking changes allowed
- **Minor versions**: Backward compatible
- **Patch versions**: Bug fixes only

## Documentation

### API Documentation
- **OpenAPI 3.0**: Swagger/ReDoc documentation
- **Version-specific**: Separate docs for v1 and v2
- **Migration guides**: Step-by-step client updates
- **Changelog**: Detailed change tracking

### Client SDKs
- **JavaScript**: `@dating/sdk` npm package
- **Python**: `dating-sdk` PyPI package
- **Version support**: v1 and v2 in same SDK

## Testing Strategy

### Version Testing
```yaml
# CI/CD pipeline
test_v1:
  - Unit tests for v1 endpoints
  - Integration tests for v1 flows
  - Performance tests for v1

test_v2:
  - Unit tests for v2 endpoints
  - Integration tests for v2 flows
  - Performance tests for v2
  - Migration tests from v1 to v2
```

### Compatibility Testing
- **v1 → v2**: Migration path testing
- **v2 → v1**: Rollback testing
- **Mixed clients**: v1 and v2 clients simultaneously

## Monitoring

### Metrics
- **Version usage**: Track v1 vs v2 usage
- **Error rates**: Monitor version-specific errors
- **Performance**: Compare v1 vs v2 performance
- **Migration success**: Track client migration progress

### Alerts
- **High v1 usage**: Alert when v1 usage is high
- **v2 errors**: Alert on v2 error spikes
- **Migration failures**: Alert on migration issues

## Implementation Plan

### Q1 2025: v2 Design
- [ ] Finalize v2 API design
- [ ] Create OpenAPI specifications
- [ ] Design migration strategy
- [ ] Plan client SDK updates

### Q2 2025: v2 Development
- [ ] Implement v2 endpoints
- [ ] Add v2 middleware
- [ ] Create v2 tests
- [ ] Update documentation

### Q3 2025: v2 Launch
- [ ] Deploy v2 alongside v1
- [ ] Update client SDKs
- [ ] Begin client migration
- [ ] Monitor usage metrics

### Q4 2025: v1 Deprecation
- [ ] Announce v1 deprecation
- [ ] Complete client migration
- [ ] Sunset v1 endpoints
- [ ] Remove v1 code

## Security Considerations

### Version Security
- **Authentication**: Same JWT tokens for v1 and v2
- **Authorization**: Consistent permission model
- **Rate limiting**: Version-specific limits
- **CORS**: Support both versions

### Migration Security
- **Token validation**: Ensure tokens work in both versions
- **Data integrity**: Maintain data consistency during migration
- **Rollback**: Secure rollback procedures

## Performance Considerations

### Version Performance
- **v1 optimization**: Maintain v1 performance
- **v2 optimization**: Optimize v2 for new features
- **Resource usage**: Monitor version-specific resource usage
- **Caching**: Version-specific cache strategies

### Migration Performance
- **Zero downtime**: Seamless version switching
- **Data migration**: Efficient data migration tools
- **Rollback**: Quick rollback capabilities

## Conclusion

The API versioning strategy provides a clear path for evolution while maintaining backward compatibility. The v2 API introduces modern RESTful patterns, enhanced error handling, and new features while ensuring a smooth migration path for existing clients.

Key benefits:
- **Future-proof**: Designed for long-term evolution
- **Client-friendly**: Clear migration path
- **Performance**: Optimized for modern use cases
- **Security**: Consistent security model
- **Monitoring**: Comprehensive version tracking
