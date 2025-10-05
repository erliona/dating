# Monitoring and Observability Setup

This document describes the complete monitoring stack for the Dating Application, including log collection, metrics collection, storage, and visualization.

## Overview

The monitoring stack consists of:
- **Prometheus v2.51.0**: Metrics collection and storage with enhanced service discovery
- **Loki v3.0.0**: Modern log aggregation and storage with TSDB backend
- **Grafana 10.4.0**: Visualization and dashboards with enhanced features
- **Promtail v3.0.0**: Advanced log shipper with JSON parsing and labeling
- **cAdvisor**: Container metrics collection
- **Node Exporter**: System metrics collection
- **Postgres Exporter**: Database metrics collection

### Version Pinning
All monitoring components use specific versions to ensure stability and compatibility. Versions are regularly updated after testing.

### Recent Updates (v3.0 Migration)

**Key Improvements:**
1. ✅ **Loki v3.0.0 Migration**
   - Modern TSDB schema (v13) for better performance
   - Environment variable expansion support
   - Removed deprecated fields (`max_transfer_retries`, `enforce_metric_name`)
   - Enhanced query limits and performance tuning
   - Improved retention management with compactor

2. ✅ **Promtail v3.0.0 Enhancement**
   - Advanced JSON log parsing and detection
   - Automatic log level extraction
   - Better container metadata labeling
   - Performance optimizations (batching, retries)
   - Empty line filtering

3. ✅ **Prometheus v2.51.0 Update**
   - Enhanced service discovery with better labeling
   - Loki metrics collection added
   - Application services discovery prepared
   - Web lifecycle API enabled
   - Health checks added

4. ✅ **Grafana 10.4.0 Upgrade**
   - Modern UI with improved performance
   - Public dashboards support
   - Enhanced query builders
   - Better alerting capabilities

**Migration Notes:**
- All services now use pinned versions instead of `:latest`
- Health checks added for better dependency management
- Configuration files updated to modern schemas
- No breaking changes to existing dashboards or queries

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Application Layer                         │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │ Services │  │ Database │  │  System  │  │  Docker  │        │
│  │(8080-85) │  │   (db)   │  │  (host)  │  │Containers│        │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘        │
│       │             │              │              │              │
└───────┼─────────────┼──────────────┼──────────────┼──────────────┘
        │             │              │              │
        ├─ Logs ─────┼──────────────┼──────────────┤
        │             │              │              │
   ┌────▼─────────────▼──────────────▼──────────────▼────┐
   │              Promtail (Log Shipper)                  │
   │     Collects Docker logs and forwards to Loki       │
   └──────────────────────┬───────────────────────────────┘
                          │
                     ┌────▼──────┐
                     │   Loki    │  Port 3100
                     │  (Logs)   │  Log Aggregation
                     └───────────┘
        
        ├─ Metrics ─┼──────────────┼──────────────┤
        │             │              │              │
   ┌────▼─────┐  ┌───▼────────┐ ┌──▼──────────┐ ┌─▼─────────┐
   │PostgreSQL│  │   Node     │ │   cAdvisor  │ │  Future   │
   │ Exporter │  │  Exporter  │ │ (Containers)│ │  Service  │
   │  :9187   │  │   :9100    │ │    :8090    │ │  Metrics  │
   └────┬─────┘  └────┬───────┘ └──┬──────────┘ └─┬─────────┘
        │             │              │              │
        └─────────────┴──────────────┴──────────────┘
                          │
                     ┌────▼──────────┐
                     │  Prometheus   │  Port 9090
                     │   (Metrics)   │  Metrics Storage
                     └───────────────┘

                          │
   ┌──────────────────────┴───────────────────────┐
   │                                               │
   │              Grafana (Port 3000)              │
   │         Dashboards and Visualization          │
   │                                               │
   │  Data Sources:                                │
   │  • Prometheus (metrics)                       │
   │  • Loki (logs)                                │
   └───────────────────────────────────────────────┘
