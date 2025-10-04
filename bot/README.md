# ⚠️ DEPRECATED: Legacy Bot Code

## ⛔ This directory contains DEPRECATED code

**Статус**: Deprecated / Legacy  
**Дата**: 2024-01-10  
**Причина**: Переход на микросервисную архитектуру

---

## Миграция на микросервисы

Эта система полностью перешла на микросервисную архитектуру. Весь функционал теперь реализован через независимые сервисы:

### Новая архитектура

```
core/                    # Платформонезависимое ядро
├── models/             # Доменные модели
├── services/           # Бизнес-логика
├── interfaces/         # Контракты
└── utils/              # Утилиты (включая security, validation)

services/                # Микросервисы
├── auth/               # JWT, аутентификация (порт 8081)
├── profile/            # Профили (порт 8082)
├── discovery/          # Матчинг (порт 8083)
├── media/              # Фотографии (порт 8084)
└── chat/               # Сообщения (порт 8085)

gateway/                 # API Gateway (порт 8080)

adapters/                # Платформенные адаптеры
└── telegram/           # Telegram интеграция
```

### Миграция функциональности

| Старый файл | Новое расположение | Статус |
|-------------|-------------------|--------|
| `bot/security.py` | `core/utils/security.py` | ✅ Перенесено |
| `bot/validation.py` | `core/utils/validation.py` | ✅ Перенесено |
| `bot/main.py` | `services/*/` + `adapters/telegram/` | ⚠️ Устарело |
| `bot/api.py` | `services/*/` + `gateway/` | ⚠️ Устарело |
| `bot/db.py` | `core/models/` | ℹ️ Используется для миграций |
| `bot/repository.py` | `adapters/telegram/repository.py` | ℹ️ Используется адаптером |
| `bot/config.py` | Переменные окружения | ℹ️ Частично используется |

---

## Что делать, если нужна старая функциональность

### 1. Для разработчиков

Если вы работаете с этим кодом:

- ❌ **НЕ ИСПОЛЬЗУЙТЕ** код из bot/main.py или bot/api.py
- ✅ **ИСПОЛЬЗУЙТЕ** микросервисы из services/
- ✅ **ИСПОЛЬЗУЙТЕ** core/ для бизнес-логики
- ✅ **ИСПОЛЬЗУЙТЕ** adapters/ для платформенной интеграции

### 2. Для новых функций

Добавляйте новую функциональность в:
- `core/services/` - если это бизнес-логика
- `services/*/` - если это REST API endpoint
- `adapters/telegram/` - если это специфично для Telegram

### 3. Миграция существующего кода

См. [ARCHITECTURE_MIGRATION_GUIDE.md](../docs/ARCHITECTURE_MIGRATION_GUIDE.md)

---

## Развертывание

### ❌ Старый способ (НЕ ИСПОЛЬЗУЙТЕ)

```bash
# Это больше не работает
docker compose -f docker-compose.dev.yml up -d
```

### ✅ Новый способ (ИСПОЛЬЗУЙТЕ)

```bash
# Микросервисная архитектура
docker compose up -d

# Проверка статуса всех сервисов
docker compose ps

# Проверка health endpoints
for port in 8080 8081 8082 8083 8084 8085; do
  curl http://localhost:$port/health
done
```

---

## Документация

- [Архитектура системы](../docs/ARCHITECTURE.md)
- [Руководство по миграции](../docs/ARCHITECTURE_MIGRATION_GUIDE.md)
- [API микросервисов](../docs/MICROSERVICES_API.md)
- [Быстрый старт с микросервисами](../MICROSERVICES_QUICK_START.md)

---

## Вопросы?

Если у вас есть вопросы по миграции:
1. Прочитайте [ARCHITECTURE_MIGRATION_GUIDE.md](../docs/ARCHITECTURE_MIGRATION_GUIDE.md)
2. Посмотрите примеры в [examples/](../examples/)
3. Откройте issue на GitHub

---

**Последнее обновление**: 2024-01-10  
**Статус**: Legacy / Deprecated  
**Рекомендация**: Используйте микросервисную архитектуру
