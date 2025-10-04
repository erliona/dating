# 💕 Dating - Приложение для знакомств в Telegram

**Современное полнофункциональное приложение для знакомств**, реализованное как Telegram Mini App с микросервисной архитектурой.

[![Tests](https://github.com/erliona/dating/actions/workflows/test.yml/badge.svg)](https://github.com/erliona/dating/actions/workflows/test.yml)
[![Code Quality](https://github.com/erliona/dating/actions/workflows/lint.yml/badge.svg)](https://github.com/erliona/dating/actions/workflows/lint.yml)
[![Docker Build](https://github.com/erliona/dating/actions/workflows/docker-build.yml/badge.svg)](https://github.com/erliona/dating/actions/workflows/docker-build.yml)
[![Deploy](https://github.com/erliona/dating/actions/workflows/deploy-microservices.yml/badge.svg)](https://github.com/erliona/dating/actions/workflows/deploy-microservices.yml)

---

## 📋 Содержание

- [О проекте](#о-проекте)
- [Возможности](#возможности)
- [Архитектура](#архитектура)
- [Быстрый старт](#быстрый-старт)
- [Установка и настройка](#установка-и-настройка)
- [Разработка](#разработка)
- [Тестирование](#тестирование)
- [Развертывание](#развертывание)
- [API документация](#api-документация)
- [Мониторинг](#мониторинг)
- [Безопасность](#безопасность)
- [Решение проблем](#решение-проблем)
- [Вклад в проект](#вклад-в-проект)

---

## 📖 О проекте

Dating - это современное приложение для знакомств, полностью интегрированное в экосистему Telegram. Приложение не требует установки, работает как Mini App прямо в мессенджере и использует встроенную авторизацию Telegram.

### Для кого этот проект?

- **Пользователи** - простой и удобный способ знакомиться в Telegram
- **Разработчики** - пример современного production-ready приложения
- **Предприниматели** - готовая база для запуска dating-сервиса

### Технологические особенности

- 🏗️ **Микросервисная архитектура** - масштабируемость и независимость компонентов
- 🐳 **Docker** - полная контейнеризация, простое развертывание
- 🔐 **Безопасность** - JWT токены, HTTPS, валидация данных
- 📊 **Мониторинг** - Prometheus, Grafana, Loki
- 🧪 **Тестирование** - 288+ тестов с высоким покрытием
- 🚀 **CI/CD** - полный pipeline: тесты, линтинг, сборка, деплой и мониторинг

---

## ✨ Возможности

### 👤 Профили пользователей

**Создание и управление профилем:**
- Имя, возраст (18+), пол
- Сексуальная ориентация
- Цели знакомства
- Биография (до 500 символов)
- До 3 фотографий (JPEG/PNG/WebP, до 5MB)
- Геолокация с приватностью (geohash, ~5км точность)

**Настройки приватности:**
- Скрыть возраст
- Скрыть расстояние
- Скрыть статус онлайн

### 🔍 Поиск и матчинг

**Просмотр анкет:**
- Карточная система
- Фильтры по возрасту, расстоянию, целям
- Информация: фото, имя, возраст, био, расстояние

**Действия:**
- ❤️ Лайк - проявить симпатию
- ✖️ Дизлайк - пропустить
- ⭐ Суперлайк - особая симпатия
- 🌟 Избранное - сохранить профиль

**Матчинг:**
- Автоматическое создание матча при взаимном лайке
- Уведомления о новых матчах
- Список всех матчей

### 💬 Взаимодействие

- Список матчей с взаимными симпатиями
- История взаимодействий
- Управление настройками

### 🔐 Безопасность

- Валидация возраста 18+
- JWT аутентификация
- HMAC валидация Telegram данных
- Rate limiting
- HTTPS everywhere
- Автоматический NSFW детектор фотографий

---

## 🏗️ Архитектура

Приложение построено на **микросервисной архитектуре** с четким разделением ответственности.

### Основные компоненты

```
┌─────────────────┐
│  Telegram Bot   │ ← Пользователи взаимодействуют через Telegram
└────────┬────────┘
         │
┌────────▼────────┐
│  API Gateway    │ ← Единая точка входа (порт 8080)
│  (маршрутизация)│
└────────┬────────┘
         │
    ┌────┴──────────────────────────┐
    │    Микросервисы (независимые) │
    ├───────────────────────────────┤
    │ • Auth Service     (8081)     │ ← JWT токены, валидация
    │ • Profile Service  (8082)     │ ← Профили, CRUD
    │ • Discovery Service(8083)     │ ← Поиск, матчинг
    │ • Media Service    (8084)     │ ← Фото, NSFW детектор
    │ • Chat Service     (8085)     │ ← Сообщения, real-time
    └───────────────────────────────┘
              │
    ┌─────────▼──────────┐
    │   PostgreSQL DB    │ ← Данные
    └────────────────────┘
```

### Структура проекта

```
dating/
├── core/                  # Платформонезависимая бизнес-логика
│   ├── models/           # Доменные модели (User, Profile, Match)
│   ├── services/         # Сервисы (ProfileService, MatchingService)
│   ├── interfaces/       # Контракты для адаптеров
│   └── utils/            # Утилиты (validation, security)
│
├── services/             # Микросервисы
│   ├── auth/            # Аутентификация
│   ├── profile/         # Профили
│   ├── discovery/       # Поиск и матчинг
│   ├── media/           # Медиа файлы
│   └── chat/            # Чат
│
├── gateway/             # API Gateway
│   └── main.py         # Маршрутизация запросов
│
├── adapters/            # Платформенные адаптеры
│   └── telegram/       # Интеграция с Telegram
│
├── webapp/              # Frontend (Mini App)
│   ├── index.html      # Главная страница
│   ├── js/             # JavaScript
│   └── css/            # Стили
│
├── tests/               # Тесты
├── migrations/          # DB миграции (Alembic)
├── monitoring/          # Конфигурация мониторинга
└── docker-compose.yml   # Оркестрация контейнеров
```

### Технологический стек

**Backend:**
- Python 3.11+
- aiogram 3.x (Telegram Bot Framework)
- SQLAlchemy 2.0 + asyncpg (ORM)
- Alembic (миграции БД)
- aiohttp (HTTP сервер)

**Frontend:**
- HTML5/CSS3/JavaScript
- Telegram WebApp API
- Адаптивный дизайн

**Инфраструктура:**
- Docker & Docker Compose
- PostgreSQL 15
- Traefik 2.11 (reverse proxy, HTTPS)
- Let's Encrypt (SSL)

**Мониторинг:**
- Prometheus (метрики)
- Grafana (визуализация)
- Loki (логи)
- cAdvisor (контейнеры)

---

## 🚀 Быстрый старт

### Предварительные требования

- Docker 20.10+
- Docker Compose v2.0+
- Telegram Bot Token (получить у [@BotFather](https://t.me/BotFather))

### Локальный запуск

```bash
# 1. Клонировать репозиторий
git clone https://github.com/erliona/dating.git
cd dating

# 2. Настроить переменные окружения
cp .env.example .env
nano .env  # Отредактировать BOT_TOKEN и другие параметры

# 3. Запустить все сервисы
docker compose up -d

# 4. Проверить статус
docker compose ps

# 5. Проверить health каждого сервиса
for port in 8080 8081 8082 8083 8084 8085; do
  echo "Checking port $port..."
  curl http://localhost:$port/health
done

# 6. Просмотреть логи
docker compose logs -f
```

### Проверка работы

1. Откройте Telegram
2. Найдите своего бота
3. Отправьте `/start`
4. Нажмите "🚀 Открыть Mini App"
5. Создайте профиль

---

## ⚙️ Установка и настройка

### Переменные окружения

#### Обязательные

| Переменная | Описание | Пример |
|------------|----------|--------|
| `BOT_TOKEN` | Токен бота от @BotFather | `123456789:ABCdef...` |
| `POSTGRES_DB` | Имя БД | `dating` |
| `POSTGRES_USER` | Пользователь БД | `dating` |
| `POSTGRES_PASSWORD` | Пароль БД | `SecurePass123` |

#### Опциональные

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `JWT_SECRET` | Секрет для JWT | Генерируется автоматически |
| `WEBAPP_URL` | URL Mini App | `https://localhost` |
| `DOMAIN` | Домен для HTTPS | `localhost` |
| `ACME_EMAIL` | Email для Let's Encrypt | `admin@example.com` |
| `NSFW_THRESHOLD` | Порог NSFW детектора | `0.7` |

Полный список переменных см. в `.env.example`.

### Настройка бота в BotFather

1. Создайте бота у [@BotFather](https://t.me/BotFather)
2. Настройте команды:
```
start - Начать использование бота
help - Получить помощь
```

3. Настройте Mini App:
```
/newapp
<выберите вашего бота>
<название приложения>
<описание>
<URL вашего Mini App>
```

---

## 💻 Разработка

### Локальная разработка

```bash
# Создать виртуальное окружение
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

# Установить зависимости
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Настроить pre-commit хуки (опционально)
pre-commit install

# Запустить базу данных
docker compose up -d db

# Применить миграции
alembic upgrade head

# Запустить отдельные сервисы для разработки
python -m services.auth.main
python -m services.profile.main
# и т.д.
```

### Структура кода

**Core (Бизнес-логика):**
- `core/models/` - Доменные модели (User, Profile, Match, etc.)
- `core/services/` - Бизнес-логика (ProfileService, MatchingService)
- `core/interfaces/` - Абстрактные интерфейсы для адаптеров
- `core/utils/` - Утилиты (validation, security, geohash)

**Services (Микросервисы):**
- `services/auth/` - Аутентификация и JWT
- `services/profile/` - CRUD операции с профилями
- `services/discovery/` - Поиск партнеров и матчинг
- `services/media/` - Загрузка и обработка фотографий
- `services/chat/` - Чат и сообщения

**Adapters (Интеграции):**
- `adapters/telegram/` - Telegram Bot и Mini App интеграция

### Добавление нового микросервиса

```python
# services/new_service/main.py
from aiohttp import web
import logging

logger = logging.getLogger(__name__)

async def health_check(request: web.Request) -> web.Response:
    return web.json_response({'status': 'healthy'})

async def example_endpoint(request: web.Request) -> web.Response:
    return web.json_response({'message': 'Hello'})

def create_app() -> web.Application:
    app = web.Application()
    app.router.add_get('/health', health_check)
    app.router.add_get('/example', example_endpoint)
    return app

if __name__ == '__main__':
    app = create_app()
    web.run_app(app, host='0.0.0.0', port=8086)
```

Добавьте в `docker-compose.yml`:
```yaml
new-service:
  build:
    context: .
    dockerfile: Dockerfile
  command: python -m services.new_service.main
  ports:
    - "8086:8086"
  environment:
    - DATABASE_URL=${BOT_DATABASE_URL}
  depends_on:
    - db
```

---

## 🧪 Тестирование

### Запуск тестов

```bash
# Все тесты
pytest

# С покрытием
pytest --cov=core --cov=services --cov-report=html

# Конкретный файл
pytest tests/core/test_profile_service.py

# С подробным выводом
pytest -v

# Остановиться на первой ошибке
pytest -x
```

### Структура тестов

```
tests/
├── core/                  # Тесты бизнес-логики
│   ├── test_models.py
│   ├── test_profile_service.py
│   └── test_matching_service.py
├── services/              # Тесты микросервисов
│   ├── test_auth.py
│   ├── test_profile.py
│   └── test_discovery.py
└── integration/           # Интеграционные тесты
    └── test_full_flow.py
```

### Написание тестов

```python
import pytest
from core.services.profile_service import ProfileService

@pytest.fixture
async def profile_service():
    # Setup
    service = ProfileService()
    yield service
    # Teardown

async def test_create_profile(profile_service):
    profile_data = {
        'name': 'John',
        'age': 25,
        'gender': 'male'
    }
    profile = await profile_service.create_profile(profile_data)
    assert profile.name == 'John'
    assert profile.age == 25
```

---

## 🚢 Развертывание

> 📚 **Полное руководство по CI/CD**: [docs/CI_CD_GUIDE.md](docs/CI_CD_GUIDE.md)

### CI/CD Pipeline

Проект имеет полностью автоматизированный CI/CD pipeline:

#### Workflows

1. **Tests** - Автоматическое тестирование на каждый push/PR
2. **Code Quality** - Проверка форматирования, линтинг, безопасность
3. **Docker Build** - Валидация сборки всех сервисов
4. **PR Validation** - Комплексная проверка перед merge
5. **Deploy** - Автоматический деплой на production
6. **Health Check** - Периодический мониторинг работоспособности

### Production развертывание через GitHub Actions

#### 1. Настройка GitHub Secrets

Перейдите в **Settings → Secrets and variables → Actions** и добавьте:

**Обязательные секреты:**

| Secret | Описание | Пример |
|--------|----------|--------|
| `DEPLOY_HOST` | IP или hostname сервера | `123.45.67.89` |
| `DEPLOY_USER` | SSH пользователь с sudo | `ubuntu` |
| `DEPLOY_SSH_KEY` | Приватный SSH ключ | `-----BEGIN RSA...` |
| `BOT_TOKEN` | Telegram bot token | `123456789:ABC...` |
| `JWT_SECRET` | Секрет для JWT (32+ символов) | `random_secret_32+` |

**Опциональные для HTTPS:**

| Secret | Описание | Пример |
|--------|----------|--------|
| `DOMAIN` | Ваш домен для HTTPS | `dating.example.com` |
| `ACME_EMAIL` | Email для Let's Encrypt | `admin@example.com` |

#### 2. Автоматический деплой

```bash
# Push в main ветку автоматически запустит полный pipeline:
git push origin main
```

**Pipeline выполнит:**
1. ✅ Запуск всех тестов
2. ✅ Валидацию Docker образов
3. ✅ Сборку всех сервисов
4. ✅ Деплой на сервер
5. ✅ Проверку работоспособности (health checks)
6. ✅ Верификацию всех сервисов

**Или запустите вручную:**
- Actions → Deploy to Production → Run workflow

#### 3. Проверка деплоя

```bash
# SSH на сервер
ssh user@your-server

# Проверить статус
cd /opt/dating
docker compose ps

# Проверить логи
docker compose logs -f
```

### Ручное развертывание

```bash
# На сервере
git clone https://github.com/erliona/dating.git
cd dating

# Настроить .env
cp .env.example .env
nano .env

# Запустить
docker compose up -d

# Проверить
docker compose ps
curl http://localhost:8080/health
```

### HTTPS и SSL

HTTPS настраивается автоматически через Traefik и Let's Encrypt:

1. Укажите `DOMAIN` в `.env`
2. Укажите `ACME_EMAIL` в `.env`
3. Запустите: `docker compose up -d`
4. Traefik автоматически получит SSL сертификат

**Важно:**
- Домен должен указывать на ваш сервер (A запись)
- Порты 80 и 443 должны быть открыты
- Email нужен для уведомлений о продлении сертификата

### Обновление приложения

```bash
# На сервере
cd /opt/dating
git pull
docker compose pull
docker compose up -d
```

**Важно:** Данные в БД сохраняются в Docker volumes и не удаляются при обновлении.

### Резервное копирование

```bash
# Создать backup БД
docker compose exec db pg_dump -U dating dating > backup_$(date +%Y%m%d).sql

# Создать backup фотографий
docker compose exec media-service tar czf - /app/photos > photos_backup_$(date +%Y%m%d).tar.gz

# Восстановить БД из backup
docker compose exec -T db psql -U dating dating < backup_20240101.sql
```

---

## 📡 API документация

### API Gateway (порт 8080)

Единая точка входа для всех запросов.

**Маршрутизация:**
- `/auth/*` → Auth Service (8081)
- `/profiles/*` → Profile Service (8082)
- `/discovery/*` → Discovery Service (8083)
- `/media/*` → Media Service (8084)
- `/chat/*` → Chat Service (8085)

### Auth Service (8081)

**Аутентификация и JWT токены**

```http
POST /auth/telegram
Content-Type: application/json

{
  "initData": "user=...", 
  "hash": "..."
}

Response: 200 OK
{
  "access_token": "eyJ...",
  "token_type": "Bearer"
}
```

### Profile Service (8082)

**Управление профилями**

```http
# Создать профиль
POST /profiles/
Authorization: Bearer {token}
Content-Type: application/json

{
  "name": "John",
  "age": 25,
  "gender": "male",
  "bio": "Hello world"
}

# Получить профиль
GET /profiles/{user_id}
Authorization: Bearer {token}

# Обновить профиль
PUT /profiles/{user_id}
Authorization: Bearer {token}
Content-Type: application/json

{
  "bio": "Updated bio"
}

# Удалить профиль
DELETE /profiles/{user_id}
Authorization: Bearer {token}
```

### Discovery Service (8083)

**Поиск и матчинг**

```http
# Получить рекомендации
GET /discovery/recommendations?limit=10&age_min=21&age_max=30
Authorization: Bearer {token}

# Лайкнуть профиль
POST /discovery/like
Authorization: Bearer {token}
Content-Type: application/json

{
  "target_user_id": 123
}

# Дизлайк
POST /discovery/dislike
Authorization: Bearer {token}
Content-Type: application/json

{
  "target_user_id": 123
}

# Получить матчи
GET /discovery/matches
Authorization: Bearer {token}
```

### Media Service (8084)

**Загрузка и обработка фотографий**

```http
# Загрузить фото
POST /media/photos
Authorization: Bearer {token}
Content-Type: multipart/form-data

file: <binary>

Response: 200 OK
{
  "photo_id": "abc123",
  "url": "/media/photos/abc123.jpg",
  "nsfw_score": 0.05
}

# Получить фото
GET /media/photos/{photo_id}

# Удалить фото
DELETE /media/photos/{photo_id}
Authorization: Bearer {token}
```

### Chat Service (8085)

**Чат и сообщения**

```http
# Получить список чатов
GET /chat/conversations
Authorization: Bearer {token}

# Получить сообщения
GET /chat/conversations/{match_id}/messages?limit=50
Authorization: Bearer {token}

# Отправить сообщение
POST /chat/conversations/{match_id}/messages
Authorization: Bearer {token}
Content-Type: application/json

{
  "text": "Hello!"
}
```

### Коды ответов

| Код | Описание |
|-----|----------|
| 200 | OK |
| 201 | Created |
| 400 | Bad Request (невалидные данные) |
| 401 | Unauthorized (нет/невалидный токен) |
| 403 | Forbidden (нет прав доступа) |
| 404 | Not Found |
| 422 | Unprocessable Entity (ошибка валидации) |
| 429 | Too Many Requests (rate limit) |
| 500 | Internal Server Error |

---

## 📊 Мониторинг

Мониторинг интегрирован и запускается автоматически. **Новые дашборды обновлены в январе 2025!**

### Доступ к дашбордам

```bash
# Запустить все с мониторингом
docker compose up -d

# URLs
http://localhost:3000    # Grafana (admin/admin)
http://localhost:9090    # Prometheus
http://localhost:8090    # cAdvisor
http://localhost:3100    # Loki
```

### Что отслеживается

**Метрики (Prometheus):**
- CPU, Memory, Network всех контейнеров
- Активные соединения к БД
- Производительность запросов
- Системные метрики (load average, disk I/O)
- Метрики PostgreSQL (transactions, cache hit rate)

**Логи (Loki):**
- Все логи всех сервисов
- JSON структурированные логи
- Фильтрация по уровню, сервису, контейнеру
- Поиск по событиям и сообщениям

**Контейнеры (cAdvisor):**
- Использование ресурсов каждым контейнером
- Сетевой трафик
- Файловая система

### Grafana дашборды

**Новые дашборды (январь 2025):**
1. **Infrastructure Overview** - Системные метрики, контейнеры, I/O, load average
2. **Application Services** - Статус микросервисов, CPU/Memory, рестарты
3. **Application Logs** - Централизованные логи, ошибки, предупреждения
4. **Database Metrics** - PostgreSQL: connections, queries, cache, transactions

### Полная документация

Подробные инструкции по использованию мониторинга:
- 📚 [Полная документация по мониторингу](docs/MONITORING_SETUP.md)
- 🔌 [Карта портов всех сервисов](docs/PORT_MAPPING.md)
- 📋 [Сводка обновления мониторинга](MONITORING_REFRESH_SUMMARY.md)

### Просмотр логов

```bash
# Все логи
docker compose logs -f

# Конкретный сервис
docker compose logs -f profile-service

# Последние 100 строк
docker compose logs --tail=100 auth-service

# Фильтр по уровню (через Grafana/Loki)
{service_name="profile-service"} |= "ERROR"
```

---

## �� Безопасность

### Аутентификация

**Telegram WebApp Data:**
- HMAC-SHA256 валидация данных
- Проверка подписи и таймстемпа
- Защита от replay атак

**JWT Tokens:**
- Время жизни токена: 24 часа
- Refresh tokens: 30 дней
- Автоматическое обновление

### Валидация данных

- Возраст 18+ обязательно
- Санитизация пользовательского ввода
- Защита от SQL инъекций (ORM)
- XSS защита

### Rate Limiting

Защита от злоупотреблений:
- API: 100 запросов/минуту на пользователя
- Регистрация: 5 попыток/час
- Фото загрузка: 10 фото/час
- Лайки: 100 лайков/день

### HTTPS

- Автоматические SSL сертификаты (Let's Encrypt)
- Принудительное перенаправление с HTTP на HTTPS
- HSTS заголовки
- Secure cookies

### NSFW детектор

Автоматическая проверка фотографий:
- Модель: NudeNet
- Порог: 0.7 (настраивается)
- Автоматическое отклонение неподходящих фото

### Приватность

- Геолокация хранится как geohash (~5км точность)
- Настройки приватности (скрыть возраст/расстояние/онлайн)
- Пароли не хранятся (Telegram авторизация)
- GDPR совместимость

### Обновления безопасности

```bash
# Проверка уязвимостей
pip-audit

# Обновление зависимостей
pip install --upgrade -r requirements.txt

# Пересборка образов
docker compose build --no-cache
docker compose up -d
```

---

## 🐛 Решение проблем

### Бот не отвечает

```bash
# Проверить логи
docker compose logs -f telegram-bot

# Проверить статус
docker compose ps telegram-bot

# Перезапустить
docker compose restart telegram-bot

# Проверить токен
echo $BOT_TOKEN
```

**Причины:**
- Неверный BOT_TOKEN
- Бот заблокирован или удален
- Проблемы с сетью

### База данных не подключается

```bash
# Проверить статус
docker compose ps db

# Проверить логи
docker compose logs db

# Проверить подключение
docker compose exec db psql -U dating -d dating -c "SELECT 1"

# Проверить пароль
echo $POSTGRES_PASSWORD
```

**Причины:**
- БД не запущена
- Неверные credentials
- Порт занят

### Сервис не стартует

```bash
# Проверить все сервисы
docker compose ps

# Найти проблемный сервис
docker compose logs {service-name}

# Проверить health endpoint
curl http://localhost:808X/health

# Пересоздать контейнер
docker compose up -d --force-recreate {service-name}
```

### HTTPS не работает

```bash
# Проверить Traefik логи
docker compose logs traefik

# Проверить сертификаты
docker compose exec traefik ls -la /letsencrypt/

# Проверить DNS
nslookup your-domain.com

# Проверить порты
netstat -tulpn | grep -E ':(80|443)'
```

**Требования:**
- Домен должен указывать на сервер
- Порты 80 и 443 открыты
- ACME_EMAIL и DOMAIN в .env

### Фото не загружаются

```bash
# Проверить media service
docker compose logs media-service

# Проверить директорию
docker compose exec media-service ls -la /app/photos

# Проверить права
docker compose exec media-service chmod 755 /app/photos
```

### Мониторинг не работает

```bash
# Проверить Prometheus
curl http://localhost:9090/-/healthy

# Проверить Grafana
curl http://localhost:3000/api/health

# Перезапустить
docker compose restart prometheus grafana loki
```

### Полный сброс (ОСТОРОЖНО!)

```bash
# ВНИМАНИЕ: Удалит ВСЕ данные!
docker compose down -v
docker compose up -d

# С сохранением данных
docker compose down
docker compose up -d
```

---

## 🤝 Вклад в проект

Мы приветствуем ваш вклад! Вот как вы можете помочь:

### Процесс контрибуции

1. **Fork** репозитория
2. **Клонируйте** ваш fork:
   ```bash
   git clone https://github.com/YOUR_USERNAME/dating.git
   ```
3. **Создайте ветку** для вашей фичи:
   ```bash
   git checkout -b feature/amazing-feature
   ```
4. **Внесите изменения** и **добавьте тесты**
5. **Проверьте**, что тесты проходят:
   ```bash
   pytest
   ```
6. **Commit** с понятным сообщением:
   ```bash
   git commit -m "Add amazing feature"
   ```
7. **Push** в вашу ветку:
   ```bash
   git push origin feature/amazing-feature
   ```
8. **Откройте Pull Request**

### Гайдлайны

**Код:**
- Следуйте PEP 8
- Пишите docstrings
- Добавляйте type hints
- Покрывайте код тестами

**Commits:**
- Используйте понятные сообщения
- Один commit = одна логическая единица
- Ссылайтесь на issues если есть

**Pull Requests:**
- Опишите, что изменено и почему
- Добавьте скриншоты для UI изменений
- Убедитесь, что CI проходит

### Что можно улучшить

**Приоритетные задачи:**
- [ ] Real-time чат через WebSocket
- [ ] Push уведомления
- [ ] Видео профили
- [ ] Верификация профилей
- [ ] Премиум функции

**Другие идеи:**
- Улучшение UI/UX
- Оптимизация производительности
- Дополнительная документация
- Интеграции (Stripe, S3, etc.)
- Локализация (i18n)

См. [Issues](https://github.com/erliona/dating/issues) для списка задач.

### Сообщество

- 📖 [Документация](https://github.com/erliona/dating)
- 🐛 [Issues](https://github.com/erliona/dating/issues)
- 💬 [Discussions](https://github.com/erliona/dating/discussions)
- 📧 [Email](mailto:support@example.com)

---

## 📄 Лицензия

Этот проект распространяется под лицензией **MIT**. См. файл [LICENSE](LICENSE) для деталей.

Это означает, что вы можете:
- ✅ Использовать коммерчески
- ✅ Модифицировать
- ✅ Распространять
- ✅ Использовать приватно

При условии сохранения копирайта и лицензии.

---

## 📞 Поддержка и контакты

**Документация:**
- README (этот файл)
- [GitHub Wiki](https://github.com/erliona/dating/wiki)

**Получить помощь:**
- 🐛 [Создать Issue](https://github.com/erliona/dating/issues/new)
- 💬 [GitHub Discussions](https://github.com/erliona/dating/discussions)
- 📧 Email: support@example.com

**Отчет о уязвимостях:**
- Не создавайте публичные issues
- Напишите на security@example.com
- См. [SECURITY.md](SECURITY.md)

---

## 🙏 Благодарности

Спасибо всем, кто внес вклад в этот проект:
- Все контрибьюторы
- Сообщество Telegram
- Open source проекты, которые мы используем

**Используемые библиотеки:**
- aiogram - Telegram Bot Framework
- SQLAlchemy - ORM
- aiohttp - HTTP сервер
- FastAPI - (планируется)
- И многие другие...

---

## 📈 Статистика проекта

- ⭐ Stars: [![Stars](https://img.shields.io/github/stars/erliona/dating)](https://github.com/erliona/dating/stargazers)
- 🍴 Forks: [![Forks](https://img.shields.io/github/forks/erliona/dating)](https://github.com/erliona/dating/network)
- 🐛 Issues: [![Issues](https://img.shields.io/github/issues/erliona/dating)](https://github.com/erliona/dating/issues)
- 📝 Commits: [![Commits](https://img.shields.io/github/commit-activity/m/erliona/dating)](https://github.com/erliona/dating/commits)

---

**Сделано с ❤️ для сообщества**

*Если проект оказался полезным, поставьте ⭐ на GitHub!*

---

**Версия документации:** 2.0  
**Последнее обновление:** 2025-01-15  
**Автор:** erliona