```

---

## Component Details

### 1. Log Collection Chain

#### Promtail v3.0.0 (Log Shipper)
- **Purpose**: Collects logs from Docker containers and forwards to Loki
- **Version**: 3.0.0 (grafana/promtail:3.0.0)
- **Configuration**: `monitoring/promtail/promtail-config.yml`
- **Collection Method**: 
  - Docker service discovery with automatic container detection
  - Reads from `/var/lib/docker/containers/`
  - Filters for `com.docker.compose.project=dating`
- **Enhanced Log Processing**:
  - Parses Docker JSON logs
  - Extracts and parses application JSON logs
  - Auto-detects log levels (DEBUG, INFO, WARN, ERROR, etc.)
  - Extracts service names from container labels
  - Adds comprehensive container metadata labels
  - Filters empty log lines
  - Batching and retry configuration for reliability

**Key Features:**
```yaml
# Enhanced labeling from Docker metadata
- container_name: Full container name
- container_id: Short container ID (12 chars)
- service: Extracted service name
- compose_project: Docker Compose project
- compose_service: Docker Compose service name
- level: Log level (if detected)

# Performance optimizations
- Batching: 1s wait, 1MB batch size
- Retries: Up to 10 retries with exponential backoff
- JSON parsing: Automatic detection and parsing
```

**Configuration:**
```yaml
scrape_configs:
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        filters:
          - name: label
            values: ["com.docker.compose.project=dating"]
    # ... enhanced relabeling and pipeline stages
```

#### Loki v3.0.0 (Log Aggregation)
- **Version**: 3.0.0 (grafana/loki:3.0.0)
- **Port**: 3100
- **Purpose**: Stores and indexes logs with modern TSDB backend
- **Configuration**: `monitoring/loki/loki-config.yml`
- **Storage**: 
  - TSDB Index: `/loki/tsdb-index` (active indexes)
  - TSDB Cache: `/loki/tsdb-cache` (query cache)
  - Chunks: `/loki/chunks` (log data)
  - WAL: `/loki/wal` (write-ahead log for durability)
  - Compactor: `/loki/compactor` (retention management)
- **Retention**: 30 days (720 hours)
- **API Endpoint**: `http://loki:3100/loki/api/v1/push`

**Modern Features:**
- **Schema v13 with TSDB**: Modern time-series database backend for better performance
- **Environment Variable Expansion**: Supports `${VARIABLE}` syntax with `-config.expand-env=true`
- **Advanced Limits**:
  - Per-stream rate limiting: 5MB/s with 10MB burst
  - Max query length: 30 days
  - Query parallelism: 16 concurrent queries
  - Split queries by 15m intervals for better performance
- **Retention Management**:
  - Compactor runs every 10 minutes
  - Automatic deletion of old data
  - 2-hour delay before deletion
- **Query Optimization**:
  - Embedded cache: 100MB for query results
  - Max 4 concurrent queries per tenant
- **Improved Ingestion**:
  - 10MB/s ingestion rate with 20MB burst
  - Snappy compression for chunks
  - WAL with flush on shutdown for data safety

**Health Check:**
```bash
curl http://localhost:3100/ready
```

### 2. Metrics Collection Chain

#### Application Services
All microservices (ports 8080-8085) expose health endpoints but don't expose Prometheus metrics yet.

**Future Enhancement**: Add `/metrics` endpoint to each service for application-specific metrics.

#### PostgreSQL Exporter
- **Port**: 9187
- **Purpose**: Exposes PostgreSQL database metrics
- **Metrics Endpoint**: `http://postgres-exporter:9187/metrics`
- **Connection**: Connects to `db:5432` using DATA_SOURCE_NAME

**Key Metrics:**
- `pg_up`: Database availability
- `pg_stat_activity_count`: Active connections
- `pg_database_size_bytes`: Database size
- `pg_stat_database_*`: Transaction stats
- `pg_stat_user_tables_*`: Table operations

