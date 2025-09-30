# Dating Bot & WebApp

Проект объединяет Telegram-бота знакомств на базе [aiogram 3](https://docs.aiogram.dev/) и
статическое Telegram WebApp-мини-приложение. Бот собирает анкету через диалог, принимает
данные из мини-приложения, сохраняет их в PostgreSQL и уведомляет о взаимных совпадениях.

## Возможности

- Пошаговый опрос в Telegram с проверкой вводимых данных и кнопкой для запуска WebApp.
- Сохранение анкет в базе данных PostgreSQL через SQLAlchemy 2.0 и миграции Alembic.
- Поиск взаимных совпадений: бот сверяет предпочтения и рассылает анкеты обеим сторонам.
- Мини-приложение с валидацией, прогресс-баром, автосохранением черновика в `localStorage`
  и проверкой HTTPS-ссылок на фото.
- Готовая инфраструктура Docker Compose с контейнерами бота, базы данных и nginx для WebApp.
- CI на GitHub Actions: запуск тестов и проверка сборки Docker-образа при каждом PR.
- Скрипт и workflow для деплоя на удалённый сервер через `docker compose`.

## Структура репозитория

```
.
├── bot/                 # код Telegram-бота
├── webapp/              # статическое мини-приложение
├── migrations/          # ревизии Alembic
├── scripts/deploy.sh    # ручной деплой на сервер
├── docker-compose.yml   # инфраструктура для локального запуска
├── Dockerfile           # образ бота
├── requirements*.txt    # зависимости
├── .github/workflows/   # CI и CD
├── README.md            # текущий файл
└── BACKLOG.md           # идеи для дальнейшего развития
```

## Требования

- Python 3.11+
- PostgreSQL 14+ (для продакшн-запуска; для тестов используется временная БД)
- Docker и Docker Compose — для контейнерного запуска
- Telegram Bot API токен

## Переменные окружения

Создайте файл `.env` на основе `.env.example` и заполните значения:

| Переменная | Назначение |
| --- | --- |
| `BOT_TOKEN` | Токен Telegram-бота. Обязателен всегда. |
| `WEBAPP_URL` | Обязателен. Публичный URL мини-приложения, который бот будет открывать по кнопке. |
| `WEBAPP_PORT` | Порт публикации WebApp в Docker Compose (по умолчанию `8080`). |
| `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_PORT` | Настройки PostgreSQL для Compose. |
| `BOT_DATABASE_URL` | Строка подключения SQLAlchemy в формате `postgresql+asyncpg://`. Нужна при запуске вне Compose. |
| `RUN_DB_MIGRATIONS` | Если выставить в `false`, контейнер бота пропустит `alembic upgrade head`. |

> ⚠️ Поддерживается только PostgreSQL. SQLite и хранение в файлах кодом не предусмотрены.

## Быстрый старт (Docker Compose)

1. Скопируйте шаблон и заполните переменные:
   ```bash
   cp .env.example .env
   nano .env  # или любой другой редактор
   ```
2. Запустите инфраструктуру:
   ```bash
   docker compose up -d --build
   ```
3. Проверьте логи бота:
   ```bash
   docker compose logs -f bot
   ```

В составе стенда:
- `db` — PostgreSQL 15 с volume `postgres_data`.
- `bot` — Python 3.11, выполняет Alembic миграции и запускает `python -m bot.main`.
- `webapp` — nginx, раздаёт статический каталог `webapp/`.

После запуска WebApp доступен по адресу `http://localhost:8080/`, а база — на порту,
указанном в `.env` (по умолчанию `5432`). Бот не запустится без `WEBAPP_URL`, поэтому
обновите переменную на публичный URL, если бот работает не локально.

## Локальный запуск без Docker

1. Установите зависимости:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install --upgrade pip
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # для запуска тестов
   ```
2. Настройте переменные окружения (через `.env` или `export`):
   ```bash
   export BOT_TOKEN="1234567890:ABC..."
   export BOT_DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/dating"
   export WEBAPP_URL="https://example.com/webapp"
   ```
3. Примените миграции:
   ```bash
   alembic upgrade head
   ```
4. Запустите бота:
   ```bash
   python -m bot.main
   ```
5. Для разработки WebApp можно поднять простой сервер:
   ```bash
   python -m http.server 8080 --directory webapp
   ```
   и указать соответствующий `WEBAPP_URL`.

## Работа с миграциями

- Создать новую ревизию:
  ```bash
  alembic revision --autogenerate -m "Добавить поле ..."
  ```
- Применить изменения:
  ```bash
  alembic upgrade head
  ```
- Откатиться на шаг назад:
  ```bash
  alembic downgrade -1
  ```

## Тесты и проверка качества

Проект покрыт `pytest`-тестами для конфигурации, репозитория и утилит бота. Запуск:
```bash
python -m pytest
```

CI workflow `.github/workflows/ci.yml` автоматически выполняет тесты и пробную сборку
Docker-образа при каждом коммите в ветки `main`/`master` и в pull request.

## Деплой

Для автоматического развёртывания предусмотрен workflow `.github/workflows/deploy.yml`.
Он копирует репозиторий на сервер по SSH, пишет `.env` из секрета и выполняет
`docker compose up -d --build`. Перед использованием настройте секреты
`DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_SSH_KEY`, `DEPLOY_PATH`, `ENV_FILE` (и при
необходимости `DEPLOY_PORT`).

Для ручного деплоя с рабочей станции используйте скрипт `scripts/deploy.sh`:
```bash
scripts/deploy.sh \
  -H server.example.com \
  -u deploy \
  -d /opt/dating \
  -e .env \
  -i ~/.ssh/id_ed25519
```
Скрипт проверит наличие Docker и `docker compose`, при необходимости установит их и
перезапустит сервисы.

## Устранение неполадок

| Симптом | Возможная причина | Решение |
| --- | --- | --- |
| `BOT_TOKEN environment variable is required` | Не задан токен бота. | Проверьте `.env` или переменные окружения. |
| `BOT_DATABASE_URL must be a valid SQLAlchemy connection string` | Строка подключения в неправильном формате. | Используйте `postgresql+asyncpg://user:pass@host:port/dbname`. |
| `Only PostgreSQL databases are supported` | Подключение к SQLite или другому драйверу. | Переключитесь на PostgreSQL. |
| `Cannot connect to database` | Сервис PostgreSQL недоступен. | Проверьте `docker compose ps`, настройки доступа и что база создана. |
| Кнопка WebApp не появляется | `WEBAPP_URL` не задан или пустой. | Установите корректный публичный URL. |
| WebApp отдаёт 404 | URL содержит дополнительный путь или nginx не запущен. | Убедитесь, что `WEBAPP_URL` указывает на корень (`http://host:8080/`) и контейнер `webapp` активен. |
| Бот не реагирует | Ошибка в логике или бот не запущен. | Просмотрите `docker compose logs -f bot`, проверьте токен и актуальность webhook (бот работает в режиме polling). |

## Дополнительные материалы

- План развития и идеи — в файле [`BACKLOG.md`](./BACKLOG.md).
- CSS/JS мини-приложения лежат в `webapp/` и не требуют сборки: любые изменения
  применяются сразу после перезапуска nginx или обновления страницы.

Удачного знакомства! 😊
