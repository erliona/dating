# 🏗️ Архитектура системы

## Обзор

Dating Bot - это микросервисная архитектура, построенная на Docker контейнерах с полной автоматизацией CI/CD.

```
┌─────────────────────────────────────────────────────────────────┐
│                        External Layer                            │
│  ┌──────────────┐         ┌──────────────┐                      │
│  │   Telegram   │         │  Let's       │                      │
│  │     Bot API  │         │  Encrypt CA  │                      │
│  └──────┬───────┘         └──────┬───────┘                      │
│         │                        │                               │
└─────────┼────────────────────────┼───────────────────────────────┘
          │                        │
          │ HTTPS (443)            │ ACME (80/443)
          │                        │
┌─────────▼────────────────────────▼───────────────────────────────┐
│                     Reverse Proxy Layer                          │
│  ┌────────────────────────────────────────────────────────┐     │
│  │                    Traefik                              │     │
│  │  - SSL Termination                                      │     │
│  │  - Auto HTTPS with Let's Encrypt                        │     │
│  │  - HTTP → HTTPS redirect                                │     │
│  │  - Request routing                                      │     │
│  └─────────┬──────────────────────────────────────────────┘     │
└───────────┼──────────────────────────────────────────────────────┘
            │
    ┌───────┴────────┐
    │                │
┌───▼────┐     ┌────▼──────────────────────────────────────────────┐
│        │     │           Application Layer                        │
│ WebApp │     │  ┌──────────────────────────────────────────┐     │
│ (nginx)│     │  │       Telegram Bot (Python)               │     │
│        │     │  │  - aiogram 3.x framework                  │     │
│        │     │  │  - Command handlers                       │     │
│        │     │  │  - WebApp data processing                 │     │
│        │     │  │  - Matching algorithm                     │     │
│        │     │  │  - Notification system                    │     │
│        │     │  │  - Analytics engine                       │     │
│        │     │  └─────────────┬────────────────────────────┘     │
└────────┘     │                │                                   │
               └────────────────┼───────────────────────────────────┘
                                │
                                │ asyncpg
                                │
               ┌────────────────▼───────────────────────────────────┐
               │              Data Layer                            │
               │  ┌──────────────────────────────────────────┐     │
               │  │       PostgreSQL 15                       │     │
               │  │  - profiles (users)                       │     │
               │  │  - user_interactions (likes/dislikes)     │     │
               │  │  - matches (mutual likes)                 │     │
               │  │  - user_settings (preferences)            │     │
               │  │  Named volume: postgres_data              │     │
               │  └───────────────────────────────────────────┘     │
               └────────────────────────────────────────────────────┘

          ┌────────────────────────────────────────────────────────┐
          │            Monitoring Layer (Optional)                  │
          │  ┌──────────┐  ┌──────────┐  ┌───────────┐            │
          │  │Prometheus│  │  Grafana │  │   Loki    │            │
          │  │ (Metrics)│  │(Dashbrd) │  │  (Logs)   │            │
          │  └──────────┘  └──────────┘  └───────────┘            │
          │  ┌──────────┐  ┌──────────┐  ┌───────────┐            │
          │  │ cAdvisor │  │   Node   │  │ Postgres  │            │
          │  │(Cntnr)   │  │ Exporter │  │ Exporter  │            │
          │  └──────────┘  └──────────┘  └───────────┘            │
          └────────────────────────────────────────────────────────┘
```

---

## Компоненты системы

### 1. Traefik (Reverse Proxy)

**Роль**: Точка входа для всех внешних запросов

**Функции**:
- Автоматическое получение SSL сертификатов от Let's Encrypt
- HTTP → HTTPS редирект
- Маршрутизация запросов к WebApp
- Health checks
- Метрики для Prometheus

**Конфигурация**:
- Порты: 80 (HTTP), 443 (HTTPS)
- Volume: `traefik_certs` для хранения сертификатов
- Метод валидации: TLS Challenge (порт 443)

**Production Only**: В dev режиме (docker-compose.dev.yml) Traefik не используется

---

### 2. Telegram Bot

**Роль**: Основная бизнес-логика приложения

**Технологический стек**:
- Python 3.11+
- aiogram 3.x (async Telegram Bot framework)
- SQLAlchemy 2.0 (async ORM)
- asyncpg (PostgreSQL driver)
- Alembic (database migrations)

