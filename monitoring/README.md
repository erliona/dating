# 📊 Dating App Monitoring & Debugging

Comprehensive monitoring setup using Grafana, Prometheus, Loki, and Promtail for system metrics and log aggregation.

## 🎯 Components

### Metrics Collection
- **Prometheus** - Time-series database for metrics
- **cAdvisor** - Container metrics collector
- **Node Exporter** - System/host metrics
- **Postgres Exporter** - Database metrics

### Visualization
- **Grafana** - Dashboards and visualization with 3 pre-configured dashboards

### Logging
- **Loki** - Log aggregation system (30-day retention)
- **Promtail** - Log shipper with automatic JSON parsing

## 🚀 Quick Start

### Deploy with Monitoring

```bash
# Start main application with monitoring stack (recommended)
docker compose --profile monitoring up -d

# Or for development with monitoring
docker compose -f docker-compose.dev.yml --profile monitoring up -d
```

### Access Dashboards

- **Grafana**: http://localhost:3000
  - Default credentials: `admin` / `admin` (change on first login)
  - Pre-configured dashboards available immediately
- **Prometheus**: http://localhost:9090
- **cAdvisor**: http://localhost:8081

### Stop Monitoring Stack

```bash
# Stop all services including monitoring
docker compose --profile monitoring down

# Remove monitoring data volumes (⚠️ this deletes all metrics and logs)
docker compose down -v
```

## 📈 Available Dashboards

### 1. System Overview Dashboard
**Path**: Home > Dating App - System Overview

**Metrics**:
- Services status (up/down)
- Container CPU usage
- Container memory usage
- PostgreSQL active connections
- Network traffic
- All container logs
- Bot application logs (JSON parsed)
- Bot error and warning logs
- Bot events timeline

### 2. Debug Dashboard (✨ NEW)
**Path**: Home > Dating App - Debug Dashboard

**Perfect for troubleshooting and debugging!**

**Features**:
- **Live Application Logs**: Real-time logs from all bot services with JSON parsing
- **Error Logs Only**: Filtered view of ERROR and CRITICAL logs with full context (logger, function, line number)
- **Warning Logs**: Separate panel for warning-level logs
- **Log Levels Distribution**: Time series chart showing log volume by level over time
- **Events Timeline**: Track specific events by type (profile_created, user_updated, photo_uploaded, match_created, etc.)
- **Service Health Indicators**: 
  - Bot service status (up/down)
  - CPU usage gauge with thresholds
  - Memory usage gauge with thresholds
  - Database connections counter
- **API Requests Panel**: Log view of all HTTP requests and responses
- **Database Queries Panel**: Track database operations from repository logs
- **User Actions Panel**: Monitor user-facing events (profiles, matches, likes, photos)

**Auto-refresh**: 30 seconds  
**Default time range**: Last 1 hour

### 3. Business Metrics Dashboard
**Path**: Home > Dating App - Business Metrics

**Metrics**:
- User registrations
- Profile completions
- Matches created
- Photo uploads
- Active users
- Business KPIs

## 🔍 Log Query Examples

All logs from the bot are structured JSON with the following fields:
- `timestamp`: ISO 8601 timestamp
- `level`: Log level (INFO, WARNING, ERROR, CRITICAL)
- `logger`: Logger name (e.g., bot.main, bot.repository, bot.media)
- `message`: Human-readable log message
- `module`: Python module name
- `function`: Function name where log was generated
- `line`: Line number in source code
- `event_type`: Optional event type for filtering (e.g., "profile_created", "photo_uploaded")
- Custom fields depending on context (user_id, filename, safe_score, etc.)

### Common LogQL Queries (for Loki)

#### View all bot logs
```logql
{container_name=~".*bot.*"}
```

#### View only errors and critical logs
```logql
{container_name=~".*bot.*"} | json | level =~ "ERROR|CRITICAL"
```

#### View specific event types
```logql
{container_name=~".*bot.*"} | json | event_type = "profile_created"
```

#### View logs for specific user
```logql
{container_name=~".*bot.*"} | json | user_id = "12345"
```

#### View all photo-related events
```logql
{container_name=~".*bot.*"} | json | event_type =~ "photo_.*"
```

#### View NSFW rejection events
```logql
{container_name=~".*bot.*"} | json | event_type = "photo_rejected_nsfw"
```

#### View database operations
```logql
{container_name=~".*bot.*"} | json | logger =~ ".*repository.*|.*db.*"
```

#### View API requests and responses
```logql
{container_name=~".*bot.*"} | json | event_type =~ ".*request.*|.*response.*"
```

#### Count logs by level over time
```logql
sum by (level) (count_over_time({container_name=~".*bot.*"} | json [1m]))
```

## 🐛 Debugging Workflows

### Troubleshooting User Issues

1. **Find all actions for a user**:
   - Open **Debug Dashboard**
   - Go to **Explore** in Grafana
   - Query:
     ```logql
     {container_name=~".*bot.*"} | json | user_id = "<USER_ID>"
     ```

