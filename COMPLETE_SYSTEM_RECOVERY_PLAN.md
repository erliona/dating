# КРИТИЧЕСКИЙ План Восстановления Dating App

## 🔥 **МАКСИМАЛЬНО ГЛУБОКАЯ ДИАГНОСТИКА - 7 БЛОКИРУЮЩИХ ПРОБЛЕМ**

### **БЛОКИРУЮЩИЕ проблемы (ДЕТАЛЬНЫЙ анализ):**

#### 1. **Миграции 007-011 в `.bak` формате** ❌❌❌ БЛОКИРУЕТ ВСЁ
- **Локация**: `/root/dating-microservices/migrations/versions/*.bak`
- **Статус**: Alembic не видит `.bak` файлы
- **Current DB version**: `006_fix_discovery_tables_timezone`
- **Отсутствующие таблицы**: 
  * `conversations` (для чатов)
  * `messages` (для сообщений)
  * `notifications` (для уведомлений)
  * `reports` (для жалоб)
  * `user_preferences` (для настроек)
  * `user_activity` (для активности)
  * `likes` (для лайков/Who Liked You)
- **Последствия**: Chat, notifications, verification, reports - ПОЛНОСТЬЮ НЕ РАБОТАЮТ
- **Проверено**: 77 Python файлов на сервере, миграции 007-011 все `.bak`

#### 2. **API Gateway и локальный репо синхронизированы** ✅ НЕ ПРОБЛЕМА
- **Статус**: gateway/ УЖЕ ЕСТЬ локально!
- **Размер на сервере**: 32K
- **Проверено**: `gateway/main.py` exists locally
- **Заключение**: Это НЕ проблема, изначальное предположение было ошибочным

#### 3. **Prometheus targets используют Docker Compose full names** ❌ CRITICAL
- **Проблема**: `prometheus.yml` содержит `dating-microservices-api-gateway-1:8080`
- **Docker DNS**: резолвит только короткие имена: `api-gateway`, `auth-service`, и т.д.
- **Статус**: ВСЕ application services показывают `down` в Prometheus
- **Error**: `dial tcp: lookup dating-microservices-discovery-service-1 on 127.0.0.11:53: server misbehaving`
- **Последствия**: Мониторинг ПОЛНОСТЬЮ сломан, невозможно видеть метрики
- **Alerts firing**: ContainerDown для всех app services, HighMemoryUsage для cadvisor

#### 4. **Admin Panel JWT middleware блокирует login** ❌ CRITICAL
- **Проблема**: `admin_jwt_middleware` применяется КО ВСЕМ endpoints
- **Endpoint**: `POST /admin/auth/login` возвращает 401
- **Error**: `{"error": "Missing or invalid Authorization header"}`
- **Тест**: `curl -X POST http://localhost:8086/admin/auth/login -d '{"username":"admin","password":"test"}'` → 401
- **Последствия**: Невозможно войти в админку, управление приложением заблокировано

#### 5. **ADMIN_PASSWORD отсутствует в .env** ❌ CRITICAL
- **Проверено**: `grep ADMIN_PASSWORD /root/dating-microservices/.env` → пусто
- **Есть в .env**: 
  * `BOT_TOKEN=8302871321:AAGDRnSDYdYHeEOqtEoKZVYLCbBlI2GBYMM`
  * `JWT_SECRET` (дублируется дважды!)
  * `WEBAPP_URL=https://dating.serge.cc`
  * `POSTGRES_PASSWORD=Fdc445fd222jhXc3Dk7`
- **Последствия**: Даже если исправить JWT middleware, логин не будет работать

#### 6. **JWT_SECRET дублируется в .env** ⚠️ MEDIUM
- **Строка 2**: `JWT_SECRET=8abfc6624ce93e31810f896ec26cab132aeed45950f09fe27dcfd9abe0c8ddb3`
- **Строка 15**: `JWT_SECRET=wUZg5LFQv3nVxp3WWROJxoXaSCgu5dvIYcIU1GH4UzU`
- **Риск**: Разные сервисы могут использовать разные ключи → токены не валидны
- **Последствия**: Потенциальная несовместимость JWT между сервисами

