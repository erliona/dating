# Examples

This directory contains example implementations demonstrating how to use Epic A features.

## webapp_auth_handler.py

Example bot handler showing:
- WebApp button integration
- Epic A feature showcase
- Basic authentication flow

### Running the Example

```bash
# Set environment variables
export BOT_TOKEN="your_bot_token"
export WEBAPP_URL="https://your-domain.com"
export JWT_SECRET="your_secret"

# Run the example
python -m examples.webapp_auth_handler
```

## Usage in Your Bot

Copy the patterns from these examples into your own bot handlers:

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

See `docs/EPIC_A_IMPLEMENTATION.md` for complete documentation.
