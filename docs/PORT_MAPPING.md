# Port Mapping Documentation

This document provides a comprehensive overview of all port allocations used in the Dating Application infrastructure.

## Overview

All ports are carefully allocated to avoid conflicts. This document serves as the single source of truth for port assignments across the entire project.

---

## Application Services (8080-8086)

These are the main microservices that power the dating application.

**Security Note:** Only the API Gateway is exposed externally. All other microservices are accessible only within the Docker internal network for enhanced security.

| Port | Service | Internal Port | Description | External Access | Health Check |
|------|---------|---------------|-------------|-----------------|--------------|
| 8080 | API Gateway | 8080 | Main entry point, routes requests to microservices | ✅ Exposed | `/health` |
| 8081 | Auth Service | 8081 | JWT authentication and session management | 🔒 Internal only | `/health` |
| 8082 | Profile Service | 8082 | User profile management | 🔒 Internal only | `/health` |
| 8083 | Discovery Service | 8083 | Matching algorithms and recommendations | 🔒 Internal only | `/health` |
| 8084 | Media Service | 8084 | Photo upload and processing | 🔒 Internal only | `/health` |
| 8085 | Chat Service | 8085 | Real-time messaging via WebSocket | 🔒 Internal only | `/health` |
| 8086 | Admin Service | 8086 | Admin panel for system management | 🔒 Internal only | `/health` |

**Network Architecture:**
- **API Gateway (8080)**: The only service with external port exposure via `ports` mapping
- **Microservices (8081-8086)**: Use `expose` directive for internal Docker network access only
- All microservices communicate through Docker's internal network
- External requests must go through the API Gateway

**All service ports are configurable via environment variables:**
- `GATEWAY_PORT=8080` - API Gateway port (externally exposed)
- `AUTH_SERVICE_PORT=8081` - Auth Service port (internal only)
- `PROFILE_SERVICE_PORT=8082` - Profile Service port (internal only)
- `DISCOVERY_SERVICE_PORT=8083` - Discovery Service port (internal only)
- `MEDIA_SERVICE_PORT=8084` - Media Service port (internal only)
- `CHAT_SERVICE_PORT=8085` - Chat Service port (internal only)
- `ADMIN_SERVICE_PORT=8086` - Admin Service port (internal only)

**Service URLs (for gateway routing - internal network):**
- `AUTH_SERVICE_URL=http://auth-service:8081`
- `PROFILE_SERVICE_URL=http://profile-service:8082`
- `DISCOVERY_SERVICE_URL=http://discovery-service:8083`
- `MEDIA_SERVICE_URL=http://media-service:8084`
- `CHAT_SERVICE_URL=http://chat-service:8085`
- `ADMIN_SERVICE_URL=http://admin-service:8086`

**Example: Custom port configuration**
```bash
# Change the API Gateway external port (only externally exposed service)
GATEWAY_PORT=9080 docker compose up -d

# Change internal service ports (still internal-only, just different ports within Docker network)
AUTH_SERVICE_PORT=9081 PROFILE_SERVICE_PORT=9082 docker compose up -d

# Or set all ports via .env file
cat > .env << EOF
GATEWAY_PORT=9080          # External port
AUTH_SERVICE_PORT=9081     # Internal only
PROFILE_SERVICE_PORT=9082  # Internal only
EOF
docker compose up -d
```

**Note:** Changing service port environment variables only affects their internal Docker network ports. Only the API Gateway port is exposed externally to the host.

---

## Monitoring Stack (3000-3100, 8090, 9090-9187)

These services collect, store, and visualize metrics and logs.

| Port | Service | Internal Port | Description | Access |
|------|---------|---------------|-------------|--------|
| 3000 | Grafana | 3000 | Visualization and dashboards | Web UI: http://localhost:3000<br/>Login: admin/admin |
| 3100 | Loki | 3100 | Log aggregation and storage | API: http://localhost:3100 |
| 8090 | cAdvisor | 8080 | Container metrics collection | Web UI: http://localhost:8090 |
| 9090 | Prometheus | 9090 | Metrics collection and storage | Web UI: http://localhost:9090 |
| 9100 | Node Exporter | 9100 | System/host metrics | Metrics: http://localhost:9100/metrics |
| 9187 | Postgres Exporter | 9187 | Database metrics | Metrics: http://localhost:9187/metrics |

**Note:** cAdvisor exposes port 8080 internally but maps to 8090 externally to avoid conflict with api-gateway.

**All monitoring service ports are configurable via environment variables:**
- `GRAFANA_PORT=3000` - Grafana dashboard port
- `GRAFANA_ADMIN_PASSWORD=admin` - Grafana admin password
- `LOKI_PORT=3100` - Loki log aggregation port
- `CADVISOR_PORT=8090` - cAdvisor container metrics port
- `PROMETHEUS_PORT=9090` - Prometheus metrics port
- `NODE_EXPORTER_PORT=9100` - Node Exporter system metrics port
- `POSTGRES_EXPORTER_PORT=9187` - Postgres Exporter database metrics port

---

## Database (5432)

| Port | Service | Internal Port | Description | Exposure |
|------|---------|---------------|-------------|----------|
| 5432 | PostgreSQL | 5432 | Primary database | **Internal only** - Not exposed to host |

**Database Connection (from containers):**
```
postgresql+asyncpg://dating:dating@db:5432/dating
```

**Security Note:** The database port is intentionally NOT exposed to the host for security. Microservices access it via Docker's internal network.

**For Local Development:** If you need external database access for debugging, uncomment the ports section in `docker-compose.yml`:
```yaml
db:
  ports:
    - "${POSTGRES_EXTERNAL_PORT:-5433}:5432"
```

---

## Optional Services

