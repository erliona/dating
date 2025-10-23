# Metrics Guide

This document provides a comprehensive guide to all metrics collected by the dating application microservices.

## Overview

The application collects three types of metrics:

1. **HTTP Metrics**: Request/response metrics for all services
2. **Business Metrics**: Application-specific business events and state
3. **System Metrics**: Infrastructure and service health metrics

All metrics are exposed in Prometheus format at `/metrics` endpoint on each service.

## HTTP Metrics

### http_requests_total

**Type**: Counter  
**Description**: Total number of HTTP requests  
**Labels**: `method`, `endpoint`, `status_code`, `service`

**Example**:
```
http_requests_total{method="POST",endpoint="/profiles",status_code="201",service="profile-service"} 42
```

### http_request_duration_seconds

**Type**: Histogram  
**Description**: HTTP request duration in seconds  
**Labels**: `method`, `endpoint`, `service`  
**Buckets**: 0.01, 0.025, 0.05, 0.075, 0.1, 0.25, 0.5, 0.75, 1.0, 2.5, 5.0, 7.5, 10.0, +Inf

**Example**:
```
http_request_duration_seconds_bucket{method="GET",endpoint="/profiles/123",service="profile-service",le="0.1"} 15
http_request_duration_seconds_sum{method="GET",endpoint="/profiles/123",service="profile-service"} 2.5
http_request_duration_seconds_count{method="GET",endpoint="/profiles/123",service="profile-service"} 20
```

### http_requests_active

**Type**: Gauge  
**Description**: Number of currently active HTTP requests  
**Labels**: `service`

**Example**:
```
http_requests_active{service="profile-service"} 3
```

## Business Metrics

### Profile Metrics

#### profile_created_total

**Type**: Counter  
**Description**: Total number of profiles created  
**Labels**: `service`

**Example**:
```
profile_created_total{service="profile-service"} 1250
```

#### profile_updated_total

**Type**: Counter  
**Description**: Total number of profiles updated  
**Labels**: `service`

**Example**:
```
profile_updated_total{service="profile-service"} 890
```

#### profile_deleted_total

**Type**: Counter  
**Description**: Total number of profiles deleted  
**Labels**: `service`

**Example**:
```
profile_deleted_total{service="profile-service"} 45
```

### Interaction Metrics

#### interaction_created_total

**Type**: Counter  
**Description**: Total number of interactions (likes, dislikes, matches)  
**Labels**: `service`, `type`

**Types**:
- `like`: User liked a profile
- `dislike`: User disliked a profile
- `match`: Mutual like created a match

**Example**:
```
interaction_created_total{service="discovery-service",type="like"} 5420
interaction_created_total{service="discovery-service",type="dislike"} 1230
interaction_created_total{service="discovery-service",type="match"} 890
```

#### swipes_total

**Type**: Counter  
**Description**: Total number of swipes (likes + dislikes)  
**Labels**: `service`, `type`

**Types**:
- `like`: Like swipe
- `dislike`: Dislike swipe

**Example**:
```
swipes_total{service="discovery-service",type="like"} 5420
swipes_total{service="discovery-service",type="dislike"} 1230
```

### Message Metrics

#### message_sent_total

**Type**: Counter  
**Description**: Total number of messages sent  
**Labels**: `service`

**Example**:
```
message_sent_total{service="chat-service"} 15670
```

#### conversation_started_total

**Type**: Counter  
**Description**: Total number of conversations started  
**Labels**: `service`

**Example**:
```
conversation_started_total{service="chat-service"} 890
```

### Current State Metrics

#### active_users_total

**Type**: Gauge  
**Description**: Number of users active in the last 24 hours  
**Labels**: `service`

**Example**:
```
active_users_total{service="discovery-service"} 1250
```

#### users_by_region

**Type**: Gauge  
**Description**: Number of users by geographic region  
**Labels**: `service`, `region`

**Example**:
```
users_by_region{service="discovery-service",region="US"} 450
users_by_region{service="discovery-service",region="EU"} 320
users_by_region{service="discovery-service",region="unknown"} 480
```

#### matches_current

**Type**: Gauge  
**Description**: Current number of matches  
**Labels**: `service`

**Example**:
```
matches_current{service="discovery-service"} 890
```

#### conversations_active

**Type**: Gauge  
**Description**: Number of active conversations  
**Labels**: `service`

**Example**:
```
conversations_active{service="chat-service"} 156
```

## Legacy Metrics

These metrics are maintained for backward compatibility but should be replaced with the new business metrics:

### users_total

**Type**: Gauge  
**Description**: Total number of users (legacy - use profile_created_total)  
**Labels**: `service`

### matches_total

**Type**: Gauge  
**Description**: Total number of matches (legacy - use interaction_created_total)  
**Labels**: `service`

### messages_total

**Type**: Gauge  
**Description**: Total number of messages (legacy - use message_sent_total)  
**Labels**: `service`

## Circuit Breaker Metrics

### circuit_breaker_calls_total

**Type**: Counter  
**Description**: Total circuit breaker calls  
**Labels**: `service`, `target`, `state`, `result`

**States**:
- `closed`: Circuit is closed, calls pass through
- `open`: Circuit is open, calls are blocked
- `half_open`: Circuit is half-open, testing calls

**Results**:
- `success`: Call succeeded
- `failure`: Call failed

