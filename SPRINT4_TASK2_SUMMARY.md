# Sprint 4 Task 2: Развитие основного приложения

## Обзор

Расширение функциональности webapp и улучшение системы рекомендаций с добавлением пользовательских предпочтений поиска.

## Изменения

### 1. Миграция базы данных

**Файл**: `migrations/versions/20241215_0003_add_user_preferences.py`

Добавлены новые поля в таблицу `user_settings`:

#### Новые поля
- `age_min` (Integer, nullable) - Минимальный возраст для поиска
- `age_max` (Integer, nullable) - Максимальный возраст для поиска  
- `max_distance` (Integer, nullable) - Максимальное расстояние в км (null = без ограничений)

**Применение миграции**:
```bash
docker compose exec bot alembic upgrade head
```

### 2. Backend изменения

#### Файл: `bot/db.py`

**UserSettingsModel** - добавлены новые поля:
```python
age_min: Mapped[Optional[int]] = mapped_column(default=None)
age_max: Mapped[Optional[int]] = mapped_column(default=None)
max_distance: Mapped[Optional[int]] = mapped_column(default=None)
```

**UserSettingsRepository** - автоматически поддерживает новые поля через метод `upsert()`.

#### Файл: `bot/main.py`

**Обновлён handler `update_settings`**:
- Теперь обрабатывает поля `age_min`, `age_max`, `max_distance`
- Сохраняет их в базу данных

**Добавлен новый handler `get_recommendations`**:
- Получает профиль пользователя
- Загружает предпочтения из `user_settings`
- Исключает уже просмотренные профили (liked/disliked)
- Применяет алгоритм `find_best_matches()` для подбора
- Фильтрует результаты по возрасту:
  - Если установлен `age_min` - фильтрует младше
  - Если установлен `age_max` - фильтрует старше
- Возвращает до 10 рекомендаций

**Формат запроса**:
```json
{
  "action": "get_recommendations"
}
```

**Формат ответа**:
```json
{
  "action": "recommendations",
  "profiles": [
    {
      "id": 12345,
      "name": "Иван",
      "age": 28,
      "gender": "male",
      "bio": "...",
      "location": "Москва",
      "interests": ["спорт", "музыка"],
      "goal": "friendship",
      "photo_url": "https://..."
    }
  ],
  "count": 10
}
```

### 3. Frontend изменения

#### Файл: `webapp/index.html`

Добавлена новая секция настроек **"Предпочтения поиска"**:

```html
<div class="settings-section">
  <h3>Предпочтения поиска</h3>
  <div class="settings-item">
    <label for="age-min">
      <span>Минимальный возраст</span>
      <input type="number" id="age-min" min="18" max="120" placeholder="18" />
    </label>
  </div>
  <div class="settings-item">
    <label for="age-max">
      <span>Максимальный возраст</span>
      <input type="number" id="age-max" min="18" max="120" placeholder="120" />
    </label>
  </div>
  <div class="settings-item">
    <label for="max-distance">
      <span>Макс. расстояние (км)</span>
      <input type="number" id="max-distance" min="1" max="10000" placeholder="Не ограничено" />
    </label>
    <span class="field-hint">Оставьте пустым для поиска по всей стране</span>
  </div>
</div>
```

#### Файл: `webapp/js/app.js`

**Обновлён объект настроек**:
```javascript
let settings = {
  lang: "ru",
  showLocation: true,
  showAge: true,
  notifyMatches: true,
  notifyMessages: true,
  ageMin: null,      // новое
  ageMax: null,      // новое
  maxDistance: null, // новое
  debugMode: false
};
```

**Обновлена функция `loadSettings()`**:
- Загружает новые поля из localStorage
- Заполняет input элементы значениями

**Обновлена функция `saveSettings()`**:
- Читает значения из новых input полей
- Преобразует в числа (null если пусто)
- Отправляет в бот через `sendData()`

**Обновлена функция `loadMatches()`**:
- Фильтрует тестовые профили по `ageMin` и `ageMax`
- Показывает только подходящие профили
- Демонстрирует работу фильтрации

**Пример фильтрации**:
```javascript
let filteredProfiles = [...testProfiles];

// Применить фильтр по возрасту
if (settings.ageMin) {
  filteredProfiles = filteredProfiles.filter(p => p.age >= settings.ageMin);
}
if (settings.ageMax) {
  filteredProfiles = filteredProfiles.filter(p => p.age <= settings.ageMax);
}
```

### 4. Тестирование

**Файл**: `tests/test_sprint4_task2.py`

Созданы 6 новых тестов:

#### TestUserPreferences
- `test_settings_model_with_preferences` - Проверка модели с новыми полями
- `test_settings_upsert_with_new_fields` - Проверка сохранения и обновления

#### TestRecommendationsHandler  
- `test_get_recommendations_action` - Проверка фильтрации с настройками
- `test_get_recommendations_no_filters` - Проверка без фильтров
- `test_get_recommendations_excludes_interacted` - Исключение просмотренных

#### TestSettingsUpdate
- `test_settings_update_payload` - Проверка формата данных

**Результаты тестирования**:
```
230 passed in 1.25s
```

Все существующие тесты продолжают работать, новые тесты добавлены и проходят успешно.

## Бизнес-логика

### Сценарий использования

1. **Пользователь открывает настройки**
   - Переходит на вкладку "Настройки"
   - Видит новую секцию "Предпочтения поиска"

2. **Устанавливает предпочтения**
   - Минимальный возраст: 25
   - Максимальный возраст: 35
   - Макс. расстояние: 50 км (опционально)

