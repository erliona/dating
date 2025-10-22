# JWT Security Implementation

## Обзор

Система теперь полностью защищена JWT аутентификацией. Все микросервисы требуют валидный JWT токен для доступа к защищенным endpoints.

## Архитектура безопасности

### JWT Middleware

```python
# core/middleware/jwt_middleware.py
@web.middleware
async def jwt_middleware(request: web.Request, handler) -> web.Response:
    """
    JWT authentication middleware.
    
    Validates JWT tokens for all protected endpoints.
    Adds user_id to request context for authenticated requests.
    """
```

### Защищенные endpoints

Все сервисы теперь защищены JWT middleware:

- **Profile Service** (8082) - `/profiles/*`
- **Discovery Service** (8083) - `/discovery/*`
- **Media Service** (8084) - `/media/*`
- **Chat Service** (8085) - `/chat/*`
- **Notification Service** (8087) - `/api/notifications/*`
- **Admin Service** (8086) - `/admin/*` (с admin_jwt_middleware)

### Исключения

Следующие endpoints не требуют аутентификации:

- `/health` - health checks
- `/auth/*` (кроме `/auth/verify`) - аутентификация
- `/admin/login` - вход в админ панель

## Конфигурация

### Environment Variables

```bash
JWT_SECRET=your-super-secret-jwt-key-here
```

### Dependencies

```txt
PyJWT>=2.8  # JWT token generation and validation
bcrypt>=4.0  # Secure password hashing
```

## Использование

### Получение JWT токена

```javascript
// WebApp - аутентификация через Telegram
const initData = Telegram.WebApp.initData;
const response = await fetch('/api/auth/tg', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ initData })
});
const { token } = await response.json();
```

### Использование токена

```javascript
// Все API запросы должны включать токен
const response = await fetch('/api/profiles/123', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
});
```

### Admin аутентификация

```javascript
// Админ панель - отдельная аутентификация
const response = await fetch('/admin/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password })
});
const { admin_token } = await response.json();
```

## Безопасность

### Токены

- **User JWT** - для обычных пользователей
- **Admin JWT** - для администраторов
- **Expiration** - токены имеют срок действия
- **Secret** - используется JWT_SECRET для подписи

### Валидация

- Все входящие запросы проверяются на наличие валидного токена
- Невалидные токены отклоняются с ошибкой 401
- Health checks и auth endpoints исключены из проверки

## Мониторинг

### Логи

Все попытки аутентификации логируются:

```json
{
  "timestamp": "2025-01-22T19:30:11.579667+00:00",
  "level": "WARNING",
  "logger": "core.middleware.jwt_middleware",
  "message": "Missing Authorization header for /profiles/123"
}
```

### Метрики

- Количество успешных аутентификаций
- Количество неудачных попыток
- Время ответа middleware

## Troubleshooting

### Ошибки аутентификации

1. **401 Unauthorized** - отсутствует или невалидный токен
2. **500 Internal Server Error** - проблема с JWT_SECRET

### Проверка токена

```bash
# Проверить токен локально
echo "your-jwt-token" | cut -d. -f2 | base64 -d
```

### Отладка

```python
# Включить debug логирование
import logging
logging.getLogger('core.middleware.jwt_middleware').setLevel(logging.DEBUG)
```

## Миграция

### Включение JWT

JWT middleware автоматически включен во всех сервисах:

```python
# services/*/main.py
from core.middleware.jwt_middleware import jwt_middleware

def create_app(config: dict) -> web.Application:
    app = web.Application()
    app.middlewares.append(jwt_middleware)
    # ...
```

### Отключение (не рекомендуется)

```python
# Временно отключить JWT
# app.middlewares.append(jwt_middleware)
```

## Best Practices

1. **Никогда не логируйте JWT токены**
2. **Используйте HTTPS в продакшене**
3. **Регулярно ротируйте JWT_SECRET**
4. **Устанавливайте разумное время жизни токенов**
5. **Мониторьте попытки аутентификации**

## Связанные документы

- [Security Guide](SECURITY.md)
- [API Documentation](API_DOCUMENTATION.md)
- [Deployment Guide](DEPLOYMENT_GUIDE.md)
