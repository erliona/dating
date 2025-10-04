# Loki Ingester Configuration Fix

## Issue Summary
**Problem:** Grafana dashboard showing "no data" for application logs and events despite Promtail and Bot containers running correctly.

**Root Cause:** Loki's `/ready` endpoint reporting "Ingester not ready: waiting for 15s after being ready" indefinitely because the `ingester` configuration section was missing.

**Impact:** Logs could not be stored or queried, blocking visibility into application logs and metrics.

---

## Solution Overview

This fix adds the missing `ingester` configuration to Loki and implements proper service health checks to ensure correct startup order.

### Architecture Flow

```
┌─────────────────────────────────────────────────────────────┐
│                    BEFORE (Broken)                          │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  Loki starts (no ingester config) ────┐                    │
│                                         │                   │
│  Promtail starts ───────────────────────┼──► Tries to send │
│                                         │    logs but Loki  │
│  Grafana starts ────────────────────────┘    not ready     │
│                                                             │
│  Result: "Ingester not ready" forever                       │
│          No logs stored or visible                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    AFTER (Fixed)                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. Loki starts (with ingester config)                     │
│     └─► Ingester initializes (15-30s)                      │
│     └─► Healthcheck passes ✓                               │
│                                                             │
│  2. Promtail starts (waits for Loki health)                │
│     └─► Discovers containers                               │
│     └─► Sends logs to Loki ✓                               │
│                                                             │
│  3. Grafana starts (waits for Loki health)                 │
│     └─► Connects to Loki datasource ✓                      │
│     └─► Logs visible in dashboards ✓                       │
└─────────────────────────────────────────────────────────────┘
```

---

## Changes Made

### 1. Loki Configuration (`monitoring/loki/loki-config.yml`)

**Added ingester section:**

```yaml
ingester:
  lifecycler:
    address: 127.0.0.1
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
    final_sleep: 0s
  chunk_idle_period: 5m       # Flush idle chunks after 5 minutes
  chunk_retain_period: 30s    # Keep chunks in memory for 30s after flush
  max_transfer_retries: 0
  wal:
    enabled: true             # Write-Ahead Log for durability
    dir: /loki/wal
```

**What this does:**
- `lifecycler`: Manages the ingester's lifecycle in the distributed ring
- `wal.enabled: true`: Ensures no data loss during restarts
- `chunk_idle_period`: Controls when inactive log chunks are flushed to storage
- `chunk_retain_period`: Keeps chunks in memory briefly for efficient queries

### 2. Docker Compose (`docker-compose.yml`)

**Added Loki healthcheck:**

```yaml
loki:
  image: grafana/loki:2.9.3
  healthcheck:
    test: ["CMD-SHELL", "wget --no-verbose --tries=1 --spider http://localhost:3100/ready || exit 1"]
    interval: 10s
    timeout: 5s
    retries: 5
    start_period: 30s    # ← Crucial: allows ingester time to initialize
```

**Updated Promtail dependency:**

```yaml
promtail:
  depends_on:
    loki:
      condition: service_healthy    # ← Wait for Loki to be fully ready
```

**Updated Grafana dependency:**

```yaml
grafana:
  depends_on:
    prometheus:
      condition: service_started
    loki:
      condition: service_healthy    # ← Wait for Loki to be fully ready
```

### 3. Documentation (`monitoring/README.md`)

**Added troubleshooting section:**
- Explained "Ingester not ready" message and normal behavior
- Documented 15-30 second initialization period
- Added validation steps for ingester issues
- Updated Quick Start with healthcheck information

---

## How to Deploy

### For Users Already Running the Application

```bash
# 1. Stop monitoring stack
docker compose --profile monitoring down

# 2. Pull latest changes
git pull origin main

# 3. Start monitoring stack with new configuration
docker compose --profile monitoring up -d

# 4. Wait ~30 seconds and verify Loki is healthy
docker compose ps loki
# Expected output: Up (healthy)

# 5. Verify logs are flowing
curl http://localhost:3100/ready
# Expected output: ready
```

### For New Deployments

