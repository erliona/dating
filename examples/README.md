# Examples

This directory contains example implementations demonstrating how to use Epic A and Epic B features.

## webapp_auth_handler.py

Example bot handler showing:
- WebApp button integration
- Epic A feature showcase
- Basic authentication flow

## profile_handler.py

Example bot handler showing:
- Profile creation and validation
- Photo upload and processing
- Geolocation handling
- Database integration
- Epic B feature showcase

### Running webapp_auth_handler.py

```bash
# Set environment variables
export BOT_TOKEN="your_bot_token"
export WEBAPP_URL="https://your-domain.com"
export JWT_SECRET="your_secret"

# Run the example
python -m examples.webapp_auth_handler
```

### Running profile_handler.py

```bash
# Set environment variables
export BOT_TOKEN="your_bot_token"
export BOT_DATABASE_URL="postgresql+asyncpg://user:pass@host:5432/dating"
export JWT_SECRET="your_secret"

# Run database migrations first
alembic upgrade head

# Run the example
python -m examples.profile_handler
```

## Usage in Your Bot

### Epic A: Authentication

```python
from bot.security import refresh_session, validate_jwt_token, ValidationError

# Validate initData and generate JWT
try:
    validated_data, jwt_token = refresh_session(
        init_data=init_data,
        bot_token=config.token,
        secret_key=config.jwt_secret,
        max_age_seconds=3600
    )
except ValidationError as e:
    # Handle authentication failure
    pass
```

### Epic B: Profile Management

```python
from bot.repository import ProfileRepository
from bot.validation import validate_profile_data
from bot.media import validate_and_process_photo
from bot.geo import process_location_data

# Validate and create profile
profile_data = {
    "name": "John Doe",
    "birth_date": "1990-01-01",
    "gender": "male",
    "orientation": "female",
    "goal": "relationship"
}

is_valid, error = validate_profile_data(profile_data)
if is_valid:
    async with session_maker() as session:
        repo = ProfileRepository(session)
        profile = await repo.create_profile(user_id, profile_data)
        await session.commit()

# Process photo upload
processed = validate_and_process_photo(base64_photo, user_id)
photo = await repo.add_photo(user_id, processed["url"], ...)

# Handle location
location = process_location_data(
    latitude=55.7558,
    longitude=37.6173,
    country="Russia",
    city="Moscow"
)
```

See `EPIC_A_IMPLEMENTATION.md` and `EPIC_B_IMPLEMENTATION.md` for complete documentation.
