# 💕 Dating Bot & WebApp

Telegram-бот для знакомств с интегрированным мини-приложением. Современный стек: Python, aiogram 3, PostgreSQL, Docker с полной автоматизацией CI/CD.

[![CI](https://github.com/erliona/dating/actions/workflows/ci.yml/badge.svg)](https://github.com/erliona/dating/actions/workflows/ci.yml)
[![Deploy](https://github.com/erliona/dating/actions/workflows/deploy.yml/badge.svg)](https://github.com/erliona/dating/actions/workflows/deploy.yml)

---

## ✨ Возможности

- 🤖 **Telegram Bot** - полнофункциональный бот с командами и обработчиками
- 📱 **Modern WebApp** - современное мини-приложение с card-swipe интерфейсом (как Tinder)
- 💑 **Умный матчинг** - алгоритм подбора на основе интересов, локации, цели и возраста
- 📊 **Аналитика** - детальная статистика использования и engagement метрики
- 🔒 **Безопасность** - rate limiting, валидация данных, защита от спама
- 📈 **Мониторинг** - Prometheus + Grafana + Loki для отслеживания метрик и логов
- 🔐 **HTTPS** - автоматические SSL сертификаты от Let's Encrypt через Traefik
- 🚀 **CI/CD** - автоматический деплой через GitHub Actions
- 💾 **Персистентность** - данные сохраняются при обновлении контейнеров
- ⚡ **Кэширование** - in-memory кэш для оптимизации производительности

---

## 🚀 Быстрый старт (5 минут)

### Предварительные требования

- Docker и Docker Compose (v2.0+)
- Telegram Bot Token от [@BotFather](https://t.me/BotFather)

### Запуск локально

```bash
# 1. Клонируйте репозиторий
git clone https://github.com/erliona/dating.git
cd dating

# 2. Настройте переменные окружения
cp .env.example .env
# Отредактируйте .env и укажите ваш BOT_TOKEN

# 3. Запустите приложение
docker compose -f docker-compose.dev.yml up -d

# 4. Проверьте статус
docker compose ps

# 5. Откройте бота в Telegram
# Найдите вашего бота и отправьте /start
```

**Готово!** Бот работает локально 🎉

### Запуск в продакшн (автоматический деплой)

См. подробное руководство: [📘 Deployment Guide](docs/DEPLOYMENT.md)

---

## 📚 Документация

### Для начинающих
- **[🚀 Getting Started](docs/GETTING_STARTED.md)** - пошаговое руководство по запуску
- **[🏗️ Architecture](docs/ARCHITECTURE.md)** - архитектура и компоненты системы
- **[🚀 Deployment](docs/DEPLOYMENT.md)** - развертывание в production

### Для разработчиков
- **[📊 Monitoring](monitoring/README.md)** - настройка и использование мониторинга
- **[🗺️ Roadmap](ROADMAP.md)** - планируемые функции и улучшения
- **[🔒 Security](SECURITY.md)** - политика безопасности

### Быстрые ссылки
- **[Monitoring Quick Start](monitoring/QUICK_START.md)** - мониторинг за 1 минуту
- **[Monitoring Architecture](monitoring/ARCHITECTURE.md)** - детали системы мониторинга

---

## 🎯 Основные команды бота

| Команда | Описание |
|---------|----------|
| `/start` | Начать работу с ботом, открыть форму профиля |
| `/matches` | Показать историю матчей с деталями профилей |
| `/stats` | Показать вашу статистику (лайки, матчи, процент успеха) |
| `/analytics` | Системная аналитика (только для админов) |
| `/debug` | Отладочная информация о статусе системы |

---

## 🏗️ Технологический стек

### Backend
- **Python 3.11+** - основной язык разработки
- **aiogram 3.x** - асинхронный фреймворк для Telegram Bot API
- **SQLAlchemy 2.0** - ORM с асинхронным драйвером
- **PostgreSQL 15** - реляционная база данных с JSONB support
- **Alembic** - миграции базы данных
- **asyncpg** - высокопроизводительный PostgreSQL драйвер

### Frontend
- **HTML/CSS/JavaScript** - мини-приложение Telegram WebApp
- **Telegram WebApp SDK** - интеграция с Telegram
- **nginx** - веб-сервер для статических файлов

### Infrastructure
- **Docker & Docker Compose** - контейнеризация
- **Traefik** - reverse proxy с автоматическим HTTPS
- **Let's Encrypt** - бесплатные SSL сертификаты

### Monitoring
- **Prometheus** - сбор метрик
- **Grafana** - дашборды и визуализация
- **Loki** - агрегация логов
- **cAdvisor** - метрики контейнеров
- **Node Exporter** - системные метрики
- **Postgres Exporter** - метрики базы данных

### CI/CD
- **GitHub Actions** - автоматизация тестирования и деплоя
- **pytest** - тестирование
- **pip-audit** - проверка безопасности зависимостей

---

## 📊 Мониторинг

Мониторинг включается автоматически при деплое через CI/CD. Для локального запуска:

```bash
# Запустить с мониторингом (Prometheus, Grafana, Loki)
docker compose --profile monitoring up -d

# Или используя отдельный compose файл
docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d

# Доступ к дашбордам
# Grafana:    http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
# cAdvisor:   http://localhost:8081
```

**⚠️ Важно для логов Loki**: 
Чтобы логи были видны в Grafana, необходимо запустить приложение с мониторингом (команды выше). Без этого Promtail не будет собирать логи из Docker контейнеров.

**Основные дашборды в Grafana**:
- Dating App - Overview (общий обзор системы + логи)
- Dating App - Business Metrics (метрики бизнеса)

**Отслеживаемые метрики**:
- Активные пользователи (24h / 7d)
- Общее количество матчей
- Match rate и engagement rate
- Ресурсы контейнеров (CPU, Memory, Network)
- Производительность базы данных
- **Логи всех сервисов через Loki** (бот, webapp, database)

**Поиск логов в Grafana**:
1. Откройте Grafana → Explore
2. Выберите datasource "Loki"
3. Используйте запросы:
   - `{job="docker"}` - все логи
   - `{job="docker", container_name=~".*bot.*"}` - логи бота
   - `{job="docker"} |= "ERROR"` - только ошибки

См. подробнее: [📊 Monitoring Guide](monitoring/README.md)

---

## 🧪 Тестирование

```bash
# Установить зависимости для разработки
pip install -r requirements-dev.txt

# Запустить все тесты
pytest -v

# С покрытием кода
pytest --cov=bot --cov-report=html

# Запустить только unit тесты
pytest tests/test_database.py -v

# Запустить только integration тесты
pytest tests/test_integration.py -v
```

**Тестовое покрытие**: 136+ тестов с покрытием основной функциональности

---

## 🔐 Переменные окружения

### Обязательные

| Переменная | Описание | Пример |
|------------|----------|--------|
| `BOT_TOKEN` | Telegram bot token от @BotFather | `123456789:ABCdef...` |
| `POSTGRES_DB` | Имя базы данных | `dating` |
| `POSTGRES_USER` | Пользователь БД | `dating` |
| `POSTGRES_PASSWORD` | Пароль БД (только алфавитно-цифровые символы!) | `SecurePass123` |

### Опциональные (для HTTPS)

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `DOMAIN` | Доменное имя для HTTPS | `localhost` |
| `WEBAPP_URL` | URL мини-приложения | `https://${DOMAIN}` |
| `ACME_EMAIL` | Email для Let's Encrypt | `admin@example.com` |
| `HTTP_PORT` | HTTP порт | `80` |
| `HTTPS_PORT` | HTTPS порт | `443` |

### Опциональные (остальные)

| Переменная | Описание | По умолчанию |
|------------|----------|--------------|
| `DEBUG` | Режим отладки | `false` |
| `RUN_DB_MIGRATIONS` | Автоматические миграции при старте | `true` |
| `GRAFANA_ADMIN_USER` | Логин Grafana | `admin` |
| `GRAFANA_ADMIN_PASSWORD` | Пароль Grafana | `admin` |

**Важно**: См. `.env.example` для полного списка и описаний.

---

## 📁 Структура проекта

```
dating/
├── .github/workflows/     # CI/CD pipelines
│   ├── ci.yml            # Тестирование и сборка
│   └── deploy.yml        # Автоматический деплой
├── bot/                  # Код бота
│   ├── main.py          # Основная логика и обработчики
│   ├── db.py            # Модели БД и репозитории
│   ├── config.py        # Конфигурация
│   ├── analytics.py     # Система аналитики
│   ├── security.py      # Rate limiting и валидация
│   └── cache.py         # Кэширование
├── webapp/              # Мини-приложение
│   ├── index.html       # Форма профиля
│   ├── css/            # Стили
│   └── js/             # JavaScript логика
├── migrations/          # Миграции Alembic
│   └── versions/       # Версии миграций
├── tests/              # Тесты
│   ├── test_*.py       # Unit и integration тесты
│   └── conftest.py     # Fixtures
├── monitoring/         # Конфигурация мониторинга
│   ├── prometheus/     # Конфиг Prometheus
│   ├── grafana/        # Дашборды Grafana
│   ├── loki/          # Конфиг Loki
│   └── promtail/      # Конфиг Promtail
├── docs/              # Документация
│   ├── GETTING_STARTED.md
│   ├── ARCHITECTURE.md
│   ├── DEPLOYMENT.md
│   └── archive/       # Старые документы
├── docker-compose.yml           # Production с HTTPS
├── docker-compose.dev.yml       # Development без HTTPS
├── Dockerfile         # Образ бота
├── .env.example      # Шаблон конфигурации
├── requirements.txt  # Production зависимости
├── requirements-dev.txt # Dev зависимости
├── ROADMAP.md       # Планируемые функции
└── README.md        # Этот файл
```

---

## 🔄 Алгоритм матчинга

Система использует многофакторный алгоритм подбора пар:

1. **Взаимный лайк** (обязательное условие)
   - Оба пользователя должны лайкнуть друг друга

2. **Совместимость интересов** (40% веса)
   - Подсчет общих интересов
   - Weighted scoring

3. **Географическая близость** (30% веса)
   - Совпадение локации

4. **Совпадение целей** (20% веса)
   - Одинаковые цели знакомства (серьезные отношения, дружба и т.д.)

5. **Возрастная совместимость** (10% веса)
   - Разница в возрасте ≤5 лет

**Порог матчинга**: score ≥ 0.3

Матчи с высоким score получают приоритет в уведомлениях.

---

## 🛡️ Безопасность

- ✅ **Rate limiting** - защита от спама и флуда
- ✅ **Input validation** - валидация всех пользовательских данных
- ✅ **SQL injection protection** - через SQLAlchemy ORM
- ✅ **HTTPS everywhere** - все соединения зашифрованы
- ✅ **Secrets management** - переменные окружения и GitHub Secrets
- ✅ **Automated SSL** - автоматическое обновление сертификатов
- ✅ **Security scanning** - pip-audit в CI pipeline

См. подробнее: [🔒 Security Policy](SECURITY.md)

---

## 💾 Персистентность данных

Все данные сохраняются в Docker named volumes и **не теряются** при обновлении контейнеров:

### Основные данные
- **`postgres_data`** - база данных пользователей и взаимодействий
- **`traefik_certs`** - SSL сертификаты

### Данные мониторинга
- **`prometheus_data`** - метрики (хранятся 30 дней)
- **`grafana_data`** - дашборды и настройки
- **`loki_data`** - логи (хранятся 30 дней)

**Важно**: При выполнении `docker compose down -v` все данные будут удалены!

### Резервное копирование

```bash
# Создать backup базы данных
docker compose exec db pg_dump -U dating dating > backup.sql

# Восстановить из backup
docker compose exec -T db psql -U dating dating < backup.sql
```

См. подробнее: [🚀 Deployment Guide - Backup Section](docs/DEPLOYMENT.md#резервное-копирование)

---

## 🐛 Решение проблем

### Бот не отвечает

```bash
# Проверьте логи
docker compose logs -f bot

# Проверьте статус
docker compose ps

# Перезапустите
docker compose restart bot
```

### База данных не подключается

```bash
# Проверьте статус БД
docker compose ps db

# Проверьте логи
docker compose logs db

# Если пароль изменился (⚠️ удалит данные!)
docker compose down -v
docker compose up -d
```

### WebApp показывает 404

```bash
# Проверьте конфигурацию
grep WEBAPP_URL .env

# Проверьте nginx
docker compose logs webapp
docker compose restart webapp
```

### SSL сертификат не получается

1. Проверьте DNS: `dig +short your-domain.com`
2. Проверьте firewall: порты 80 и 443 должны быть открыты
3. Проверьте логи Traefik: `docker compose logs traefik`

См. полный список: [🚀 Deployment Guide - Troubleshooting](docs/DEPLOYMENT.md#решение-проблем)

---

## 🗺️ Roadmap

Планируемые функции:

- 🤖 **ML-рекомендации** - машинное обучение для улучшения матчинга
- 💬 **Чат внутри приложения** - прямой обмен сообщениями
- 📹 **Видеозвонки** - WebRTC интеграция
- ✅ **Верификация профилей** - AI-powered валидация
- 💰 **Премиум подписка** - монетизация
- 📱 **Нативные приложения** - iOS и Android
- 🌐 **Мультиязычность** - поддержка разных языков
- 🔔 **Push уведомления** - в реальном времени
- 🎮 **Gamification** - ачивки и награды

См. подробнее: [🗺️ Roadmap](ROADMAP.md)

---

## 🤝 Вклад в проект

Мы приветствуем вклад в развитие проекта!

1. Fork репозиторий
2. Создайте feature ветку (`git checkout -b feature/AmazingFeature`)
3. Commit изменения (`git commit -m 'Add some AmazingFeature'`)
4. Push в ветку (`git push origin feature/AmazingFeature`)
5. Откройте Pull Request

**Перед созданием PR**:
- Убедитесь что все тесты проходят: `pytest -v`
- Проверьте code style: `python -m py_compile bot/*.py`
- Обновите документацию при необходимости

---

## 📜 Лицензия

Этот проект распространяется под лицензией MIT. См. файл [LICENSE](LICENSE) для деталей.

---

## 📞 Поддержка

- 📖 **Документация**: см. [docs/](docs/)
- 🐛 **Bug reports**: [GitHub Issues](https://github.com/erliona/dating/issues)
- 💬 **Обсуждения**: [GitHub Discussions](https://github.com/erliona/dating/discussions)

---

## 🙏 Благодарности

- [aiogram](https://github.com/aiogram/aiogram) - отличный Telegram Bot framework
- [SQLAlchemy](https://www.sqlalchemy.org/) - мощная ORM
- [Traefik](https://traefik.io/) - современный reverse proxy
- [Grafana](https://grafana.com/) - красивые дашборды
- Telegram за отличный Bot API и WebApp SDK

---

## ⭐ Статистика

![GitHub stars](https://img.shields.io/github/stars/erliona/dating?style=social)
![GitHub forks](https://img.shields.io/github/forks/erliona/dating?style=social)
![GitHub issues](https://img.shields.io/github/issues/erliona/dating)
![GitHub pull requests](https://img.shields.io/github/issues-pr/erliona/dating)

---

**Сделано с ❤️ для сообщества**

*Если проект оказался полезным, поставьте ⭐ на GitHub!*