| Port | Service | Internal Port | Description | Status |
|------|---------|---------------|-------------|--------|
| 80 | WebApp (nginx) | 80 | Static web files | Profile-gated (`--profile webapp`) |

**Enable with:**
```bash
docker compose --profile webapp up -d
```

**Alternative Port:** Set `WEBAPP_PORT` environment variable:
```bash
WEBAPP_PORT=8888 docker compose --profile webapp up -d
```

---

## Log Shippers (Internal Only)

These services don't expose ports to the host:

| Service | Purpose | Destination |
|---------|---------|-------------|
| Promtail | Docker log collection | Sends to Loki (3100) |

---

## Port Ranges Summary

| Range | Purpose | Services |
|-------|---------|----------|
| 80-80 | Web serving | WebApp (optional) |
| 3000-3999 | Monitoring UIs | Grafana (3000), Loki (3100) |
| 5432 | Database | PostgreSQL (internal only) |
| 8080-8089 | Application | API Gateway, Auth, Profile, Discovery, Media, Chat, cAdvisor |
| 9090-9199 | Metrics exporters | Prometheus, Node Exporter, Postgres Exporter |

---

## CI/CD Port Checking

The deployment workflow (`.github/workflows/deploy-microservices.yml`) includes port availability checks before deployment:

**Checked Ports:** 8080, 8081, 8082, 8083, 8084, 8085, 8086

**Logic:**
1. Stop all containers
2. Wait up to 30 seconds per port for release
3. Log warnings if ports remain in use
4. Continue deployment (graceful degradation)

**Script excerpt:**
```bash
PORTS_TO_CHECK="8080 8081 8082 8083 8084 8085 8086"
MAX_WAIT=30

for port in $PORTS_TO_CHECK; do
  WAIT_TIME=0
  while ss -tuln | grep -q ":$port "; do
    if [ $WAIT_TIME -ge $MAX_WAIT ]; then
      echo "⚠️  Port $port still in use after ${MAX_WAIT}s"
      break
    fi
    sleep 2
    WAIT_TIME=$((WAIT_TIME + 2))
  done
done
```

---

## Service Inter-Communication

Services communicate using service names on the internal Docker network:

| From | To | URL |
|------|----|----|
| API Gateway | Auth Service | http://auth-service:8081 |
| API Gateway | Profile Service | http://profile-service:8082 |
| API Gateway | Discovery Service | http://discovery-service:8083 |
| API Gateway | Media Service | http://media-service:8084 |
| API Gateway | Chat Service | http://chat-service:8085 |
| API Gateway | Admin Service | http://admin-service:8086 |
| Telegram Bot | API Gateway | http://api-gateway:8080 |
| All Services | Database | postgresql://db:5432 |
| Promtail | Loki | http://loki:3100 |
| Prometheus | cAdvisor | http://cadvisor:8080 |
| Prometheus | Node Exporter | http://node-exporter:9100 |
| Prometheus | Postgres Exporter | http://postgres-exporter:9187 |
| Grafana | Prometheus | http://prometheus:9090 |
| Grafana | Loki | http://loki:3100 |

**Note:** These URLs use default port values. If you customize ports via environment variables, update the service URLs accordingly (e.g., `AUTH_SERVICE_URL=http://auth-service:9081`).

---

## Troubleshooting Port Conflicts

### Check Port Usage
```bash
# List all listening ports
sudo ss -tulnp

# Check specific port
sudo ss -tulnp | grep :8080

# Find process using a port
sudo lsof -i :8080
```

### Manual Port Release
```bash
# Stop all project containers
docker compose down --remove-orphans

# Force remove any remaining containers
docker ps -aq --filter "name=dating" | xargs -r docker rm -f

# Wait for ports to be released
sleep 10

# Verify ports are free
for port in 8080 8081 8082 8083 8084 8085; do
  if ss -tuln | grep -q ":$port "; then
    echo "Port $port still in use"
  else
    echo "Port $port is free"
  fi
done
```

---

## Adding New Services

When adding new services to the project:

1. **Choose a port** from an available range:
   - 8086-8089 for new application services
   - 9200+ for new metrics exporters

2. **Update this document** with the new port allocation

3. **Add to CI/CD checks** if the service is critical:
   ```yaml
   PORTS_TO_CHECK="8080 8081 8082 8083 8084 8085 8086"  # Add your port
   ```

4. **Update docker-compose.yml** with port mapping:
   ```yaml
   your-service:
     ports:
       - "8086:8086"
   ```

5. **Add environment variable** for the port:
   ```yaml
   environment:
     YOUR_SERVICE_PORT: 8086
   ```

6. **Update Prometheus scrape config** if it exposes metrics:
   ```yaml
   - job_name: 'your-service'
     static_configs:
       - targets: ['your-service:8086']
   ```

---

## Related Documentation

- **Deployment Guide:** `docs/MICROSERVICES_DEPLOYMENT.md`
- **Troubleshooting:** `docs/DEPLOYMENT_TROUBLESHOOTING.md`
- **Port Conflict Fixes:**
  - `docs/BUG_FIX_PORT_80_CONFLICT.md`
  - `docs/BUG_FIX_PORT_5432_CONFLICT.md`
  - `docs/BUG_FIX_PORT_8080_CONFLICT.md`
  - `docs/BUG_FIX_PORT_8080_RACE_CONDITION.md`
- **Fix Summaries:**
  - `DEPLOYMENT_FIX_SUMMARY_PORT_5432.md`
  - `DEPLOYMENT_FIX_SUMMARY_PORT_8080.md`
  - `DEPLOYMENT_FIX_SUMMARY_PORT_8080_RACE.md`

---

**Last Updated:** January 2025  
**Maintained By:** Development Team  
**Version:** 1.0
