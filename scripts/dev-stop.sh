#!/bin/bash
# Stop local development environment

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🛑 Stopping development environment...${NC}"

# Stop all services
docker compose down

echo -e "${GREEN}✅ Development environment stopped!${NC}"
echo ""
echo "📋 To start again: ./scripts/dev-start.sh"
