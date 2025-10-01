#!/usr/bin/env bash
# Validate monitoring stack deployment
#
# This script checks if all monitoring components are running correctly
# and can collect metrics/logs.

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
  echo -e "${GREEN}✓${NC} $1"
}

print_error() {
  echo -e "${RED}✗${NC} $1"
}

print_warning() {
  echo -e "${YELLOW}⚠${NC} $1"
}

print_info() {
  echo -e "${BLUE}ℹ${NC} $1"
}

print_section() {
  echo ""
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
  echo -e "${BLUE}$1${NC}"
  echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
}

# Check if monitoring services are defined
print_section "1. Checking Docker Compose Configuration"

if docker compose -f docker-compose.yml -f docker-compose.monitoring.yml config > /dev/null 2>&1; then
  print_success "Docker Compose configuration is valid"
else
  print_error "Docker Compose configuration has errors"
  exit 1
fi

# Check if services are running
print_section "2. Checking Service Status"

SERVICES=(
  "prometheus"
  "grafana"
  "loki"
  "promtail"
  "cadvisor"
  "node-exporter"
  "postgres-exporter"
)

ALL_RUNNING=true
for service in "${SERVICES[@]}"; do
  if docker compose ps "$service" 2>/dev/null | grep -q "Up"; then
    print_success "$service is running"
  else
    print_error "$service is not running"
    ALL_RUNNING=false
  fi
done

if [ "$ALL_RUNNING" = false ]; then
  print_warning "Some monitoring services are not running"
  print_info "Start them with: docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d"
  exit 1
fi

# Check if Prometheus is reachable
print_section "3. Checking Prometheus"

if curl -s http://localhost:9090/-/healthy > /dev/null 2>&1; then
  print_success "Prometheus is healthy and reachable"
  
  # Check if Prometheus has targets
  TARGETS=$(curl -s http://localhost:9090/api/v1/targets | grep -o '"up"' | wc -l)
  if [ "$TARGETS" -gt 0 ]; then
    print_success "Prometheus has $TARGETS active targets"
  else
    print_warning "Prometheus has no active targets"
  fi
else
  print_error "Prometheus is not reachable at http://localhost:9090"
fi

# Check if Grafana is reachable
print_section "4. Checking Grafana"

if curl -s http://localhost:3000/api/health > /dev/null 2>&1; then
  print_success "Grafana is healthy and reachable"
  
  # Check if datasources are configured
  if curl -s -u admin:admin http://localhost:3000/api/datasources 2>/dev/null | grep -q "Prometheus"; then
    print_success "Prometheus datasource is configured"
  else
    print_warning "Prometheus datasource is not configured"
  fi
  
  if curl -s -u admin:admin http://localhost:3000/api/datasources 2>/dev/null | grep -q "Loki"; then
    print_success "Loki datasource is configured"
  else
    print_warning "Loki datasource is not configured"
  fi
else
  print_error "Grafana is not reachable at http://localhost:3000"
fi

# Check if Loki is reachable
print_section "5. Checking Loki"

if curl -s http://localhost:3100/ready > /dev/null 2>&1; then
  print_success "Loki is healthy and reachable"
else
  print_error "Loki is not reachable at http://localhost:3100"
fi

# Check if cAdvisor is reachable
print_section "6. Checking cAdvisor"

if curl -s http://localhost:8081/healthz > /dev/null 2>&1; then
  print_success "cAdvisor is healthy and reachable"
else
  print_error "cAdvisor is not reachable at http://localhost:8081"
fi

# Check if metrics are being collected
print_section "7. Checking Metrics Collection"

# Check container metrics
if curl -s http://localhost:9090/api/v1/query?query=up 2>/dev/null | grep -q '"status":"success"'; then
  print_success "Metrics are being collected by Prometheus"
  
  # Show some metrics
  CONTAINER_COUNT=$(curl -s http://localhost:9090/api/v1/query?query=count\(container_memory_usage_bytes\) 2>/dev/null | grep -o '"value":\[.*,.*\]' | grep -o '"[0-9]*"' | tail -1 | tr -d '"')
  if [ -n "$CONTAINER_COUNT" ] && [ "$CONTAINER_COUNT" -gt 0 ]; then
    print_success "Collecting metrics from $CONTAINER_COUNT containers"
  fi
else
  print_warning "Could not verify metric collection"
fi

# Check log collection
print_section "8. Checking Log Collection"

if curl -s http://localhost:3100/loki/api/v1/labels 2>/dev/null | grep -q "status.*success"; then
  print_success "Loki is collecting logs"
else
  print_warning "Could not verify log collection"
fi

# Check alert rules
print_section "9. Checking Alert Rules"

ALERTS=$(curl -s http://localhost:9090/api/v1/rules 2>/dev/null | grep -o '"name"' | wc -l)
if [ "$ALERTS" -gt 0 ]; then
  print_success "$ALERTS alert rules are loaded"
else
  print_warning "No alert rules are loaded"
fi

# Summary
print_section "Summary"

echo ""
print_info "Monitoring Stack Status:"
echo ""
echo "  • Prometheus:        http://localhost:9090"
echo "  • Grafana:           http://localhost:3000 (admin/admin)"
echo "  • Loki:              http://localhost:3100"
echo "  • cAdvisor:          http://localhost:8081"
echo ""

if [ "$ALL_RUNNING" = true ]; then
  print_success "All monitoring services are operational!"
  echo ""
  print_info "Next steps:"
  echo "  1. Open Grafana at http://localhost:3000"
  echo "  2. Login with admin/admin"
  echo "  3. Navigate to Dashboards → Dating App - Overview"
  echo "  4. Explore metrics and logs"
  echo ""
  exit 0
else
  print_error "Some checks failed. Please review the output above."
  echo ""
  exit 1
fi
