# 🚀 Getting Started - Dating Application

Добро пожаловать в проект Dating! Это руководство поможет вам быстро начать работу с проектом.

## 📋 Содержание

- [Предварительные требования](#предварительные-требования)
- [Быстрый старт](#быстрый-старт)
- [Структура проекта](#структура-проекта)
- [Архитектура](#архитектура)
- [Разработка](#разработка)
- [Тестирование](#тестирование)
- [Полезные ссылки](#полезные-ссылки)

---

## 🔧 Предварительные требования

### Обязательное ПО

- **Docker** 20.10+ и **Docker Compose** v2.0+
- **Python** 3.12+ (для локальной разработки)
- **Node.js** 20+ (для разработки webapp)
- **Git** 2.30+

### Получение токена бота

1. Откройте [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте команду `/newbot`
3. Следуйте инструкциям
4. Сохраните полученный токен

---

## 🚀 Быстрый старт

### 1. Клонирование репозитория

```bash
git clone https://github.com/erliona/dating.git
cd dating
```

### 2. Настройка окружения

```bash
# Копируйте пример конфигурации
cp .env.example .env

# Отредактируйте .env и укажите:
# - BOT_TOKEN: ваш токен от @BotFather
# - POSTGRES_PASSWORD: надежный пароль для БД
# - JWT_SECRET: случайная строка (32+ символов)
nano .env
```

### 3. Запуск приложения

```bash
# Запустить все сервисы
docker compose up -d

# Проверить статус
docker compose ps

# Просмотреть логи
docker compose logs -f
```

### 4. Проверка работы

**Проверка health endpoints всех сервисов:**

```bash
# Скрипт для проверки всех сервисов
for port in 8080 8081 8082 8083 8084 8085 8086; do
  echo "Checking port $port..."
  curl -s http://localhost:$port/health | jq .
done
```

**Доступ к интерфейсам:**

- 🤖 Telegram Bot: найдите бота в Telegram и отправьте `/start`
- 🌐 WebApp: http://localhost/ (через Traefik)
- 👨‍💼 Admin Panel: http://localhost:8086/admin-panel/ (admin/admin123)
- 📊 Grafana: http://localhost:3000 (admin/admin)
- 📈 Prometheus: http://localhost:9090

---

## 📁 Структура проекта

```
dating/
├── 📦 core/                  # Бизнес-логика (domain models, services)
├── 🔌 adapters/              # Платформенные адаптеры (Telegram)
├── 🏢 services/              # Микросервисы (auth, profile, etc.)
│   ├── auth/                 # Аутентификация (порт 8081)
│   ├── profile/              # Профили (порт 8082)
│   ├── discovery/            # Поиск и матчинг (порт 8083)
│   ├── media/                # Фото (порт 8084)
│   ├── chat/                 # Чат (порт 8085)
│   ├── admin/                # Админ панель (порт 8086)
│   └── notification/         # Push-уведомления (порт 8087)
├── 🌐 gateway/               # API Gateway (порт 8080)
├── 🤖 bot/                   # Telegram Bot (минималистичный)
├── 🎨 webapp/                # Next.js 15 WebApp (React 19)
├── 🧪 tests/                 # 380+ автоматических тестов
│   ├── unit/                 # Модульные тесты
│   ├── integration/          # Интеграционные тесты
│   └── e2e/                  # End-to-end тесты
├── 📊 monitoring/            # Конфигурация мониторинга
├── 🗄️ migrations/            # Миграции БД (Alembic)
└── 📚 docs/                  # Документация
```

---

## 🏗️ Архитектура

### Микросервисная архитектура

Приложение построено на 7 независимых микросервисах:

```
┌─────────────────────────────────────────────────┐
│              Telegram Mini App                  │
│         (Next.js 15 + React 19)                 │
└────────────────┬────────────────────────────────┘
                 │ HTTPS/REST
┌────────────────▼────────────────────────────────┐
│         API Gateway (порт 8080)                 │
│    Единая точка входа для всех запросов        │
└─────────────┬───────────────────────────────────┘
              │
    ┌─────────┴─────────┐
    │  Микросервисы:    │
    ├───────────────────┤
    │ Auth (8081)       │ ← JWT токены
    │ Profile (8082)    │ ← Профили CRUD
    │ Discovery (8083)  │ ← Поиск и матчинг
    │ Media (8084)      │ ← Фото + NSFW
    │ Chat (8085)       │ ← Сообщения
    │ Admin (8086)      │ ← Админка
    │ Notification (8087)│ ← Push
    └───────────────────┘
              │
    ┌─────────▼─────────┐
    │   PostgreSQL 15   │
    │   (shared DB)     │
    └───────────────────┘
```

### Ключевые принципы

- **Thin Client Pattern**: Бот минималистичный, вся логика в микросервисах
- **API Gateway**: Единая точка входа, маршрутизация к сервисам
- **Clean Architecture**: Разделение на core/adapters/services
- **Микросервисы**: Независимое развертывание и масштабирование

---

## 💻 Разработка

### Локальная разработка (Python)

```bash
# Создать виртуальное окружение
python3.12 -m venv venv
source venv/bin/activate  # Linux/Mac
# или venv\Scripts\activate  # Windows

# Установить зависимости
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Настроить окружение
export DATABASE_URL="postgresql+asyncpg://dating:dating@localhost:5432/dating"
export BOT_TOKEN="your-token-here"
export API_GATEWAY_URL="http://localhost:8080"
```

### Разработка WebApp (Next.js)

```bash
cd webapp

# Установить зависимости
npm install

# Запустить dev сервер
npm run dev

# Открыть http://localhost:3000
```

### Полезные команды

```bash
# Просмотр логов конкретного сервиса
docker compose logs -f profile-service

# Перезапуск сервиса
docker compose restart profile-service

# Пересборка и перезапуск
docker compose up -d --build profile-service

# Остановить все
docker compose down

# Остановить и удалить данные (⚠️ ОСТОРОЖНО!)
docker compose down -v
```

### Работа с базой данных

```bash
# Создать новую миграцию
alembic revision --autogenerate -m "Описание изменений"

# Применить миграции
alembic upgrade head

# Откатить последнюю миграцию
alembic downgrade -1

# Подключиться к БД (если включен внешний порт)
psql -h localhost -p 5432 -U dating -d dating
```

### Code Quality

```bash
# Форматирование
black .
isort --profile black .

# Линтинг
flake8 . --max-line-length=127

# Проверка типов
mypy --ignore-missing-imports .

# Проверка безопасности
pip-audit
```

---

## 🧪 Тестирование

### Запуск тестов

```bash
# Все тесты (~11 секунд)
pytest

# По категориям
pytest -m unit          # Модульные тесты
pytest -m integration   # Интеграционные тесты
pytest -m e2e           # End-to-end тесты

# С покрытием кода
pytest --cov=bot --cov=core --cov=services --cov-report=html

# Конкретный файл
pytest tests/unit/test_validation.py -v

# Остановиться на первой ошибке
pytest -x
```

### Структура тестов

- **Unit tests** (`tests/unit/`) - Тесты отдельных функций/классов
- **Integration tests** (`tests/integration/`) - Тесты взаимодействия компонентов
- **E2E tests** (`tests/e2e/`) - Тесты полных пользовательских сценариев

**Статистика:** 380+ тестов, высокий процент успешных тестов

---

## 📚 Полезные ссылки

### Основная документация

- [README.md](../README.md) - Общее описание проекта
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Гайд по контрибуции
- [ROADMAP.md](../ROADMAP.md) - Планируемые функции
- [CHANGELOG.md](../CHANGELOG.md) - История изменений
- [SECURITY.md](../SECURITY.md) - Безопасность

### Детальная документация

- [CI/CD Guide](CI_CD_GUIDE.md) - Continuous Integration/Deployment
- [Monitoring Setup](MONITORING_SETUP.md) - Настройка мониторинга
- [Port Mapping](PORT_MAPPING.md) - Карта портов всех сервисов
- [Admin Panel Guide](ADMIN_PANEL_GUIDE.md) - Административная панель
- [API Gateway Routes](API_GATEWAY_ROUTES.md) - Маршруты API Gateway
- [Thin Client Architecture](THIN_CLIENT_ARCHITECTURE.md) - Архитектура тонкого клиента
- [Test Refactoring 2024](TEST_REFACTORING_2024.md) - Обновление тестов
- [Deployment Troubleshooting](DEPLOYMENT_TROUBLESHOOTING.md) - Решение проблем

### Специфичные компоненты

- [WebApp README](../webapp/README.md) - Next.js WebApp
- [Admin Service README](../services/admin/README.md) - Админ панель

### Внешние ресурсы

- [Telegram Bot API](https://core.telegram.org/bots/api)
- [Telegram WebApp API](https://core.telegram.org/bots/webapps)
- [Next.js Documentation](https://nextjs.org/docs)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Docker Documentation](https://docs.docker.com/)

---

## 🎯 Следующие шаги

После успешного запуска:

1. ✅ Изучите [архитектуру проекта](../README.md#архитектура)
2. ✅ Ознакомьтесь с [API документацией](../README.md#api-документация)
3. ✅ Попробуйте добавить [новую функцию](../CONTRIBUTING.md)
4. ✅ Запустите и изучите [мониторинг](MONITORING_SETUP.md)
5. ✅ Прочитайте про [deployment](CI_CD_GUIDE.md)

## ❓ Нужна помощь?

- 🐛 [Создать Issue](https://github.com/erliona/dating/issues)
- 💬 [GitHub Discussions](https://github.com/erliona/dating/discussions)
- 📧 Email: support@example.com

---

**Удачи в разработке! 🚀**
