# Monitoring and Observability Setup

This document describes the complete monitoring stack for the Dating Application, including log collection, metrics collection, storage, and visualization.

## Overview

The monitoring stack consists of:
- **Prometheus**: Metrics collection and storage
- **Loki**: Log aggregation and storage
- **Grafana**: Visualization and dashboards
- **Promtail**: Log shipper
- **cAdvisor**: Container metrics
- **Node Exporter**: System metrics
- **Postgres Exporter**: Database metrics

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

#### Promtail (Log Shipper)
- **Purpose**: Collects logs from Docker containers and forwards to Loki
- **Configuration**: `monitoring/promtail/promtail-config.yml`
- **Collection Method**: 
  - Docker service discovery
  - Reads from `/var/lib/docker/containers/`
  - Filters for `com.docker.compose.project=dating`
- **Log Processing**:
  - Parses JSON logs
  - Extracts timestamps
  - Adds container labels

**Key Configuration:**
```yaml
scrape_configs:
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        filters:
          - name: label
            values: ["com.docker.compose.project=dating"]
```

#### Loki (Log Aggregation)
- **Port**: 3100
- **Purpose**: Stores and indexes logs
- **Configuration**: `monitoring/loki/loki-config.yml`
- **Storage**: 
  - Chunks: `/loki/chunks`
  - WAL: `/loki/wal`
- **Retention**: 30 days (720 hours)
- **API Endpoint**: `http://loki:3100/loki/api/v1/push`

**Features:**
- JSON log parsing
- Label-based indexing
- LogQL query language
- 30-day retention policy

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

#### Prometheus (Metrics Storage)
- **Port**: 9090
- **Purpose**: Collects, stores, and queries metrics
- **Configuration**: `monitoring/prometheus/prometheus.yml`
- **Storage**: `/prometheus` (30 days retention)
- **Web UI**: `http://localhost:9090`

**Scrape Configuration:**
```yaml
scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']
  
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']
  
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']
  
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
```

**Scrape Interval**: 15 seconds

### 3. Visualization Layer

#### Grafana
- **Port**: 3000
- **Purpose**: Dashboards and visualization
- **Web UI**: `http://localhost:3000`
- **Default Credentials**: admin/admin
- **Configuration**: `monitoring/grafana/provisioning/`

**Data Sources:**
1. **Prometheus** (UID: `prometheus`)
   - URL: `http://prometheus:9090`
   - Query metrics
   
2. **Loki** (UID: `loki`)
   - URL: `http://loki:3100`
   - Query logs
   - Default data source

**Provisioning:**
- Datasources: `monitoring/grafana/provisioning/datasources/datasources.yml`
- Dashboards: `monitoring/grafana/provisioning/dashboards/dashboards.yml`
- Dashboard Files: `monitoring/grafana/dashboards/*.json`

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

### No Logs Appearing

**Check Promtail is running:**
```bash
docker compose ps promtail
docker compose logs promtail
```

**Verify Promtail can reach Loki:**
```bash
docker compose exec promtail wget -O- http://loki:3100/ready
```

**Check Docker socket permissions:**
```bash
docker compose logs promtail | grep -i "permission denied"
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

---

## Performance Tuning

### Prometheus

**Reduce storage:**
```yaml
# In prometheus.yml
storage.tsdb.retention.time=15d  # Default: 30d
```

**Adjust scrape interval:**
```yaml
# In prometheus.yml
scrape_interval: 30s  # Default: 15s
```

### Loki

**Reduce retention:**
```yaml
# In loki-config.yml
table_manager:
  retention_period: 360h  # 15 days instead of 30
```

**Adjust ingestion limits:**
```yaml
# In loki-config.yml
limits_config:
  ingestion_rate_mb: 4  # Default: 10
  ingestion_burst_size_mb: 8  # Default: 20
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
- **Deployment Guide**: `docs/MICROSERVICES_DEPLOYMENT.md`
- **Troubleshooting**: `docs/DEPLOYMENT_TROUBLESHOOTING.md`

---

**Last Updated:** January 2025  
**Maintained By:** Development Team  
**Version:** 1.0
