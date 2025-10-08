# Deployment Guide

## Runtime Configuration

### Docker Compose

The webapp service is configured to run **Node.js runtime** (not nginx static files):

```yaml
webapp:
  build:
    context: ./webapp
    dockerfile: Dockerfile # Uses Node.js 20 Alpine
  environment:
    NODE_ENV: production
    PORT: 3000
  ports:
    - "3000:3000"
  restart: unless-stopped
  healthcheck:
    test: ["CMD", "wget", "--spider", "http://localhost:3000/api/health"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s
```

**Key Points:**

- ✅ Uses `build` with Dockerfile (Node.js 20 Alpine)
- ✅ Runs `node server.js` (standalone Next.js server)
- ✅ Supports SSR, App Router, and dynamic routes
- ✅ Port 3000 exposed for Traefik
- ✅ Healthcheck on `/api/health` endpoint

### Traefik Integration

Complete Traefik labels for HTTP/HTTPS routing (updated to serve at root domain):

```yaml
labels:
  - "traefik.enable=true"
  # HTTP router - low priority catch-all
  - "traefik.http.routers.webapp.rule=Host(`${DOMAIN:-localhost}`) && PathPrefix(`/`)"
  - "traefik.http.routers.webapp.entrypoints=web"
  - "traefik.http.routers.webapp.priority=1"
  - "traefik.http.services.webapp.loadbalancer.server.port=3000"
  # HTTPS router - low priority catch-all
  - "traefik.http.routers.webapp-secure.rule=Host(`${DOMAIN:-localhost}`) && PathPrefix(`/`)"
  - "traefik.http.routers.webapp-secure.entrypoints=websecure"
  - "traefik.http.routers.webapp-secure.priority=1"
  - "traefik.http.routers.webapp-secure.tls.certresolver=letsencrypt"
  # HTTP to HTTPS redirect
  - "traefik.http.routers.webapp.middlewares=redirect-to-https"
```

**Routing Priority:**
- WebApp serves the root domain (/) with priority 1 (catch-all)
- API Gateway handles specific paths (/api, /health, /admin-panel, /chat) with priority 100
- This allows https://yourdomain.com/ to serve the webapp while https://yourdomain.com/api/* routes to the API

### Dockerfile Overview

Multi-stage build for optimal size and performance:

```dockerfile
# Stage 1: Dependencies (deps)
FROM node:20-alpine
COPY package.json package-lock.json ./
RUN npm ci

# Stage 2: Builder
FROM node:20-alpine
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# Stage 3: Runner (production)
FROM node:20-alpine
RUN apk add --no-cache wget  # For healthcheck
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
CMD ["node", "server.js"]
```

**Output Mode:** `standalone` (configured in `next.config.ts`)

## Environment Variables

### Required

```env
# Backend API URL (for API proxy)
NEXT_PUBLIC_API_URL=http://api-gateway:8080

# Public site URL (for SEO/sitemap)
NEXT_PUBLIC_SITE_URL=https://yourdomain.com
```

### Optional

```env
# Custom webapp port (default: 3000)
WEBAPP_PORT=3000

# Domain for Traefik (default: localhost)
DOMAIN=yourdomain.com
```

## Deployment Commands

### Development

```bash
cd webapp
npm install
npm run dev  # http://localhost:3000
```

### Production (Docker Compose)

```bash
# Build and start (webapp is now a core service)
docker compose up -d

# Check health
curl http://localhost:3000/api/health

# View logs
docker compose logs -f webapp

# Restart
docker compose restart webapp
```

### CI/CD

GitHub Actions workflow automatically runs on:

- Push to `main`, `develop`, or `copilot/**` branches
- Pull requests to `main` or `develop`
- Changes in `webapp/**` directory

**Pipeline:**

1. Install dependencies (`npm ci`)
2. Lint code (`npm run lint`)
3. Check formatting (`npm run format:check`)
4. Type check (`npm run type-check`)
5. Build production bundle (`npm run build`)
6. Run Playwright smoke tests (`npm test`)

## Health Check

The webapp exposes a health endpoint for monitoring:

**Endpoint:** `GET /api/health`

**Response:**

```json
{
  "status": "healthy",
  "service": "webapp",
  "timestamp": "2025-01-27T10:00:00.000Z",
  "uptime": 123.45
}
```

**Docker Health Check:**

- Interval: 30 seconds
- Timeout: 10 seconds
- Retries: 3
- Start period: 40 seconds (allows app to initialize)

## Troubleshooting

### Issue: Routes not working (404)

**Cause:** Using nginx instead of Node.js runtime

**Solution:** Verify `docker-compose.yml` uses:

```yaml
build:
  context: ./webapp
  dockerfile: Dockerfile
```

NOT:

```yaml
image: nginx:alpine
volumes:
  - ./webapp:/usr/share/nginx/html
```

### Issue: API requests fail

**Cause:** CSP blocking connections or wrong API URL

**Solution:** Check `NEXT_PUBLIC_API_URL` and review `docs/SECURITY.md` for CSP configuration

### Issue: Healthcheck fails

**Cause:** App not fully started or `/api/health` endpoint missing

**Solution:**

- Check logs: `docker compose logs webapp`
- Verify endpoint: `curl http://localhost:3000/api/health`
- Increase `start_period` in healthcheck if needed

## Performance

### Build Optimization

- **Multi-stage Docker build:** Reduces final image size
- **Standalone output:** Includes only necessary dependencies
- **npm ci:** Fast, reproducible dependency installation
- **.dockerignore:** Excludes unnecessary files from build context

### Runtime Optimization

- **Node.js 20 Alpine:** Minimal base image (~50MB)
- **Static asset caching:** Next.js handles efficiently
- **Health checks:** Ensures service availability
- **Graceful shutdown:** Handled by Next.js server

## Monitoring

### Logs

```bash
# Follow webapp logs
docker compose logs -f webapp

# Last 100 lines
docker compose logs --tail=100 webapp
```

### Metrics

The webapp can integrate with Prometheus for monitoring:

- Request rates
- Response times
- Error rates
- Health check status

See main `docker-compose.yml` for Prometheus/Grafana integration.
