# GitHub Copilot Instructions for Dating App

This document provides context and guidelines for GitHub Copilot when working with this repository.

## Project Overview

**Dating** is a production-ready Telegram dating application built with a microservices architecture. The application features:
- **Minimalist Telegram bot** for notifications and basic commands
- **Next.js 15 WebApp** (primary modern frontend with React 19)
- **Legacy Telegram Mini App** (Vanilla JS, gradually being replaced)

### Tech Stack

#### Backend
- **Language**: Python 3.11+ (Docker images use 3.11, CI uses 3.12, dev: 3.12+ recommended)
- **Framework**: python-telegram-bot, FastAPI (for microservices)
- **Database**: PostgreSQL with SQLAlchemy (async)
- **Deployment**: Docker + Docker Compose
- **Testing**: pytest (380+ tests with pytest-asyncio)
- **CI/CD**: GitHub Actions
- **Monitoring**: Prometheus 2.51.0, Grafana 10.4.0, Loki v3.0.0 with TSDB

#### Frontend (Next.js WebApp)
- **Framework**: Next.js 15.5.4 with App Router
- **Runtime**: React 19.1.0 + React DOM 19.1.0
- **Language**: TypeScript (strict mode)
- **Styling**: Tailwind CSS v4 (PostCSS plugin)
- **UI Components**: shadcn/ui + lucide-react
- **State Management**: TanStack Query v5
- **Internationalization**: next-intl (ru/en)
- **Testing**: Playwright (smoke tests)
- **Code Quality**: ESLint 9 + Prettier 3

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
├── services/             # Microservices (7 services: auth, profile, discovery, media, chat, admin, notification)
├── gateway/              # API Gateway (port 8080 - single entry point)
├── adapters/             # Platform adapters
│   └── telegram/        # Telegram integration
├── bot/                  # Telegram bot code (thin client, notifications only)
├── webapp/               # Next.js 15 WebApp (primary modern frontend)
│   ├── src/
│   │   ├── app/         # Next.js App Router pages
│   │   ├── shared/      # Shared utilities and components
│   │   ├── entities/    # Domain entities
│   │   ├── features/    # Feature components
│   │   └── i18n/        # Internationalization
│   ├── messages/        # i18n translations (ru/en)
│   ├── public/          # Static assets
│   └── tests/           # Playwright tests
├── webapp_old/           # Legacy Vanilla JS Mini App (being phased out)
├── tests/                # Backend test suite (380+ tests)
│   ├── unit/            # Unit tests (180+)
│   ├── integration/     # Integration tests (110+)
│   └── e2e/             # End-to-end tests (90+)
└── docs/                 # Documentation (18+ guides)
    ├── INDEX.md         # Complete documentation index
    ├── GETTING_STARTED.md  # Quick start guide for new developers
    └── archive/         # Historical documentation (30+ files)
```

## Coding Standards

### Python Code Style (Backend)
- **Python Version**: 3.11+ with modern syntax (Docker: 3.11, CI: 3.12, dev: 3.12+ recommended)
- **Use Modern Syntax**: Use `|` for unions, not `Union`
- **Formatting**: Black with 88 character line length
- **Import Sorting**: isort with `--profile black`
- **Type Hints**: Use type hints everywhere (mypy validation)
- **Async/Await**: All I/O operations must be async (database, API calls)
- **Error Handling**: Always handle exceptions, provide clear error messages
- **Logging**: Use Python's `logging` module, not print statements

### TypeScript Code Style (Frontend - webapp/)
- **TypeScript Version**: 5.x with strict mode enabled
- **Framework**: Next.js 15 with App Router (use `app/` directory, not `pages/`)
- **React Version**: 19.x (use modern patterns: hooks, server components)
- **Formatting**: Prettier 3.x with Tailwind CSS plugin
- **Linting**: ESLint 9 with Next.js config
- **CSS**: Tailwind CSS v4 - use utility classes, avoid custom CSS when possible
- **Components**: Use shadcn/ui pattern (components in `src/shared/ui/`)
- **State Management**: TanStack Query v5 for server state, React hooks for local state
- **Internationalization**: Use next-intl for all user-facing text

### Code Quality Tools

#### Backend (Python)
Run these before committing:
```bash
black .                              # Format code
isort --profile black .              # Sort imports
flake8 . --max-line-length=127      # Lint (warnings only)
mypy --ignore-missing-imports .      # Type check
pip-audit                            # Security scan
pytest -v                            # Run all tests
```

#### Frontend (webapp/)
Run these before committing:
```bash
cd webapp
npm run format                       # Format with Prettier
npm run lint                         # Run ESLint
npm run type-check                   # TypeScript compiler check
npm test                             # Run Playwright tests
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

