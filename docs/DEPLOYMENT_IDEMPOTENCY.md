# Deployment Idempotency Guide

This document explains how the Dating Mini App deployment is designed to be idempotent, meaning you can run deployments multiple times safely without unintended side effects.

## Overview

**Idempotency** means that running the same deployment operation multiple times produces the same result as running it once. This is critical for:
- Zero-downtime deployments
- Rollback capabilities
- Disaster recovery
- Infrastructure as Code (IaC) principles

## Database Migrations (Idempotent ✓)

### Alembic Migration System

The application uses Alembic for database schema migrations, which is **inherently idempotent**:

```bash
# Safe to run multiple times - Alembic tracks applied migrations
alembic upgrade head
```

**How it works:**
- Alembic maintains an `alembic_version` table tracking applied migrations
- Each migration has a unique revision ID
- Running `alembic upgrade head` only applies unapplied migrations
- Already-applied migrations are skipped automatically

**Example from our migrations:**
```python
# Migration 002_create_discovery_tables.py
def upgrade() -> None:
    """Create interactions, matches and favorites tables."""
    op.create_table('interactions', ...)  # Only runs if table doesn't exist
    
def downgrade() -> None:
    """Drop interactions, matches and favorites tables."""
    op.drop_table('interactions')  # Rollback support
```

**Verification:**
```bash
# Check current migration status
alembic current

# Check migration history
alembic history

# Apply migrations (idempotent)
alembic upgrade head
```

### Database Volume Persistence

Docker volumes ensure data persists across deployments:

```yaml
# docker-compose.yml
volumes:
  postgres_data:  # Named volume persists between deployments

services:
  db:
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

**Important Notes:**
- Password changes require volume reset: `docker compose down -v`
- Use same `POSTGRES_PASSWORD` across deployments to avoid connection issues
- Deploy script automatically reuses existing passwords

## Logging (Idempotent ✓)

### Log Rotation Configuration

All services use **JSON file logging with automatic rotation**:

```yaml
# docker-compose.yml - Applied to all services
logging:
  driver: "json-file"
  options:
    max-size: "10m"    # Rotate after 10MB
    max-file: "3"      # Keep 3 rotated files
```

**Benefits:**
- Prevents disk space exhaustion
- Automatic cleanup of old logs
- Consistent across all services
- No manual intervention needed

### Log Aggregation with Loki

Loki (optional monitoring stack) provides centralized logging:

```yaml
# Loki configuration (monitoring/loki/loki-config.yml)
schema_config:
  configs:
    - from: 2020-10-24
      store: boltdb-shipper
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 24h

storage_config:
  boltdb_shipper:
    active_index_directory: /loki/boltdb-shipper-active
    cache_location: /loki/boltdb-shipper-cache
    shared_store: filesystem
  filesystem:
    directory: /loki/chunks
```

**Idempotency features:**
- Loki uses time-based indexes (24h periods)
- Redeployment preserves existing logs via volume
- New logs append without affecting historical data
- Chunk storage is content-addressable

**Enable monitoring stack:**
```bash
# Idempotent - safe to run multiple times
docker compose --profile monitoring up -d
```

### Promtail Log Collection

Promtail configuration is **declarative and idempotent**:

```yaml
# monitoring/promtail/promtail-config.yml
scrape_configs:
  - job_name: containers
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        target_label: container
```

**Idempotency:**
- Configuration is applied on startup
- No state maintained in Promtail itself
- Redeploy = reload configuration
- Missed logs during downtime are not retroactively collected (by design)

## Grafana Provisioning (Idempotent ✓)

### Datasource Provisioning

Grafana datasources are provisioned **declaratively**:

```yaml
# monitoring/grafana/provisioning/datasources/datasources.yml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    uid: prometheus
    url: http://prometheus:9090
    isDefault: false
    editable: true

  - name: Loki
    type: loki
    uid: loki
    url: http://loki:3100
    isDefault: true
    editable: true
