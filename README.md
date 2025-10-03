# 🏗️ Telegram Bot Infrastructure Template

**Production-ready infrastructure template** for Telegram bot projects with complete DevOps stack.

Готовая инфраструктура для разработки Telegram ботов с полной автоматизацией развертывания, мониторингом и CI/CD.

[![CI](https://github.com/erliona/dating/actions/workflows/ci.yml/badge.svg)](https://github.com/erliona/dating/actions/workflows/ci.yml)
[![Deploy](https://github.com/erliona/dating/actions/workflows/deploy.yml/badge.svg)](https://github.com/erliona/dating/actions/workflows/deploy.yml)

---

## ✨ Что включено

### Infrastructure
- 🐳 **Docker & Docker Compose** - полная контейнеризация приложения
- 🔐 **HTTPS из коробки** - автоматические SSL сертификаты от Let's Encrypt через Traefik
- 🚀 **CI/CD Pipeline** - автоматическое тестирование и развертывание через GitHub Actions
- 📈 **Мониторинг** - Prometheus + Grafana + Loki для метрик и логов
- 💾 **PostgreSQL** - готовая конфигурация базы данных
- ⚙️ **Конфигурация окружения** - управление через .env файлы
- 🔒 **Security Best Practices** - безопасные настройки по умолчанию

### Dating App Features (Implemented)
- ✅ **Epic A**: Mini App foundation & authentication (JWT, HMAC validation)
- ✅ **Epic B**: Onboarding, profiles, media gallery, geolocation
  - 18+ age validation
  - Photo upload (max 3, JPEG/PNG/WebP, 5MB limit)
  - Geohash for location privacy (~5km precision)
  - Privacy settings (hide age/distance/online)
  - **WebApp → Bot integration** - Profile data saved to database ✅
  - 162 tests passing, 76% code coverage

📖 See [EPIC_A_IMPLEMENTATION.md](EPIC_A_IMPLEMENTATION.md), [EPIC_B_IMPLEMENTATION.md](EPIC_B_IMPLEMENTATION.md), and [PROJECT_STATUS.md](PROJECT_STATUS.md) for details.

---

## 👥 User Flow (Currently Working)

1. **Start Bot**: User sends `/start` command to bot
2. **Open Mini App**: User clicks "🚀 Открыть Mini App" button
3. **Onboarding**: New users see welcome screen with app features
4. **Create Profile**: User fills complete profile form:
   - Name, birth date (18+ required)
   - Gender and preferences
   - Dating goals
   - Bio and location
   - Upload 3 photos
5. **Submit**: Profile data sent to bot and **saved to database** ✅
6. **Confirmation**: Bot sends success message with profile details

📊 See [PROJECT_STATUS.md](PROJECT_STATUS.md) for detailed feature status and roadmap.

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

# 3. Запустите инфраструктуру
docker compose -f docker-compose.dev.yml up -d

# 4. Проверьте статус
docker compose ps
```

### Production развертывание

Автоматическое развертывание через GitHub Actions:

1. Настройте GitHub Secrets (Settings → Secrets → Actions):
   - `DEPLOY_HOST` - IP или hostname сервера
   - `DEPLOY_USER` - SSH пользователь
   - `DEPLOY_SSH_KEY` - приватный SSH ключ
   - `BOT_TOKEN` - токен вашего бота

2. Push в main ветку запустит автоматический деплой

См. подробности: 
- [📘 Deployment Guide](docs/DEPLOYMENT.md)
- [🔄 Deployment Idempotency Guide](docs/DEPLOYMENT_IDEMPOTENCY.md) - Database, logs, Grafana

---

## 🏗️ Технологический стек

### Infrastructure
- **Docker & Docker Compose** - контейнеризация
- **Traefik 2.11** - reverse proxy с автоматическим HTTPS
- **Let's Encrypt** - бесплатные SSL сертификаты
- **PostgreSQL 15** - база данных
- **nginx** - веб-сервер для статики

### Bot Framework
- **Python 3.11+** - язык разработки
- **aiogram 3.x** - асинхронный Telegram Bot framework
- **SQLAlchemy 2.0** - ORM с async поддержкой
- **Alembic** - миграции базы данных

### Monitoring
- **Prometheus** - сбор метрик
- **Grafana** - дашборды и визуализация
- **Loki** - агрегация логов
- **cAdvisor** - метрики контейнеров
- **Node Exporter** - системные метрики
- **Postgres Exporter** - метрики базы данных

### CI/CD
- **GitHub Actions** - автоматизация тестирования и деплоя
- **pytest** - фреймворк тестирования
- **pip-audit** - проверка безопасности зависимостей

---

## 📊 Мониторинг

Мониторинг включается автоматически при деплое через CI/CD. Для локального запуска:

```bash
# Запустить с мониторингом (Prometheus, Grafana, Loki)
docker compose --profile monitoring up -d

# Доступ к дашбордам
# Grafana:    http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
# cAdvisor:   http://localhost:8081
```

**Что отслеживается**:
- 📊 **Метрики**: CPU, Memory, Network всех контейнеров
- 💾 **База данных**: Активные соединения, производительность
- 📝 **Логи**: Все логи приложений через Loki с JSON-парсингом
- 🔍 **События**: Старт/стоп приложения, ошибки, предупреждения

**Структурированное логирование**:
Бот автоматически логирует все события в JSON формате для удобного анализа в Grafana:
- Фильтрация по уровню (INFO, WARNING, ERROR)
- Отслеживание событий жизненного цикла
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
├── bot/                  # Код бота (11 модулей)
│   ├── main.py          # Точка входа, хендлеры
│   ├── api.py           # HTTP API для фото
│   ├── db.py            # Модели базы данных
│   ├── repository.py    # Слой доступа к данным
│   └── ...              # validation, security, geo, media, cache
├── webapp/              # Mini App фронтенд
│   ├── index.html       # Главная страница
│   ├── js/              # JavaScript модули
│   └── css/             # Стили
├── tests/               # Тесты (254 теста, 82% покрытие)
├── migrations/          # Миграции Alembic
├── monitoring/          # Конфигурация мониторинга
│   ├── grafana/        # 3 дашборда Grafana
│   ├── prometheus/     # Prometheus конфиг
│   └── loki/          # Loki конфиг
├── docs/               # Документация (см. DOCUMENTATION.md)
├── docker-compose.yml           # Production с HTTPS
├── docker-compose.dev.yml       # Development без HTTPS
├── Dockerfile          # Образ бота
├── .env.example       # Шаблон конфигурации
├── requirements.txt   # Production зависимости
└── requirements-dev.txt # Dev зависимости
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

Все данные сохраняются в Docker named volumes и не теряются при обновлении контейнеров:

- **`postgres_data`** - база данных
- **`traefik_certs`** - SSL сертификаты
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
