# Microservices Deployment Guide

This guide covers deploying the dating application using microservices architecture.

## Architecture Overview

The application consists of the following microservices:

### Services

1. **API Gateway** (Port 8080)
   - Routes requests to appropriate microservices
   - Handles load balancing and request routing
   - Endpoint: `/health`

2. **Auth Service** (Port 8081)
   - JWT token generation and validation
   - Telegram WebApp initData validation
   - Endpoints: `/auth/validate`, `/auth/verify`, `/auth/refresh`, `/health`

3. **Profile Service** (Port 8082)
   - User profile management
   - Photo management
   - Endpoints: `/profiles/{user_id}`, `/profiles`, `/health`

4. **Discovery Service** (Port 8083)
   - Matching algorithm
   - Candidate recommendations
   - Endpoints: `/discovery/candidates`, `/discovery/like`, `/discovery/matches`, `/health`

5. **Media Service** (Port 8084)
   - Photo upload and storage
   - Media file serving
   - Endpoints: `/media/upload`, `/media/{file_id}`, `/health`

6. **Chat Service** (Port 8085)
   - WebSocket connections for real-time messaging
   - Message history
   - Endpoints: `/chat/connect` (WS), `/chat/conversations`, `/chat/messages`, `/health`

### Infrastructure

- **PostgreSQL Database** (Port 5432): Shared database for all services
- **Telegram Bot Adapter**: Connects Telegram interface to microservices via API Gateway
- **WebApp**: Static frontend served by nginx

## Deployment Options

### Option 1: Local Development

Deploy all services on your local machine for development:

```bash
# 1. Configure environment
cp .env.example .env
nano .env  # Set BOT_TOKEN, JWT_SECRET, etc.

# 2. Deploy with automated script
./scripts/deploy-microservices.sh

# 3. Verify deployment
curl http://localhost:8080/health
```

### Option 2: Production Deployment

Deploy to production server:

```bash
# 1. On your server, clone the repository
git clone https://github.com/erliona/dating.git
cd dating

# 2. Configure environment variables
cp .env.example .env
nano .env

# Required variables for production:
# - BOT_TOKEN: Your Telegram bot token
# - JWT_SECRET: Strong random secret (generate with: openssl rand -hex 32)
# - POSTGRES_PASSWORD: Secure database password
# - DOMAIN: Your domain name (for HTTPS)
# - ACME_EMAIL: Email for SSL certificates

# 3. Deploy services
docker compose -f docker-compose.microservices.yml up -d

# 4. Check service health
docker compose -f docker-compose.microservices.yml ps
```

### Option 3: CI/CD Deployment

Automated deployment via GitHub Actions (recommended for production):

1. **Configure GitHub Secrets**
   - Go to: `Settings → Secrets and variables → Actions`
   - Add required secrets:
     - `DEPLOY_HOST`: Your server IP/hostname
     - `DEPLOY_USER`: SSH user with sudo
     - `DEPLOY_SSH_KEY`: Private SSH key
     - `BOT_TOKEN`: Telegram bot token
     - `JWT_SECRET`: JWT secret key
     - `DOMAIN` (optional): Your domain for HTTPS
     - `ACME_EMAIL` (optional): Email for Let's Encrypt

2. **Trigger Deployment**
   ```bash
   # Push to main branch
   git push origin main
   
   # Or manually trigger via GitHub UI:
   # Actions → Deploy → Run workflow
   ```

3. **Monitor Deployment**
   - Check GitHub Actions logs
   - Verify services: `ssh user@server "docker compose ps"`

## Configuration

### Environment Variables

Required for all deployments:

```env
# Bot Configuration
BOT_TOKEN=your-telegram-bot-token
JWT_SECRET=your-jwt-secret-key

# Database Configuration
POSTGRES_DB=dating
POSTGRES_USER=dating
POSTGRES_PASSWORD=secure-password
POSTGRES_PORT=5432

# Service URLs (auto-configured in docker-compose)
AUTH_SERVICE_URL=http://auth-service:8081
PROFILE_SERVICE_URL=http://profile-service:8082
DISCOVERY_SERVICE_URL=http://discovery-service:8083
MEDIA_SERVICE_URL=http://media-service:8084
CHAT_SERVICE_URL=http://chat-service:8085
```