#### Node Exporter
- **Port**: 9100
- **Purpose**: Exposes system-level metrics
- **Metrics Endpoint**: `http://node-exporter:9100/metrics`

**Key Metrics:**
- CPU usage: `node_cpu_seconds_total`
- Memory: `node_memory_*`
- Disk: `node_disk_*`
- Network: `node_network_*`
- Filesystem: `node_filesystem_*`

#### cAdvisor
- **External Port**: 8090 (internal 8080)
- **Purpose**: Container resource usage metrics
- **Metrics Endpoint**: `http://cadvisor:8080/metrics`
- **Web UI**: `http://localhost:8090`

**Key Metrics:**
- `container_cpu_usage_seconds_total`: Container CPU
- `container_memory_usage_bytes`: Container memory
- `container_network_*`: Container network I/O
- `container_fs_*`: Container filesystem usage

#### Prometheus v2.51.0 (Metrics Storage)
- **Version**: v2.51.0 (prom/prometheus:v2.51.0)
- **Port**: 9090
- **Purpose**: Collects, stores, and queries metrics with time-series database
- **Configuration**: `monitoring/prometheus/prometheus.yml`
- **Storage**: `/prometheus` (30 days retention)
- **Web UI**: `http://localhost:9090`

**Enhanced Configuration:**
```yaml
global:
  scrape_interval: 15s
  scrape_timeout: 10s
  evaluation_interval: 15s
  external_labels:
    cluster: 'dating-app'
    environment: '${ENVIRONMENT:-production}'  # Supports env vars

scrape_configs:
  # Self-monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
        labels:
          service: 'prometheus'
          component: 'monitoring'
  
  # Log aggregation metrics
  - job_name: 'loki'
    static_configs:
      - targets: ['loki:3100']
        labels:
          service: 'loki'
          component: 'monitoring'
  
  # Container metrics
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']
        labels:
          service: 'cadvisor'
          component: 'monitoring'
  
  # System metrics
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
        labels:
          service: 'node-exporter'
          component: 'monitoring'
          instance: 'dating-host'
  
  # Database metrics
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
        labels:
          service: 'postgres'
          component: 'database'
          database: 'dating'
  
  # Proxy metrics
  - job_name: 'traefik'
    static_configs:
      - targets: ['traefik:8080']
        labels:
          service: 'traefik'
          component: 'proxy'
  
  # Application services (for future /metrics endpoints)
  - job_name: 'application-services'
    static_configs:
      - targets:
          - 'api-gateway:8080'
          - 'auth-service:8081'
          - 'profile-service:8082'
          - 'discovery-service:8083'
          - 'media-service:8084'
          - 'chat-service:8085'
        labels:
          component: 'application'
```

**Features:**
- Enhanced labeling for better metric organization
- Loki metrics collection (new)
- Application services discovery (ready for future metrics)
- Web lifecycle API enabled for configuration reloads
- Health check endpoint: `http://localhost:9090/-/healthy`

**Scrape Interval**: 15 seconds (configurable)  
**Timeout**: 10 seconds per scrape

### 3. Visualization Layer

#### Grafana 10.4.0
- **Version**: 10.4.0 (grafana/grafana:10.4.0)
- **Port**: 3000
- **Purpose**: Dashboards and visualization with modern UI
- **Web UI**: `http://localhost:3000`
- **Default Credentials**: admin/admin (change on first login)
- **Configuration**: `monitoring/grafana/provisioning/`

**Enhanced Features:**
- Public dashboards support (via feature toggles)
- Improved UI and performance
- Better query builder for LogQL and PromQL
- Enhanced alerting capabilities

**Data Sources:**
1. **Prometheus** (UID: `prometheus`)
   - URL: `http://prometheus:9090`
   - Type: Time-series metrics
   - Query interval: 15s
   - Use for: System metrics, application metrics, resource usage
   
