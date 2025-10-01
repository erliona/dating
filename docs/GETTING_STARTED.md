# 🚀 Быстрый старт

Это руководство поможет вам быстро запустить Dating Bot на вашей машине.

## Предварительные требования

- Docker и Docker Compose (v2.0+)
- Telegram Bot Token от [@BotFather](https://t.me/BotFather)
- (Опционально) Домен с SSL для продакшн деплоя

## Локальная разработка (5 минут)

### 1. Клонируйте репозиторий

```bash
git clone https://github.com/erliona/dating.git
cd dating
```

### 2. Создайте .env файл

```bash
cp .env.example .env
```

### 3. Настройте BOT_TOKEN

Откройте `.env` и укажите ваш токен бота:

```env
BOT_TOKEN=123456789:ABCdefGHIjklMNOpqrsTUVwxyz
```

### 4. Запустите приложение

```bash
# Локальная разработка (без HTTPS)
docker compose -f docker-compose.dev.yml up -d

# Или продакшн режим (с HTTPS через Traefik)
docker compose up -d
```

### 5. Проверьте работу

```bash
# Посмотрите статус контейнеров
docker compose ps

# Проверьте логи бота
docker compose logs -f bot
```

### 6. Откройте бота в Telegram

Найдите вашего бота по имени в Telegram и отправьте `/start`

---

## Продакшн деплой через CI/CD (автоматический)

### 1. Форкните репозиторий

Создайте форк репозитория в вашем GitHub аккаунте.

### 2. Настройте GitHub Secrets

Перейдите в `Settings → Secrets and variables → Actions` и добавьте:

**Обязательные секреты**:
- `DEPLOY_HOST` - IP или домен вашего сервера
- `DEPLOY_USER` - SSH пользователь (с sudo правами)
- `DEPLOY_SSH_KEY` - Приватный SSH ключ для доступа
- `BOT_TOKEN` - Telegram bot token от @BotFather

**Опциональные секреты (для HTTPS)**:
- `DOMAIN` - Ваш домен (например, dating.example.com)
- `ACME_EMAIL` - Email для уведомлений Let's Encrypt

### 3. Запустите деплой

```bash
# Пуш в main ветку автоматически запустит деплой
git push origin main

# Или запустите вручную через GitHub Actions
```

### 4. Проверьте деплой

После деплоя ваше приложение будет доступно:
- Bot: в Telegram
- WebApp: https://your-domain.com
- Grafana: http://your-server:3000 (admin/admin)
- Prometheus: http://your-server:9090

---

## Мониторинг (опционально)

### Запуск с мониторингом

```bash
# Локально
docker compose -f docker-compose.dev.yml --profile monitoring up -d

# Продакшн (мониторинг включен по умолчанию при деплое)
docker compose --profile monitoring up -d
```

### Доступ к дашбордам

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **cAdvisor**: http://localhost:8081

---

## Проверка здоровья системы

### Проверить статус всех сервисов

```bash
docker compose ps
```

Все сервисы должны быть в статусе `Up` и `healthy`.

### Проверить логи

```bash
# Все сервисы
docker compose logs -f

# Только бот
docker compose logs -f bot

# Только база данных
docker compose logs -f db
```

### Подключиться к базе данных

```bash
docker compose exec db psql -U dating -d dating

# Полезные команды:
# \dt              - список таблиц
# \d profiles      - структура таблицы profiles
# SELECT COUNT(*) FROM profiles;  - количество профилей
```

---

## Остановка и очистка

### Остановить приложение

```bash
docker compose down
```

### Остановить и удалить данные (⚠️ удалит все профили!)

```bash
docker compose down -v
```

### Очистить старые образы

```bash
docker system prune -a
```

---

## Следующие шаги

После успешного запуска:

1. **Настройте мониторинг** - см. [Monitoring Guide](../monitoring/README.md)
2. **Изучите архитектуру** - см. [Architecture Documentation](ARCHITECTURE.md)
3. **Запустите тесты** - см. [Testing Guide](TESTING.md)
4. **Кастомизируйте WebApp** - см. [WebApp Customization](WEBAPP.md)

---

## Частые проблемы

### Бот не отвечает

**Причины**:
- Неправильный BOT_TOKEN
- Контейнер не запущен
- База данных недоступна

**Решение**:
```bash
# Проверьте логи
docker compose logs bot

# Перезапустите
docker compose restart bot
```

### База данных не подключается

**Причины**:
- Изменился пароль БД
- Volume поврежден

**Решение**:
```bash
# Пересоздайте БД (⚠️ удалит данные)
docker compose down -v
docker compose up -d
```

### WebApp показывает 404

**Причины**:
- Неправильный WEBAPP_URL в .env
- nginx контейнер не запущен

**Решение**:
```bash
# Проверьте конфигурацию
docker compose ps webapp
docker compose logs webapp

# Перезапустите WebApp
docker compose restart webapp
```

---

## Получение помощи

- 📖 [Полная документация](../README.md)
- 🐛 [Создать issue](https://github.com/erliona/dating/issues)
- 💬 [Обсуждения](https://github.com/erliona/dating/discussions)

---

**Успешного деплоя! 🎉**