**Модули**:

#### `bot/main.py`
- Обработчики команд (`/start`, `/matches`, `/stats`, `/analytics`)
- Приём данных из WebApp
- Алгоритм матчинга
- Система уведомлений

#### `bot/db.py`
- Модели данных (ProfileModel, UserInteractionModel, MatchModel, UserSettingsModel)
- Репозитории для работы с БД
- Бизнес-логика взаимодействий

#### `bot/config.py`
- Загрузка и валидация конфигурации
- Проверка формата BOT_TOKEN
- Парсинг переменных окружения

#### `bot/analytics.py`
- Сбор метрик использования
- Агрегация статистики
- Расчет engagement rates

#### `bot/security.py`
- Rate limiting
- Валидация входных данных
- Защита от спама

#### `bot/cache.py`
- In-memory кэширование профилей
- TTL управление
- Оптимизация запросов к БД

**Алгоритм матчинга**:

1. **Взаимный лайк**: Пользователи должны лайкнуть друг друга
2. **Совместимость интересов**: 
   - Weighted scoring на основе общих интересов
   - 40% веса - совпадение интересов
3. **Географическая близость**:
   - 30% веса - одинаковая локация
4. **Совпадение целей**:
   - 20% веса - совпадающие цели знакомства
5. **Возрастная совместимость**:
   - 10% веса - близкий возраст (±5 лет)

**Процесс матчинга**:
```
User A likes User B
       ↓
Check if User B liked User A
       ↓
If YES → Calculate compatibility score
       ↓
If score > threshold → Create match
       ↓
Send notifications to both users
```

---

### 3. PostgreSQL Database

**Роль**: Персистентное хранилище данных

**Версия**: PostgreSQL 15 Alpine (оптимизированный образ)

**Схема данных**:

#### Таблица `profiles`
```sql
- id (SERIAL PRIMARY KEY)
- user_id (BIGINT UNIQUE) -- Telegram user ID
- name (VARCHAR)
- age (INTEGER)
- gender (VARCHAR)
- preference (VARCHAR) -- ищу: male/female/any
- bio (TEXT)
- location (VARCHAR)
- interests (JSONB) -- массив строк
- goal (VARCHAR) -- цель знакомства
- photo_file_id (VARCHAR)
- photo_url (VARCHAR)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)

INDEX: idx_user_id ON user_id
INDEX: idx_gender_preference ON (gender, preference)
INDEX: idx_location ON location
INDEX: idx_interests ON interests USING GIN
```

#### Таблица `user_interactions`
```sql
- id (SERIAL PRIMARY KEY)
- from_user_id (BIGINT) -- кто оценил
- to_user_id (BIGINT) -- кого оценили
- action (VARCHAR) -- 'like' или 'dislike'
- created_at (TIMESTAMP)

INDEX: idx_from_user ON from_user_id
INDEX: idx_to_user ON to_user_id
INDEX: idx_from_to ON (from_user_id, to_user_id)
UNIQUE CONSTRAINT: (from_user_id, to_user_id)
```

#### Таблица `matches`
```sql
- id (SERIAL PRIMARY KEY)
- user1_id (BIGINT)
- user2_id (BIGINT)
- compatibility_score (FLOAT)
- matched_at (TIMESTAMP)

INDEX: idx_user1 ON user1_id
INDEX: idx_user2 ON user2_id
UNIQUE CONSTRAINT: (user1_id, user2_id)
```

#### Таблица `user_settings`
```sql
- id (SERIAL PRIMARY KEY)
- user_id (BIGINT UNIQUE)
- min_age (INTEGER)
- max_age (INTEGER)
- max_distance (INTEGER)
- show_online_status (BOOLEAN)
- allow_notifications (BOOLEAN)

INDEX: idx_user_settings ON user_id
```

**Персистентность**:
- Named volume: `postgres_data`
- Данные сохраняются при перезапуске контейнеров
- При изменении пароля БД требуется пересоздание volume

**Backup стратегия**:
```bash
# Создать backup
docker compose exec db pg_dump -U dating dating > backup.sql

# Восстановить из backup
docker compose exec -T db psql -U dating dating < backup.sql
```

---

### 4. WebApp (nginx)

**Роль**: Современное мини-приложение Telegram для dating app

**Версия**: Полностью переработано (2024) с индустриальными best practices

