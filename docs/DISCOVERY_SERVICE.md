# Discovery Service Documentation

## Overview

The Discovery Service handles the core matching algorithm, candidate discovery, and user interactions (swipes, likes, matches) for the dating platform.

## Endpoints

### 1. Get Candidates
**GET** `/discovery/candidates`

Retrieve potential matches for a user.

**Query Parameters:**
- `user_id` (required): User ID
- `limit` (optional): Number of candidates (default: 10)
- `cursor` (optional): Pagination cursor
- `lat`, `lon` (optional): User's location for distance-based matching
- `age_min`, `age_max` (optional): Age range filter
- `max_distance_km` (optional): Maximum distance in kilometers
- `goal` (optional): Relationship goal filter
- `height_min`, `height_max` (optional): Height range filter
- `has_children` (optional): Children preference filter
- `smoking` (optional): Smoking preference filter
- `drinking` (optional): Drinking preference filter
- `education` (optional): Education level filter
- `verified_only` (optional): Show only verified profiles

**Response:**
```json
{
  "candidates": [
    {
      "id": 123,
      "name": "Alice",
      "age": 25,
      "bio": "Love hiking and coffee",
      "photos": ["photo1.jpg", "photo2.jpg"],
      "location": "New York, NY",
      "distance_km": 5.2,
      "interests": ["hiking", "coffee", "travel"],
      "verified": true
    }
  ],
  "cursor": "next_page_token"
}
```

### 2. Swipe User
**POST** `/discovery/swipe`

Unified endpoint for liking or passing on a user.

**Request Body:**
```json
{
  "user_id": 123,
  "target_user_id": 456,
  "action": "like" | "pass"
}
```

**Response:**
```json
{
  "is_match": true,
  "match_id": "match_123",
  "message": "It's a match!"
}
```

### 3. Get Likes
**GET** `/discovery/likes`

Get users who liked the current user.

**Query Parameters:**
- `user_id` (required): User ID
- `limit` (optional): Number of likes (default: 20)

**Response:**
```json
{
  "likes": [
    {
      "id": 789,
      "name": "Bob",
      "age": 30,
      "bio": "Looking for adventure",
      "photos": ["photo1.jpg"],
      "liked_at": "2024-01-24T10:30:00Z"
    }
  ]
}
```

### 4. Get Matches
**GET** `/discovery/matches`

Get user's matches.

**Query Parameters:**
- `user_id` (required): User ID
- `limit` (optional): Number of matches (default: 20)

**Response:**
```json
{
  "matches": [
    {
      "id": 456,
      "name": "Charlie",
      "age": 28,
      "bio": "Love music and art",
      "photos": ["photo1.jpg", "photo2.jpg"],
      "matched_at": "2024-01-24T10:30:00Z",
      "last_message": "Hey! How are you?",
      "unread_count": 2
    }
  ]
}
```

## Geocoding Integration

### Location-Based Matching
The service integrates with Nominatim for geocoding and distance calculations:

```python
# Reverse geocoding
location_info = await reverse_geocode(lat, lon)
# Returns: {"city": "New York", "country": "United States", ...}

# Distance calculation
distance = calculate_distance(lat1, lon1, lat2, lon2)
# Returns: distance in kilometers
```

### Supported Location Features
- **Reverse Geocoding**: Convert coordinates to city/country
- **Distance Calculation**: Haversine formula for accurate distances
- **Location Filtering**: Filter candidates by distance
- **Smart Matching**: Prioritize local matches

## Matching Algorithm

### Smart Filtering
1. **Basic Filters**: Age, distance, preferences
2. **Interest Overlap**: Jaccard similarity for interests
3. **Location Priority**: Local matches first
4. **Verification Boost**: Verified profiles prioritized
5. **Activity Score**: Recent activity weighting

### ELO Rating System
- **Initial Rating**: 1200 for new users
- **K-Factor**: 32 for active users
- **Rating Update**: After each swipe interaction
- **Match Probability**: Based on rating similarity

## Event Publishing

### Match Events
When a match occurs, the service publishes events:

