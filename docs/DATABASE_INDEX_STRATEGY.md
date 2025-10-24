# Database Index Strategy

**Version**: 1.0  
**Last Updated**: 2025-01-24

## Overview

This document outlines the comprehensive database indexing strategy for the dating platform, optimized for high-performance queries across all microservices.

## Index Categories

### 1. Primary Key Indexes (Automatic)
All tables have primary key indexes created automatically by PostgreSQL:
- `users.id` (PK)
- `profiles.id` (PK) 
- `photos.id` (PK)
- `interactions.id` (PK)
- `matches.id` (PK)
- `messages.id` (PK)
- `conversations.id` (PK)
- `notifications.id` (PK)
- `reports.id` (PK)
- `likes.id` (PK)

### 2. Foreign Key Indexes
Essential for JOIN operations and referential integrity:

```sql
-- User relationships
idx_profiles_user_id (profiles.user_id)
idx_photos_user_id (photos.user_id)
idx_user_preferences_user_id (user_preferences.user_id)
idx_user_activity_user_id (user_activity.user_id)

-- Interaction relationships
idx_interactions_user_id (interactions.user_id)
idx_interactions_target_id (interactions.target_user_id)
idx_matches_user1 (matches.user1_id)
idx_matches_user2 (matches.user2_id)
idx_likes_liker_id (likes.liker_id)
idx_likes_liked_id (likes.liked_id)

-- Chat relationships
idx_conversations_user1 (conversations.user1_id)
idx_conversations_user2 (conversations.user2_id)
idx_messages_conversation_id (messages.conversation_id)
idx_messages_sender_id (messages.sender_id)

-- Notification relationships
idx_notifications_user_id (notifications.user_id)

-- Report relationships
idx_reports_reporter_id (reports.reporter_id)
idx_reports_reported_user_id (reports.reported_user_id)
```

### 3. Composite Indexes for Business Logic

#### Discovery & Matching
```sql
-- Prevent duplicate interactions
idx_interactions_user_target (interactions.user_id, target_user_id)

-- Optimize discovery queries
idx_profiles_age_gender (profiles.age, gender)
idx_profiles_location_gist (profiles.location) -- GIST for spatial queries
idx_profiles_city (profiles.city)

-- User preferences filtering
idx_user_preferences_age_range (user_preferences.min_age, max_age)
idx_user_preferences_distance (user_preferences.max_distance)
```

#### Chat & Messaging
```sql
-- Message pagination (most critical)
idx_messages_conversation_created (messages.conversation_id, created_at, id)

-- Conversation lookup
idx_conversations_users (conversations.user1_id, user2_id)

-- Read state tracking
idx_participant_read_state_user (participant_read_state.user_id)
```

#### User Activity & Engagement
```sql
-- Activity tracking
idx_user_activity_last_active (user_activity.last_active_at)

-- Recent interactions
idx_interactions_created_at (interactions.created_at)
idx_likes_created_at (likes.created_at)

-- Photo management
idx_photos_user_id_sort (photos.user_id, sort_order)
idx_photos_is_primary (photos.is_primary)
```

### 4. Performance Optimization Indexes

#### Time-based Queries
```sql
-- Temporal ordering
idx_profiles_created_at (profiles.created_at)
idx_messages_created_at (messages.created_at)
idx_notifications_created_at (notifications.created_at)
idx_reports_created_at (reports.created_at)

-- Recent activity
idx_interactions_created_at (interactions.created_at)
idx_likes_created_at (likes.created_at)
```

#### Status & State Queries
```sql
-- Notification status
idx_notifications_read_created (notifications.is_read, created_at)
idx_notifications_user_type (notifications.user_id, notification_type)

-- Report status
idx_reports_status (reports.status)
idx_reports_created_status (reports.created_at, status)
idx_reports_reported_status (reports.reported_user_id, status)

-- Chat blocks
idx_chat_blocks_blocker (chat_blocks.blocker_id)
idx_chat_blocks_target (chat_blocks.target_user_id)
```

#### Search & Filtering
```sql
-- User search
idx_users_tg_username (users.tg_username)
idx_users_ip_address (users.ip_address)
idx_users_risk_score (users.risk_score)

-- Admin operations
idx_admins_username (admins.username)
idx_admins_email (admins.email)
```

## Query-Specific Optimizations

### 1. Discovery Service Queries

**Location-based Discovery:**
```sql
-- Optimized with GIST index on location
SELECT * FROM profiles 
WHERE location && ST_MakeEnvelope($1, $2, $3, $4, 4326)
AND age BETWEEN $5 AND $6
AND gender = $7
ORDER BY ST_Distance(location, ST_Point($8, $9, 4326));
```

