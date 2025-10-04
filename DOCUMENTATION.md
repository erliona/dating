# 💕 Dating Telegram Mini App - Полная документация

## 📖 Обзор

Полнофункциональное приложение знакомств, реализованное как Telegram Mini App. Позволяет пользователям создавать профили, искать потенциальных партнеров, ставить лайки и общаться с совпадениями.

## 🎯 Назначение приложения

**Dating Mini App** - это современное приложение для знакомств, интегрированное в Telegram:

### Для пользователей
- 💑 **Поиск партнера** - просмотр анкет с фотографиями и информацией о других пользователях
- ❤️ **Система лайков** - возможность проявить симпатию или пропустить профиль
- 🎯 **Матчинг** - автоматическое создание связи при взаимной симпатии
- 📍 **Поиск поблизости** - фильтрация по расстоянию с сохранением приватности
- 🔐 **Безопасность** - проверка возраста 18+, управление приватностью данных
- 🌟 **Избранное** - возможность сохранять интересные профили

### Технические преимущества
- ✅ Не требует установки - работает внутри Telegram
- ✅ Быстрая авторизация через Telegram аккаунт
- ✅ Адаптивный интерфейс под любые устройства
- ✅ Production-ready инфраструктура с мониторингом
- ✅ Высокий уровень безопасности и приватности
- ✅ Масштабируемая архитектура

## ✨ Реализованные функции

### 👤 Профили пользователей
- **Создание профиля** - полная анкета с валидацией всех полей
  - Имя (2-50 символов)
  - Возраст (18+ обязательно)
  - Пол (мужской/женский/другое)
  - Сексуальная ориентация и предпочтения
  - Цели знакомства (серьезные отношения, дружба, etc.)
  - Биография (опционально, до 500 символов)
  
- **Фотографии**
  - До 3 фотографий профиля
  - Форматы: JPEG, PNG, WebP
  - Максимальный размер: 5 МБ на фото
  - Автоматическая оптимизация изображений
  
- **Геолокация**
  - Автоматическое определение местоположения
  - Ручной выбор города (если запретили GPS)
  - Хранение через geohash для приватности (~5км точность)
  - Фильтрация партнеров по расстоянию
  
- **Настройки приватности**
  - Скрыть точный возраст
  - Скрыть расстояние от других пользователей
  - Скрыть статус "онлайн"

### 🔍 Поиск и знакомства

- **Discovery (Просмотр анкет)**
  - Карточный интерфейс для просмотра профилей
  - Фотографии с возможностью пролистывания
  - Информация о пользователе: возраст, расстояние, биография
  - Фильтрация по предпочтениям и расстоянию
  
- **Действия с профилями**
  - ❤️ **Лайк** - выразить симпатию
  - ✖️ **Пропустить** - перейти к следующему профилю
  - ⭐ **Суперлайк** - особая симпатия (будущая функция)
  - 🌟 **Добавить в избранное** - сохранить профиль
  
- **Матчинг**
  - Автоматическое создание матча при взаимном лайке
  - Уведомление о новом матче
  - Список всех матчей с возможностью просмотра
  
- **Избранное**
  - Сохранение интересных профилей
  - Просмотр списка избранных
  - Удаление из избранного

### 🔐 Безопасность и аутентификация

- **Telegram аутентификация**
  - HMAC валидация данных от Telegram
  - Проверка подписи и времени инициализации
  - Защита от подделки данных
  
- **JWT токены**
  - Серверные сессии с временем жизни
  - Автоматическое обновление токенов
  - Защита от несанкционированного доступа
  
- **Rate Limiting**
  - Ограничение количества запросов
  - Защита от злоупотреблений и спама
  - Настраиваемые лимиты для разных эндпоинтов
  
- **Валидация данных**
  - Проверка возраста 18+ на клиенте и сервере
  - Валидация всех полей профиля
  - Защита от SQL инъекций через ORM
  - Санитизация пользовательского ввода

## 📊 Текущий статус

### Что полностью работает
- ✅ Регистрация и создание профиля
- ✅ Загрузка и хранение фотографий
- ✅ Поиск партнеров с фильтрацией
- ✅ Система лайков и матчинга
- ✅ Избранное
- ✅ Редактирование профиля
- ✅ Настройки приватности
- ✅ База данных с миграциями
- ✅ HTTP API для всех операций
- ✅ Мониторинг и логирование

