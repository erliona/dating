# Test Suite Documentation

This directory contains the comprehensive test suite for the Dating Bot application.

## 📊 Overview

**Total Tests**: 360+  
**Pass Rate**: 338 passed, 27 xfailed (API mismatches documented), 1 xpassed  
**Organization**: Unit, Integration, and End-to-End tests  
**Test Markers**: `unit`, `integration`, `e2e`  
**Coverage Goal**: >75% code coverage

## 📁 Test Structure

### Unit Tests (`unit/`)

Unit tests focus on testing individual functions, classes, and modules in isolation.

- **`test_api_client.py`** - API Gateway client functionality
  - Request/response handling
  - Error handling and retries
  - Idempotency support
  - Profile and discovery operations

- **`test_config.py`** - Configuration loading and validation
  - Environment variable handling
  - Database URL construction
  - JWT secret management

- **`test_validation.py`** - Data validation functions
  - Profile data validation
  - Name, bio, interests validation
  - Birth date and age validation
  - Location validation

- **`test_core_services.py`** - Core business logic
  - Profile service operations
  - Matching algorithm logic
  - Orientation compatibility
  - User service functions
  - Rate limiting
  - Caching

- **`test_cache.py`** - Cache system
  - Set/get operations
  - TTL expiration
  - Auto cleanup

- **`test_geo.py`** - Geolocation utilities
  - Coordinate validation
  - Distance calculations
  - City name handling

- **`test_utils.py`** - Utility functions
  - Helper functions
  - Shared test utilities

### Integration Tests (`integration/`)

Integration tests verify that different components work together correctly.

- **`test_api.py`** - HTTP API endpoints
  - Photo upload/download
  - Profile management
  - Authentication flows
  - Error responses
  - CDN integration

- **`test_security.py`** - Authentication and authorization
  - Telegram initData validation
  - JWT token generation/validation
  - HMAC signature verification
  - Token expiration handling

- **`test_media.py`** - Media file handling
  - Image optimization
  - NSFW detection
  - Format validation
  - Resource cleanup

- **`test_repository.py`** - Database operations
  - CRUD operations
  - Query optimization
  - Transaction handling
  - Data consistency

- **`test_monitoring_config.py`** - Monitoring configuration
  - Loki configuration validation
  - Prometheus setup
  - Health checks
  - Version compatibility

### End-to-End Tests (`e2e/`)

End-to-end tests simulate complete user workflows and scenarios.

- **`test_user_flows.py`** - Complete user journeys
  - New user onboarding
  - Profile creation/editing
  - Photo upload with NSFW check
  - Discovery and matching
  - Chat initialization
  - Location updates
  - Error handling flows

- **`test_main.py`** - Bot handlers and commands
  - /start command
  - WebApp data handling
  - Location processing
  - Message handling
  - Logging configuration

- **`test_discovery.py`** - Discovery system
  - Candidate fetching
  - Filtering logic
  - Interaction recording
  - Match creation

- **`test_discovery_api.py`** - Discovery API endpoints
  - Candidate API
  - Interaction API
  - Match API

- **`test_gateway.py`** - API Gateway routing
  - Request forwarding
  - Service routing
  - Error handling

- **`test_admin.py`** - Admin panel functionality
  - User management
  - Content moderation
  - Statistics

- **`test_orientation_filtering.py`** - Orientation-based matching
  - Mutual compatibility checks
  - Gender and orientation filtering

## 🚀 Running Tests

### Test Markers

Tests are organized using pytest markers for easy filtering:
- `@pytest.mark.unit` - Fast, isolated component tests
- `@pytest.mark.integration` - Component interaction tests
- `@pytest.mark.e2e` - Complete user flow tests
- `@pytest.mark.xfail` - Known issues/API mismatches (documented)

### All Tests
```bash
pytest -v
```

### By Marker (Recommended)
```bash
# Unit tests only (fast ~2s)
pytest -m unit -v

# Integration tests (~4s)
pytest -m integration -v

# End-to-end tests (~3s)
pytest -m e2e -v

# Run unit and integration (skip e2e)
pytest -m "unit or integration" -v
```

### By Directory
```bash
# Unit tests
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# End-to-end tests
pytest tests/e2e/ -v
```

### Specific Test File
```bash
pytest tests/unit/test_validation.py -v
```

### With Coverage
```bash
pytest --cov=bot --cov=core --cov=services --cov-report=html --cov-report=term
```

### Failed Tests Only
```bash
pytest --lf -v
```