**Preference Filtering:**
```sql
-- Uses composite indexes for age and distance
SELECT p.* FROM profiles p
JOIN user_preferences up ON up.user_id = $1
WHERE p.age BETWEEN up.min_age AND up.max_age
AND ST_DWithin(p.location, up.location, up.max_distance);
```

### 2. Chat Service Queries

**Message Pagination:**
```sql
-- Critical for chat performance
SELECT * FROM messages 
WHERE conversation_id = $1
ORDER BY created_at DESC, id DESC
LIMIT 50;
```

**Read State Updates:**
```sql
-- Optimized participant read state
UPDATE participant_read_state 
SET last_read_message_id = $1, last_read_at = NOW()
WHERE conversation_id = $2 AND user_id = $3;
```

### 3. Profile Service Queries

**Profile with Photos:**
```sql
-- Efficient profile loading
SELECT p.*, array_agg(ph.url ORDER BY ph.sort_order) as photos
FROM profiles p
LEFT JOIN photos ph ON p.user_id = ph.user_id
WHERE p.user_id = $1
GROUP BY p.id;
```

### 4. Analytics Queries

**Daily Active Users:**
```sql
-- Time-series analytics
SELECT DATE(last_active_at) as date, COUNT(*) as dau
FROM user_activity
WHERE last_active_at >= CURRENT_DATE - INTERVAL '30 days'
GROUP BY DATE(last_active_at)
ORDER BY date DESC;
```

## Index Maintenance

### 1. Monitoring
- **Query Performance**: Monitor slow queries (>1s)
- **Index Usage**: Track index hit ratios
- **Storage Impact**: Monitor index size growth

### 2. Maintenance Tasks
```sql
-- Analyze table statistics
ANALYZE profiles;
ANALYZE messages;
ANALYZE interactions;

-- Reindex if needed
REINDEX INDEX idx_messages_conversation_created;
```

### 3. Performance Metrics
- **Index Hit Ratio**: Should be >95%
- **Query Execution Time**: <100ms for most queries
- **Index Size**: Monitor growth vs. table size

## Index Size Estimates

| Table | Estimated Rows | Index Count | Estimated Size |
|-------|----------------|-------------|----------------|
| users | 100K | 4 | 50MB |
| profiles | 100K | 6 | 100MB |
| photos | 300K | 3 | 75MB |
| interactions | 1M | 4 | 200MB |
| messages | 10M | 4 | 500MB |
| notifications | 500K | 4 | 100MB |
| **Total** | **~12M** | **25** | **~1GB** |

## Best Practices

### 1. Index Design Principles
- **Selectivity**: High cardinality columns first
- **Query Patterns**: Index columns used in WHERE clauses
- **Sort Order**: Match ORDER BY clauses
- **Composite Order**: Most selective columns first

### 2. Avoid Over-Indexing
- **Write Performance**: Each index slows INSERT/UPDATE
- **Storage Cost**: Indexes consume disk space
- **Maintenance**: More indexes = more maintenance

### 3. Index Types by Use Case
- **B-tree**: Equality and range queries
- **GIST**: Spatial and geometric data
- **Hash**: Simple equality lookups
- **Partial**: Conditional indexes for specific cases

## Migration Strategy

### 1. Index Creation Order
1. **Foreign Key Indexes** (essential for JOINs)
2. **Composite Business Logic Indexes** (discovery, chat)
3. **Performance Optimization Indexes** (time-based, status)
4. **Search Indexes** (admin, user lookup)

### 2. Rollback Strategy
- All indexes have corresponding DROP statements
- Test rollback procedures in staging
- Monitor performance during index creation

### 3. Production Deployment
- Create indexes during low-traffic periods
- Use `CONCURRENTLY` for large tables
- Monitor system performance during creation

## Performance Testing

### 1. Query Performance Script
```bash
# Run performance tests
python scripts/test_query_performance.py
```

### 2. Key Metrics
- **Execution Time**: <100ms for most queries
- **Index Usage**: >95% hit ratio
- **Query Plans**: Avoid sequential scans
- **Memory Usage**: Monitor buffer usage

### 3. Load Testing
- **Concurrent Users**: Test with 100+ concurrent connections
- **Query Mix**: Realistic query distribution
- **Performance Degradation**: Monitor under load

## Monitoring & Alerts

### 1. Key Metrics
- **Slow Queries**: >1s execution time
- **Index Bloat**: >30% bloat ratio
- **Missing Indexes**: Sequential scan warnings
- **Lock Contention**: High lock wait times

### 2. Alerting Thresholds
- **Query Time**: >500ms average
- **Index Hit Ratio**: <90%
- **Lock Wait Time**: >100ms
- **Connection Pool**: >80% utilization

---

**Implementation Status**: ✅ Complete  
**Testing**: ✅ Performance tests included  
**Monitoring**: ✅ Metrics and alerts configured  
**Documentation**: ✅ This comprehensive guide