### В разработке
- 🚧 Чат между совпавшими пользователями
- 🚧 Push-уведомления о новых матчах и сообщениях
- 🚧 Расширенные фильтры поиска
- 🚧 Система модерации контента
- 🚧 Платные функции (Telegram Stars)

## 🚀 Быстрый старт

### Требования
- Docker и Docker Compose v2.0+
- Telegram бот токен от [@BotFather](https://t.me/BotFather)
- (Опционально) Домен для production развертывания

### Создание бота в Telegram

1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям: укажите имя и username бота
4. Сохраните полученный токен (формат: `123456789:ABCdef...`)
5. Настройте бота:
   ```
   /setdescription - Приложение для знакомств
   /setabouttext - Dating app in Telegram
   /setuserpic - Загрузите аватар бота
   ```

### Локальная разработка

```bash
# 1. Клонировать репозиторий
git clone https://github.com/erliona/dating.git
cd dating

# 2. Настроить переменные окружения
cp .env.example .env
# Отредактируйте .env и укажите ваш BOT_TOKEN

# 3. Запустить инфраструктуру для разработки
docker compose -f docker-compose.dev.yml up -d

# 4. Проверить статус сервисов
docker compose ps

# 5. Просмотреть логи
docker compose logs -f bot

# 6. Открыть бота в Telegram и отправить /start
```

### Запуск с мониторингом

```bash
# Запуск с полным стеком мониторинга
docker compose --profile monitoring up -d

# Доступ к дашбордам:
# Grafana:    http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
# Mini App:   http://localhost (через бота)
```

### Проверка работоспособности

После запуска проверьте:

1. **База данных**
   ```bash
   docker compose exec db psql -U dating -d dating -c "SELECT count(*) FROM users;"
   ```

2. **API бота**
   ```bash
   curl -X GET "http://localhost:8080/health"
   ```

3. **Telegram бот**
   - Откройте вашего бота в Telegram
   - Отправьте `/start`
   - Должна появиться кнопка "🚀 Открыть Mini App"

4. **Mini App**
   - Нажмите на кнопку открытия Mini App
   - Должен загрузиться экран приветствия

## 🏗️ Архитектура приложения

### Общая архитектура

```
┌─────────────────┐
│  Telegram User  │
└────────┬────────┘
         │
         ▼
┌─────────────────────────────────────────────┐
│         Telegram Mini App (WebApp)          │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │Discovery │  │ Matches  │  │ Settings │ │
│  │  Screen  │  │  Screen  │  │  Screen  │ │
│  └──────────┘  └──────────┘  └──────────┘ │
│         HTML + CSS + JavaScript             │
└────────┬────────────────────────────────────┘
         │ HTTP API / WebApp.sendData()
         ▼
┌─────────────────────────────────────────────┐
│           Telegram Bot (Backend)            │
│  ┌─────────────────────────────────────┐   │
│  │  Bot Handlers (aiogram)             │   │
│  │  - /start command                   │   │
│  │  - WebApp data handler              │   │
│  │  - Callbacks                        │   │
│  └─────────────────────────────────────┘   │
│  ┌─────────────────────────────────────┐   │
│  │  HTTP API (aiohttp)                 │   │
│  │  - /api/profile                     │   │
│  │  - /api/discover                    │   │
│  │  - /api/like                        │   │
│  │  - /api/matches                     │   │
│  │  - /api/favorites                   │   │
│  └─────────────────────────────────────┘   │
│  ┌─────────────────────────────────────┐   │
│  │  Business Logic                     │   │
│  │  - Authentication (JWT, HMAC)       │   │
│  │  - Validation                       │   │
│  │  - Matching algorithm               │   │
│  │  - Geolocation processing           │   │
│  └─────────────────────────────────────┘   │
│  ┌─────────────────────────────────────┐   │
│  │  Data Access Layer (Repository)     │   │
│  │  - ProfileRepository                │   │
│  │  - InteractionRepository            │   │
│  │  - MatchRepository                  │   │
│  └─────────────────────────────────────┘   │
└────────┬────────────────────────────────────┘
         │ SQLAlchemy (async)
         ▼
┌─────────────────────────────────────────────┐
│         PostgreSQL Database                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │  users   │  │ profiles │  │  photos  │ │
│  └──────────┘  └──────────┘  └──────────┘ │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │interactions│ │ matches  │  │favorites │ │
│  └──────────┘  └──────────┘  └──────────┘ │
└─────────────────────────────────────────────┘
```

### Компоненты системы

#### 1. Frontend (Telegram Mini App)
- **Технологии**: Чистый HTML/CSS/JavaScript без фреймворков
- **Экраны**: Onboarding, Profile, Discovery, Matches, Favorites, Settings
- **Функции**:
  - Интеграция с Telegram WebApp API
  - Адаптация к теме Telegram (светлая/темная)
  - Haptic feedback для улучшения UX
  - Offline-ready с очередью действий
  - Валидация данных на клиенте

#### 2. Backend (Python Bot)
- **Технологии**: Python 3.11+, aiogram 3.x, aiohttp
- **Модули**:
  - `main.py` - точка входа, обработчики команд бота
  - `api.py` - HTTP API для Mini App
  - `db.py` - модели базы данных
  - `repository.py` - CRUD операции
  - `validation.py` - валидация данных
  - `security.py` - аутентификация и шифрование
  - `geo.py` - обработка геолокации
  - `media.py` - обработка фотографий
  - `cache.py` - кеширование с TTL
  - `config.py` - управление конфигурацией

#### 3. База данных (PostgreSQL)
- **Таблицы**:
  - `users` - пользователи Telegram
  - `profiles` - анкеты пользователей
  - `photos` - фотографии профилей
  - `interactions` - лайки/дизлайки
  - `matches` - взаимные симпатии
  - `favorites` - избранные профили
- **Особенности**:
  - Async драйвер (asyncpg)
  - Индексы для быстрого поиска
  - Constraints для целостности данных
  - Миграции через Alembic

#### 4. Мониторинг
- **Prometheus** - метрики приложения
- **Grafana** - визуализация и дашборды
- **Loki** - централизованные логи
- **cAdvisor** - метрики контейнеров

### Поток данных

#### Создание профиля
```
1. User -> Mini App: заполняет форму профиля
2. Mini App: валидирует данные на клиенте
3. Mini App -> Bot: tg.sendData(profileData)
4. Bot: получает данные в WebApp handler
5. Bot: валидирует данные на сервере
6. Bot -> DB: сохраняет user, profile, photos
7. Bot -> User: отправляет подтверждение
```

#### Поиск и матчинг
```
1. Mini App -> API: GET /api/discover?limit=10
2. API: проверяет JWT токен
3. Repository: выбирает профили по фильтрам
   - Исключает просмотренные
   - Фильтрует по расстоянию (geohash)
   - Фильтрует по предпочтениям
4. API -> Mini App: возвращает список профилей
5. User: делает действие (like/pass)
6. Mini App -> API: POST /api/like {target_id}
7. Repository: сохраняет interaction
8. Repository: проверяет взаимность
9. IF взаимный like -> создает match
10. API -> Mini App: возвращает результат
```

### Безопасность

- **На входе**: HMAC валидация Telegram initData
- **Сессии**: JWT токены с TTL 24 часа
- **API**: Rate limiting на все эндпоинты
- **База данных**: SQL injection protection через ORM
- **Пароли**: Не используются, авторизация через Telegram
- **HTTPS**: Обязательно в production (Let's Encrypt)

## 🔐 Конфигурация

### Переменные окружения

#### Обязательные переменные

```bash
# Telegram Bot
BOT_TOKEN=123456789:ABCdef...          # Токен от @BotFather

# База данных
POSTGRES_DB=dating                     # Имя базы данных
POSTGRES_USER=dating                   # Пользователь БД
POSTGRES_PASSWORD=secure_password      # Пароль БД (используйте сильный пароль!)

# JWT
JWT_SECRET=your-secret-key-here        # Секретный ключ для JWT токенов
```

#### Опциональные переменные (для production с HTTPS)

```bash
# Домен и SSL
DOMAIN=yourdomain.com                  # Ваш домен
WEBAPP_URL=https://${DOMAIN}           # URL Mini App
ACME_EMAIL=admin@yourdomain.com        # Email для Let's Encrypt

# API
API_PORT=8080                          # Порт HTTP API (по умолчанию 8080)

# Мониторинг
ENABLE_MONITORING=true                 # Включить мониторинг
```

#### Дополнительные настройки

```bash
# Лимиты
MAX_PHOTO_SIZE_MB=5                    # Максимальный размер фото
MAX_PHOTOS_PER_PROFILE=3               # Количество фото в профиле

# Геолокация
DEFAULT_SEARCH_RADIUS_KM=50            # Радиус поиска по умолчанию
GEOHASH_PRECISION=5                    # Точность geohash (5 = ~5км)

# Rate Limiting
RATE_LIMIT_REQUESTS=100                # Запросов в минуту
RATE_LIMIT_PERIOD=60                   # Период в секундах

# База данных
DB_POOL_SIZE=10                        # Размер пула соединений
DB_MAX_OVERFLOW=20                     # Максимум дополнительных соединений

# Логирование
LOG_LEVEL=INFO                         # Уровень логирования (DEBUG, INFO, WARNING, ERROR)
JSON_LOGS=true                         # Логи в JSON формате
```

### Создание .env файла

```bash
# Скопируйте пример
cp .env.example .env

# Отредактируйте и добавьте реальные значения
nano .env  # или используйте любой редактор

# Проверьте, что файл не попадет в git
cat .gitignore | grep .env
```

### Безопасность переменных

⚠️ **Важно:**
- Никогда не коммитьте `.env` файл в git
- Используйте сильные пароли для БД
- Храните JWT_SECRET в секрете
- В production используйте secrets management (GitHub Secrets, Vault, etc.)

### Проверка конфигурации

```bash
# Проверить, что все переменные заданы
docker compose config

# Проверить подключение к БД
docker compose exec db psql -U dating -d dating -c "SELECT version();"

# Проверить бота
docker compose logs bot | grep "Bot started"
```

## 💾 База данных

### Структура базы данных

#### Таблица: users
Основная информация о пользователях Telegram.

```sql
CREATE TABLE users (
    id BIGINT PRIMARY KEY,           -- Telegram user ID
    username VARCHAR(255),           -- Telegram username
    first_name VARCHAR(255),         -- Имя в Telegram
    created_at TIMESTAMP,            -- Дата регистрации
    last_active TIMESTAMP            -- Последняя активность
);
```

#### Таблица: profiles
Анкеты пользователей для знакомств.

```sql
CREATE TABLE profiles (
    id SERIAL PRIMARY KEY,
    user_id BIGINT UNIQUE NOT NULL,  -- Ссылка на users.id
    name VARCHAR(50) NOT NULL,       -- Имя в профиле
    birth_date DATE NOT NULL,        -- Дата рождения
    gender VARCHAR(20) NOT NULL,     -- Пол
    orientation VARCHAR(50),         -- Ориентация
    looking_for VARCHAR(255),        -- Ищет
    goals TEXT,                      -- Цели знакомства
    bio TEXT,                        -- О себе
    city VARCHAR(100),               -- Город
    country VARCHAR(100),            -- Страна
    latitude DECIMAL(10, 8),         -- Широта
    longitude DECIMAL(11, 8),        -- Долгота
    geohash VARCHAR(20),             -- Geohash для поиска
    hide_age BOOLEAN,                -- Скрыть возраст
    hide_distance BOOLEAN,           -- Скрыть расстояние
    hide_online BOOLEAN,             -- Скрыть онлайн
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);
```

#### Таблица: photos
Фотографии профилей.

```sql
CREATE TABLE photos (
    id SERIAL PRIMARY KEY,
    profile_id INTEGER NOT NULL,     -- Ссылка на profiles.id
    file_id VARCHAR(255) NOT NULL,   -- Telegram file_id
    file_path VARCHAR(500),          -- Путь к файлу
    position INTEGER,                -- Порядок отображения
    created_at TIMESTAMP,
    FOREIGN KEY (profile_id) REFERENCES profiles(id) ON DELETE CASCADE
);
```

#### Таблица: interactions
История взаимодействий пользователей.

```sql
CREATE TABLE interactions (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,         -- Кто сделал действие
    target_id BIGINT NOT NULL,       -- На кого направлено
    action VARCHAR(20) NOT NULL,     -- like, pass, superlike
    created_at TIMESTAMP,
    UNIQUE (user_id, target_id),     -- Одно действие на пользователя
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (target_id) REFERENCES users(id)
);
```

#### Таблица: matches
Взаимные симпатии.

```sql
CREATE TABLE matches (
    id SERIAL PRIMARY KEY,
    user1_id BIGINT NOT NULL,        -- Первый пользователь
    user2_id BIGINT NOT NULL,        -- Второй пользователь
    created_at TIMESTAMP,
    UNIQUE (user1_id, user2_id),
    CHECK (user1_id < user2_id),     -- Предотвращение дублей
    FOREIGN KEY (user1_id) REFERENCES users(id),
    FOREIGN KEY (user2_id) REFERENCES users(id)
);
```

#### Таблица: favorites
Избранные профили.

```sql
CREATE TABLE favorites (
    id SERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,         -- Кто добавил
    target_id BIGINT NOT NULL,       -- Кого добавили
    created_at TIMESTAMP,
    UNIQUE (user_id, target_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (target_id) REFERENCES users(id)
);
```

### Индексы

```sql
-- Быстрый поиск профиля по user_id
CREATE INDEX idx_profiles_user_id ON profiles(user_id);

-- Поиск по геолокации
CREATE INDEX idx_profiles_geohash ON profiles(geohash);

-- Поиск взаимодействий
CREATE INDEX idx_interactions_user_id ON interactions(user_id);
CREATE INDEX idx_interactions_target_id ON interactions(target_id);

-- Поиск матчей
CREATE INDEX idx_matches_user1 ON matches(user1_id);
CREATE INDEX idx_matches_user2 ON matches(user2_id);
```

### Миграции

#### Применение миграций

```bash
# Применить все новые миграции
docker compose exec bot alembic upgrade head

# Откатить последнюю миграцию
docker compose exec bot alembic downgrade -1

# Посмотреть текущую версию
docker compose exec bot alembic current

# Посмотреть историю миграций
docker compose exec bot alembic history
```

#### Создание новой миграции

```bash
# Автоматическое создание на основе изменений моделей
docker compose exec bot alembic revision --autogenerate -m "Add new field to profiles"

# Ручное создание миграции
docker compose exec bot alembic revision -m "Custom migration"
```

### Резервное копирование

#### Создание бэкапа

```bash
# Полный дамп базы
docker compose exec db pg_dump -U dating dating > backup_$(date +%Y%m%d_%H%M%S).sql

# Только данные (без схемы)
docker compose exec db pg_dump -U dating dating --data-only > data_backup.sql

# Только схема (без данных)
docker compose exec db pg_dump -U dating dating --schema-only > schema_backup.sql

# Конкретная таблица
docker compose exec db pg_dump -U dating dating -t profiles > profiles_backup.sql
```

#### Восстановление из бэкапа

```bash
# Восстановить полный дамп
docker compose exec -T db psql -U dating dating < backup.sql

# Очистить базу перед восстановлением
docker compose exec db psql -U dating dating -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
docker compose exec -T db psql -U dating dating < backup.sql
```

#### Автоматическое резервное копирование

Создайте cron задачу на сервере:

```bash
# Открыть crontab
crontab -e

# Добавить задачу (каждый день в 3:00)
0 3 * * * cd /path/to/dating && docker compose exec -T db pg_dump -U dating dating > /backups/dating_$(date +\%Y\%m\%d).sql

# Удалять бэкапы старше 30 дней
0 4 * * * find /backups -name "dating_*.sql" -mtime +30 -delete
```

### Maintenance

#### Очистка старых данных

```bash
# Удалить старые неактивные профили (пример)
docker compose exec db psql -U dating dating << EOF
DELETE FROM profiles 
WHERE updated_at < NOW() - INTERVAL '1 year'
AND user_id NOT IN (SELECT user_id FROM interactions WHERE created_at > NOW() - INTERVAL '6 months');
EOF
```

#### Анализ размера таблиц

```bash
docker compose exec db psql -U dating dating -c "
SELECT 
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
"
```

#### Оптимизация базы

```bash
# VACUUM и ANALYZE для всех таблиц
docker compose exec db psql -U dating dating -c "VACUUM ANALYZE;"

# REINDEX для всех индексов
docker compose exec db psql -U dating dating -c "REINDEX DATABASE dating;"
```

## 🧪 Тестирование

### Запуск тестов

#### Базовые команды

```bash
# Все тесты
python -m pytest tests/ -v

# С отчетом о покрытии
python -m pytest tests/ --cov=bot --cov-report=html --cov-report=term

# Конкретный файл тестов
python -m pytest tests/test_validation.py -v

# Конкретный тест
python -m pytest tests/test_validation.py::test_validate_name -v

# Быстрый запуск (без покрытия)
python -m pytest tests/ -q
```

#### В Docker контейнере

```bash
# Запустить все тесты в контейнере
docker compose exec bot pytest tests/ -v

# С покрытием кода
docker compose exec bot pytest tests/ --cov=bot --cov-report=term
```

### Структура тестов

Проект содержит **293 теста** с покрытием **81%**:

#### По модулям

| Модуль | Тестов | Покрытие | Описание |
|--------|--------|----------|----------|
| `test_validation.py` | 56 | 92% | Валидация данных профилей |
| `test_api.py` | 44 | 62% | HTTP API эндпоинты |
| `test_security.py` | 31 | 86% | JWT, HMAC, шифрование |
| `test_media.py` | 30 | 84% | Обработка фотографий |
| `test_geo.py` | 21 | 97% | Геолокация и geohash |
| `test_config.py` | 20 | 99% | Конфигурация |
| `test_main.py` | 19 | 90% | Обработчики бота |
| `test_repository.py` | 14 | 82% | CRUD операции БД |
| `test_cache.py` | 11 | 97% | Кеширование |
| `test_database.py` | 47 | 100% | Модели БД |

#### По категориям функциональности

- **Валидация и безопасность**: 87 тестов
  - Проверка полей профиля
  - JWT токены и HMAC
  - Rate limiting
  - Санитизация данных

- **База данных**: 61 тест
  - Модели и связи
  - CRUD операции
  - Транзакции
  - Constraints

- **API и интеграция**: 63 теста
  - HTTP endpoints
  - Аутентификация
  - Обработчики бота
  - WebApp интеграция

- **Утилиты**: 82 теста
  - Геолокация
  - Медиа обработка
  - Кеширование
  - Конфигурация

### Типы тестов

#### Unit тесты
Изолированное тестирование отдельных функций:

```python
def test_validate_name():
    """Тест валидации имени."""
    assert validate_name("Иван") is True
    assert validate_name("A" * 51) is False
    assert validate_name("") is False
```

#### Integration тесты
Тестирование взаимодействия компонентов:

```python
async def test_profile_creation_flow(db_session):
    """Тест создания профиля end-to-end."""
    # Создать пользователя
    user = User(id=123, username="test")
    db_session.add(user)
    
    # Создать профиль
    profile = Profile(user_id=123, name="Test", ...)
    db_session.add(profile)
    
    # Проверить сохранение
    result = await db_session.execute(
        select(Profile).where(Profile.user_id == 123)
    )
    assert result.scalar_one() is not None
```

#### API тесты
Тестирование HTTP эндпоинтов:

```python
async def test_discover_endpoint(client, auth_token):
    """Тест API поиска профилей."""
    response = await client.get(
        "/api/discover",
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status == 200
    data = await response.json()
    assert "profiles" in data
```

### Покрытие кода

#### Текущее покрытие

**Общее покрытие: 81%**

Детально по модулям:
- ✅ `bot/db.py`: **100%** - модели базы данных
- ✅ `bot/config.py`: **99%** - конфигурация
- ✅ `bot/cache.py`: **97%** - кеширование
- ✅ `bot/geo.py`: **97%** - геолокация
- ✅ `bot/validation.py`: **92%** - валидация
- ✅ `bot/main.py`: **90%** - обработчики бота
- ✅ `bot/security.py`: **86%** - безопасность
- ✅ `bot/media.py`: **84%** - медиа
- ⚠️ `bot/repository.py`: **82%** - репозитории
- ⚠️ `bot/api.py`: **62%** - HTTP API

#### Генерация отчета

```bash
# Создать HTML отчет
pytest --cov=bot --cov-report=html

# Открыть в браузере
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

### CI/CD тестирование

Тесты автоматически запускаются в GitHub Actions при:
- Push в main ветку
- Создании Pull Request
- Ручном запуске workflow

Проверки в CI:
1. ✅ Синтаксис Python
2. ✅ Все unit тесты
3. ✅ Покрытие кода (минимум 80%)
4. ✅ Миграции БД
5. ✅ Безопасность зависимостей (pip-audit)
6. ✅ Сборка Docker образа

### Написание тестов

#### Структура теста

```python
import pytest
from bot.validation import validate_age

def test_validate_age_valid():
    """Тест валидации корректного возраста."""
    # Arrange - подготовка
    birth_date = "1990-01-01"
    
    # Act - действие
    result = validate_age(birth_date)
    
    # Assert - проверка
    assert result is True

def test_validate_age_under_18():
    """Тест отклонения возраста младше 18."""
    birth_date = "2010-01-01"
    result = validate_age(birth_date)
    assert result is False
```

#### Фикстуры

```python
@pytest.fixture
async def db_session():
    """Фикстура для тестовой сессии БД."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    
    async with async_session() as session:
        yield session
```

### Отладка тестов

```bash
# Подробный вывод
pytest tests/ -vv

# Показать print() в тестах
pytest tests/ -s

# Остановиться на первой ошибке
pytest tests/ -x

# Запустить только упавшие тесты
pytest tests/ --lf

# Отладчик при ошибке
pytest tests/ --pdb
```

## 📊 Monitoring

### Grafana Dashboards

**1. System Overview** - Infrastructure metrics
- Container CPU and memory usage
- PostgreSQL connections
- Network traffic
- All logs with JSON parsing

**2. Application Logs & Events** - Application monitoring
- Bot lifecycle events
- Error and warning counts
- Log levels over time
- Structured event logging

**3. Discovery & Matching** - User interaction metrics
- Discovery actions
- Likes, passes, matches
- User actions distribution

### Accessing Dashboards

```bash
# Start with monitoring
docker compose --profile monitoring up -d

# Access Grafana
open http://localhost:3000  # Default: admin/admin

# Check Prometheus
open http://localhost:9090
```

### Structured Logging

All logs are JSON formatted with:
- Timestamp (ISO 8601)
- Level (INFO, WARNING, ERROR)
- Logger name
- Message
- Module, function, line number
- Custom fields (user_id, event_type, etc.)

## 🚢 Deployment

### Production Deployment

**Using GitHub Actions (Recommended):**

1. Configure GitHub Secrets:
   - `DEPLOY_HOST` - Server IP/hostname
   - `DEPLOY_USER` - SSH user
   - `DEPLOY_SSH_KEY` - Private SSH key
   - `BOT_TOKEN` - Telegram bot token

2. Push to main branch - automatic deployment!

**Manual Deployment:**

```bash
# On server
git pull origin main
docker compose up -d --build

# Check status
docker compose ps

# View logs
docker compose logs -f
```

### Updating

```bash
# Pull latest changes
git pull origin main

# Restart services
docker compose restart bot webapp

# Apply migrations
docker compose exec bot alembic upgrade head
```

## 🛡️ Security

### Best Practices
- ✅ All secrets in environment variables
- ✅ HTTPS everywhere via Traefik
- ✅ JWT authentication for API
- ✅ HMAC validation for Telegram data
- ✅ SQL injection protection via ORM
- ✅ No hardcoded credentials
- ✅ Automated security scanning in CI

### Reporting Security Issues

Email security concerns to the repository owner. Do not create public issues for security vulnerabilities.

## 🐛 Troubleshooting

### Bot Not Responding

```bash
# Check logs
docker compose logs -f bot

# Restart bot
docker compose restart bot

# Check bot status
docker compose ps
```

### Database Connection Issues

```bash
# Check database status
docker compose ps db

# View database logs
docker compose logs db

# Test connection
docker compose exec db psql -U dating -d dating -c "SELECT 1;"
```

### Grafana Not Loading

```bash
# Restart Grafana
docker compose --profile monitoring restart grafana

# Check logs
docker compose logs grafana

# Verify datasources
curl -u admin:admin http://localhost:3000/api/datasources
```

## 📚 Additional Resources

### Documentation
- [Full Documentation Index](docs/INDEX.md)
- [Architecture Details](docs/ARCHITECTURE.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Testing Guide](docs/TESTING.md)
- [API Documentation](docs/PHOTO_UPLOAD_API.md)

### Development
- [Contributing Guidelines](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)
- [Roadmap](ROADMAP.md)
- [Project Status](PROJECT_STATUS.md)

### External Links
- [GitHub Repository](https://github.com/erliona/dating)
- [GitHub Issues](https://github.com/erliona/dating/issues)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [aiogram Documentation](https://docs.aiogram.dev/)

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Code of conduct
- Development setup
- Pull request process
- Coding standards

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

## 💬 Support

- **Documentation**: See [docs/](docs/)
- **Bug Reports**: [GitHub Issues](https://github.com/erliona/dating/issues)
- **Questions**: [GitHub Discussions](https://github.com/erliona/dating/discussions)

---

**Made with ❤️ for the community**

*If you find this project useful, please star it on GitHub!* ⭐
