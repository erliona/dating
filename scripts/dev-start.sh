#!/bin/bash
# Start local development environment
# This script starts all services without monitoring stack

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting development environment...${NC}"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️  .env file not found. Creating from .env.example..."
    cp .env.example .env
    echo "📝 Please edit .env file with your local configuration"
    echo "   Required: BOT_TOKEN, JWT_SECRET, POSTGRES_PASSWORD"
    exit 1
fi

# Set development environment
export ENVIRONMENT=development

# Start services (without monitoring profile)
echo -e "${BLUE}📦 Starting application services...${NC}"
docker compose up -d

# Wait for services to be ready
echo -e "${BLUE}⏳ Waiting for services to start...${NC}"
sleep 10

# Check service status
echo -e "${BLUE}🔍 Checking service status...${NC}"
docker compose ps

echo -e "${GREEN}✅ Development environment started!${NC}"
echo ""
echo "🌐 Services available at:"
echo "   - WebApp: http://localhost"
echo "   - API Gateway: http://localhost:8080"
echo "   - Database: localhost:5433 (external access)"
echo ""
echo "📋 Useful commands:"
echo "   - View logs: ./scripts/dev-logs.sh"
echo "   - Stop services: ./scripts/dev-stop.sh"
echo "   - Check status: docker compose ps"