```

**Idempotency features:**
- `uid` field ensures datasource identity
- Redeployment updates existing datasources (doesn't duplicate)
- `editable: true` allows manual adjustments without breaking provisioning
- No datasource duplication on redeploy

**How it works:**
1. Grafana reads YAML on startup
2. Matches by `uid` if datasource exists
3. Updates configuration if changed
4. Creates new datasource if not found

### Dashboard Provisioning

Dashboards are provisioned from JSON files:

```yaml
# monitoring/grafana/provisioning/dashboards/dashboards.yml
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
      foldersFromFilesStructure: true
```

**Idempotency features:**
- Dashboards identified by `uid` in JSON
- `updateIntervalSeconds: 10` - auto-syncs changes
- `allowUiUpdates: true` - manual changes preserved
- `disableDeletion: false` - removes dashboards deleted from files

**Dashboard JSON structure:**
```json
{
  "uid": "dating-app-overview",  // Unique identifier
  "title": "Dating App - Overview",
  "version": 1,
  // ... dashboard definition
}
```

### Grafana Data Persistence

User data (saved queries, annotations, etc.) persists via volume:

```yaml
volumes:
  grafana_data:

services:
  grafana:
    volumes:
      - grafana_data:/var/lib/grafana
```

**Important:**
- Provisioned datasources/dashboards come from files (immutable)
- User-created content stored in volume (mutable)
- Redeploy preserves both provisioned and user content

## Deployment Script Idempotency

### Password Management

Deploy script intelligently handles passwords:

```bash
# scripts/deploy.sh
# Reuses existing password to avoid database connection issues
EXISTING_PASSWORD=$(ssh "$REMOTE" "grep '^POSTGRES_PASSWORD=' $REMOTE_PATH/.env" || echo "")
if [ -n "$EXISTING_PASSWORD" ]; then
  POSTGRES_PASSWORD="$EXISTING_PASSWORD"
  echo "✓ Found existing database password, reusing it"
fi
```

**Why this matters:**
- Changing password breaks database connections
- Requires `docker compose down -v` (data loss!)
- Reusing password = zero-downtime redeploy

### Docker Compose Operations

All operations are idempotent:

```bash
# Stop old containers gracefully
docker compose down --timeout 30  # Safe if no containers running

# Pull latest images
docker compose pull  # Only downloads updated layers

# Build and start
docker compose up -d --build --remove-orphans
# - Creates missing containers
# - Recreates containers with config changes
# - Removes orphaned containers
# - Starts stopped containers
```

### Service Health Checks

Deploy script waits for healthy services:

```bash
# scripts/deploy.sh
MAX_WAIT=60
while [ $WAIT_COUNT -lt $MAX_WAIT ]; do
  if docker compose ps | grep -qE "Up.*healthy"; then
    ALL_HEALTHY=true
    break
  fi
  sleep 5
done
```

**Idempotency:**
- Health checks defined in `docker-compose.yml`
- Containers report healthy when ready
- Deploy succeeds only when all services healthy

## Volume Persistence Strategy

### Named Volumes (Persistent)

These volumes **persist across deployments**:

```yaml
volumes:
  postgres_data:      # Database data
  traefik_certs:      # SSL certificates
  prometheus_data:    # Metrics history
  grafana_data:       # Dashboards & user data
  loki_data:          # Log history
  photo_storage:      # User photos
```

**Behavior:**
- Data survives `docker compose down`
- Data survives `docker compose up --build`
- Only deleted with `docker compose down -v` (explicit)

### Configuration Files (Immutable)

These are mounted read-only from host:

```yaml
volumes:
  - ./webapp:/usr/share/nginx/html:ro  # Read-only
  - ./monitoring/prometheus:/etc/prometheus
  - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
```

**Behavior:**
- Changes deployed by updating files and restarting containers
- No state maintained in containers
- Fully reproducible from source code

## Testing Idempotency

### Test 1: Multiple Deployments

```bash
# Deploy once
scripts/deploy.sh -H server.com -u deploy -t "BOT_TOKEN"