#### 7. **WebApp не может обратиться к API через `/api/v1/`** ❌ CRITICAL
- **Проблема**: Traefik forwards `/api/v1/...` → API Gateway ожидает `/v1/...`
- **Тест 1**: `curl https://dating.serge.cc/api/v1/auth/health` → 404
- **Тест 2**: `curl http://localhost:8080/v1/auth/health` → 200 OK
- **Traefik rule**: `PathPrefix(/api) && !PathPrefix(/api/profiles)` ✅ correct
- **API Gateway routes**: `/v1/auth/{tail:.*}` ✅ correct
- **Проблема**: `/api` prefix НЕ stripped перед forwarding в Gateway
- **Последствия**: WebApp НЕ МОЖЕТ делать API calls, Mini App НЕ РАБОТАЕТ

### **ЧТО РАБОТАЕТ (подтверждено):**

✅ **API Gateway**: Healthy, видит все 7 сервисов, отвечает на `/health`
✅ **All Services**: auth(8081), profile(8082), discovery(8083), media(8084), chat(8085), admin(8086), notification(8087) - все healthy
✅ **Database**: PostgreSQL работает, 8 таблиц существуют (users, profiles, photos, matches, interactions, favorites, admins, alembic_version)
✅ **Telegram Bot**: Подключен (@zintradating_bot), BOT_TOKEN valid
✅ **WebApp Static**: https://dating.serge.cc отдает HTML + JS bundle
✅ **Traefik**: SSL работает, routing rules configured
✅ **Docker Network**: Все контейнеры в одной сети, могут видеть друг друга по коротким именам

## 📋 **ПОЛНЫЙ ДЕТАЛЬНЫЙ План Исправления**

### **Этап 1: Восстановить миграции БД** (БЛОКИРУЕТ всё!)

1. Переименовать `.bak` → `.py`:
   ```bash
   ssh root@dating.serge.cc "cd /root/dating-microservices && docker compose exec telegram-bot bash -c 'cd /app/migrations/versions && for f in *.bak; do mv \"\$f\" \"\${f%.bak}\"; done'"
   ```

2. Verify rename:
   ```bash
   ssh root@dating.serge.cc "cd /root/dating-microservices && docker compose exec telegram-bot ls -la /app/migrations/versions/ | grep -E '007|008|009|010|011'"
   # Должны быть .py files, НЕ .bak
   ```

3. Check current DB version:
   ```bash
   ssh root@dating.serge.cc "cd /root/dating-microservices && docker compose exec -T db psql -U dating -d dating -c 'SELECT version_num FROM alembic_version;'"
   # Текущая: 006_fix_discovery_tables_timezone
   ```

4. Restart bot to apply migrations:
   ```bash
   ssh root@dating.serge.cc "cd /root/dating-microservices && docker compose restart telegram-bot"
   ```

5. Watch migration logs:
   ```bash
   ssh root@dating.serge.cc "cd /root/dating-microservices && docker compose logs -f telegram-bot | grep -E 'migration|alembic|upgrade|007|008|009|010|011'"
   ```

6. Verify tables created:
   ```bash
   ssh root@dating.serge.cc "cd /root/dating-microservices && docker compose exec -T db psql -U dating -d dating -c 'SELECT tablename FROM pg_tables WHERE schemaname = '\''public'\'' ORDER BY tablename;'"
   # Должны появиться: conversations, messages, notifications, reports, user_preferences, user_activity, likes
   ```

7. Verify final version:
   ```bash
   ssh root@dating.serge.cc "cd /root/dating-microservices && docker compose exec -T db psql -U dating -d dating -c 'SELECT version_num FROM alembic_version;'"
   # Должно быть: 011_create_likes_table
   ```

### **Этап 2: Исправить Prometheus мониторинг** (CRITICAL)

**Файл**: `monitoring/prometheus/prometheus.yml` lines 88-96

**Было**:
```yaml
- targets:
    - 'dating-microservices-api-gateway-1:8080'
    - 'dating-microservices-auth-service-1:8081'
    ...
```

**Должно быть**:
```yaml
- targets:
    - 'api-gateway:8080'
    - 'auth-service:8081'
    - 'profile-service:8082'
    - 'discovery-service:8083'
    - 'media-service:8084'
    - 'chat-service:8085'
    - 'admin-service:8086'
    - 'notification-service:8087'
    - 'data-service:8088'
```

**relabel_configs** (lines 102-128): Обновить все regex patterns с `dating-microservices-.*-1` на short names

**Deploy**:
```bash
scp monitoring/prometheus/prometheus.yml root@dating.serge.cc:/root/dating-microservices/monitoring/prometheus/
ssh root@dating.serge.cc "cd /root/dating-microservices && docker compose restart prometheus"
```

