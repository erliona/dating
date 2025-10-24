#!/bin/bash
# Docker Security Validation Script
# Validates Docker security standards across all services

set -e

# Configuration
DOCKERFILE_PATTERN="**/Dockerfile"
COMPOSE_FILE="docker-compose.yml"
REQUIRED_HEALTH_ENDPOINT="/health"
REQUIRED_RESTART_POLICY="unless-stopped"

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

# Check if we're in the right directory
check_directory() {
    if [ ! -f "$COMPOSE_FILE" ]; then
        error_exit "docker-compose.yml not found. Run from project root."
    fi
    success "Running in correct directory"
}

# Validate Dockerfile security
validate_dockerfile_security() {
    log "🔍 Validating Dockerfile security..."
    
    local violations=0
    
    # Find all Dockerfiles
    local dockerfiles=$(find . -name "Dockerfile" -type f)
    
    if [ -z "$dockerfiles" ]; then
        error_exit "No Dockerfiles found"
    fi
    
    for dockerfile in $dockerfiles; do
        log "Checking $dockerfile..."
        
        # Check for pinned base image
        if ! grep -q "FROM.*@sha256:" "$dockerfile" && ! grep -q "FROM.*:[0-9]\+\.[0-9]\+\.[0-9]\+" "$dockerfile"; then
            warning "Unpinned base image in $dockerfile"
            violations=$((violations + 1))
        fi
        
        # Check for non-root user
        if ! grep -q "USER " "$dockerfile"; then
            error_exit "No USER directive found in $dockerfile"
            violations=$((violations + 1))
        fi
        
        # Check for root user (should not exist)
        if grep -q "USER root" "$dockerfile"; then
            warning "USER root found in $dockerfile (should be avoided)"
            violations=$((violations + 1))
        fi
        
        # Check for multi-stage build
        if ! grep -q "FROM.*AS" "$dockerfile"; then
            warning "No multi-stage build detected in $dockerfile"
        fi
        
        # Check for security practices
        if grep -q "apt-get update" "$dockerfile" && ! grep -q "rm -rf /var/lib/apt/lists/\*" "$dockerfile"; then
            warning "apt-get cache not cleaned in $dockerfile"
            violations=$((violations + 1))
        fi
        
        success "Dockerfile $dockerfile checked"
    done
    
    if [ $violations -eq 0 ]; then
        success "All Dockerfiles passed security validation"
    else
        warning "Found $violations security violations in Dockerfiles"
    fi
}

# Validate docker-compose.yml security
validate_compose_security() {
    log "🔍 Validating docker-compose.yml security..."
    
    local violations=0
    
    # Check if docker-compose.yml exists
    if [ ! -f "$COMPOSE_FILE" ]; then
        error_exit "docker-compose.yml not found"
    fi
    
    # Extract service names
    local services=$(grep -E "^  [a-zA-Z0-9_-]+:" "$COMPOSE_FILE" | sed 's/://g' | sed 's/^  //' | grep -v "version")
    
    if [ -z "$services" ]; then
        error_exit "No services found in docker-compose.yml"
    fi
    
    for service in $services; do
        log "Checking service: $service"
        
        # Check for security options
        if ! grep -A 20 "^  $service:" "$COMPOSE_FILE" | grep -q "security_opt:"; then
            warning "No security_opt found for service $service"
            violations=$((violations + 1))
        fi
        
        # Check for capability dropping
        if ! grep -A 20 "^  $service:" "$COMPOSE_FILE" | grep -q "cap_drop:"; then
            warning "No cap_drop found for service $service"
            violations=$((violations + 1))
        fi
        
        # Check for health check
        if ! grep -A 20 "^  $service:" "$COMPOSE_FILE" | grep -q "healthcheck:"; then
            error_exit "No healthcheck found for service $service"
            violations=$((violations + 1))
        fi
        
        # Check for restart policy
        if ! grep -A 20 "^  $service:" "$COMPOSE_FILE" | grep -q "restart:"; then
            error_exit "No restart policy found for service $service"
            violations=$((violations + 1))
        fi
        
        # Check for read-only filesystem
        if ! grep -A 20 "^  $service:" "$COMPOSE_FILE" | grep -q "read_only:"; then
            warning "No read_only filesystem for service $service"
            violations=$((violations + 1))
        fi
        
        # Check for resource limits
        if ! grep -A 20 "^  $service:" "$COMPOSE_FILE" | grep -q "deploy:"; then
            warning "No resource limits found for service $service"
        fi
        
        success "Service $service checked"
    done
    
    if [ $violations -eq 0 ]; then
        success "All services passed security validation"
    else
        warning "Found $violations security violations in docker-compose.yml"
    fi
}

# Validate health check endpoints
validate_health_endpoints() {
    log "🔍 Validating health check endpoints..."
    
    local violations=0
    
    # Check if all services have /health endpoint
    local services=$(grep -E "^  [a-zA-Z0-9_-]+:" "$COMPOSE_FILE" | sed 's/://g' | sed 's/^  //' | grep -v "version")
    
    for service in $services; do
        # Check if health check uses /health endpoint
        if grep -A 10 "^  $service:" "$COMPOSE_FILE" | grep -A 5 "healthcheck:" | grep -q "/health"; then
            success "Service $service has /health endpoint"
        else
            warning "Service $service may not have /health endpoint"
            violations=$((violations + 1))
        fi
    done
    
    if [ $violations -eq 0 ]; then
        success "All health check endpoints validated"
    else
        warning "Found $violations health check issues"
    fi
}

