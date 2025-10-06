# 🤝 Contributing to Dating Bot

Спасибо за интерес к проекту! Мы рады любому вкладу - от исправления опечаток до добавления новых функций.

## 📋 Содержание

- [Как внести вклад](#как-внести-вклад)
- [Процесс разработки](#процесс-разработки)
- [Стиль кода](#стиль-кода)
- [Тестирование](#тестирование)
- [Документация](#документация)
- [Коммиты и Pull Requests](#коммиты-и-pull-requests)

---

## Как внести вклад

### Типы вкладов

- 🐛 **Bug fixes** - исправление ошибок
- ✨ **Features** - новая функциональность
- 📝 **Documentation** - улучшение документации
- 🎨 **UI/UX** - улучшение интерфейса WebApp
- ⚡ **Performance** - оптимизация производительности
- 🔒 **Security** - улучшение безопасности
- 🧪 **Tests** - добавление тестов

### С чего начать

1. **Найдите подходящую задачу**
   - Посмотрите [Issues](https://github.com/erliona/dating/issues)
   - Ищите метки: `good first issue`, `help wanted`
   - Или предложите свою идею

2. **Обсудите перед началом**
   - Для больших изменений создайте issue для обсуждения
   - Убедитесь что никто не работает над этим

3. **Fork и clone**
   ```bash
   # Fork через GitHub UI, затем:
   git clone https://github.com/YOUR_USERNAME/dating.git
   cd dating
   ```

---

## Процесс разработки

### 1. Настройка окружения

```bash
# Создайте виртуальное окружение
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate  # Windows

# Установите зависимости
pip install -r requirements-dev.txt

# Настройте .env для тестов
cp .env.example .env
# Укажите BOT_TOKEN (можно использовать тестовый бот)
```

### 2. Создайте ветку

```bash
# Используйте описательное имя
git checkout -b feature/add-video-calls
git checkout -b fix/profile-update-bug
git checkout -b docs/improve-readme
```

### 3. Сделайте изменения

- Пишите чистый, читаемый код
- Следуйте существующему стилю
- Добавляйте комментарии для сложной логики
- Обновляйте документацию при необходимости

### 4. Добавьте тесты

```bash
# Создайте тесты для новой функциональности
# В tests/test_your_feature.py

# Запустите тесты
pytest -v

# Проверьте покрытие
pytest --cov=bot --cov-report=html
```

### 5. Локальная проверка

```bash
# Проверьте синтаксис
python -m py_compile bot/*.py

# Запустите линтер (если используете)
flake8 bot/ tests/

# Проверьте форматирование (если используете)
black --check bot/ tests/
```

### 6. Commit и push

```bash
git add .
git commit -m "feat: add video call feature"
git push origin feature/add-video-calls
```

### 7. Создайте Pull Request

- Откройте PR на GitHub
- Заполните шаблон PR (если есть)
- Свяжите с соответствующим issue (`Closes #123`)
- Дождитесь CI проверок
- Ответьте на комментарии ревьюеров

---

## Стиль кода

### Python Code Style

Следуем [PEP 8](https://pep8.org/) с небольшими отклонениями:

```python
# ✅ Хорошо
async def create_profile(
    user_id: int,
    name: str,
    age: int,
    interests: list[str]
) -> ProfileModel:
    """Create a new user profile.
    
    Args:
        user_id: Telegram user ID
        name: User's name
        age: User's age
        interests: List of interests
        
    Returns:
        Created profile model
        
    Raises:
        ValidationError: If data is invalid
    """
    if age < 18:
        raise ValidationError("User must be 18+")
    
    profile = ProfileModel(
        user_id=user_id,
        name=name,
        age=age,
        interests=interests
    )
    return profile


# ❌ Плохо
def createProfile(userId,n,a,i):
    if a<18: raise ValidationError("no")
    p=ProfileModel(user_id=userId,name=n,age=a,interests=i)
    return p
```

### Ключевые правила

1. **Naming Conventions**
   - `snake_case` для функций и переменных
   - `PascalCase` для классов
   - `UPPERCASE` для констант
   - Описательные имена (не `x`, `tmp`, `data`)

2. **Type Hints**
   ```python
   # Всегда используйте type hints
   def process_user(user_id: int) -> dict[str, Any]:
       ...
   
   async def get_profile(user_id: int) -> Optional[ProfileModel]:
       ...
   ```

3. **Docstrings**
   ```python
   def function(param: str) -> bool:
       """Short description.
       
       Longer description if needed.
       
       Args:
           param: Parameter description
           
       Returns:
           Return value description
       """
   ```

4. **Imports**
   ```python
   # Группировка и сортировка
   # 1. Standard library
   import logging
   from datetime import datetime
   
   # 2. Third party
   from aiogram import Bot, Dispatcher
   from sqlalchemy import select
   
   # 3. Local
   from .db import ProfileRepository
   from .config import settings
   ```

5. **Line Length**
   - Максимум 100 символов (но 88 предпочтительнее для black)
   - Разбивайте длинные строки логично

### JavaScript/HTML/CSS

- Используйте современный ES6+ синтаксис
- Индентация: 2 пробела
- Semicolons: используйте
- Quotes: одинарные `'string'`

---

## Тестирование

**Current Status**: 360+ comprehensive tests organized by type

### Структура тестов

Тесты организованы в три категории:

- **`tests/unit/`** - Unit tests для отдельных функций и модулей
  - `test_api_client.py` - тесты API Gateway клиента
  - `test_config.py` - тесты конфигурации
  - `test_validation.py` - тесты валидации данных
  - `test_core_services.py` - тесты сервисов (профиль, матчинг, пользователи)
  - `test_cache.py`, `test_geo.py`, `test_utils.py` - вспомогательные модули

- **`tests/integration/`** - Integration tests для взаимодействия компонентов
  - `test_api.py` - HTTP API endpoints
  - `test_security.py` - аутентификация и безопасность
  - `test_media.py` - обработка медиа файлов
  - `test_repository.py` - работа с базой данных
  - `test_monitoring_config.py` - конфигурация мониторинга

- **`tests/e2e/`** - End-to-end tests для полных пользовательских сценариев
  - `test_user_flows.py` - создание профиля, discovery, матчинг
  - `test_main.py` - бот handlers и команды
  - `test_discovery.py` - система поиска и рекомендаций
  - `test_gateway.py` - API Gateway маршрутизация
  - `test_admin.py` - админ панель

### Требования к тестам

1. **Каждая новая функция должна иметь тесты**
   ```python
   @pytest.mark.asyncio
   async def test_new_feature():
       """Test the new feature works correctly."""
       result = await new_feature()
       assert result.status == "success"
   ```

2. **Тесты должны быть изолированными**
   - Не зависеть от других тестов
   - Не зависеть от порядка выполнения
   - Очищать за собой данные
   - Использовать fixtures для общих данных

3. **Покрывайте edge cases**
   ```python
   @pytest.mark.parametrize("age,expected", [
       (17, False),  # Too young
       (18, True),   # Minimum age
       (100, True),  # Very old
       (0, False),   # Invalid
       (-1, False),  # Invalid
   ])
   async def test_age_validation(age, expected):
       assert validate_age(age) == expected
   ```

4. **Тестируйте ошибки**
   ```python
   async def test_handles_invalid_data():
       with pytest.raises(ValidationError):
           await create_profile(user_id=None)
   ```

### Запуск тестов

```bash
# Все тесты
pytest -v

# По категориям (используя markers)
pytest -m unit -v              # Только unit tests (быстрые ~2s)
pytest -m integration -v       # Только integration tests (~4s)
pytest -m e2e -v              # Только e2e tests (~3s)

# По директориям
pytest tests/unit/ -v          # Unit tests
pytest tests/integration/ -v   # Integration tests
pytest tests/e2e/ -v          # E2E tests

# Конкретный файл
pytest tests/unit/test_validation.py -v

# С покрытием
pytest --cov=bot --cov=core --cov=services --cov-report=term --cov-report=html

# С таймаутом (предотвращает зависания)
pytest -m e2e --timeout=900 -v           # E2E с таймаутом 15 мин
pytest -m integration --timeout=600 -v   # Integration с таймаутом 10 мин

# Быстрая проверка (только упавшие)
pytest --lf -v

# Пропустить xfail тесты
pytest --no-xfail -v

# Параллельный запуск (если установлен pytest-xdist)
pytest -n auto
```

---

## Документация

### Когда обновлять документацию

- ✅ Добавили новую команду бота → обновите README
- ✅ Изменили API → обновите docstrings
- ✅ Добавили новую переменную окружения → обновите .env.example
- ✅ Изменили деплой процесс → обновите docs/DEPLOYMENT.md
- ✅ Добавили новую зависимость → обновите requirements.txt

### Где писать документацию

| Что | Где |
|-----|-----|
| Общий обзор | README.md |
| Быстрый старт | docs/GETTING_STARTED.md |
| Архитектура | docs/ARCHITECTURE.md |
| Деплой | docs/DEPLOYMENT.md |
| Тестирование | docs/TESTING.md |
| API функций | Docstrings в коде |
| Roadmap | ROADMAP.md |

### Стиль документации

- Используйте markdown
- Добавляйте примеры кода
- Используйте emoji для структуры (умеренно)
- Пишите просто и понятно
- Добавляйте ссылки на связанные разделы

---

## Коммиты и Pull Requests

### Commit Messages

Следуем [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Формат
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat` - новая функция
- `fix` - исправление бага
- `docs` - изменения в документации
- `style` - форматирование, отсутствующие точки с запятой и т.д.
- `refactor` - рефакторинг кода
- `test` - добавление тестов
- `chore` - обновление зависимостей, конфигурации и т.д.

**Примеры**:
```bash
feat(bot): add video call functionality

Implemented WebRTC integration for peer-to-peer video calls.
Added STUN/TURN server configuration.

Closes #123

---

fix(db): resolve connection pool exhaustion

Fixed issue where database connections weren't being released
properly after failed transactions.

Fixes #456

---

docs(readme): update deployment instructions

Added section about monitoring stack configuration.
Clarified environment variable requirements.

---

test(matching): add tests for compatibility algorithm

Added parametrized tests covering all edge cases
of the matching score calculation.
```

### Pull Request Guidelines

1. **Название PR**
   - Используйте тот же формат что и commit messages
   - Пример: `feat: add user profile verification`

2. **Описание PR**
   ```markdown
   ## Changes
   - Added profile verification feature
   - Implemented photo validation using AI
   - Added verification badge to profiles
   
   ## Testing
   - Added unit tests for verification logic
   - Tested with 100+ sample photos
   - All existing tests pass
   
   ## Screenshots
   [Add screenshots if UI changed]
   
   ## Checklist
   - [x] Tests added/updated
   - [x] Documentation updated
   - [x] No breaking changes
   - [x] Follows code style guidelines
   
   Closes #123
   ```

3. **Размер PR**
   - Предпочтительно: <400 строк изменений
   - Для больших изменений: разбейте на несколько PR
   - Легче ревьюить = быстрее мерджить

4. **Ревью**
   - Будьте открыты к обратной связи
   - Отвечайте на комментарии
   - Вносите запрошенные изменения
   - Будьте терпеливы

---

## Code Review Process

### Для авторов PR

- ✅ Прогоните тесты локально перед PR
- ✅ Проверьте что CI проходит
- ✅ Ответьте на все комментарии
- ✅ Сделайте запрошенные изменения
- ✅ Пометьте комментарии как resolved после исправления

### Для ревьюеров

- ✅ Будьте конструктивны и вежливы
- ✅ Объясняйте почему нужно изменение
- ✅ Предлагайте альтернативы
- ✅ Хвалите хороший код
- ❌ Не требуйте перфекционизма

---

## Release Process

Для мейнтейнеров проекта:

1. **Update version**
   ```bash
   # В setup.py или pyproject.toml
   version = "1.2.0"
   ```

2. **Update CHANGELOG**
   ```markdown
   ## [1.2.0] - 2024-01-15
   
   ### Added
   - Video call feature
   - Profile verification
   
   ### Fixed
   - Database connection issues
   - UI bugs in WebApp
   ```

3. **Create tag**
   ```bash
   git tag -a v1.2.0 -m "Release v1.2.0"
   git push origin v1.2.0
   ```

4. **GitHub Release**
   - Создайте release на GitHub
   - Добавьте release notes из CHANGELOG
   - Приложите artifacts если нужно

---

## Вопросы?

- 💬 [GitHub Discussions](https://github.com/erliona/dating/discussions)
- 🐛 [GitHub Issues](https://github.com/erliona/dating/issues)
- 📖 [Documentation](docs/)

---

## Code of Conduct

- Будьте уважительны
- Приветствуется конструктивная критика
- Никакой дискриминации
- Помогайте новичкам
- Создавайте позитивное сообщество

---

**Спасибо за вклад в проект! 🎉**

Ваша помощь делает Dating Bot лучше для всех пользователей.