Optional for production:

```env
# HTTPS Configuration
DOMAIN=your-domain.com
ACME_EMAIL=admin@your-domain.com
WEBAPP_URL=https://your-domain.com

# Photo Storage
PHOTO_STORAGE_PATH=/app/photos
PHOTO_CDN_URL=https://cdn.your-domain.com

# API Configuration
API_HOST=0.0.0.0
API_PORT=8080
NSFW_THRESHOLD=0.7
```

### Service-Specific Configuration

Each service can be configured with environment variables:

**Auth Service:**
```env
AUTH_SERVICE_HOST=0.0.0.0
AUTH_SERVICE_PORT=8081
JWT_SECRET=your-jwt-secret
```

**Profile Service:**
```env
PROFILE_SERVICE_HOST=0.0.0.0
PROFILE_SERVICE_PORT=8082
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/dating
```

**Discovery Service:**
```env
DISCOVERY_SERVICE_HOST=0.0.0.0
DISCOVERY_SERVICE_PORT=8083
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/dating
```

**Media Service:**
```env
MEDIA_SERVICE_HOST=0.0.0.0
MEDIA_SERVICE_PORT=8084
PHOTO_STORAGE_PATH=/app/photos
NSFW_THRESHOLD=0.7
```

**Chat Service:**
```env
CHAT_SERVICE_HOST=0.0.0.0
CHAT_SERVICE_PORT=8085
```

**API Gateway:**
```env
GATEWAY_HOST=0.0.0.0
GATEWAY_PORT=8080
```

## Health Checks

All services expose a `/health` endpoint:

```bash
# Check all services
curl http://localhost:8080/health  # API Gateway
curl http://localhost:8081/health  # Auth
curl http://localhost:8082/health  # Profile
curl http://localhost:8083/health  # Discovery
curl http://localhost:8084/health  # Media
curl http://localhost:8085/health  # Chat

# Expected response:
# {"status": "healthy", "service": "service-name"}
```

## Scaling Services

Scale individual services based on load:

```bash
# Scale profile service to 3 instances
docker compose -f docker-compose.microservices.yml up -d --scale profile-service=3

# Scale discovery service to 5 instances
docker compose -f docker-compose.microservices.yml up -d --scale discovery-service=5

# Scale down
docker compose -f docker-compose.microservices.yml up -d --scale profile-service=1
```

Note: API Gateway will automatically load balance requests across instances.

## Monitoring

### Service Logs

View logs for all services:

```bash
# All services
docker compose -f docker-compose.microservices.yml logs -f

# Specific service
docker compose -f docker-compose.microservices.yml logs -f auth-service
docker compose -f docker-compose.microservices.yml logs -f profile-service
docker compose -f docker-compose.microservices.yml logs -f api-gateway

# Last 100 lines
docker compose -f docker-compose.microservices.yml logs --tail=100 auth-service
```

### Service Status

Check service status:

```bash
# List all services with status
docker compose -f docker-compose.microservices.yml ps

# Detailed service info
docker compose -f docker-compose.microservices.yml ps --format json | jq

# Check container health
docker inspect dating-auth-service-1 --format='{{.State.Health.Status}}'
```

### Resource Usage

Monitor resource consumption:

```bash
# CPU and memory usage
docker stats

# Disk usage
docker system df

# Volume usage
docker volume ls
docker volume inspect dating_postgres_data
```

## Troubleshooting

### Service Won't Start

```bash
# Check logs
docker compose -f docker-compose.microservices.yml logs service-name

# Rebuild service
docker compose -f docker-compose.microservices.yml build --no-cache service-name
docker compose -f docker-compose.microservices.yml up -d service-name

# Check container status
docker compose -f docker-compose.microservices.yml ps
```

### Database Connection Issues

```bash
# Check database is running
docker compose -f docker-compose.microservices.yml ps db

# Test database connection
docker compose -f docker-compose.microservices.yml exec db psql -U dating -d dating -c "SELECT 1"

# Check database logs
docker compose -f docker-compose.microservices.yml logs db
```

### Service Communication Issues

```bash
# Check network
docker network ls
docker network inspect dating_default

# Test service connectivity
docker compose -f docker-compose.microservices.yml exec api-gateway ping auth-service
docker compose -f docker-compose.microservices.yml exec api-gateway curl http://auth-service:8081/health
```