#### Backend Tests (380+ tests)
- **Unit tests** (`tests/unit/`): Test individual functions in isolation with mocks (180+ tests)
- **Integration tests** (`tests/integration/`): Test component interactions (110+ tests)
- **E2E tests** (`tests/e2e/`): Test complete user workflows (90+ tests)

#### Running Backend Tests
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

#### Frontend Tests (webapp/)
- **Playwright tests** (`webapp/tests/`): End-to-end smoke tests for WebApp

```bash
cd webapp
npm test                    # Run Playwright tests
npm run test:ui            # Run with UI mode
npm run test:headed        # Run in headed mode (see browser)
```

### Writing Tests

#### Backend Tests (pytest)
- **Name pattern**: `test_*.py` for files, `test_*` for functions
- **Use fixtures**: Defined in `conftest.py` files
- **Async tests**: Use `@pytest.mark.asyncio` decorator
- **Mocking**: Use `unittest.mock` or `pytest-mock`
- **Coverage goal**: Aim for >75% coverage for new code
- **Test data**: Use realistic data, check edge cases

#### Frontend Tests (Playwright)
- **Location**: `webapp/tests/` directory
- **Pattern**: Test critical user flows (homepage, navigation, i18n)
- **Configuration**: `playwright.config.ts` with timeout and retry settings
- **Best practices**: Test user-visible behavior, not implementation details

### Test Guidelines
1. Each test should test ONE thing
2. Use descriptive test names: `test_profile_creation_validates_age_requirement`
3. Follow AAA pattern: Arrange, Act, Assert
4. Mock external dependencies (database, API calls)
5. Clean up resources in teardown/fixtures
6. Update tests when changing functionality

## Common Development Tasks

### Adding a New Feature

#### Backend Feature
1. Create a feature branch: `git checkout -b feature/feature-name`
2. Update core business logic in `core/` if needed
3. Update relevant microservice in `services/`
4. Add/update tests in `tests/`
5. Update documentation
6. Run linting and tests locally (black, isort, pytest)
7. Create pull request

#### Frontend Feature (webapp/)
1. Create a feature branch: `git checkout -b feature/feature-name`
2. Add/update components in appropriate directory:
   - UI components: `src/shared/ui/`
   - Feature components: `src/features/`
   - Domain entities: `src/entities/`
3. Add translations to `messages/ru.json` and `messages/en.json`
4. Update routing if needed (`src/app/[locale]/`)
5. Add/update Playwright tests if testing critical flows
6. Run linting and tests locally (npm run lint, npm run format, npm test)
7. Create pull request

### Working with Database
- **Migrations**: Use Alembic (`alembic revision --autogenerate -m "description"`)
- **Models**: Define in `core/models/`
- **Repository pattern**: Access via repository classes
- **Async SQLAlchemy**: Always use `AsyncSession` and async queries
- **Connection strings**: Use `asyncpg` driver for PostgreSQL

### Environment Variables

#### Backend Environment Variables
Required (see `.env.example`):
- `BOT_TOKEN`: Telegram bot token
- `DATABASE_URL`: PostgreSQL connection string
- `JWT_SECRET`: Secret for JWT tokens (32+ characters)
- `API_GATEWAY_URL`: URL of API Gateway (e.g., `http://api-gateway:8080`)

Optional:
- `PHOTO_STORAGE_PATH`: Path for photos (default: `/app/photos`)
- `NSFW_THRESHOLD`: NSFW detection sensitivity (0.0-1.0, default: 0.7)
- `DOMAIN`: Domain for HTTPS deployment
- `ACME_EMAIL`: Email for Let's Encrypt certificates

