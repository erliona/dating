# Security Documentation

## Overview

This document describes the security measures implemented in the Dating Bot application.

## Security Enhancements (Sprint 3, Task 1)

### 1. Dependency Security Audit

#### Automated Security Scanning
- **pip-audit** has been integrated for continuous dependency vulnerability scanning
- Security scans are run automatically in CI/CD pipeline (`.github/workflows/ci.yml`)
- Current dependencies are clean with no known vulnerabilities

#### Dependency Management
- All dependencies use specific version ranges to avoid unexpected updates
- `python-dotenv>=1.0` added for secure environment variable loading
- Regular security audits should be performed using:
  ```bash
  pip-audit -r requirements.txt -r requirements-dev.txt
  ```

#### Update Policy
- Dependencies should be reviewed and updated quarterly
- Security patches should be applied immediately when available
- Breaking changes should be tested thoroughly before deployment

### 2. API Protection Measures

#### Rate Limiting
The application includes rate limiting to prevent abuse and DoS attacks:

- **Configuration**: 20 requests per user per 60 seconds (configurable)
- **Implementation**: In-memory rate limiter with automatic TTL-based cleanup
- **Location**: `bot/security.py` - `RateLimiter` class
- **Applied to**: All authenticated API endpoints
- **Response**: Returns HTTP 429 (Too Many Requests) when limit exceeded

The rate limiter automatically cleans up expired entries every 60 seconds to prevent memory leaks.

Example usage:
```python
from bot.security import RateLimiter

# Initialize rate limiter
rate_limiter = RateLimiter(
    max_requests=20,  # Maximum requests per window
    window_seconds=60  # Time window in seconds
)

# Check if request is allowed
if rate_limiter.is_allowed(user_id):
    # Process request
    pass
else:
    # Return 429 error
    pass
```

#### Input Validation and Sanitization
All user input is validated and sanitized before processing:

**Profile Data Validation** (`validate_profile_data`):
- Required fields: name, age, gender, preference
- Age range: 18-120 years
- Name length: 2-100 characters
- Bio length: max 1000 characters
- Location length: max 200 characters
- Interests: max 20 items, each max 50 characters
- Valid gender values: male, female, other
- Valid preference values: male, female, any
- Valid goal values: friendship, dating, relationship, networking, serious, casual, friends, fun

**Input Sanitization** (`sanitize_user_input`):
- Removes null bytes and control characters
- Preserves printable text and newlines/tabs
- Truncates to maximum length (configurable, default 10000 chars)
- Strips leading/trailing whitespace

#### Request Size Limits
- JSON payload size is limited by Telegram's WebApp API
- Individual text fields have explicit length limits (see validation above)

### 3. Authentication System Improvements

#### Telegram WebApp Data Validation
Enhanced authentication using Telegram's official validation algorithm:

**Implementation** (`validate_webapp_data`):
- Validates HMAC-SHA256 signature from Telegram
- Checks data freshness (default: 1 hour max age)
- Verifies auth_date timestamp
- Parses and validates user data
- Implements timing-safe comparison for hash validation

**Security Features**:
- Uses `hmac.compare_digest()` to prevent timing attacks
- Validates data age to prevent replay attacks
- Proper error handling without exposing internals
- Comprehensive logging for security events

#### JWT Token Validation
Enhanced JWT token validation in `bot/api.py`:

- **Format validation**: Authorization header must start with "Bearer "
- **Empty token detection**: Rejects empty tokens after "Bearer " prefix
- **Whitespace handling**: Strips whitespace from tokens
- **Expiration check**: Validates JWT expiration time
- **Suspicious activity logging**: Logs all authentication failures with IP and endpoint

#### Bot Token Validation
Enhanced token validation in `bot/config.py`:

- Format validation: must match `<numeric_id>:<alphanumeric_hash>` pattern
- Placeholder detection: rejects common placeholder values
- Whitespace handling: strips and validates non-empty tokens
- Clear error messages for configuration issues

#### Session Management
- Uses aiogram's built-in session management with MemoryStorage
- Rate limiting provides basic session protection
- All authentication events are logged for audit purposes

### 4. Security Logging and Suspicious Activity Detection

Enhanced security logging throughout the application with automatic detection of suspicious patterns:

**Logged Events**:
- Rate limit violations (WARNING level) - includes user_id, IP, and endpoint
- Authentication failures (WARNING level) - includes reason (missing_header, invalid_format, empty_token, invalid_token)
- WebApp data validation failures (WARNING level)
- Profile validation errors (WARNING level)
- Database connection errors (ERROR level)
- Unexpected exceptions (EXCEPTION level with stack traces)

**Suspicious Activity Detection**:
- Multiple authentication failures from same IP
- Empty or malformed Authorization headers
- Rate limit exceeded events
- All security events include:
  - Event type for easy filtering
  - User ID (when available)
  - IP address (when available)
  - Endpoint path
  - Timestamp (automatic via logging)