# Deploy again (should be no-op or minimal changes)
scripts/deploy.sh -H server.com -u deploy -t "BOT_TOKEN"

# Verify:
# - No database errors
# - All services healthy
# - Data still accessible
# - Dashboards unchanged
```

### Test 2: Database Migration

```bash
# SSH to server
ssh user@server.com
cd /opt/dating

# Run migrations multiple times
docker compose exec bot alembic current
docker compose exec bot alembic upgrade head  # First time
docker compose exec bot alembic upgrade head  # Second time (no-op)
docker compose exec bot alembic upgrade head  # Third time (no-op)

# All should succeed with no errors
```

### Test 3: Grafana Provisioning

```bash
# Restart Grafana multiple times
docker compose restart grafana

# Check logs
docker compose logs grafana | grep -i provision

# Should see:
# - "Provisioning datasources" (updates existing)
# - "Provisioning dashboards" (updates existing)
# - No "duplicate" or "conflict" errors
```

### Test 4: Log Rotation

```bash
# Generate logs
for i in {1..1000}; do
  curl http://localhost:8080/health
done

# Check log size
docker compose exec bot du -sh /var/log

# Verify rotation happened
docker compose logs --tail=10 bot
```

## Best Practices

### 1. Always Use Same Environment Variables

```bash
# BAD: Different password each time
POSTGRES_PASSWORD=$(openssl rand -base64 32)

# GOOD: Reuse existing password
POSTGRES_PASSWORD="${EXISTING_PASSWORD:-$(openssl rand -base64 32)}"
```

### 2. Version Your Migrations

```python
# migrations/versions/003_add_user_settings.py
revision = '003_add_user_settings'
down_revision = '002_create_discovery_tables'  # Explicit dependency
```

### 3. Use UIDs in Grafana

```yaml
# Always include uid for idempotency
datasources:
  - name: Prometheus
    uid: prometheus  # Required for idempotency
```

### 4. Enable Health Checks

```yaml
services:
  bot:
    healthcheck:
      test: ["CMD", "python", "-c", "import sys; sys.exit(0)"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### 5. Use Volume Backups

```bash
# Backup before risky operations
docker run --rm -v dating_postgres_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/postgres_backup.tar.gz /data

# Restore if needed
docker run --rm -v dating_postgres_data:/data -v $(pwd):/backup \
  alpine tar xzf /backup/postgres_backup.tar.gz -C /
```

## Troubleshooting

### Issue: Database Connection Refused

**Cause:** Password changed without resetting volume

**Solution:**
```bash
# Reset database (WARNING: DATA LOSS)
docker compose down -v
docker compose up -d
```

### Issue: Duplicate Grafana Datasources

**Cause:** Missing `uid` in provisioning YAML

**Solution:**
```yaml
# Add unique uid to datasource
datasources:
  - name: Prometheus
    uid: prometheus  # Add this
```

### Issue: Old Logs Not Rotating

**Cause:** Logging driver not configured

**Solution:**
```yaml
# Add to all services in docker-compose.yml
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### Issue: Migration Conflicts

**Cause:** Manual database changes

**Solution:**
```bash
# Check migration status
alembic current

# If out of sync, manually fix or reset
alembic downgrade base  # WARNING: DATA LOSS
alembic upgrade head
```

## Deployment Checklist

Before each deployment, verify:

- [ ] `.env` file has consistent `POSTGRES_PASSWORD`
- [ ] All migration files are committed
- [ ] Grafana dashboards have unique `uid` fields
- [ ] Docker volumes are backed up (if needed)
- [ ] Health checks are defined for all services
- [ ] Log rotation is configured
- [ ] Test deployment in staging environment

## Summary

All three components requested are **fully idempotent**:

✅ **Database (Alembic):** Migration tracking, automatic skip of applied migrations  
✅ **Logs (Docker):** Automatic rotation, volume persistence, centralized aggregation  
✅ **Grafana:** UID-based provisioning, declarative configuration, volume persistence

You can safely run deployments multiple times without side effects!
