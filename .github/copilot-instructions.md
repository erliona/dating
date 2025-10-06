# GitHub Copilot Instructions for Dating App

This document provides context and guidelines for GitHub Copilot when working with this repository.

## Project Overview

**Dating** is a production-ready Telegram dating application built with a microservices architecture. The application features a minimalist Telegram bot for notifications and a Telegram Mini App (WebApp) for the main user interface.

### Tech Stack
- **Language**: Python 3.12
- **Framework**: python-telegram-bot, FastAPI (for microservices)
- **Database**: PostgreSQL with SQLAlchemy (async)
- **Deployment**: Docker + Docker Compose
- **Testing**: pytest (360+ tests with pytest-asyncio)
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus, Grafana, Loki

## Architecture

### Microservices Structure
The application uses a clean microservices architecture with the following services:

- **telegram-bot**: Minimalist bot for notifications and basic commands
- **api-gateway** (port 8080): Single entry point for all API requests
- **auth-service** (port 8081): JWT tokens and authentication
- **profile-service** (port 8082): User profiles and CRUD operations
- **discovery-service** (port 8083): Matching algorithm and search
- **media-service** (port 8084): Photo handling and NSFW detection
- **chat-service** (port 8085): Messaging functionality
- **admin-service** (port 8086): Administrative panel
- **notification-service** (port 8087): Centralized push notifications

### Key Architecture Principles
1. **Thin Client Pattern**: Bot acts as notification gateway, WebApp handles all logic
2. **API Gateway**: All client requests go through the gateway (no direct service access)
3. **Clean Architecture**: Business logic in `core/`, adapters in `adapters/`, services in `services/`
4. **Single Source of Truth**: PostgreSQL database, accessed through services

### Project Structure
```
dating/
├── core/                  # Platform-agnostic business logic
│   ├── models/           # Domain models (User, Profile, Match)
│   ├── services/         # Business services
│   └── utils/            # Utilities (validation, security)
├── services/             # Microservices (auth, profile, discovery, etc.)
├── gateway/              # API Gateway
├── adapters/             # Platform adapters
│   └── telegram/        # Telegram integration
├── bot/                  # Telegram bot code
├── webapp/               # Frontend (Mini App)
├── tests/                # Test suite
│   ├── unit/            # Unit tests
│   ├── integration/     # Integration tests
│   └── e2e/             # End-to-end tests
└── docs/                 # Documentation
```

## Coding Standards

### Python Code Style
- **Python Version**: 3.12+ with modern syntax (use `|` for unions, not `Union`)
- **Formatting**: Black with 88 character line length
- **Import Sorting**: isort with `--profile black`
- **Type Hints**: Use type hints everywhere (mypy validation)
- **Async/Await**: All I/O operations must be async (database, API calls)
- **Error Handling**: Always handle exceptions, provide clear error messages
- **Logging**: Use Python's `logging` module, not print statements

### Code Quality Tools
Run these before committing:
```bash
black .                              # Format code
isort --profile black .              # Sort imports
flake8 . --max-line-length=127      # Lint (warnings only)
mypy --ignore-missing-imports .      # Type check
pip-audit                            # Security scan
```

### Best Practices
1. **Never commit secrets** - Use environment variables via `.env` files
2. **Validate all user input** - Use `validate_profile_data()` and `sanitize_user_input()`
3. **Use dataclasses** - With `@dataclass(slots=True)` for performance
4. **Async contexts** - Use `async with` for sessions, connections
5. **Resource cleanup** - Always close connections, files, sessions
6. **API versioning** - Maintain backward compatibility when changing APIs

## Testing Requirements

### Test Organization
- **Unit tests** (`tests/unit/`): Test individual functions in isolation with mocks
- **Integration tests** (`tests/integration/`): Test component interactions
- **E2E tests** (`tests/e2e/`): Test complete user workflows

### Running Tests
```bash
# Run all tests
pytest -v

# Run specific category
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/e2e/ -v

# Run with markers
pytest -m unit
pytest -m integration

# Coverage report
pytest --cov=bot --cov=core --cov=services --cov-report=html
```

### Writing Tests
- **Name pattern**: `test_*.py` for files, `test_*` for functions
- **Use fixtures**: Defined in `conftest.py` files
- **Async tests**: Use `@pytest.mark.asyncio` decorator
- **Mocking**: Use `unittest.mock` or `pytest-mock`
- **Coverage goal**: Aim for >75% coverage for new code
- **Test data**: Use realistic data, check edge cases

### Test Guidelines
1. Each test should test ONE thing
2. Use descriptive test names: `test_profile_creation_validates_age_requirement`
3. Follow AAA pattern: Arrange, Act, Assert
4. Mock external dependencies (database, API calls)
5. Clean up resources in teardown/fixtures
6. Update tests when changing functionality

## Common Development Tasks

### Adding a New Feature
1. Create a feature branch: `git checkout -b feature/feature-name`
2. Update core business logic in `core/` if needed
3. Update relevant microservice in `services/`
4. Add/update tests in `tests/`
5. Update documentation
6. Run linting and tests locally
7. Create pull request

### Working with Database
- **Migrations**: Use Alembic (`alembic revision --autogenerate -m "description"`)
- **Models**: Define in `core/models/`
- **Repository pattern**: Access via repository classes
- **Async SQLAlchemy**: Always use `AsyncSession` and async queries
- **Connection strings**: Use `asyncpg` driver for PostgreSQL

