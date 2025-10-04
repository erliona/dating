# Core Business Logic

Platform-independent business logic for the dating application.

## Overview

The `core` module contains all business logic that is completely independent of any platform (Telegram, mobile apps, web, etc.). This allows the application to be deployed on multiple platforms while maintaining consistent business rules.

## Structure

```
core/
├── models/           # Domain models
│   ├── user.py      # User, UserProfile, UserSettings
│   └── enums.py     # Gender, Orientation, Goal, Education
├── services/         # Business logic services
│   ├── user_service.py       # User management
│   ├── profile_service.py    # Profile management
│   └── matching_service.py   # Matching algorithm
├── interfaces/       # Contracts for platform adapters
│   ├── repository.py         # Data access interfaces
│   ├── notification.py       # Notification interface
│   └── storage.py           # File storage interface
└── utils/           # Utility functions
    └── validation.py # Validation helpers
```

## Principles

### 1. Platform Independence

The core module has **ZERO** dependencies on:
- Telegram (aiogram, python-telegram-bot, etc.)
- Mobile SDKs (iOS, Android)
- Web frameworks (Django, FastAPI, etc.)
- Any platform-specific libraries

This is enforced by tests and code reviews.

### 2. Pure Business Logic

All business rules are implemented in core services:
- Age validation (18+ requirement)
- Photo limits (max 6 photos)
- Matching algorithm
- Compatibility scoring
- User banning/unbanning

### 3. Interface-Based Design

Core services depend on **interfaces**, not implementations:
```python
class ProfileService:
    def __init__(self, profile_repository: IProfileRepository):
        # Depends on interface, not concrete implementation
        self.profile_repository = profile_repository
```

Platform adapters implement these interfaces:
- `TelegramProfileRepository` (for Telegram)
- `MobileProfileRepository` (for iOS/Android)
- `WebProfileRepository` (for web)

## Usage

### Creating Services

```python
from core.services import UserService, ProfileService
from adapters.telegram import TelegramUserRepository, TelegramProfileRepository

# Platform adapter (Telegram)
user_repo = TelegramUserRepository(session)
profile_repo = TelegramProfileRepository(session)

# Core services (platform-independent)
user_service = UserService(user_repo)
profile_service = ProfileService(profile_repo)
```

### Creating a Profile

```python
from datetime import date
from core.models.enums import Gender, Orientation

profile = await profile_service.create_profile(
    user_id=123,
    name="John Doe",
    birth_date=date(1990, 1, 1),
    gender=Gender.MALE,
    orientation=Orientation.FEMALE,
    city="Moscow",
    bio="Love traveling and music"
)
```

### Matching Profiles

```python
from core.services import MatchingService

matching_service = MatchingService(profile_repo)

# Get recommendations
settings = await settings_service.get_settings(user_id)
recommendations = await matching_service.get_recommendations(
    user_id=user_id,
    settings=settings,
    limit=10
)

# Calculate compatibility
score = matching_service.calculate_compatibility_score(
    profile1, profile2
)
```

## Models

### User
Basic user entity (platform-agnostic):
- `id`: Internal user ID
- `username`: Optional username
- `first_name`: First name
- `is_premium`: Premium status
- `is_banned`: Ban status

### UserProfile
Complete dating profile:
- Personal info (name, birth_date, gender, city)
- Bio and interests
- Photos (list of URLs)
- Location (geohash for privacy)
- Education and work
- Preferences (orientation, goal)

### UserSettings
User preferences for discovery:
- Age range (min_age, max_age)
- Distance (max_distance)
- Gender preference (show_me)
- Privacy settings
- Notification preferences

## Services

### UserService
User account management:
- `create_user()` - Create new user
- `ban_user()` - Ban user
- `unban_user()` - Unban user
- `update_user()` - Update user info
- `delete_user()` - Delete user account

### ProfileService
Profile management:
- `create_profile()` - Create dating profile
- `update_profile()` - Update profile info
- `add_photo()` - Add photo (max 6)
- `remove_photo()` - Remove photo
- `set_visibility()` - Show/hide profile
- `delete_profile()` - Delete profile

### MatchingService
Matching algorithm:
- `get_recommendations()` - Get candidate profiles
- `calculate_compatibility_score()` - Score compatibility (0-100)
- `apply_filters()` - Filter by age, distance, gender

## Interfaces

### IUserRepository
Data access for users:
- `get_user(user_id)` - Get user by ID
- `create_user(user)` - Create user
- `update_user(user)` - Update user
- `delete_user(user_id)` - Delete user

### IProfileRepository
Data access for profiles:
- `get_profile(user_id)` - Get profile
- `create_profile(profile)` - Create profile
- `update_profile(profile)` - Update profile
- `delete_profile(user_id)` - Delete profile
- `search_profiles(...)` - Search candidates

### INotificationService
Send notifications to users:
- `send_notification(user_id, type, data)` - Send notification
- `send_batch_notifications(...)` - Send to multiple users

### IStorageService
File storage operations:
- `store_file(...)` - Store file
- `get_file_url(path)` - Get file URL
- `delete_file(path)` - Delete file
- `file_exists(path)` - Check existence

## Testing

All core logic is thoroughly tested:

```bash
# Run core tests
pytest tests/core/

# Run with coverage
pytest tests/core/ --cov=core --cov-report=html
```

Tests use mock repositories, ensuring platform independence.

## Adding New Features

When adding new features:

1. **Add domain models** to `core/models/`
2. **Add business logic** to `core/services/`
3. **Define interfaces** in `core/interfaces/` if needed
4. **Write tests** in `tests/core/`
5. **Implement adapters** in `adapters/` for each platform

**Rule**: Core code should never import from `bot/`, `adapters/`, or any platform-specific module.

## Migration from Legacy Code

When migrating code from `bot/` to `core/`:

1. ✅ Remove Telegram-specific dependencies
2. ✅ Extract business logic to services
3. ✅ Define interfaces for external dependencies
4. ✅ Update adapters to implement interfaces
5. ✅ Add tests for new core code

## Benefits

### 1. Multi-Platform Support
- ✅ Telegram Mini App (via adapter)
- 📋 iOS/Android apps (future)
- 📋 Web application (future)
- 📋 Desktop apps (future)

All using the same business logic!

### 2. Better Testing
- Unit tests for business logic (no mocking platform SDKs)
- Integration tests for adapters
- E2E tests for complete flows

### 3. Easier Maintenance
- Business logic in one place
- Platform changes don't affect core
- Clear separation of concerns

### 4. Team Scaling
- Core team works on business logic
- Platform teams work on adapters
- Clear interfaces between teams

## Documentation

- [Architecture Overview](../docs/ARCHITECTURE.md)
- [Migration Guide](../docs/ARCHITECTURE_MIGRATION_GUIDE.md)
- [Project Status](../PROJECT_STATUS.md)

## Support

Questions? Check:
1. This README
2. Code examples in services
3. Tests in `tests/core/`
4. Create GitHub issue

---

**Version**: 1.0.0  
**Status**: Production Ready  
**Last Updated**: 2024-01-10
