#!/bin/bash
# View development logs
# Usage: ./scripts/dev-logs.sh [service_name]

set -e

# Colors for output
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}📋 Viewing development logs...${NC}"

if [ $# -eq 0 ]; then
    # Show logs for all services
    echo "Showing logs for all services (Ctrl+C to exit):"
    docker compose logs -f
else
    # Show logs for specific service
    echo "Showing logs for service: $1 (Ctrl+C to exit):"
    docker compose logs -f "$1"
fi
