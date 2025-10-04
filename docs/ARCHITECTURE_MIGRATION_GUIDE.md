# Architecture Migration Guide

Руководство по переходу от монолитной архитектуры к платформонезависимому ядру с микросервисами.

## Обзор изменений

### До
```
bot/
  ├── main.py        # Telegram-специфичный код + бизнес-логика
  ├── api.py         # API endpoints
  ├── repository.py  # Data access
  └── ...
```

### После
```
core/                      # Платформонезависимое ядро
  ├── models/             # Доменные модели
  ├── services/           # Бизнес-логика
  └── interfaces/         # Контракты для адаптеров

adapters/                 # Платформенная интеграция
  └── telegram/          # Telegram adapter
      ├── repository.py  # Реализация интерфейсов для Telegram
      ├── notification.py
      └── storage.py

services/                 # Микросервисы
  ├── auth/
  ├── profile/
  ├── discovery/
  ├── chat/
  └── media/

bot/                      # Legacy Telegram код (постепенная миграция)
```

## Платформонезависимое ядро

### Core Models (`core/models/`)

Доменные модели, не зависящие от платформы:

```python
from core.models import User, UserProfile, UserSettings
from core.models.enums import Gender, Orientation

# Создание пользователя (не зависит от Telegram)
profile = UserProfile(
    user_id=123,
    name="John",
    birth_date=date(1990, 1, 1),
    gender=Gender.MALE,
    orientation=Orientation.FEMALE,
    city="Moscow"
)
```

### Core Services (`core/services/`)

Вся бизнес-логика в сервисах:

```python
from core.services import UserService, ProfileService, MatchingService

# Использование через интерфейсы (dependency injection)
user_service = UserService(user_repository)
profile_service = ProfileService(profile_repository)
matching_service = MatchingService(profile_repository)

# Бизнес-логика работает одинаково для всех платформ
profile = await profile_service.create_profile(...)
recommendations = await matching_service.get_recommendations(...)
```

### Core Interfaces (`core/interfaces/`)

Контракты для реализации в адаптерах:

```python
from core.interfaces import IUserRepository, INotificationService

class IUserRepository(ABC):
    @abstractmethod
    async def get_user(self, user_id: int) -> Optional[User]:
        pass
```

## Адаптеры

### Telegram Adapter (`adapters/telegram/`)

Реализация интерфейсов для Telegram:

```python
from adapters.telegram import TelegramUserRepository, TelegramNotificationService

# Telegram-специфичная реализация
telegram_repo = TelegramUserRepository(session)
telegram_notifier = TelegramNotificationService(bot, tg_id_mapping)

# Использование с core services
user_service = UserService(telegram_repo)
```

### Будущие адаптеры

- **Mobile Adapter** - для iOS/Android приложений
- **Web Adapter** - для web-версии
- **Desktop Adapter** - для desktop приложений

Все адаптеры реализуют одни и те же интерфейсы из `core.interfaces`.

## Микросервисы

### Архитектура микросервисов

```
┌─────────────┐
│  API Gateway│
│  (Port 8080)│
└──────┬──────┘
       │
   ┌───┴────┬──────────┬──────────┬──────────┐
   │        │          │          │          │
┌──▼──┐  ┌──▼──┐  ┌───▼───┐  ┌───▼───┐  ┌───▼───┐
│Auth │  │Prof.│  │Discov.│  │ Chat  │  │ Media │
│8081 │  │8082 │  │ 8083  │  │ 8085  │  │ 8084  │
└──┬──┘  └──┬──┘  └───┬───┘  └───┬───┘  └───┬───┘
   │        │          │          │          │
   └────────┴──────────┴──────────┴──────────┘
                       │
                  ┌────▼────┐
                  │PostgreSQL│
                  └─────────┘
```

### Запуск микросервисов

```bash
# Запуск всех микросервисов
docker-compose -f docker-compose.microservices.yml up

# Запуск отдельного сервиса
docker-compose -f docker-compose.microservices.yml up auth-service

# Масштабирование сервиса
docker-compose -f docker-compose.microservices.yml up --scale profile-service=3
```

### Endpoints

