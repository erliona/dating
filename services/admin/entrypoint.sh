#!/bin/sh
set -eu

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
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

# Wait for database to be ready
wait_for_database() {
  if [ -z "${DATABASE_URL:-}" ]; then
    log_warn "DATABASE_URL is not set, skipping database check"
    return 0
  fi

  # Parse database connection info from DATABASE_URL using Python for robustness
  DB_HOST=$(python3 -c "import sys; from urllib.parse import urlparse; u = urlparse(sys.argv[1]); print(u.hostname or '')" "$DATABASE_URL")
  DB_PORT=$(python3 -c "import sys; from urllib.parse import urlparse; u = urlparse(sys.argv[1]); print(u.port or '')" "$DATABASE_URL")

  if [ -n "$DB_HOST" ] && [ -n "$DB_PORT" ]; then
    echo "⏳ Waiting for database at ${DB_HOST}:${DB_PORT}..."
    
    MAX_WAIT=30
    WAIT_COUNT=0
    DB_CONNECT_TIMEOUT="${DB_CONNECT_TIMEOUT:-15}"
    while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
      if nc -z -w"$DB_CONNECT_TIMEOUT" "$DB_HOST" "$DB_PORT" 2>/dev/null; then
        log_info "Database is ready"
        return 0
      fi
      WAIT_COUNT=$((WAIT_COUNT + 1))
      echo "   Attempt $WAIT_COUNT/$MAX_WAIT - waiting 2s (timeout: ${DB_CONNECT_TIMEOUT}s)..."
      sleep 2
    done
    
    log_error "Database not ready after ${MAX_WAIT} attempts"
    return 1
  else
    log_warn "Could not parse database connection details"
    return 0
  fi
}

# Run database migrations
run_migrations() {
  if [ "${RUN_DB_MIGRATIONS:-true}" != "true" ]; then
    log_warn "Skipping database migrations (RUN_DB_MIGRATIONS=${RUN_DB_MIGRATIONS})"
    return 0
  fi

  echo "📦 Running database migrations..."
  
  # Wait for database first
  if ! wait_for_database; then
    log_error "Cannot proceed with migrations - database not available"
    exit 1
  fi

  # Run migrations with retry logic
  MAX_RETRIES=5
  RETRY_DELAY=3
  
  for i in $(seq 1 $MAX_RETRIES); do
    if output=$(alembic upgrade head 2>&1); then
      log_info "Database migrations completed successfully"
      return 0
    else
      log_error "Migration failed: $output"
      if [ "$i" -eq "$MAX_RETRIES" ]; then
        log_error "Failed to apply database migrations after $MAX_RETRIES attempts"
        exit 1
      fi
      log_warn "Migration attempt $i/$MAX_RETRIES failed, retrying in ${RETRY_DELAY}s..."
      sleep "$RETRY_DELAY"
    fi
  done
}

# Main execution
echo "========================================"
echo "  Admin Service Startup"
echo "========================================"
echo ""

# Skip migrations - Admin Service now works through Data Service
log_info "Skipping database migrations - Admin Service works through Data Service"

# Create nginx directories and set permissions
log_info "Creating nginx directories..."
mkdir -p /var/lib/nginx/body /var/lib/nginx/fastcgi /var/lib/nginx/proxy /var/lib/nginx/scgi /var/lib/nginx/uwsgi
chmod -R 755 /var/lib/nginx

# Start nginx in background
log_info "Starting nginx for static files..."
nginx -g "daemon on;"

echo ""
echo "========================================"
echo "Starting admin service..."
echo "========================================"
echo ""

# Start the application
exec python -m services.admin.main
