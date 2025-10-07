# Timezone Fix Migration Guide

## Overview

This guide explains how to apply the timezone fix migrations that convert all timestamp columns from `TIMESTAMP WITHOUT TIME ZONE` to `TIMESTAMPTZ` (timezone-aware timestamps).

## Problem Statement

The admin panel was crashing when querying user statistics because the database columns were `TIMESTAMP WITHOUT TIME ZONE` but the Python code was using timezone-aware datetime objects (`datetime.now(timezone.utc)`). This caused PostgreSQL/asyncpg to throw errors like:

```
can't subtract offset-naive and offset-aware datetimes
```

Queries like `WHERE users.created_at >= $1::TIMESTAMP WITHOUT TIME ZONE` would fail when `$1` was a timezone-aware datetime object.

## Solution

All timestamp columns in all tables have been converted to use `TIMESTAMPTZ` (timezone-aware timestamps) at the database level, and all SQLAlchemy models have been updated to use `DateTime(timezone=True)`.

## Migrations Applied

Three new migrations have been created:

1. **Migration 004** (already exists): `004_fix_admin_timezone.py`
   - Fixes `admins` table: `last_login`, `created_at`, `updated_at`

2. **Migration 005** (new): `005_fix_profile_tables_timezone.py`
   - Fixes `users` table: `created_at`, `updated_at`
   - Fixes `profiles` table: `created_at`, `updated_at`
   - Fixes `photos` table: `created_at`

3. **Migration 006** (new): `006_fix_discovery_tables_timezone.py`
   - Fixes `interactions` table: `created_at`, `updated_at`
   - Fixes `matches` table: `created_at`
   - Fixes `favorites` table: `created_at`

## Models Updated

All models in `bot/db.py` have been updated:

- `User`: `created_at`, `updated_at`
- `Profile`: `created_at`, `updated_at`
- `Photo`: `created_at`
- `Interaction`: `created_at`, `updated_at`
- `Match`: `created_at`
- `Favorite`: `created_at`
- `Admin`: `last_login`, `created_at`, `updated_at` (already fixed)

## How to Apply Migrations

### Using Docker (Recommended for Production)

The migrations will be applied automatically when the services start up. The deployment process should:

1. Pull the latest code
2. Rebuild the Docker images
3. Run the migrations via Alembic on startup

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart services
docker compose down
docker compose build
docker compose up -d
```

The migrations will run automatically as part of the startup process.

### Manual Migration (if needed)

If you need to run migrations manually:

```bash
# Connect to the database container or host where Alembic is available
docker compose exec telegram-bot alembic upgrade head

# Or if running locally:
alembic upgrade head
```

### Verifying Migration Status

Check the current migration version:

```bash
docker compose exec telegram-bot alembic current

# Expected output should show: 006 (or later)
```

Check which migrations are pending:

```bash
docker compose exec telegram-bot alembic history
```

## Database Changes

All timestamp columns are converted using:

```sql
ALTER TABLE {table_name}
ALTER COLUMN {column_name} TYPE TIMESTAMPTZ 
USING {column_name} AT TIME ZONE 'UTC';
```

This conversion:
- Interprets existing timestamp data as UTC
- Converts the column type to store timezone information
- Is **safe** and **reversible** (downgrade migrations are included)
- Does **not** modify the actual timestamp values, just adds timezone awareness

## Testing

Comprehensive tests have been added in `tests/unit/test_all_models_timezone.py`:

- 15 tests covering all 7 database tables
- Tests verify that models accept timezone-aware datetime objects
- Tests verify that database columns have `timezone=True`

Run tests with:

```bash
pytest tests/unit/test_all_models_timezone.py -v
pytest tests/unit/test_admin_model_timezone.py -v
```

## Rollback (if needed)

If you need to rollback the migrations:

```bash
# Rollback to migration 003 (before all timezone fixes)
alembic downgrade 003

# Or rollback one migration at a time
alembic downgrade -1
```

**Note**: Rollback converts columns back to `TIMESTAMP WITHOUT TIME ZONE`, which may cause the original issue to reappear.

## Impact

- **Zero data loss**: All existing timestamp values are preserved
- **Performance**: No performance impact - `TIMESTAMPTZ` has the same storage size as `TIMESTAMP`
- **Compatibility**: All Python code already uses timezone-aware datetimes, so no code changes needed
- **Admin panel**: Statistics queries will now work correctly
- **Future-proof**: All future timestamp operations will be timezone-aware

## Troubleshooting

### Issue: Migration fails with "column does not exist"

**Solution**: Check that all previous migrations (001, 002, 003, 004) have been applied first.

```bash
alembic current
alembic upgrade head
```

### Issue: Still seeing timezone errors after migration

**Possible causes**:
1. Old containers still running - restart all services
2. Code not updated - pull latest code and rebuild
3. Database not migrated - check `alembic current`

**Solution**:
```bash
docker compose down
git pull
docker compose build --no-cache
docker compose up -d
```

### Issue: Want to verify database column types

```bash
docker compose exec db psql -U dating -d dating -c "\d+ users"
docker compose exec db psql -U dating -d dating -c "\d+ profiles"
```

Look for `timestamp with time zone` (TIMESTAMPTZ) in the output.

## References

- Original issue: "timezones issue" - Admin panel crashing on statistics queries
- Migrations: `migrations/versions/004_fix_admin_timezone.py`, `005_fix_profile_tables_timezone.py`, `006_fix_discovery_tables_timezone.py`
- Models: `bot/db.py`
- Tests: `tests/unit/test_all_models_timezone.py`, `tests/unit/test_admin_model_timezone.py`
- CHANGELOG: `CHANGELOG.md` - See "Timezone Issue Across All Tables" entry
