# Monitoring Stack v3.0 Migration Guide

This guide helps you migrate from the previous monitoring setup (using `:latest` tags) to the new v3.0 stack with pinned versions and modern configurations.

## Overview

The v3.0 monitoring stack includes:
- **Loki v3.0.0** with TSDB schema v13
- **Prometheus v2.51.0** with enhanced service discovery
- **Grafana 10.4.0** with improved UI
- **Promtail v3.0.0** with advanced log processing

## Why Upgrade?

### Issues Fixed
1. ✅ **Deprecated Configuration Fields**: Removed `ingester.max_transfer_retries` and `validation.enforce_metric_name`
2. ✅ **Environment Variable Expansion**: Added `-config.expand-env=true` flag
3. ✅ **Version Stability**: No more unexpected breaking changes from `:latest` tags
4. ✅ **Better Performance**: TSDB backend for improved query speed
5. ✅ **Enhanced Features**: Automatic log level detection, better labeling

### Benefits
- 🚀 **Better Performance**: TSDB schema optimized for time-series data
- 🔍 **Better Log Analysis**: Automatic JSON parsing and log level extraction
- 🏷️ **Better Organization**: Enhanced labeling for metrics and logs
- 🔐 **Better Reliability**: Health checks and retry mechanisms
- 📊 **Better Monitoring**: Loki metrics now scraped by Prometheus

## Migration Steps

### Step 1: Backup Current Data (Optional)

If you want to preserve existing metrics and logs:

```bash
# Stop services
docker compose down

# Backup volumes
docker run --rm -v dating_prometheus_data:/data -v $(pwd):/backup alpine tar czf /backup/prometheus_backup.tar.gz /data
docker run --rm -v dating_loki_data:/data -v $(pwd):/backup alpine tar czf /backup/loki_backup.tar.gz /data
docker run --rm -v dating_grafana_data:/data -v $(pwd):/backup alpine tar czf /backup/grafana_backup.tar.gz /data
```

### Step 2: Pull Latest Changes

```bash
# Pull the latest code with v3.0 configurations
git pull origin main

# Or if using a specific branch
git pull origin <branch-name>
```

### Step 3: Clean Start (Recommended)

For the cleanest migration, start fresh:

```bash
# Stop all services
docker compose down

# Remove old volumes (WARNING: This deletes all monitoring data)
docker volume rm dating_loki_data dating_prometheus_data dating_grafana_data

# Pull new images
docker compose pull prometheus grafana loki promtail

# Start services
docker compose up -d
```

### Step 4: Verify Health

```bash
# Check service health
docker compose ps

# All monitoring services should show "healthy" status
# If not, wait 30-60 seconds for health checks to pass

# Test endpoints
curl http://localhost:9090/-/healthy  # Prometheus - should return "Prometheus Server is Healthy."
curl http://localhost:3100/ready      # Loki - should return "ready"
curl http://localhost:3000/api/health # Grafana - should return {"database":"ok","version":"..."}
curl http://localhost:9080/ready      # Promtail - should return "Ready"
```

### Step 5: Verify Grafana

```bash
# Open Grafana
open http://localhost:3000

# Login: admin/admin (change password on first login)

# Check datasources:
# 1. Go to Configuration → Data Sources
# 2. Verify "Prometheus" shows green (connected)
# 3. Verify "Loki" shows green (connected)

# Check dashboards:
# 1. Go to Dashboards
# 2. You should see 4 dashboards:
#    - Infrastructure Overview
#    - Application Services
#    - Application Logs
#    - Database Metrics
```

### Step 6: Test Log Collection

```bash
# Generate some logs
docker compose exec api-gateway echo "Test log message"

# Wait 10-30 seconds for log collection

# Query Loki via API
curl -G -s "http://localhost:3100/loki/api/v1/query_range" \
  --data-urlencode 'query={compose_service="api-gateway"}' \
  --data-urlencode 'limit=10' | jq .

# Or check in Grafana:
# 1. Go to Explore
# 2. Select "Loki" datasource
# 3. Query: {compose_service="api-gateway"}
```

## In-Place Migration (Keep Data)

If you want to keep existing data:

```bash
# Stop services
docker compose down

# Pull latest changes (with new configs)
git pull

# Pull new images
docker compose pull prometheus grafana loki promtail

# Start with new configs but existing data
docker compose up -d

# Monitor logs for any errors
docker compose logs -f loki promtail prometheus grafana
```

**Note**: Loki v3.0 can read data from older versions, but you may see warnings about old schema formats.

