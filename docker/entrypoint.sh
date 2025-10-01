#!/bin/sh
set -eu

# Function to check database connectivity
check_database_connection() {
  # Extract connection details from BOT_DATABASE_URL
  if [ -z "${BOT_DATABASE_URL:-}" ]; then
    echo "⚠️  BOT_DATABASE_URL is not set"
    return 1
  fi
  
  # Parse the database URL to extract user, host, port, and database name
  # Format: postgresql+asyncpg://user:password@host:port/database
  DB_USER=$(echo "$BOT_DATABASE_URL" | sed -n 's|^.*://\([^:]*\):.*@.*$|\1|p')
  DB_HOST=$(echo "$BOT_DATABASE_URL" | sed -n 's|^.*@\([^:]*\):.*$|\1|p')
  DB_PORT=$(echo "$BOT_DATABASE_URL" | sed -n 's|^.*:\([0-9]*\)/.*$|\1|p')
  DB_NAME=$(echo "$BOT_DATABASE_URL" | sed -n 's|^.*/\([^/]*\)$|\1|p')
  
  if [ -n "$DB_USER" ] && [ -n "$DB_HOST" ] && [ -n "$DB_PORT" ] && [ -n "$DB_NAME" ]; then
    echo "🔍 Testing database connection to ${DB_HOST}:${DB_PORT}..."
    echo "   Database: $DB_NAME, User: $DB_USER"
    
    # Try to connect using psql (we don't have the password here, so we can't test auth)
    # Instead, check if the database server is reachable
    if command -v nc > /dev/null 2>&1; then
      if nc -z "$DB_HOST" "$DB_PORT" 2>/dev/null; then
        echo "✓ Database server is reachable at ${DB_HOST}:${DB_PORT}"
      else
        echo "⚠️  Cannot reach database server at ${DB_HOST}:${DB_PORT}"
        return 1
      fi
    fi
  else
    echo "⚠️  Could not parse database connection details from BOT_DATABASE_URL"
  fi
  
  return 0
}

if [ "${RUN_DB_MIGRATIONS:-true}" = "true" ]; then
  echo "Applying database migrations..."
  
  # Check database connection first
  check_database_connection || true
  
  # Retry logic for database migrations
  MAX_RETRIES=5
  RETRY_DELAY=3
  
  for i in $(seq 1 $MAX_RETRIES); do
    if alembic upgrade head; then
      echo "✓ Database migrations completed successfully"
      break
    else
      if [ "$i" -eq "$MAX_RETRIES" ]; then
        echo "✗ Failed to apply database migrations after $MAX_RETRIES attempts"
        echo ""
        echo "Common causes:"
        echo "  1. Password mismatch: The database was initialized with a different password"
        echo "     than what's currently in POSTGRES_PASSWORD environment variable."
        echo "  2. Database not ready: The database server may still be initializing."
        echo "  3. Network issue: Cannot reach the database server."
        echo ""
        echo "To fix password issues:"
        echo "  - Option 1: Reset the database volume: docker compose down -v && docker compose up"
        echo "  - Option 2: Manually change the password in PostgreSQL to match POSTGRES_PASSWORD"
        echo "  - Option 3: Update POSTGRES_PASSWORD to match the password used when the database was initialized"
        echo ""
        exit 1
      fi
      echo "⚠️  Database migration attempt $i/$MAX_RETRIES failed, retrying in ${RETRY_DELAY}s..."
      sleep "$RETRY_DELAY"
    fi
  done
else
  echo "Skipping database migrations (RUN_DB_MIGRATIONS=${RUN_DB_MIGRATIONS})."
fi

echo "Starting bot..."
exec python -m bot.main
