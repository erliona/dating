# Monitoring Stack for Dating App

This directory contains the monitoring and observability stack for the Dating app, including Prometheus, Grafana, Loki, and related components.

## 🎯 Components

### Metrics Collection
- **Prometheus** - Time-series database for metrics
- **cAdvisor** - Container metrics collector
- **Node Exporter** - System/host metrics
- **Postgres Exporter** - Database metrics

### Visualization
- **Grafana** - Dashboards and visualization

### Logging
- **Loki** - Log aggregation system
- **Promtail** - Log shipper

## 🚀 Quick Start

### Deploy with Monitoring

```bash
# Start main application with monitoring stack
docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d

# Or for development
docker compose -f docker-compose.dev.yml -f docker-compose.monitoring.yml up -d
```

### Access Dashboards

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090
- **cAdvisor**: http://localhost:8081

### Stop Monitoring Stack

```bash
# Stop all services including monitoring
docker compose -f docker-compose.yml -f docker-compose.monitoring.yml down

# Remove monitoring data volumes (⚠️ this deletes all metrics and logs)
docker compose -f docker-compose.monitoring.yml down -v
```

## 📊 Available Metrics

### Container Metrics (cAdvisor)
- CPU usage per container
- Memory usage and limits
- Network I/O
- Disk I/O
- Container restart counts

### System Metrics (Node Exporter)
- CPU usage
- Memory usage
- Disk space
- Network statistics
- System load

### Database Metrics (Postgres Exporter)
- Active connections
- Transaction rate
- Query performance
- Database size
- Cache hit ratio

### Application Logs (Loki)
- All container logs
- System logs
- Searchable and filterable

## 📈 Grafana Dashboards

### Pre-configured Dashboards

1. **Dating App - Overview**
   - Container status
   - CPU and memory usage
   - Database connections
   - Network traffic
   - Recent logs

### Creating Custom Dashboards

1. Open Grafana at http://localhost:3000
2. Login with admin/admin (change password on first login)
3. Click "+" → "Dashboard"
4. Add panels with Prometheus or Loki queries

### Dashboard Examples

**Container CPU Usage:**
```promql
rate(container_cpu_usage_seconds_total{name=~"dating.*"}[5m]) * 100
```

**Memory Usage:**
```promql
container_memory_usage_bytes{name=~"dating.*"} / 1024 / 1024
```

**Database Connections:**
```promql
pg_stat_database_numbackends{datname="dating"}
```

**Log Query (Loki):**
```logql
{container_name=~"dating.*"} |= "error"
```

## 🔔 Alerts

Prometheus is configured with basic alerting rules in `prometheus/alerts.yml`:

- Container down
- High memory usage (>90%)
- High CPU usage (>80%)
- Low disk space (<10%)
- Database connection issues

### Configuring Alertmanager (Optional)

To receive alert notifications:

1. Deploy Alertmanager:
```yaml
# Add to docker-compose.monitoring.yml
alertmanager:
  image: prom/alertmanager:v0.26.0
  ports:
    - "9093:9093"
  volumes:
    - ./monitoring/alertmanager:/etc/alertmanager
```

2. Configure notification channels in `alertmanager/alertmanager.yml`

3. Uncomment alerting section in `prometheus/prometheus.yml`

## 🔧 Configuration

### Prometheus

Edit `prometheus/prometheus.yml` to:
- Add new scrape targets
- Adjust scrape intervals
- Configure service discovery

### Loki

Edit `loki/loki-config.yml` to:
- Change retention period (default: 30 days)
- Adjust storage settings
- Configure limits

### Grafana

- **Datasources**: `grafana/provisioning/datasources/`
- **Dashboards**: `grafana/provisioning/dashboards/`
- **Custom Dashboards**: `grafana/dashboards/`

## 💡 Best Practices

### For Production

1. **Secure Grafana**:
   ```bash
   # Set strong admin password
   docker compose exec grafana grafana-cli admin reset-admin-password newpassword
   ```

2. **Enable HTTPS**: Add Grafana to Traefik with SSL

3. **Set up Alertmanager**: Configure email/Slack notifications

4. **Regular Backups**: Backup Grafana dashboards and Prometheus data

5. **Resource Limits**: Adjust memory limits based on your workload

### For Development

1. Use default credentials (admin/admin)
2. Explore metrics and create custom dashboards
3. Test alert rules locally

## 📦 Storage and Retention

### Data Volumes

- `prometheus_data` - Metrics (30 days retention)
- `grafana_data` - Dashboards and settings
- `loki_data` - Logs (30 days retention)

### Disk Space Management

Monitor disk usage:
```bash
docker system df -v
```

Clean old data:
```bash
# Prometheus retention is configured to 30 days
# Loki retention is configured to 30 days

# To manually clean old data:
docker compose -f docker-compose.monitoring.yml down -v
docker compose -f docker-compose.monitoring.yml up -d
```

## 🐛 Troubleshooting

### Grafana shows "No data"

1. Check if Prometheus is running:
   ```bash
   curl http://localhost:9090/api/v1/targets
   ```

2. Verify datasource configuration in Grafana

3. Check Prometheus logs:
   ```bash
   docker compose logs prometheus
   ```

### High resource usage

1. Reduce scrape intervals in `prometheus.yml`
2. Adjust retention periods
3. Limit the number of metrics collected

### Cannot access dashboards

1. Check if ports are exposed:
   ```bash
   docker compose ps
   ```

2. Verify firewall rules

3. Check container logs for errors

## 📚 Resources

- [Prometheus Documentation](https://prometheus.io/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Loki Documentation](https://grafana.com/docs/loki/)
- [PromQL Basics](https://prometheus.io/docs/prometheus/latest/querying/basics/)
- [LogQL Documentation](https://grafana.com/docs/loki/latest/logql/)

## 🎓 Learning Resources

### Prometheus Query Examples

```promql
# Average CPU usage across all containers
avg(rate(container_cpu_usage_seconds_total[5m])) * 100

# Total memory usage
sum(container_memory_usage_bytes) / 1024 / 1024 / 1024

# Request rate
rate(http_requests_total[5m])

# 95th percentile response time
histogram_quantile(0.95, rate(http_request_duration_seconds_bucket[5m]))
```

### Loki Query Examples

```logql
# All errors
{job="docker"} |= "error"

# Bot container logs
{container_name="dating-bot-1"}

# Database errors
{container_name="dating-db-1"} |= "ERROR"

# Rate of errors per minute
rate({job="docker"} |= "error" [1m])
```

## 🔒 Security Notes

1. Change default Grafana password immediately
2. Restrict access to monitoring ports in production
3. Use authentication for Prometheus in production
4. Consider using Grafana's role-based access control
5. Enable TLS for all monitoring endpoints in production

---

For questions or issues, refer to the main [README.md](../README.md) or create an issue.
