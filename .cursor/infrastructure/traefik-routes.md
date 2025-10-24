# Traefik Routing Contracts & Standards

## Overview

This document defines standardized routing contracts, middleware stacks, and priority matrices for consistent Traefik configuration across all services.

## Middleware Standards

### Core Middleware Stack

```yaml
# Standard middleware definitions
middlewares:
  # Strip API prefix for internal routing
  strip-api:
    stripPrefix:
      prefixes:
        - "/api"
  
  # Security headers
  security-headers:
    headers:
      customRequestHeaders:
        X-Forwarded-Proto: "https"
      customResponseHeaders:
        X-Content-Type-Options: "nosniff"
        X-Frame-Options: "DENY"
        X-XSS-Protection: "1; mode=block"
        Strict-Transport-Security: "max-age=31536000; includeSubDomains"
  
  # Rate limiting
  rate-limit:
    rateLimit:
      burst: 100
      average: 50
  
  # Redirect to HTTPS
  redirect-to-https:
    redirectScheme:
      scheme: "https"
      permanent: true
```

### Service-Specific Middleware

```yaml
# API Gateway middleware
api-gateway-middleware:
  stripPrefix:
    prefixes: ["/api"]
  headers:
    customRequestHeaders:
      X-Forwarded-Proto: "https"
      X-Real-IP: "{{ .ClientIP }}"

# Admin service middleware  
admin-middleware:
  headers:
    customResponseHeaders:
      X-Admin-Panel: "true"
      Cache-Control: "no-cache, no-store, must-revalidate"

# Webapp middleware
webapp-middleware:
  headers:
    customResponseHeaders:
      Cache-Control: "public, max-age=3600"
```

## Route Priority Matrix

### Priority Levels

| Priority | Service Type | Path Pattern | Description |
|----------|--------------|--------------|-------------|
| 1 | Webapp | `/` | Main application (highest priority) |
| 50 | Admin | `/admin` | Admin panel |
| 100 | API Gateway | `/v1/*` | Direct API routes |
| 200 | API Gateway | `/api/*` | API routes with strip middleware |
| 300 | Health | `/health` | Health checks |
| 400 | Metrics | `/metrics` | Prometheus metrics |

### Route Configuration Examples

```yaml
# Webapp (Priority 1)
- "traefik.http.routers.webapp.rule=Host(`${DOMAIN}`) && PathPrefix(`/`)"
- "traefik.http.routers.webapp.priority=1"
- "traefik.http.routers.webapp.entrypoints=websecure"
- "traefik.http.routers.webapp.tls.certresolver=letsencrypt"

# Admin Panel (Priority 50)
- "traefik.http.routers.admin.rule=Host(`${DOMAIN}`) && PathPrefix(`/admin`)"
- "traefik.http.routers.admin.priority=50"
- "traefik.http.routers.admin.entrypoints=websecure"
- "traefik.http.routers.admin.tls.certresolver=letsencrypt"
- "traefik.http.routers.admin.middlewares=admin-middleware"

# API Gateway Direct Routes (Priority 100)
- "traefik.http.routers.api-gateway.rule=Host(`${DOMAIN}`) && PathPrefix(`/v1`)"
- "traefik.http.routers.api-gateway.priority=100"
- "traefik.http.routers.api-gateway.entrypoints=websecure"
- "traefik.http.routers.api-gateway.tls.certresolver=letsencrypt"
- "traefik.http.routers.api-gateway.middlewares=api-gateway-middleware"

# API Gateway Strip Routes (Priority 200)
- "traefik.http.routers.api-gateway-api.rule=Host(`${DOMAIN}`) && PathPrefix(`/api`)"
- "traefik.http.routers.api-gateway-api.priority=200"
- "traefik.http.routers.api-gateway-api.entrypoints=websecure"
- "traefik.http.routers.api-gateway-api.tls.certresolver=letsencrypt"
- "traefik.http.routers.api-gateway-api.middlewares=strip-api,security-headers,rate-limit"
```

## Service Label Templates

### API Gateway Service