### Skip Xfail Tests
```bash
# Show only real pass/fail (skip known issues)
pytest --no-xfail -v
```

### Parallel Execution
```bash
# Requires pytest-xdist
pytest -n auto
```

### Stop on First Failure
```bash
pytest -x
```

## 📝 Writing Tests

### Test Naming Convention

- Test files: `test_*.py`
- Test functions: `test_*`
- Test classes: `Test*`

### Example Unit Test

```python
"""Tests for profile validation."""

import pytest
from bot.validation import validate_profile_data


class TestProfileValidation:
    """Test profile validation functions."""

    def test_valid_profile(self):
        """Test that valid profile passes validation."""
        profile = {
            "name": "John Doe",
            "birth_date": "1995-01-15",
            "gender": "male",
            "orientation": "heterosexual"
        }
        
        is_valid, errors = validate_profile_data(profile)
        
        assert is_valid
        assert not errors

    def test_invalid_age(self):
        """Test that underage users are rejected."""
        profile = {
            "name": "Too Young",
            "birth_date": "2010-01-01",
            "gender": "male",
            "orientation": "heterosexual"
        }
        
        is_valid, errors = validate_profile_data(profile)
        
        assert not is_valid
        assert "age" in str(errors).lower()
```

### Example Integration Test

```python
"""Tests for API authentication."""

import pytest
from aiohttp import web
from bot.security import generate_jwt_token


@pytest.mark.asyncio
class TestAuthentication:
    """Test authentication endpoints."""

    async def test_token_generation(self):
        """Test JWT token generation."""
        secret = "test-secret"
        user_id = 12345
        
        token = generate_jwt_token(user_id, secret)
        
        assert token is not None
        assert len(token) > 0
```

### Example E2E Test

```python
"""Tests for complete user flows."""

import pytest
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
class TestUserOnboarding:
    """Test complete onboarding flow."""

    async def test_new_user_creates_profile(self):
        """Test new user going through complete onboarding."""
        # Mock bot message
        message = create_mock_message(user_id=12345)
        
        # Mock API client
        with patch("bot.main.APIGatewayClient") as mock_client:
            mock_client.create_profile = AsyncMock(return_value={"id": 1})
            
            # Send /start
            await start_handler(message)
            
            # Submit profile data
            await handle_profile_creation(message, profile_data)
            
            # Verify profile was created
            mock_client.create_profile.assert_called_once()
```

## 🔧 Test Configuration

### pytest.ini

```ini
[pytest]
addopts = -ra
asyncio_mode = auto
asyncio_default_fixture_loop_scope = function
filterwarnings =
    error
    ignore::DeprecationWarning:aiogram.*
```

### conftest.py

Contains shared fixtures and test configuration:
- `ensure_test_environment` - Sets required environment variables
- Shared mocks and helpers

## 📋 Test Guidelines

### Do's ✅

- Write isolated tests that don't depend on other tests
- Use descriptive test names that explain what is being tested
- Test both success and failure cases
- Use parametrize for testing multiple inputs
- Mock external dependencies (API calls, database, etc.)
- Clean up resources after tests (files, database records)
- Add docstrings to test functions
- Group related tests in classes

### Don'ts ❌

- Don't test implementation details, test behavior
- Don't use sleep() for timing - use proper async/await
- Don't hardcode sensitive data
- Don't modify global state
- Don't skip tests without a good reason and comment
- Don't write tests that depend on test execution order

## 🐛 Debugging Tests

### Run with verbose output
```bash
pytest -vv
```

### Show print statements
```bash
pytest -s
```

### Run specific test
```bash
pytest tests/unit/test_validation.py::TestProfileValidation::test_valid_profile -v
```

### Drop into debugger on failure
```bash
pytest --pdb
```

### Show local variables on failure
```bash
pytest -l
```

## 📈 Coverage

### Generate HTML coverage report
```bash
pytest --cov=bot --cov=core --cov=services --cov-report=html
open htmlcov/index.html
```

### Show missing lines
```bash
pytest --cov=bot --cov-report=term-missing
```

## 🔄 Continuous Integration

Tests are automatically run on:
- Push to main/develop branches
- Pull requests to main/develop branches

See `.github/workflows/test.yml` for CI configuration.

## 📚 Resources

- [pytest Documentation](https://docs.pytest.org/)
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/)
- [Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [CONTRIBUTING.md](../CONTRIBUTING.md) - Project contribution guidelines
