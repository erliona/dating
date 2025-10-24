#!/bin/bash
# Production Deployment Script
# Deploys specific version to production environment

set -e

# Configuration
PRODUCTION_SERVER="root@dating.serge.cc"
PRODUCTION_PATH="/root/dating-microservices"
REGISTRY_URL="ghcr.io/erliona/dating"
ENVIRONMENT="production"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

# Error handling
error_exit() {
    log "${RED}ERROR: $1${NC}"
    exit 1
}

# Success message
success() {
    log "${GREEN}✅ $1${NC}"
}

# Warning message
warning() {
    log "${YELLOW}⚠️  $1${NC}"
}

# Check prerequisites
check_prerequisites() {
    log "🔍 Checking prerequisites..."
    
    # Check if version is provided
    if [ -z "$1" ]; then
        error_exit "Version required. Usage: $0 <version>"
    fi
    
    local version=$1
    
    # Validate version format
    if [[ ! $version =~ ^v[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
        error_exit "Invalid version format: $version. Use format: v1.2.3"
    fi
    
    # Check if version exists locally
    if ! git describe --tags --exact-match "$version" &>/dev/null; then
        error_exit "Version $version not found locally. Pull latest changes first."
    fi
    
    success "Prerequisites check passed"
}

# Backup current deployment
backup_current_deployment() {
    log "💾 Creating backup of current deployment..."
    
    # Create backup directory
    local backup_dir="/root/backups/$(date +%Y%m%d_%H%M%S)"
    
    ssh "$PRODUCTION_SERVER" "mkdir -p $backup_dir"
    
    # Backup current docker-compose.yml
    ssh "$PRODUCTION_SERVER" "cp $PRODUCTION_PATH/docker-compose.yml $backup_dir/"
    
    # Backup current .env
    ssh "$PRODUCTION_SERVER" "cp $PRODUCTION_PATH/.env $backup_dir/"
    
    # Backup current images list
    ssh "$PRODUCTION_SERVER" "docker images | grep $REGISTRY_URL > $backup_dir/images.txt"
    
    success "Backup created at $backup_dir"
}

# Update code on production server
update_production_code() {
    local version=$1
    
    log "📥 Updating code on production server..."
    
    # Pull latest changes
    ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && git fetch origin"
    ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && git checkout $version"
    
    success "Code updated to version $version"
}

# Update docker-compose.yml with version tags
update_docker_compose() {
    local version=$1
    
    log "🐳 Updating docker-compose.yml with version tags..."
    
    # Create temporary docker-compose file with version tags
    cat > /tmp/docker-compose.prod.yml << EOF
# Production docker-compose.yml with version tags
version: '3.8'

services:
  api-gateway:
    image: $REGISTRY_URL/api-gateway:$version
    # ... rest of configuration

  auth-service:
    image: $REGISTRY_URL/auth-service:$version
    # ... rest of configuration

  profile-service:
    image: $REGISTRY_URL/profile-service:$version
    # ... rest of configuration

  discovery-service:
    image: $REGISTRY_URL/discovery-service:$version
    # ... rest of configuration

  media-service:
    image: $REGISTRY_URL/media-service:$version
    # ... rest of configuration

  chat-service:
    image: $REGISTRY_URL/chat-service:$version
    # ... rest of configuration

  admin-service:
    image: $REGISTRY_URL/admin-service:$version
    # ... rest of configuration

  telegram-bot:
    image: $REGISTRY_URL/telegram-bot:$version
    # ... rest of configuration

  webapp:
    image: $REGISTRY_URL/webapp:$version
    # ... rest of configuration
EOF
    
    # Copy to production server
    scp /tmp/docker-compose.prod.yml "$PRODUCTION_SERVER:$PRODUCTION_PATH/docker-compose.prod.yml"
    
    success "Docker-compose updated with version $version"
}

# Pull new images
pull_images() {
    local version=$1
    
    log "📦 Pulling new images..."
    
    # List of services
    services=(
        "api-gateway"
        "auth-service"
        "profile-service"
        "discovery-service"
        "media-service"
        "chat-service"
        "admin-service"
        "telegram-bot"
        "webapp"
    )
    
    for service in "${services[@]}"; do
        log "Pulling $service:$version..."
        ssh "$PRODUCTION_SERVER" "docker pull $REGISTRY_URL/$service:$version"
        success "Pulled $service:$version"
    done
}

# Deploy services
deploy_services() {
    local version=$1
    
    log "🚀 Deploying services..."
    
    # Stop current services
    ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && docker compose down"
    
    # Start new services
    ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && docker compose -f docker-compose.prod.yml up -d"
    
    success "Services deployed"
}

# Wait for services to be healthy
wait_for_services() {
    log "⏳ Waiting for services to be healthy..."
    
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        log "Health check attempt $attempt/$max_attempts..."
        
        # Check if all services are healthy
        local unhealthy_count=$(ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && docker compose ps | grep -v 'healthy' | grep -v 'NAME' | wc -l")
        
        if [ "$unhealthy_count" -eq 0 ]; then
            success "All services are healthy"
            return 0
        fi
        
        log "Found $unhealthy_count unhealthy services, waiting..."
        sleep 10
        attempt=$((attempt + 1))
    done
    
    error_exit "Services failed to become healthy after $max_attempts attempts"
}

# Run health checks
run_health_checks() {
    log "🏥 Running health checks..."
    
    # Check API Gateway
    if curl -f -s "https://dating.serge.cc/health" > /dev/null; then
        success "API Gateway health check passed"
    else
        error_exit "API Gateway health check failed"
    fi
    
    # Check Auth Service
    if curl -f -s "https://dating.serge.cc/api/v1/auth/health" > /dev/null; then
        success "Auth Service health check passed"
    else
        error_exit "Auth Service health check failed"
    fi
    
    # Check Admin Service
    local admin_response=$(curl -s -o /dev/null -w "%{http_code}" -X POST "https://dating.serge.cc/admin/auth/login" \
        -H "Content-Type: application/json" \
        -d '{"username":"test","password":"test"}')
    
    if [ "$admin_response" = "401" ] || [ "$admin_response" = "403" ]; then
        success "Admin Service health check passed"
    else
        error_exit "Admin Service health check failed (HTTP $admin_response)"
    fi
    
    success "All health checks passed"
}

# Run smoke tests
run_smoke_tests() {
    log "🧪 Running smoke tests..."
    
    # Test critical endpoints
    local endpoints=(
        "https://dating.serge.cc/health"
        "https://dating.serge.cc/api/v1/auth/health"
        "https://dating.serge.cc/admin/"
    )
    
    for endpoint in "${endpoints[@]}"; do
        if curl -f -s "$endpoint" > /dev/null; then
            success "Smoke test passed: $endpoint"
        else
            error_exit "Smoke test failed: $endpoint"
        fi
    done
    
    success "All smoke tests passed"
}

# Monitor deployment
monitor_deployment() {
    log "📊 Monitoring deployment for 5 minutes..."
    
    local start_time=$(date +%s)
    local end_time=$((start_time + 300)) # 5 minutes
    
    while [ $(date +%s) -lt $end_time ]; do
        # Check service health
        local unhealthy_count=$(ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && docker compose ps | grep -v 'healthy' | grep -v 'NAME' | wc -l")
        
        if [ "$unhealthy_count" -gt 0 ]; then
            warning "Found $unhealthy_count unhealthy services"
        fi
        
        # Check for errors in logs
        local error_count=$(ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && docker compose logs --tail=50 | grep -i error | wc -l")
        
        if [ "$error_count" -gt 10 ]; then
            warning "High error count detected: $error_count"
        fi
        
        sleep 30
    done
    
    success "Deployment monitoring completed"
}

# Rollback deployment
rollback_deployment() {
    log "🔄 Rolling back deployment..."
    
    # Stop current services
    ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && docker compose down"
    
    # Restore previous docker-compose.yml
    ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && cp docker-compose.yml.backup docker-compose.yml"
    
    # Start previous services
    ssh "$PRODUCTION_SERVER" "cd $PRODUCTION_PATH && docker compose up -d"
    
    success "Deployment rolled back"
}

# Main deployment function
deploy_production() {
    local version=$1
    
    log "🚀 Starting production deployment of $version"
    
    check_prerequisites "$version"
    backup_current_deployment
    update_production_code "$version"
    update_docker_compose "$version"
    pull_images "$version"
    deploy_services "$version"
    wait_for_services
    run_health_checks
    run_smoke_tests
    monitor_deployment
    
    success "Production deployment of $version completed successfully!"
    log "📋 Deployment summary:"
    log "  Version: $version"
    log "  Environment: $ENVIRONMENT"
    log "  Server: $PRODUCTION_SERVER"
    log "  Registry: $REGISTRY_URL"
    log "  Health: https://dating.serge.cc/health"
    log "  Admin: https://dating.serge.cc/admin/"
}

# Main script logic
main() {
    case "${1:-help}" in
        "deploy")
            deploy_production "$2"
            ;;
        "rollback")
            rollback_deployment
            ;;
        "health")
            run_health_checks
            ;;
        "smoke")
            run_smoke_tests
            ;;
        "help"|*)
            echo "Usage: $0 {deploy|rollback|health|smoke|help} [version]"
            echo ""
            echo "Commands:"
            echo "  deploy <version>  - Deploy specific version to production"
            echo "  rollback          - Rollback to previous deployment"
            echo "  health            - Run health checks"
            echo "  smoke             - Run smoke tests"
            echo "  help              - Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 deploy v1.2.0"
            echo "  $0 rollback"
            echo "  $0 health"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