2. **Loki** (UID: `loki`)
   - URL: `http://loki:3100`
   - Type: Logs
   - Default data source: Yes
   - Max lines: 1000 per query
   - Use for: Application logs, debugging, error tracking

**Provisioning:**
- Datasources: `monitoring/grafana/provisioning/datasources/datasources.yml`
- Dashboards: `monitoring/grafana/provisioning/dashboards/dashboards.yml`
- Dashboard Files: `monitoring/grafana/dashboards/*.json`

**Health Check:**
```bash
curl http://localhost:3000/api/health
```

---

## Dashboards

### 1. Infrastructure Overview (`1-infrastructure-overview.json`)
**Purpose**: System-level monitoring

**Panels:**
- Services Up count
- Total containers
- System CPU usage (gauge)
- System memory usage (gauge)
- Container CPU usage over time
- Container memory usage over time
- Network I/O (receive/transmit)
- Disk I/O (read/write)
- Filesystem usage by mount
- System load average (1m, 5m, 15m)

**Use Cases:**
- Monitor overall system health
- Identify resource bottlenecks
- Track container resource usage

### 2. Application Services (`2-application-services.json`)
**Purpose**: Microservices health and performance

**Panels:**
- Service status indicators (Gateway, Auth, Profile, Discovery, Media, Chat)
- Service CPU usage
- Service memory usage
- Container restarts count
- Bot container status
- Service network I/O

**Use Cases:**
- Monitor service availability
- Detect service failures
- Track service resource consumption
- Identify problematic services

### 3. Application Logs (`3-application-logs.json`)
**Purpose**: Centralized log viewing and analysis

**Panels:**
- Error count (last hour)
- Warning count (last hour)
- Info count (last hour)
- Total logs (last hour)
- Log rate by container
- Log levels over time
- Error logs (recent)
- Warning logs (recent)
- Service-specific logs (API Gateway, Auth, Bot)
- Full logs from all services

**Use Cases:**
- Debug application issues
- Monitor error rates
- Track warning patterns
- Search logs across services

### 4. Database Metrics (`4-database-metrics.json`)
**Purpose**: PostgreSQL performance monitoring

**Panels:**
- Database status
- Active connections
- Database size
- Total tables
- Queries per second (gauge)
- Cache hit rate (gauge)
- Connections over time
- Transaction rate (commits/rollbacks)
- Database I/O (disk reads vs cache hits)
- Table operations (inserts/updates/deletes)
- Deadlocks count
- Slow queries duration
- Temporary files count

**Use Cases:**
- Monitor database health
- Optimize query performance
- Detect connection issues
- Track database growth

---

## Access URLs

| Component | URL | Credentials |
|-----------|-----|-------------|
| Grafana | http://localhost:3000 | admin/admin |
| Prometheus | http://localhost:9090 | - |
| Loki | http://localhost:3100 | - |
| cAdvisor | http://localhost:8090 | - |
| Node Exporter | http://localhost:9100/metrics | - |
| Postgres Exporter | http://localhost:9187/metrics | - |

---

## Usage Guide

### Starting the Monitoring Stack

```bash
# Start all services including monitoring
docker compose up -d

# Check monitoring services
docker compose ps prometheus grafana loki promtail cadvisor node-exporter postgres-exporter
```

### Accessing Grafana

1. Open http://localhost:3000
2. Login with `admin` / `admin`
3. Change password on first login (or skip)
4. Navigate to Dashboards → Browse
5. Open any dashboard (1-4)

### Querying Logs in Grafana

**Example LogQL queries:**

```logql
# All logs from bot container
{job="docker", container_name=~".*bot.*"}

# Error logs from all services
{job="docker"} | json | level="ERROR"

# Logs containing "error" in message
{job="docker"} | json | message =~ "(?i)error"

# Count errors per minute
count_over_time({job="docker"} | json | level="ERROR" [1m])
```

### Querying Metrics in Grafana

**Example PromQL queries:**

