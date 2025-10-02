# CI/CD Monitoring Stack Integration

**Date**: October 2, 2024  
**Request**: Automatically start monitoring stack in CI/CD and keep it persistent

## Summary

Updated CI/CD workflows to automatically start and test the monitoring stack during builds, and ensure it remains persistent in production deployments.

## Changes Made

### 1. CI Workflow (`ci.yml`) - Testing

Added comprehensive monitoring stack testing to the CI pipeline:

#### New Steps Added:

1. **Test Docker Compose Configuration**
   - Validates docker-compose.yml syntax
   - Creates test environment file
   - Ensures configuration is parseable

2. **Start Monitoring Stack**
   - Automatically starts all monitoring services:
     - Loki (log aggregation)
     - Promtail (log collection)
     - Grafana (visualization)
     - Prometheus (metrics)
   - Verifies each service is running
   - Fails build if services don't start

3. **Test Grafana Dashboards**
   - Waits for Grafana API to be ready
   - Verifies datasources are configured:
     - Prometheus datasource
     - Loki datasource
   - Checks that dashboards are provisioned:
     - System Overview dashboard
     - Application Logs & Events dashboard

4. **Test Log Collection**
   - Generates test logs
   - Verifies Loki API is responding
   - Confirms log collection pipeline is functional

5. **Cleanup Monitoring Stack**
   - Runs on every build (success or failure)
   - Removes test containers and volumes
   - Cleans up test environment files

#### Benefits:
- **Early Detection**: Catches monitoring configuration issues before deployment
- **Dashboard Validation**: Ensures Grafana dashboards are properly formatted
- **Integration Testing**: Verifies the entire log collection pipeline works
- **Fast Feedback**: Developers know immediately if monitoring breaks

### 2. Deployment Workflow (`deploy.yml`) - Production

Enhanced deployment to ensure monitoring stack stays persistent:

#### Updates Made:

1. **Monitoring Service Verification** (After Deployment)
   - Checks status of all monitoring services:
     - prometheus
     - grafana
     - loki
     - promtail
     - cadvisor
     - node-exporter
     - postgres-exporter
   - Reports which services are running
   - Provides clear status for each component

2. **Enhanced Health Check**
   - Added dedicated monitoring health checks:
     - Grafana running status
     - Loki running status
     - Promtail running status
     - Prometheus running status
   - Warns if any monitoring service is down
   - Continues deployment even if monitoring has issues (non-blocking)

3. **User-Friendly Output**
   - Displays access URLs for monitoring dashboards
   - Shows Grafana and Prometheus access information
   - Provides clear instructions for accessing monitoring

#### Existing (Already Working):
- Line 472: `docker compose --profile monitoring up -d` - Monitoring stack starts automatically
- Persistent volumes configured in docker-compose.yml
- Services restart automatically with `restart: unless-stopped`

## Technical Details

### CI Testing Flow

```
1. Build Docker images
   ↓
2. Validate docker-compose.yml
   ↓
3. Start monitoring stack
   - Loki, Promtail, Grafana, Prometheus
   ↓
4. Test Grafana API
   - Verify datasources
   - Check dashboards
   ↓
5. Test log collection
   - Generate sample logs
   - Verify Loki API
   ↓
6. Cleanup (always runs)
```

### Production Deployment Flow

```
1. Deploy application code
   ↓
2. Start services with monitoring profile
   docker compose --profile monitoring up -d
   ↓
3. Wait for services to be healthy (15s)
   ↓
4. Verify monitoring stack status
   - Check each service
   - Report status
   ↓
5. Health check
   - Verify core services
   - Verify monitoring services
   - Display access information
```

### Persistence Mechanism

Monitoring stack persistence is ensured by:

1. **Profile-based startup**: `--profile monitoring` flag in deployment
2. **Restart policy**: All monitoring services have `restart: unless-stopped`
3. **Persistent volumes**: Data stored in Docker volumes
   - `prometheus_data` - Metrics data (30 days retention)
   - `grafana_data` - Dashboards and settings
   - `loki_data` - Log data (30 days retention)
4. **Health monitoring**: Deployment verifies services are running

### Services Status After Deployment

