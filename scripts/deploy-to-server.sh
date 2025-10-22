#!/bin/bash

# Deploy to Server Script
# This script copies files to server and runs force deploy

set -e

SERVER="root@dating.serge.cc"
SERVER_PATH="/opt/dating-microservices"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Get list of services to deploy (can be passed as arguments)
SERVICES=${@:-"webapp api-gateway profile-service"}

print_status "Deploying to server: $SERVICES"

# Step 1: Copy deploy scripts to server
print_status "Copying deploy scripts to server..."
scp scripts/force-deploy.sh $SERVER:$SERVER_PATH/
scp scripts/quick-deploy.sh $SERVER:$SERVER_PATH/
ssh $SERVER "chmod +x $SERVER_PATH/force-deploy.sh $SERVER_PATH/quick-deploy.sh"

# Step 2: Copy configuration files
print_status "Copying configuration files..."
scp docker-compose.yml $SERVER:$SERVER_PATH/
scp requirements.txt $SERVER:$SERVER_PATH/

# Step 3: Copy changed files based on services
for service in $SERVICES; do
    case $service in
        "webapp")
            print_status "Copying webapp files..."
            scp -r webapp/* $SERVER:$SERVER_PATH/webapp/
            ;;
        "api-gateway")
            print_status "Copying API Gateway files..."
            scp -r gateway $SERVER:$SERVER_PATH/
            ;;
        "profile-service")
            print_status "Copying Profile Service files..."
            scp -r services/profile $SERVER:$SERVER_PATH/services/
            ;;
        "data-service")
            print_status "Copying Data Service files..."
            scp -r services/data $SERVER:$SERVER_PATH/services/
            ;;
        "auth-service")
            print_status "Copying Auth Service files..."
            scp -r services/auth $SERVER:$SERVER_PATH/services/
            ;;
        "admin-service")
            print_status "Copying Admin Service files..."
            scp -r services/admin $SERVER:$SERVER_PATH/services/
            ;;
        "discovery-service")
            print_status "Copying Discovery Service files..."
            scp -r services/discovery $SERVER:$SERVER_PATH/services/
            ;;
        *)
            print_error "Unknown service: $service"
            exit 1
            ;;
    esac
done

# Step 3: Run force deploy on server
print_status "Running force deploy on server..."
ssh $SERVER "cd $SERVER_PATH && ./force-deploy.sh $SERVICES"

print_success "Deploy completed successfully!"
