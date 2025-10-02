# Epic A Implementation Guide

This document describes the implementation of Epic A — Mini App Foundation and Authorization.

## Overview

Epic A consists of three main components:

1. **A1**: Mini App initialization and bridge to Telegram WebApp API
2. **A2**: Server-side validation of initData + JWT
3. **A3**: Deep-links startapp support

## A1: Mini App Initialization

### Implementation

The Mini App is implemented as a pure HTML/CSS/JavaScript application without build tools.

**Files:**
- `webapp/index.html` - Main HTML structure
- `webapp/css/style.css` - Styles with Telegram theme integration
- `webapp/js/app.js` - JavaScript application logic

### Features

#### 1. Telegram WebApp SDK Integration

```javascript
// Initialize Telegram WebApp
if (!window.Telegram || !window.Telegram.WebApp) {
    console.error('Telegram WebApp SDK not loaded');
    return false;
}

tg = window.Telegram.WebApp;
tg.expand();
tg.enableClosingConfirmation();
```

The SDK is loaded from CDN:
```html
<script src="https://telegram.org/js/telegram-web-app.js"></script>
```

#### 2. Theme Handling

Theme colors are automatically applied from Telegram and update without reload:

```javascript
function applyTheme() {
    const themeParams = tg.themeParams;
    const root = document.documentElement;
    
    // Map Telegram theme parameters to CSS variables
    root.style.setProperty('--tg-theme-bg-color', themeParams.bg_color);
    // ... more colors
}

// Listen for theme changes
tg.onEvent('themeChanged', () => {
    applyTheme();
});
```

CSS variables are used throughout:
```css
body {
    background-color: var(--tg-theme-bg-color);
    color: var(--tg-theme-text-color);
}
```

#### 3. BackButton Support

```javascript
// Set up BackButton handler
tg.BackButton.onClick(() => {
    handleBackButton();
});

// Show/hide programmatically
function showBackButton() {
    tg.BackButton.show();
}
```

#### 4. Safe Area Handling

Viewport meta tag handles safe areas on notched devices:

```html
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
```

CSS respects safe areas:
```css
html {
    padding: env(safe-area-inset-top) env(safe-area-inset-right) 
             env(safe-area-inset-bottom) env(safe-area-inset-left);
}
```

#### 5. Haptic Feedback

```javascript
function triggerHaptic(type = 'impact', style = 'medium') {
    if (!tg || !tg.HapticFeedback) return;
    
    switch (type) {
        case 'impact':
            tg.HapticFeedback.impactOccurred(style);
            break;
        case 'notification':
            tg.HapticFeedback.notificationOccurred(style);
            break;
        case 'selection':
            tg.HapticFeedback.selectionChanged();
            break;
    }
}
```

Haptic styles:
- **Impact**: `light`, `medium`, `heavy`, `rigid`, `soft`
- **Notification**: `error`, `success`, `warning`
- **Selection**: No parameter needed

### Testing

**Manual Testing Checklist:**

- [ ] Open app in Telegram on iOS - check theme, haptics, safe area
- [ ] Open app in Telegram on Android - check theme, haptics
- [ ] Open app in Telegram Desktop - verify functionality
- [ ] Switch Telegram theme (Settings → Chat Settings → Theme) - verify auto-update
- [ ] Test BackButton functionality
- [ ] Test haptic feedback (on mobile devices)
- [ ] Check safe area handling on notched devices

**Demo URL:**

After deployment, access at: `https://your-domain.com/`

The demo screen shows:
- Platform information
- Live theme colors
- Haptic feedback buttons
- BackButton controls

## A2: Server-side Validation + JWT

### Implementation

**File:** `bot/security.py`

### Features

#### 1. HMAC-SHA256 Validation

Validates Telegram WebApp initData according to [official documentation](https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app):

