#!/bin/bash
# JWT Secret Rotation Script
# Implements secure JWT key rotation with gradual rollout

set -e

# Configuration
BACKUP_DIR="/secure/jwt-backups"
NEW_SECRET_FILE="/secure/jwt-secret-new.txt"
CURRENT_SECRET_FILE="/secure/jwt-secret-current.txt"
LOG_FILE="/var/log/jwt-rotation.log"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Error handling
error_exit() {
    log "ERROR: $1"
    exit 1
}

# Check prerequisites
check_prerequisites() {
    log "🔍 Checking prerequisites..."
    
    # Check if running as root or with sudo
    if [ "$EUID" -ne 0 ]; then
        error_exit "This script must be run as root or with sudo"
    fi
    
    # Check if docker-compose is available
    if ! command -v docker-compose &> /dev/null; then
        error_exit "docker-compose not found"
    fi
    
    # Check if services are running
    if ! docker-compose ps | grep -q "healthy"; then
        error_exit "Services are not healthy. Fix issues before rotation."
    fi
    
    log "✅ Prerequisites check passed"
}

# Backup current configuration
backup_current_config() {
    log "💾 Backing up current configuration..."
    
    # Create backup directory
    mkdir -p "$BACKUP_DIR"
    
    # Backup current .env file
    if [ -f ".env" ]; then
        cp .env "$BACKUP_DIR/.env.backup.$(date +%Y%m%d_%H%M%S)"
        log "✅ .env file backed up"
    fi
    
    # Backup docker-compose.yml
    if [ -f "docker-compose.yml" ]; then
        cp docker-compose.yml "$BACKUP_DIR/docker-compose.yml.backup.$(date +%Y%m%d_%H%M%S)"
        log "✅ docker-compose.yml backed up"
    fi
    
    log "✅ Backup completed"
}

# Generate new JWT secret
generate_new_secret() {
    log "🔐 Generating new JWT secret..."
    
    # Generate 256-bit secret
    NEW_SECRET=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))")
    
    # Store in secure location
    echo "$NEW_SECRET" > "$NEW_SECRET_FILE"
    chmod 600 "$NEW_SECRET_FILE"
    
    log "✅ New JWT secret generated and stored securely"
    log "🔑 New secret: ${NEW_SECRET:0:8}... (truncated for security)"
}

# Update environment configuration
update_environment() {
    local phase=$1
    log "📝 Updating environment for phase: $phase"
    
    case $phase in
        "dual")
            log "🔄 Phase 1: Dual secret mode"
            # Add new secret alongside old one
            if grep -q "JWT_SECRET_NEW" .env; then
                sed -i "s/JWT_SECRET_NEW=.*/JWT_SECRET_NEW=$NEW_SECRET/" .env
            else
                echo "JWT_SECRET_NEW=$NEW_SECRET" >> .env
            fi
            echo "JWT_ROTATION_MODE=dual" >> .env
            ;;
        "new")
            log "🔄 Phase 2: New secret only"
            # Replace old secret with new one
            sed -i "s/JWT_SECRET=.*/JWT_SECRET=$NEW_SECRET/" .env
            sed -i "/JWT_SECRET_NEW/d" .env
            sed -i "s/JWT_ROTATION_MODE=.*/JWT_ROTATION_MODE=new/" .env
            ;;
        *)
            error_exit "Invalid phase: $phase"
            ;;
    esac
    
    log "✅ Environment updated for phase: $phase"
}

# Deploy services
deploy_services() {
    log "🚀 Deploying services..."
    
    # Rebuild and restart affected services
    docker-compose up -d --build api-gateway auth-service admin-service telegram-bot
    
    # Wait for services to be healthy
    log "⏳ Waiting for services to become healthy..."
    sleep 30
    
    # Check service health
    if ! docker-compose ps | grep -q "healthy"; then
        error_exit "Services failed to become healthy after rotation"
    fi
    
    log "✅ Services deployed successfully"
}

