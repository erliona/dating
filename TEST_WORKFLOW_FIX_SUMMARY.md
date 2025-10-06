# Test Workflow Fix Summary

## Issue
Tests in GitHub Actions were hanging because:
1. PostgreSQL service container started but tests ran immediately without waiting for database readiness
2. Database migrations were never applied, causing tests to hang on connection attempts to non-existent tables
3. Missing environment variables caused tests to fail or attempt external network calls

Reference: [GitHub Actions Run #18271536114](https://github.com/erliona/dating/actions/runs/18271536114/job/52014734369)

## Root Causes
1. **No explicit database wait**: While GitHub Actions service containers have health checks, the workflow didn't wait for the database to be fully ready before proceeding
2. **Missing migrations**: Test database schema was never created - `alembic upgrade head` was never run in CI
3. **Incomplete environment**: Tests required `BOT_DATABASE_URL` and `API_GATEWAY_URL` environment variables that weren't set

## Changes Made

### 1. Fixed GitHub Actions Workflows
Updated both `.github/workflows/test.yml` and `.github/workflows/pr-validation.yml`:

#### Added PostgreSQL Readiness Wait
```yaml
- name: Wait for PostgreSQL
  run: |
    echo "Waiting for PostgreSQL to be ready..."
    for i in {1..30}; do
      if pg_isready -h localhost -p 5432 -U dating > /dev/null 2>&1; then
        echo "PostgreSQL is ready!"
        break
      fi
      echo "Attempt $i/30 - waiting 2s..."
      sleep 2
    done
    pg_isready -h localhost -p 5432 -U dating || (echo "PostgreSQL failed to become ready" && exit 1)
```

#### Added Database Migrations
```yaml
- name: Apply database migrations
  env:
    BOT_DATABASE_URL: postgresql+asyncpg://dating:test_password@localhost:5432/dating_test
  run: |
    echo "Applying database migrations..."
    alembic upgrade head
    echo "Migrations applied successfully"
```

#### Updated Environment Variables
```yaml
- name: Run tests
  env:
    DATABASE_URL: postgresql+asyncpg://dating:test_password@localhost:5432/dating_test
    BOT_DATABASE_URL: postgresql+asyncpg://dating:test_password@localhost:5432/dating_test  # Added
    BOT_TOKEN: test:token
    JWT_SECRET: test-secret-key-for-testing-32chars
    API_GATEWAY_URL: http://localhost:8080  # Added
```

### 2. Fixed Migration Chain
Fixed broken migration dependency in `migrations/versions/003_create_admin_table.py`:

**Before:**
```python
down_revision: Union[str, None] = "002"
```

**After:**
```python
down_revision: Union[str, None] = "002_create_discovery_tables"
```

This fixes the `KeyError: '002'` that occurred when running migrations.

### 3. Updated Documentation
Updated `docs/CI_CD_GUIDE.md` to document:
- The new explicit database readiness wait step
- The migration application step
- Updated environment variable configuration
- Troubleshooting tips for database-related test failures

## Testing
Verified the fix by:
1. Starting a local PostgreSQL container
2. Running `alembic upgrade head` - confirmed migrations apply successfully
3. Running tests with all required environment variables - confirmed tests run without hanging

## Impact
- ✅ Tests no longer hang waiting for database connections
- ✅ Database schema is properly created before tests run
- ✅ Tests have all required environment variables
- ✅ Migration chain is fixed and can be run successfully
- ✅ Both `test.yml` and `pr-validation.yml` workflows are fixed

## Files Changed
1. `.github/workflows/test.yml` - Added wait, migrations, and env vars
2. `.github/workflows/pr-validation.yml` - Added wait, migrations, and env vars  
3. `migrations/versions/003_create_admin_table.py` - Fixed down_revision reference
4. `docs/CI_CD_GUIDE.md` - Updated documentation

## Next Steps
The workflows are now fixed and ready for testing in CI. When the next commit is pushed, GitHub Actions will:
1. Start PostgreSQL service container
2. Wait explicitly for it to be ready
3. Apply database migrations to create schema
4. Run tests with proper environment variables

This should resolve the hanging test issues completely.