2. **Check for errors specific to user**:
   ```logql
   {container_name=~".*bot.*"} | json | user_id = "<USER_ID>" | level = "ERROR"
   ```

3. **Track user's profile creation flow**:
   ```logql
   {container_name=~".*bot.*"} | json | user_id = "<USER_ID>" | event_type =~ "profile_.*"
   ```

### Investigating Performance Issues

1. Open **Debug Dashboard**
2. Check **Bot CPU Usage** gauge - should be < 80%
3. Check **Bot Memory Usage** gauge - should be < 90%
4. Review **Database Connections** - high count may indicate connection leaks
5. Correlate with **Log Levels Distribution** for spike in errors during performance issues
6. Check **Events Timeline** for unusual activity patterns

### Analyzing Photo Upload Issues

1. **Use Debug Dashboard "User Actions" panel** or query:
   ```logql
   {container_name=~".*bot.*"} | json | event_type =~ "photo_.*"
   ```

2. **Check for NSFW rejections**:
   ```logql
   {container_name=~".*bot.*"} | json | event_type = "photo_rejected_nsfw"
   ```

3. **Look for EXIF removal operations**:
   ```logql
   {container_name=~".*bot.*"} | json | event_type = "exif_removal_success"
   ```

4. **Check for upload errors**:
   ```logql
   {container_name=~".*bot.*"} | json | level = "ERROR" | message =~ ".*photo.*|.*upload.*"
   ```

### Tracking Match Algorithm Performance

**View all match-related events**:
```logql
{container_name=~".*bot.*"} | json | event_type =~ "match_.*"
```

**Count matches created per time window**:
```logql
sum(count_over_time({container_name=~".*bot.*"} | json | event_type = "match_created" [5m]))
```

### Debugging API Endpoints

1. **View all API requests in last hour**:
   - Open **Debug Dashboard**
   - Check **API Requests by Endpoint** panel

2. **Find slow requests** (in Explore):
   ```logql
   {container_name=~".*bot.*"} | json | event_type = "request" | duration > 1000
   ```

## 📊 Available Metrics (Prometheus)
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

**Important**: Loki logs require Promtail to be running to collect Docker container logs. Ensure you start the monitoring stack as shown in Quick Start above.

## 📈 Grafana Dashboards

### Pre-configured Dashboards

1. **Dating App - System Overview**
   - Services status (all monitoring components)
   - Container CPU and memory usage
   - PostgreSQL active connections
   - Container network traffic
   - All container logs
   - Bot application logs (JSON parsed)
   - Bot error and warning logs
   - Bot events timeline

2. **Dating App - Application Logs & Events**
   - Bot lifecycle events count
   - Error and warning log counts
   - Total log entries
   - Log levels over time
   - Event types over time
   - Recent bot logs with JSON parsing
   - Detailed bot logs with metadata

### Structured Logging

The bot application uses **JSON structured logging** for better log parsing and analysis in Grafana:

```json
{
  "timestamp": "2024-10-02T12:36:09.468968Z",
  "level": "INFO",
  "logger": "bot.main",
  "message": "Configuration loaded successfully",
  "module": "main",
  "function": "main",
  "line": 67,
  "event_type": "config_loaded",
  "webapp_url": "https://example.com",
  "database_configured": true
}
```

This allows Grafana to:
- Filter logs by level (INFO, WARNING, ERROR)
- Extract event types for tracking
- Parse metadata fields
- Create time-series visualizations from logs

### Creating Custom Dashboards

1. Open Grafana at http://localhost:3000
2. Login with admin/admin (change password on first login)
3. Click "+" → "Dashboard"
4. Add panels with Prometheus or Loki queries

### Dashboard Query Examples

**Container CPU Usage:**
```promql
rate(container_cpu_usage_seconds_total{name=~".+"}[5m]) * 100
```

**Memory Usage:**
```promql
container_memory_usage_bytes{name=~".+"} / 1024 / 1024
```

**Database Connections:**
```promql
pg_stat_database_numbackends{datname!=""}
```

**All Bot Logs (Loki):**
```logql
{job="docker", container_name=~".*bot.*"}
```

**Bot JSON Logs with Parsing:**
```logql
{job="docker", container_name=~".*bot.*"} | json | line_format "[{{.level}}] {{.message}}"
```

**Error Logs Only:**
```logql
{job="docker", container_name=~".*bot.*"} | json | level="ERROR"
```

