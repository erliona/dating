# Mini App Production Troubleshooting

## 🚨 Проблема: Мини-приложение не открывается в production

### Быстрая диагностика

Запустите скрипт диагностики:
```bash
./scripts/diagnose-miniapp.sh
```

### Ручная проверка

#### 1. Проверьте статус сервисов
```bash
docker compose ps
```

Должны быть запущены:
- ✅ `traefik` - reverse proxy
- ✅ `db` - база данных  
- ✅ `api-gateway` - API шлюз
- ✅ `telegram-bot` - бот
- ✅ `webapp` - веб-приложение

#### 2. Проверьте логи бота
```bash
docker compose logs telegram-bot --tail=20
```

Ищите ошибки:
- `Unauthorized` - неверный BOT_TOKEN
- `Connection refused` - проблемы с API Gateway
- `WebApp URL` - неправильный URL мини-приложения

#### 3. Проверьте доступность WebApp
```bash
# Внутри контейнера
docker compose exec webapp curl -s http://localhost:3000

# Через Traefik
curl -s -I http://localhost/webapp
```

#### 4. Проверьте конфигурацию
```bash
# Проверьте .env файл
cat .env | grep -E "(BOT_TOKEN|WEBAPP_URL|DOMAIN)"

# Проверьте Traefik маршруты
curl -s http://localhost:8091/api/rawdata | grep -A5 -B5 webapp
```

## 🔧 Частые проблемы и решения

### 1. BOT_TOKEN неверный или неактивный

**Симптомы:**
- Бот не отвечает на команды
- Логи показывают `Unauthorized`

**Решение:**
```bash
# Получите новый токен от @BotFather
# Обновите .env файл
sed -i 's/BOT_TOKEN=.*/BOT_TOKEN=YOUR_NEW_TOKEN/' .env

# Перезапустите бота
docker compose restart telegram-bot
```

### 2. WebApp URL неправильно настроен

**Симптомы:**
- Мини-приложение показывает черный экран
- Ошибки в консоли браузера

**Решение:**
```bash
# Убедитесь что WEBAPP_URL правильный
echo "WEBAPP_URL=https://yourdomain.com/webapp" >> .env

# Перезапустите все сервисы
docker compose restart
```

### 3. SSL сертификат не работает

**Симптомы:**
- Telegram показывает "Небезопасное соединение"
- Ошибки SSL в логах

**Решение:**
```bash
# Проверьте домен
curl -s -I https://yourdomain.com/webapp

# Если не работает, проверьте Let's Encrypt
docker compose logs traefik | grep -i certificate
```

### 4. Traefik не маршрутизирует запросы

**Симптомы:**
- 404 ошибки при обращении к WebApp
- Traefik dashboard не показывает маршруты

**Решение:**
```bash
# Проверьте labels в docker-compose.yml
docker compose config | grep -A10 -B5 webapp

# Перезапустите Traefik
docker compose restart traefik
```

### 5. API Gateway недоступен

**Симптомы:**
- WebApp загружается, но API не работает
- Ошибки 502/503 в логах

**Решение:**
```bash
# Проверьте API Gateway
curl -s http://localhost:8080/health

# Проверьте логи
docker compose logs api-gateway --tail=20
```

## 📊 Мониторинг

### Grafana Dashboard
```bash
# Откройте Grafana
open http://localhost:3000
# Логин: admin/admin
```

### Prometheus метрики
```bash
# Проверьте метрики
curl -s http://localhost:9090/api/v1/query?query=up
```

### Loki логи
```bash
# Поиск логов
curl -s "http://localhost:3100/loki/api/v1/query?query={service=\"telegram-bot\"}"
```

## 🚀 Команды для быстрого исправления

### Полный перезапуск
```bash
docker compose down
docker compose up -d
```

### Перезапуск только проблемного сервиса
```bash
docker compose restart telegram-bot
docker compose restart webapp
docker compose restart api-gateway
```

### Проверка ресурсов
```bash
# Память и CPU
docker stats

# Дисковое пространство
df -h
docker system df
```

### Очистка и пересборка
```bash
# Очистка неиспользуемых образов
docker system prune -f

# Пересборка образов
docker compose build --no-cache
docker compose up -d
```

## 📞 Получение помощи

Если проблема не решается:

1. **Соберите информацию:**
   ```bash
   ./scripts/diagnose-miniapp.sh > diagnosis.log
   docker compose logs > all-logs.log
   ```

2. **Проверьте GitHub Issues:**
   - [Issues](https://github.com/erliona/dating/issues)
   - [Discussions](https://github.com/erliona/dating/discussions)

3. **Создайте новый Issue** с:
   - Выводом `diagnosis.log`
   - Описанием проблемы
   - Шагами для воспроизведения

---

**Последнее обновление:** 2025-01-22  
**Версия:** 1.0