```yaml
api-gateway:
  labels:
    # HTTP router
    - "traefik.enable=true"
    - "traefik.http.routers.api-gateway.rule=Host(`${DOMAIN}`) && PathPrefix(`/v1`)"
    - "traefik.http.routers.api-gateway.entrypoints=websecure"
    - "traefik.http.routers.api-gateway.priority=100"
    - "traefik.http.routers.api-gateway.tls.certresolver=letsencrypt"
    - "traefik.http.routers.api-gateway.middlewares=api-gateway-middleware"
    
    # API router with strip middleware
    - "traefik.http.routers.api-gateway-api.rule=Host(`${DOMAIN}`) && PathPrefix(`/api`)"
    - "traefik.http.routers.api-gateway-api.entrypoints=websecure"
    - "traefik.http.routers.api-gateway-api.priority=200"
    - "traefik.http.routers.api-gateway-api.tls.certresolver=letsencrypt"
    - "traefik.http.routers.api-gateway-api.middlewares=strip-api,security-headers,rate-limit"
    
    # Service configuration
    - "traefik.http.services.api-gateway.loadbalancer.server.port=${GATEWAY_PORT:-8080}"
```

### Admin Service

```yaml
admin-service:
  labels:
    # HTTP router
    - "traefik.enable=true"
    - "traefik.http.routers.admin.rule=Host(`${DOMAIN}`) && PathPrefix(`/admin`)"
    - "traefik.http.routers.admin.entrypoints=websecure"
    - "traefik.http.routers.admin.priority=50"
    - "traefik.http.routers.admin.tls.certresolver=letsencrypt"
    - "traefik.http.routers.admin.middlewares=admin-middleware"
    
    # Service configuration
    - "traefik.http.services.admin.loadbalancer.server.port=${ADMIN_SERVICE_PORT:-8086}"
```

### Webapp Service

```yaml
webapp:
  labels:
    # HTTP router
    - "traefik.enable=true"
    - "traefik.http.routers.webapp.rule=Host(`${DOMAIN}`) && PathPrefix(`/`)"
    - "traefik.http.routers.webapp.entrypoints=websecure"
    - "traefik.http.routers.webapp.priority=1"
    - "traefik.http.routers.webapp.tls.certresolver=letsencrypt"
    - "traefik.http.routers.webapp.middlewares=webapp-middleware"
    
    # Service configuration
    - "traefik.http.services.webapp.loadbalancer.server.port=80"
```

## Route Testing Commands

### Verify Route Configuration

```bash
# Check all routers
curl http://localhost:8091/api/http/routers | jq '.[] | {name: .name, rule: .rule, priority: .priority}'

# Check specific service routes
curl http://localhost:8091/api/http/routers | jq '.[] | select(.name | contains("api-gateway"))'

# Check middleware configuration
curl http://localhost:8091/api/http/middlewares | jq '.[] | {name: .name, type: .type}'

# Test route resolution
curl -H "Host: dating.serge.cc" http://localhost:8080/v1/auth/health
curl -H "Host: dating.serge.cc" http://localhost:8080/api/v1/auth/health
curl -H "Host: dating.serge.cc" http://localhost:8080/admin/
```

### Route Debugging

```bash
# Check route priorities
curl http://localhost:8091/api/http/routers | jq '.[] | {name: .name, priority: .priority} | sort_by(.priority)'

# Verify middleware chain
curl http://localhost:8091/api/http/routers | jq '.[] | select(.name == "api-gateway-api") | .middlewares'

# Test rate limiting
for i in {1..10}; do curl -H "Host: dating.serge.cc" http://localhost:8080/api/v1/auth/health; done
```

## Troubleshooting Guide

### Common Issues

1. **Route not matching**: Check rule syntax and priority
2. **Middleware not applied**: Verify middleware name and configuration
3. **Strip prefix not working**: Check middleware order and prefix configuration
4. **SSL certificate issues**: Verify certresolver and domain configuration

### Debug Commands

```bash
# Check Traefik logs
docker compose logs traefik --tail=50

# Verify service discovery
curl http://localhost:8091/api/http/services

# Test route resolution with verbose output
curl -v -H "Host: dating.serge.cc" http://localhost:8080/api/v1/auth/health
```

## Migration Guide

### Updating Existing Routes

1. **Check current configuration**:
   ```bash
   curl http://localhost:8091/api/http/routers | jq '.[] | {name: .name, rule: .rule, priority: .priority}'
   ```

2. **Update docker-compose.yml** with new labels

3. **Restart affected services**:
   ```bash
   docker compose up -d service-name
   ```

4. **Verify new configuration**:
   ```bash
   curl http://localhost:8091/api/http/routers | jq '.[] | select(.name | contains("service-name"))'
   ```

### Rollback Procedure

1. **Revert docker-compose.yml** to previous labels
2. **Restart services**:
   ```bash
   docker compose up -d service-name
   ```
3. **Verify rollback**:
   ```bash
   curl http://localhost:8091/api/http/routers | jq '.[] | select(.name | contains("service-name"))'
   ```