No special steps needed! Just start normally:

```bash
docker compose --profile monitoring up -d
```

The healthcheck ensures Loki is ready before Promtail and Grafana start.

---

## Validation Checklist

Use this checklist to verify the fix is working:

- [ ] Loki container status shows "healthy" after ~30 seconds
- [ ] `/ready` endpoint returns "ready" (not "Ingester not ready")
- [ ] Promtail logs show successful connection to Loki
- [ ] Loki logs show "POST /loki/api/v1/push" (receiving data from Promtail)
- [ ] Grafana datasource test shows "Data source is working"
- [ ] Logs visible in Grafana Explore with query `{job="docker"}`
- [ ] Dashboard "Application Logs & Events" shows data

### Quick Validation Commands

```bash
# Check Loki health
docker compose ps loki

# Check Loki ready status
curl http://localhost:3100/ready

# Check Promtail is sending logs
docker compose logs loki | grep "POST /loki/api/v1/push"

# Query logs directly
curl -G -s "http://localhost:3100/loki/api/v1/query" \
  --data-urlencode 'query={job="docker"}' \
  --data-urlencode 'limit=5' \
  | python3 -m json.tool
```

---

## Troubleshooting

### Issue: Loki stays "Ingester not ready" for more than 1 minute

**Solutions:**
1. Check Loki logs for errors:
   ```bash
   docker compose logs loki | tail -50
   ```

2. Verify volume permissions:
   ```bash
   docker compose exec loki ls -la /loki/wal
   ```

3. Restart Loki:
   ```bash
   docker compose restart loki
   ```

### Issue: Promtail not sending logs

**Solutions:**
1. Verify Promtail has discovered containers:
   ```bash
   curl http://localhost:9080/targets | python3 -m json.tool
   ```

2. Check Promtail logs:
   ```bash
   docker compose logs promtail | tail -50
   ```

3. Restart Promtail:
   ```bash
   docker compose restart promtail
   ```

### Issue: Grafana shows "No data"

**Solutions:**
1. Verify Loki datasource is working:
   - Go to Configuration → Data Sources → Loki
   - Click "Save & Test"
   - Should show green "Data source is working"

2. Check time range in Grafana (default: last 6 hours)

3. Try a simpler query in Explore:
   ```logql
   {job="docker"}
   ```

---

## Technical Details

### Why Was This Happening?

Loki has a microservices architecture with several components:
- **Distributor**: Receives logs from clients (Promtail)
- **Ingester**: Writes logs to storage
- **Querier**: Handles log queries

Without the `ingester` configuration:
1. Loki would start but the ingester component wouldn't initialize properly
2. The `/ready` endpoint waits for all components to be ready
3. It would stay in "waiting" state indefinitely
4. Logs couldn't be stored or queried

### Why the 30-Second Start Period?

The ingester has a built-in grace period (`min_ready_duration`) that defaults to 15 seconds. Combined with initialization time, 30 seconds ensures the healthcheck doesn't fail prematurely during normal startup.

### Why Use Healthchecks Instead of `depends_on`?

Simple `depends_on` only waits for the container to start, not for the application to be ready. Using `condition: service_healthy` ensures:
- Loki's ingester is fully initialized
- Promtail won't try to send logs before Loki is ready
- Grafana can immediately connect to a working Loki datasource

---

## Related Documentation

- [Loki Configuration](https://grafana.com/docs/loki/latest/configure/)
- [Loki Ingester](https://grafana.com/docs/loki/latest/get-started/components/#ingester)
- [Monitoring README](./monitoring/README.md)
- [Troubleshooting Loki](https://grafana.com/docs/loki/latest/troubleshooting/)

---

## Questions?

If you encounter issues after applying this fix:

1. Check the troubleshooting section above
2. Review logs: `docker compose logs loki promtail grafana`
3. Verify configuration: `docker compose config --services`
4. Review the [monitoring README](./monitoring/README.md) for detailed troubleshooting steps

---

*This fix resolves the issue reported in: "Logs not visible in Grafana: Loki ingester not ready, no logs in dashboard"*