### Environment Variables
Required environment variables (see `.env.example`):
- `BOT_TOKEN`: Telegram bot token
- `DATABASE_URL`: PostgreSQL connection string
- `JWT_SECRET`: Secret for JWT tokens
- `API_GATEWAY_URL`: URL of API Gateway (e.g., `http://api-gateway:8080`)

Optional:
- `PHOTO_STORAGE_PATH`: Path for photos (default: `/app/photos`)
- `NSFW_THRESHOLD`: NSFW detection sensitivity (0.0-1.0, default: 0.7)
- `DOMAIN`: Domain for HTTPS deployment
- `ACME_EMAIL`: Email for Let's Encrypt certificates

### Docker Development
```bash
# Build and start all services
docker compose build
docker compose up -d

# Start with monitoring
docker compose --profile monitoring up -d

# View logs
docker compose logs -f telegram-bot
docker compose logs -f api-gateway

# Restart a service
docker compose restart telegram-bot

# Stop all services
docker compose down
```

### API Gateway Usage
All bot and WebApp requests should go through API Gateway at port 8080:
- Bot uses `APIGatewayClient` class (see `bot/api_client.py`)
- WebApp calls endpoints like `/api/profiles`, `/api/matches`
- Never access microservices directly from clients

## CI/CD Pipeline

### Workflows
1. **test.yml**: Runs on every push/PR - executes all tests with PostgreSQL
2. **lint.yml**: Code quality checks (black, isort, flake8, mypy, pip-audit)
3. **docker-build.yml**: Validates Docker images can be built
4. **deploy-microservices.yml**: Deploys to production on main branch
5. **health-check.yml**: Periodic production health monitoring
6. **pr-validation.yml**: Additional PR checks

### GitHub Secrets Required
For deployment:
- `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_SSH_KEY`: SSH credentials
- `BOT_TOKEN`: Telegram bot token
- `JWT_SECRET`: JWT signing key
- Optional: `DOMAIN`, `ACME_EMAIL`, `CODECOV_TOKEN`

## Security Guidelines

### Critical Security Rules
1. **Never hardcode credentials** - Always use environment variables
2. **Validate age**: Users must be 18+ (see `validate_profile_data`)
3. **Sanitize input**: All user text through `sanitize_user_input()`
4. **Rate limiting**: Apply to all authenticated endpoints (20 req/min default)
5. **JWT validation**: Verify tokens on all protected endpoints
6. **HTTPS only**: Production must use HTTPS (Traefik + Let's Encrypt)
7. **NSFW detection**: All photos through NSFW detector before approval

### HMAC Validation
Telegram WebApp data must be validated:
```python
from bot.security import validate_telegram_webapp_data
if not validate_telegram_webapp_data(init_data, bot_token):
    raise Unauthorized("Invalid Telegram data")
```

### Password Handling
- Use bcrypt for hashing (admin panel)
- Never store plaintext passwords
- Enforce strong password requirements

## Common Patterns

### Async Database Operations
```python
from sqlalchemy.ext.asyncio import AsyncSession

async def get_profile(session: AsyncSession, user_id: int):
    result = await session.execute(
        select(Profile).where(Profile.user_id == user_id)
    )
    return result.scalar_one_or_none()
```

### API Client Usage (Bot)
```python
from bot.api_client import APIGatewayClient

async with APIGatewayClient(config.api_gateway_url) as client:
    profile = await client.get_profile(user_id)
```

### Error Responses
```python
from fastapi import HTTPException

raise HTTPException(
    status_code=400,
    detail="Invalid profile data: age must be 18+"
)
```

### Logging
```python
import logging

logger = logging.getLogger(__name__)
logger.info(f"Profile created for user {user_id}")
logger.error(f"Failed to upload photo: {error}", exc_info=True)
```

## Documentation

### Where to Update Documentation
- **README.md**: Project overview, setup instructions
- **CONTRIBUTING.md**: Contribution guidelines
- **docs/**: Detailed guides (CI/CD, deployment, architecture)
- **services/*/README.md**: Service-specific documentation
- **Docstrings**: All public functions and classes

### Documentation Style
- Use clear, concise language
- Include code examples
- Keep documentation in sync with code
- Add inline comments only for complex logic

## Troubleshooting

### Common Issues
1. **Port conflicts**: Check `docker-compose.yml` for port mappings
2. **Database connection**: Ensure PostgreSQL is ready before running migrations
3. **JWT errors**: Check `JWT_SECRET` is set and consistent
4. **NSFW detection**: Model downloads on first run (may be slow)
5. **Test failures**: Ensure test database is migrated (`alembic upgrade head`)

### Getting Help
1. Check existing [GitHub Issues](https://github.com/erliona/dating/issues)
2. Review documentation in `docs/` directory
3. Check workflow runs for CI/CD issues
4. Review logs: `docker compose logs -f service-name`

## Notes for AI Assistants

When suggesting code changes:
1. **Maintain backward compatibility** unless explicitly requested to break it
2. **Follow existing patterns** - Look at similar code in the repository
3. **Test thoroughly** - Always suggest running tests after changes
4. **Keep it minimal** - Make smallest possible changes
5. **Update tests** - If changing logic, update or add tests
6. **Document changes** - Update docstrings and relevant docs
7. **Consider performance** - This is a production application
8. **Think microservices** - Changes may affect multiple services

Remember: This is a production dating application handling personal data. Security, privacy, and data validation are paramount.
