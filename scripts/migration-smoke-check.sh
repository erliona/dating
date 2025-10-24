#!/bin/bash
# Migration Smoke Check Script
# Verifies migration chain integrity and critical endpoints after deployment

set -e

echo "🔍 Starting migration smoke check..."

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo "❌ ERROR: docker-compose.yml not found. Run from project root."
    exit 1
fi

# Check if database is running
if ! docker compose ps db | grep -q "healthy"; then
    echo "❌ ERROR: Database is not running or not healthy"
    echo "Start database first: docker compose up -d db"
    exit 1
fi

echo "📊 Checking current migration state..."
docker compose exec -T db alembic current

echo "🔍 Checking migration chain integrity..."
docker compose exec -T db alembic check || {
    echo "❌ Migration chain is broken"
    exit 1
}

echo "⬆️ Applying migrations..."
docker compose exec -T db alembic upgrade head || {
    echo "❌ Migration application failed"
    exit 1
}

echo "🏥 Testing critical endpoints..."

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 5

# Test API Gateway health
if curl -f -s http://localhost:8080/health > /dev/null; then
    echo "✅ API Gateway health check passed"
else
    echo "❌ API Gateway health check failed"
    exit 1
fi

# Test Auth service health
if curl -f -s http://localhost:8080/api/v1/auth/health > /dev/null; then
    echo "✅ Auth service health check passed"
else
    echo "❌ Auth service health check failed"
    exit 1
fi

# Test Admin service (login endpoint should exist, even if auth fails)
if curl -f -s -X POST http://localhost:8080/admin/auth/login \
    -H "Content-Type: application/json" \
    -d '{"username":"test","password":"test"}' > /dev/null 2>&1; then
    echo "✅ Admin service endpoint accessible"
else
    # Check if it's a 401/403 (expected) vs 404 (service not found)
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8080/admin/auth/login \
        -H "Content-Type: application/json" \
        -d '{"username":"test","password":"test"}')
    
    if [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "403" ]; then
        echo "✅ Admin service endpoint accessible (authentication failed as expected)"
    else
        echo "❌ Admin service endpoint not accessible (HTTP $HTTP_CODE)"
        exit 1
    fi
fi

echo "✅ Migration smoke check completed successfully"
echo "🎉 All critical endpoints are responding"