```python
await event_publisher.publish_match_event(
    user_id=user_id,
    target_user_id=target_user_id,
    match_id=match_id
)
```

### Event Types
- **Match Created**: New match between users
- **Swipe Recorded**: User interaction logged
- **Location Updated**: User location changed

## Metrics & Analytics

### Business Metrics
- **Swipe Rate**: Swipes per user per day
- **Match Rate**: Matches per swipe
- **Distance Distribution**: Average match distance
- **Filter Usage**: Most popular filters
- **Geocoding Success**: Location resolution rate

### Performance Metrics
- **Candidate Retrieval Time**: Query performance
- **Geocoding Latency**: Location service response time
- **Match Calculation Time**: Algorithm performance
- **Event Publishing Time**: Message queue performance

## Error Handling

### Common Errors
- **400 Bad Request**: Missing required parameters
- **404 Not Found**: User not found
- **500 Internal Server Error**: Service unavailable

### Error Response Format
```json
{
  "error": "Error message",
  "code": "ERROR_CODE",
  "details": {
    "field": "validation error"
  }
}
```

## Testing

### Unit Tests
- **Endpoint Testing**: All endpoints with various inputs
- **Geocoding Testing**: Location service integration
- **Algorithm Testing**: Matching logic validation
- **Error Handling**: Edge cases and failures

### Integration Tests
- **Data Service Integration**: Database operations
- **Event Publishing**: Message queue integration
- **Geocoding Service**: Nominatim integration
- **End-to-End**: Complete user flows

## Configuration

### Environment Variables
```bash
# Data Service URL
DATA_SERVICE_URL=http://data-service:8088

# Nominatim URL
NOMINATIM_URL=http://nominatim:8080

# Event Publisher
RABBITMQ_URL=amqp://rabbitmq:5672
```

### Service Dependencies
- **Data Service**: Profile and interaction data
- **Nominatim**: Geocoding and location services
- **RabbitMQ**: Event publishing
- **PostgreSQL**: Database operations

## Performance Optimization

### Database Indexes
```sql
-- Profile location index
CREATE INDEX idx_profiles_location ON profiles USING GIST (location);

-- Interaction user index
CREATE INDEX idx_interactions_user ON interactions(user_id, created_at DESC);

-- Match index
CREATE INDEX idx_matches_users ON matches(user1_id, user2_id);
```

### Caching Strategy
- **Candidate Cache**: 30-minute TTL for candidate lists
- **Location Cache**: 1-hour TTL for geocoding results
- **User Preferences**: 15-minute TTL for user settings

### Query Optimization
- **Pagination**: Cursor-based pagination for large datasets
- **Filtering**: Database-level filtering for performance
- **Distance Calculation**: Optimized Haversine implementation
- **Batch Operations**: Bulk operations for efficiency

## Security Considerations

### Input Validation
- **User ID Validation**: Ensure valid user IDs
- **Location Validation**: Validate coordinate ranges
- **Filter Validation**: Sanitize filter parameters
- **Rate Limiting**: Prevent abuse of endpoints

### Privacy Protection
- **Location Privacy**: Optional location sharing
- **Profile Visibility**: Respect user privacy settings
- **Data Retention**: Automatic cleanup of old data
- **Audit Logging**: Track all user interactions

## Monitoring & Alerting

### Key Metrics
- **Swipe Rate**: Monitor user engagement
- **Match Rate**: Track algorithm effectiveness
- **Error Rate**: Monitor service health
- **Response Time**: Performance monitoring

### Alerts
- **High Error Rate**: >5% error rate
- **Slow Response**: >2s response time
- **Low Match Rate**: <10% match rate
- **Geocoding Failures**: >20% failure rate

## Future Enhancements

### Planned Features
- **Machine Learning**: AI-powered matching
- **Advanced Filters**: More sophisticated filtering
- **Location History**: Track user movement patterns
- **Social Integration**: Connect with social media
- **Video Profiles**: Video introduction support

### Performance Improvements
- **Redis Caching**: Advanced caching strategy
- **CDN Integration**: Global content delivery
- **Microservice Scaling**: Horizontal scaling
- **Database Sharding**: Partition large datasets
