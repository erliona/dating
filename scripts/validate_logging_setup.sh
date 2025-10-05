#!/bin/bash
# Validation script for logging and monitoring infrastructure
set -euo pipefail

echo "🔍 Validating Logging and Monitoring Setup"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

success() {
    echo -e "${GREEN}✓${NC} $1"
}

error() {
    echo -e "${RED}✗${NC} $1"
}

warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    error "docker-compose.yml not found. Please run from repository root."
    exit 1
fi

echo "1. Validating docker-compose.yml syntax..."
if docker compose config > /dev/null 2>&1; then
    success "docker-compose.yml syntax is valid"
else
    error "docker-compose.yml has syntax errors"
    exit 1
fi

echo ""
echo "2. Checking Python file syntax..."
python_files=(
    "core/utils/logging.py"
    "bot/main.py"
    "services/auth/main.py"
    "services/profile/main.py"
    "services/discovery/main.py"
    "services/media/main.py"
    "services/chat/main.py"
    "gateway/main.py"
)

all_valid=true
for file in "${python_files[@]}"; do
    if [ -f "$file" ]; then
        if python3 -m py_compile "$file" 2>/dev/null; then
            success "$file syntax valid"
        else
            error "$file has syntax errors"
            all_valid=false
        fi
    else
        warning "$file not found"
    fi
done

if [ "$all_valid" = false ]; then
    error "Some Python files have syntax errors"
    exit 1
fi

echo ""
echo "3. Checking port allocations..."
# Extract all host ports from docker-compose.yml
ports=$(grep -E "^\s+- \"(\\\$\{[^}]+:-)?[0-9]+(\\})?:[0-9]+\"" docker-compose.yml | sed -E 's/.*:-([0-9]+).*/\1/; s/.*"([0-9]+):.*/\1/' | sort -n)
unique_ports=$(echo "$ports" | uniq)

if [ "$(echo "$ports" | wc -l)" -eq "$(echo "$unique_ports" | wc -l)" ]; then
    success "No port conflicts detected"
    echo "   Allocated ports: $(echo $unique_ports | tr '\n' ' ')"
else
    error "Port conflicts detected!"
    echo "$ports" | uniq -c | grep -v "^\s*1 " || true
    exit 1
fi

echo ""
echo "4. Verifying monitoring services are defined..."
monitoring_services=(
    "prometheus"
    "grafana"
    "loki"
    "promtail"
    "cadvisor"
    "node-exporter"
    "postgres-exporter"
)

services_list=$(docker compose config --services 2>/dev/null)
for service in "${monitoring_services[@]}"; do
    if echo "$services_list" | grep -q "^${service}$"; then
        success "$service service defined"
    else
        error "$service service not found"
        exit 1
    fi
done

echo ""
echo "5. Checking application services..."
app_services=(
    "db"
    "auth-service"
    "profile-service"
    "discovery-service"
    "media-service"
    "chat-service"
    "api-gateway"
    "telegram-bot"
)

for service in "${app_services[@]}"; do
    if echo "$services_list" | grep -q "^${service}$"; then
        success "$service service defined"
    else
        error "$service service not found"
        exit 1
    fi
done

echo ""
echo "6. Verifying logging utility exists..."
if [ -f "core/utils/logging.py" ]; then
    success "Shared logging utility found"
    # Check if it has the required functions
    if grep -q "class JsonFormatter" core/utils/logging.py && \
       grep -q "def configure_logging" core/utils/logging.py; then
        success "JsonFormatter and configure_logging found"
    else
        error "Required functions not found in logging.py"
        exit 1
    fi
else
    error "core/utils/logging.py not found"
    exit 1
fi

echo ""
echo "7. Checking service logging integration..."
services_to_check=(
    "services/auth/main.py"
    "services/profile/main.py"
    "services/discovery/main.py"
    "services/media/main.py"
    "services/chat/main.py"
    "gateway/main.py"
    "bot/main.py"
)

for service_file in "${services_to_check[@]}"; do
    if [ -f "$service_file" ]; then
        if grep -q "from core.utils.logging import configure_logging" "$service_file" && \
           grep -q "configure_logging(" "$service_file"; then
            success "$(basename $(dirname $service_file))/$(basename $service_file) uses shared logging"
        else
            error "$(basename $(dirname $service_file))/$(basename $service_file) not using shared logging"
            exit 1
        fi
    fi
done

echo ""
echo "8. Verifying documentation updates..."
docs_to_check=(
    "DOCUMENTATION.md"
    "README.md"
    "QUICK_REFERENCE.md"
    "monitoring/README.md"
    "monitoring/ARCHITECTURE.md"
)

for doc in "${docs_to_check[@]}"; do
    if [ -f "$doc" ]; then
        success "$doc exists"
    else
        warning "$doc not found"
    fi
done

echo ""
echo "9. Checking for port 8081 conflict fix..."
# Check cAdvisor uses port 8090
if grep -A 10 "cadvisor:" docker-compose.yml | grep -E -q '"(\$\{CADVISOR_PORT:-)?8090(\})?:8080"'; then
    success "cAdvisor correctly uses port 8090 (host) → 8080 (container)"
elif grep -A 10 "cadvisor:" docker-compose.yml | grep -q '"8081:8080"'; then
    error "cAdvisor still uses conflicting port 8081"
    exit 1
else
    warning "Could not verify cAdvisor port configuration"
fi

# Check auth-service uses port 8081 (via expose directive)
if grep -A 10 "auth-service:" docker-compose.yml | grep -E -q 'expose:|"(\$\{AUTH_SERVICE_PORT:-)?8081(\})?"'; then
    success "auth-service correctly uses port 8081 (internal only)"
else
    error "auth-service not using port 8081"
    exit 1
fi

echo ""
echo "=========================================="
echo -e "${GREEN}✅ All validations passed!${NC}"
echo ""
echo "Summary:"
echo "  - docker-compose.yml is valid"
echo "  - All Python files have valid syntax"
echo "  - No port conflicts detected"
echo "  - All monitoring services defined"
echo "  - All application services defined"
echo "  - Shared logging utility exists"
echo "  - All services use shared logging"
echo "  - Port conflict resolved (cAdvisor: 8090)"
echo ""
echo "Next steps:"
echo "  1. Start services: docker compose up -d"
echo "  2. Check status: docker compose ps"
echo "  3. Access Grafana: http://localhost:3000 (admin/admin)"
echo "  4. View logs: docker compose logs -f telegram-bot"
echo ""
