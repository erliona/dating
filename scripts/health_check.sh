#!/bin/bash

# Health Check Script for Dating App Services
# This script checks the health of all services and reports status

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
API_GATEWAY_URL="http://localhost:8080"
SERVICES=(
    "api-gateway:8080"
    "auth-service:8081"
    "profile-service:8082"
    "discovery-service:8083"
    "media-service:8084"
    "chat-service:8085"
    "admin-service:8086"
    "notification-service:8087"
    "data-service:8088"
)

# Database connection
DB_HOST="localhost"
DB_PORT="5432"
DB_NAME="dating"
DB_USER="dating"

log_info() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

check_service() {
    local service_name=$1
    local port=$2
    local url="http://localhost:${port}/health"
    
    if curl -s -f "$url" > /dev/null 2>&1; then
        log_info "$service_name is healthy (port $port)"
        return 0
    else
        log_error "$service_name is unhealthy (port $port)"
        return 1
    fi
}

check_database() {
    log_info "Checking database connectivity..."
    
    if docker compose exec -T db psql -U "$DB_USER" -d "$DB_NAME" -c "SELECT 1;" > /dev/null 2>&1; then
        log_info "Database connection successful"
        
        # Check migration status
        version=$(docker compose exec -T db psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT version_num FROM alembic_version;" 2>/dev/null | tr -d ' \n')
        if [ -n "$version" ]; then
            log_info "Database migration version: $version"
        else
            log_warn "Could not determine migration version"
        fi
        
        # Check table counts
        user_count=$(docker compose exec -T db psql -U "$DB_USER" -d "$DB_NAME" -t -c "SELECT COUNT(*) FROM users;" 2>/dev/null | tr -d ' \n')
        if [ -n "$user_count" ]; then
            log_info "Users in database: $user_count"
        fi
        
        return 0
    else
        log_error "Database connection failed"
        return 1
    fi
}

check_telegram_bot() {
    log_info "Checking Telegram bot status..."
    
    # Check if bot container is running
    if docker compose ps telegram-bot | grep -q "Up"; then
        log_info "Telegram bot container is running"
        
        # Check bot logs for successful authentication
        if docker compose logs telegram-bot --tail=50 | grep -q "Bot authenticated successfully"; then
            log_info "Telegram bot is authenticated"
        else
            log_warn "Telegram bot authentication status unclear"
        fi
        
        return 0
    else
        log_error "Telegram bot container is not running"
        return 1
    fi
}

check_monitoring() {
    log_info "Checking monitoring services..."
    
    monitoring_services=("prometheus:9090" "grafana:3000" "loki:3100")
    all_healthy=true
    
    for service in "${monitoring_services[@]}"; do
        name=$(echo $service | cut -d: -f1)
        port=$(echo $service | cut -d: -f2)
        
        if curl -s -f "http://localhost:${port}" > /dev/null 2>&1; then
            log_info "$name is accessible (port $port)"
        else
            log_warn "$name is not accessible (port $port)"
            all_healthy=false
        fi
    done
    
    if [ "$all_healthy" = true ]; then
        return 0
    else
        return 1
    fi
}

check_api_gateway_routes() {
    log_info "Checking API Gateway routes..."
    
    routes=(
        "/health"
        "/v1/auth/health"
        "/v1/profiles/health"
        "/v1/discovery/health"
        "/v1/media/health"
        "/v1/chat/health"
        "/v1/admin/health"
    )
    
    all_healthy=true
    
    for route in "${routes[@]}"; do
        if curl -s -f "${API_GATEWAY_URL}${route}" > /dev/null 2>&1; then
            log_info "Route $route is accessible"
        else
            log_warn "Route $route is not accessible"
            all_healthy=false
        fi
    done
    
    if [ "$all_healthy" = true ]; then
        return 0
    else
        return 1
    fi
}

# Main execution
echo "========================================"
echo "  Dating App Health Check"
echo "========================================"
echo ""

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    log_error "docker-compose.yml not found. Please run from the project root directory."
    exit 1
fi

# Check if Docker Compose is running
if ! docker compose ps > /dev/null 2>&1; then
    log_error "Docker Compose is not running. Please start services first."
    exit 1
fi

# Initialize counters
total_checks=0
failed_checks=0

# Check individual services
log_info "Checking individual services..."
for service in "${SERVICES[@]}"; do
    name=$(echo $service | cut -d: -f1)
    port=$(echo $service | cut -d: -f2)
    
    total_checks=$((total_checks + 1))
    if ! check_service "$name" "$port"; then
        failed_checks=$((failed_checks + 1))
    fi
done

# Check database
total_checks=$((total_checks + 1))
if ! check_database; then
    failed_checks=$((failed_checks + 1))
fi

# Check Telegram bot
total_checks=$((total_checks + 1))
if ! check_telegram_bot; then
    failed_checks=$((failed_checks + 1))
fi

# Check monitoring
total_checks=$((total_checks + 1))
if ! check_monitoring; then
    failed_checks=$((failed_checks + 1))
fi

# Check API Gateway routes
total_checks=$((total_checks + 1))
if ! check_api_gateway_routes; then
    failed_checks=$((failed_checks + 1))
fi

# Summary
echo ""
echo "========================================"
echo "  Health Check Summary"
echo "========================================"

if [ $failed_checks -eq 0 ]; then
    log_info "All checks passed! ($total_checks/$total_checks)"
    echo ""
    log_info "System is healthy and ready for use."
    exit 0
else
    log_error "Some checks failed! ($failed_checks/$total_checks failed)"
    echo ""
    log_warn "Please review the failed checks above."
    exit 1
fi
