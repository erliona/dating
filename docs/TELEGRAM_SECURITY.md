# Telegram Security Implementation

## Overview

This document describes the security measures implemented to protect the Telegram Mini App from unauthorized access and forged requests.

## Security Layers

### 1. Origin Validation

**Purpose**: Ensure requests come only from Telegram WebApp.

**Implementation**:
```python
def validate_telegram_origin(request: web.Request) -> bool:
    origin = request.headers.get('Origin', '')
    referer = request.headers.get('Referer', '')
    user_agent = request.headers.get('User-Agent', '')
    
    # Check Origin header
    if not origin.startswith('https://web.telegram.org'):
        return False
    
    # Check User-Agent (should contain TelegramBot)
    if 'TelegramBot' not in user_agent:
        return False
    
    return True
```

**Validates**:
- ✅ Origin header: `https://web.telegram.org`
- ✅ Referer header: `https://web.telegram.org` (optional)
- ✅ User-Agent: Contains `TelegramBot`

### 2. Bot Secret Token Validation

**Purpose**: Verify request authenticity using Telegram's secret token.

**Implementation**:
```python
def validate_telegram_bot_secret(request: web.Request) -> bool:
    secret_token = request.headers.get('X-Telegram-Bot-Api-Secret-Token')
    expected_secret = os.getenv('TELEGRAM_BOT_SECRET_TOKEN')
    
    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(secret_token, expected_secret)
```

**Security Features**:
- ✅ Constant-time comparison (prevents timing attacks)
- ✅ Environment variable configuration
- ✅ Required header validation

### 3. Middleware Integration

**Applied to**: All `/auth/*` endpoints

**Order**:
1. Standard middleware stack
2. Rate limiting
3. **Telegram security validation**
4. Business logic

## Configuration

### 1. Generate Secret Token

```bash
# Generate new secret token
python3 scripts/generate-telegram-secret.py

# Output:
# TELEGRAM_BOT_SECRET_TOKEN=abc123...
```

### 2. Configure BotFather

```bash
# Set domain and secret token
/setdomain
# Select your bot
# Domain: dating.serge.cc
# Secret token: abc123...
```

### 3. Environment Variables

```bash
# .env file
TELEGRAM_BOT_SECRET_TOKEN=abc123...
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz-1234567
```

## Security Benefits

### 1. Origin Protection
- **Prevents**: Direct API access from browsers
- **Blocks**: Cross-origin attacks
- **Ensures**: Requests only from Telegram WebApp

### 2. Bot Authentication
- **Prevents**: Forged requests without bot token
- **Blocks**: Unauthorized API access
- **Ensures**: Only authenticated Telegram bots

### 3. Timing Attack Protection
- **Uses**: `hmac.compare_digest()` for constant-time comparison
- **Prevents**: Secret token extraction via timing analysis

## Testing

### 1. Valid Request (Should Pass)
```bash
curl -X POST https://dating.serge.cc/v1/auth/validate \
  -H "Origin: https://web.telegram.org" \
  -H "User-Agent: TelegramBot/1.0" \
  -H "X-Telegram-Bot-Api-Secret-Token: abc123..." \
  -H "Content-Type: application/json" \
  -d '{"init_data": "valid_telegram_data"}'
```

### 2. Invalid Origin (Should Fail)
```bash
curl -X POST https://dating.serge.cc/v1/auth/validate \
  -H "Origin: https://evil.com" \
  -H "User-Agent: TelegramBot/1.0" \
  -H "X-Telegram-Bot-Api-Secret-Token: abc123..." \
  -H "Content-Type: application/json" \
  -d '{"init_data": "valid_telegram_data"}'
# Response: 403 Forbidden
```

### 3. Invalid Secret Token (Should Fail)
```bash
curl -X POST https://dating.serge.cc/v1/auth/validate \
  -H "Origin: https://web.telegram.org" \
  -H "User-Agent: TelegramBot/1.0" \
  -H "X-Telegram-Bot-Api-Secret-Token: wrong_token" \
  -H "Content-Type: application/json" \
  -d '{"init_data": "valid_telegram_data"}'
# Response: 403 Forbidden
```

## Monitoring

### Security Metrics
- `telegram_origin_validations`: Successful origin validations
- `telegram_origin_failures`: Failed origin validations
- `telegram_bot_secret_validations`: Successful secret validations
- `telegram_bot_secret_failures`: Failed secret validations

### Logging
```json
{
  "event_type": "telegram_security_failure",
  "remote_addr": "192.168.1.1",
  "path": "/auth/validate",
  "origin": "https://evil.com",
  "user_agent": "Mozilla/5.0...",
  "secret_token_present": true
}
```

## Error Responses

### Invalid Origin
```json
{
  "error": "Invalid origin",
  "code": "INVALID_ORIGIN"
}
```

### Invalid Bot Secret
```json
{
  "error": "Invalid bot secret", 
  "code": "INVALID_BOT_SECRET"
}
```

### Security Error
```json
{
  "error": "Security validation failed",
  "code": "SECURITY_ERROR"
}
```

## Best Practices

1. **Rotate Secret Token**: Change `TELEGRAM_BOT_SECRET_TOKEN` regularly
2. **Monitor Failures**: Alert on high failure rates
3. **Log Security Events**: Track all security violations
4. **Test Regularly**: Verify security measures work
5. **Keep Updated**: Update Telegram SDK and security measures

## Troubleshooting

### Common Issues

1. **403 Forbidden**: Check Origin header and secret token
2. **Missing Headers**: Ensure Telegram WebApp sends all required headers
3. **Environment Variables**: Verify `TELEGRAM_BOT_SECRET_TOKEN` is set
4. **BotFather Configuration**: Ensure domain and secret are configured correctly

### Debug Mode
```python
# Enable debug logging
import logging
logging.getLogger('core.middleware.telegram_security').setLevel(logging.DEBUG)
```