```promql
# Container CPU usage
rate(container_cpu_usage_seconds_total[5m]) * 100

# Memory usage by container
container_memory_usage_bytes{name=~".+"}

# Database connections
pg_stat_activity_count

# System CPU usage
100 - (avg(rate(node_cpu_seconds_total{mode="idle"}[5m])) * 100)
```

### Querying Prometheus Directly

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Query metric
curl 'http://localhost:9090/api/v1/query?query=up'

# Query range
curl 'http://localhost:9090/api/v1/query_range?query=up&start=2024-01-01T00:00:00Z&end=2024-01-01T01:00:00Z&step=15s'
```

### Querying Loki Directly

```bash
# Query logs
curl -G -s "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={job="docker"}' \
  --data-urlencode 'limit=10'

# Get log labels
curl http://localhost:3100/loki/api/v1/labels
```

---

## Troubleshooting

### Service Health Checks

**Check all monitoring services health:**
```bash
# Quick health check for all services
curl http://localhost:9090/-/healthy  # Prometheus
curl http://localhost:3100/ready      # Loki
curl http://localhost:3000/api/health # Grafana
curl http://localhost:9080/ready      # Promtail

# Docker compose health status
docker compose ps
```

### Grafana Can't Connect to Datasources

**Check datasource URLs:**
```bash
# From Grafana container
docker compose exec grafana wget -O- http://prometheus:9090/api/v1/status/config
docker compose exec grafana wget -O- http://loki:3100/ready
```

**Verify network:**
```bash
docker network inspect dating_monitoring
```

**Check Grafana logs:**
```bash
docker compose logs grafana | tail -50
```

### No Metrics Appearing

**Check Prometheus targets:**
1. Open http://localhost:9090/targets
2. All targets should show "UP"
3. If DOWN, check the service is running:
   ```bash
   docker compose ps
   ```

**Check scrape configuration:**
```bash
docker compose logs prometheus | grep -i error
```

**Verify Loki metrics are being scraped:**
```bash
# Check if Loki metrics endpoint is accessible
curl http://localhost:3100/metrics
```

### No Logs Appearing

**Check Promtail is running and healthy:**
```bash
docker compose ps promtail
docker compose logs promtail | tail -50
```

**Verify Promtail can reach Loki:**
```bash
docker compose exec promtail wget -O- http://loki:3100/ready
```

**Check Docker socket permissions:**
```bash
docker compose logs promtail | grep -i "permission denied"
```

**Test log collection:**
```bash
# Generate test log
docker compose exec api-gateway echo "Test log message"

# Check if it appears in Loki
curl -G -s "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={compose_service="api-gateway"}' \
  --data-urlencode 'limit=10'
```

### Loki Configuration Errors

**Common issues after v3.0 migration:**

1. **"unknown field" errors**: Old config fields are deprecated
   - Solution: Use the updated config from `monitoring/loki/loki-config.yml`
   
2. **Environment variable not expanded**: Missing `-config.expand-env=true`
   - Solution: Verify docker-compose.yml has the correct command flag
   
3. **Schema mismatch**: Old schema versions not compatible
   - Solution: Modern config uses schema v13 with TSDB

**Check Loki logs for errors:**
```bash
docker compose logs loki | grep -i error
docker compose logs loki | grep -i "level=error"
```

### Dashboards Not Loading

**Check dashboard provisioning:**
```bash
docker compose logs grafana | grep -i dashboard
ls -la monitoring/grafana/dashboards/
```

**Manually import dashboard:**
1. Go to Grafana → Dashboards → Import
2. Upload JSON file from `monitoring/grafana/dashboards/`

**Re-provision dashboards:**
```bash
# Restart Grafana to re-read provisioning configs
docker compose restart grafana
```

### Container Restart Loops

**Check for version incompatibilities:**
```bash
docker compose logs loki --tail 100
docker compose logs promtail --tail 100
```

**Verify volume permissions:**
```bash
docker compose down
docker volume rm dating_loki_data dating_prometheus_data dating_grafana_data
docker compose up -d
```

---

## Performance Tuning

### Prometheus v2.51.0

**Reduce storage (in docker-compose.yml):**
```yaml
command:
  - '--storage.tsdb.retention.time=15d'  # Default: 30d
  - '--storage.tsdb.retention.size=10GB'  # Limit disk usage