# Validate restart policies
validate_restart_policies() {
    log "🔍 Validating restart policies..."
    
    local violations=0
    
    local services=$(grep -E "^  [a-zA-Z0-9_-]+:" "$COMPOSE_FILE" | sed 's/://g' | sed 's/^  //' | grep -v "version")
    
    for service in $services; do
        # Check if restart policy is unless-stopped
        if grep -A 10 "^  $service:" "$COMPOSE_FILE" | grep -q "restart: unless-stopped"; then
            success "Service $service has correct restart policy"
        else
            warning "Service $service does not have 'unless-stopped' restart policy"
            violations=$((violations + 1))
        fi
    done
    
    if [ $violations -eq 0 ]; then
        success "All restart policies validated"
    else
        warning "Found $violations restart policy issues"
    fi
}

# Validate security options
validate_security_options() {
    log "🔍 Validating security options..."
    
    local violations=0
    
    local services=$(grep -E "^  [a-zA-Z0-9_-]+:" "$COMPOSE_FILE" | sed 's/://g' | sed 's/^  //' | grep -v "version")
    
    for service in $services; do
        # Check for no-new-privileges
        if grep -A 10 "^  $service:" "$COMPOSE_FILE" | grep -A 5 "security_opt:" | grep -q "no-new-privileges:true"; then
            success "Service $service has no-new-privileges"
        else
            warning "Service $service missing no-new-privileges security option"
            violations=$((violations + 1))
        fi
        
        # Check for capability dropping
        if grep -A 10 "^  $service:" "$COMPOSE_FILE" | grep -A 5 "cap_drop:" | grep -q "ALL"; then
            success "Service $service drops all capabilities"
        else
            warning "Service $service does not drop all capabilities"
            violations=$((violations + 1))
        fi
    done
    
    if [ $violations -eq 0 ]; then
        success "All security options validated"
    else
        warning "Found $violations security option issues"
    fi
}

# Check for exposed ports
validate_port_exposure() {
    log "🔍 Validating port exposure..."
    
    local violations=0
    
    # Check for unnecessary port exposure
    local exposed_ports=$(grep -A 10 "ports:" "$COMPOSE_FILE" | grep -E "^\s*-.*:" | wc -l)
    
    if [ "$exposed_ports" -gt 0 ]; then
        warning "Found $exposed_ports exposed ports. Review if all are necessary."
        violations=$((violations + 1))
    else
        success "No unnecessary port exposure found"
    fi
    
    if [ $violations -eq 0 ]; then
        success "Port exposure validated"
    else
        warning "Found $violations port exposure issues"
    fi
}

# Generate security report
generate_security_report() {
    log "📊 Generating Docker security report..."
    
    local report_file="/tmp/docker-security-report-$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "Docker Security Report - $(date)"
        echo "=================================="
        echo ""
        
        echo "Dockerfiles found:"
        find . -name "Dockerfile" -type f
        echo ""
        
        echo "Services in docker-compose.yml:"
        grep -E "^  [a-zA-Z0-9_-]+:" "$COMPOSE_FILE" | sed 's/://g' | sed 's/^  //' | grep -v "version"
        echo ""
        
        echo "Security options check:"
        grep -A 5 "security_opt:" "$COMPOSE_FILE" || echo "No security_opt found"
        echo ""
        
        echo "Capability dropping check:"
        grep -A 5 "cap_drop:" "$COMPOSE_FILE" || echo "No cap_drop found"
        echo ""
        
        echo "Health checks:"
        grep -A 10 "healthcheck:" "$COMPOSE_FILE" || echo "No healthcheck found"
        echo ""
        
        echo "Restart policies:"
        grep -A 2 "restart:" "$COMPOSE_FILE" || echo "No restart policies found"
        echo ""
        
    } > "$report_file"
    
    log "📄 Security report generated: $report_file"
}

# Main validation function
validate_docker_security() {
    log "🚀 Starting Docker security validation..."
    
    check_directory
    validate_dockerfile_security
    validate_compose_security
    validate_health_endpoints
    validate_restart_policies
    validate_security_options
    validate_port_exposure
    generate_security_report
    
    log "✅ Docker security validation completed"
}

# Check specific service
check_service() {
    local service_name=$1
    
    if [ -z "$service_name" ]; then
        error_exit "Service name required"
    fi
    
    log "🔍 Checking specific service: $service_name"
    
    # Check if service exists
    if ! grep -q "^  $service_name:" "$COMPOSE_FILE"; then
        error_exit "Service $service_name not found in docker-compose.yml"
    fi
    
    # Check service configuration
    log "Service configuration for $service_name:"
    grep -A 20 "^  $service_name:" "$COMPOSE_FILE"
    
    success "Service $service_name checked"
}

# Main script logic
main() {
    case "${1:-validate}" in
        "validate")
            validate_docker_security
            ;;
        "check")
            check_service "$2"
            ;;
        "report")
            generate_security_report
            ;;
        "help"|*)
            echo "Usage: $0 {validate|check|report|help} [service_name]"
            echo ""
            echo "Commands:"
            echo "  validate           - Run full Docker security validation"
            echo "  check <service>    - Check specific service security"
            echo "  report             - Generate security report"
            echo "  help               - Show this help message"
            echo ""
            echo "Examples:"
            echo "  $0 validate"
            echo "  $0 check api-gateway"
            echo "  $0 report"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