3. **Сохраняет настройки**
   - Нажимает кнопку сохранения (автоматически при изменении)
   - Данные отправляются в бот
   - Бот сохраняет в базу данных

4. **Просматривает рекомендации**
   - Переходит на вкладку "Метчи"
   - Видит только профили в диапазоне 25-35 лет
   - Уже просмотренные профили не показываются

5. **Backend обработка** (будущее)
   - При запросе `get_recommendations`
   - Бот загружает профиль и настройки
   - Применяет фильтры по возрасту
   - Использует алгоритм `find_best_matches()`
   - Возвращает персонализированные рекомендации

## Улучшения системы рекомендаций

### Текущая реализация

1. **Smart matching алгоритм** (существующий)
   - Оценка совместимости по интересам (40%)
   - Оценка по локации (30%)
   - Оценка по целям знакомства (20%)
   - Оценка по возрасту (10%)

2. **Новые фильтры** (добавлено)
   - Фильтрация по возрастному диапазону
   - Исключение уже взаимодействовавших пользователей
   - Подготовка к фильтрации по расстоянию

### Будущие улучшения

1. **Geo-фильтрация**
   - Вычисление расстояния между городами
   - Применение фильтра `max_distance`
   - Приоритизация близких пользователей

2. **Персонализация**
   - Учёт истории взаимодействий
   - Обучение на основе лайков/дизлайков
   - A/B тестирование алгоритмов

3. **Оптимизация**
   - Кэширование рекомендаций
   - Предзагрузка профилей
   - Batch обработка запросов

## Технические детали

### Обратная совместимость

- Все новые поля nullable (не требуют миграции данных)
- Существующие пользователи увидят пустые значения
- При пустых значениях фильтры не применяются
- Старые клиенты продолжают работать

### Валидация данных

**Backend** (bot/main.py):
- Возраст: проверяется при сохранении профиля (18-120)
- Предпочтения: nullable, любые числа принимаются
- Расстояние: nullable, положительные числа

**Frontend** (webapp/js/app.js):
- HTML5 валидация: `min="18" max="120"`
- JavaScript конвертация: `parseInt()` с fallback на `null`
- Локальное хранение для офлайн работы

### Производительность

**Database**:
- Новые поля добавлены в существующую таблицу
- Без индексов (не критично для поиска)
- Простые скалярные типы (Integer)

**Queries**:
- Фильтрация на уровне приложения (Python)
- Можно оптимизировать через SQL WHERE
- Текущая реализация достаточна для MVP

## API изменения

### Новый action: `get_recommendations`

**Request**:
```json
{
  "action": "get_recommendations"
}
```

**Response** (через bot message):
```json
{
  "action": "recommendations",
  "profiles": [...],
  "count": 10
}
```

### Обновлённый action: `update_settings`

**Request** (расширенный):
```json
{
  "action": "update_settings",
  "lang": "ru",
  "show_location": true,
  "show_age": true,
  "notify_matches": true,
  "notify_messages": true,
  "age_min": 25,        // новое
  "age_max": 35,        // новое
  "max_distance": 50    // новое
}
```

## Ограничения текущей реализации

### WebApp API

Telegram WebApp API не поддерживает двустороннюю коммуникацию напрямую:
- `sendData()` закрывает webapp после отправки
- Нет механизма получения ответа в реальном времени
- Нужен workaround через внешний API или polling

### Решение для будущего

1. **Backend API endpoint**
   - Создать REST API на bot сервере
   - WebApp делает HTTP запросы
   - Получает JSON ответы

2. **WebSocket**
   - Долгоживущее соединение
   - Real-time обновления
   - Push уведомления

3. **Telegram Bot API**
   - Inline queries
   - Callback queries
   - Bot messages с inline кнопками

## Статистика изменений

- **Файлов изменено**: 6
- **Добавлено строк**: 367
- **Удалено строк**: 4
- **Новых тестов**: 6
- **Всего тестов**: 230 (все проходят)

## Чеклист

- [x] Миграция базы данных создана
- [x] Модель данных обновлена
- [x] Backend handler реализован
- [x] Frontend UI добавлен
- [x] JavaScript логика обновлена
- [x] Тесты написаны и проходят
- [x] Обратная совместимость сохранена
- [x] Документация обновлена

## Примеры использования

### Установка предпочтений

```javascript
// В webapp/js/app.js
settings = {
  ageMin: 25,
  ageMax: 35,
  maxDistance: 50
};
saveSettings();
```

### Запрос рекомендаций (будущее)

```javascript
// Отправить запрос
tg.sendData(JSON.stringify({
  action: "get_recommendations"
}));

// Получить ответ (требует доработки)
// Пока используются тестовые профили с фильтрацией
```

### Фильтрация на клиенте

```javascript
// Текущая реализация
let profiles = testProfiles.filter(p => {
  if (settings.ageMin && p.age < settings.ageMin) return false;
  if (settings.ageMax && p.age > settings.ageMax) return false;
  return true;
});
```

## Заключение

Sprint 4 Task 2 успешно реализован с минимальными изменениями:

1. ✅ Добавлены новые фичи в webapp (настройки предпочтений)
2. ✅ Улучшена система рекомендаций (фильтрация, API handler)
3. ✅ Расширены пользовательские настройки (БД, UI, логика)
4. ✅ Все тесты проходят (230/230)
5. ✅ Обратная совместимость сохранена

Следующие шаги:
- Реализация реального API endpoint для рекомендаций
- Добавление geo-фильтрации по расстоянию
- Оптимизация алгоритма подбора
- A/B тестирование различных стратегий
