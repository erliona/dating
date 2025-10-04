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

## 📊 Мониторинг и наблюдаемость

### Обзор стека мониторинга

Приложение использует полный стек observability:

```
Приложение → Prometheus (метрики) → Grafana (визуализация)
           → Loki (логи) → Grafana (поиск и анализ)
           → cAdvisor (контейнеры) → Prometheus
           → Node Exporter (система) → Prometheus
           → Postgres Exporter (БД) → Prometheus
```

### Компоненты мониторинга

#### 1. Prometheus
**Назначение**: Сбор и хранение метрик

**Метрики приложения**:
- HTTP запросы (общее количество, время отклика)
- Операции БД (запросы, соединения, latency)
- Кеш (hits, misses, размер)
- Ошибки и исключения

**Системные метрики**:
- CPU, память, диск
- Сетевая активность
- Метрики контейнеров Docker

**Доступ**: http://localhost:9090

#### 2. Grafana
**Назначение**: Визуализация метрик и логов

**Дашборды**:

1. **System Overview** (Обзор системы)
   - CPU и память всех контейнеров
   - Нагрузка на PostgreSQL
   - Сетевая активность
   - Использование диска
   - Статус сервисов

2. **Application Logs & Events** (Логи приложения)
   - События жизненного цикла бота
   - Ошибки и предупреждения
   - Структурированные логи с фильтрацией
   - Временные графики по уровням логов

3. **Discovery & Matching** (Метрики знакомств)
   - Количество просмотров профилей
   - Лайки, дизлайки, суперлайки
   - Созданные матчи
   - Активность пользователей
   - Conversion rate (просмотры → лайки → матчи)

**Доступ**: http://localhost:3000 (admin/admin)

#### 3. Loki
**Назначение**: Агрегация и хранение логов

**Особенности**:
- Централизованное хранение логов всех сервисов
- Индексация по меткам (labels)
- Интеграция с Grafana для поиска
- Retention: 30 дней

#### 4. Promtail
**Назначение**: Сбор логов с контейнеров

Автоматически собирает логи из:
- Bot (приложение)
- PostgreSQL
- Traefik
- Все другие контейнеры

### Запуск мониторинга

#### Локально

```bash
# Запустить с мониторингом
docker compose --profile monitoring up -d

# Проверить статус
docker compose ps

# Просмотреть логи мониторинга
docker compose logs -f prometheus grafana loki
```

#### Production

Мониторинг автоматически включается в CI/CD при деплое:

```yaml
# .github/workflows/deploy.yml
run_docker compose --profile monitoring up -d --build
```

### Доступ к дашбордам

```bash
# Grafana
http://your-domain.com:3000
# Логин: admin
# Пароль: admin (смените при первом входе!)

# Prometheus
http://your-domain.com:9090

# cAdvisor (метрики контейнеров)
http://your-domain.com:8081
```

### Структурированное логирование

Все логи приложения в JSON формате для удобного анализа:

```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "level": "INFO",
  "logger": "bot.main",
  "message": "User created profile",
  "module": "main",
  "function": "handle_profile_creation",
  "line": 145,
  "user_id": 123456789,
  "event_type": "profile_created"
}
```

