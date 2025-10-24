#!/bin/bash

# Prometheus Alerts Check Script
# This script checks for active alerts in Prometheus and reports their status

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Configuration
PROMETHEUS_URL="http://localhost:9090"
GRAFANA_URL="http://localhost:3000"

log_info() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠️${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

check_prometheus_alerts() {
    log_info "Checking Prometheus alerts..."
    
    # Check if Prometheus is accessible
    if ! curl -s -f "$PROMETHEUS_URL/api/v1/query?query=up" > /dev/null 2>&1; then
        log_error "Prometheus is not accessible at $PROMETHEUS_URL"
        return 1
    fi
    
    # Get active alerts
    local alerts_response=$(curl -s "$PROMETHEUS_URL/api/v1/alerts" 2>/dev/null)
    
    if [ $? -ne 0 ]; then
        log_error "Failed to fetch alerts from Prometheus"
        return 1
    fi
    
    # Parse alerts using jq if available, otherwise use basic parsing
    if command -v jq > /dev/null 2>&1; then
        local firing_count=$(echo "$alerts_response" | jq '.data.alerts | map(select(.state == "firing")) | length' 2>/dev/null || echo "0")
        local pending_count=$(echo "$alerts_response" | jq '.data.alerts | map(select(.state == "pending")) | length' 2>/dev/null || echo "0")
    else
        # Basic parsing without jq
        local firing_count=$(echo "$alerts_response" | grep -o '"state":"firing"' | wc -l)
        local pending_count=$(echo "$alerts_response" | grep -o '"state":"pending"' | wc -l)
    fi
    
    if [ "$firing_count" -gt 0 ]; then
        log_error "Found $firing_count FIRING alerts!"
        echo "$alerts_response" | jq '.data.alerts[] | select(.state == "firing") | {alertname: .labels.alertname, severity: .labels.severity, instance: .labels.instance}' 2>/dev/null || echo "Use 'curl $PROMETHEUS_URL/api/v1/alerts' to see details"
        return 1
    elif [ "$pending_count" -gt 0 ]; then
        log_warn "Found $pending_count PENDING alerts"
        echo "$alerts_response" | jq '.data.alerts[] | select(.state == "pending") | {alertname: .labels.alertname, severity: .labels.severity, instance: .labels.instance}' 2>/dev/null || echo "Use 'curl $PROMETHEUS_URL/api/v1/alerts' to see details"
        return 0
    else
        log_info "No active alerts found"
        return 0
    fi
}

check_grafana_dashboards() {
    log_info "Checking Grafana dashboards..."
    
    # Check if Grafana is accessible
    if ! curl -s -f "$GRAFANA_URL/api/health" > /dev/null 2>&1; then
        log_warn "Grafana is not accessible at $GRAFANA_URL"
        return 1
    fi
    
    log_info "Grafana is accessible"
    log_info "Dashboard URLs:"
    log_info "  - Main: $GRAFANA_URL/d/dating-overview"
    log_info "  - Business: $GRAFANA_URL/d/dating-business"
    log_info "  - Discovery: $GRAFANA_URL/d/dating-discovery"
    
    return 0
}

check_critical_metrics() {
    log_info "Checking critical metrics..."
    
    local metrics=(
        "up{job=\"api-gateway\"}"
        "up{job=\"auth-service\"}"
        "up{job=\"profile-service\"}"
        "up{job=\"discovery-service\"}"
        "up{job=\"media-service\"}"
        "up{job=\"chat-service\"}"
        "up{job=\"admin-service\"}"
        "up{job=\"telegram-bot\"}"
    )
    
    local failed_services=()
    
    for metric in "${metrics[@]}"; do
        local result=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=$metric" 2>/dev/null)
        
        if echo "$result" | grep -q '"result":\[\]' || echo "$result" | grep -q '"value":\[.*,0\]'; then
            local service_name=$(echo "$metric" | sed 's/up{job="\(.*\)"}/\1/')
            failed_services+=("$service_name")
        fi
    done
    
    if [ ${#failed_services[@]} -gt 0 ]; then
        log_error "Failed services: ${failed_services[*]}"
        return 1
    else
        log_info "All services are up"
        return 0
    fi
}

check_resource_usage() {
    log_info "Checking resource usage..."
    
    # Check high CPU usage
    local high_cpu=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=rate(container_cpu_usage_seconds_total[5m]) > 0.8" 2>/dev/null)
    if echo "$high_cpu" | grep -q '"result":\[.*\]' && ! echo "$high_cpu" | grep -q '"result":\[\]'; then
        log_warn "High CPU usage detected"
    fi
    
    # Check high memory usage
    local high_memory=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=container_memory_usage_bytes / container_spec_memory_limit_bytes > 0.8" 2>/dev/null)
    if echo "$high_memory" | grep -q '"result":\[.*\]' && ! echo "$high_memory" | grep -q '"result":\[\]'; then
        log_warn "High memory usage detected"
    fi
    
    # Check disk usage
    local high_disk=$(curl -s "$PROMETHEUS_URL/api/v1/query?query=node_filesystem_avail_bytes / node_filesystem_size_bytes < 0.1" 2>/dev/null)
    if echo "$high_disk" | grep -q '"result":\[.*\]' && ! echo "$high_disk" | grep -q '"result":\[\]'; then
        log_warn "Low disk space detected"
    fi
    
    log_info "Resource usage check completed"
    return 0
}

# Main execution
echo "========================================"
echo "  Prometheus Alerts Check"
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

# Check Prometheus alerts
total_checks=$((total_checks + 1))
if ! check_prometheus_alerts; then
    failed_checks=$((failed_checks + 1))
fi

# Check Grafana dashboards
total_checks=$((total_checks + 1))
if ! check_grafana_dashboards; then
    failed_checks=$((failed_checks + 1))
fi

# Check critical metrics
total_checks=$((total_checks + 1))
if ! check_critical_metrics; then
    failed_checks=$((failed_checks + 1))
fi

# Check resource usage
total_checks=$((total_checks + 1))
if ! check_resource_usage; then
    failed_checks=$((failed_checks + 1))
fi

# Summary
echo ""
echo "========================================"
echo "  Alerts Check Summary"
echo "========================================"

if [ $failed_checks -eq 0 ]; then
    log_info "All monitoring checks passed! ($total_checks/$total_checks)"
    echo ""
    log_info "No critical alerts or issues detected."
    exit 0
else
    log_error "Some monitoring checks failed! ($failed_checks/$total_checks failed)"
    echo ""
    log_warn "Please review the failed checks above."
    echo ""
    log_info "Manual checks:"
    log_info "  - Prometheus: $PROMETHEUS_URL/alerts"
    log_info "  - Grafana: $GRAFANA_URL"
    exit 1
fi
