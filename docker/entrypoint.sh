#!/bin/sh
set -eu

if [ "${RUN_DB_MIGRATIONS:-true}" = "true" ]; then
  echo "Applying database migrations..."
  
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
