# 🔒 Критические исправления безопасности

## 1. Удалить хардкод паролей

### services/admin/main.py
```python
# ❌ УДАЛИТЬ ЭТО:
if username == "admin" and password == "admin123":

# ✅ ЗАМЕНИТЬ НА:
# Получить админа из базы через Data Service
admin_data = await get_admin_by_username(username)
if admin_data and verify_password(password, admin_data['password_hash']):
```

## 2. Усилить JWT секреты

### .env файл
```bash
# ❌ НЕ ИСПОЛЬЗОВАТЬ:
JWT_SECRET=your-secret-key

# ✅ ИСПОЛЬЗОВАТЬ:
JWT_SECRET=$(openssl rand -base64 64)
```

## 3. Добавить валидацию входных данных

### services/auth/main.py
```python
# Добавить rate limiting
from aiohttp_ratelimit import RateLimiter

@RateLimiter(requests=5, window=60)  # 5 запросов в минуту
async def validate_telegram_init_data(request):
    # существующий код
```

## 4. Улучшить хеширование паролей

### services/admin/main.py
```python
import bcrypt

def hash_password(password: str) -> str:
    """Hash password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt).decode()

def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against bcrypt hash."""
    return bcrypt.checkpw(password.encode(), password_hash.encode())
```

## 5. Добавить CORS политики

### services/auth/main.py
```python
from aiohttp_cors import setup as cors_setup, ResourceOptions

# Настроить CORS
cors = cors_setup(app, defaults={
    "*": ResourceOptions(
        allow_credentials=True,
        expose_headers="*",
        allow_headers="*",
        allow_methods="*"
    )
})
```

## 6. Добавить валидацию токенов

### services/auth/main.py
```python
def validate_jwt_token(token: str, secret: str) -> dict:
    """Validate JWT token with additional security checks."""
    try:
        payload = jwt.decode(token, secret, algorithms=["HS256"])
        
        # Проверить срок действия
        if payload.get('exp', 0) < time.time():
            raise ValidationError("Token expired")
            
        # Проверить issuer
        if payload.get('iss') != 'dating-app':
            raise ValidationError("Invalid issuer")
            
        return payload
    except jwt.InvalidTokenError as e:
        raise ValidationError(f"Invalid token: {e}")
```
