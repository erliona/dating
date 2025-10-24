#!/bin/bash
# JWT Metrics Monitoring Script
# Monitors JWT performance and security metrics

set -e

# Configuration
PROMETHEUS_URL="http://localhost:9090"
ALERT_THRESHOLD_JWT_ERRORS=10
ALERT_THRESHOLD_RESPONSE_TIME=200
ALERT_THRESHOLD_SUCCESS_RATE=95

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Check Prometheus connectivity
check_prometheus() {
    if ! curl -f -s "$PROMETHEUS_URL/api/v1/query?query=up" > /dev/null; then
        log "❌ Prometheus is not accessible at $PROMETHEUS_URL"
        exit 1
    fi
    log "✅ Prometheus is accessible"
}

# Query Prometheus metrics
query_metric() {
    local query="$1"
    local result=$(curl -s "$PROMETHEUS_URL/api/v1/query" --data-urlencode "query=$query" | jq -r '.data.result[0].value[1]' 2>/dev/null || echo "0")
    echo "$result"
}

# Check JWT validation success rate
check_jwt_success_rate() {
    log "🔍 Checking JWT validation success rate..."
    
    local total_validations=$(query_metric "rate(jwt_tokens_validated_total[5m])")
    local failed_validations=$(query_metric "rate(jwt_tokens_validated_total{result=\"invalid\"}[5m])")
    
    if [ "$total_validations" != "0" ]; then
        local success_rate=$(echo "scale=2; (($total_validations - $failed_validations) / $total_validations) * 100" | bc -l)
        log "📊 JWT Success Rate: ${success_rate}%"
        
        if (( $(echo "$success_rate < $ALERT_THRESHOLD_SUCCESS_RATE" | bc -l) )); then
            log "⚠️  WARNING: JWT success rate is below threshold (${success_rate}% < ${ALERT_THRESHOLD_SUCCESS_RATE}%)"
            return 1
        fi
    else
        log "ℹ️  No JWT validation metrics found"
    fi
}

# Check JWT response times
check_jwt_response_times() {
    log "🔍 Checking JWT response times..."
    
    local avg_generation_time=$(query_metric "jwt_generation_duration_seconds{quantile=\"0.95\"}")
    local avg_validation_time=$(query_metric "jwt_validation_duration_seconds{quantile=\"0.95\"}")
    
    if [ "$avg_generation_time" != "0" ] && [ "$avg_generation_time" != "null" ]; then
        local generation_ms=$(echo "scale=2; $avg_generation_time * 1000" | bc -l)
        log "📊 JWT Generation Time (95th percentile): ${generation_ms}ms"
        
        if (( $(echo "$generation_ms > 50" | bc -l) )); then
            log "⚠️  WARNING: JWT generation time exceeds SLO (${generation_ms}ms > 50ms)"
        fi
    fi
    
    if [ "$avg_validation_time" != "0" ] && [ "$avg_validation_time" != "null" ]; then
        local validation_ms=$(echo "scale=2; $avg_validation_time * 1000" | bc -l)
        log "📊 JWT Validation Time (95th percentile): ${validation_ms}ms"
        
        if (( $(echo "$validation_ms > 10" | bc -l) )); then
            log "⚠️  WARNING: JWT validation time exceeds SLO (${validation_ms}ms > 10ms)"
        fi
    fi
}

# Check token expiration rates
check_token_expiration() {
    log "🔍 Checking token expiration patterns..."
    
    local expired_tokens=$(query_metric "rate(jwt_tokens_validated_total{result=\"expired\"}[5m])")
    local total_tokens=$(query_metric "rate(jwt_tokens_validated_total[5m])")
    
    if [ "$total_tokens" != "0" ]; then
        local expiration_rate=$(echo "scale=2; ($expired_tokens / $total_tokens) * 100" | bc -l)
        log "📊 Token Expiration Rate: ${expiration_rate}%"
        
        if (( $(echo "$expiration_rate > 20" | bc -l) )); then
            log "⚠️  WARNING: High token expiration rate (${expiration_rate}% > 20%)"
        fi
    fi
}

# Check authentication endpoints
check_auth_endpoints() {
    log "🔍 Checking authentication endpoints..."
    
    # Test auth service health
    if curl -f -s http://localhost:8080/api/v1/auth/health > /dev/null; then
        log "✅ Auth service health check passed"
    else
        log "❌ Auth service health check failed"
        return 1
    fi
    
    # Test admin auth endpoint
    local admin_response=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8080/admin/auth/login \
        -H "Content-Type: application/json" \
        -d '{"username":"test","password":"test"}')
    
    if [ "$admin_response" = "401" ] || [ "$admin_response" = "403" ]; then
        log "✅ Admin auth endpoint accessible (authentication failed as expected)"
    else
        log "❌ Admin auth endpoint not accessible (HTTP $admin_response)"
        return 1
    fi
}

