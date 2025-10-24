# ==== CRITICAL WORKFLOWS ====

## Code Synchronization (CRITICAL)
- ALWAYS keep code synchronized between: Local Machine ↔ GitHub ↔ Server
- After ANY code changes: 1) Commit locally 2) Push to GitHub 3) Update server
- Server update: `ssh root@dating.serge.cc "cd /root/dating-microservices && git pull origin main && docker compose restart [affected-services]"`
- Never make changes directly on server - always go through Git workflow
- If server changes are needed, commit them locally first, then sync
- Verify synchronization: check git status, commit hashes, and service health on all three points

## Git Workflow
- All code changes must go through git: feature branch → commits → PR → review → merge → CI/CD rebuild
- Never modify files inside running containers or rely on manual hot-patches
- Use descriptive branch names: `feat/feature-name`, `fix/bug-description`, `refactor/component-name`
- Keep branches focused on single features or fixes
- Rebase feature branches on main before creating PR
- Use conventional commit messages: `<type>(scope): description`
- Include testing notes and deployment instructions in PR description

# ==== PROJECT IDENTITY & STACK ====

## Project Identity
- This is a Telegram Mini App with an API Gateway and multiple Python microservices
- Stack: Python 3.11+, aiogram 3.x, aiohttp 3.9+, SQLAlchemy 2.x (async), asyncpg, Alembic, PyJWT, bcrypt
- Infra: Docker + Docker Compose, Traefik 2.x, PostgreSQL 15, Prometheus/Grafana/Loki
- Frontend: Vue 3 + Vite + Pinia behind Nginx
- Always respect the existing folder layout: bot/, core/, gateway/, services/*, webapp/, monitoring/, migrations/, scripts/
- Never hardcode ports. Use envs from .env/.env.example and docker-compose

# ==== NAMING CONVENTIONS & STANDARDS ====

## Migration Naming & Management
- ✅ **Standard approach**: Use full filename as revision ID (e.g., `"007_create_chat_tables"`)
- ✅ **File naming**: Use descriptive filenames like `007_create_chat_tables.py` for readability
- ❌ **Anti-pattern**: Manual revision ID changes after migration is in main branch
- ❌ **Anti-pattern**: Short numeric IDs like `"007"` (causes conflicts)
- ❌ **Anti-pattern**: Renaming migrations to `.bak` - Alembic won't see them

### Migration Workflow Rules
- **New migrations**: Use `alembic revision -m "descriptive message"` (auto-generates hash)
- **File naming**: Keep descriptive filenames for human readability
- **Never manually edit revision IDs** after migration is committed to main
- **Merge conflicts**: Use `alembic merge` command, never manual editing
- **Database version**: Check with `SELECT version_num FROM alembic_version;`
- **RUN_DB_MIGRATIONS**: Set to `true` only for one service (usually telegram-bot)

### Migration Conflict Resolution
- **Before merging**: Always run `alembic check` to verify migration chain
- **Merge conflicts**: Use `alembic merge -m "merge message"` to create merge migration
- **Never manually edit** `down_revision` in existing migrations
- **PR checklist**: Verify migration chain integrity before approval
- **Rollback safety**: Test `alembic downgrade` before production deployment

### PR Checklist for Migrations
- [ ] Migration file has descriptive name (e.g., `007_create_chat_tables.py`)
- [ ] Revision ID is full filename (not manually edited)
- [ ] `down_revision` points to correct previous migration
- [ ] Run `alembic check` - no errors
- [ ] Test migration locally: `alembic upgrade head`
- [ ] Test rollback: `alembic downgrade -1` then `alembic upgrade head`
- [ ] No `.bak` files in migrations/versions/
- [ ] Migration is reversible (has both `upgrade()` and `downgrade()`)

### Emergency Migration Procedures
- **Broken migration chain**: Use `alembic stamp <revision>` to reset to known good state
- **Missing migrations**: Never skip migrations - always create proper merge migration
- **Production issues**: Have rollback plan ready before applying migrations
- **Database corruption**: Restore from backup, then reapply migrations in order

### Common Migration Commands
```bash
# Create new migration
alembic revision -m "descriptive message"

# Check migration chain integrity
alembic check

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision>

# Merge conflicting migrations
alembic merge -m "merge message" <revision1> <revision2>

# Reset to specific revision (emergency only)
alembic stamp <revision>

# Show current revision
alembic current

# Show migration history
alembic history
```

## API Route Naming
- Pattern: `/api/v1/<resource>/<action>`
- Public routes: No JWT required (e.g., `/admin/auth/login`, `/health`)
- Protected routes: JWT required via sub-applications
- Admin routes: `/admin/` for UI, `/admin/auth/` for auth, `/admin/api/` for protected API
- Use nouns for resources; verbs only for RPC-like actions
- Keep OpenAPI/markdown snippets in `docs/` (or service-local); include request/response examples

## Docker Service Naming
- Services: Use kebab-case (e.g., `api-gateway`, `admin-service`, `telegram-bot`)
- Networks: `default`, `monitoring` (simple, descriptive)
- Containers: Auto-generated by Docker Compose (don't rely on them)
- Prometheus targets: Use short service names, NOT full container names
- Service names in targets: use short names (`api-gateway`), NOT full Docker Compose names (`dating-microservices-api-gateway-1`)

## Docker Network Standards
- Application services: `default` network
- Monitoring services: `monitoring` network
- Cross-network access: Add service to both networks if needed (e.g., Prometheus in `default` + `monitoring`)
- NEVER use IP addresses in configurations (Prometheus, service URLs, etc.)
- Use only domain names or Docker service names
- Format for inter-service calls: `<service-name>:<port>` or `dating-microservices-<service>-1:<port>`
- Check service connection to necessary Docker networks (especially `monitoring`) before deployment
- Command to check: `docker network inspect <network> | jq '.[0].Containers'`

## Environment Variables
- Format: `SCREAMING_SNAKE_CASE`
- Secrets: Must be in `.env`, never hardcoded
- Documentation: Must be in `.env.example` with description
- No duplicates: Check for duplicate variable definitions
- When changing ENV vars: use `docker compose up -d service` (recreate), NOT just `restart`
- Check that ENV vars got into container: `docker compose exec service env | grep VARIABLE`
- Secrets generation: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- NEVER duplicate variables in .env file (especially JWT_SECRET)
- Check .env.example sync when adding new variables

## Static File Serving
- Pattern: `app.router.add_static("/path/", "directory/")`
- Trailing slashes: Consistent use for directories
- Index files: Configure via `show_index=False` by default

## Middleware & Sub-Applications
- Public routes: No JWT middleware
- Protected routes: Separate sub-application with JWT middleware
- Pattern: Mount protected sub-app under specific prefix (e.g., `/admin/api/`)

# ==== CODING STANDARDS ====

## Python Style
- Use modern Python with full type hints and `from __future__ import annotations`
- Async first: prefer async/await everywhere; no blocking calls in event loops
- Use SQLAlchemy 2.0 ORM (async) with explicit `select()` API; avoid legacy 1.x patterns
- Keep functions focused (< ~50 LOC when reasonable). Prefer pure functions; minimize side effects
- Logging only via project utilities in core; no `print`
- Validate inputs at all edges (bot handlers, HTTP handlers); sanitize user text before storage/render

## Database & SQLAlchemy
- Use explicit transactions with async sessions (one per request when needed)
- Every schema change → Alembic migration; keep migrations reversible and idempotent
- Prevent N+1 via joined eager loads or batching; confirm with test data and logs
- Add DB indexes for hot queries via migrations; consider back-pressure friendly designs

## API Design & Error Handling
- Handlers return typed JSON with a consistent error envelope:
  { "error": { "code": string, "message": string, "details": object? } }
- Map exceptions to sensible 4xx/5xx; do not leak stack traces to clients (log them)
- Timeouts/retries/circuit breakers on inter-service calls where appropriate
- Paginate list endpoints; cap payload sizes; stream large media via Media Service

# ==== ARCHITECTURE & BOUNDARIES ====

## Microservices Separation
- Gateway is the single public entrypoint. Services talk via gateway/API contracts only
- Each service owns its DB schema and Alembic migrations; do not mutate other services' tables
- JWT: verification/refresh only via Auth Service; do not reimplement JWT in other services
- Media through Media Service; Chat through Chat Service; Discovery encapsulates matching; Admin isolated; Notification handles outbound messages
- Share code only through core utilities or well-defined client modules; avoid cross-imports between services

## Bot (aiogram)
- Handlers must be thin; move business logic to service layer
- Use middlewares from `core/middleware` (jwt, metrics, request logging) consistently
- Never block the bot loop; offload heavy work to background jobs/workers if present

## Frontend (webapp/)
- **Vue 3 + Vite + Pinia**: Modern reactive framework with composition API and state management
- **Component structure**: Single File Components (.vue) with `<script setup>`, `<template>`, `<style scoped>`
- **State management**: Pinia stores for user, chat, discovery, matches with reactive state
- **Routing**: Vue Router with lazy loading, route guards, and admin route protection
- **Composables**: Reusable logic in `composables/` (useApi, useWebSocket, useTelegram, useSwipe)
- **Telegram integration**: Telegram WebApp SDK for theme, user data, and platform features
- **API communication**: Axios for HTTP requests, WebSocket for real-time chat
- **Build optimization**: Vite for fast builds, tree-shaking, and code splitting
- **Responsive design**: Mobile-first CSS with Telegram theme integration
- **Performance**: Lazy loading, component caching, minimal bundle size

### Vue 3 Development Standards
- **Composition API**: Use `<script setup>` syntax, avoid Options API
- **Reactivity**: Use `ref()`, `reactive()`, `computed()`, `watch()` for reactive state
- **Component props**: Define with TypeScript-like syntax: `defineProps<{ prop: string }>()`
- **Emits**: Use `defineEmits<{ event: [payload: any] }>()` for type-safe events
- **Lifecycle**: Use `onMounted()`, `onUnmounted()`, `onUpdated()` instead of options
- **Pinia stores**: Use `defineStore()` with composition API, avoid mutations
- **Telegram WebApp**: Always check `window.Telegram?.WebApp` availability
- **Error handling**: Use try/catch in async functions, show user-friendly messages
- **Loading states**: Implement loading spinners and skeleton screens
- **Accessibility**: Use semantic HTML, ARIA attributes, keyboard navigation

# ==== SECURITY & CONFIGURATION ====

## Secrets Management
- **No secrets in code**: Use env vars; keep `.env.example` in sync
- **JWT Security Policy**: See `docs/jwt-security-policy.md` for comprehensive JWT standards, key rotation, and SLO requirements
- **Password hashing**: bcrypt with appropriate rounds (minimum 12)
- **Token management**: PyJWT with proper expiration and refresh flows
- **Key rotation**: JWT secrets rotated every 90 days, emergency rotation within 24 hours
- **SLO targets**: JWT generation < 50ms, validation < 10ms, refresh flow < 150ms (95th percentile)
- **Strong secrets**: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- **Audit logging**: All authentication events logged with timestamps
- **NEVER commit secrets**: Check .gitignore before commit
- **Update documentation**: Update .env.example when adding new variables

## JWT Authentication
- Public routes (login, health) MUST NOT require JWT
- Use sub-applications in aiohttp for separating public/protected routes
- Check that ADMIN_PASSWORD and JWT_SECRET are set in .env
- NEVER duplicate JWT_SECRET in .env file
- Test login endpoints after middleware changes

# ==== ENVIRONMENT MANAGEMENT ====

## Two Environments Only
- **TWO environments ONLY**: development (local) and production (server)
- **Environment detection**: Use `ENVIRONMENT=development|production` to distinguish
- **Monitoring stack**: Prometheus, Grafana, Loki ONLY on production
- **Development**: `docker compose up -d` (no monitoring)
- **Production**: `docker compose --profile production up -d` (with monitoring)
- **Always test locally** before deploying to production

## Environment Configuration
- **Local development**: Use `.env` file with `ENVIRONMENT=development`
- **Production server**: Use `.env` file with `ENVIRONMENT=production`
- **Required variables**: `BOT_TOKEN`, `JWT_SECRET`, `POSTGRES_PASSWORD`
- **Environment-specific**: Different domains, SSL, monitoring
- **Never commit**: `.env` files to git

# ==== DOCKER & INFRASTRUCTURE ====

## Container Management
- All services must build & run under `docker-compose` without manual steps
- Do not change service names/labels without updating Traefik routes
- Use slim, pinned base images; multi-stage builds; avoid running as root where possible
- Code changes: `docker compose build <service> && docker compose up -d <service>`
- Dependency changes: `docker compose build --no-cache <service> && docker compose up -d <service>`
- Environment changes: `docker compose up -d <service>` (recreate container)
- Infrastructure changes: `docker compose up --build -d` (rebuild all affected services)

## Docker Security Standards
- **Base images**: MUST be pinned with specific versions (e.g., `python:3.11.7-slim`, not `python:3.11-slim`)
- **Distroless/Slim**: Prefer distroless or slim variants to minimize attack surface
- **Non-root user**: ALL services MUST run as non-root user (USER app)
- **Security options**: Add to docker-compose.yml for each service:
  - `security_opt: [no-new-privileges:true]`
  - `cap_drop: [ALL]`
  - `cap_add:` only specific capabilities if needed
- **Read-only root**: Use `read_only: true` where possible, with tmpfs for writable dirs
- **Health checks**: MANDATORY HTTP health check on `/health` endpoint for all services
- **Restart policy**: Use `restart: unless-stopped` for all production services

## Nginx Configuration
- In `/etc/nginx/conf.d/*.conf` NEVER include `events {}` or `http {}` blocks
- Only `server {}` blocks in conf.d files
- When error "directive is not allowed here" - check that there are no top-level directives
- Check that Nginx config is valid: `nginx -t` before restart

## Traefik & Routing
- **Standardized routing contracts**: See `docs/traefik-routes.md` for complete middleware stacks and priority matrices
- **Middleware standards**: Use consistent strip-prefix, security-headers, rate-limit middleware
- **Priority matrix**: Webapp(1) > Admin(50) > API Direct(100) > API Strip(200) > Health(300) > Metrics(400)
- **Route testing**: `curl http://localhost:8091/api/http/routers | jq '.[] | {name: .name, rule: .rule, priority: .priority}'`
- **Service discovery**: `curl http://localhost:8091/api/http/services`

# ==== DATABASE & MIGRATIONS ====

## Alembic Best Practices
- **Use full filename as revision ID**: Let Alembic create 12-char hashes automatically
- **Descriptive filenames**: Use meaningful names like `007_create_chat_tables.py`
- **Never edit revision IDs**: Once in main branch, never manually change revision IDs
- **Reversible migrations**: Always implement both `upgrade()` and `downgrade()`
- **Test locally first**: Always test migrations before production deployment
- **Merge conflicts**: Use `alembic merge` command, never manual editing
- **Chain integrity**: Run `alembic check` before merging PRs
- **Single migration service**: Set `RUN_DB_MIGRATIONS=true` only for one service (usually telegram-bot)
- **Emergency procedures**: Know how to use `alembic stamp` for recovery

### Migration Safety Guards
- **CI Validation**: Build MUST fail if multiple services have `RUN_DB_MIGRATIONS=true`
- **Deployment Smoke Check**: 
  1. Check current migration: `alembic current`
  2. Apply migrations: `alembic upgrade head`
  3. Verify critical endpoints: `/health`, `/admin/auth/login`, `/api/v1/auth/health`
- **Pre-deployment**: Always verify migration chain integrity before production
- **Post-deployment**: Confirm all services can connect to updated schema

### CI Migration Validation Script
```bash
#!/bin/bash
# Check that only one service has RUN_DB_MIGRATIONS=true
MIGRATION_SERVICES=$(grep -r "RUN_DB_MIGRATIONS.*true" docker-compose.yml | wc -l)
if [ "$MIGRATION_SERVICES" -gt 1 ]; then
    echo "ERROR: Multiple services have RUN_DB_MIGRATIONS=true"
    echo "Only one service should run migrations to avoid conflicts"
    exit 1
fi
echo "✅ Migration safety check passed"
```

### Deployment Smoke Check Script
```bash
#!/bin/bash
# Pre-deployment migration verification
echo "🔍 Checking migration chain integrity..."
alembic check || { echo "❌ Migration chain broken"; exit 1; }

echo "📊 Current migration state..."
alembic current

echo "⬆️ Applying migrations..."
alembic upgrade head || { echo "❌ Migration failed"; exit 1; }

echo "🏥 Testing critical endpoints..."
curl -f http://localhost:8080/health || { echo "❌ Health check failed"; exit 1; }
curl -f http://localhost:8080/api/v1/auth/health || { echo "❌ Auth service failed"; exit 1; }
curl -f http://localhost:8080/admin/auth/login -X POST -H "Content-Type: application/json" -d '{"username":"test","password":"test"}' || echo "⚠️ Admin login test (expected to fail with test credentials)"

echo "✅ Migration smoke check passed"
```

### GitHub Actions Integration
```yaml
# Add to .github/workflows/test.yml
- name: Validate Migration Safety
  run: |
    # Check only one service has RUN_DB_MIGRATIONS=true
    MIGRATION_SERVICES=$(grep -r "RUN_DB_MIGRATIONS.*true" docker-compose.yml | wc -l)
    if [ "$MIGRATION_SERVICES" -gt 1 ]; then
      echo "❌ ERROR: Multiple services have RUN_DB_MIGRATIONS=true"
      echo "Only one service should run migrations to avoid conflicts"
      exit 1
    fi
    echo "✅ Migration safety check passed"

- name: Test Migration Chain
  run: |
    # Start database for migration testing
    docker compose up -d db
    sleep 10
    
    # Check migration chain integrity
    docker compose exec -T db alembic check
    echo "✅ Migration chain integrity verified"
```

# ==== TESTING & QUALITY ====

## Testing Standards
- Use pytest. For new logic add unit tests; for endpoints add integration tests with test DB
- Keep tests deterministic and fast; use fixtures/factories; mock network calls
- Maintain/raise coverage thresholds defined in repo configs; add regression tests for fixed bugs

## Code Quality & Standards
- **Pre-commit hooks**: Install with `./scripts/setup-code-quality.sh` - enforces formatting, linting, type checking
- **Black formatting**: Line length 88, Python 3.11+ target, auto-format on commit
- **Ruff linting**: Fast Python linter with auto-fix, comprehensive rule set
- **MyPy type checking**: Strict mode for core/, services/, gateway/ - catches type errors early
- **isort imports**: Black-compatible import sorting, consistent import organization
- **Bandit security**: Security vulnerability scanning, excludes tests and migrations
- **YAML linting**: Docker-compose and CI configuration validation
- **Conventional Commits**: Use `cz commit` or follow pattern: `type(scope): description`
- **CI enforcement**: Static checks job fails on any quality violations
- **Coverage threshold**: Minimum 80% code coverage, enforced in CI

## Versioning & Releases
- **Semantic Versioning**: Use `vMAJOR.MINOR.PATCH` format (e.g., `v1.2.0`)
- **Release process**: Use `./scripts/release.sh patch|minor|major` for automated releases
- **Changelog generation**: Auto-generated with git-cliff from conventional commits
- **Docker images**: Tagged with version and pushed to `ghcr.io/erliona/dating`
- **Production deployment**: Deploy from specific version tags, not `latest`
- **Registry locations**: All images stored in GitHub Container Registry
- **Release automation**: GitHub Actions workflow for CI/CD releases
- **Rollback procedures**: Use `./scripts/release.sh rollback <version>` for emergency rollback

# ==== DEPLOYMENT & OPERATIONS ====

## Pre-Deployment Checklist
- Check .gitignore before committing (ensure no secrets, build artifacts, or temporary files)
- Verify all environment variables are documented in .env.example
- Ensure all new dependencies are added to requirements*.txt
- Test that services build and start correctly with `docker compose up --build`
- Verify that health checks pass for all modified services
- **Migration Safety**: Run CI migration validation script
- **Migration Chain**: Verify `alembic check` passes before deployment

## Post-Deployment Verification
- After deployment always check container status: `docker compose ps`
- Check health status of all services: should be `healthy`, not `starting` or `unhealthy`
- Check logs of each modified service: `docker compose logs <service> --tail=20`
- Check `/health` and `/metrics` endpoints via curl for each service
- For critical changes use `--no-cache` when rebuilding
- **Migration Verification**: Run deployment smoke check script
- **Critical Endpoints**: Test auth, admin, and API gateway endpoints

## Container Status
- Container status: `docker compose ps` - all should be `healthy`
- Prometheus alerts: `./scripts/check_alerts.sh` - check firing alerts
- Health endpoints: `./scripts/health_check.sh` - all services respond
- Service logs: `docker compose logs --tail=20 service | grep -E 'ERROR|WARN'`
- Database state: `SELECT version_num FROM alembic_version;`
- Critical endpoints: test via curl (auth, profile, admin login)
- Monitoring targets: `curl http://localhost:9090/api/v1/targets | jq`

## Rollback Procedures
- Update README/changelog for all significant changes
- Document breaking changes in API or database schema
- Have rollback plan for each deployment
- Test rollback procedures in staging environment
- Never deploy on Friday evening without emergency plan

# ==== TROUBLESHOOTING & DIAGNOSTICS ====

## Systematic Diagnostic Approach

### Phase 1: Services Status
- Container status: `docker compose ps -a` - all should be `healthy` or `running`
- Health checks: `docker compose logs service --tail=20 | grep -E 'health|healthy'`
- Startup logs: `docker compose logs service --tail=50 | grep -E 'Starting|Started|Running'`
- Resource usage: `docker stats --no-stream` - check CPU/memory usage

### Phase 2: Database State
- Migration status: `SELECT version_num FROM alembic_version;`
- Table existence: `SELECT tablename FROM pg_tables WHERE schemaname='public' ORDER BY tablename;`
- Connection test: `docker compose exec -T db psql -U dating -d dating -c '\l'`
- Migration files: `ls -la migrations/versions/ | grep -E '\.py$'` - should NOT have .bak files

### Phase 3: Network & Routing
- DNS resolution: `docker compose exec service wget -qO- http://target:port/health`
- Traefik routes: `curl http://localhost:8091/api/http/routers | jq '.[] | select(.name | contains("service-name"))'`
- Traefik services: `curl http://localhost:8091/api/http/services | jq '.[] | select(.name | contains("service-name"))'`
- API Gateway logs: `docker compose logs api-gateway --tail=20 | grep -E 'routing|404|500'`

### Phase 4: Configuration
- Environment variables: `docker compose exec service env | grep VARIABLE`
- Container labels: `docker inspect container-name | jq '.[0].Config.Labels' | grep traefik`
- File existence: `docker compose exec service ls -la /path/to/config`
- Config validation: `docker compose exec service python -c "import config; print('OK')"`

### Phase 5: Monitoring
- Prometheus targets: `curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | select(.health != "up")'`
- Prometheus alerts: `curl http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.state == "firing")'`
- Grafana dashboards: check that there's no "No data" in critical dashboards
- Metrics endpoints: `curl http://localhost:port/metrics | head -20`

### Phase 6: Application Logs
- Error logs: `docker compose logs service --tail=50 | grep -E 'ERROR|CRITICAL|Failed'`
- Warning logs: `docker compose logs service --tail=50 | grep -E 'WARN|Warning'`
- Startup issues: `docker compose logs service | grep -E 'Starting|Failed to start|Exception'`
- Request logs: `docker compose logs service --tail=20 | grep -E 'GET|POST|PUT|DELETE'`

## Common Problem Patterns

### Pattern 1: "Migrations not applying"
**Symptoms:**
- Missing tables in DB
- Alembic version not updating
- Services can't find tables

**Diagnosis:**
- Check: .bak files in migrations/versions/
- Check: current alembic_version in DB
- Check: migration file revision IDs

**Solution:**
- Restore .bak files to .py
- Fix revision IDs to full filenames
- Update down_revision references
- Recreate alembic_version table if needed

### Pattern 2: "Service not starting"
**Symptoms:**
- Container exits immediately
- Health checks failing
- Missing dependencies

**Diagnosis:**
- Check startup logs: `docker compose logs service`
- Check health endpoint: `curl http://localhost:port/health`
- Check dependencies: `docker compose exec service pip list`

**Solution:**
- Fix missing dependencies
- Update requirements.txt
- Rebuild container: `docker compose build service`

### Pattern 3: "Network connectivity issues"
**Symptoms:**
- Services can't reach each other
- DNS resolution failures
- Timeout errors

**Diagnosis:**
- Check network membership: `docker network inspect network-name`
- Test connectivity: `docker compose exec service wget -qO- http://target:port/health`
- Check service discovery: `curl http://localhost:8091/api/http/services`

**Solution:**
- Add service to correct network
- Fix DNS configuration
- Update service URLs

# ==== OBSERVABILITY ====

## Logging Standards
- Structured logs must include service name, request path, correlation/request ID when available
- Expose Prometheus metrics via middleware; names like `service_operation_total`, `request_duration_seconds`
- Provide `/health` and `/ready` endpoints per service
- Logging only via project utilities in core; no `print`

## Metrics Patterns
- Expose Prometheus metrics via middleware; names like `service_operation_total`, `request_duration_seconds`
- Provide `/health` and `/ready` endpoints per service
- Monitor resource usage: CPU, memory, disk space
- Check health checks: all services should respond to `/health`
- Use retries and timeouts for inter-service calls
- Check database connections: connection pool, query performance
- Monitor logs for memory leaks or performance degradation

## Tracing Guidelines
- Use correlation IDs for request tracing
- Include service name in all log entries
- Track request flow across services
- Monitor performance metrics

# ==== EXAMPLE PATTERNS ====

## aiohttp Route Skeleton
```py
from aiohttp import web
from .schemas import MatchRequest, MatchResponse
from .service import make_match

async def post_match(request: web.Request) -> web.Response:
    body = await request.json()
    req = MatchRequest.model_validate(body)
    result = await make_match(req, request.app['db'])
    return web.json_response(MatchResponse.model_validate(result).model_dump())
```

## Cursor-Specific Guidance
- When generating code, match existing folders/imports; never create new top-level dirs without instruction
- When adding a new endpoint/handler, generate **all** of:
  1) route/handler (aiohttp),
  2) service-layer function,
  3) repository call (SQLAlchemy),
  4) schema/DTO,
  5) tests,
  6) logging + metrics,
  7) docs snippet
- When touching DB models, also create an Alembic migration stub and a covering test
- Prefer incremental edits to existing files; preserve maintainers' comments and structure

## Safe Defaults & Guardrails
- Never hardcode ports, URLs, or secrets; read from env/config
- Avoid adding dependencies unless necessary; justify additions in PR description
- For exploratory chats, do **not** modify files unless explicitly asked (describe steps instead)

## PR & Docs Conventions
- Commits: `<type>(scope): summary` (e.g., `feat(discovery): add mutual likes`)
- PRs must include context, changes, testing notes, rollout/backout plan
- Update README/TECH_STACK/ROADMAP when adding notable features/services
