#!/bin/bash
# Production deployment script
# Deploys to production server with monitoring stack

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
PRODUCTION_SERVER="root@dating.serge.cc"
PRODUCTION_PATH="/root/dating-microservices"

echo -e "${BLUE}🚀 Deploying to production...${NC}"

# Check if we're on the right branch
current_branch=$(git branch --show-current)
if [ "$current_branch" != "main" ]; then
    echo -e "${RED}❌ Not on main branch. Current branch: $current_branch${NC}"
    echo "Please switch to main branch before deploying to production"
    exit 1
fi

# Check if there are uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo -e "${RED}❌ Uncommitted changes detected${NC}"
    echo "Please commit or stash your changes before deploying"
    exit 1
fi

# Push to GitHub first
echo -e "${BLUE}📤 Pushing to GitHub...${NC}"
git push origin main

# Deploy to production server
echo -e "${BLUE}🖥️  Deploying to production server...${NC}"
ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && \
  git pull origin main && \
  export ENVIRONMENT=production && \
  docker compose --profile production up --build -d"

# Wait for services to start
echo -e "${BLUE}⏳ Waiting for services to start...${NC}"
sleep 15

# Check production status
echo -e "${BLUE}🔍 Checking production status...${NC}"
ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && docker compose --profile production ps"

echo -e "${GREEN}✅ Production deployment complete!${NC}"
echo ""
echo "🌐 Production services available at:"
echo "   - WebApp: https://dating.serge.cc"
echo "   - Admin Panel: https://dating.serge.cc/admin"
echo "   - Monitoring: https://dating.serge.cc:3001 (Grafana)"
echo ""
echo "📋 Useful commands:"
echo "   - Check status: ssh $PRODUCTION_SERVER 'cd $PRODUCTION_PATH && docker compose --profile production ps'"
echo "   - View logs: ssh $PRODUCTION_SERVER 'cd $PRODUCTION_PATH && docker compose --profile production logs -f'"
echo "   - Restart services: ssh $PRODUCTION_SERVER 'cd $PRODUCTION_PATH && docker compose --profile production restart'"