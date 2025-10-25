# Monitoring Setup Guide

## Overview

This document describes the monitoring stack for the dating platform, including Prometheus, Grafana, and Loki.

## Components

### Prometheus
- **Purpose**: Metrics collection and storage
- **Port**: 9090
- **Version**: 2.51.0
- **Storage**: TSDB (Time Series Database)
- **Configuration**: `monitoring/prometheus/prometheus.yml`

### Grafana
- **Purpose**: Visualization and dashboards
- **Port**: 3000
- **Version**: 10.4.0
- **Configuration**: `monitoring/grafana/`

### Loki
- **Purpose**: Log aggregation
- **Port**: 3100
- **Version**: 3.0.0
- **Configuration**: `monitoring/loki/loki-config.yml`

## Setup

1. **Start monitoring stack**:
   ```bash
   docker compose --profile production up -d
   ```

2. **Access Grafana**:
   - URL: http://localhost:3000
   - Default credentials: admin/admin

3. **Access Prometheus**:
   - URL: http://localhost:9090

## Dashboards

### Available Dashboards
- Infrastructure Overview
- Application Services
- Business Metrics
- API Performance
- Database Metrics
- Security Dashboard
- Application Logs

### Dashboard Configuration
Dashboards are located in `monitoring/grafana/dashboards/` and are automatically provisioned.

## Alerts

### Alert Rules
Alert rules are defined in `monitoring/prometheus/alerts.yml` and include:
- High error rates
- Service downtime
- Resource usage
- Security events

### Alert Channels
- Email notifications
- Slack integration
- PagerDuty (optional)

## Log Management

### Log Sources
- Application logs
- System logs
- Database logs
- Security logs

### Log Retention
- Production: 30 days
- Development: 7 days

## Performance Monitoring

### Key Metrics
- Response times
- Throughput
- Error rates
- Resource utilization

### SLIs/SLOs
- Availability: 99.9%
- Response time: <200ms (95th percentile)
- Error rate: <1%

## Troubleshooting

### Common Issues
1. **Grafana not accessible**: Check if port 3000 is available
2. **No metrics**: Verify Prometheus targets are up
3. **Missing logs**: Check Loki configuration

### Debug Commands
```bash
# Check service status
docker compose ps

# View logs
docker compose logs -f prometheus
docker compose logs -f grafana
docker compose logs -f loki

# Test connectivity
curl http://localhost:9090/-/healthy
curl http://localhost:3000/api/health
```

## Security

### Access Control
- Grafana: Basic auth + LDAP (optional)
- Prometheus: No auth (internal network only)
- Loki: No auth (internal network only)

### Network Security
- All services on internal network
- No external port exposure
- TLS termination at reverse proxy

## Maintenance

### Regular Tasks
- Review alert rules monthly
- Update dashboards quarterly
- Clean old logs weekly
- Backup configurations

### Backup
- Grafana dashboards: Git repository
- Prometheus data: Volume snapshots
- Loki data: Volume snapshots