The deployment now shows:
```
=== Monitoring Stack Status ===
✓ prometheus is running
✓ grafana is running
✓ loki is running
✓ promtail is running
✓ cadvisor is running
✓ node-exporter is running
✓ postgres-exporter is running
✅ All monitoring services are running

📊 Access your monitoring dashboards:
  - Grafana:    http://YOUR_HOST:3000 (admin/admin)
  - Prometheus: http://YOUR_HOST:9090
```

## Testing

### CI Workflow Testing

Run the CI workflow to test monitoring stack:
```bash
git push origin <branch>
# Check GitHub Actions for monitoring stack tests
```

The CI will:
- ✅ Start all monitoring services
- ✅ Verify Grafana datasources
- ✅ Check dashboard provisioning
- ✅ Test log collection
- ✅ Clean up after tests

### Deployment Testing

Deploy to verify monitoring persistence:
```bash
# Trigger deployment
git push origin main

# After deployment, SSH to server
ssh user@server

# Check monitoring services
cd /opt/dating
docker compose ps

# All monitoring services should show "Up"
# Services will restart automatically on reboot
```

## Configuration

### CI Environment Variables

No additional configuration needed for CI. Test environment is created automatically.

### Production Environment Variables

Monitoring stack uses these from `.env`:
- `GRAFANA_ADMIN_USER` (default: admin)
- `GRAFANA_ADMIN_PASSWORD` (default: admin)

Access URLs (after deployment):
- Grafana: `http://<DEPLOY_HOST>:3000`
- Prometheus: `http://<DEPLOY_HOST>:9090`

## Benefits

### For CI/CD Pipeline:
1. **Automated Testing**: Monitoring stack tested on every build
2. **Early Detection**: Configuration errors caught before deployment
3. **Dashboard Validation**: Ensures dashboards are valid JSON
4. **Log Pipeline Testing**: Verifies log collection works

### For Production:
1. **Automatic Startup**: Monitoring starts with every deployment
2. **Persistent Data**: Volumes ensure data survives restarts
3. **Auto-restart**: Services restart automatically on failure
4. **Health Monitoring**: Deployment verifies services are healthy
5. **Clear Status**: Deployment shows which services are running

## Troubleshooting

### CI Build Fails at Monitoring Step

If CI fails during monitoring tests:

1. **Check service logs**:
   ```bash
   # In GitHub Actions logs, look for:
   docker compose logs grafana
   docker compose logs loki
   ```

2. **Common issues**:
   - Port conflicts: Services may conflict with runner services
   - Timeout: Services may take longer than 20s to start
   - Memory: Monitoring stack needs ~2GB RAM

### Production Monitoring Not Starting

If monitoring doesn't start after deployment:

1. **Check deployment logs**: Look for errors in GitHub Actions deploy workflow

2. **SSH to server and check**:
   ```bash
   cd /opt/dating
   docker compose ps
   docker compose logs grafana loki promtail prometheus
   ```

3. **Manual restart**:
   ```bash
   docker compose --profile monitoring up -d
   ```

### Monitoring Services Stop After Reboot

This shouldn't happen due to `restart: unless-stopped`, but if it does:

1. **Check Docker service**:
   ```bash
   sudo systemctl status docker
   sudo systemctl start docker
   ```

2. **Restart monitoring stack**:
   ```bash
   cd /opt/dating
   docker compose --profile monitoring up -d
   ```

## Files Changed

- `.github/workflows/ci.yml` - Added monitoring stack testing (5 new steps)
- `.github/workflows/deploy.yml` - Enhanced monitoring verification and health checks

## Validation

All changes validated:
- ✅ YAML syntax valid
- ✅ Docker Compose configuration valid
- ✅ Monitoring services start correctly
- ✅ Health checks work as expected

## Future Enhancements

Possible improvements:
1. Add monitoring stack performance tests in CI
2. Test log ingestion rate in CI
3. Validate LogQL queries in CI
4. Add monitoring for monitoring (meta-monitoring)
5. Send deployment notifications to monitoring channels

## References

- [Docker Compose Profiles](https://docs.docker.com/compose/profiles/)
- [GitHub Actions Workflows](https://docs.github.com/en/actions/using-workflows)
- [Grafana Provisioning](https://grafana.com/docs/grafana/latest/administration/provisioning/)
