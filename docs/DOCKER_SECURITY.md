# Docker Security Standards & Implementation Guide

## Overview

This document defines comprehensive Docker security standards for the dating application project, covering base image security, container runtime security, and infrastructure hardening.

## Security Principles

### 1. Defense in Depth
- Multiple layers of security controls
- Fail-safe defaults
- Principle of least privilege
- Regular security updates

### 2. Zero Trust Architecture
- Never trust, always verify
- Assume breach mentality
- Continuous monitoring and validation

## Base Image Security

### Pinned Base Images

**REQUIRED**: All base images MUST be pinned to specific versions.

```dockerfile
# ✅ GOOD: Pinned version
FROM python:3.11.7-slim

# ❌ BAD: Floating tag
FROM python:3.11-slim

# ✅ BETTER: SHA256 digest (most secure)
FROM python:3.11.7-slim@sha256:abc123...
```

### Distroless/Slim Variants

**PREFERRED**: Use minimal base images to reduce attack surface.

```dockerfile
# ✅ GOOD: Slim variant
FROM python:3.11.7-slim

# ✅ BETTER: Distroless (if available)
FROM gcr.io/distroless/python3-debian11

# ❌ BAD: Full image with unnecessary packages
FROM python:3.11.7
```

### Multi-stage Builds

Use multi-stage builds to minimize final image size and attack surface.

```dockerfile
# Build stage
FROM python:3.11.7-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Runtime stage
FROM python:3.11.7-slim AS runtime

# Install only runtime dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
    libpq5 \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy virtual environment
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Application setup
WORKDIR /app
COPY . .

# Security: Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser
RUN chown -R appuser:appuser /app
USER appuser

CMD ["python", "app.py"]
```

## Container Runtime Security

### Non-Root User

**MANDATORY**: All containers MUST run as non-root user.

```dockerfile
# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Set proper permissions
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser
```

### Security Options

**MANDATORY**: Apply security options in docker-compose.yml.

```yaml
services:
  api-gateway:
    # ... other config ...
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE  # Only if needed for port binding
    read_only: true
    tmpfs:
      - /tmp
      - /app/cache
      - /app/logs
```

### Capability Management

**Principle**: Drop all capabilities, add only what's needed.

```yaml
# Drop all capabilities by default
cap_drop:
  - ALL

# Add only specific capabilities if needed
cap_add:
  - NET_BIND_SERVICE  # For binding to ports < 1024
  - CHOWN             # For file ownership changes
  - SETUID             # For setuid operations
```

### Read-Only Root Filesystem

**RECOMMENDED**: Use read-only root filesystem with tmpfs for writable directories.

```yaml
services:
  api-gateway:
    read_only: true
    tmpfs:
      - /tmp:rw,noexec,nosuid,size=100m
      - /app/cache:rw,noexec,nosuid,size=50m
      - /app/logs:rw,noexec,nosuid,size=100m
      - /var/run:rw,noexec,nosuid,size=10m
```

## Health Checks

### HTTP Health Endpoint

**MANDATORY**: All services MUST implement `/health` endpoint.

```python
# Example health endpoint implementation
from aiohttp import web

async def health_check(request: web.Request) -> web.Response:
    """Health check endpoint."""
    try:
        # Check database connectivity
        await check_database()
        
        # Check external dependencies
        await check_dependencies()
        
        return web.json_response({
            "status": "healthy",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.2.0"
        })
    except Exception as e:
        return web.json_response({
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }, status=503)
```

### Docker Compose Health Check

**MANDATORY**: All services MUST have health checks in docker-compose.yml.

```yaml
services:
  api-gateway:
    # ... other config ...
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    restart: unless-stopped
```

## Network Security

### Network Isolation

```yaml
services:
  api-gateway:
    networks:
      - frontend
      - backend
    # No external port exposure for internal services
    
  database:
    networks:
      - backend
    # No external port exposure
```

### Internal Communication

```yaml
# Use internal service names
environment:
  DATABASE_URL: postgresql://db:5432/dating
  REDIS_URL: redis://redis:6379
  AUTH_SERVICE_URL: http://auth-service:8081
```

## Secrets Management

### Environment Variables

```yaml
services:
  api-gateway:
    environment:
      - JWT_SECRET=${JWT_SECRET}
      - DATABASE_URL=${DATABASE_URL}
    # Never use secrets in docker-compose.yml directly
```

### Docker Secrets (Production)

