#!/bin/bash

# Force Deploy Script
# This script ensures that all changes are properly applied by:
# 1. Stopping services
# 2. Removing old containers and images
# 3. Rebuilding without cache
# 4. Starting fresh containers

set -e  # Exit on any error

echo "🚀 Starting force deploy process..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    print_error "docker-compose.yml not found. Please run this script from the project root."
    exit 1
fi

# Get list of services to deploy (can be passed as arguments)
SERVICES=${@:-"webapp api-gateway profile-service auth-service"}

print_status "Deploying services: $SERVICES"

# Step 1: Stop services
print_status "Stopping services..."
docker compose stop $SERVICES

# Step 2: Remove containers
print_status "Removing containers..."
docker compose rm -f $SERVICES

# Step 3: Remove old images (optional, uncomment if needed)
# print_status "Removing old images..."
# docker compose images -q $SERVICES | xargs -r docker rmi -f

# Step 4: Build without cache
print_status "Building services without cache..."
docker compose build --no-cache --pull $SERVICES

# Step 5: Start services
print_status "Starting services..."
docker compose up -d $SERVICES

# Step 6: Wait for services to be healthy
print_status "Waiting for services to be healthy..."
sleep 10

# Step 7: Check status
print_status "Checking service status..."
docker compose ps $SERVICES

# Step 8: Show logs for verification
print_status "Showing recent logs..."
for service in $SERVICES; do
    echo ""
    print_status "=== $service logs ==="
    docker compose logs --tail=5 $service
done

print_success "Force deploy completed!"
print_warning "Please test the services to ensure they're working correctly."
