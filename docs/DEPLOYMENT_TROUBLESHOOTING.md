# Deployment Troubleshooting Guide

This guide helps resolve common deployment issues for the dating application microservices.

---

## Common Deployment Errors

### 1. Port Already Allocated Errors

**Symptom:**
```
Error: Bind for 0.0.0.0:<port> failed: port is already allocated
```

**Common Ports and Solutions:**

#### Port 80 (HTTP)
**Cause**: Webapp service trying to bind to port 80  
**Status**: ✅ Fixed - webapp is profile-gated by default  
**If you see this error**: The webapp profile might have been accidentally enabled

**Solution:**
```bash
# Option 1: Deploy without webapp (recommended)
docker compose up -d

# Option 2: Use custom port
WEBAPP_PORT=8080 docker compose --profile webapp up -d
```

#### Port 5432 (PostgreSQL)
**Cause**: Database service trying to bind to port 5432  
**Status**: ✅ Fixed - database port not exposed by default  
**If you see this error**: Someone might have uncommented the ports section

**Solution:**
```bash
# Ensure ports section is commented in docker-compose.yml under db service
# Or use a different port for development:
POSTGRES_EXTERNAL_PORT=5433 docker compose up -d
```

#### Port 443 (HTTPS)
**Cause**: Traefik or another reverse proxy  
**Solution**: Check if Traefik is properly configured or disable it

#### Other Application Ports (8080-8085)
**Cause**: Previous containers not cleaned up or conflicting applications  
**Solution:**
```bash
# Stop all containers
docker compose down

# Remove conflicting containers
docker ps -a | grep <port-number>
docker stop <container-id>
docker rm <container-id>

# Restart deployment
docker compose up -d
```

---

## 2. Service Fails to Start

**Symptom:**
```
Service <name> exited with code 1
```

**Diagnosis Steps:**

1. **Check logs:**
   ```bash
   docker compose logs <service-name>
   docker compose logs --tail=100 <service-name>
   ```

2. **Check service status:**
   ```bash
   docker compose ps
   docker inspect <container-name>
   ```

3. **Common causes:**
   - Missing environment variables (BOT_TOKEN, JWT_SECRET)
   - Database not ready (check depends_on and healthcheck)
   - Syntax errors in code
   - Missing dependencies

**Solutions:**

### Missing Environment Variables
```bash
# Check .env file exists
ls -la .env

# Copy from example if needed
cp .env.example .env
nano .env  # Edit with your values

# Required variables:
# - BOT_TOKEN
# - JWT_SECRET
# - POSTGRES_PASSWORD (optional, auto-generated if not set)
```

### Database Connection Issues
```bash
# Check database is running
docker compose ps db

# Check database logs
docker compose logs db

# Wait for database to be ready
docker compose up -d db
sleep 10
docker compose up -d
```

---

## 3. Health Check Failures

**Symptom:**
```
Service <name> is unhealthy
```

**Diagnosis:**
```bash
# Check health status
docker compose ps

# Check health check logs
docker inspect <container-name> | grep -A 10 Health

# Test endpoint manually
curl http://localhost:<port>/health
```

**Common Solutions:**

1. **Service not fully started**: Wait 30-60 seconds and check again
2. **Port not accessible**: Check firewall rules
3. **Service crashed**: Check logs for errors
4. **Database not connected**: Check database connectivity

---

## 4. Network Issues

**Symptom:**
```
Service cannot connect to <other-service>
```

**Solutions:**

1. **Check networks:**
   ```bash
   docker network ls
   docker network inspect dating_default
   docker network inspect dating_monitoring
   ```

2. **Verify service names:**
   - Services connect using service names, not localhost
   - Example: `http://auth-service:8081`, NOT `http://localhost:8081`

3. **Check depends_on:**
   ```bash
   docker compose config | grep -A 5 "depends_on:"
   ```

4. **Restart with clean network:**
   ```bash
   docker compose down
   docker network prune -f
   docker compose up -d
   ```

---

## 5. Volume/Permission Issues

**Symptom:**
```
Permission denied when accessing volume
Cannot write to directory
```

**Solutions:**

1. **Check volume ownership:**
   ```bash
   docker volume ls
   docker volume inspect <volume-name>
   ```

2. **Fix permissions:**
   ```bash
   # For postgres_data
   docker compose down
   docker volume rm dating_postgres_data
   docker compose up -d

   # For media_storage (if needed)
   sudo chown -R 1000:1000 /var/lib/docker/volumes/dating_media_storage
   ```

3. **Clean slate (CAUTION: deletes all data):**
   ```bash
   docker compose down -v
   docker compose up -d
   ```

