"""Centralized business metrics for the dating application."""

from prometheus_client import Counter, Gauge

# Profile metrics - Counter for events (increment only)
PROFILE_CREATED = Counter(
    'profile_created_total',
    'Total profiles created',
    ['service']
)

PROFILE_UPDATED = Counter(
    'profile_updated_total',
    'Total profiles updated',
    ['service']
)

PROFILE_DELETED = Counter(
    'profile_deleted_total',
    'Total profiles deleted',
    ['service']
)

# Interaction metrics - Counter for events
INTERACTION_CREATED = Counter(
    'interaction_created_total',
    'Total interactions (likes, dislikes, matches)',
    ['service', 'type']
)

SWIPES_TOTAL = Counter(
    'swipes_total',
    'Total swipes (likes + dislikes)',
    ['service', 'type']
)

# Message metrics - Counter for events
MESSAGE_SENT = Counter(
    'message_sent_total',
    'Total messages sent',
    ['service']
)

CONVERSATION_STARTED = Counter(
    'conversation_started_total',
    'Total conversations started',
    ['service']
)

# Current state gauges (synchronized with database)
USERS_ACTIVE = Gauge(
    'active_users_total',
    'Number of users active in last 24h',
    ['service']
)

USERS_BY_REGION = Gauge(
    'users_by_region',
    'Users by geographic region',
    ['service', 'region']
)

MATCHES_CURRENT = Gauge(
    'matches_current',
    'Current number of matches',
    ['service']
)

CONVERSATIONS_ACTIVE = Gauge(
    'conversations_active',
    'Number of active conversations',
    ['service']
)

# Legacy metrics for backward compatibility (will be deprecated)
USERS_TOTAL = Gauge(
    'users_total',
    'Total number of users (legacy - use profile_created_total)',
    ['service']
)

MATCHES_TOTAL = Gauge(
    'matches_total',
    'Total number of matches (legacy - use interaction_created_total)',
    ['service']
)

MESSAGES_TOTAL = Gauge(
    'messages_total',
    'Total number of messages (legacy - use message_sent_total)',
    ['service']
)

# JWT and Authentication metrics
JWT_TOKENS_CREATED = Counter(
    'jwt_tokens_created_total',
    'Total JWT tokens created',
    ['service', 'token_type']
)

JWT_TOKENS_VALIDATED = Counter(
    'jwt_tokens_validated_total',
    'Total JWT token validations',
    ['service', 'result']
)

JWT_TOKENS_EXPIRED = Counter(
    'jwt_tokens_expired_total',
    'Total expired JWT tokens',
    ['service']
)

JWT_VALIDATION_FAILED = Counter(
    'jwt_validation_failed_total',
    'Failed JWT validations',
    ['service', 'reason']
)

TELEGRAM_AUTH_SUCCESS = Counter(
    'telegram_auth_success_total',
    'Successful Telegram authentications',
    ['service']
)

TELEGRAM_AUTH_FAILED = Counter(
    'telegram_auth_failed_total',
    'Failed Telegram authentications',
    ['service', 'reason']
)

# NSFW Detection metrics
NSFW_DETECTION_TOTAL = Counter(
    'nsfw_detection_total',
    'Total NSFW detections',
    ['service', 'result']
)

NSFW_BLOCKED_TOTAL = Counter(
    'nsfw_blocked_total',
    'Total NSFW blocked uploads',
    ['service']
)


def record_profile_created(service: str):
    """Record a profile creation event."""
    PROFILE_CREATED.labels(service=service).inc()


def record_profile_updated(service: str):
    """Record a profile update event."""
    PROFILE_UPDATED.labels(service=service).inc()


def record_profile_deleted(service: str):
    """Record a profile deletion event."""
    PROFILE_DELETED.labels(service=service).inc()


def record_interaction(service: str, interaction_type: str):
    """Record an interaction event (like, dislike, match)."""
    INTERACTION_CREATED.labels(service=service, type=interaction_type).inc()


def record_swipe(service: str, swipe_type: str):
    """Record a swipe event (like or dislike)."""
    SWIPES_TOTAL.labels(service=service, type=swipe_type).inc()


def record_message_sent(service: str):
    """Record a message sent event."""
    MESSAGE_SENT.labels(service=service).inc()


def record_conversation_started(service: str):
    """Record a conversation started event."""
    CONVERSATION_STARTED.labels(service=service).inc()


def update_active_users(service: str, count: int):
    """Update the number of active users."""
    USERS_ACTIVE.labels(service=service).set(count)


def update_users_by_region(service: str, region: str, count: int):
    """Update the number of users in a specific region."""
    USERS_BY_REGION.labels(service=service, region=region).set(count)


def update_matches_current(service: str, count: int):
    """Update the current number of matches."""
    MATCHES_CURRENT.labels(service=service).set(count)


def update_conversations_active(service: str, count: int):
    """Update the number of active conversations."""
    CONVERSATIONS_ACTIVE.labels(service=service).set(count)


# Legacy functions for backward compatibility
def update_users_total(service: str, count: int):
    """Update the total number of users (legacy)."""
    USERS_TOTAL.labels(service=service).set(count)


def update_matches_total(service: str, count: int):
    """Update the total number of matches (legacy)."""
    MATCHES_TOTAL.labels(service=service).set(count)


def update_messages_total(service: str, count: int):
    """Update the total number of messages (legacy)."""
    MESSAGES_TOTAL.labels(service=service).set(count)
