# Monitoring Quick Start Guide

## 🚀 1-Minute Setup

```bash
# Start application with monitoring
docker compose --profile monitoring up -d

# Wait for services to start (30 seconds)
sleep 30

# Validate monitoring setup (if script exists)
./scripts/validate-monitoring.sh 2>/dev/null || echo "Validation script not found, skipping"
```

## 📊 Access Dashboards

| Service | URL | Default Credentials |
|---------|-----|---------------------|
| Grafana | http://localhost:3000 | admin / admin |
| Prometheus | http://localhost:9090 | - |
| cAdvisor | http://localhost:8081 | - |

## 🎯 Quick Tasks

### View Application Metrics

1. Open Grafana: http://localhost:3000
2. Login with `admin/admin` (change password when prompted)
3. Navigate to: **Dashboards** → **Dating App - Overview**

### Check Container Resources

```bash
# Real-time resource usage
docker stats

# Container health status
docker compose ps
```

### View Logs

**In Grafana:**
1. Open Grafana
2. Go to **Explore** (compass icon)
3. Select **Loki** datasource
4. Query examples:
   ```logql
   {container_name=~"dating.*"}              # All app logs
   {container_name="dating-bot-1"}           # Bot logs
   {container_name=~"dating.*"} |= "error"   # Errors only
   ```

**Via Docker:**
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f bot
```

### Query Metrics

**In Prometheus:**
Open http://localhost:9090 and try these queries:

```promql
# CPU usage per container
rate(container_cpu_usage_seconds_total[5m]) * 100

# Memory usage
container_memory_usage_bytes / 1024 / 1024

# Database connections
pg_stat_database_numbackends

# Container status
up
```

## 🔔 Check Alerts

```bash
# View active alerts
curl http://localhost:9090/api/v1/alerts | jq

# View alert rules
curl http://localhost:9090/api/v1/rules | jq
```

## 🛠️ Common Commands

```bash
# Restart monitoring services
docker compose restart prometheus grafana loki

# View monitoring logs
docker compose logs prometheus grafana loki

# Stop monitoring (keeps data)
docker compose stop prometheus grafana loki promtail cadvisor

# Remove monitoring (deletes data)
docker compose --profile monitoring down -v
```

## 📈 What to Monitor

### Performance
- **CPU Usage**: Keep below 80%
- **Memory Usage**: Keep below 90%
- **Disk Space**: Keep above 20%

### Application
- **Database Connections**: Monitor for leaks
- **Response Times**: Track performance
- **Error Rates**: Watch for spikes

### Availability
- **Container Status**: All should be "Up"
- **Health Checks**: All should be "healthy"
- **Service Uptime**: Track downtime

## 🚨 Troubleshooting

### Grafana shows "No data"

```bash
# Check Prometheus
curl http://localhost:9090/-/healthy

# Check Grafana datasources
curl -u admin:admin http://localhost:3000/api/datasources
```

### Prometheus has no targets

```bash
# Check if exporters are running
docker compose ps cadvisor node-exporter postgres-exporter

# Check Prometheus config
docker compose exec prometheus cat /etc/prometheus/prometheus.yml
```

### High resource usage

```bash
# Check resource usage
docker stats

# Reduce scrape intervals in monitoring/prometheus/prometheus.yml
# Reduce retention in docker-compose.yml (prometheus service)
```

## 📚 Learn More

- [Full Documentation](README.md)
- [Architecture Diagram](ARCHITECTURE.md)
- [Alert Configuration](prometheus/alerts.yml)
- [Grafana Provisioning](grafana/provisioning/)

## 💡 Pro Tips

1. **Change Grafana password immediately** in production
2. **Set up email/Slack alerts** for critical issues
3. **Create custom dashboards** for your metrics
4. **Export dashboards regularly** for backup
5. **Monitor disk space** - logs and metrics can grow

## 🎓 Useful Resources

### PromQL Examples

```promql
# 95th percentile CPU usage
histogram_quantile(0.95, rate(container_cpu_usage_seconds_total[5m]))

# Memory limit usage percentage
(container_memory_usage_bytes / container_spec_memory_limit_bytes) * 100

# Network traffic rate
rate(container_network_transmit_bytes_total[5m])
```

### LogQL Examples

```logql
# Count errors per minute
count_over_time({container_name=~"dating.*"} |= "error" [1m])

# Filter by log level
{container_name="dating-bot-1"} | json | level="ERROR"

# Search in message content
{job="docker"} |~ "(?i)exception|fatal|critical"
```

## 🔒 Production Checklist

- [ ] Change default Grafana password
- [ ] Set up HTTPS for Grafana
- [ ] Configure Alertmanager
- [ ] Set up notification channels (email, Slack)
- [ ] Create backup strategy for dashboards
- [ ] Set appropriate retention periods
- [ ] Restrict access to monitoring ports
- [ ] Enable authentication on Prometheus
- [ ] Monitor monitoring stack itself
- [ ] Document custom dashboards and alerts

---

Need help? Check the [main documentation](README.md) or create an issue.