**Структура**:
```
webapp/
├── README.md           # Подробная документация
├── index.html          # Современный HTML5 (семантический)
├── css/
│   └── style.css       # Модульный CSS с переменными
└── js/
    └── app.js          # Модульный ES6+ JavaScript
```

**Ключевые особенности**:
- ✅ **Card-based swipe interface** - индустриальный стандарт для dating apps
- ✅ **Модульная архитектура** - разделение UI/logic/data
- ✅ **Haptic feedback** - нативный опыт на мобильных
- ✅ **Offline queue** - взаимодействия сохраняются локально
- ✅ **Theme integration** - автоматическое следование Telegram theme
- ✅ **Accessibility** - WCAG 2.1 AA compliant
- ✅ **Mobile-first** - оптимизирован для мобильных устройств
- ✅ **No build step** - чистый HTML/CSS/JS

**Экраны**:
1. Profile Form - создание/редактирование анкеты
2. Discover - карточный интерфейс для свайпов
3. Matches - список взаимных симпатий

**Интеграция**:
- Отправка данных через `tg.sendData()` (Telegram WebApp SDK)
- Совместимо с существующим `webapp_handler` в боте
- Queuing механизм для взаимодействий

**Доступ**:
- Production: https://your-domain.com
- Development: http://localhost:8080

**Подробнее**: См. [webapp/README.md](../webapp/README.md)

---

### 5. Monitoring Stack (опционально)

Мониторинг включается через profile:
```bash
docker compose --profile monitoring up -d
```

#### Prometheus
- **Порт**: 9090
- **Роль**: Сбор и хранение метрик
- **Retention**: 30 дней
- **Targets**: cAdvisor, Node Exporter, Postgres Exporter, Traefik

#### Grafana
- **Порт**: 3000
- **Роль**: Визуализация и дашборды
- **Credentials**: admin/admin (измените при первом входе)
- **Datasources**: Prometheus, Loki

#### Loki + Promtail
- **Порт**: 3100
- **Роль**: Агрегация логов
- **Retention**: 30 дней
- **Sources**: Docker containers, system logs

#### Exporters
- **cAdvisor**: Метрики контейнеров (порт 8081)
- **Node Exporter**: Системные метрики (порт 9100)
- **Postgres Exporter**: Метрики БД (порт 9187)

---

## Data Flow

### 1. Создание профиля

```
User → Telegram Bot → /start command
        ↓
Bot → Send inline keyboard with WebApp button
        ↓
User → Click button → Open WebApp (nginx)
        ↓
User → Fill form → Submit
        ↓
WebApp → Send data via Telegram WebApp API
        ↓
Bot → Receive WebAppData → Validate
        ↓
Bot → Save to PostgreSQL (profiles table)
        ↓
Bot → Send confirmation message
```

### 2. Лайк и матчинг

```
User A → Bot → View User B profile
        ↓
User A → Like User B
        ↓
Bot → Save interaction (user_interactions table)
        ↓
Bot → Check if User B liked User A
        ↓
If YES:
    ├→ Calculate compatibility score
    ├→ Create match (matches table)
    ├→ Notify User A
    └→ Notify User B
```

### 3. Аналитика

```
Admin → /analytics command
        ↓
Bot → Query aggregated data from DB
        ↓
Bot → Calculate metrics (DAU, match rate, etc.)
        ↓
Bot → Format and send report
```

---

## Deployment Flow

### Local Development
```
Developer → docker compose -f docker-compose.dev.yml up
            ↓
Docker → Pull base images (postgres, nginx)
            ↓
Docker → Build bot image from Dockerfile
            ↓
Docker → Start containers (db → bot → webapp)
            ↓
Bot → Run migrations (Alembic)
            ↓
Bot → Start polling Telegram API
            ↓
Ready for testing ✓
```

### Production Deployment (CI/CD)
```
Developer → git push origin main
            ↓
GitHub Actions → Trigger deploy workflow
            ↓
Workflow → Validate secrets
            ↓
Workflow → Setup SSH connection
            ↓
Workflow → Prepare server (install Docker if needed)
            ↓
Workflow → Upload project files via rsync
            ↓
Workflow → Generate .env from secrets
            ↓
Workflow → Validate configuration
            ↓
Server → docker compose --profile monitoring up -d --build
            ↓
Server → Pull images & build bot
            ↓
Server → Start containers (Traefik, DB, Bot, WebApp, Monitoring)
            ↓
Server → Run migrations
            ↓
Workflow → Health checks
            ↓
Production ready ✓
```

