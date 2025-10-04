# 🔐 Admin Panel - Dating App

Административная панель для управления приложением знакомств.

## 🌟 Возможности

### 👥 Управление пользователями
- Просмотр всех пользователей с поиском и фильтрацией
- Детальная информация о пользователе (профиль, фото, статистика)
- Блокировка/разблокировка пользователей
- Просмотр статистики взаимодействий

### 📸 Модерация фотографий
- Просмотр всех загруженных фотографий
- Фильтр по статусу (на модерации / проверенные)
- Одобрение фотографий
- Удаление неподходящих фотографий
- Просмотр NSFW score для каждого фото

### 📊 Статистика системы
- Общее количество пользователей
- Активные пользователи (за последние 30 дней)
- Количество заполненных профилей
- Статистика фотографий
- Количество матчей и взаимодействий
- Заблокированные пользователи

### ⚙️ Настройки системы
- Управление порогом NSFW детектора
- Создание новых администраторов

## 🚀 Быстрый старт

### Доступ к панели

После запуска приложения админ панель доступна по адресу:
```
http://localhost:8086/admin-panel/index.html
```

Или через API Gateway:
```
http://localhost:8080/admin-panel/index.html
```

### Учетные данные по умолчанию

**Логин:** `admin`  
**Пароль:** `admin123`

> ⚠️ **ВАЖНО:** Измените пароль администратора по умолчанию после первого входа в production среде!

## 🔧 Конфигурация

### Переменные окружения

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `DATABASE_URL` | URL подключения к PostgreSQL | `postgresql+asyncpg://dating:dating@localhost:5432/dating` |
| `JWT_SECRET` | Секретный ключ для JWT токенов | `your-secret-key` |
| `ADMIN_SERVICE_HOST` | Хост для admin service | `0.0.0.0` |
| `ADMIN_SERVICE_PORT` | Порт для admin service | `8086` |

### Docker Compose

Admin service уже настроен в `docker-compose.yml`:

```yaml
admin-service:
  build:
    context: .
    dockerfile: services/admin/Dockerfile
  depends_on:
    db:
      condition: service_healthy
  environment:
    DATABASE_URL: postgresql+asyncpg://${POSTGRES_USER:-dating}:${POSTGRES_PASSWORD:-dating}@db:5432/${POSTGRES_DB:-dating}
    JWT_SECRET: ${JWT_SECRET}
    ADMIN_SERVICE_HOST: 0.0.0.0
    ADMIN_SERVICE_PORT: 8086
  ports:
    - "8086:8086"
```

## 📡 API Endpoints

### Аутентификация
- `POST /admin/login` - Вход в систему

### Статистика
- `GET /admin/stats` - Получить статистику системы

### Пользователи
- `GET /admin/users` - Список пользователей (с пагинацией и поиском)
- `GET /admin/users/{user_id}` - Детальная информация о пользователе
- `PUT /admin/users/{user_id}` - Обновить информацию пользователя

### Фотографии
- `GET /admin/photos` - Список фотографий (с фильтрацией)
- `PUT /admin/photos/{photo_id}` - Обновить статус фотографии
- `DELETE /admin/photos/{photo_id}` - Удалить фотографию

### Здоровье сервиса
- `GET /health` - Health check

## 🔒 Безопасность

### Создание нового администратора

Для создания нового администратора используйте SQL:

```sql
-- Пароль хешируется с помощью SHA-256
-- Для генерации хеша: echo -n "your_password" | sha256sum
INSERT INTO admins (username, password_hash, full_name, email, is_active, is_super_admin)
VALUES (
    'username',
    'your_password_hash',
    'Full Name',
    'email@example.com',
    true,
    false
);
```

Или используйте форму в разделе "Настройки" админ панели.

### Смена пароля администратора

```sql
-- Обновить пароль (пароль должен быть хеширован SHA-256)
UPDATE admins 
SET password_hash = 'new_password_hash', 
    updated_at = NOW()
WHERE username = 'admin';
```

### Рекомендации по безопасности

1. **Измените пароль по умолчанию** сразу после первого входа
2. **Используйте сложные пароли** (минимум 12 символов)
3. **Ограничьте доступ к админ панели** через firewall/VPN
4. **Регулярно проверяйте логи** входа администраторов
5. **Используйте HTTPS** в production среде
6. **Настройте rate limiting** для защиты от брутфорса

## 🛠️ Разработка

### Локальный запуск

```bash
# Установить зависимости
pip install -r requirements.txt

# Запустить admin service
export DATABASE_URL="postgresql+asyncpg://dating:dating@localhost:5432/dating"
export JWT_SECRET="your-secret-key"
python -m services.admin.main
```

### Структура файлов

```
services/admin/
├── __init__.py           # Package init
├── main.py               # Основной сервер и API endpoints
├── Dockerfile            # Docker образ
├── README.md             # Эта документация
└── static/               # Веб интерфейс
    ├── index.html        # HTML страница
    ├── css/
    │   └── admin.css     # Стили
    └── js/
        └── admin.js      # JavaScript логика
```

## 📝 Миграция базы данных

Миграция для создания таблицы `admins`:

```bash
# Применить миграцию
alembic upgrade head
```

Миграция создает:
- Таблицу `admins` с полями для аутентификации
- Индексы на username и email
- Администратора по умолчанию (admin/admin123)

## 🔍 Мониторинг

### Логи

Admin service использует структурированное логирование:

```python
logger.info("Admin login", extra={
    "event_type": "admin_login",
    "username": username,
    "ip": request.remote
})
```

### Метрики

Health check endpoint:
```bash
curl http://localhost:8086/health
```

## 📚 Дополнительная документация

- [Основной README](../../README.md)
- [Архитектура](../../docs/ARCHITECTURE.md)
- [Deployment](../../docs/DEPLOYMENT.md)

## 🐛 Известные ограничения

1. **Сессии в памяти** - токены не сохраняются между перезапусками
   - Для production используйте Redis или database storage
2. **Базовая аутентификация** - использует SHA-256 вместо bcrypt
   - Для production рекомендуется bcrypt/argon2
3. **Нет 2FA** - двухфакторная аутентификация не реализована
4. **Нет rate limiting** - нет защиты от брутфорса

## 🚀 Будущие улучшения

- [ ] Хранение сессий в Redis
- [ ] Использование bcrypt/argon2 для паролей
- [ ] Двухфакторная аутентификация (2FA)
- [ ] Rate limiting для API
- [ ] Аудит лог действий администраторов
- [ ] Экспорт данных в CSV/Excel
- [ ] Графики и аналитика
- [ ] Управление настройками системы через UI
- [ ] Bulk операции над пользователями
- [ ] Расширенная модерация контента

---

**Версия:** 1.0.0  
**Последнее обновление:** 2024-01-15