### Port Conflicts

If ports are already in use:

```bash
# Check what's using the port
sudo lsof -i :8080
sudo netstat -tulpn | grep 8080

# Stop conflicting service or change port in docker-compose.microservices.yml
# Example: Change "8080:8080" to "8090:8080"
```

## Maintenance

### Updating Services

```bash
# Pull latest code
git pull origin main

# Rebuild and restart services
docker compose -f docker-compose.microservices.yml build
docker compose -f docker-compose.microservices.yml up -d

# Restart specific service
docker compose -f docker-compose.microservices.yml restart profile-service
```

### Database Migrations

```bash
# Run migrations (through telegram-bot service)
docker compose -f docker-compose.microservices.yml exec telegram-bot alembic upgrade head

# Check migration status
docker compose -f docker-compose.microservices.yml exec telegram-bot alembic current
```

### Backup and Restore

```bash
# Backup database
docker compose -f docker-compose.microservices.yml exec db pg_dump -U dating dating > backup.sql

# Restore database
cat backup.sql | docker compose -f docker-compose.microservices.yml exec -T db psql -U dating dating
```

### Cleanup

```bash
# Stop all services
docker compose -f docker-compose.microservices.yml down

# Remove volumes (WARNING: deletes all data)
docker compose -f docker-compose.microservices.yml down -v

# Remove images
docker compose -f docker-compose.microservices.yml down --rmi all
```

## Migration from Monolithic

If migrating from the monolithic deployment:

1. **Backup existing data:**
   ```bash
   docker compose exec db pg_dump -U dating dating > backup-monolithic.sql
   ```

2. **Stop monolithic deployment:**
   ```bash
   docker compose down
   ```

3. **Deploy microservices:**
   ```bash
   docker compose -f docker-compose.microservices.yml up -d
   ```

4. **Restore data if needed:**
   ```bash
   cat backup-monolithic.sql | docker compose -f docker-compose.microservices.yml exec -T db psql -U dating dating
   ```

5. **Verify migration:**
   ```bash
   # Check all services are healthy
   curl http://localhost:8080/health
   
   # Test API endpoints through gateway
   curl http://localhost:8080/auth/verify
   curl http://localhost:8080/profiles/1
   ```

## Performance Tuning

### Database Optimization

```yaml
# In docker-compose.microservices.yml, add to db service:
command:
  - postgres
  - -c
  - max_connections=200
  - -c
  - shared_buffers=256MB
  - -c
  - effective_cache_size=1GB
```

### Service Resources

```yaml
# Limit service resources
services:
  profile-service:
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 512M
        reservations:
          cpus: '0.5'
          memory: 256M
```

### Connection Pooling

Each service manages its own database connection pool. Configure in service environment:

```env
# SQLAlchemy pool settings
SQLALCHEMY_POOL_SIZE=10
SQLALCHEMY_MAX_OVERFLOW=20
SQLALCHEMY_POOL_TIMEOUT=30
```

## Security

### Best Practices

1. **Use strong secrets:**
   ```bash
   # Generate secure JWT secret
   openssl rand -hex 32
   
   # Generate secure database password
   openssl rand -base64 24
   ```

2. **Enable HTTPS in production:**
   - Set `DOMAIN` and `ACME_EMAIL` in .env
   - Use Traefik for automatic SSL certificates

3. **Restrict database access:**
   ```yaml
   # Don't expose database port in production
   db:
     # ports:
     #   - "5432:5432"  # Comment this out
   ```

4. **Use secrets management:**
   - For production, use Docker secrets or environment encryption
   - Never commit .env files to git

5. **Enable rate limiting:**
   - Configure rate limits in API Gateway
   - Use Redis for distributed rate limiting

## Additional Resources

- [Architecture Migration Guide](./ARCHITECTURE_MIGRATION_GUIDE.md)
- [Getting Started](./GETTING_STARTED.md)
- [Deployment Guide](./DEPLOYMENT.md)
- [Services README](../services/README.md)

## Support

For issues or questions:
- Check troubleshooting section above
- Review logs for error messages
- Open an issue on GitHub
- Consult documentation in `/docs` directory