**Bot Events:**
```logql
{job="docker", container_name=~".*bot.*"} | json | event_type!=""
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
# Add to docker-compose.yml under the monitoring profile
alertmanager:
  image: prom/alertmanager:v0.26.0
  profiles: ["monitoring"]
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
docker compose --profile monitoring down -v
docker compose --profile monitoring up -d
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

### Loki logs not visible in Grafana

**Problem**: The "Recent Logs" panel in Grafana shows "No data" or logs are not appearing.

**Root Causes & Solutions**:

1. **Monitoring stack not started properly**
   
   The monitoring components (Loki, Promtail) must be explicitly started:
   ```bash
   # Start with the monitoring profile
   docker compose --profile monitoring up -d
   
   # Verify Loki and Promtail are running
   docker compose ps loki promtail
   ```
   
   Both should show status: "Up"

2. **Promtail not collecting logs**
   
   Check Promtail logs to verify it's working:
   ```bash
   docker compose logs promtail | tail -50
   ```
   
   You should see messages like:
   - "Starting Promtail"
   - "client: connected" or "client/client.go" messages
   - "Seeked" messages indicating it's reading log files
   - No errors about file permissions or "no such file"
   
   If you see errors about Docker socket or container discovery, restart Promtail:
   ```bash
   docker compose restart promtail
   ```

3. **Docker socket permissions**
   
   Promtail uses Docker service discovery to automatically find containers. Verify it has access:
   ```bash
   docker compose logs promtail | grep -i "permission\|error\|discovery"
   ```
   
   Common issues:
   - Docker socket not accessible: Make sure `/var/run/docker.sock` is mounted
   - Container path issues: Promtail uses Docker API to find log files

4. **Loki datasource not configured**
   
   In Grafana (http://localhost:3000):
   - Go to Configuration → Data Sources
   - Find "Loki"
   - Click "Save & Test" 
   - Should show green "Data source is working"
   
   If the test fails:
   - Check Loki is running: `docker compose ps loki`
   - Check Loki logs: `docker compose logs loki | tail -20`
   - Verify URL is correct: `http://loki:3100`

5. **Test Loki directly**
   
   Query Loki API to verify it's receiving logs:
   ```bash
   # Check if Loki is ready
   curl http://localhost:3100/ready
   
   # Query for logs
   curl -G -s "http://localhost:3100/loki/api/v1/query" \
     --data-urlencode 'query={job="docker"}' \
     --data-urlencode 'limit=10' \
     | python3 -m json.tool
   ```
   
   You should see:
   - `/ready` returns "ready"
   - Query returns `"status": "success"` and some log entries

6. **Check Loki storage**
   
   Verify Loki has write permissions and is storing logs:
   ```bash
   # Check for errors
   docker compose logs loki | grep -i "error\|permission"
   
   # Check if Loki is accepting data
   docker compose logs loki | grep -i "POST /loki/api/v1/push"
   ```
   
   If you see "POST /loki/api/v1/push" messages, Promtail is successfully sending logs to Loki.

7. **Use correct LogQL queries**
   
   In Grafana Explore, try these queries:
   ```logql
   # All Docker container logs
   {job="docker"}
   
   # Bot service logs specifically
   {container_name=~".*bot.*"}
   
   # Specific container by name
   {container_name="dating-bot-1"}
   
   # Filter by log content
   {job="docker"} |= "ERROR"
   {container_name=~".*bot.*"} |= "profile"
   
   # Webapp logs
   {container_name=~".*webapp.*"}
   
   # All logs from dating project
   {job="docker"} | json
   ```

8. **Restart monitoring stack**
   
   If logs are still not appearing, restart the monitoring services:
   ```bash
   # Restart Loki and Promtail
   docker compose restart loki promtail
   
   # Wait 10-15 seconds for services to stabilize
   sleep 15
   
   # Check logs to verify they're working
   docker compose logs --tail=50 loki promtail
   ```

**Quick Verification Checklist**:
- [ ] Started with monitoring profile (`--profile monitoring`)
- [ ] Loki container is running (`docker compose ps loki`)
- [ ] Promtail container is running (`docker compose ps promtail`)
- [ ] No errors in Promtail logs about Docker socket or discovery
- [ ] Promtail logs show "Seeked" messages (reading files)
- [ ] Loki logs show "POST /loki/api/v1/push" (receiving data)
- [ ] Loki datasource shows "Working" in Grafana
- [ ] Test query `{job="docker"}` returns logs in Explore

**Advanced debugging**:

Check Promtail targets:
```bash
# Promtail exposes its targets on port 9080
curl http://localhost:9080/targets | python3 -m json.tool
```

This shows which containers Promtail discovered and is scraping.

**Still not working?**

1. Check Docker Compose project name:
   ```bash
   docker compose ps --format json | python3 -m json.tool | grep -i project
   ```
   
   The project name should be "dating". If it's different, update the filter in `promtail-config.yml`.

2. Verify container logs are being written:
   ```bash
   # Check bot container is producing logs
   docker compose logs bot --tail=10
   
   # Check actual Docker log file exists
   docker inspect $(docker compose ps -q bot) | grep LogPath
   ```

3. Complete restart of monitoring stack:
   ```bash
   # Stop monitoring services
   docker compose --profile monitoring down
   
   # Start them again
   docker compose --profile monitoring up -d
   
   # Follow logs to see startup
   docker compose logs -f loki promtail
   ```
   
   Press Ctrl+C when you see "client connected" or "Seeked" messages from Promtail.

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
