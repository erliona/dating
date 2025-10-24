# 💕 Dating - Telegram Mini App для знакомств

**Современное приложение для знакомств**, полностью интегрированное в Telegram как Mini App с микросервисной архитектурой.

[![Tests](https://github.com/erliona/dating/actions/workflows/test.yml/badge.svg)](https://github.com/erliona/dating/actions/workflows/test.yml)
[![Code Quality](https://github.com/erliona/dating/actions/workflows/lint.yml/badge.svg)](https://github.com/erliona/dating/actions/workflows/lint.yml)
[![Docker Build](https://github.com/erliona/dating/actions/workflows/docker-build.yml/badge.svg)](https://github.com/erliona/dating/actions/workflows/docker-build.yml)
[![Deploy](https://github.com/erliona/dating/actions/workflows/deploy-microservices.yml/badge.svg)](https://github.com/erliona/dating/actions/workflows/deploy-microservices.yml)

---

## 📋 Содержание

- [О проекте](#о-проекте)
- [Архитектура](#архитектура)
- [Технологический стек](#технологический-стек)
- [Быстрый старт](#быстрый-старт)
- [Установка](#установка)
- [Разработка](#разработка)
- [Тестирование](#тестирование)
- [Развертывание](#развертывание)
- [Мониторинг](#мониторинг)
- [Безопасность](#безопасность)
- [API](#api)
- [Документация](#документация)

---

## 🎯 О проекте

Dating - это приложение для знакомств, работающее как Telegram Mini App. Пользователи могут создавать профили, искать партнеров, общаться и встречаться.

### Основные возможности

- **Профили пользователей** - создание, редактирование, фото
- **Поиск и матчинг** - алгоритм подбора совместимых партнеров
- **Чат** - общение между совпавшими пользователями
- **Административная панель** - модерация и управление
- **Мониторинг** - полная система наблюдения за системой

### Ключевые особенности

- 🏗️ **8 микросервисов** - масштабируемая архитектура
- 🐳 **Docker** - полная контейнеризация
- 🔐 **JWT аутентификация** - безопасность и rate limiting
- 📊 **Мониторинг** - Prometheus, Grafana, Loki
- 🧪 **18 тестовых файлов** - ~3,600 строк тестов
- 🚀 **CI/CD** - автоматизированный pipeline

---

## 🏗️ Архитектура

### Микросервисы

```
┌─────────────────┐
│  Telegram Bot   │ ← Команды и уведомления
└────────┬────────┘
         │
┌────────▼────────┐        ┌─────────────────┐
│ Notification    │◄───────│  Telegram       │
│ Service (8087)  │        │  WebApp         │ ← Основной интерфейс
└────────┬────────┘        └────────┬────────┘
         │                          │
┌────────▼──────────────────────────▼────────┐
│           API Gateway (8080)                │ ← Единая точка входа
└────────┬────────────────────────────────────┘
         │
    ┌────┴──────────────────────────┐
    │    Микросервисы               │
    ├───────────────────────────────┤
    │ • Auth Service      (8081)    │ ← JWT токены
    │ • Profile Service   (8082)    │ ← Профили пользователей
    │ • Discovery Service (8083)    │ ← Поиск и матчинг
    │ • Media Service     (8084)    │ ← Фото и файлы
    │ • Chat Service      (8085)    │ ← Сообщения
    │ • Admin Service     (8086)    │ ← Админ панель
    │ • Notification Svc  (8087)    │ ← Push уведомления
    │ • Data Service      (8088)    │ ← Централизованный доступ к БД
    └───────────────────────────────┘
              │
    ┌─────────▼──────────┐
    │   PostgreSQL DB    │ ← База данных
    └────────────────────┘
```

### Структура проекта

```
dating/
├── bot/                  # Telegram Bot
│   ├── main.py          # Точка входа бота
│   ├── config.py        # Конфигурация
│   ├── db.py            # Модели БД
│   ├── repository.py    # Доступ к данным
│   └── cache.py         # Кэширование
│
├── core/                # Общие компоненты
│   ├── middleware/      # Middleware
│   │   ├── jwt_middleware.py      # JWT аутентификация
│   │   ├── metrics_middleware.py  # Prometheus метрики
│   │   └── request_logging.py    # Логирование запросов
│   └── utils/           # Утилиты
│       ├── logging.py   # Настройка логирования
│       ├── security.py  # Безопасность
│       └── validation.py # Валидация данных
│
├── services/            # Микросервисы (8 штук)
│   ├── auth/           # Аутентификация (8081)
│   ├── profile/        # Профили (8082)
│   ├── discovery/      # Поиск (8083)
│   ├── media/          # Медиа (8084)
│   ├── chat/           # Чат (8085)
│   ├── admin/          # Админка (8086)
│   ├── notification/   # Уведомления (8087)
│   └── data/           # Данные (8088)
│
├── gateway/             # API Gateway
│   └── main.py         # Маршрутизация
│
├── webapp/              # Frontend (HTML/CSS/JS)
│   ├── index.html      # Главная страница
│   ├── admin.html      # Админ панель
│   ├── css/            # Стили
│   ├── js/             # JavaScript
│   └── nginx.conf      # Конфигурация Nginx
│
│   ├── src/            # React компоненты
│   ├── package.json    # Next.js 15.5.4, React 19
│   └── ...
│
├── tests/               # Тесты (18 файлов)
│   ├── unit/           # Unit тесты
│   ├── integration/    # Integration тесты
│   └── e2e/            # End-to-end тесты
│
├── monitoring/          # Мониторинг
│   ├── grafana/        # Дашборды Grafana
│   ├── prometheus/     # Конфигурация Prometheus
│   ├── loki/           # Конфигурация Loki
│   └── promtail/       # Конфигурация Promtail
│
├── migrations/          # Миграции БД (Alembic)
├── scripts/             # Скрипты развертывания
└── docker-compose.yml   # Оркестрация контейнеров
```

---

## 🛠️ Технологический стек

### Backend

- **Python 3.11+** - основной язык
- **aiogram 3.3** - Telegram Bot Framework
- **SQLAlchemy 2.0+** - ORM
- **asyncpg 0.29+** - PostgreSQL драйвер
- **aiohttp 3.9+** - HTTP сервер для микросервисов
- **Alembic 1.13+** - миграции БД
- **PyJWT 2.8+** - JWT токены
- **bcrypt 4.0+** - хеширование паролей
- **prometheus-client 0.19+** - метрики

### Frontend

**Основной (webapp/):**
- **HTML/CSS/JavaScript** - vanilla
- **Nginx** - веб-сервер
- **Telegram WebApp SDK** - интеграция с Telegram


### Инфраструктура

- **Docker & Docker Compose** - контейнеризация
- **PostgreSQL 15** - база данных
- **Traefik 2.11** - reverse proxy
- **Let's Encrypt** - SSL сертификаты

### Мониторинг

- **Prometheus 2.51** - сбор метрик
- **Grafana 10.4** - визуализация
- **Loki 3.0** - сбор логов
- **cAdvisor** - метрики контейнеров
- **Node Exporter** - системные метрики

---

## 🚀 Быстрый старт

### Предварительные требования

- Docker 20.10+
- Docker Compose v2.0+
- Telegram Bot Token

### Локальный запуск

```bash
# 1. Клонировать репозиторий
git clone https://github.com/erliona/dating.git
cd dating

# 2. Настроить переменные окружения
cp .env.example .env
nano .env  # Отредактировать BOT_TOKEN

# 3. Запустить все сервисы (без мониторинга)
./scripts/dev-start.sh

# 4. Проверить статус
docker compose ps

# 5. Проверить health endpoints
curl http://localhost:8080/health  # API Gateway
curl http://localhost:8081/health  # Auth Service
curl http://localhost:8082/health  # Profile Service
# ... и так далее для всех сервисов
```

### Проверка работы

**Telegram Mini App:**
1. Откройте Telegram
2. Найдите своего бота
3. Отправьте `/start`
4. Нажмите "🚀 Открыть Mini App"

**Административная панель:**
1. Откройте http://localhost:8086/admin-panel/index.html
2. Войдите: `admin` / `admin123`

---

## 🌍 Среды разработки

Проект поддерживает **две среды**:

### 🏠 Локальная разработка
- **Без мониторинга** (Prometheus, Grafana, Loki)
- **Локальный домен**: `localhost`
- **Внешний доступ к БД**: порт `5433`
- **Команда**: `./scripts/dev-start.sh`

### 🚀 Продакшн
- **С полным мониторингом** (Prometheus, Grafana, Loki)
- **Продакшн домен**: `dating.serge.cc`
- **SSL сертификаты** (Let's Encrypt)
- **Команда**: `./scripts/deploy-production.sh`

## ⚙️ Установка

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
| `DOMAIN` | Домен для HTTPS | `localhost` |
| `ACME_EMAIL` | Email для Let's Encrypt | `admin@example.com` |

#### Порты сервисов

| Переменная | Сервис | Порт |
|------------|--------|------|
| `GATEWAY_PORT` | API Gateway | 8080 |
| `AUTH_SERVICE_PORT` | Auth Service | 8081 |
| `PROFILE_SERVICE_PORT` | Profile Service | 8082 |
| `DISCOVERY_SERVICE_PORT` | Discovery Service | 8083 |
| `MEDIA_SERVICE_PORT` | Media Service | 8084 |
| `CHAT_SERVICE_PORT` | Chat Service | 8085 |
| `ADMIN_SERVICE_PORT` | Admin Service | 8086 |
| `NOTIFICATION_SERVICE_PORT` | Notification Service | 8087 |
| `DATA_SERVICE_PORT` | Data Service | 8088 |

---

## 💻 Разработка

### Локальная разработка

```bash
# Создать виртуальное окружение
python3 -m venv venv
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Запустить базу данных
docker compose up -d db

# Применить миграции
alembic upgrade head

# Запустить отдельные сервисы
python -m services.auth.main
python -m services.profile.main
```

### Структура кода

**Core (Общие компоненты):**
- `core/middleware/` - JWT, метрики, логирование
- `core/utils/` - утилиты, безопасность, валидация

**Services (Микросервисы):**
- Каждый сервис независим и имеет свой порт
- Все сервисы используют общие middleware
- Data Service - централизованный доступ к БД

**Gateway:**
- Единая точка входа для всех запросов
- Маршрутизация по префиксам

---

## 🧪 Тестирование

### Статистика тестов

- **18 тестовых файлов**
- **~3,600 строк кода тестов**
- **Unit, Integration, E2E тесты**

### Запуск тестов

```bash
# Все тесты
pytest -v

# По типам
pytest tests/unit/ -v          # Unit tests
pytest tests/integration/ -v   # Integration tests
pytest tests/e2e/ -v          # E2E tests

# С покрытием
pytest --cov=bot --cov=core --cov=services --cov-report=html
```

### Структура тестов

```
tests/
├── unit/                  # Unit tests
│   ├── test_config.py
│   ├── test_utils.py
│   └── test_*_timezone.py
├── integration/           # Integration tests
│   ├── test_api.py
│   ├── test_repository.py
│   └── test_monitoring_config.py
└── e2e/                   # End-to-end tests
    ├── test_main.py
    ├── test_admin.py
    ├── test_discovery.py
    ├── test_gateway.py
    ├── test_user_flows.py
    └── test_orientation_filtering.py
```

---

## 🚢 Развертывание

### CI/CD Pipeline

**GitHub Actions workflows:**
- `test.yml` - автоматическое тестирование
- `lint.yml` - проверка качества кода
- `docker-build.yml` - сборка Docker образов
- `deploy-microservices.yml` - деплой на сервер

### Production развертывание

#### 1. Настройка GitHub Secrets

**Обязательные секреты:**
- `DEPLOY_HOST` - IP сервера
- `DEPLOY_USER` - SSH пользователь
- `DEPLOY_SSH_KEY` - приватный SSH ключ
- `BOT_TOKEN` - токен Telegram бота
- `JWT_SECRET` - секрет для JWT
- `POSTGRES_PASSWORD` - пароль БД

**Опциональные:**
- `DOMAIN` - домен для HTTPS
- `ACME_EMAIL` - email для Let's Encrypt

#### 2. Автоматический деплой

```bash
# Push в main ветку автоматически запустит деплой
git push origin main
```

#### 3. Ручное развертывание

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

HTTPS настраивается автоматически через Traefik:

1. Укажите `DOMAIN` в `.env`
2. Укажите `ACME_EMAIL` в `.env`
3. Запустите: `docker compose up -d`
4. Traefik автоматически получит SSL сертификат

---

## 📊 Мониторинг

### Доступ к мониторингу

**Production (dating.serge.cc):**
- **Grafana**: http://dating.serge.cc:3000
- **Prometheus**: http://dating.serge.cc:9090
- **Webapp**: http://dating.serge.cc
- **Admin Panel**: http://dating.serge.cc/admin

**Доступ к Grafana:**
- Пользователь: `admin`
- Пароль: `admin`

### Дашборды Grafana

1. **Infrastructure Overview** - общее состояние системы
2. **System Health** - здоровье сервисов
3. **Application Services** - метрики приложений
4. **Business Metrics** - бизнес-метрики (пользователи, матчи)
5. **API Performance** - производительность API
6. **Application Logs** - логи приложений
7. **Database Infrastructure** - метрики БД
8. **Database Metrics** - детальные метрики PostgreSQL
9. **Security & Authentication** - безопасность

### Что отслеживается

**Метрики (Prometheus):**
- HTTP запросы по сервисам
- Время ответа
- Статус коды
- Бизнес-метрики (users_total, matches_total, messages_total)
- Системные метрики (CPU, память, диск)
- Метрики PostgreSQL

**Логи (Loki):**
- Все логи всех сервисов
- JSON структурированные логи
- Фильтрация по уровню, сервису
- Поиск по событиям

---

## 🔒 Безопасность

### Реализованные меры безопасности

- **JWT аутентификация** - все API endpoints защищены токенами
- **Rate limiting** - защита от brute force атак (5 запросов/5 минут для auth)
- **Input validation** - валидация и санитизация всех входных данных
- **SQL injection защита** - параметризированные запросы через SQLAlchemy ORM
- **CORS ограничения** - доступ только с разрешенных доменов
- **HTTPS enforcement** - принудительное перенаправление на HTTPS
- **Environment variables** - все секреты в переменных окружения
- **Security monitoring** - логирование и мониторинг событий безопасности

### Критические требования для production

⚠️ **ВНИМАНИЕ**: Для production развертывания ОБЯЗАТЕЛЬНО установите:

```bash
# Обязательные переменные окружения
JWT_SECRET=your-strong-jwt-secret-here
POSTGRES_PASSWORD=your-strong-database-password
ADMIN_PASSWORD=your-strong-admin-password
WEBAPP_DOMAIN=https://your-domain.com
```

### Безопасность по умолчанию

- ❌ **Нет дефолтных паролей** - все сервисы требуют явной настройки
- ❌ **Нет test endpoints** - удалены потенциально опасные endpoints
- ❌ **Нет wildcard CORS** - ограничен доступ только к указанным доменам
- ✅ **Валидация входных данных** - все пользовательские данные проверяются
- ✅ **Логирование безопасности** - все события безопасности логируются

### Дополнительная информация

- 📋 **SECURITY.md** - подробная политика безопасности
- 🔍 **Vulnerability reporting** - процесс сообщения об уязвимостях
- 🛡️ **Security best practices** - рекомендации по безопасности

---

## 📡 API

### API Gateway (порт 8080)

Единая точка входа для всех запросов.

**Маршрутизация:**
- `/auth/*` → Auth Service (8081)
- `/profiles/*` → Profile Service (8082)
- `/discovery/*` → Discovery Service (8083)
- `/media/*` → Media Service (8084)
- `/chat/*` → Chat Service (8085)
- `/admin/*` → Admin Service (8086)
- `/data/*` → Data Service (8088)

### Основные endpoints

#### Auth Service (8081)
```http
POST /auth/validate    # Валидация Telegram данных
GET /auth/verify       # Проверка JWT токена
POST /auth/refresh     # Обновление токена
GET /auth/test_token   # Тестовый токен (dev)
```

#### Profile Service (8082)
```http
GET /profiles/{user_id}     # Получить профиль
POST /profiles/             # Создать профиль
PUT /profiles/{user_id}     # Обновить профиль
POST /sync-metrics          # Синхронизация метрик
```

#### Data Service (8088)
```http
GET /data/profiles/{user_id}    # Получить профиль
POST /data/profiles             # Создать профиль
PUT /data/profiles/{user_id}    # Обновить профиль
GET /data/profiles-count        # Количество профилей
```

### Коды ответов

| Код | Описание |
|-----|----------|
| 200 | OK |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 422 | Unprocessable Entity |
| 429 | Too Many Requests |
| 500 | Internal Server Error |

---

## 📚 Документация

### Основная документация

- **[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)** - Архитектура системы
- **[docs/API_DOCUMENTATION.md](docs/API_DOCUMENTATION.md)** - Полная документация API
- **[docs/DEVELOPMENT_GUIDE.md](docs/DEVELOPMENT_GUIDE.md)** - Руководство разработчика
- **[docs/CI_CD_GUIDE.md](docs/CI_CD_GUIDE.md)** - CI/CD pipeline
- **[docs/DEPLOYMENT_GUIDE.md](docs/DEPLOYMENT_GUIDE.md)** - Развертывание

### Специфичные темы

- **[services/admin/README.md](services/admin/README.md)** - Admin Service
- **[tests/README.md](tests/README.md)** - Тестирование
- **[scripts/README.md](scripts/README.md)** - Скрипты

---

## 🤝 Вклад в проект

### Процесс контрибуции

1. **Fork** репозитория
2. **Клонируйте** ваш fork
3. **Создайте ветку** для фичи
4. **Внесите изменения** и добавьте тесты
5. **Проверьте**, что тесты проходят
6. **Commit** с понятным сообщением
7. **Push** в вашу ветку
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

---

## 📄 Лицензия

Этот проект распространяется под лицензией **MIT**.

---

## 📞 Поддержка

**Получить помощь:**
- 🐛 [GitHub Issues](https://github.com/erliona/dating/issues)
- 💬 [GitHub Discussions](https://github.com/erliona/dating/discussions)

**Отчет о уязвимостях:**
- Не создавайте публичные issues
- Напишите на security@example.com

---

## 📈 Статистика проекта

- **Язык**: Python 3.11+
- **Архитектура**: 8 микросервисов
- **Тесты**: 18 файлов, ~3,600 строк
- **Frontend**: HTML/CSS/JS
- **Мониторинг**: Prometheus + Grafana + Loki
- **CI/CD**: 4 GitHub Actions workflows

---

**Сделано с ❤️ для сообщества**

*Если проект оказался полезным, поставьте ⭐ на GitHub!*

---

**Версия документации:** 3.1  
**Последнее обновление:** 2025-10-23  
**Автор:** erliona