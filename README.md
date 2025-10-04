# 💕 Dating Telegram Mini App

**Production-ready dating application** built as a Telegram Mini App with modern infrastructure and best practices.

Полнофункциональное приложение знакомств в Telegram с мини-приложением, поиском партнеров, системой матчинга и обменом сообщениями.

[![CI](https://github.com/erliona/dating/actions/workflows/ci.yml/badge.svg)](https://github.com/erliona/dating/actions/workflows/ci.yml)
[![Deploy](https://github.com/erliona/dating/actions/workflows/deploy.yml/badge.svg)](https://github.com/erliona/dating/actions/workflows/deploy.yml)

---

## ✨ Основные возможности

### 💑 Функции приложения знакомств
- 👤 **Профили пользователей** - создание и редактирование анкет
  - Имя, возраст (18+), пол и ориентация
  - Биография и цели знакомства
  - До 3 фотографий (JPEG/PNG/WebP, до 5MB)
  - Геолокация с приватностью (~5км точность через geohash)
  - Настройки приватности (скрыть возраст/расстояние/онлайн)

- 🔍 **Поиск и знакомства** - карточная система просмотра анкет
  - Поиск партнеров с учетом расстояния и предпочтений
  - Лайки, дизлайки и суперлайки
  - Автоматическое создание матчей при взаимных лайках
  - Система избранного для сохранения интересных профилей
  - Фильтры по возрасту, расстоянию и целям

- 💬 **Взаимодействие** - общение и управление контактами
  - Список матчей с взаимными симпатиями
  - История взаимодействий
  - Управление настройками профиля

- 🔐 **Безопасность и приватность**
  - Валидация возраста 18+
  - JWT аутентификация
  - HMAC валидация данных Telegram
  - Rate limiting для защиты от злоупотреблений
  - Управление приватностью данных

### 🏗️ Техническая инфраструктура
- 🐳 **Docker** - полная контейнеризация
- 🏗️ **Микросервисы** - независимые масштабируемые сервисы (Auth, Profile, Discovery, Media, Chat)
- 🌐 **API Gateway** - единая точка входа с маршрутизацией запросов
- 🔐 **HTTPS** - автоматические SSL сертификаты через Let's Encrypt/Traefik
- 🚀 **CI/CD** - автоматическое тестирование и развертывание через GitHub Actions
- 📈 **Мониторинг** - Prometheus + Grafana + Loki для метрик и логов
- 💾 **PostgreSQL** - надежная база данных с async SQLAlchemy
- 🧪 **Тестирование** - 293 теста с покрытием 81%

---

## 👥 Сценарии использования

### Регистрация и создание профиля
1. **Запуск бота** - пользователь отправляет `/start` боту
2. **Открытие Mini App** - нажатие на кнопку "🚀 Открыть Mini App"
3. **Приветствие** - знакомство с возможностями приложения
4. **Создание анкеты** - заполнение профиля:
   - Имя и дата рождения (18+ обязательно)
   - Пол и ориентация
   - Цели знакомства
   - О себе и местоположение
   - Загрузка до 3 фотографий
5. **Сохранение** - данные сохраняются в базе данных
6. **Подтверждение** - бот отправляет подтверждение создания профиля

### Поиск партнера
1. **Просмотр анкет** - карточки с фотографиями и информацией о пользователях
2. **Оценка профилей** - лайк (❤️), дизлайк (✖️) или суперлайк (⭐)
3. **Матч** - при взаимной симпатии создается матч
4. **Общение** - доступ к контактам совпавших пользователей

### Управление профилем
1. **Мои матчи** - просмотр списка взаимных симпатий
2. **Избранное** - сохраненные интересные профили
3. **Настройки** - изменение параметров профиля и приватности

📊 Подробнее: [PROJECT_STATUS.md](PROJECT_STATUS.md) | [DOCUMENTATION.md](DOCUMENTATION.md)

---

## 🚀 Быстрый старт

### Предварительные требования

- Docker и Docker Compose (v2.0+)
- Telegram Bot Token от [@BotFather](https://t.me/BotFather)

### Локальный запуск

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/erliona/dating.git
cd dating

# 2. Настройте переменные окружения
cp .env.example .env
# Отредактируйте .env и укажите ваш BOT_TOKEN

# 3. Запустите микросервисы
docker compose up -d

# Проверьте статус всех сервисов
docker compose ps

# Проверьте health endpoints
for port in 8080 8081 8082 8083 8084 8085; do
  curl http://localhost:$port/health
done
```

### Архитектура микросервисов

Приложение построено на современной микросервисной архитектуре:

- **API Gateway** (порт 8080) - единая точка входа, маршрутизация запросов
- **Auth Service** (порт 8081) - аутентификация и JWT токены
- **Profile Service** (порт 8082) - управление профилями пользователей
- **Discovery Service** (порт 8083) - поиск и матчинг
- **Media Service** (порт 8084) - загрузка и обработка фотографий
- **Chat Service** (порт 8085) - real-time сообщения

Каждый сервис может масштабироваться независимо.

### Production развертывание

Автоматическое развертывание микросервисов через GitHub Actions:

1. Настройте GitHub Secrets (Settings → Secrets → Actions):
   - `DEPLOY_HOST` - IP или hostname сервера
   - `DEPLOY_USER` - SSH пользователь
   - `DEPLOY_SSH_KEY` - приватный SSH ключ
   - `BOT_TOKEN` - токен вашего бота
   - `JWT_SECRET` - секретный ключ для JWT токенов

2. Push в main ветку запустит автоматический деплой микросервисов

**Документация по архитектуре:**
- [🚀 Microservices Quick Start](MICROSERVICES_QUICK_START.md) - Быстрый старт
- [📘 Microservices Deployment Guide](docs/MICROSERVICES_DEPLOYMENT.md) - Полное руководство
- [📖 Microservices API Reference](docs/MICROSERVICES_API.md) - API документация
- [🏗️ Architecture Guide](docs/ARCHITECTURE.md) - Архитектура системы
- [📚 Migration Guide](docs/ARCHITECTURE_MIGRATION_GUIDE.md) - Переход на микросервисы

**Операционная документация:**
- [⚠️ **Data Persistence & Backup Guide**](docs/DATA_PERSISTENCE.md) - **CRITICAL: Read before any database operations!**
- [🔄 Deployment Idempotency Guide](docs/DEPLOYMENT_IDEMPOTENCY.md) - Database, logs, Grafana

---

## 🏗️ Технологический стек

### Frontend (Mini App)
- **HTML5/CSS3/JavaScript** - нативные веб-технологии
- **Telegram WebApp API** - интеграция с Telegram
- **Адаптивный дизайн** - оптимизация под мобильные устройства
- **Offline-ready** - работа без постоянного подключения

### Backend
- **Python 3.11+** - основной язык разработки
- **aiogram 3.x** - асинхронный фреймворк для Telegram ботов
- **SQLAlchemy 2.0** - ORM с поддержкой async
- **Alembic** - управление миграциями базы данных
- **PostgreSQL 15** - реляционная база данных
- **aiohttp** - HTTP сервер для API

### Инфраструктура
- **Docker & Docker Compose** - контейнеризация всех компонентов
- **Traefik 2.11** - обратный прокси с автоматическим HTTPS
- **Let's Encrypt** - бесплатные SSL сертификаты
- **nginx** - веб-сервер для статических файлов

### Мониторинг и наблюдаемость
- **Prometheus** - сбор метрик приложения и инфраструктуры
- **Grafana** - визуализация метрик и дашборды
- **Loki** - централизованное хранение и поиск логов
- **Promtail** - агент сбора логов с автоматическим парсингом JSON
- **cAdvisor** - метрики контейнеров Docker
- **Node Exporter** - системные метрики хоста
- **Postgres Exporter** - метрики базы данных
- **JSON Structured Logging** - все сервисы используют единый формат логов

### DevOps и CI/CD
- **GitHub Actions** - автоматизация тестирования и развертывания
- **pytest** - фреймворк для тестирования (293 теста)
- **pytest-cov** - измерение покрытия кода
- **pip-audit** - сканирование безопасности зависимостей

---

## 📊 Мониторинг

**Мониторинг интегрирован в основной docker-compose.yml и запускается автоматически:**

```bash
# Запустить все сервисы с мониторингом
docker compose up -d

# Проверить статус мониторинга
docker compose ps prometheus grafana loki promtail

# Доступ к дашбордам
# Grafana:    http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
# cAdvisor:   http://localhost:8090 (изменен с 8081)
```

**Порты мониторинга:**
- `3000` - Grafana (визуализация)
- `9090` - Prometheus (метрики)
- `8090` - cAdvisor (контейнеры) - **изменен с 8081 для избежания конфликта с auth-service**
- `9100` - Node Exporter (система)
- `9187` - Postgres Exporter (БД)
- `3100` - Loki (логи)

**Что отслеживается**:
- 📊 **Метрики**: CPU, Memory, Network всех контейнеров и микросервисов
- 💾 **База данных**: Активные соединения, производительность запросов
- 📝 **Логи**: Все логи из всех сервисов через Loki с JSON-парсингом
- 🔍 **События**: Старт/стоп сервисов, ошибки, предупреждения, бизнес-события

**Структурированное логирование (JSON)**:
Все сервисы автоматически логируют события в JSON формате для удобного анализа:
- ✅ `telegram-bot` - бот адаптер Telegram
- ✅ `auth-service` - аутентификация и JWT
- ✅ `profile-service` - управление профилями
- ✅ `discovery-service` - поиск и матчинг
- ✅ `media-service` - обработка медиа
- ✅ `chat-service` - чат и сообщения
- ✅ `api-gateway` - маршрутизация запросов

**Возможности анализа логов:**
- Фильтрация по уровню (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- Фильтрация по сервису (service_name)
- Поиск по пользователю (user_id)
- Отслеживание событий (event_type)
- Парсинг метаданных (модуль, функция, номер строки)

См. подробнее: [📊 Monitoring Guide](monitoring/README.md)

---

## 🔐 Переменные окружения

### Обязательные

| Переменная | Описание | Пример |
|------------|----------|--------|
| `BOT_TOKEN` | Telegram bot token от @BotFather | `123456789:ABCdef...` |
| `POSTGRES_DB` | Имя базы данных | `dating` |
| `POSTGRES_USER` | Пользователь БД | `dating` |
| `POSTGRES_PASSWORD` | Пароль БД | `SecurePass123` |

### Опциональные (для HTTPS)

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `DOMAIN` | Доменное имя для HTTPS | `localhost` |
| `WEBAPP_URL` | URL мини-приложения | `https://${DOMAIN}` |
| `ACME_EMAIL` | Email для Let's Encrypt | `admin@example.com` |

**Важно**: См. `.env.example` для полного списка и описаний.

---

## 📁 Структура проекта

```
dating/
├── core/                       # Платформонезависимое ядро
│   ├── models/                # Доменные модели (User, Profile, etc.)
│   ├── services/              # Бизнес-логика (ProfileService, MatchingService)
│   ├── interfaces/            # Контракты для адаптеров
│   └── utils/                 # Утилиты (validation, security)
│
├── services/                   # Микросервисы
│   ├── auth/                  # Сервис аутентификации (JWT, валидация)
│   ├── profile/               # Сервис профилей (CRUD, настройки)
│   ├── discovery/             # Сервис поиска (матчинг, рекомендации)
│   ├── media/                 # Сервис медиа (фото, NSFW detection)
│   └── chat/                  # Сервис чата (WebSocket, сообщения)
│
├── gateway/                    # API Gateway
│   └── main.py                # Маршрутизация запросов к микросервисам
│
├── adapters/                   # Платформенные адаптеры
│   └── telegram/              # Telegram интеграция
│       ├── repository.py      # Реализация репозиториев для Telegram
│       ├── notification.py    # Уведомления через Telegram bot
│       └── storage.py         # Хранение файлов
│
├── webapp/                     # Frontend (Telegram Mini App)
│   ├── index.html             # Главная страница с экранами
│   ├── js/                    # JavaScript модули
│   └── css/                   # Стили
│
├── tests/                      # Тесты
│   └── core/                  # Тесты платформонезависимой логики
│
├── migrations/                 # Миграции базы данных (Alembic)
│   └── versions/              # История изменений схемы БД
│
├── monitoring/                 # Конфигурация мониторинга
│   ├── grafana/               # Дашборды Grafana
│   ├── prometheus/            # Конфиг сбора метрик
│   └── loki/                  # Конфиг агрегации логов
│
├── docs/                       # Документация
│   ├── ARCHITECTURE.md        # Архитектура системы
│   ├── MICROSERVICES_API.md   # API микросервисов
│   └── ...                    # Другая документация
│
├── docker-compose.yml          # Микросервисная конфигурация
├── .env.example               # Шаблон переменных окружения
├── requirements.txt           # Python зависимости
└── pytest.ini                 # Конфигурация тестов
```

---

## 🛡️ Безопасность

- ✅ **HTTPS everywhere** - все соединения зашифрованы
- ✅ **Secrets management** - переменные окружения и GitHub Secrets
- ✅ **Automated SSL** - автоматическое обновление сертификатов
- ✅ **Security scanning** - pip-audit в CI pipeline
- ✅ **SQL injection protection** - через SQLAlchemy ORM

См. подробнее: [🔒 Security Policy](SECURITY.md)

---

## 💾 Персистентность данных

**✅ База данных ПОСТОЯННА (persistent)** - все данные сохраняются в Docker named volumes и не теряются при обновлении контейнеров:

- **`postgres_data`** - база данных (профили, взаимодействия, сообщения)
- **`traefik_certs`** - SSL сертификаты
- **`photo_storage`** - загруженные фотографии

### ⚠️ КРИТИЧЕСКИ ВАЖНО

**НИКОГДА не используйте `docker compose down -v` без резервной копии!**

Эта команда **БЕЗВОЗВРАТНО УДАЛЯЕТ ВСЕ ДАННЫЕ**:
- ❌ Все профили пользователей
- ❌ Все взаимодействия и матчи
- ❌ Все сообщения
- ❌ Все фотографии
- ❌ Все настройки

**Перед любыми рискованными операциями:**
```bash
# Создайте резервную копию!
docker compose exec db pg_dump -U dating dating > backup_$(date +%Y%m%d).sql
```

**Подробнее:** [⚠️ Data Persistence & Backup Guide](docs/DATA_PERSISTENCE.md)
- **`prometheus_data`** - метрики (30 дней)
- **`grafana_data`** - дашборды и настройки
- **`loki_data`** - логи (30 дней)

### Резервное копирование

```bash
# Создать backup базы данных
docker compose exec db pg_dump -U dating dating > backup.sql

# Восстановить из backup
docker compose exec -T db psql -U dating dating < backup.sql
```

---

## 🐛 Решение проблем

### Бот не отвечает

```bash
# Проверьте логи
docker compose logs -f bot

# Перезапустите
docker compose restart bot
```

### База данных не подключается

```bash
# Проверьте статус БД
docker compose ps db

# Проверьте логи
docker compose logs db
```

См. полный список: [🚀 Deployment Guide - Troubleshooting](docs/DEPLOYMENT.md#решение-проблем)

---

## 🤝 Вклад в проект

1. Fork репозиторий
2. Создайте feature ветку (`git checkout -b feature/AmazingFeature`)
3. Commit изменения (`git commit -m 'Add AmazingFeature'`)
4. Push в ветку (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

---

## 📜 Лицензия

Этот проект распространяется под лицензией MIT. См. файл [LICENSE](LICENSE) для деталей.

---

## 📖 Документация

### Основные документы
- **[📘 Полная документация](DOCUMENTATION.md)** - Comprehensive guide (English)
- **[📋 Индекс документации](docs/INDEX.md)** - Навигация по всей документации
- **[🏗️ Архитектура](docs/ARCHITECTURE.md)** - Архитектура системы
- **[🚀 Deployment](docs/DEPLOYMENT.md)** - Руководство по развертыванию
- **[🧪 Тестирование](docs/TESTING.md)** - Запуск и написание тестов

### Статус проекта
- **[📊 Project Status](PROJECT_STATUS.md)** - Реализованные и планируемые функции
- **[📝 Changelog](CHANGELOG.md)** - История изменений
- **[🗺️ Roadmap](ROADMAP.md)** - План развития

---

## 📞 Поддержка

- 📖 **Документация**: [DOCUMENTATION.md](DOCUMENTATION.md) | [docs/](docs/)
- 🐛 **Bug reports**: [GitHub Issues](https://github.com/erliona/dating/issues)
- 💬 **Обсуждения**: [GitHub Discussions](https://github.com/erliona/dating/discussions)

---

**Сделано с ❤️ для сообщества**

*Если проект оказался полезным, поставьте ⭐ на GitHub!*
