#!/bin/sh
set -eu

# Colors for output (optional, works in most terminals)
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
  echo "${GREEN}✓${NC} $1"
}

log_warn() {
  echo "${YELLOW}⚠️${NC} $1"
}

log_error() {
  echo "${RED}✗${NC} $1"
}

# Function to check database connectivity with timeout
check_database_connection() {
  if [ -z "${BOT_DATABASE_URL:-}" ]; then
    log_warn "BOT_DATABASE_URL is not set"
    return 1
  fi
  
  # Parse the database URL
  DB_USER=$(echo "$BOT_DATABASE_URL" | sed -n 's|^.*://\([^:]*\):.*@.*$|\1|p')
  DB_HOST=$(echo "$BOT_DATABASE_URL" | sed -n 's|^.*@\([^:]*\):.*$|\1|p')
  DB_PORT=$(echo "$BOT_DATABASE_URL" | sed -n 's|^.*:\([0-9]*\)/.*$|\1|p')
  DB_NAME=$(echo "$BOT_DATABASE_URL" | sed -n 's|^.*/\([^/]*\)$|\1|p')
  
  if [ -n "$DB_USER" ] && [ -n "$DB_HOST" ] && [ -n "$DB_PORT" ] && [ -n "$DB_NAME" ]; then
    echo "🔍 Testing database connection to ${DB_HOST}:${DB_PORT}..."
    echo "   Database: $DB_NAME, User: $DB_USER"
    
    # Check if the database server is reachable with timeout
    if command -v nc > /dev/null 2>&1; then
      if nc -z -w5 "$DB_HOST" "$DB_PORT" 2>/dev/null; then
        log_info "Database server is reachable at ${DB_HOST}:${DB_PORT}"
        return 0
      else
        log_warn "Cannot reach database server at ${DB_HOST}:${DB_PORT}"
        return 1
      fi
    else
      log_warn "netcat not available, skipping connectivity check"
    fi
  else
    log_warn "Could not parse database connection details from BOT_DATABASE_URL"
  fi
  
  return 0
}

# Wait for database to be ready
wait_for_database() {
  MAX_WAIT=30
  WAIT_COUNT=0
  
  echo "⏳ Waiting for database to be ready..."
  
  while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
    if check_database_connection; then
      log_info "Database is ready"
      return 0
    fi
    WAIT_COUNT=$((WAIT_COUNT + 1))
    echo "   Attempt $WAIT_COUNT/$MAX_WAIT - waiting 2s..."
    sleep 2
  done
  
  log_error "Database not ready after ${MAX_WAIT} attempts"
  return 1
}

# Run database migrations
run_migrations() {
  if [ "${RUN_DB_MIGRATIONS:-true}" != "true" ]; then
    echo "Skipping database migrations (RUN_DB_MIGRATIONS=${RUN_DB_MIGRATIONS})."
    return 0
  fi
  
  echo "Applying database migrations..."
  
  # Wait for database first
  if ! wait_for_database; then
    log_error "Cannot proceed with migrations - database not available"
    exit 1
  fi
  
  # Retry logic for database migrations
  MAX_RETRIES=5
  RETRY_DELAY=3
  
  for i in $(seq 1 $MAX_RETRIES); do
    if alembic upgrade head 2>&1; then
      log_info "Database migrations completed successfully"
      return 0
    else
      if [ "$i" -eq "$MAX_RETRIES" ]; then
        log_error "Failed to apply database migrations after $MAX_RETRIES attempts"
        echo ""
        echo "Common causes:"
        echo "  1. Password mismatch: The database was initialized with a different password"
        echo "     than what's currently in POSTGRES_PASSWORD environment variable."
        echo "  2. Database not ready: The database server may still be initializing."
        echo "  3. Network issue: Cannot reach the database server."
        echo ""
        echo "To fix password issues:"
        echo "  - Option 1: Reset the database (⚠️ WILL DELETE ALL DATA!):"
        echo "              First backup: docker compose exec db pg_dump -U dating dating > backup.sql"
        echo "              Then reset: docker compose down -v && docker compose up"
        echo "              Then restore: docker compose exec -T db psql -U dating dating < backup.sql"
        echo "  - Option 2: Manually change the password in PostgreSQL to match POSTGRES_PASSWORD"
        echo "  - Option 3: Update POSTGRES_PASSWORD to match the password used when the database was initialized"
        echo ""
        exit 1
      fi
      log_warn "Database migration attempt $i/$MAX_RETRIES failed, retrying in ${RETRY_DELAY}s..."
      sleep "$RETRY_DELAY"
    fi
  done
}

# Main execution
echo "========================================"
echo "  Dating Bot Startup"
echo "========================================"
echo ""

# Run migrations
run_migrations

echo ""
echo "========================================"
echo "Starting bot..."
echo "========================================"

# Execute the main application
exec python -m bot.main
