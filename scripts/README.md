# Deployment Scripts

Этот набор скриптов решает проблему с кешированием Docker и обеспечивает надежный деплой изменений.

## Проблема

Docker часто кеширует слои и не пересобирает образы при изменениях в коде, что приводит к тому, что изменения не применяются на сервере.

## Решение

### 1. `force-deploy.sh` - Принудительный деплой

Полностью пересобирает сервисы без кеша:

```bash
# Деплой всех сервисов
./scripts/force-deploy.sh

# Деплой конкретных сервисов
./scripts/force-deploy.sh webapp api-gateway profile-service
```

**Что делает:**
- Останавливает сервисы
- Удаляет контейнеры
- Пересобирает образы без кеша (`--no-cache`)
- Запускает новые контейнеры
- Показывает статус и логи

### 2. `quick-deploy.sh` - Быстрый деплой одного сервиса

Для быстрого деплоя одного сервиса:

```bash
# Деплой только webapp
./scripts/quick-deploy.sh webapp

# Деплой только API Gateway
./scripts/quick-deploy.sh api-gateway
```

### 3. `deploy-to-server.sh` - Деплой на сервер

Автоматически копирует файлы на сервер и запускает force deploy:

```bash
# Деплой webapp на сервер
./scripts/deploy-to-server.sh webapp

# Деплой нескольких сервисов
./scripts/deploy-to-server.sh webapp api-gateway profile-service
```

**Что делает:**
- Копирует скрипты деплоя на сервер
- Копирует измененные файлы (webapp/src, gateway/, services/*)
- Запускает force deploy на сервере

## Использование

### Локальная разработка

```bash
# Быстрый деплой одного сервиса
./scripts/quick-deploy.sh webapp

# Полный пересбор всех сервисов
./scripts/force-deploy.sh
```

### Деплой на продакшн

```bash
# Деплой webapp на сервер
./scripts/deploy-to-server.sh webapp

# Деплой API Gateway на сервер
./scripts/deploy-to-server.sh api-gateway

# Деплой нескольких сервисов
./scripts/deploy-to-server.sh webapp api-gateway profile-service
```

## Доступные сервисы

- `webapp` - Next.js приложение
- `api-gateway` - API Gateway
- `profile-service` - Profile Service
- `auth-service` - Auth Service
- `discovery-service` - Discovery Service
- `media-service` - Media Service
- `chat-service` - Chat Service
- `admin-service` - Admin Service
- `notification-service` - Notification Service

## Примеры

### Изменения в webapp

```bash
# 1. Внесите изменения в webapp/src/
# 2. Деплой на сервер
./scripts/deploy-to-server.sh webapp
```

### Изменения в API Gateway

```bash
# 1. Внесите изменения в gateway/
# 2. Деплой на сервер
./scripts/deploy-to-server.sh api-gateway
```

### Изменения в нескольких сервисах

```bash
# 1. Внесите изменения в несколько сервисов
# 2. Деплой всех измененных сервисов
./scripts/deploy-to-server.sh webapp api-gateway profile-service
```

## Проверка деплоя

После деплоя проверьте:

1. **Статус сервисов:**
   ```bash
   ssh root@dating.serge.cc "cd /opt/dating-microservices && docker compose ps"
   ```

2. **Логи сервисов:**
   ```bash
   ssh root@dating.serge.cc "cd /opt/dating-microservices && docker compose logs webapp --tail=20"
   ```

3. **Функциональность:**
   - Откройте приложение в браузере
   - Проверьте API endpoints
   - Убедитесь, что изменения применились

## Устранение проблем

### Если изменения не применились

1. **Проверьте, что скрипт выполнился без ошибок**
2. **Проверьте логи сервиса:**
   ```bash
   ssh root@dating.serge.cc "cd /opt/dating-microservices && docker compose logs webapp --tail=50"
   ```
3. **Попробуйте полный пересбор:**
   ```bash
   ./scripts/deploy-to-server.sh webapp
   ```

### Если сервис не запускается

1. **Проверьте статус:**
   ```bash
   ssh root@dating.serge.cc "cd /opt/dating-microservices && docker compose ps webapp"
   ```
2. **Проверьте логи ошибок:**
   ```bash
   ssh root@dating.serge.cc "cd /opt/dating-microservices && docker compose logs webapp"
   ```

## Преимущества

✅ **Надежность** - принудительная пересборка без кеша  
✅ **Автоматизация** - один скрипт для полного деплоя  
✅ **Быстрота** - деплой только измененных сервисов  
✅ **Отладка** - автоматический показ логов и статуса  
✅ **Безопасность** - проверка статуса после деплоя  

## История

Эти скрипты были созданы для решения проблемы с кешированием Docker, когда изменения в коде не применялись на сервере из-за того, что Docker использовал кешированные слои образов.