```yaml
services:
  api-gateway:
    secrets:
      - jwt_secret
      - database_password
    environment:
      - JWT_SECRET_FILE=/run/secrets/jwt_secret
      - DATABASE_PASSWORD_FILE=/run/secrets/database_password

secrets:
  jwt_secret:
    external: true
  database_password:
    external: true
```

## Resource Limits

### CPU and Memory Limits

```yaml
services:
  api-gateway:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
```

### Process Limits

```yaml
services:
  api-gateway:
    ulimits:
      nproc: 100
      nofile:
        soft: 1024
        hard: 2048
```

## Security Scanning

### Base Image Scanning

```bash
# Scan base images for vulnerabilities
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image python:3.11.7-slim

# Scan built images
docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
  aquasec/trivy image dating/api-gateway:latest
```

### Runtime Security Monitoring

```yaml
services:
  api-gateway:
    # Enable security monitoring
    labels:
      - "security.scan=true"
      - "security.level=high"
```

## Security Checklist

### Dockerfile Security Checklist

- [ ] Base image is pinned to specific version
- [ ] Using slim/distroless variant
- [ ] Multi-stage build implemented
- [ ] Non-root user created and used
- [ ] No unnecessary packages installed
- [ ] Secrets not embedded in image
- [ ] Proper file permissions set
- [ ] No hardcoded credentials
- [ ] Minimal attack surface

### Docker Compose Security Checklist

- [ ] All services have health checks
- [ ] Restart policy set to `unless-stopped`
- [ ] Security options configured (`no-new-privileges`)
- [ ] Capabilities dropped (`ALL`)
- [ ] Read-only root filesystem enabled
- [ ] Resource limits set
- [ ] Network isolation implemented
- [ ] No unnecessary port exposure
- [ ] Secrets managed securely

## Implementation Examples

### Secure Dockerfile Template

```dockerfile
# Multi-stage build for security and size
FROM python:3.11.7-slim@sha256:abc123... AS builder

# Install build dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --no-deps -r requirements.txt

# Runtime stage
FROM python:3.11.7-slim@sha256:abc123... AS runtime

# Install only runtime dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
    libpq5 \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser appuser

# Copy virtual environment
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Set up application
WORKDIR /app
COPY --chown=appuser:appuser . .

# Set proper permissions
RUN chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run application
CMD ["python", "-m", "services.api_gateway.main"]
```

### Secure Docker Compose Template

```yaml
version: '3.8'

services:
  api-gateway:
    build:
      context: .
      dockerfile: services/api-gateway/Dockerfile
    image: dating/api-gateway:latest
    container_name: dating-api-gateway
    
    # Security options
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
    
    # Read-only root filesystem
    read_only: true
    tmpfs:
      - /tmp:rw,noexec,nosuid,size=100m
      - /app/cache:rw,noexec,nosuid,size=50m
      - /app/logs:rw,noexec,nosuid,size=100m
      - /var/run:rw,noexec,nosuid,size=10m
    
    # Resource limits
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.25'
          memory: 256M
    
    # Process limits
    ulimits:
      nproc: 100
      nofile:
        soft: 1024
        hard: 2048
    
    # Health check
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    
    # Restart policy
    restart: unless-stopped
    
    # Environment
    environment:
      - PYTHONUNBUFFERED=1
      - PYTHONDONTWRITEBYTECODE=1
      - JWT_SECRET=${JWT_SECRET}
      - DATABASE_URL=${DATABASE_URL}
    
    # Networks
    networks:
      - frontend
      - backend
    
    # No external ports for internal services
    # ports: []  # Commented out for security
```

## Monitoring and Alerting

### Security Metrics

```yaml
# Prometheus metrics for security monitoring
security_container_restarts_total
security_health_check_failures_total
security_capability_violations_total
security_privilege_escalation_attempts_total
```

### Security Alerts

```yaml
# Alert on security violations
- alert: ContainerSecurityViolation
  expr: increase(security_capability_violations_total[5m]) > 0
  for: 0m
  labels:
    severity: critical
  annotations:
    summary: "Container security violation detected"
    description: "Capability violation in container {{ $labels.container }}"
```

## Best Practices

### Development

1. **Always use pinned base images**
2. **Implement multi-stage builds**
3. **Run as non-root user**
4. **Minimize attack surface**
5. **Regular security scanning**

### Production

1. **Enable all security options**
2. **Use read-only filesystem**
3. **Implement proper health checks**
4. **Monitor security metrics**
5. **Regular security updates**

### Maintenance

1. **Regular base image updates**
2. **Security vulnerability scanning**
3. **Dependency updates**
4. **Security policy reviews**
5. **Incident response procedures**