---

## Scaling Considerations

### Vertical Scaling
- Увеличить ресурсы контейнеров (memory, CPU limits)
- Оптимизировать SQL запросы и индексы
- Включить кэширование (Redis)

### Horizontal Scaling
**Текущее ограничение**: Бот работает в single-instance режиме

**Для горизонтального масштабирования потребуется**:
1. Redis для shared state
2. Message queue (RabbitMQ) для распределения обновлений
3. Stateless bot instances
4. Load balancer перед ботами
5. Distributed session storage

**См. также**: [ROADMAP.md](../ROADMAP.md) - секция "Горизонтальное масштабирование"

---

## Security

### 1. Network Security
- Все внешние соединения через HTTPS (TLS 1.2+)
- Закрытые порты БД (доступна только из Docker network)
- Rate limiting в боте

### 2. Data Security
- Хэширование паролей не требуется (Telegram авторизация)
- Валидация всех входных данных
- SQL injection защита через SQLAlchemy ORM
- XSS защита в WebApp

### 3. Secrets Management
- Переменные окружения в .env (не коммитится)
- GitHub Secrets для CI/CD
- Автоматическая ротация SSL сертификатов

### 4. Access Control
- Telegram user_id как первичная идентификация
- Нет публичного API (только через Telegram)
- Admin команды доступны только владельцу бота

---

## Performance

### Database
- Индексы на часто используемых полях
- Connection pooling через SQLAlchemy
- Async queries для неблокирующих операций

### Bot
- In-memory кэш профилей (TTL 300s)
- Batch processing для уведомлений
- Async/await для всех I/O операций

### WebApp
- Статические файлы сжаты gzip (nginx)
- CDN готовность (можно добавить CloudFlare)
- Минифицированные JS/CSS

---

## Monitoring and Observability

### Метрики (Prometheus)
- Request rate, error rate, duration
- Container resources (CPU, Memory, Network)
- Database connections, query performance
- Custom business metrics (matches, likes, users)

### Логирование (Loki)
- Structured logging (JSON format)
- Log levels: DEBUG, INFO, WARNING, ERROR, CRITICAL
- Centralized log aggregation
- Full-text search

### Alerting (Prometheus Alerts)
- Container down
- High memory/CPU usage
- Database connection issues
- Error rate spikes

### Dashboards (Grafana)
- System overview (all services)
- Business metrics (users, matches, engagement)
- Database performance
- Container resources

---

## Disaster Recovery

### Backup Strategy
```bash
# Database backup (daily cron recommended)
docker compose exec db pg_dump -U dating dating | gzip > backup-$(date +%Y%m%d).sql.gz

# Volume backup
docker run --rm -v dating_postgres_data:/data -v $(pwd):/backup alpine tar czf /backup/postgres_data.tar.gz /data
```

### Recovery Procedure
```bash
# Restore database
gunzip < backup-20240101.sql.gz | docker compose exec -T db psql -U dating dating

# Restore volume
docker run --rm -v dating_postgres_data:/data -v $(pwd):/backup alpine tar xzf /backup/postgres_data.tar.gz -C /
```

### RTO/RPO
- **RTO** (Recovery Time Objective): < 15 минут
- **RPO** (Recovery Point Objective): < 24 часа (daily backups)

---

## Future Architecture

См. [ROADMAP.md](../ROADMAP.md) для планируемых архитектурных изменений:
- Microservices separation
- Event-driven architecture
- GraphQL API
- Mobile app backends
- Redis caching layer
- CDN integration

---

## Технические решения и обоснования

### Почему aiogram?
- Современный async framework
- Type hints support
- Отличная документация
- Active community

### Почему PostgreSQL?
- JSONB для гибких данных (interests)
- Robust и production-ready
- Отличная производительность
- GIN индексы для JSONB

### Почему Docker Compose?
- Простота локальной разработки
- Декларативная конфигурация
- Легко мигрировать на Kubernetes
- Built-in networking

### Почему Traefik?
- Автоматический HTTPS
- Динамическая конфигурация
- Docker-native
- Excellent для микросервисов

---

**Документация обновлена**: 2024-12-21