**Log Format**:
```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

**Sensitive Data Protection**:
- Passwords masked in database URLs
- Bot tokens never logged in full
- User IDs logged for audit but no personal data

### 5. Database Security

#### Connection Security
- Uses PostgreSQL with asyncpg driver over SSL-capable connections
- Connection strings support URL encoding for special characters
- Database credentials stored in environment variables only
- Password masking in logs and debug output

#### Input Validation
- All user inputs sanitized before database operations
- SQLAlchemy ORM prevents SQL injection
- Parameterized queries used throughout

#### Migration Security
- Alembic migrations version controlled
- Migration safety checks before deployment
- Database backups recommended before major updates

### 7. Memory Leak Prevention

#### Cache TTL Management
The in-memory cache system includes automatic TTL-based cleanup:

- **Auto-cleanup**: Runs every 5 minutes during cache access
- **TTL enforcement**: All cached items have time-to-live
- **Default TTL**: 5 minutes (300 seconds)
- **Manual cleanup**: `cleanup_expired()` method available
- **Statistics tracking**: Monitor cache size and hit rates

```python
from bot.cache import get_cache

cache = get_cache()
cache.set("key", "value", ttl=300)  # 5 minute TTL
value = cache.get("key")  # Auto-cleanup runs periodically
```

#### Rate Limiter Cleanup
The rate limiter includes automatic cleanup of expired request history:

- **Auto-cleanup**: Runs every 60 seconds during rate limit checks
- **Window-based**: Only keeps requests within the time window
- **Memory efficient**: Removes empty user entries automatically

#### Session Management
- JWT tokens have 24-hour expiration
- No indefinite sessions stored in memory
- Token validation includes expiration checks

### 6. HTTPS and Transport Security

#### Production Requirements
- WEBAPP_URL must use HTTPS (enforced in config validation)
- Localhost/127.0.0.1 allowed HTTP for development only
- Traefik configured for automatic Let's Encrypt SSL certificates
- HTTP automatically redirects to HTTPS in production

#### Certificate Management
- Automatic renewal via Traefik
- ACME email required for certificate notifications
- Staging environment available for testing

## Security Best Practices

### For Developers

1. **Never commit secrets**:
   - Use `.env` files (excluded in `.gitignore`)
   - Never hardcode credentials in source code
   - Use environment variables for all sensitive data

2. **Input validation**:
   - Always validate user input using `validate_profile_data()`
   - Sanitize text inputs using `sanitize_user_input()`
   - Check for SQL injection risks in raw queries

3. **Error handling**:
   - Don't expose internal errors to users
   - Log detailed errors for debugging
   - Return generic error messages to users

4. **Dependencies**:
   - Run `pip-audit` before deploying
   - Review dependency updates for security patches
   - Test thoroughly after dependency updates

### For Operations

1. **Environment configuration**:
   - Use strong, randomly generated passwords
   - Rotate credentials periodically
   - Use alphanumeric passwords to avoid URL encoding issues

2. **Monitoring**:
   - Review logs regularly for security events
   - Monitor rate limit violations
   - Check for unusual authentication patterns

3. **Backups**:
   - Regular database backups
   - Test backup restoration procedures
   - Secure backup storage

4. **Updates**:
   - Keep Docker images updated
   - Apply security patches promptly
   - Test updates in staging before production

## Testing Security Features

Run security tests:
```bash
pytest tests/test_security.py -v
```

Run all tests including security:
```bash
pytest -v --tb=short
```

Test rate limiting manually:
```python
from bot.security import RateLimiter, RateLimitConfig

config = RateLimitConfig(max_requests=3, window_seconds=60)
limiter = RateLimiter(config)

user_id = 12345
print(limiter.is_allowed(user_id))  # Should return True
print(limiter.get_remaining_requests(user_id))  # Should return 2
```

## Incident Response

If a security issue is discovered:

1. **Immediate action**:
   - Document the issue (time, impact, affected users)
   - If active attack: consider rate limiting or temporary shutdown
   - Preserve logs for analysis

2. **Investigation**:
   - Check logs for suspicious activity
   - Identify affected users and data
   - Determine root cause

3. **Remediation**:
   - Apply security patch
   - Update dependencies if needed
   - Test thoroughly

4. **Post-incident**:
   - Document lessons learned
   - Update security procedures
   - Consider additional monitoring

## Security Checklist for Deployment

- [ ] All dependencies scanned with `pip-audit`
- [ ] Environment variables configured (not defaults)
- [ ] HTTPS enabled with valid certificate
- [ ] Database password is strong and alphanumeric
- [ ] Bot token validated and not a placeholder
- [ ] Logs configured and monitored
- [ ] Rate limiting enabled
- [ ] Backups configured
- [ ] Security tests passing
- [ ] README security documentation reviewed

## Contact

For security concerns or to report vulnerabilities, please contact the repository maintainers.

---

**Last Updated**: 2024-12-01  
**Version**: 1.0.0  
**Related Sprint**: Sprint 3, Task 1