# Check for JWT errors in logs
check_jwt_errors() {
    log "🔍 Checking for JWT errors in logs..."
    
    local error_count=0
    
    # Check API Gateway logs
    local api_errors=$(docker-compose logs --tail=100 api-gateway 2>/dev/null | grep -i "jwt" | grep -i "error" | wc -l)
    error_count=$((error_count + api_errors))
    
    # Check Auth Service logs
    local auth_errors=$(docker-compose logs --tail=100 auth-service 2>/dev/null | grep -i "jwt" | grep -i "error" | wc -l)
    error_count=$((error_count + auth_errors))
    
    # Check Admin Service logs
    local admin_errors=$(docker-compose logs --tail=100 admin-service 2>/dev/null | grep -i "jwt" | grep -i "error" | wc -l)
    error_count=$((error_count + admin_errors))
    
    log "📊 JWT Errors in logs (last 100 lines): $error_count"
    
    if [ "$error_count" -gt "$ALERT_THRESHOLD_JWT_ERRORS" ]; then
        log "⚠️  WARNING: High JWT error count detected ($error_count > $ALERT_THRESHOLD_JWT_ERRORS)"
        return 1
    fi
}

# Check service health
check_service_health() {
    log "🔍 Checking service health..."
    
    local unhealthy_services=$(docker-compose ps | grep -v "healthy" | grep -v "NAME" | wc -l)
    
    if [ "$unhealthy_services" -gt 0 ]; then
        log "❌ Found $unhealthy_services unhealthy services:"
        docker-compose ps | grep -v "healthy" | grep -v "NAME"
        return 1
    else
        log "✅ All services are healthy"
    fi
}

# Generate JWT metrics report
generate_report() {
    log "📊 Generating JWT metrics report..."
    
    local report_file="/tmp/jwt-metrics-report-$(date +%Y%m%d_%H%M%S).txt"
    
    {
        echo "JWT Metrics Report - $(date)"
        echo "=================================="
        echo ""
        
        echo "Service Health:"
        docker-compose ps
        echo ""
        
        echo "JWT Validation Metrics:"
        curl -s "$PROMETHEUS_URL/api/v1/query?query=jwt_tokens_validated_total" | jq '.data.result[]'
        echo ""
        
        echo "JWT Performance Metrics:"
        curl -s "$PROMETHEUS_URL/api/v1/query?query=jwt_generation_duration_seconds" | jq '.data.result[]'
        curl -s "$PROMETHEUS_URL/api/v1/query?query=jwt_validation_duration_seconds" | jq '.data.result[]'
        echo ""
        
        echo "Recent JWT Errors:"
        docker-compose logs --tail=50 api-gateway auth-service admin-service | grep -i "jwt" | grep -i "error" | tail -10
        
    } > "$report_file"
    
    log "📄 Report generated: $report_file"
}

# Main monitoring function
monitor_jwt_metrics() {
    log "🚀 Starting JWT metrics monitoring..."
    
    check_prometheus
    check_service_health
    check_auth_endpoints
    check_jwt_success_rate
    check_jwt_response_times
    check_token_expiration
    check_jwt_errors
    
    log "✅ JWT metrics monitoring completed"
}

# Continuous monitoring
continuous_monitor() {
    local interval=${1:-60}
    log "🔄 Starting continuous monitoring (interval: ${interval}s)"
    
    while true; do
        monitor_jwt_metrics
        sleep "$interval"
    done
}

# Alert on issues
alert_on_issues() {
    local issues=0
    
    # Check for critical issues
    if ! check_service_health; then
        issues=$((issues + 1))
    fi
    
    if ! check_auth_endpoints; then
        issues=$((issues + 1))
    fi
    
    if ! check_jwt_success_rate; then
        issues=$((issues + 1))
    fi
    
    if ! check_jwt_errors; then
        issues=$((issues + 1))
    fi
    
    if [ "$issues" -gt 0 ]; then
        log "🚨 ALERT: $issues critical issues detected"
        generate_report
        return 1
    else
        log "✅ No critical issues detected"
        return 0
    fi
}

# Main script logic
main() {
    case "${1:-monitor}" in
        "monitor")
            monitor_jwt_metrics
            ;;
        "continuous")
            continuous_monitor "${2:-60}"
            ;;
        "alert")
            alert_on_issues
            ;;
        "report")
            generate_report
            ;;
        *)
            echo "Usage: $0 {monitor|continuous|alert|report}"
            echo ""
            echo "Commands:"
            echo "  monitor     - Run one-time JWT metrics check"
            echo "  continuous  - Run continuous monitoring (default: 60s interval)"
            echo "  alert       - Check for critical issues and alert"
            echo "  report      - Generate detailed metrics report"
            exit 1
            ;;
    esac
}

# Run main function
main "$@"
