# Comprehensive Naming Conventions

## Overview
Unified naming standards for all project components to ensure consistency and avoid confusion.

## Migration Naming

### File Naming Pattern
```
{sequence_number}_{descriptive_name}.py
```
**Examples:**
- `001_create_profile_tables.py`
- `002_create_discovery_tables.py`
- `007_create_chat_tables.py`
- `010_add_user_preferences_activity.py`

### Revision ID Standards
- **Format**: Use full filename as revision ID
- **Example**: `revision: str = "007_create_chat_tables"`
- **Never use**: Short IDs like `"007"` or `"abc123def456"`
- **Always update**: `down_revision` to full filename of previous migration

### Migration Naming Rules
- Use descriptive names that explain the migration purpose
- Use snake_case for file names
- Include action verb (create, add, modify, remove, fix)
- Include target entity (tables, columns, indexes, constraints)
- Use sequence numbers for ordering

## API Route Naming

### Route Pattern
```
/api/v1/{resource}/{action}
```
**Examples:**
- `/api/v1/auth/login`
- `/api/v1/profiles/{user_id}`
- `/api/v1/discovery/swipe`
- `/api/v1/chat/messages`

### Route Naming Rules
- Use nouns for resources (auth, profiles, discovery, chat)
- Use verbs only for RPC-like actions (swipe, match, report)
- Use kebab-case for multi-word resources
- Use plural forms for collections (profiles, messages)
- Use singular forms for individual resources (profile, message)

### Admin Route Pattern
```
/admin/{section}/{action}
```
**Examples:**
- `/admin/auth/login` (public)
- `/admin/api/stats` (protected)
- `/admin/api/users` (protected)

## Docker Service Naming

### Service Naming Pattern
```
{service-type}-{purpose}
```
**Examples:**
- `api-gateway`
- `admin-service`
- `telegram-bot`
- `auth-service`
- `profile-service`

### Service Naming Rules
- Use kebab-case for all service names
- Use descriptive names that indicate purpose
- Use consistent suffixes (-service, -bot, -gateway)
- Avoid abbreviations unless commonly understood
- Keep names concise but clear

### Container Naming
- **Auto-generated**: Use Docker Compose auto-generated names
- **Format**: `{project-name}-{service-name}-{instance}`
- **Example**: `dating-microservices-api-gateway-1`
- **Never rely on**: Container names for configuration

## Docker Network Naming

### Network Naming Pattern
```
{environment}-{purpose}
```
**Examples:**
- `default` (application services)
- `monitoring` (monitoring services)
- `production` (production-specific services)

### Network Naming Rules
- Use simple, descriptive names
- Use lowercase with hyphens for multi-word names
- Use consistent naming across environments
- Avoid technical implementation details in names

## Environment Variables

### Variable Naming Pattern
```
{COMPONENT}_{PURPOSE}_{SPECIFIER}
```
**Examples:**
- `BOT_TOKEN`
- `JWT_SECRET`
- `POSTGRES_PASSWORD`
- `ADMIN_PASSWORD`
- `AUTH_SERVICE_PORT`

### Environment Variable Rules
- Use SCREAMING_SNAKE_CASE
- Use descriptive names that indicate purpose
- Use consistent prefixes for related variables
- Use standard suffixes for common types:
  - `_URL` for service URLs
  - `_PORT` for port numbers
  - `_PASSWORD` for passwords
  - `_SECRET` for secrets
  - `_TOKEN` for tokens

### Service URL Pattern
```
{SERVICE_NAME}_SERVICE_URL
```
**Examples:**
- `AUTH_SERVICE_URL`
- `PROFILE_SERVICE_URL`
- `DISCOVERY_SERVICE_URL`

## Database Naming

### Table Naming Pattern
```
{entity_name}
```
**Examples:**
- `users`
- `profiles`
- `photos`
- `interactions`
- `matches`

### Table Naming Rules
- Use snake_case for all table names
- Use plural forms for entity tables
- Use descriptive names that indicate content
- Avoid abbreviations unless commonly understood
- Use consistent naming across related tables

