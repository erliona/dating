# 🧪 Testing Guide

Руководство по тестированию Dating Bot приложения.

**Current Status**: 162 tests, 76% code coverage

## Test Coverage Summary

| Module | Coverage | Description |
|--------|----------|-------------|
| bot/db.py | 100% | Database models |
| bot/repository.py | 100% | Database repository operations |
| bot/geo.py | 97% | Geolocation utilities |
| bot/media.py | 93% | Photo validation and storage |
| bot/security.py | 88% | Security and encryption |
| bot/validation.py | 86% | Data validation |
| bot/config.py | 72% | Configuration management |
| bot/main.py | 70% | Bot handlers and main entry point |
| bot/api.py | 36% | HTTP API endpoints |
| **TOTAL** | **76%** | Overall test coverage |

---

## Содержание

- [Запуск тестов](#запуск-тестов)
- [Тестовая инфраструктура](#тестовая-инфраструктура)
- [Написание тестов](#написание-тестов)
- [CI/CD тестирование](#cicd-тестирование)
- [Покрытие кода](#покрытие-кода)

---

## Запуск тестов

### Предварительные требования

```bash
# Установите зависимости для разработки
pip install -r requirements-dev.txt
```

### Все тесты

```bash
# Запустить все тесты
pytest -v

# С подробным выводом
pytest -vv

# С выводом print() statements
pytest -v -s
```

### Запуск конкретных тестов

```bash
# Один файл
pytest tests/test_database.py -v

# Один тест
pytest tests/test_database.py::test_create_profile -v

# По pattern (все тесты с "match" в имени)
pytest -k "match" -v

# По маркеру (если есть @pytest.mark.slow)
pytest -m slow -v
```

### Параллельное выполнение

```bash
# Установить pytest-xdist
pip install pytest-xdist

# Запустить на 4 воркерах
pytest -n 4 -v
```

---

## Тестовая инфраструктура

### Структура тестов

```
tests/
├── __init__.py                  # Test suite marker
├── test_api.py                  # API endpoints, JWT, image optimization (14 tests)
├── test_config.py               # Configuration validation (3 tests)
├── test_geo.py                  # Geolocation utilities (20 tests)
├── test_main.py                 # Bot handlers, logging, WebApp data (14 tests)
├── test_media.py                # Photo validation and storage (27 tests)
├── test_repository.py           # Database CRUD operations (14 tests)
├── test_security.py             # Security and encryption (59 tests)
└── test_validation.py           # Data validation functions (47 tests)
```

**Total**: 162 tests covering all core functionality

### Test Categories

#### Unit Tests (148 tests)
- **Configuration**: Bot config loading, JWT secret generation
- **Validation**: Profile data validation, age checks, field validation
- **Geolocation**: Geohash encoding, coordinate validation, location processing
- **Media**: Photo validation, MIME type detection, EXIF removal, storage
- **Security**: Encryption, key derivation, password hashing, token generation
- **Repository**: User/profile CRUD, photo management
- **Bot Handlers**: Command handlers, WebApp data processing, logging
- **API**: JWT authentication, image optimization, NSFW detection

#### Integration Tests (14 tests)
- WebApp data flow (bot → database)
- Profile creation and updates
- Photo upload pipeline
- Authentication flow

### Fixtures (conftest.py)

Основные fixtures доступные во всех тестах:

#### `db_session`
Асинхронная сессия БД для тестов.

```python
async def test_something(db_session):
    # db_session автоматически создается и очищается
    profile = await db_session.execute(...)
```

#### `sample_profile`
Тестовый профиль пользователя.

```python
async def test_with_profile(db_session, sample_profile):
    # sample_profile уже создан в БД
    assert sample_profile.name == "Test User"
```

#### `bot`
Mock объект Telegram бота.

```python
async def test_handler(bot):
    # bot это AsyncMock с настроенными методами
    await bot.send_message(chat_id=123, text="Test")
    bot.send_message.assert_called_once()
```

#### `message`
Mock объект Telegram сообщения.

```python
async def test_command(message):
    # message.from_user.id, message.text и т.д.
    assert message.from_user.id == 12345
```

---

## Написание тестов

### Unit Test Example

```python
import pytest
from bot.db import ProfileRepository

@pytest.mark.asyncio
async def test_create_profile(db_session):
    """Test creating a new user profile."""
    repo = ProfileRepository(db_session)
    
    # Arrange
    user_id = 12345
    profile_data = {
        "name": "Alice",
        "age": 25,
        "gender": "female",
        "preference": "male",
        "bio": "Test bio",
        "interests": ["music", "travel"]
    }
    
    # Act
    profile = await repo.create_or_update_profile(user_id, profile_data)
    
    # Assert
    assert profile.user_id == user_id
    assert profile.name == "Alice"
    assert profile.age == 25
    assert "music" in profile.interests
```

### Integration Test Example

```python
import pytest
from bot.main import handle_start_command

@pytest.mark.asyncio
async def test_start_command_flow(bot, message, db_session):
    """Test complete /start command flow."""
    # Arrange
    message.text = "/start"
    message.from_user.id = 12345
    
    # Act
    await handle_start_command(message)
    
    # Assert
    bot.send_message.assert_called()
    call_args = bot.send_message.call_args
    assert "Добро пожаловать" in call_args.kwargs["text"]
```

### Testing Async Code

```python
@pytest.mark.asyncio
async def test_async_function():
    """Test asynchronous function."""
    result = await some_async_function()
    assert result == expected_value
```

### Mocking External APIs

```python
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_telegram_api_call():
    """Test function that calls Telegram API."""
    with patch('bot.main.bot.send_message', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True
        
        result = await send_notification(user_id=123, text="Test")
        
        assert result is True
        mock_send.assert_called_once_with(chat_id=123, text="Test")
```

### Testing Error Handling

```python
@pytest.mark.asyncio
async def test_handles_database_error(db_session):
    """Test graceful handling of database errors."""
    repo = ProfileRepository(db_session)
    
    # Force an error
    with pytest.raises(DatabaseError):
        await repo.create_or_update_profile(None, {})
```

### Parametrized Tests

```python
@pytest.mark.asyncio
@pytest.mark.parametrize("age,expected", [
    (18, True),
    (17, False),
    (100, True),
    (16, False),
])
async def test_age_validation(age, expected):
    """Test age validation with multiple values."""
    result = validate_age(age)
    assert result == expected
```

---

## Покрытие кода

### Генерация отчета о покрытии

```bash
# Запустить тесты с покрытием
pytest --cov=bot --cov-report=html --cov-report=term

# Открыть HTML отчет
open htmlcov/index.html  # Mac
xdg-open htmlcov/index.html  # Linux
```

### Настройка минимального покрытия

В `pytest.ini` или `pyproject.toml`:

```ini
[tool:pytest]
addopts = --cov=bot --cov-fail-under=80
```

### Покрытие по модулям

```bash
# Покрытие только для конкретного модуля
pytest --cov=bot.db --cov-report=term tests/test_database.py
```

### Исключение файлов из покрытия

В `.coveragerc`:

```ini
[run]
omit = 
    */tests/*
    */migrations/*
    */__pycache__/*
```

---

## CI/CD тестирование

### GitHub Actions

Тесты автоматически запускаются при:
- Push в main/master ветки
- Создании Pull Request
- Ручном запуске workflow

См. `.github/workflows/ci.yml`

### Что тестируется в CI

1. **Python Syntax** - `python -m py_compile`
2. **Unit Tests** - `pytest -v`
3. **Coverage** - генерация отчета и артефакта
4. **Database Migrations** - `alembic upgrade head`
5. **Docker Build** - сборка образа
6. **Security Scan** - `pip-audit`

### Просмотр результатов

1. Откройте GitHub Actions в репозитории
2. Выберите workflow run
3. Посмотрите детали каждого шага
4. Скачайте artifacts (coverage report)

---

## Best Practices

### 1. Изоляция тестов

✅ **Хорошо**:
```python
async def test_create_profile(db_session):
    # Создаем данные внутри теста
    profile = await create_test_profile(db_session)
    assert profile is not None
```

❌ **Плохо**:
```python
# Зависимость от других тестов или глобального состояния
async def test_update_profile():
    # Предполагает что профиль уже существует
    profile = await get_profile(12345)
    ...
```

### 2. Понятные имена

✅ **Хорошо**:
```python
def test_user_can_like_another_user_only_once()
def test_match_created_when_both_users_like_each_other()
```

❌ **Плохо**:
```python
def test_1()
def test_feature()
```

### 3. AAA Pattern

```python
async def test_something():
    # Arrange - подготовка данных
    user = create_user(id=1)
    
    # Act - выполнение действия
    result = await process_user(user)
    
    # Assert - проверка результата
    assert result.status == "success"
```

### 4. Один assert на концепцию

✅ **Хорошо**:
```python
def test_profile_created():
    assert profile.name == "Alice"
    assert profile.age == 25
    # Все проверки связаны с созданием профиля
```

❌ **Плохо**:
```python
def test_everything():
    assert profile.name == "Alice"
    assert match.status == "active"  # Другая концепция
    assert settings.notifications == True  # И еще одна
```

### 5. Мокировать внешние зависимости

```python
# Мокируем Telegram API, внешние сервисы, файловую систему
with patch('bot.main.bot.send_message'):
    # Тест не делает реальный API call
    await notify_user(user_id)
```

---

## Отладка тестов

### Использование pdb

```python
def test_something():
    import pdb; pdb.set_trace()  # Точка останова
    result = compute()
    assert result == expected
```

### Pytest с отладкой

```bash
# Остановиться на первой ошибке
pytest -x

# Открыть pdb при ошибке
pytest --pdb

# Показать локальные переменные при ошибке
pytest -l
```

### Verbose вывод

```bash
# Максимально подробный вывод
pytest -vv -s --tb=long
```

---

## Производительность тестов

### Профилирование

```bash
# Показать самые медленные тесты
pytest --durations=10
```

### Оптимизация

1. **Используйте fixtures правильно**
   - `scope='session'` для дорогих ресурсов
   - `scope='function'` для изолированных данных

2. **Параллельное выполнение**
   ```bash
   pytest -n auto  # Автоматически определить кол-во воркеров
   ```

3. **Кэширование pytest**
   ```bash
   pytest --lf  # Запустить только упавшие тесты
   pytest --ff  # Сначала упавшие, потом остальные
   ```

---

## Интеграционное тестирование

### Тестирование с реальной БД

```python
# В conftest.py
@pytest.fixture(scope="session")
async def test_database():
    # Создать тестовую БД
    engine = create_async_engine("postgresql+asyncpg://...")
    await create_tables(engine)
    yield engine
    await drop_tables(engine)
```

### Docker для интеграционных тестов

```bash
# Запустить PostgreSQL в Docker для тестов
docker run -d --name test-db \
  -e POSTGRES_PASSWORD=test \
  -p 5433:5432 \
  postgres:15-alpine

# Запустить тесты
DATABASE_URL=postgresql+asyncpg://postgres:test@localhost:5433/postgres pytest

# Очистить
docker rm -f test-db
```

---

## Примеры команд

```bash
# Быстрый запуск (только упавшие)
pytest --lf -v

# Полный запуск с покрытием
pytest --cov=bot --cov-report=html -v

# Только быстрые тесты (исключить медленные)
pytest -m "not slow" -v

# Отладка конкретного теста
pytest tests/test_database.py::test_create_profile --pdb -v

# Запуск с разными уровнями детализации
pytest -v    # Verbose
pytest -vv   # Very verbose
pytest -q    # Quiet

# Показать stdout/stderr
pytest -s

# Остановиться на первой ошибке
pytest -x

# Показать топ-10 медленных тестов
pytest --durations=10
```

---

## Ресурсы

- [pytest документация](https://docs.pytest.org/)
- [pytest-asyncio](https://github.com/pytest-dev/pytest-asyncio)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)
- [Coverage.py](https://coverage.readthedocs.io/)

---

## Получение помощи

- 📖 [Основная документация](../README.md)
- 🏗️ [Архитектура](ARCHITECTURE.md)
- 🐛 [Создать issue](https://github.com/erliona/dating/issues)

---

**Хороших тестов! 🧪**