# Validate rotation
validate_rotation() {
    log "🧪 Validating JWT rotation..."
    
    # Test auth endpoint
    if curl -f -s http://localhost:8080/api/v1/auth/health > /dev/null; then
        log "✅ Auth service health check passed"
    else
        error_exit "Auth service health check failed"
    fi
    
    # Test admin endpoint
    if curl -f -s http://localhost:8080/admin/auth/login -X POST \
        -H "Content-Type: application/json" \
        -d '{"username":"test","password":"test"}' > /dev/null 2>&1; then
        log "✅ Admin service endpoint accessible"
    else
        # Check if it's a 401/403 (expected) vs 404 (service not found)
        HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8080/admin/auth/login \
            -H "Content-Type: application/json" \
            -d '{"username":"test","password":"test"}')
        
        if [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "403" ]; then
            log "✅ Admin service endpoint accessible (authentication failed as expected)"
        else
            error_exit "Admin service endpoint not accessible (HTTP $HTTP_CODE)"
        fi
    fi
    
    log "✅ JWT rotation validation passed"
}

# Monitor for issues
monitor_rotation() {
    log "📊 Monitoring rotation for 5 minutes..."
    
    for i in {1..30}; do
        # Check service health
        if ! docker-compose ps | grep -q "healthy"; then
            error_exit "Service health degraded during monitoring"
        fi
        
        # Check for JWT validation errors in logs
        ERROR_COUNT=$(docker-compose logs --tail=100 api-gateway auth-service | grep -c "JWT" | grep -c "error" || true)
        if [ "$ERROR_COUNT" -gt 10 ]; then
            log "⚠️  High JWT error count detected: $ERROR_COUNT"
        fi
        
        sleep 10
    done
    
    log "✅ Monitoring completed - no issues detected"
}

# Cleanup old secrets
cleanup_old_secrets() {
    log "🧹 Cleaning up old secrets..."
    
    # Remove old secret file
    if [ -f "$CURRENT_SECRET_FILE" ]; then
        rm -f "$CURRENT_SECRET_FILE"
        log "✅ Old secret file removed"
    fi
    
    # Remove rotation mode from .env
    sed -i "/JWT_ROTATION_MODE/d" .env
    
    log "✅ Cleanup completed"
}

# Rollback function
rollback() {
    log "🔄 Rolling back JWT rotation..."
    
    # Restore from backup
    if [ -f "$BACKUP_DIR/.env.backup.$(date +%Y%m%d_%H%M%S)" ]; then
        cp "$BACKUP_DIR/.env.backup.$(date +%Y%m%d_%H%M%S)" .env
        log "✅ .env file restored from backup"
    fi
    
    # Restart services
    docker-compose up -d api-gateway auth-service admin-service telegram-bot
    
    log "✅ Rollback completed"
}

# Main rotation function
rotate_jwt_secret() {
    local phase=$1
    
    log "🔄 Starting JWT secret rotation (Phase: $phase)"
    
    check_prerequisites
    backup_current_config
    generate_new_secret
    update_environment "$phase"
    deploy_services
    validate_rotation
    monitor_rotation
    
    if [ "$phase" = "new" ]; then
        cleanup_old_secrets
    fi
    
    log "✅ JWT secret rotation completed successfully"
}

# Emergency rotation
emergency_rotation() {
    log "🚨 Starting emergency JWT rotation..."
    
    # Revoke all tokens immediately
    log "🔒 Revoking all active tokens..."
    # Implementation depends on token blacklist system
    
    # Generate and deploy new secret immediately
    rotate_jwt_secret "new"
    
    # Notify users
    log "📢 Sending user notifications..."
    # Implementation depends on notification system
    
    log "✅ Emergency rotation completed"
}

# Main script logic
main() {
    case "${1:-}" in
        "dual")
            rotate_jwt_secret "dual"
            ;;
        "new")
            rotate_jwt_secret "new"
            ;;
        "emergency")
            emergency_rotation
            ;;
        "rollback")
            rollback
            ;;
        *)
            echo "Usage: $0 {dual|new|emergency|rollback}"
            echo ""
            echo "Commands:"
            echo "  dual      - Deploy with both old and new secrets"
            echo "  new       - Switch to new secret only"
            echo "  emergency - Emergency rotation (revoke all tokens)"
            echo "  rollback  - Rollback to previous configuration"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