**Verify**:
```bash
ssh root@dating.serge.cc "curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.health != \"up\") | {job: .labels.job, instance: .labels.instance, health: .health}'"
# Должен вернуть пустой массив []
```

### **Этап 3: Исправить WebApp routing `/api/v1/`** (CRITICAL)

**Проблема**: Traefik forwards `/api/v1/auth/health` → Gateway получает `/api/v1/auth/health` → Ищет route → НЕ находит (есть только `/v1/auth/{tail}`)

**Решение**: Add Traefik middleware to strip `/api` prefix

**Файл**: `docker-compose.yml`

**Добавить** после line 276 (в секции api-gateway labels):
```yaml
      # Middleware to strip /api prefix
      - "traefik.http.middlewares.strip-api.stripprefix.prefixes=/api"
      - "traefik.http.routers.api-gateway.middlewares=strip-api,redirect-to-https"
      - "traefik.http.routers.api-gateway-secure.middlewares=strip-api"
```

**Обновить** line 284 (убрать старый middleware):
```yaml
# Было:
      - "traefik.http.routers.api-gateway.middlewares=redirect-to-https"
# Должно быть уже обновлено выше
```

**Deploy**:
```bash
scp docker-compose.yml root@dating.serge.cc:/root/dating-microservices/
ssh root@dating.serge.cc "cd /root/dating-microservices && docker compose up -d api-gateway"
```

**Test**:
```bash
ssh root@dating.serge.cc "curl -s https://dating.serge.cc/api/v1/auth/health"
# Должен вернуть: {"status": "healthy", "service": "auth"}
```

### **Этап 4: Исправить Admin Panel authentication** (CRITICAL)

**Проблема**: JWT middleware на ВСЕХ routes, включая `/admin/auth/login`

**Файл**: `services/admin/main.py`

**Найти** функцию `setup_app()` (около line 270-300)

**Заменить** структуру:
```python
def setup_app() -> web.Application:
    # Main app WITHOUT JWT middleware
    app = web.Application(
        middlewares=[
            correlation_middleware,
            user_context_middleware,
            request_logging_middleware,
            metrics_middleware,
        ]
    )
    
    # PUBLIC routes (NO JWT)
    app.router.add_post("/admin/auth/login", login_handler)
    app.router.add_get("/health", health_handler)
    
    # PROTECTED sub-app WITH JWT middleware
    protected = web.Application(middlewares=[admin_jwt_middleware])
    protected.router.add_get("/users", get_users_handler)
    protected.router.add_post("/users/{user_id}/ban", ban_user_handler)
    protected.router.add_get("/photos/pending", get_pending_photos_handler)
    protected.router.add_post("/photos/{photo_id}/approve", approve_photo_handler)
    protected.router.add_post("/photos/{photo_id}/reject", reject_photo_handler)
    # ... all other protected routes ...
    
    # Mount protected app under /admin/api
    app.add_subapp("/admin/api/", protected)
    
    add_metrics_route(app)
    
    return app
```

### **Этап 5: Добавить ADMIN_PASSWORD** (CRITICAL)

1. Generate password:
   ```bash
   ADMIN_PASSWORD=$(python3 -c "import secrets; print(secrets.token_urlsafe(16))")
   echo "Generated ADMIN_PASSWORD: $ADMIN_PASSWORD"
   # Save this!
   ```

2. Add to `.env` on server:
   ```bash
   ssh root@dating.serge.cc "cd /root/dating-microservices && echo 'ADMIN_PASSWORD=$ADMIN_PASSWORD' >> .env"
   ```

3. Update `docker-compose.yml` - add to admin-service environment (around line 200):
   ```yaml
   admin-service:
     environment:
       ADMIN_PASSWORD: ${ADMIN_PASSWORD}
   ```

4. Deploy:
   ```bash
   scp services/admin/main.py root@dating.serge.cc:/root/dating-microservices/services/admin/
   scp docker-compose.yml root@dating.serge.cc:/root/dating-microservices/
   ssh root@dating.serge.cc "cd /root/dating-microservices && docker compose build admin-service && docker compose up -d admin-service"
   ```

5. Test login:
   ```bash
   ssh root@dating.serge.cc "curl -X POST http://localhost:8086/admin/auth/login -H 'Content-Type: application/json' -d '{\"username\":\"admin\",\"password\":\"$ADMIN_PASSWORD\"}'"
   # Должен вернуть JWT token
   ```