**Поля логов**:
- `timestamp` - время в UTC (ISO 8601)
- `level` - уровень (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `logger` - имя логгера
- `message` - текст сообщения
- `module`, `function`, `line` - место в коде
- Кастомные поля: `user_id`, `event_type`, `error`, etc.

### Поиск логов в Grafana

1. Откройте Grafana → Explore
2. Выберите источник данных: Loki
3. Используйте LogQL для поиска:

```logql
# Все логи бота
{container="bot"}

# Только ошибки
{container="bot"} |= "ERROR"

# Логи конкретного пользователя
{container="bot"} | json | user_id="123456789"

# Ошибки за последний час
{container="bot"} |= "ERROR" [1h]

# Количество событий по типам
sum by (event_type) (rate({container="bot"} | json [5m]))
```

### Алерты и уведомления

#### Настройка алертов в Grafana

1. Создайте notification channel (Email, Telegram, Slack)
2. Настройте правила алертов для критических метрик:

**Примеры алертов**:

- **High Error Rate**
  ```
  rate(errors_total[5m]) > 10
  ```
  Уведомление, если более 10 ошибок в минуту

- **Database Connections**
  ```
  pg_stat_database_numbackends > 80
  ```
  Уведомление, если более 80 активных соединений

- **Low Disk Space**
  ```
  node_filesystem_avail_bytes / node_filesystem_size_bytes < 0.1
  ```
  Уведомление, если менее 10% свободного места

- **Service Down**
  ```
  up{job="bot"} == 0
  ```
  Уведомление, если бот не отвечает

### Метрики производительности

#### Ключевые показатели (KPI)

**Производительность**:
- Response time API: p50, p95, p99
- Database query time
- Cache hit rate
- Requests per second

**Бизнес-метрики**:
- Новые регистрации в день
- Активные пользователи (DAU, MAU)
- Созданные матчи
- Conversion rate (просмотры → лайки → матчи)
- Средние лайки на пользователя

**Надежность**:
- Uptime (%)
- Error rate (%)
- Failed requests
- Database availability

### Troubleshooting с помощью мониторинга

#### Высокая нагрузка на CPU

1. Проверить Grafana → System Overview → CPU usage
2. Найти контейнер с высокой нагрузкой
3. Проверить логи: `docker compose logs <container>`
4. Увеличить ресурсы или оптимизировать код

#### Медленные запросы к БД

1. Grafana → System Overview → PostgreSQL metrics
2. Prometheus → Query: `pg_stat_statements_mean_time_seconds`
3. Найти медленные запросы в логах
4. Добавить индексы или оптимизировать запросы

#### Высокий error rate

1. Grafana → Logs & Events → Filter by ERROR
2. Найти паттерн ошибок
3. Проверить стек-трейсы
4. Исправить код и задеплоить

## 🚢 Развертывание (Deployment)

### Требования к серверу

**Минимальные требования**:
- Ubuntu 20.04+ или Debian 11+
- 2 CPU cores
- 4 GB RAM
- 20 GB SSD
- Docker 20.10+
- Docker Compose 2.0+

**Рекомендуемые**:
- 4 CPU cores
- 8 GB RAM
- 50 GB SSD
- Доменное имя с DNS
- Открыты порты: 80 (HTTP), 443 (HTTPS)

### Подготовка сервера

#### 1. Установка Docker

```bash
# Обновить систему
sudo apt update && sudo apt upgrade -y

# Установить Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Добавить пользователя в группу docker
sudo usermod -aG docker $USER

# Установить Docker Compose
sudo apt install docker-compose-plugin

# Проверить установку
docker --version
docker compose version
```

#### 2. Настройка файрвола

```bash
# Установить UFW
sudo apt install ufw

# Разрешить SSH
sudo ufw allow 22/tcp

# Разрешить HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Включить файрвол
sudo ufw enable
```

#### 3. Настройка DNS

Добавьте A-запись для вашего домена:
```
A    @    YOUR_SERVER_IP
A    www  YOUR_SERVER_IP
```

### Автоматическое развертывание (GitHub Actions)

#### 1. Настройка GitHub Secrets

Перейдите в Settings → Secrets and variables → Actions и добавьте:

| Secret | Описание | Пример |
|--------|----------|--------|
| `DEPLOY_HOST` | IP или hostname сервера | `198.51.100.1` |
| `DEPLOY_USER` | SSH пользователь | `ubuntu` |
| `DEPLOY_SSH_KEY` | Приватный SSH ключ | `-----BEGIN OPENSSH...` |
| `BOT_TOKEN` | Telegram bot token | `123456789:ABCdef...` |
| `DOMAIN` | Доменное имя (опционально) | `dating.example.com` |

#### 2. Деплой

```bash
# Просто запушьте в main ветку
git push origin main

# GitHub Actions автоматически:
# 1. Запустит тесты
# 2. Соберет Docker образ
# 3. Подключится к серверу по SSH
# 4. Скопирует файлы
# 5. Запустит docker compose
# 6. Применит миграции
# 7. Проверит health check
```

Отслеживайте прогресс в GitHub → Actions

### Ручное развертывание

#### 1. Клонировать репозиторий на сервер

```bash
# Подключиться к серверу
ssh user@your-server.com

# Клонировать репозиторий
git clone https://github.com/erliona/dating.git
cd dating
```

#### 2. Настроить .env файл

```bash
# Создать из примера
cp .env.example .env

# Отредактировать
nano .env
```

Укажите необходимые переменные:
```bash
BOT_TOKEN=your_bot_token_here
DOMAIN=your-domain.com
ACME_EMAIL=admin@your-domain.com
POSTGRES_PASSWORD=your_secure_password
JWT_SECRET=your_secret_key
```

#### 3. Запустить приложение

```bash
# Production с HTTPS и мониторингом
docker compose --profile monitoring up -d --build

# Проверить статус
docker compose ps

# Просмотреть логи
docker compose logs -f bot
```

#### 4. Применить миграции БД

```bash
# Применить все миграции
docker compose exec bot alembic upgrade head

# Проверить статус
docker compose exec bot alembic current
```

#### 5. Проверить работу

```bash
# Проверить health endpoint
curl https://your-domain.com/health

# Проверить бота в Telegram
# Откройте бота и отправьте /start
```

### Обновление приложения

#### С GitHub Actions

Просто запушьте изменения в main ветку - деплой произойдет автоматически.

#### Вручную

```bash
# На сервере
cd /path/to/dating

# Получить изменения
git pull origin main

# Пересобрать и перезапустить
docker compose --profile monitoring up -d --build

# Применить новые миграции
docker compose exec bot alembic upgrade head

# Проверить логи
docker compose logs -f bot
```

### Откат к предыдущей версии

```bash
# Посмотреть историю коммитов
git log --oneline

# Откатиться к конкретному коммиту
git checkout <commit-hash>

# Пересобрать
docker compose up -d --build

# Откатить миграции (если нужно)
docker compose exec bot alembic downgrade <revision>
```

### Zero-downtime deployment

Для обновления без простоя:

```bash
# 1. Запустить новую версию на другом порту
docker compose -f docker-compose.blue-green.yml up -d

# 2. Проверить работоспособность
curl http://localhost:8081/health

# 3. Переключить Traefik на новую версию
# (обновить конфигурацию или labels)

# 4. Остановить старую версию
docker compose down
```

### SSL сертификаты

Traefik автоматически получает SSL сертификаты от Let's Encrypt.

#### Проверка сертификатов

```bash
# Посмотреть логи Traefik
docker compose logs traefik | grep acme

# Проверить сертификат
openssl s_client -connect your-domain.com:443 -servername your-domain.com
```

#### Ручное обновление сертификатов

Обычно не требуется, но если нужно:

```bash
# Удалить старый сертификат
docker compose exec traefik rm /letsencrypt/acme.json

# Перезапустить Traefik
docker compose restart traefik

# Новый сертификат будет получен автоматически
```

### Масштабирование

#### Горизонтальное масштабирование бота

```bash
# Запустить несколько экземпляров бота
docker compose up -d --scale bot=3

# Использовать webhook вместо polling
# для распределения нагрузки
```

#### Масштабирование БД

```bash
# Настроить PostgreSQL репликацию
# 1. Master для записи
# 2. Replicas для чтения

# В коде использовать read replicas для select запросов
```

### Мониторинг развертывания

#### Health checks

```bash
# Проверить все сервисы
curl https://your-domain.com/health

# Проверить конкретный контейнер
docker compose ps bot
docker compose logs bot | tail -20
```

#### Метрики после деплоя

1. Откройте Grafana
2. Проверьте дашборд "System Overview"
3. Убедитесь, что:
   - Все контейнеры запущены
   - CPU/Memory в норме
   - Нет ошибок в логах
   - БД доступна

### Troubleshooting

#### Бот не запускается

```bash
# Проверить логи
docker compose logs bot

# Проверить переменные окружения
docker compose config | grep BOT_TOKEN

# Проверить подключение к БД
docker compose exec bot python -c "from bot.db import engine; print('OK')"
```

#### HTTPS не работает

```bash
# Проверить DNS
dig your-domain.com

# Проверить порты
sudo netstat -tlnp | grep -E '(80|443)'

# Проверить логи Traefik
docker compose logs traefik | grep -i error

# Проверить файрвол
sudo ufw status
```

#### База данных не доступна

```bash
# Проверить контейнер
docker compose ps db

# Проверить логи
docker compose logs db

# Проверить подключение
docker compose exec db psql -U dating -d dating -c "SELECT 1;"
```

## 🛡️ Безопасность

### Реализованные меры безопасности

#### 1. Аутентификация и авторизация

**Telegram аутентификация**:
- ✅ HMAC-SHA256 валидация `initData` от Telegram
- ✅ Проверка времени инициализации (max 1 час)
- ✅ Проверка подписи данных
- ✅ Защита от replay атак

**JWT токены**:
- ✅ Серверные сессии с TTL 24 часа
- ✅ Подписанные токены (HS256)
- ✅ Автоматическое обновление
- ✅ Отзыв токенов при необходимости

**Rate Limiting**:
- ✅ Ограничение запросов по IP
- ✅ Ограничение по пользователю
- ✅ Защита от DDoS
- ✅ Настраиваемые лимиты

#### 2. Защита данных

**В транзите**:
- ✅ HTTPS везде (Let's Encrypt)
- ✅ TLS 1.2+ только
- ✅ Strong ciphers
- ✅ HSTS заголовки

**В хранилище**:
- ✅ Пароли БД в переменных окружения
- ✅ JWT секреты не в коде
- ✅ Фотографии с ограничениями доступа
- ✅ Geohash для приватности локации (~5км точность)

**В коде**:
- ✅ SQL injection protection (SQLAlchemy ORM)
- ✅ XSS protection (санитизация ввода)
- ✅ CSRF protection для API
- ✅ Input validation на клиенте и сервере

#### 3. Приватность пользователей

**Контроль данных**:
- ✅ Настройки приватности (скрыть возраст/расстояние/онлайн)
- ✅ Geohash вместо точных координат
- ✅ Удаление аккаунта с данными
- ✅ Экспорт данных (GDPR compliance готовность)

**Минимизация данных**:
- ✅ Хранятся только необходимые данные
- ✅ Нет сбора лишней информации
- ✅ Автоматическая очистка старых сессий
- ✅ Логи без персональных данных

#### 4. Безопасность инфраструктуры

**Docker**:
- ✅ Минимальные базовые образы
- ✅ Non-root пользователи в контейнерах
- ✅ Изолированные сети
- ✅ Read-only файловые системы где возможно

**База данных**:
- ✅ Изолированная сеть
- ✅ Сильные пароли
- ✅ Регулярные бэкапы
- ✅ Шифрование соединений

**Секреты**:
- ✅ GitHub Secrets для CI/CD
- ✅ Переменные окружения (.env)
- ✅ Не коммитятся в git
- ✅ Ротация секретов

#### 5. Мониторинг безопасности

**Логирование**:
- ✅ Все попытки аутентификации
- ✅ Неудачные запросы API
- ✅ Превышение rate limits
- ✅ Ошибки валидации

**Алерты**:
- ✅ Высокий error rate
- ✅ Подозрительная активность
- ✅ Превышение лимитов
- ✅ Падение сервисов

**Аудит**:
- ✅ История изменений профилей
- ✅ Лог взаимодействий
- ✅ Отслеживание блокировок
- ✅ Security scanning в CI (pip-audit)

### Рекомендации по безопасности

#### Для разработчиков

1. **Никогда не коммитьте секреты**
   ```bash
   # Проверьте перед коммитом
   git diff --staged | grep -i "password\|secret\|token"
   ```

2. **Используйте сильные пароли**
   ```bash
   # Генерация безопасного пароля
   openssl rand -base64 32
   ```

3. **Обновляйте зависимости**
   ```bash
   # Проверка уязвимостей
   pip-audit
   
   # Обновление пакетов
   pip install --upgrade -r requirements.txt
   ```

4. **Валидируйте все входные данные**
   ```python
   # Пример валидации
   def validate_input(data: str) -> bool:
       # Проверка на XSS
       if re.search(r'<script|javascript:', data, re.I):
           return False
       return True
   ```

#### Для администраторов

1. **Регулярно обновляйте систему**
   ```bash
   sudo apt update && sudo apt upgrade -y
   docker compose pull
   ```

2. **Настройте файрвол**
   ```bash
   sudo ufw default deny incoming
   sudo ufw allow 22/tcp  # SSH
   sudo ufw allow 80/tcp  # HTTP
   sudo ufw allow 443/tcp # HTTPS
   sudo ufw enable
   ```

3. **Настройте автоматические бэкапы**
   ```bash
   # Cron задача для ежедневного бэкапа
   0 3 * * * /path/to/backup-script.sh
   ```

4. **Мониторьте логи безопасности**
   ```bash
   # SSH попытки
   sudo grep "Failed password" /var/log/auth.log
   
   # Необычная активность
   docker compose logs bot | grep "WARNING\|ERROR"
   ```

### Соответствие стандартам

#### GDPR Ready
- ✅ Право на удаление данных
- ✅ Право на экспорт данных
- ✅ Прозрачность обработки данных
- ✅ Минимизация данных
- ⚠️ Требуется юридическая политика конфиденциальности

#### 18+ Compliance
- ✅ Валидация возраста при регистрации
- ✅ Блокировка младше 18 лет
- ✅ Проверка даты рождения

#### Telegram Guidelines
- ✅ Следование ToS Telegram
- ✅ Корректное использование Bot API
- ✅ Уважение privacy пользователей

### Сообщение об уязвимостях

Если вы обнаружили уязвимость:

1. **НЕ создавайте публичный issue**
2. **Отправьте email** владельцу репозитория
3. **Опишите**:
   - Тип уязвимости
   - Шаги для воспроизведения
   - Потенциальное влияние
   - Предложения по исправлению

Мы обязуемся:
- Ответить в течение 48 часов
- Исправить критические уязвимости в течение 7 дней
- Упомянуть вас в credits (по желанию)

## 🐛 Решение проблем (Troubleshooting)

### Частые проблемы и решения

#### 1. Бот не отвечает в Telegram

**Симптомы**: Бот не реагирует на команды `/start`

**Диагностика**:
```bash
# Проверить статус контейнера
docker compose ps bot

# Посмотреть логи
docker compose logs -f bot

# Проверить webhook (если используется)
curl https://api.telegram.org/bot${BOT_TOKEN}/getWebhookInfo
```

**Решения**:
```bash
# 1. Перезапустить бота
docker compose restart bot

# 2. Проверить BOT_TOKEN
docker compose exec bot env | grep BOT_TOKEN

# 3. Пересобрать контейнер
docker compose up -d --build bot

# 4. Проверить подключение к интернету
docker compose exec bot ping -c 3 api.telegram.org
```

#### 2. База данных не доступна

**Симптомы**: Ошибки "connection refused" в логах

**Диагностика**:
```bash
# Проверить статус PostgreSQL
docker compose ps db

# Проверить логи
docker compose logs db | tail -50

# Проверить подключение изнутри контейнера
docker compose exec bot python -c "
from bot.config import load_config
config = load_config()
print(config.database_url)
"
```

**Решения**:
```bash
# 1. Перезапустить БД
docker compose restart db

# 2. Проверить пароль в .env
cat .env | grep POSTGRES_PASSWORD

# 3. Подключиться напрямую
docker compose exec db psql -U dating -d dating -c "SELECT version();"

# 4. Пересоздать volume (ВНИМАНИЕ: удалит данные!)
docker compose down
docker volume rm dating_postgres_data
docker compose up -d
```

#### 3. Ошибки миграций БД

**Симптомы**: "alembic.util.exc.CommandError" при старте

**Диагностика**:
```bash
# Проверить текущую версию
docker compose exec bot alembic current

# Проверить историю
docker compose exec bot alembic history
```

**Решения**:
```bash
# 1. Применить миграции
docker compose exec bot alembic upgrade head

# 2. Если не помогает - сбросить до начала и применить заново
docker compose exec bot alembic downgrade base
docker compose exec bot alembic upgrade head

# 3. Проверить файлы миграций
ls -la migrations/versions/
```

#### 4. Mini App не загружается

**Симптомы**: Белый экран или ошибка загрузки

**Диагностика**:
```bash
# Проверить веб-сервер
curl http://localhost/

# Проверить логи nginx
docker compose logs webapp

# Проверить файлы
docker compose exec webapp ls -la /usr/share/nginx/html/
```

**Решения**:
```bash
# 1. Проверить WEBAPP_URL в .env
cat .env | grep WEBAPP_URL

# 2. Перезапустить веб-сервер
docker compose restart webapp

# 3. Открыть в браузере напрямую
open http://localhost  # или ваш домен

# 4. Проверить в консоли браузера на ошибки JavaScript
```

#### 5. SSL сертификаты не получаются

**Симптомы**: HTTPS не работает, ошибки сертификата

**Диагностика**:
```bash
# Проверить логи Traefik
docker compose logs traefik | grep -i acme

# Проверить DNS
dig +short your-domain.com

# Проверить доступность портов
sudo netstat -tlnp | grep -E '(80|443)'
```

**Решения**:
```bash
# 1. Проверить DOMAIN и ACME_EMAIL в .env
cat .env | grep -E "DOMAIN|ACME_EMAIL"

# 2. Убедиться, что порты открыты
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# 3. Удалить старый сертификат и попробовать снова
docker compose down
docker volume rm dating_traefik_certs
docker compose up -d

# 4. Проверить DNS A-record
nslookup your-domain.com
```

#### 6. Высокая нагрузка CPU/Memory

**Симптомы**: Медленная работа, зависания

**Диагностика**:
```bash
# Проверить использование ресурсов
docker stats

# Конкретный контейнер
docker stats dating_bot_1

# Проверить в Grafana
open http://localhost:3000
```

**Решения**:
```bash
# 1. Увеличить лимиты в docker-compose.yml
services:
  bot:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G

# 2. Перезапустить сервисы
docker compose restart

# 3. Очистить кеш (если используется)
docker compose exec bot python -c "from bot.cache import cache; cache.clear()"

# 4. Оптимизировать БД
docker compose exec db psql -U dating dating -c "VACUUM ANALYZE;"
```

#### 7. Ошибки аутентификации

**Симптомы**: "Unauthorized", "Invalid JWT"

**Диагностика**:
```bash
# Проверить JWT_SECRET
docker compose exec bot env | grep JWT_SECRET

# Проверить логи бота
docker compose logs bot | grep -i "auth\|jwt"
```

**Решения**:
```bash
# 1. Проверить, что JWT_SECRET задан в .env
cat .env | grep JWT_SECRET

# 2. Очистить сессии
docker compose exec bot python -c "
from bot.security import clear_expired_sessions
clear_expired_sessions()
"

# 3. Перезапустить бота
docker compose restart bot
```

#### 8. Фотографии не загружаются

**Симптомы**: Ошибки при загрузке фото

**Диагностика**:
```bash
# Проверить API
curl -X POST http://localhost:8080/api/upload_photo \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -F "photo=@test.jpg"

# Проверить логи
docker compose logs bot | grep -i photo
```

**Решения**:
```bash
# 1. Проверить лимиты размера
cat .env | grep MAX_PHOTO_SIZE

# 2. Проверить права на volume
docker compose exec bot ls -la /app/photos

# 3. Проверить свободное место
df -h
docker system df
```

### Логи и отладка

#### Просмотр логов

```bash
# Все сервисы
docker compose logs -f

# Конкретный сервис
docker compose logs -f bot

# Последние N строк
docker compose logs --tail=100 bot

# С временными метками
docker compose logs -f --timestamps bot

# Только ошибки
docker compose logs bot | grep ERROR
```

#### Подключение к контейнеру

```bash
# Запустить shell в контейнере
docker compose exec bot bash

# Запустить Python REPL
docker compose exec bot python

# Выполнить команду
docker compose exec bot python -c "print('Hello')"
```

#### Отладка в реальном времени

```bash
# Смотреть изменения в реальном времени
watch -n 1 'docker compose ps'

# Мониторинг ресурсов
docker stats

# Живые логи с фильтрацией
docker compose logs -f bot | grep -i error
```

### Получение помощи

Если проблема не решается:

1. **Соберите информацию**:
   ```bash
   # Версии
   docker --version
   docker compose version
   
   # Статус
   docker compose ps
   
   # Конфигурация
   docker compose config
   
   # Логи (последние 100 строк)
   docker compose logs --tail=100 > logs.txt
   ```

2. **Создайте issue** на GitHub с:
   - Описанием проблемы
   - Шагами для воспроизведения
   - Логами
   - Версиями ПО

3. **Проверьте существующие issues**:
   - https://github.com/erliona/dating/issues

4. **Обратитесь в Discussions**:
   - https://github.com/erliona/dating/discussions

## 📚 Дополнительные ресурсы

### Документация проекта

- **[📖 Основная документация](README.md)** - обзор и быстрый старт
- **[📊 Статус проекта](PROJECT_STATUS.md)** - реализованные и планируемые функции
- **[📝 История изменений](CHANGELOG.md)** - changelog всех версий
- **[🗺️ Roadmap](ROADMAP.md)** - план развития проекта
- **[📋 Индекс документации](docs/INDEX.md)** - навигация по всем документам

### Техническая документация

- **[🏗️ Архитектура](docs/ARCHITECTURE.md)** - детали архитектуры системы
- **[🚀 Развертывание](docs/DEPLOYMENT.md)** - подробное руководство по deployment
- **[🧪 Тестирование](docs/TESTING.md)** - запуск и написание тестов
- **[📡 API Reference](docs/PHOTO_UPLOAD_API.md)** - документация API
- **[💾 Персистентность данных](docs/DATA_PERSISTENCE.md)** - управление данными и бэкапы

### Для разработчиков

- **[🤝 Contributing](CONTRIBUTING.md)** - как внести вклад в проект
  - Настройка окружения
  - Стиль кода
  - Процесс PR
  - Code of conduct

- **[🔒 Security](SECURITY.md)** - политика безопасности
  - Сообщение об уязвимостях
  - Best practices

### Внешние ресурсы

#### Telegram
- [Telegram Bot API](https://core.telegram.org/bots/api) - официальная документация API
- [Telegram Mini Apps](https://core.telegram.org/bots/webapps) - руководство по Mini Apps
- [@BotFather](https://t.me/BotFather) - создание и настройка ботов

#### Фреймворки и библиотеки
- [aiogram Documentation](https://docs.aiogram.dev/) - документация aiogram
- [SQLAlchemy](https://docs.sqlalchemy.org/) - ORM документация
- [FastAPI](https://fastapi.tiangolo.com/) - альтернатива для REST API
- [Alembic](https://alembic.sqlalchemy.org/) - миграции БД

#### Инфраструктура
- [Docker Documentation](https://docs.docker.com/) - Docker и Compose
- [Traefik](https://doc.traefik.io/traefik/) - reverse proxy
- [Prometheus](https://prometheus.io/docs/) - мониторинг
- [Grafana](https://grafana.com/docs/) - визуализация

### Полезные ссылки

- **[GitHub Repository](https://github.com/erliona/dating)** - исходный код
- **[GitHub Issues](https://github.com/erliona/dating/issues)** - баг-репорты и фичи
- **[GitHub Discussions](https://github.com/erliona/dating/discussions)** - вопросы и обсуждения
- **[GitHub Actions](https://github.com/erliona/dating/actions)** - CI/CD статус

## 🤝 Вклад в проект

Мы приветствуем любые вклады в проект! 

### Как помочь

- 🐛 **Сообщить о баге** - создайте [issue](https://github.com/erliona/dating/issues)
- 💡 **Предложить функцию** - откройте [discussion](https://github.com/erliona/dating/discussions)
- 📝 **Улучшить документацию** - отправьте PR
- 💻 **Написать код** - исправьте баг или реализуйте фичу
- ⭐ **Поставить звезду** - если проект полезен

### Процесс контрибуции

1. Fork репозитория
2. Создайте ветку (`git checkout -b feature/amazing-feature`)
3. Внесите изменения
4. Напишите/обновите тесты
5. Убедитесь, что тесты проходят (`pytest`)
6. Commit изменений (`git commit -m 'Add amazing feature'`)
7. Push в ветку (`git push origin feature/amazing-feature`)
8. Откройте Pull Request

Подробнее: [CONTRIBUTING.md](CONTRIBUTING.md)

### Правила

- ✅ Следуйте существующему стилю кода
- ✅ Пишите тесты для новой функциональности
- ✅ Обновляйте документацию
- ✅ Одна фича = один PR
- ✅ Подробное описание в PR

## 📄 Лицензия

Этот проект распространяется под лицензией **MIT License**.

Это означает, что вы можете:
- ✅ Использовать в коммерческих целях
- ✅ Модифицировать код
- ✅ Распространять
- ✅ Использовать в приватных проектах

При условии:
- 📝 Сохранения копирайта и лицензии
- 📝 Указания авторства

Подробнее см. [LICENSE](LICENSE)

## 💬 Поддержка

### Получить помощь

- 📖 **Документация**: начните с [README.md](README.md) и этого файла
- 🐛 **Баги**: [GitHub Issues](https://github.com/erliona/dating/issues)
- 💬 **Вопросы**: [GitHub Discussions](https://github.com/erliona/dating/discussions)
- 🔒 **Безопасность**: см. [SECURITY.md](SECURITY.md)

### Канатлы связи

- GitHub Issues - баг-репорты и фичи-реквесты
- GitHub Discussions - общие вопросы и обсуждения
- Email - для вопросов безопасности (см. SECURITY.md)

### FAQ

**Q: Можно ли использовать этот проект коммерчески?**
A: Да, проект под MIT лицензией, можно использовать в любых целях.

**Q: Как добавить новую функцию?**
A: Создайте issue с описанием или discussion для обсуждения, затем PR.

**Q: Есть ли демо?**
A: Демо не предоставляется, но вы можете развернуть локально за 5 минут.

**Q: Какие требования к серверу?**
A: Минимум 2 CPU, 4GB RAM, 20GB диск. Рекомендуется 4 CPU, 8GB RAM.

**Q: Поддерживается ли масштабирование?**
A: Да, можно запустить несколько экземпляров бота и использовать репликацию БД.

---

## 🎉 Благодарности

Спасибо всем контрибьюторам и сообществу за поддержку проекта!

### Используемые технологии

- [Python](https://www.python.org/) - язык программирования
- [aiogram](https://aiogram.dev/) - Telegram Bot framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - ORM
- [PostgreSQL](https://www.postgresql.org/) - база данных
- [Docker](https://www.docker.com/) - контейнеризация
- [Traefik](https://traefik.io/) - reverse proxy
- [Grafana](https://grafana.com/) - мониторинг
- [Prometheus](https://prometheus.io/) - метрики

---

**Сделано с ❤️ для сообщества**

*Если проект оказался полезным, поставьте ⭐ на GitHub!*

---

**Версия документации**: 2.0  
**Последнее обновление**: Январь 2025  
**Статус**: Production Ready