```

**Adjust scrape interval (in prometheus.yml):**
```yaml
global:
  scrape_interval: 30s  # Default: 15s (reduce for less data)
  scrape_timeout: 15s   # Must be less than scrape_interval
```

**Optimize query performance:**
```yaml
global:
  evaluation_interval: 30s  # Match scrape_interval
```

### Loki v3.0.0

**Reduce retention (in loki-config.yml):**
```yaml
# Multiple places to update for consistency
limits_config:
  retention_period: 360h  # 15 days instead of 30

compactor:
  retention_enabled: true
  compaction_interval: 10m

table_manager:
  retention_deletes_enabled: true
  retention_period: 360h  # Match limits_config
```

**Adjust ingestion limits (in loki-config.yml):**
```yaml
limits_config:
  # Per-tenant ingestion limits
  ingestion_rate_mb: 4              # Default: 10
  ingestion_burst_size_mb: 8        # Default: 20
  
  # Per-stream limits
  per_stream_rate_limit: 3MB        # Default: 5MB
  per_stream_rate_limit_burst: 6MB  # Default: 10MB
  
  # Query limits
  max_entries_limit_per_query: 3000 # Default: 5000
  max_query_length: 360h            # Match retention
```

**Optimize query performance (in loki-config.yml):**
```yaml
limits_config:
  split_queries_by_interval: 30m    # Default: 15m (larger = fewer queries)
  max_query_parallelism: 8          # Default: 16 (reduce for less CPU)

query_range:
  results_cache:
    cache:
      embedded_cache:
        enabled: true
        max_size_mb: 200              # Default: 100 (increase for better cache hit rate)
```

### Promtail v3.0.0

**Optimize batching (in promtail-config.yml):**
```yaml
clients:
  - url: http://loki:3100/loki/api/v1/push
    batchwait: 2s        # Default: 1s (wait longer for larger batches)
    batchsize: 2097152   # 2MB, Default: 1MB (larger batches = fewer requests)
```

**Reduce scrape frequency:**
```yaml
scrape_configs:
  - job_name: docker
    docker_sd_configs:
      - refresh_interval: 10s  # Default: 5s (less frequent discovery)
```

### General Resource Limits

**Set memory limits in docker-compose.yml:**
```yaml
services:
  loki:
    deploy:
      resources:
        limits:
          memory: 512M
  
  prometheus:
    deploy:
      resources:
        limits:
          memory: 1G
  
  grafana:
    deploy:
      resources:
        limits:
          memory: 256M
```

---

## Adding New Metrics

### From Application Services

1. **Add metrics library** to your service:
   ```python
   from prometheus_client import Counter, Histogram, generate_latest
   
   request_count = Counter('http_requests_total', 'Total HTTP requests')
   ```

2. **Expose metrics endpoint**:
   ```python
   @app.route('/metrics')
   def metrics():
       return generate_latest()
   ```

3. **Add to Prometheus scrape config**:
   ```yaml
   # In monitoring/prometheus/prometheus.yml
   scrape_configs:
     - job_name: 'my-service'
       static_configs:
         - targets: ['my-service:8086']
   ```

4. **Restart Prometheus**:
   ```bash
   docker compose restart prometheus
   ```

---

## Related Documentation

- **Port Mapping**: `docs/PORT_MAPPING.md`
- **CI/CD Guide**: `docs/CI_CD_GUIDE.md`
- **Troubleshooting**: `docs/DEPLOYMENT_TROUBLESHOOTING.md`

---

**Last Updated:** January 2025  
**Maintained By:** Development Team  
**Version:** 1.0