#### Frontend Environment Variables (webapp/)
Required (in `webapp/.env.local` or via Docker):
- `NEXT_PUBLIC_API_URL`: Backend API URL (e.g., `http://api-gateway:8080`)
- `NEXT_PUBLIC_SITE_URL`: Public site URL for SEO (e.g., `https://yourdomain.com`)

Optional:
- `DOMAIN`: Domain for Traefik routing (default: `localhost`)

### Docker Development
```bash
# Build and start all services (backend only)
docker compose build
docker compose up -d

# Start with monitoring (Prometheus, Grafana, Loki v3.0)
docker compose --profile monitoring up -d

# Start with webapp (Next.js frontend)
docker compose --profile webapp up -d

# Full stack (all services + monitoring + webapp)
docker compose --profile monitoring --profile webapp up -d

# View logs
docker compose logs -f telegram-bot
docker compose logs -f api-gateway
docker compose logs -f webapp

# Restart a service
docker compose restart telegram-bot
docker compose restart webapp

# Stop all services
docker compose down
```

### Local Development (without Docker)

#### Backend Development
```bash
# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run database migrations
alembic upgrade head

# Start a microservice (example: profile service)
cd services/profile
python main.py
```

#### Frontend Development (webapp/)
```bash
cd webapp

# Install dependencies
npm install

# Set environment variables
cp .env.example .env.local
# Edit .env.local with your API_GATEWAY_URL

# Start development server (port 3000)
npm run dev

# Open http://localhost:3000
```

### API Gateway Usage
All bot and WebApp requests should go through API Gateway at port 8080:
- **Bot** uses `APIGatewayClient` class (see `bot/api_client.py`)
- **Legacy Mini App** calls endpoints like `/api/profiles`, `/api/matches`
- **Next.js WebApp** uses Next.js API routes that proxy to API Gateway
- **Never** access microservices directly from clients - always through Gateway

