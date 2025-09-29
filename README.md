# Dating Bot & WebApp

Набор инструментов для запуска Telegram-бота знакомств с мини-приложением. Проект
включает Python-бекенд на `aiogram`, базу данных PostgreSQL с миграциями Alembic и
статический Telegram WebApp с валидацией формы.

## Возможности

- Диалоговый опрос в Telegram с проверкой вводимых данных.
- Сохранение анкет в PostgreSQL через SQLAlchemy 2.0 и JSONB-поля.
- Подбор взаимных совпадений и уведомления собеседников.
- Мини-приложение с прогресс-баром, подсказками и автосохранением черновика.
- Автоматическое применение миграций при запуске контейнера бота.

## Структура репозитория

```
.
├── alembic.ini
├── bot/
│   ├── __init__.py
│   ├── config.py
│   ├── db.py
│   └── main.py
├── docker/
│   └── entrypoint.sh
├── docker-compose.yml
├── Dockerfile
├── migrations/
│   ├── env.py
│   └── versions/
│       └── 20240611_0001_create_profiles_table.py
├── requirements.txt
├── webapp/
│   ├── css/
│   ├── js/
│   └── index.html
├── .env.example
└── README.md
```

## Быстрый старт (Docker Compose)

Инфраструктура описана в `docker-compose.yml`. Всё приложение разворачивается на
чистом сервере несколькими командами:

```bash
cp .env.example .env            # заполните токен и при необходимости другие настройки
nano .env                       # или используйте любой редактор

docker compose up -d --build    # собираем образ бота и поднимаем все сервисы
```

Что происходит:

- поднимается контейнер `db` с PostgreSQL 15;
- контейнер `bot` собирается из `Dockerfile`, применяет миграции Alembic и
  запускает Telegram-бота;
- контейнер `webapp` на Nginx раздаёт статические файлы из каталога `webapp/`.

Посмотреть логи можно так:

```bash
docker compose logs -f bot
```

По умолчанию база данных слушает порт `5432`, WebApp доступен по адресу
http://localhost:8080. Значения можно изменить в `.env` (переменные `POSTGRES_PORT`
и `WEBAPP_PORT`). При изменении порта не забудьте обновить `WEBAPP_URL`.

### Переменные окружения для Compose

Файл `.env` используется одновременно для Docker Compose и для самого приложения.
Важные параметры:

- `BOT_TOKEN` — токен Telegram-бота (обязательно).
- `WEBAPP_URL` — публичный URL мини-приложения. По умолчанию указывает на локальный
  контейнер Nginx.
- `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_PORT` — настройки
  сервиса PostgreSQL.
- `WEBAPP_PORT` — внешний порт, по которому отдаётся WebApp.
- `RUN_DB_MIGRATIONS` — необязательная переменная. Если выставить в `false`, бот
  пропустит выполнение `alembic upgrade head` при старте контейнера.

### Состав сервисов

- **db** — PostgreSQL 15, c volume `postgres_data` для хранения данных между
  перезапусками. Настроен healthcheck.
- **bot** — Python 3.11 с установленными зависимостями из `requirements.txt` и
  скриптом `docker/entrypoint.sh`, который накатывает миграции и запускает
  `python -m bot.main`.
- **webapp** — `nginx:alpine`, который монтирует директорию `webapp/` и раздаёт её
  содержимое.

## Ручной запуск без Docker

1. Установите Python 3.11+, PostgreSQL и создайте базу данных.
2. Создайте виртуальное окружение и установите зависимости:

   ```bash
   python -m venv .venv
   source .venv/bin/activate  # Windows: .venv\Scripts\activate
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

3. Установите переменные окружения:

   ```bash
   export BOT_TOKEN="1234567890:ABC..."
   export BOT_DATABASE_URL="postgresql+asyncpg://user:pass@localhost:5432/dating"
   export WEBAPP_URL="https://example.com/webapp/index.html"
   ```

4. Примените миграции и запустите бота:

   ```bash
   alembic upgrade head
   python -m bot.main
   ```

## Конфигурация и миграции

- Бот ищет строку подключения в переменных `BOT_DATABASE_URL` или `DATABASE_URL`.
- Alembic использует те же переменные. Если они не заданы, берётся значение из
  `alembic.ini`.
- Все миграции лежат в `migrations/versions`. Добавляйте новые через `alembic
  revision --autogenerate -m "comment"`.

## Мини-приложение

Каталог `webapp/` содержит статические файлы. В Docker Compose он автоматически
раздаётся через Nginx. Для стороннего хостинга просто загрузите содержимое каталога
на любой статический сервер (GitHub Pages, Firebase Hosting и т.д.) и укажите URL в
`WEBAPP_URL`.

## Проверка качества кода

- Валидация ввода в боте учитывает случаи, когда пользователь отправляет не текст,
  поэтому сценарии со стикерами или пустыми сообщениями не ломают диалог.
- Веб-приложение выполняет клиентскую валидацию и нормализует данные перед
  отправкой.

## Бэклог развития

Расширенные идеи и планы по развитию описаны в [`BACKLOG.md`](./BACKLOG.md).