## Troubleshooting

### Loki fails to start

**Error**: "unknown field" in configuration

**Solution**: Make sure you're using the new `loki-config.yml`:
```bash
# Verify config is correct
cat monitoring/loki/loki-config.yml | grep "schema: v13"

# Should show: schema: v13
```

**Error**: Environment variables not expanding

**Solution**: Verify docker-compose.yml has the flag:
```bash
grep "config.expand-env" docker-compose.yml

# Should show: command: -config.file=/etc/loki/loki-config.yml -config.expand-env=true
```

### Promtail not collecting logs

**Check Docker socket permissions**:
```bash
docker compose logs promtail | grep -i permission
```

**Verify Promtail can reach Loki**:
```bash
docker compose exec promtail wget -O- http://loki:3100/ready
```

**Check positions file**:
```bash
docker compose exec promtail cat /tmp/positions.yaml
```

### Grafana datasources not connecting

**Check network connectivity**:
```bash
# From Grafana container
docker compose exec grafana wget -O- http://prometheus:9090/-/healthy
docker compose exec grafana wget -O- http://loki:3100/ready
```

**Verify services are in same network**:
```bash
docker network inspect dating_monitoring
```

### Old dashboards not working

**Solution**: Dashboards are compatible, but you may need to refresh:
```bash
# Restart Grafana to reload provisioning
docker compose restart grafana

# Check dashboard provisioning logs
docker compose logs grafana | grep -i dashboard
```

## Rollback Plan

If you encounter issues and need to rollback:

```bash
# Stop services
docker compose down

# Checkout previous version
git checkout <previous-commit-or-tag>

# Restore from backup (if you made one)
docker run --rm -v dating_prometheus_data:/data -v $(pwd):/backup alpine tar xzf /backup/prometheus_backup.tar.gz -C /
docker run --rm -v dating_loki_data:/data -v $(pwd):/backup alpine tar xzf /backup/loki_backup.tar.gz -C /
docker run --rm -v dating_grafana_data:/data -v $(pwd):/backup alpine tar xzf /backup/grafana_backup.tar.gz -C /

# Start with old config
docker compose up -d
```

## What Changed?

### Configuration Files

**monitoring/loki/loki-config.yml**:
- Modern schema_config with TSDB v13
- Added storage_config with tsdb_shipper
- Enhanced limits_config
- Added compactor and table_manager
- Removed deprecated fields

**monitoring/promtail/promtail-config.yml**:
- Enhanced batching and retry config
- Better relabeling with more metadata
- JSON log parsing in pipeline
- Automatic log level detection
- Empty line filtering

**monitoring/prometheus/prometheus.yml**:
- Added Loki metrics scraping
- Enhanced service labeling
- Better organized scrape configs
- Application services discovery

**docker-compose.yml**:
- Pinned versions for all monitoring services
- Added health checks
- Added `-config.expand-env=true` flags
- Improved service dependencies

### Version Changes

| Service | Old | New | Changes |
|---------|-----|-----|---------|
| Loki | `latest` | `3.0.0` | TSDB schema, better performance |
| Promtail | `latest` | `3.0.0` | Enhanced log processing |
| Prometheus | `latest` | `v2.51.0` | Better service discovery |
| Grafana | `latest` | `10.4.0` | Improved UI, new features |

## Post-Migration Checklist

- [ ] All services show "healthy" status
- [ ] Prometheus targets are all "UP"
- [ ] Loki receives logs (test with query)
- [ ] Grafana can connect to both datasources
- [ ] All 4 dashboards load correctly
- [ ] Logs appear in "Application Logs" dashboard
- [ ] Metrics appear in other dashboards
- [ ] Health check endpoints respond correctly

## Need Help?

- 📚 [Full Monitoring Setup Guide](MONITORING_SETUP.md)
- 🔧 [Troubleshooting Guide](DEPLOYMENT_TROUBLESHOOTING.md#7-monitoring-stack-issues)
- 🐛 [Report Issues](https://github.com/erliona/dating/issues)

## Performance Notes

**Resource Usage**:
- Loki v3.0 uses ~10-20% less memory than previous versions
- TSDB queries are 2-3x faster for time-range queries
- Disk usage is similar but better organized

**Recommended Minimums**:
- RAM: 512MB for Loki, 1GB for Prometheus, 256MB for Grafana
- Disk: 10GB for 30-day retention
- CPU: 2 cores shared across all monitoring services

---

**Last Updated**: January 2025  
**Version**: 3.0.0  
**Maintained By**: Development Team