#### Next.js API Routes (webapp/)
The webapp uses Next.js server-side API routes to proxy requests:
```typescript
// Example: webapp/src/app/api/profiles/route.ts
export async function GET() {
  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/profiles`)
  return response
}
```

## CI/CD Pipeline

### Workflows

#### Backend Workflows
1. **test.yml**: Runs on every push/PR - executes all 380+ backend tests with PostgreSQL
2. **lint.yml**: Code quality checks (black, isort, flake8, mypy, pip-audit)
3. **docker-build.yml**: Validates Docker images can be built
4. **deploy-microservices.yml**: Deploys to production on main branch
5. **health-check.yml**: Periodic production health monitoring
6. **pr-validation.yml**: Additional PR checks

#### Frontend Workflows (webapp/)
7. **webapp-ci.yml**: Runs on webapp changes
   - Installs dependencies with npm ci
   - Lints code (ESLint)
   - Checks formatting (Prettier)
   - Type checks (TypeScript)
   - Builds production bundle
   - Runs Playwright smoke tests

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

### Documentation Structure
The project has a comprehensive documentation system:
- **docs/INDEX.md**: Complete navigation hub for all documentation (start here!)
- **docs/GETTING_STARTED.md**: Step-by-step guide for new developers
- **README.md**: Project overview, quick start, main reference
- **CONTRIBUTING.md**: Contribution guidelines and standards
- **ROADMAP.md**: Feature planning (with "Already Implemented" section)
- **CHANGELOG.md**: Version history and changes
- **docs/archive/**: Historical documentation (30+ completed summaries and bug fixes)

### Where to Update Documentation

#### For New Features
1. Update **README.md** if it's a major user-facing feature
2. Move relevant items from "Planned" to "Already Implemented" in **ROADMAP.md**
3. Add entry to **CHANGELOG.md** under [Unreleased]
4. Create/update specific documentation in **docs/**
5. Update **docs/INDEX.md** if adding new documentation file

#### For Code Changes
- **Backend**: Update docstrings in Python code
- **Frontend**: Update JSDoc comments in TypeScript code
- **services/*/README.md**: Service-specific documentation
- **webapp/README.md**: Frontend-specific documentation
- **webapp/docs/**: Frontend guides (deployment, security, etc.)

### Documentation Style
- Use clear, concise language
- Include code examples
- Keep documentation in sync with code
- Add inline comments only for complex logic
- Use Russian for user-facing documentation (docs/INDEX.md, docs/GETTING_STARTED.md)
- Use English for technical API documentation

## Troubleshooting

### Common Issues

#### Backend Issues
1. **Port conflicts**: Check `docker-compose.yml` for port mappings (8080-8087)
2. **Database connection**: Ensure PostgreSQL is ready before running migrations
3. **JWT errors**: Check `JWT_SECRET` is set and consistent
4. **NSFW detection**: Model downloads on first run (may be slow)
5. **Test failures**: Ensure test database is migrated (`alembic upgrade head`)

#### Frontend Issues (webapp/)
1. **Build errors**: Check Node.js version (must be 20+)
2. **Type errors**: Run `npm run type-check` to see all TypeScript errors
3. **Styling issues**: Ensure Tailwind CSS v4 PostCSS plugin is configured
4. **API connection**: Check `NEXT_PUBLIC_API_URL` in `.env.local`
5. **i18n errors**: Ensure translations exist in both `messages/ru.json` and `messages/en.json`

#### Docker Issues
1. **Traefik routing**: WebApp accessible only via Traefik (not on exposed ports directly)
2. **Network issues**: Run `docker compose down && docker network prune -f`
3. **Volume issues**: Check `docker volume ls` and `docker compose down -v` to clean

### Getting Help
1. Check **docs/INDEX.md** for complete documentation navigation
2. Review **docs/DEPLOYMENT_TROUBLESHOOTING.md** for deployment issues
3. Check existing [GitHub Issues](https://github.com/erliona/dating/issues)
4. Review documentation in `docs/` directory
5. Check workflow runs for CI/CD issues
6. Review logs: `docker compose logs -f service-name`

## Monitoring and Observability

The project uses a comprehensive monitoring stack (v3.0):

### Stack Components
- **Prometheus 2.51.0**: Metrics collection with TSDB
- **Grafana 10.4.0**: Visualization and dashboards
- **Loki v3.0.0**: Log aggregation with TSDB
- **Promtail**: Log shipping to Loki

### Starting Monitoring
```bash
# Start with monitoring profile
docker compose --profile monitoring up -d

# Access interfaces
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
```

### Key Metrics
All microservices expose metrics at `/metrics` endpoint:
- Request rates and latencies
- Error rates
- Database connection pool stats
- Custom business metrics

See **docs/MONITORING_SETUP.md** for detailed configuration.

## Notes for AI Assistants

When suggesting code changes:

### General Principles
1. **Maintain backward compatibility** unless explicitly requested to break it
2. **Follow existing patterns** - Look at similar code in the repository
3. **Test thoroughly** - Always suggest running tests after changes
4. **Keep it minimal** - Make smallest possible changes
5. **Update tests** - If changing logic, update or add tests
6. **Document changes** - Update docstrings and relevant docs
7. **Consider performance** - This is a production application
8. **Think microservices** - Changes may affect multiple services

### Frontend-Specific (webapp/)
1. **Use App Router** - All new pages go in `src/app/[locale]/`
2. **Server Components by default** - Only use 'use client' when necessary
3. **Internationalization** - All user text must be in both ru.json and en.json
4. **Tailwind-first** - Use Tailwind utilities, avoid custom CSS
5. **shadcn/ui pattern** - Follow established component structure
6. **Type safety** - Leverage TypeScript strict mode
7. **Responsive design** - Mobile-first approach
8. **Accessibility** - Use semantic HTML and ARIA when needed

### Backend-Specific
1. **Async everywhere** - All I/O operations must be async
2. **Service isolation** - Keep microservices independent
3. **API Gateway** - All client requests go through gateway
4. **Database migrations** - Use Alembic for schema changes
5. **Health checks** - All services must expose `/health` endpoint

Remember: This is a production dating application handling personal data. Security, privacy, and data validation are paramount.
