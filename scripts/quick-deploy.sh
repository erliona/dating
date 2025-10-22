#!/bin/bash

# Quick Deploy Script
# For deploying a single service with force rebuild

set -e

if [ $# -eq 0 ]; then
    echo "Usage: $0 <service-name>"
    echo "Example: $0 webapp"
    echo "Example: $0 api-gateway"
    exit 1
fi

SERVICE=$1

echo "🚀 Quick deploying $SERVICE..."

# Stop, remove, rebuild and start
docker compose stop $SERVICE
docker compose rm -f $SERVICE
docker compose build --no-cache $SERVICE
docker compose up -d $SERVICE

echo "✅ $SERVICE deployed successfully!"

# Show status
docker compose ps $SERVICE

# Show recent logs
echo ""
echo "Recent logs:"
docker compose logs --tail=10 $SERVICE
