#!/bin/bash
# Migration Safety Validation Script
# Ensures only one service has RUN_DB_MIGRATIONS=true

set -e

echo "🔍 Validating migration safety..."

# Check that only one service has RUN_DB_MIGRATIONS=true
MIGRATION_SERVICES=$(grep -r "RUN_DB_MIGRATIONS.*true" docker-compose.yml | wc -l)

if [ "$MIGRATION_SERVICES" -eq 0 ]; then
    echo "⚠️  WARNING: No services have RUN_DB_MIGRATIONS=true"
    echo "At least one service should run migrations"
    exit 1
elif [ "$MIGRATION_SERVICES" -gt 1 ]; then
    echo "❌ ERROR: Multiple services have RUN_DB_MIGRATIONS=true"
    echo "Found $MIGRATION_SERVICES services with migrations enabled:"
    grep -r "RUN_DB_MIGRATIONS.*true" docker-compose.yml
    echo ""
    echo "Only one service should run migrations to avoid conflicts"
    echo "Recommended: Set RUN_DB_MIGRATIONS=true only for telegram-bot service"
    exit 1
else
    echo "✅ Migration safety check passed"
    echo "Found $MIGRATION_SERVICES service with migrations enabled"
    grep -r "RUN_DB_MIGRATIONS.*true" docker-compose.yml
fi
