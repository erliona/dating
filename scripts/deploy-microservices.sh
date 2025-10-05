#!/bin/bash
# Deployment script for microservices architecture

set -euo pipefail

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo "======================================"
echo "Dating App - Microservices Deployment"
echo "======================================"
echo ""

# Check for required environment variables
echo "1. Checking environment variables..."
REQUIRED_VARS=("BOT_TOKEN" "JWT_SECRET" "POSTGRES_PASSWORD")
MISSING_VARS=()

echo "Note: POSTGRES_PASSWORD must be set to a static value."
echo "Do not use auto-generated passwords to avoid breaking database connections."

for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var:-}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    echo -e "${RED}✗ Missing required environment variables:${NC}"
    printf '  - %s\n' "${MISSING_VARS[@]}"
    echo ""
    echo "Please set these variables in your .env file:"
    echo "  cp .env.example .env"
    echo "  nano .env"
    exit 1
fi

echo -e "${GREEN}✓ All required environment variables are set${NC}"
echo ""

# Check Docker installation
echo "2. Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    echo -e "${RED}✗ Docker is not installed${NC}"
    echo "Install Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! docker compose version &> /dev/null; then
    echo -e "${RED}✗ Docker Compose is not installed${NC}"
    echo "Install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

echo -e "${GREEN}✓ Docker and Docker Compose are installed${NC}"
echo ""

# Build services
echo "3. Building microservices..."
docker compose build

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ All services built successfully${NC}"
else
    echo -e "${RED}✗ Build failed${NC}"
    exit 1
fi
echo ""

# Start services
echo "4. Starting microservices..."
docker compose up -d

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✓ All services started${NC}"
else
    echo -e "${RED}✗ Failed to start services${NC}"
    exit 1
fi
echo ""

# Wait for services to be healthy
echo "5. Waiting for services to be healthy..."
sleep 10

SERVICES=("db" "auth-service" "profile-service" "discovery-service" "media-service" "chat-service" "api-gateway" "telegram-bot")
ALL_HEALTHY=true

for service in "${SERVICES[@]}"; do
    STATUS=$(docker compose ps --format json | jq -r "select(.Service == \"$service\") | .Health" 2>/dev/null || echo "unknown")
    
    if [ "$STATUS" == "healthy" ] || [ "$STATUS" == "unknown" ]; then
        echo -e "  ${GREEN}✓${NC} $service"
    else
        echo -e "  ${RED}✗${NC} $service (status: $STATUS)"
        ALL_HEALTHY=false
    fi
done

echo ""

if [ "$ALL_HEALTHY" = false ]; then
    echo -e "${YELLOW}⚠ Some services are not healthy yet. Check logs:${NC}"
    echo "  docker compose logs"
fi

# Display service URLs
echo "======================================"
echo "Deployment Complete!"
echo "======================================"
echo ""
echo "Service URLs:"
echo "  API Gateway:   http://localhost:8080"
echo "  Auth Service:  http://localhost:8081"
echo "  Profile:       http://localhost:8082"
echo "  Discovery:     http://localhost:8083"
echo "  Media:         http://localhost:8084"
echo "  Chat:          http://localhost:8085"
echo ""
echo "Health checks:"
echo "  curl http://localhost:8080/health"
echo "  curl http://localhost:8081/health"
echo "  curl http://localhost:8082/health"
echo "  curl http://localhost:8083/health"
echo "  curl http://localhost:8084/health"
echo "  curl http://localhost:8085/health"
echo ""
echo "To view logs:"
echo "  docker compose logs -f"
echo ""
echo "To stop services:"
echo "  docker compose down"
echo ""
