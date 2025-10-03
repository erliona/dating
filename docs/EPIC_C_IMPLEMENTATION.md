# Epic C Implementation Guide

## Overview

This document describes the implementation of Epic C — Discovery/свайпы/матчи/избранное (Discovery/swipes/matches/favorites) for the Dating Mini App.

## Features Implemented

### C1. Candidate Generation + Filters

**Endpoint:** `GET /api/discover`

**Features:**
- Cursor-based pagination for scalability
- Response time ≤200ms (p95) from cache
- Multiple filters supported:
  - Age range (age_min, age_max)
  - Distance (max_distance_km)
  - Relationship goal
  - Height range (height_min, height_max)
  - Lifestyle filters (has_children, smoking, drinking)
  - Education level
  - Verified profiles only

**Query Parameters:**
```
GET /api/discover?limit=10&cursor=123&age_min=25&age_max=35&goal=dating
```

**Response:**
```json
{
  "profiles": [
    {
      "id": 123,
      "user_id": 456,
      "name": "Alice",
      "age": 28,
      "gender": "female",
      "goal": "dating",
      "bio": "Love traveling...",
      "interests": ["travel", "music"],
      "height_cm": 165,
      "education": "bachelor",
      "city": "Moscow",
      "photos": [
        {"url": "https://...", "is_verified": true}
      ]
    }
  ],
  "next_cursor": 124,
  "count": 10
}
```

**Caching Strategy:**
- Discovery results are not cached directly to ensure fresh candidates
- Profile data is cached at the repository level (5 min TTL)

### C2. Swipes and Gestures

#### Like/Superlike

**Endpoint:** `POST /api/like`

**Features:**
- Idempotent - multiple likes don't create duplicates
- Automatic mutual match detection
- Superlike support (priority in discovery)

**Request Body:**
```json
{
  "target_id": 456,
  "type": "like"  // or "superlike"
}
```

**Response:**
```json
{
  "success": true,
  "match_id": 789  // Only present if mutual match created
}
```

#### Pass/Dislike

**Endpoint:** `POST /api/pass`

**Request Body:**
```json
{
  "target_id": 456
}
```

**Response:**
```json
{
  "success": true
}
```

**Idempotency:**
- Creating the same interaction multiple times updates the timestamp
- Changing from like to superlike (or vice versa) updates the interaction type
- All interaction operations are idempotent

### C3. Likes/Superlikes/Matches

**Features:**
- Automatic match creation on mutual like
- Match normalization (user1_id < user2_id)
- Idempotent match creation
- Cache invalidation on match creation

**Match Detection Flow:**
1. User A likes User B → Interaction created
2. User B likes User A → Interaction created + mutual check
3. Mutual like detected → Match created automatically
4. Both users receive match_id in response

**Endpoint:** `GET /api/matches`

**Query Parameters:**
```
GET /api/matches?limit=20&cursor=100
```

**Response:**
```json
{
  "matches": [
    {
      "match_id": 789,
      "created_at": "2024-10-03T12:00:00Z",
      "profile": {
        "id": 123,
        "user_id": 456,
        "name": "Alice",
        "age": 28,
        "bio": "...",
        "photos": [{"url": "https://..."}]
      }
    }
  ],
  "next_cursor": 788,
  "count": 20
}
```

**Caching:**
- Matches list cached for 3 minutes
- Cache invalidated when new match is created

### C4. Favorites

#### Add to Favorites

**Endpoint:** `POST /api/favorites`

**Request Body:**
```json
{
  "target_id": 456
}
```

**Response:**
```json
{
  "success": true,
  "favorite_id": 123
}
```

#### Remove from Favorites

**Endpoint:** `DELETE /api/favorites/{target_id}`

**Response:**
```json
{
  "success": true
}
```

#### Get Favorites

**Endpoint:** `GET /api/favorites`

**Query Parameters:**
```
GET /api/favorites?limit=20&cursor=100
```

**Response:**
```json
{
  "favorites": [
    {
      "favorite_id": 123,
      "created_at": "2024-10-03T12:00:00Z",
      "profile": {
        "id": 456,
        "user_id": 789,
        "name": "Bob",
        "age": 30,
        "bio": "...",
        "photos": [{"url": "https://..."}]
      }
    }
  ],
  "next_cursor": 122,
  "count": 20
}
```

**Caching:**
- Favorites list cached for 5 minutes
- Cache invalidated on add/remove operations

## Database Schema

### Interactions Table

```sql
CREATE TABLE interactions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    target_id INTEGER NOT NULL,
    interaction_type VARCHAR(20) NOT NULL, -- 'like', 'superlike', 'pass'
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, target_id),
    CHECK (interaction_type IN ('like', 'superlike', 'pass'))
);

CREATE INDEX idx_interactions_user_id ON interactions(user_id);
CREATE INDEX idx_interactions_target_id ON interactions(target_id);
CREATE INDEX idx_interactions_user_target ON interactions(user_id, target_id);
```

### Matches Table

```sql
CREATE TABLE matches (
    id SERIAL PRIMARY KEY,
    user1_id INTEGER NOT NULL,
    user2_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user1_id, user2_id),
    CHECK (user1_id < user2_id)
);

CREATE INDEX idx_matches_user1 ON matches(user1_id);
CREATE INDEX idx_matches_user2 ON matches(user2_id);
```

### Favorites Table

```sql
CREATE TABLE favorites (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL,
    target_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, target_id)
);

CREATE INDEX idx_favorites_user_id ON favorites(user_id);
CREATE INDEX idx_favorites_target_id ON favorites(target_id);
```

## Cache System

### Architecture

The cache system uses an in-memory store with TTL (Time To Live) support. In production, this can be replaced with Redis.