---

## 6. Build Failures

**Symptom:**
```
ERROR: failed to build <service>
```

**Solutions:**

1. **Check Dockerfile exists:**
   ```bash
   ls -la services/*/Dockerfile gateway/Dockerfile
   ```

2. **Clear build cache:**
   ```bash
   docker compose build --no-cache
   docker compose up -d
   ```

3. **Check disk space:**
   ```bash
   df -h
   docker system df
   
   # Clean up if needed
   docker system prune -a
   ```

4. **Check Python syntax:**
   ```bash
   python3 -m py_compile services/*/main.py
   python3 -m py_compile gateway/main.py
   ```

---

## 7. Monitoring Stack Issues

### Prometheus Not Scraping Metrics
```bash
# Check Prometheus config
cat monitoring/prometheus/prometheus.yml

# Check targets in Prometheus UI
# Visit: http://localhost:9090/targets

# Restart Prometheus
docker compose restart prometheus
```

### Grafana Dashboards Not Loading
```bash
# Check Grafana logs
docker compose logs grafana

# Verify provisioning
ls -la monitoring/grafana/provisioning/

# Login credentials (default):
# Username: admin
# Password: admin
```

### Loki Not Receiving Logs
```bash
# Check Promtail is running
docker compose ps promtail

# Check Promtail config
cat monitoring/promtail/promtail-config.yml

# Verify Promtail can reach Loki
docker compose exec promtail wget -O- http://loki:3100/ready
```

---

## Preventive Measures

### Pre-Deployment Checklist

Before deploying, verify:

1. ✅ All required secrets configured in GitHub
   - DEPLOY_HOST
   - DEPLOY_USER
   - DEPLOY_SSH_KEY
   - BOT_TOKEN
   - JWT_SECRET

2. ✅ .env file configured locally (for local deployment)
   ```bash
   cp .env.example .env
   # Edit .env with your values
   ```

3. ✅ Docker and Docker Compose installed
   ```bash
   docker --version
   docker compose version
   ```

4. ✅ Sufficient disk space
   ```bash
   df -h
   # Need at least 5GB free
   ```

5. ✅ No port conflicts
   ```bash
   # Check if ports are in use
   netstat -tuln | grep -E ':(80|5432|8080|8081|8082|8083|8084|8085|3000|9090)'
   ```

6. ✅ Configuration validated
   ```bash
   docker compose config
   ```

---

## Quick Fixes

### Complete Reset (Nuclear Option)
**WARNING**: This deletes all data and containers

```bash
# Stop everything
docker compose down -v

# Clean Docker system
docker system prune -a --volumes -f

# Clean networks
docker network prune -f

# Start fresh
docker compose up -d
```

### Restart Single Service
```bash
# Restart without rebuilding
docker compose restart <service-name>

# Restart with rebuild
docker compose up -d --build <service-name>
```

### View All Logs
```bash
# All services
docker compose logs -f

# Specific service
docker compose logs -f <service-name>

# Last 100 lines
docker compose logs --tail=100
```

---

## Getting Help

### Collect Debug Information

Before asking for help, collect:

1. **Configuration:**
   ```bash
   docker compose config > debug-compose-config.yml
   ```

2. **Service status:**
   ```bash
   docker compose ps > debug-ps.txt
   ```

3. **Logs:**
   ```bash
   docker compose logs > debug-logs.txt
   docker compose logs <failing-service> > debug-service.txt
   ```

4. **System info:**
   ```bash
   docker version > debug-docker.txt
   docker info >> debug-docker.txt
   df -h > debug-disk.txt
   ```

### Useful Commands

```bash
# Check what's using a port
lsof -i :<port>
netstat -tuln | grep <port>

# Check Docker resource usage
docker stats

# Check service resource usage
docker compose stats

# Check volume usage
docker system df -v

# Validate docker-compose.yml
docker compose config

# List all networks
docker network ls

# Inspect a network
docker network inspect <network-name>

# List all volumes
docker volume ls

# Inspect a volume
docker volume inspect <volume-name>
```

---

## Related Documentation

- **Historical Port Conflict Fixes**: `docs/archive/` (archived bug fixes and deployment summaries)
- **Port Mapping**: `docs/PORT_MAPPING.md`
- **CI/CD Guide**: `docs/CI_CD_GUIDE.md`
- **Monitoring Setup**: `docs/MONITORING_SETUP.md`
- **Admin Panel Guide**: `docs/ADMIN_PANEL_GUIDE.md`

---

**Last Updated**: January 2025  
**Maintained By**: Development Team