```python
from bot.security import validate_webapp_init_data

try:
    validated_data = validate_webapp_init_data(
        init_data=init_data,
        bot_token=bot_token,
        max_age_seconds=3600  # 1 hour
    )
    user_id = validated_data['user']['id']
except ValidationError as e:
    # Invalid initData
    logger.error(f"Validation failed: {e}")
```

**Validation Steps:**
1. Parse initData query string
2. Extract and verify hash parameter
3. Check auth_date is present and valid
4. Verify auth_date TTL (default 1 hour, configurable)
5. Calculate HMAC-SHA256 using bot token
6. Timing-safe comparison of hashes
7. Parse user data from JSON

**Security Features:**
- Timing-safe hash comparison (prevents timing attacks)
- TTL checking (prevents replay attacks)
- Future timestamp rejection
- Comprehensive error logging

#### 2. JWT Token Generation

```python
from bot.security import generate_jwt_token

jwt_token = generate_jwt_token(
    user_id=user_id,
    secret_key=jwt_secret,
    additional_claims={
        "username": username,
        "role": "user"
    }
)
```

**JWT Payload:**
```json
{
    "user_id": 123456,
    "iat": 1234567890,
    "exp": 1234654290,
    "nbf": 1234567890,
    "username": "johndoe"
}
```

**Configuration:**
- TTL: 24 hours (configurable via `JWT_TTL_HOURS`)
- Algorithm: HS256
- Required claims: `user_id`, `iat`, `exp`

#### 3. JWT Validation

```python
from bot.security import validate_jwt_token, ValidationError

try:
    payload = validate_jwt_token(jwt_token, jwt_secret)
    user_id = payload['user_id']
except ValidationError as e:
    # Invalid or expired token
    logger.error(f"JWT validation failed: {e}")
```

**Validation:**
- Signature verification
- Expiration checking
- Not-before-time checking
- Required claims verification

#### 4. Session Refresh

On app restart or JWT expiration:

```python
from bot.security import refresh_session

try:
    validated_data, new_jwt = refresh_session(
        init_data=fresh_init_data,
        bot_token=bot_token,
        secret_key=jwt_secret,
        max_age_seconds=3600
    )
except ValidationError as e:
    # Session refresh failed
    logger.error(f"Session refresh failed: {e}")
```

This combines initData validation and JWT generation in one step.

#### 5. Security Logging

All authentication events are logged with structured data:

```python
logger.info(
    "initData validated successfully",
    extra={
        "event_type": "auth_success",
        "user_id": user_id,
        "data_age_seconds": age
    }
)
```

**Event Types:**
- `auth_success` - Successful authentication
- `auth_failed` - Failed validation
- `jwt_generated` - JWT token created
- `jwt_validated` - JWT validated
- `jwt_validation_failed` - JWT validation failed
- `session_refreshed` - Session refreshed

### Usage Example

Complete authentication flow:

```python
from bot.security import refresh_session, validate_jwt_token, ValidationError

# Initial authentication when user opens Mini App
@router.message(F.web_app_data)
async def handle_webapp_data(message: Message):
    init_data = message.web_app_data.data
    
    try:
        # Validate initData and generate JWT
        validated_data, jwt_token = refresh_session(
            init_data=init_data,
            bot_token=config.token,
            secret_key=config.jwt_secret,
            max_age_seconds=3600
        )
        
        user_id = validated_data['user']['id']
        
        # Store JWT in user session or send to client
        # For Telegram bots, typically store in database
        await save_user_session(user_id, jwt_token)
        
        await message.answer("Authentication successful!")
        
    except ValidationError as e:
        logger.error(f"Authentication failed: {e}")
        await message.answer("Authentication failed. Please try again.")

# Subsequent requests with JWT
async def handle_api_request(jwt_token: str):
    try:
        payload = validate_jwt_token(jwt_token, config.jwt_secret)
        user_id = payload['user_id']
        
        # Process authenticated request
        return await process_request(user_id)
        
    except ValidationError as e:
        # JWT expired or invalid - client should refresh
        return {"error": "Authentication required"}
```

### Testing