**File:** `bot/cache.py`

### Usage

```python
from bot.cache import get_cache

cache = get_cache()

# Set value with TTL
cache.set("key", "value", ttl=300)  # 5 minutes

# Get value
value = cache.get("key")  # Returns None if not found or expired

# Delete single key
cache.delete("key")

# Delete by pattern
cache.delete_pattern("user:123:")  # Deletes all keys starting with "user:123:"

# Get statistics
stats = cache.get_stats()
# {"size": 100, "hits": 850, "misses": 150, "hit_rate": 85.0}
```

### Cache Keys

- **Discovery:** Not cached directly (to ensure fresh candidates)
- **Profiles:** `profile:{user_id}` (TTL: 5 minutes)
- **Matches:** `matches:{user_id}:{cursor}:{limit}` (TTL: 3 minutes)
- **Favorites:** `favorites:{user_id}:{cursor}:{limit}` (TTL: 5 minutes)

### Cache Invalidation

- **Matches:** Invalidated when new match is created
- **Favorites:** Invalidated when favorite is added or removed
- **Profile updates:** Should invalidate profile cache (implement as needed)

## Repository Methods

### Discovery

```python
from bot.repository import ProfileRepository

async with session_maker() as session:
    repository = ProfileRepository(session)
    
    profiles, next_cursor = await repository.find_candidates(
        user_id=user.id,
        limit=10,
        cursor=None,
        age_min=25,
        age_max=35,
        goal="dating"
    )
```

### Interactions

```python
# Create interaction (idempotent)
interaction = await repository.create_interaction(
    user_id=1,
    target_id=2,
    interaction_type="like"
)

# Check for mutual like
is_mutual = await repository.check_mutual_like(user_id=1, target_id=2)
```

### Matches

```python
# Create match (idempotent, normalized)
match = await repository.create_match(user1_id=1, user2_id=2)

# Get matches with pagination
matches, next_cursor = await repository.get_matches(
    user_id=1,
    limit=20,
    cursor=None
)
```

### Favorites

```python
# Add to favorites (idempotent)
favorite = await repository.add_favorite(user_id=1, target_id=2)

# Remove from favorites
removed = await repository.remove_favorite(user_id=1, target_id=2)

# Get favorites with pagination
favorites, next_cursor = await repository.get_favorites(
    user_id=1,
    limit=20,
    cursor=None
)
```

## Authentication

All endpoints require JWT authentication via the `Authorization` header:

```
Authorization: Bearer <jwt_token>
```

Generate a token using:
```
POST /api/auth/token
Body: {"user_id": 12345}
```

## Error Handling

All endpoints return consistent error format:

```json
{
  "error": {
    "code": "validation_error",
    "message": "target_id is required"
  }
}
```

**Error Codes:**
- `invalid_init_data` - Authentication failed
- `validation_error` - Invalid request parameters
- `not_found` - Resource not found
- `internal_error` - Server error

## Performance

### Metrics

- **Discovery endpoint:** ≤200ms (p95) for cached results
- **Like/pass endpoints:** <50ms average
- **Match creation:** <100ms average
- **Cache hit rate:** Target 85%+

### Optimization Tips

1. **Pagination:** Always use cursor-based pagination for large datasets
2. **Caching:** Leverage cache for frequently accessed data
3. **Indexes:** All foreign keys and frequently queried columns are indexed
4. **Batch operations:** Consider batch operations for bulk actions

## Migration

To apply the database migration:

```bash
# Run migration
alembic upgrade head

# Rollback if needed
alembic downgrade -1
```

The migration creates three new tables: `interactions`, `matches`, and `favorites`.

## Testing

Run tests with:

```bash
# All tests
pytest tests/

# Cache tests only
pytest tests/test_cache.py

# Discovery tests only
pytest tests/test_discovery.py
```

**Test Coverage:**
- 11 cache tests
- 14 discovery/interaction/match/favorite tests
- All operations tested for idempotency
- Pagination tested
- Error cases covered

## Future Enhancements

### Phase 2 (Optional)

1. **Rate Limiting:**
   - Daily like limits for free users
   - Superlike limits
   - Premium user unlimited likes

2. **Boost System:**
   - Profile visibility boost (paid feature)
   - Priority in discovery queue

3. **Undo Last Action:**
   - Store last interaction
   - Allow undo once per session

4. **Advanced Filters:**
   - Interests matching score
   - Distance-based sorting
   - Recently active users

5. **Recommendation Engine:**
   - ML-based candidate scoring
   - Interest compatibility
   - Engagement prediction

6. **Analytics Events:**
   - `card_view` - Profile viewed
   - `like_sent` - Like sent
   - `superlike_sent` - Superlike sent
   - `match_created` - Mutual match
   - `favorite_added` - Added to favorites

## Production Considerations

### Scaling

1. **Redis Migration:**
   - Replace in-memory cache with Redis
   - Use Redis Cluster for high availability
   - Configure cache invalidation via pub/sub

2. **Database:**
   - Monitor query performance
   - Add database replicas for read scaling
   - Consider sharding for very large datasets

3. **Monitoring:**
   - Track cache hit rates
   - Monitor API response times
   - Alert on high error rates

### Security

1. **Rate Limiting:**
   - Implement per-user rate limits
   - Prevent spam/abuse
   - Use Redis for distributed rate limiting

2. **Data Privacy:**
   - Don't expose internal user IDs in public APIs
   - Audit logs for sensitive operations
   - GDPR compliance for user data

## Support

For questions or issues, refer to:
- Main README: `/README.md`
- API Specification: `/SPEC.md`
- Other Epic implementations: `/docs/EPIC_*_IMPLEMENTATION.md`
