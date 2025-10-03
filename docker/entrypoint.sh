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

# Function to attempt password migration when authentication fails
# This helps handle password changes without requiring database volume reset
attempt_password_migration() {
  if [ -z "${BOT_DATABASE_URL:-}" ]; then
    log_warn "BOT_DATABASE_URL is not set, cannot attempt password migration"
    return 1
  fi
  
  # Parse the database URL
  DB_USER=$(echo "$BOT_DATABASE_URL" | sed -n 's|^.*://\([^:]*\):.*@.*$|\1|p')
  DB_PASSWORD=$(echo "$BOT_DATABASE_URL" | sed -n 's|^.*://[^:]*:\([^@]*\)@.*$|\1|p')
  DB_PORT=$(echo "$BOT_DATABASE_URL" | sed -n 's|^.*:\([0-9]*\)/.*$|\1|p')
  DB_NAME=$(echo "$BOT_DATABASE_URL" | sed -n 's|^.*/\([^/]*\)$|\1|p')
  
  if [ -z "$DB_USER" ] || [ -z "$DB_PASSWORD" ] || [ -z "$DB_HOST" ] || [ -z "$DB_PORT" ] || [ -z "$DB_NAME" ]; then
    log_warn "Could not parse database credentials from BOT_DATABASE_URL"
    return 1
  fi
  
  log_info "Attempting to update database password for user: $DB_USER"
  
  # Try to connect as postgres superuser (available in docker postgres container)
  # and update the user's password
  if command -v psql > /dev/null 2>&1; then
    # Use a temporary .pgpass file for secure password handling
    TMP_PGPASS=$(mktemp)
    # Validate POSTGRES_PASSWORD is set and non-empty
    if [ -z "${POSTGRES_PASSWORD:-}" ]; then
      log_error "POSTGRES_PASSWORD is not set or is empty. Cannot perform password migration."
      rm -f "$TMP_PGPASS"
      return 1
    fi
    # Escape special characters for .pgpass (colon, backslash, newline)
    escape_pgpass() {
      # Escape backslash first, then colon, then newline
      printf '%s' "$1" | sed -e 's/\\/\\\\/g' -e 's/:/\\:/g' -e ':a;N;$!ba;s/\n/\\n/g'
    }
    ESCAPED_POSTGRES_PASSWORD=$(escape_pgpass "$POSTGRES_PASSWORD")
    echo "$DB_HOST:$DB_PORT:$DB_NAME:postgres:$ESCAPED_POSTGRES_PASSWORD" > "$TMP_PGPASS"
    chmod 600 "$TMP_PGPASS"
    if PGPASSFILE="$TMP_PGPASS" psql -h "$DB_HOST" -p "$DB_PORT" -U postgres -d "$DB_NAME" -c "ALTER USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" 2>/dev/null; then
      log_info "Successfully updated database password for user: $DB_USER"
      rm -f "$TMP_PGPASS"
      return 0
    else
      log_warn "Could not update password using postgres superuser"
    fi
    rm -f "$TMP_PGPASS"
  fi
  
  log_warn "Password migration failed - manual intervention may be required"
  return 1
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

# Wait for database to be ready with exponential backoff
wait_for_database() {
  MAX_RETRIES=12
  RETRY_COUNT=0
  WAIT_SECONDS=1
  
  echo "⏳ Waiting for database to be ready..."
  
  while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    if check_database_connection; then
      log_info "Database is ready"
      return 0
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    
    if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
      echo "   Attempt $RETRY_COUNT/$MAX_RETRIES - waiting ${WAIT_SECONDS}s before retry..."
      sleep "$WAIT_SECONDS"
      
      # Exponential backoff: double wait time up to 16 seconds max
      if [ $WAIT_SECONDS -lt 16 ]; then
        WAIT_SECONDS=$((WAIT_SECONDS * 2))
      fi
    fi
  done
  
  log_error "Database not ready after ${MAX_RETRIES} attempts"
  return 1
}

# Run database migrations with retry and password migration support
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
  
  # Retry logic for database migrations with exponential backoff
  MAX_RETRIES=6
  RETRY_COUNT=0
  WAIT_SECONDS=2
  PASSWORD_MIGRATION_ATTEMPTED=false
  
  while [ $RETRY_COUNT -lt $MAX_RETRIES ]; do
    MIGRATION_OUTPUT=$(alembic upgrade head 2>&1)
    MIGRATION_STATUS=$?
    
    if [ $MIGRATION_STATUS -eq 0 ]; then
      log_info "Database migrations completed successfully"
      return 0
    fi
    
    RETRY_COUNT=$((RETRY_COUNT + 1))
    
    # Check if this is an authentication failure
    if echo "$MIGRATION_OUTPUT" | grep -qi "password authentication failed\|authentication failed\|no password supplied"; then
      if [ "$PASSWORD_MIGRATION_ATTEMPTED" = "false" ]; then
        log_warn "Authentication failed - attempting password migration..."
        if attempt_password_migration; then
          PASSWORD_MIGRATION_ATTEMPTED=true
          log_info "Password migration successful, retrying migrations..."
          # Reset retry count to give migrations another chance with new password
          RETRY_COUNT=0
          WAIT_SECONDS=2
          continue
        else
          PASSWORD_MIGRATION_ATTEMPTED=true
          log_warn "Password migration failed"
        fi
      fi
    fi
    
    if [ $RETRY_COUNT -lt $MAX_RETRIES ]; then
      log_warn "Database migration attempt $RETRY_COUNT/$MAX_RETRIES failed, retrying in ${WAIT_SECONDS}s..."
      sleep "$WAIT_SECONDS"
      
      # Exponential backoff: double wait time up to 16 seconds max
      if [ $WAIT_SECONDS -lt 16 ]; then
        WAIT_SECONDS=$((WAIT_SECONDS * 2))
      fi
    else
      log_error "Failed to apply database migrations after $MAX_RETRIES attempts"
      echo ""
      echo "Last error output:"
      echo "$MIGRATION_OUTPUT"
      echo ""
      echo "Common causes:"
      echo "  1. Password mismatch: The database was initialized with a different password"
      echo "     than what's currently in POSTGRES_PASSWORD environment variable."
      echo "  2. Database not ready: The database server may still be initializing."
      echo "  3. Network issue: Cannot reach the database server."
      echo ""
      echo "Automatic password migration was attempted but failed."
      echo ""
      echo "To fix password issues manually:"
      echo "  - Option 1: Update password in PostgreSQL:"
      echo "              docker compose exec db psql -U postgres -d dating -c \"ALTER USER dating WITH PASSWORD 'new_password';\""
      echo "  - Option 2: Reset the database (⚠️ WILL DELETE ALL DATA!):"
      echo "              First backup: docker compose exec db pg_dump -U dating dating > backup.sql"
      echo "              Then reset: docker compose down -v && docker compose up"
      echo "              Then restore: docker compose exec -T db psql -U dating dating < backup.sql"
      echo ""
      exit 1
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