### Column Naming Pattern
```
{attribute_name}
```
**Examples:**
- `user_id`
- `created_at`
- `updated_at`
- `is_verified`
- `profile_completion`

### Column Naming Rules
- Use snake_case for all column names
- Use descriptive names that indicate purpose
- Use consistent suffixes for common types:
  - `_id` for foreign keys
  - `_at` for timestamps
  - `is_` for boolean flags
  - `_count` for counters
  - `_url` for URLs

## File and Directory Naming

### Python Module Naming
```
{module_name}.py
```
**Examples:**
- `main.py`
- `config.py`
- `repository.py`
- `validation.py`

### Python Module Naming Rules
- Use snake_case for all module names
- Use descriptive names that indicate purpose
- Use consistent naming across similar modules
- Avoid abbreviations unless commonly understood

### Directory Naming Pattern
```
{directory_name}/
```
**Examples:**
- `bot/`
- `core/`
- `services/`
- `webapp/`
- `monitoring/`

### Directory Naming Rules
- Use lowercase with hyphens for multi-word names
- Use descriptive names that indicate purpose
- Use consistent naming across similar directories
- Avoid abbreviations unless commonly understood

## Configuration File Naming

### Configuration File Pattern
```
{service_name}.{config_type}
```
**Examples:**
- `nginx.conf`
- `prometheus.yml`
- `docker-compose.yml`
- `alembic.ini`

### Configuration File Naming Rules
- Use descriptive names that indicate purpose
- Use standard extensions for file types
- Use consistent naming across similar files
- Avoid abbreviations unless commonly understood

## Traefik Label Naming

### Label Naming Pattern
```
traefik.{component}.{attribute}
```
**Examples:**
- `traefik.http.routers.webapp.rule`
- `traefik.http.routers.webapp.entrypoints`
- `traefik.http.routers.webapp.priority`
- `traefik.http.services.webapp.loadbalancer.server.port`

### Traefik Label Naming Rules
- Use kebab-case for all label names
- Use descriptive names that indicate purpose
- Use consistent naming across similar labels
- Follow Traefik's standard label format

## Monitoring and Metrics Naming

### Metric Naming Pattern
```
{service}_{operation}_{type}
```
**Examples:**
- `service_operation_total`
- `request_duration_seconds`
- `database_connections_active`
- `cache_hits_total`

### Metric Naming Rules
- Use snake_case for all metric names
- Use descriptive names that indicate purpose
- Use consistent suffixes for common types:
  - `_total` for counters
  - `_seconds` for durations
  - `_active` for active items
  - `_hits` for cache hits
  - `_misses` for cache misses

## Log Naming

### Log Naming Pattern
```
{service_name}_{log_type}.log
```
**Examples:**
- `api-gateway_access.log`
- `admin-service_error.log`
- `telegram-bot_debug.log`

### Log Naming Rules
- Use kebab-case for all log names
- Use descriptive names that indicate purpose
- Use consistent naming across similar logs
- Include service name for identification

## Summary

### Key Principles
1. **Consistency**: Use the same naming pattern across similar components
2. **Descriptiveness**: Names should clearly indicate purpose and content
3. **Simplicity**: Avoid unnecessary complexity and abbreviations
4. **Standards**: Follow established conventions for each technology
5. **Clarity**: Names should be self-explanatory to new team members

### Technology-Specific Standards
- **Python**: snake_case for modules, functions, variables
- **JavaScript**: camelCase for variables, kebab-case for files
- **Docker**: kebab-case for services, networks, containers
- **Database**: snake_case for tables, columns, indexes
- **API**: kebab-case for routes, camelCase for JSON properties
- **Environment**: SCREAMING_SNAKE_CASE for variables

### Validation Checklist
- [ ] All names follow established patterns
- [ ] No abbreviations unless commonly understood
- [ ] Names are descriptive and self-explanatory
- [ ] Consistent naming across similar components
- [ ] No conflicts with existing naming conventions
- [ ] Names are appropriate for the technology stack
