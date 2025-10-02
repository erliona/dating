# 🚀 Руководство по развертыванию

Это руководство описывает различные способы развертывания Dating Bot в production.

## Содержание

- [Автоматический деплой через CI/CD (рекомендуется)](#автоматический-деплой-через-cicd)
- [Ручное развертывание](#ручное-развертывание)
- [Обслуживание и мониторинг](#обслуживание-и-мониторинг)
- [Резервное копирование](#резервное-копирование)
- [Решение проблем](#решение-проблем)

---

## Автоматический деплой через CI/CD

Рекомендуемый способ для production. Автоматизирует весь процесс развертывания.

### Требования

**На сервере**:
- Ubuntu 20.04+ / Debian 11+ / CentOS 8+
- SSH доступ с sudo правами
- Открытые порты: 22 (SSH), 80 (HTTP), 443 (HTTPS)
- Минимум 2GB RAM, 20GB disk space
- Docker и Docker Compose установятся автоматически

**В GitHub**:
- Форк репозитория
- Доступ к Settings (для настройки Secrets)

### Шаг 1: Подготовка SSH ключа

На локальной машине создайте SSH ключ для деплоя:

```bash
# Создайте новый SSH ключ (если нет)
ssh-keygen -t ed25519 -C "deploy@dating-bot" -f ~/.ssh/dating_deploy

# Скопируйте публичный ключ на сервер
ssh-copy-id -i ~/.ssh/dating_deploy.pub user@your-server.com

# Проверьте доступ
ssh -i ~/.ssh/dating_deploy user@your-server.com
```

### Шаг 2: Настройка GitHub Secrets

Перейдите в ваш репозиторий на GitHub:
**Settings → Secrets and variables → Actions → New repository secret**

#### Обязательные секреты:

| Секрет | Описание | Пример |
|--------|----------|--------|
| `DEPLOY_HOST` | IP адрес или домен сервера | `123.45.67.89` или `server.example.com` |
| `DEPLOY_USER` | SSH пользователь с sudo | `ubuntu` или `root` |
| `DEPLOY_SSH_KEY` | Приватный SSH ключ | Содержимое `~/.ssh/dating_deploy` |
| `BOT_TOKEN` | Telegram bot token | `123456789:ABCdef...` от @BotFather |

**Как добавить DEPLOY_SSH_KEY**:
```bash
# Linux/Mac
cat ~/.ssh/dating_deploy | pbcopy  # копирует в буфер

# Или выведите в консоль
cat ~/.ssh/dating_deploy
```

Скопируйте **весь** вывод, включая строки `-----BEGIN ... KEY-----` и `-----END ... KEY-----`.

#### Опциональные секреты (для HTTPS):

| Секрет | Описание | По умолчанию |
|--------|----------|--------------|
| `DOMAIN` | Ваш домен для HTTPS | `localhost` |
| `ACME_EMAIL` | Email для Let's Encrypt | `admin@example.com` |
| `POSTGRES_DB` | Имя БД | `dating` |
| `POSTGRES_USER` | Пользователь БД | `dating` |
| `POSTGRES_PASSWORD` | Пароль БД | Генерируется автоматически |

⚠️ **Важно**: `DOMAIN` обязателен для получения SSL сертификата. DNS должен указывать на ваш сервер.

### Шаг 3: Настройка DNS (для HTTPS)

Если у вас есть домен, настройте A-запись:

```
Тип: A
Имя: dating (или @)
Значение: <IP вашего сервера>
TTL: 300
```

Проверьте DNS:
```bash
dig +short dating.example.com
# Должен вернуть IP вашего сервера
```

### Шаг 4: Запуск деплоя

**Автоматический** (при push в main):
```bash
git add .
git commit -m "Configure production deployment"
git push origin main
```

**Ручной** (через GitHub UI):
1. Откройте **Actions** в репозитории
2. Выберите workflow **Deploy**
3. Нажмите **Run workflow** → **Run workflow**

### Шаг 5: Мониторинг деплоя

Следите за прогрессом в GitHub Actions:
- ✅ Зеленая галочка = успешный деплой
- ❌ Красный крестик = ошибка (см. логи)

После успешного деплоя:

**Проверьте сервисы**:
```bash
ssh user@your-server "cd /opt/dating && docker compose ps"
```

Все сервисы должны быть `Up` и `healthy`.

**Проверьте бота**:
- Откройте Telegram
- Найдите вашего бота
- Отправьте `/start`

**Проверьте WebApp**:
- Откройте https://your-domain.com
- Должна загрузиться форма профиля

**Проверьте мониторинг** (опционально):
- Grafana: http://your-server:3000 (admin/admin)
- Prometheus: http://your-server:9090

### Что происходит при деплое?

1. **Проверка секретов** - валидация наличия обязательных секретов
2. **SSH подключение** - настройка безопасного соединения с сервером
3. **Подготовка сервера**:
   - Проверка и установка Docker/Docker Compose
   - Создание директории `/opt/dating`
   - Настройка прав доступа
4. **Загрузка проекта** - rsync файлов на сервер
5. **Генерация .env** - создание конфигурации из секретов
6. **Валидация** - проверка BOT_TOKEN и других параметров
7. **Развертывание**:
   - Остановка старых контейнеров (graceful shutdown)
   - Сохранение текущего .env как .env.previous
   - Проверка изменения пароля БД
   - Сборка новых образов
   - Запуск с мониторингом
8. **Health check** - проверка работоспособности всех сервисов

---

## Ручное развертывание

Для случаев когда CI/CD недоступен.

### Предварительные требования

На сервере должны быть установлены:
- Docker Engine 20.10+
- Docker Compose v2.0+
- Git

```bash
# Установка Docker (Ubuntu/Debian)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Добавить пользователя в группу docker
sudo usermod -aG docker $USER

# Перелогиньтесь для применения изменений
```

### Шаг 1: Клонирование репозитория

```bash
cd /opt
sudo mkdir dating
sudo chown $USER:$USER dating
cd dating

git clone https://github.com/erliona/dating.git .
```

### Шаг 2: Конфигурация

```bash
# Скопируйте пример
cp .env.example .env

# Отредактируйте переменные
nano .env
```

**Минимальная конфигурация** для .env:
```env
BOT_TOKEN=your-telegram-bot-token-here
POSTGRES_DB=dating
POSTGRES_USER=dating
POSTGRES_PASSWORD=secure_password_here
DOMAIN=your-domain.com
WEBAPP_URL=https://your-domain.com
ACME_EMAIL=admin@your-domain.com
```

⚠️ **Важно**: Используйте только алфавитно-цифровые символы для `POSTGRES_PASSWORD`

### Шаг 3: Развертывание

```bash
# Запуск с мониторингом
docker compose --profile monitoring up -d --build

# Проверка статуса
docker compose ps

# Просмотр логов
docker compose logs -f
```

### Шаг 4: Проверка

```bash
# Проверить все контейнеры
docker compose ps

# Должно быть ~13 контейнеров в статусе Up:
# - traefik (reverse proxy)
# - db (PostgreSQL)
# - bot (приложение)
# - webapp (nginx)
# - prometheus, grafana, loki, promtail (мониторинг)
# - cadvisor, node-exporter, postgres-exporter (экспортеры метрик)

# Проверить логи бота
docker compose logs bot | tail -50

# Проверить БД
docker compose exec db pg_isready -U dating
```

### Шаг 5: Настройка автозапуска

Создайте systemd service для автостарта после перезагрузки:

```bash
sudo nano /etc/systemd/system/dating-bot.service
```

Содержимое:
```ini
[Unit]
Description=Dating Bot
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/opt/dating
ExecStart=/usr/bin/docker compose --profile monitoring up -d
ExecStop=/usr/bin/docker compose down
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
```

Активируйте:
```bash
sudo systemctl daemon-reload
sudo systemctl enable dating-bot.service
sudo systemctl start dating-bot.service
```

---

## Обновление приложения

### Через CI/CD

Просто сделайте push в main ветку - деплой запустится автоматически.

### Вручную

```bash
cd /opt/dating

# Сохраните текущий .env
cp .env .env.backup

# Получите обновления
git pull origin main

# Пересоберите и перезапустите
docker compose --profile monitoring up -d --build

# Проверьте статус
docker compose ps
```

---

## Обслуживание и мониторинг

### Просмотр логов

```bash
# Все сервисы
docker compose logs -f

# Только бот
docker compose logs -f bot

# Последние 100 строк
docker compose logs --tail=100 bot

# Логи за последний час
docker compose logs --since 1h bot
```

### Проверка ресурсов

```bash
# Использование CPU/Memory в реальном времени
docker stats

# Использование диска
docker system df
```

### Мониторинг через Grafana

1. Откройте http://your-server:3000
2. Логин: `admin`, Пароль: `admin` (измените при первом входе)
3. Перейдите в **Dashboards**
4. Выберите **Dating App - Overview**

**Основные метрики**:
- Active users (24h / 7d)
- Total matches
- Match rate
- Container resources
- Database performance

### Алерты

Настроенные алерты (в Prometheus):
- Контейнер упал (>1 минута)
- PostgreSQL недоступен (>1 минута)
- Memory usage >90% (>5 минут)
- CPU usage >80% (>10 минут)
- Disk space <10% (>5 минут)

Для получения уведомлений настройте Alertmanager (см. [monitoring/README.md](../monitoring/README.md)).

---

## Резервное копирование

### Автоматический backup базы данных

Создайте cron job:

```bash
sudo nano /etc/cron.daily/dating-backup
```

Содержимое:
```bash
#!/bin/bash
BACKUP_DIR="/opt/backups/dating"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p "$BACKUP_DIR"

# Backup базы данных
docker compose -f /opt/dating/docker-compose.yml exec -T db \
  pg_dump -U dating dating | gzip > "$BACKUP_DIR/db_$DATE.sql.gz"

# Удалить backups старше 30 дней
find "$BACKUP_DIR" -name "db_*.sql.gz" -mtime +30 -delete

echo "Backup completed: $BACKUP_DIR/db_$DATE.sql.gz"
```

Сделайте исполняемым:
```bash
sudo chmod +x /etc/cron.daily/dating-backup
```

### Ручной backup

```bash
# База данных
docker compose exec db pg_dump -U dating dating | gzip > backup-$(date +%Y%m%d).sql.gz

# Все volumes
docker run --rm \
  -v dating_postgres_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/volumes-$(date +%Y%m%d).tar.gz /data
```

### Восстановление из backup

```bash
# Восстановить БД
gunzip < backup-20240101.sql.gz | docker compose exec -T db psql -U dating dating

# Или полностью пересоздать
docker compose down -v  # ⚠️ удалит текущие данные
docker compose up -d
gunzip < backup-20240101.sql.gz | docker compose exec -T db psql -U dating dating
```

---

## Масштабирование

### Вертикальное масштабирование

Увеличьте ресурсы в docker-compose.yml:

```yaml
bot:
  deploy:
    resources:
      limits:
        memory: 1G  # было 512M
        cpus: '2'   # было не указано
```

### Горизонтальное масштабирование

Для multi-instance деплоя потребуется:
1. Redis для shared state
2. Load balancer
3. Message queue

См. [ROADMAP.md](../ROADMAP.md) для деталей.

---

## Решение проблем

### Бот не запускается

**Симптомы**: Контейнер bot постоянно перезапускается

**Решение**:
```bash
# Проверьте логи
docker compose logs bot

# Частые причины:
# 1. Неправильный BOT_TOKEN
# 2. БД недоступна
# 3. Ошибка в миграциях

# Проверьте подключение к БД
docker compose exec db pg_isready -U dating

# Проверьте BOT_TOKEN
grep BOT_TOKEN .env

# Пересоберите контейнер
docker compose up -d --build bot
```

### База данных не подключается

**Симптомы**: Ошибка "could not connect to server"

**Решение**:
```bash
# Проверьте статус БД
docker compose ps db

# Если контейнер stopped
docker compose up -d db

# Если пароль изменился - требуется пересоздать volume
# ⚠️ Это удалит все данные! Сделайте backup сначала
docker compose exec db pg_dump -U dating dating > backup.sql
docker compose down -v
docker compose up -d
docker compose exec -T db psql -U dating dating < backup.sql
```

### SSL сертификат не получается

**Симптомы**: "Failed to obtain certificate"

**Причины и решения**:

1. **DNS не настроен**:
```bash
# Проверьте DNS
dig +short your-domain.com
# Должен вернуть IP сервера
```

2. **Порты закрыты**:
```bash
# Проверьте firewall
sudo ufw status
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
```

3. **Лимит Let's Encrypt**:
   - Staging: используйте `ACME_CA_SERVER=https://acme-staging-v02.api.letsencrypt.org/directory`
   - Production: макс 5 попыток в неделю

4. **Проверьте логи Traefik**:
```bash
docker compose logs traefik | grep -i certificate
```

### Высокое использование памяти

**Решение**:

```bash
# Проверьте какой контейнер использует память
docker stats

# Обычно виновники:
# 1. Prometheus - уменьшите retention
# 2. Loki - уменьшите retention
# 3. Grafana - отключите неиспользуемые plugins

# Для Prometheus измените в docker-compose.yml (в секции prometheus):
# '--storage.tsdb.retention.time=15d'  # было 30d

# Перезапустите сервисы
docker compose --profile monitoring up -d --force-recreate prometheus
```

### Место на диске заканчивается

**Решение**:

```bash
# Проверьте использование
docker system df -v

# Очистите неиспользуемое
docker system prune -a -f

# Очистите старые логи
sudo journalctl --vacuum-time=7d

# Настройте ротацию логов Docker
sudo nano /etc/docker/daemon.json
```

Добавьте:
```json
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  }
}
```

Перезапустите Docker:
```bash
sudo systemctl restart docker
docker compose --profile monitoring up -d
```

---

## Best Practices

### Безопасность

1. **Измените пароли по умолчанию**:
   - Grafana admin (первый вход)
   - PostgreSQL (в .env)

2. **Ограничьте доступ к портам**:
```bash
# Закройте порты мониторинга от внешнего доступа
sudo ufw deny 3000  # Grafana
sudo ufw deny 9090  # Prometheus
sudo ufw allow from <your-ip> to any port 3000  # Разрешить только для вашего IP
```

3. **Регулярно обновляйте**:
```bash
# Еженедельно обновляйте образы
docker compose pull
docker compose --profile monitoring up -d
```

### Производительность

1. **Включите индексы БД** (уже настроены в миграциях)
2. **Мониторьте slow queries** через Grafana
3. **Настройте кэширование** (Redis - см. ROADMAP)

### Надежность

1. **Настройте автоматические backups** (см. выше)
2. **Тестируйте процедуру восстановления** ежемесячно
3. **Мониторьте алерты** в Grafana
4. **Ведите changelog** изменений конфигурации

---

## Чеклист деплоя

Перед запуском в production убедитесь:

- [ ] DNS настроен и указывает на сервер
- [ ] Firewall настроен (порты 22, 80, 443)
- [ ] Секреты настроены в GitHub
- [ ] BOT_TOKEN валиден и от правильного бота
- [ ] DOMAIN соответствует реальному домену
- [ ] .env файл содержит prod конфигурацию
- [ ] Пароль БД безопасный (не "dating")
- [ ] Автоматический backup настроен
- [ ] Мониторинг работает (Grafana доступна)
- [ ] SSL сертификат получен (https работает)
- [ ] Бот отвечает в Telegram
- [ ] WebApp загружается
- [ ] Процедура восстановления протестирована

---

## Получение помощи

- 📖 [Основная документация](../README.md)
- 🏗️ [Архитектура](ARCHITECTURE.md)
- 🚀 [Быстрый старт](GETTING_STARTED.md)
- 🐛 [Создать issue](https://github.com/erliona/dating/issues)

---

**Успешного деплоя! 🚀**
