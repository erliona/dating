# Monitoring Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         Dating App Stack                         │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                      Application Layer                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │ Traefik  │───▶│   Bot    │───▶│    DB    │    │  WebApp  │  │
│  │  :443    │    │  Python  │    │ Postgres │    │  nginx   │  │
│  │  :80     │    │          │    │  :5432   │    │  :80     │  │
│  └────┬─────┘    └────┬─────┘    └────┬─────┘    └────┬─────┘  │
│       │               │               │               │         │
│       │               │               │               │         │
│       └───────────────┴───────────────┴───────────────┘         │
│                           │                                      │
└───────────────────────────┼──────────────────────────────────────┘
                            │
                            │ Metrics & Logs
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Monitoring Layer                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌────────────────┐         ┌──────────────┐                    │
│  │   cAdvisor     │────────▶│  Prometheus  │                    │
│  │   Container    │         │   Metrics    │                    │
│  │   Metrics      │         │   :9090      │                    │
│  └────────────────┘         └──────┬───────┘                    │
│                                    │                             │
│  ┌────────────────┐                │                             │
│  │ Node Exporter  │────────────────┤                             │
│  │   System       │                │                             │
│  │   Metrics      │                │                             │
│  └────────────────┘                │                             │
│                                    │                             │
│  ┌────────────────┐                │         ┌──────────────┐   │
│  │ Postgres       │────────────────┼────────▶│   Grafana    │   │
│  │ Exporter       │                │         │  Dashboards  │   │
│  │ DB Metrics     │                │         │   :3000      │   │
│  └────────────────┘                │         └──────────────┘   │
│                                    │               ▲             │
│  ┌────────────────┐         ┌──────▼───────┐      │             │
│  │   Promtail     │────────▶│     Loki     │──────┘             │
│  │   Log          │         │     Logs     │                    │
│  │   Shipper      │         │   :3100      │                    │
│  └────────────────┘         └──────────────┘                    │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘

                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                        Alert Layer                               │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────────────────────────────────────────────────┐   │
│  │  Prometheus Alerts                                        │   │
│  │  • Container Down                                         │   │
│  │  • High Memory Usage (>90%)                               │   │
│  │  • High CPU Usage (>80%)                                  │   │
│  │  • Low Disk Space (<10%)                                  │   │
│  │  • Database Connection Issues                             │   │
│  │  • High Database Connections (>80)                        │   │
│  └──────────────────────────────────────────────────────────┘   │
│                                                                   │
└─────────────────────────────────────────────────────────────────┘
```

## Data Flow

### Metrics Collection

1. **cAdvisor** → collects container metrics (CPU, memory, network, disk I/O)
2. **Node Exporter** → collects host metrics (system resources)
3. **Postgres Exporter** → collects database metrics (connections, queries, cache)
4. **Prometheus** → scrapes all exporters every 15s
5. **Grafana** → queries Prometheus for visualization

### Logs Collection

1. **Docker containers** → write JSON logs to `/var/lib/docker/containers/`
2. **Promtail** → reads container logs and system logs
3. **Loki** → aggregates and stores logs
4. **Grafana** → queries Loki for log viewing

## Ports

### Application Ports
- `80` - HTTP (redirects to HTTPS)
- `443` - HTTPS (Traefik)
- `5432` - PostgreSQL
- `8080` - WebApp (dev mode)

### Monitoring Ports
- `3000` - Grafana UI
- `9090` - Prometheus UI
- `3100` - Loki API
- `8081` - cAdvisor UI
- `9100` - Node Exporter metrics
- `9187` - Postgres Exporter metrics

## Volumes

### Application Volumes
- `postgres_data` - Database data
- `traefik_certs` - SSL certificates

### Monitoring Volumes
- `prometheus_data` - Metrics (30 days retention)
- `grafana_data` - Dashboards and settings
- `loki_data` - Logs (30 days retention)

## Resource Limits

### Application Services
- **Traefik**: 256MB limit / 128MB reserved
- **Database**: 512MB limit / 256MB reserved
- **Bot**: 512MB limit / 256MB reserved
- **WebApp**: 128MB limit / 64MB reserved

### Monitoring Services
- **Prometheus**: 512MB limit / 256MB reserved
- **Grafana**: 512MB limit / 256MB reserved
- **Loki**: 512MB limit / 256MB reserved
- **Promtail**: 256MB limit / 128MB reserved
- **cAdvisor**: 256MB limit / 128MB reserved
- **Node Exporter**: 128MB limit / 64MB reserved
- **Postgres Exporter**: 128MB limit / 64MB reserved

## Health Checks

All services have configured health checks:

- **Traefik**: `traefik healthcheck --ping` every 10s
- **Database**: `pg_isready` every 10s
- **Bot**: Python runtime check every 30s
- **WebApp**: `wget` localhost check every 30s

## Alerting Rules

### Critical Alerts
- Container down for >1 minute
- PostgreSQL down for >1 minute

### Warning Alerts
- Memory usage >90% for 5 minutes
- CPU usage >80% for 10 minutes
- Disk space <10% for 5 minutes
- Database connections >80 for 5 minutes

## Monitoring Stack Benefits

✅ **Real-time monitoring** of all services
✅ **Historical data** for trend analysis
✅ **Alerting** on critical issues
✅ **Log aggregation** for debugging
✅ **Visual dashboards** for quick overview
✅ **Resource usage tracking** for optimization
✅ **Database performance** monitoring
✅ **Network traffic** analysis

## Next Steps

1. Deploy Alertmanager for notifications
2. Configure email/Slack alerts
3. Create custom dashboards for business metrics
4. Set up log-based alerts in Loki
5. Configure remote storage for Prometheus (Thanos/Cortex)
6. Enable authentication for monitoring endpoints
7. Set up HTTPS for Grafana via Traefik