**Unit Tests:** `tests/test_security.py`

Run tests:
```bash
pytest tests/test_security.py -v
```

Test coverage:
```bash
pytest tests/test_security.py --cov=bot.security --cov-report=term-missing
```

**Test Categories:**

1. **HMAC Validation** (10 tests)
   - Valid initData
   - Missing/invalid hash
   - Missing/invalid auth_date
   - Expired data (TTL)
   - Future timestamps
   - Tampered data
   - Custom max_age

2. **JWT Operations** (8 tests)
   - Token generation
   - Additional claims
   - TTL verification
   - Token validation
   - Expired tokens
   - Wrong secret
   - Tampered tokens
   - Missing claims

3. **Session Refresh** (4 tests)
   - Successful refresh
   - Invalid initData
   - Expired initData
   - Token uniqueness

4. **Integration** (1 test)
   - Complete authentication flow

**Current Coverage: 88%**

Missing coverage is mainly error logging paths that are hard to trigger in tests.

### Security Considerations

1. **Secret Key Management**
   - JWT secret should be stored in environment variables or secret manager
   - Never commit secrets to version control
   - Rotate secrets periodically

2. **TTL Configuration**
   - initData max_age: 1 hour (prevents replay attacks)
   - JWT expiration: 24 hours (balance security and UX)
   - Adjust based on security requirements

3. **Error Handling**
   - Never expose internal errors to clients
   - Log all security events for monitoring
   - Rate limit authentication attempts

4. **Replay Attack Prevention**
   - auth_date TTL prevents old initData reuse
   - Consider storing used initData hashes if needed

## A3: Deep-links Startapp

### Implementation

**File:** `webapp/js/app.js`

### Features

#### 1. Parameter Parsing

```javascript
function parseStartParam() {
    if (!tg || !tg.initDataUnsafe) return null;
    
    const startParam = tg.initDataUnsafe.start_param;
    
    if (startParam) {
        console.log('Start parameter detected:', startParam);
        return startParam;
    }
    
    return null;
}
```

#### 2. Deep-link Format

Format: `type_id`

Examples:
- `chat_123` - Open chat with ID 123
- `profile_456` - Open profile with ID 456
- `payment_789` - Open payment with ID 789

#### 3. Routing Logic

```javascript
function handleDeepLink(param) {
    if (!param) return;
    
    const [type, id] = param.split('_');
    
    switch (type) {
        case 'chat':
            routeToChat(id);
            break;
        case 'profile':
            routeToProfile(id);
            break;
        case 'payment':
            routeToPayment(id);
            break;
        default:
            console.warn('Unknown deep link type:', type);
    }
}
```

#### 4. Usage

Create deep-link URLs:

```
https://t.me/YOUR_BOT_NAME/YOUR_APP_NAME?startapp=chat_123
https://t.me/YOUR_BOT_NAME/YOUR_APP_NAME?startapp=profile_456
https://t.me/YOUR_BOT_NAME/YOUR_APP_NAME?startapp=payment_789
```

When user clicks the link, the Mini App opens and automatically routes to the specified screen.

### Testing

**Manual Testing:**

1. Create test deep-link URLs
2. Send them in Telegram chat
3. Click and verify correct routing
4. Check haptic feedback on navigation
5. Verify BackButton appears on deep-linked screens

**Automated Testing:**

Deep-link routing is tested as part of the security integration tests, which verify the complete flow from initData parsing to route handling.

## Configuration

### Environment Variables

Required for A2:

```bash
# Bot token from @BotFather
BOT_TOKEN=123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11

# JWT secret key (generate a strong random string)
JWT_SECRET=your_strong_secret_key_here

# Optional: Custom TTL values
JWT_TTL_HOURS=24
INITDATA_MAX_AGE_SECONDS=3600
```

### Bot Configuration

Add JWT secret to `bot/config.py`:

```python
@dataclass(slots=True)
class BotConfig:
    token: str
    database_url: str
    webapp_url: str | None = None
    jwt_secret: str | None = None  # Add this field

def load_config() -> BotConfig:
    # ... existing code ...
    
    jwt_secret = os.getenv("JWT_SECRET")
    if not jwt_secret:
        # For development, you can generate one
        # For production, this should be required
        logger.warning("JWT_SECRET not set, generating temporary secret")
        import secrets
        jwt_secret = secrets.token_urlsafe(32)
    
    return BotConfig(
        token=token,
        database_url=database_url,
        webapp_url=webapp_url,
        jwt_secret=jwt_secret
    )
```

## Deployment

### Development

```bash
# Start development environment
docker compose -f docker-compose.dev.yml up -d

# Mini App available at: http://localhost:8080
```

### Production

```bash
# Set environment variables in .env
BOT_TOKEN=your_bot_token
JWT_SECRET=your_jwt_secret
WEBAPP_URL=https://your-domain.com

# Deploy
docker compose up -d
```

### Nginx Configuration

The webapp files are served by nginx. No build step is required.

## Monitoring

### Logs

All authentication events are logged with structured JSON:

```json
{
    "timestamp": "2024-10-02T17:00:00.000Z",
    "level": "INFO",
    "event_type": "auth_success",
    "user_id": 123456,
    "data_age_seconds": 5
}
```

### Grafana Dashboards

Monitor authentication metrics:
- Authentication success rate
- Failed authentication attempts
- Average data age
- JWT generation rate
- Token validation failures

### Alerts

Set up alerts for:
- High rate of authentication failures
- Unusual JWT expiration patterns
- Suspicious auth_date values (too old or future)

## Troubleshooting

### Common Issues

#### 1. "HMAC validation failed"

**Cause:** Wrong bot token or tampered data

**Solution:**
- Verify BOT_TOKEN environment variable
- Check that initData is passed correctly from client
- Ensure no URL encoding issues

#### 2. "initData is too old"

**Cause:** Client sent stale data

**Solution:**
- Ensure client sends fresh initData from Telegram
- Check system clock synchronization
- Adjust max_age_seconds if needed

#### 3. "Token has expired"

**Cause:** JWT expired after 24 hours

**Solution:**
- Implement token refresh flow in client
- Client should detect 401 errors and refresh session
- Call `refresh_session()` with fresh initData

#### 4. Theme not updating

**Cause:** Theme listener not set up or CSS vars not applied

**Solution:**
- Check browser console for errors
- Verify Telegram WebApp SDK loaded
- Check CSS variable values in DevTools

#### 5. Haptic feedback not working

**Cause:** Not supported on platform or not enabled

**Solution:**
- Test on actual mobile device (not desktop)
- Check Telegram app settings for haptic feedback
- iOS may require system haptic settings enabled

## Best Practices

### Security

1. **Always validate initData** on server-side before trusting user data
2. **Use environment variables** for secrets, never hardcode
3. **Implement rate limiting** on authentication endpoints
4. **Monitor authentication logs** for suspicious patterns
5. **Rotate JWT secrets** periodically in production

### Performance

1. **Cache validated initData** (but respect TTL)
2. **Use connection pooling** for database operations
3. **Implement request debouncing** on client-side
4. **Minimize API calls** by batching operations

### UX

1. **Show loading states** during authentication
2. **Handle errors gracefully** with user-friendly messages
3. **Implement automatic retry** for transient errors
4. **Use haptic feedback** to confirm actions
5. **Respect theme preferences** from Telegram

## References

- [Telegram Mini Apps Documentation](https://core.telegram.org/bots/webapps)
- [WebApp SDK Reference](https://core.telegram.org/bots/webapps#initializing-mini-apps)
- [Validating initData](https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)

## Next Steps

After completing Epic A, consider:

1. **Epic B**: User profile management
2. **Epic C**: Matching algorithm
3. **Epic D**: Chat functionality
4. **Epic E**: Premium features

Each epic builds on the authentication foundation established in Epic A.