### **Этап 6: Исправить дубликат JWT_SECRET** (MEDIUM)

1. Check current duplicates:
   ```bash
   ssh root@dating.serge.cc "cd /root/dating-microservices && grep -n JWT_SECRET .env"
   # Покажет 2 строки
   ```

2. Remove duplicate (keep first one):
   ```bash
   ssh root@dating.serge.cc "cd /root/dating-microservices && sed -i '15d' .env"
   # Удалить строку 15 (второй JWT_SECRET)
   ```

3. Verify:
   ```bash
   ssh root@dating.serge.cc "cd /root/dating-microservices && grep -c JWT_SECRET .env"
   # Должно быть 1
   ```

4. Restart all services to pick up correct JWT_SECRET:
   ```bash
   ssh root@dating.serge.cc "cd /root/dating-microservices && docker compose restart auth-service profile-service discovery-service media-service chat-service admin-service notification-service"
   ```

### **Этап 7: ПОЛНАЯ ВАЛИДАЦИЯ СИСТЕМЫ**

#### 7.1 Database Check:
```bash
ssh root@dating.serge.cc "cd /root/dating-microservices && docker compose exec -T db psql -U dating -d dating -c 'SELECT COUNT(*) as table_count FROM pg_tables WHERE schemaname = '\''public'\'';'"
# Должно быть >= 15

ssh root@dating.serge.cc "cd /root/dating-microservices && docker compose exec -T db psql -U dating -d dating -c 'SELECT tablename FROM pg_tables WHERE schemaname = '\''public'\'' ORDER BY tablename;'"
# Проверить наличие всех таблиц
```

#### 7.2 All Services Health:
```bash
for port in 8080 8081 8082 8083 8084 8085 8086 8087 8088; do
  echo "=== Port $port ==="
  ssh root@dating.serge.cc "curl -s http://localhost:$port/health | jq"
done
```

#### 7.3 Prometheus Check:
```bash
ssh root@dating.serge.cc "curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job: .labels.job, health: .health}'"
# Все должны быть "up"

ssh root@dating.serge.cc "cd /root/dating-microservices && ./scripts/check_alerts.sh"
# Должно быть 0 firing alerts
```

#### 7.4 WebApp API Access:
```bash
ssh root@dating.serge.cc "curl -s https://dating.serge.cc/api/v1/auth/health"
# {"status": "healthy", "service": "auth"}

ssh root@dating.serge.cc "curl -s https://dating.serge.cc/api/v1/profile/health"
# {"status": "healthy", "service": "profile"}
```

#### 7.5 Telegram Bot Mini App:
- Открыть Telegram → @zintradating_bot
- Отправить `/start`
- Нажать "Открыть Mini App"
- Проверить что загружается (не белый экран)
- Open DevTools Console → не должно быть ошибок API

#### 7.6 Admin Panel:
```bash
curl -X POST https://dating.serge.cc/admin/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"<ADMIN_PASSWORD>"}'
# Должен вернуть JWT token
```

### **Этап 8: Обновить правила Cursor AI** (ВАЖНО - lessons learned)

**Цель**: Задокументировать найденные паттерны ошибок для предотвращения в будущем.

**Файл**: `.cursor/rules`

**Действия**:

1. Открыть `.cursor/rules` и добавить новый раздел в конец файла

2. Добавить следующий раздел:

```
## System Recovery & Deep Diagnostics (Added 2025-10-24)

### Critical Patterns Found in Production Incident:

1. MIGRATION FILES WITH .bak EXTENSION
   - Alembic ignores non-.py files
   - Always check: docker compose exec telegram-bot ls /app/migrations/versions/
   - Fix: rename .bak to .py

2. PROMETHEUS USES FULL CONTAINER NAMES
   - Docker DNS only resolves SHORT service names
   - Bad: dating-microservices-api-gateway-1:8080
   - Good: api-gateway:8080
   - Fix: update prometheus.yml targets

3. JWT MIDDLEWARE ON LOGIN ENDPOINT
   - Middleware applied to ALL routes blocks login
   - Fix: separate public routes from protected sub-app

4. MISSING ENVIRONMENT VARIABLES
   - Check for: ADMIN_PASSWORD, JWT_SECRET, BOT_TOKEN
   - Look for duplicates: grep -n VAR_NAME .env

5. API PATH ROUTING MISMATCH
   - Traefik forwards /api/v1/auth → Gateway expects /v1/auth
   - Fix: add stripprefix middleware in Traefik

### Deep Diagnostics Checklist:

When system is broken, run in this order:

1. Check container status:
   docker compose ps -a

2. Check migration files:
   docker compose exec telegram-bot ls -la /app/migrations/versions/

3. Check DB version:
   docker compose exec -T db psql -U dating -d dating -c "SELECT version_num FROM alembic_version;"

4. Check all service health:
   for port in 8080 8081 8082 8083 8084 8085 8086 8087 8088; do
     curl -s http://localhost:$port/health
   done

5. Check Prometheus targets:
   curl -s http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.health != "up")'

6. Check Prometheus alerts:
   ./scripts/check_alerts.sh

7. Check environment variables:
   grep -E "(PASSWORD|SECRET|TOKEN)" .env

8. Test API routing end-to-end:
   curl https://domain.com/api/v1/auth/health
   curl http://localhost:8080/v1/auth/health
   curl http://localhost:8081/health

### Prevention Rules:

- NEVER assume local repo matches production server
- ALWAYS verify files inside Docker containers (not just host)
- CHECK for .bak, .old, .disabled file extensions
- USE Docker service names in configs, not full container names
- TEST end-to-end flows, not just component health
- VERIFY environment variables are set and not duplicated
```

3. Сохранить файл

4. Зафиксировать изменения:
```bash
git add .cursor/rules
git commit -m "docs: add system recovery diagnostics to cursor rules

Added lessons learned from production incident:
- Check for .bak migration files
- Use Docker DNS short names
- Prevent JWT middleware on login endpoints
- Deep diagnostics checklist
- API routing verification steps
"
```

### **Этап 9: Commit все изменения**

```bash
git add .
git commit -m "fix: restore full system functionality

CRITICAL FIXES:
- Restore migrations 007-011 from .bak format
- Fix Prometheus targets (use Docker DNS short names)
- Fix Admin JWT middleware (separate public/protected routes)
- Add ADMIN_PASSWORD to environment
- Fix WebApp API routing (strip /api prefix in Traefik)
- Remove duplicate JWT_SECRET from .env

TABLES RESTORED:
- conversations, messages (chat functionality)
- notifications (push notifications)
- reports (moderation)
- user_preferences, user_activity (settings & analytics)
- likes (Who Liked You feature)

MONITORING RESTORED:
- All Prometheus targets now UP
- 0 firing alerts
- Full observability restored

DOCUMENTATION:
- Updated .cursor/rules with system recovery procedures
- Added deep diagnostics checklist
- Documented common critical patterns

Closes: #migrations #monitoring #admin-auth #webapp-routing"

git push origin main
```

## 📊 **Execution Order (STRICT)**

1. ✅ **Restore migrations** (15 min) - BLOCKS chat, notifications, reports
2. ✅ **Fix Prometheus** (10 min) - restores monitoring
3. ✅ **Fix WebApp routing** (10 min) - BLOCKS Mini App functionality
4. ✅ **Fix Admin JWT** (15 min) - restores admin panel
5. ✅ **Add ADMIN_PASSWORD** (5 min) - enables admin login
6. ✅ **Remove JWT duplicate** (5 min) - prevents token issues
7. ✅ **Full system validation** (20 min) - verify everything works
8. ✅ **Update cursor rules** (10 min) - document lessons learned
9. ✅ **Commit changes** (5 min) - save work

**Total Time:** ~95 минут

## 🔥 **Критичность (финальная)**

1. **Migrations (.bak)** - БЛОКИРУЕТ (0 таблиц из 7 новых)
2. **WebApp routing** - БЛОКИРУЕТ (Mini App не может делать API calls)
3. **Admin JWT + PASSWORD** - БЛОКИРУЕТ (невозможно войти в админку)
4. **Prometheus** - HIGH (нет мониторинга)
5. **JWT duplicate** - MEDIUM (риск несовместимости токенов)

## ✅ **Ожидаемый результат**

- ✅ 15+ таблиц БД существуют
- ✅ Migration version: 011_create_likes_table
- ✅ Prometheus: все targets UP, 0 alerts
- ✅ Admin panel: login работает
- ✅ WebApp: API calls работают через https://dating.serge.cc/api/v1/
- ✅ Mini App: открывается и функционирует
- ✅ Chat, notifications, reports: полностью работают
- ✅ **СИСТЕМА ПОЛНОСТЬЮ РАБОТОСПОСОБНА**