**Example**:
```
circuit_breaker_calls_total{service="profile-service",target="data-service",state="closed",result="success"} 1250
circuit_breaker_calls_total{service="profile-service",target="data-service",state="open",result="failure"} 45
```

### circuit_breaker_state

**Type**: Gauge  
**Description**: Current circuit breaker state  
**Labels**: `service`, `target`

**Values**:
- `0`: Closed
- `1`: Open
- `2`: Half-open

**Example**:
```
circuit_breaker_state{service="profile-service",target="data-service"} 0
```

## Security Metrics

### security_events_total

**Type**: Counter  
**Description**: Total number of security events  
**Labels**: `service`, `event_type`, `severity`

**Example**:
```
security_events_total{service="auth-service",event_type="invalid_token",severity="warning"} 25
```

### auth_attempts_total

**Type**: Counter  
**Description**: Total authentication attempts  
**Labels**: `service`, `result`

**Example**:
```
auth_attempts_total{service="auth-service",result="success"} 1250
auth_attempts_total{service="auth-service",result="failure"} 45
```

### auth_failures_total

**Type**: Counter  
**Description**: Total authentication failures  
**Labels**: `service`, `reason`

**Example**:
```
auth_failures_total{service="auth-service",reason="invalid_token"} 25
auth_failures_total{service="auth-service",reason="expired_token"} 20
```

### jwt_validations_total

**Type**: Counter  
**Description**: Total JWT token validations  
**Labels**: `service`, `result`

**Example**:
```
jwt_validations_total{service="profile-service",result="success"} 5420
jwt_validations_total{service="profile-service",result="failure"} 45
```

### rate_limit_hits_total

**Type**: Counter  
**Description**: Total rate limit hits  
**Labels**: `service`, `endpoint`

**Example**:
```
rate_limit_hits_total{service="auth-service",endpoint="/auth/validate"} 12
```

## Grafana Queries

### Business Metrics Dashboard

#### Total Users
```promql
sum(profile_created_total)
```

#### Total Matches
```promql
sum(interaction_created_total{type="match"})
```

#### Total Messages
```promql
sum(message_sent_total)
```

#### Active Users (24h)
```promql
sum(active_users_total)
```

#### Match Rate
```promql
rate(interaction_created_total{type="match"}[1h]) / rate(swipes_total[1h]) * 100
```

#### Message Rate
```promql
rate(message_sent_total[1h])
```

### API Performance Dashboard

#### Request Rate
```promql
rate(http_requests_total[5m])
```

#### Error Rate
```promql
rate(http_requests_total{status_code=~"5.."}[5m]) / rate(http_requests_total[5m]) * 100
```

#### Response Time (95th percentile)
```promql
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

#### Active Requests
```promql
sum(http_requests_active)
```

### Circuit Breaker Dashboard

#### Circuit Breaker State
```promql
circuit_breaker_state
```

#### Circuit Breaker Call Rate
```promql
rate(circuit_breaker_calls_total[5m])
```

#### Circuit Breaker Success Rate
```promql
rate(circuit_breaker_calls_total{result="success"}[5m]) / rate(circuit_breaker_calls_total[5m]) * 100
```

## Alerting Rules

### Critical Alerts

#### High Error Rate
```yaml
- alert: HighErrorRate
  expr: rate(http_requests_total{status_code=~"5.."}[5m]) / rate(http_requests_total[5m]) > 0.05
  for: 2m
  labels:
    severity: critical
  annotations:
    summary: "High error rate detected"
    description: "Error rate is {{ $value | humanizePercentage }} for service {{ $labels.service }}"
```

#### Circuit Breaker Open
```yaml
- alert: CircuitBreakerOpen
  expr: circuit_breaker_state == 1
  for: 1m
  labels:
    severity: warning
  annotations:
    summary: "Circuit breaker is open"
    description: "Circuit breaker for {{ $labels.service }} -> {{ $labels.target }} is open"
```

#### High Response Time
```yaml
- alert: HighResponseTime
  expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m])) > 2
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "High response time detected"
    description: "95th percentile response time is {{ $value }}s for service {{ $labels.service }}"
```

## Best Practices

### Metric Naming

1. Use descriptive names that clearly indicate what is being measured
2. Use `_total` suffix for counters
3. Use `_current` or `_active` suffix for gauges
4. Use consistent label names across related metrics

### Label Usage

1. Keep label cardinality low to avoid performance issues
2. Use meaningful label values
3. Include service name in all metrics
4. Use consistent label names across metrics

### Metric Collection

1. Use counters for events that can only increase
2. Use gauges for values that can go up and down
3. Use histograms for request durations
4. Avoid high-cardinality labels

### Dashboard Design

1. Group related metrics together
2. Use appropriate visualization types
3. Include time ranges and refresh intervals
4. Add meaningful titles and descriptions
5. Use consistent color schemes

## Troubleshooting

### Missing Metrics

1. Check if metrics are defined in the service
2. Verify metric names and labels
3. Check Prometheus configuration for scraping
4. Verify service is exposing `/metrics` endpoint

### High Cardinality

1. Review label usage
2. Avoid using high-cardinality values as labels
3. Consider using recording rules for complex queries
4. Monitor Prometheus memory usage

### Performance Issues

1. Check metric collection frequency
2. Review query complexity
3. Use recording rules for expensive queries
4. Monitor Prometheus resource usage