#### Auth Service (Port 8081)
- `POST /auth/validate` - Validate Telegram initData
- `GET /auth/verify` - Verify JWT token
- `POST /auth/refresh` - Refresh token

#### Profile Service (Port 8082)
- `GET /profiles/{user_id}` - Get profile
- `POST /profiles` - Create profile
- `PUT /profiles/{user_id}` - Update profile

#### Discovery Service (Port 8083)
- `GET /discovery/candidates` - Get recommendations
- `POST /discovery/like` - Like profile
- `GET /discovery/matches` - Get matches

#### Chat Service (Port 8085)
- `WS /chat/connect` - WebSocket connection
- `GET /chat/conversations` - Get conversations

#### Media Service (Port 8084)
- `POST /media/upload` - Upload file
- `GET /media/{file_id}` - Get file

## Этапы миграции

### Phase 1: Core extraction ✅ DONE
1. ✅ Создан модуль `core/` с бизнес-логикой
2. ✅ Определены интерфейсы в `core/interfaces/`
3. ✅ Реализованы core services

### Phase 2: Adapter implementation ✅ DONE
1. ✅ Создан `adapters/telegram/`
2. ✅ Реализованы Telegram adapters
3. ✅ Telegram код использует core через адаптеры

### Phase 3: Microservices structure ✅ DONE
1. ✅ Создана структура `services/`
2. ✅ Реализованы базовые микросервисы
3. ✅ Создан docker-compose.microservices.yml

### Phase 4: Deployment 🔄 IN PROGRESS
1. 📋 Разработка API Gateway
2. 📋 Настройка service discovery
3. 📋 Deployment каждого сервиса
4. 📋 Миграция трафика

### Phase 5: Database per service 📋 PLANNED
1. 📋 Разделение БД для каждого сервиса
2. 📋 Event-driven синхронизация
3. 📋 Saga pattern для транзакций

## Преимущества новой архитектуры

### 1. Платформонезависимость
- ✅ Бизнес-логика не зависит от Telegram
- ✅ Можно создать mobile/desktop версии
- ✅ Легко добавить новые платформы

### 2. Масштабируемость
- ✅ Каждый микросервис масштабируется независимо
- ✅ Горизонтальное масштабирование
- ✅ Оптимизация ресурсов

### 3. Гибкость разработки
- ✅ Независимое развертывание сервисов
- ✅ Разные команды работают над разными сервисами
- ✅ Технологическая гибкость (разные языки/технологии)

### 4. Надежность
- ✅ Изоляция сбоев
- ✅ Circuit breakers
- ✅ Graceful degradation

### 5. Тестируемость
- ✅ Unit-тесты для core logic
- ✅ Integration тесты для адаптеров
- ✅ E2E тесты для микросервисов

## Backward Compatibility

Telegram Mini App продолжает работать без изменений:
- ✅ Все существующие endpoints сохранены
- ✅ API Gateway проксирует запросы к микросервисам
- ✅ Telegram bot использует core через адаптер
- ✅ WebApp не требует изменений

## Следующие шаги

1. **Для разработчиков**:
   - Изучите структуру `core/` и `adapters/`
   - При добавлении новой функциональности используйте core services
   - Telegram-специфичный код только в `adapters/telegram/`

2. **Для DevOps**:
   - Настройка CI/CD для микросервисов
   - Deployment каждого сервиса
   - Мониторинг и логирование

3. **Для будущего**:
   - Разработка mobile/desktop адаптеров
   - Миграция оставшегося legacy кода
   - Разделение баз данных для сервисов

## Документация

- [ARCHITECTURE.md](ARCHITECTURE.md) - Обновленная архитектура
- [Core Services](../core/services/) - Бизнес-логика
- [Adapters](../adapters/) - Платформенная интеграция
- [Microservices](../services/) - Микросервисы

## Помощь

Если у вас возникли вопросы по новой архитектуре:
1. Прочитайте эту документацию
2. Изучите примеры в `core/` и `adapters/`
3. Создайте issue в GitHub

---

**Дата обновления**: 2024-01-10  
**Версия**: 1.0.0  
**Статус**: Phase 3 Complete
