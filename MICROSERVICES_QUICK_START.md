# Microservices Quick Start Guide

Quick reference for deploying and using the dating app microservices.

## 🚀 Quick Deploy

### Option 1: Automated Script (Recommended)

```bash
# 1. Configure environment
cp .env.example .env
nano .env  # Set BOT_TOKEN, JWT_SECRET, POSTGRES_PASSWORD

# 2. Run deployment script
./scripts/deploy-microservices.sh
```

### Option 2: Manual Docker Compose

```bash
# Build and start
docker compose -f docker-compose.microservices.yml up -d

# Check status
docker compose -f docker-compose.microservices.yml ps

# View logs
docker compose -f docker-compose.microservices.yml logs -f
```

### Option 3: CI/CD (Production)

1. Configure GitHub Secrets (Settings → Secrets → Actions):
   - `DEPLOY_HOST`, `DEPLOY_USER`, `DEPLOY_SSH_KEY`
   - `BOT_TOKEN`, `JWT_SECRET`
   
2. Push to main or trigger workflow manually

## 📊 Service Overview

| Service | Port | Description | Health Check |
|---------|------|-------------|--------------|
| API Gateway | 8080 | Request routing | `curl http://localhost:8080/health` |
| Auth | 8081 | JWT tokens | `curl http://localhost:8081/health` |
| Profile | 8082 | User profiles | `curl http://localhost:8082/health` |
| Discovery | 8083 | Matching | `curl http://localhost:8083/health` |
| Media | 8084 | Photo storage | `curl http://localhost:8084/health` |
| Chat | 8085 | Messaging | `curl http://localhost:8085/health` |
| Database | 5432 | PostgreSQL | N/A |

## 🔧 Common Commands

### Start/Stop Services

```bash
# Start all
docker compose -f docker-compose.microservices.yml up -d

# Stop all
docker compose -f docker-compose.microservices.yml down

# Restart specific service
docker compose -f docker-compose.microservices.yml restart profile-service

# Stop and remove volumes (WARNING: deletes data)
docker compose -f docker-compose.microservices.yml down -v
```

### View Logs

```bash
# All services
docker compose -f docker-compose.microservices.yml logs -f

# Specific service
docker compose -f docker-compose.microservices.yml logs -f auth-service

# Last 50 lines
docker compose -f docker-compose.microservices.yml logs --tail=50 profile-service
```

### Check Status

```bash
# Service status
docker compose -f docker-compose.microservices.yml ps

# Resource usage
docker stats

# Health checks
for port in 8080 8081 8082 8083 8084 8085; do
  echo "Port $port: $(curl -s http://localhost:$port/health | jq -r .status)"
done
```

### Scale Services

```bash
# Scale profile service to 3 instances
docker compose -f docker-compose.microservices.yml up -d --scale profile-service=3

# Scale discovery to 5 instances
docker compose -f docker-compose.microservices.yml up -d --scale discovery-service=5
```

## 🧪 Testing API

### Auth Service

```bash
# Validate Telegram initData
curl -X POST http://localhost:8081/auth/validate \
  -H "Content-Type: application/json" \
  -d '{"init_data":"data","bot_token":"token"}'

# Verify token
curl http://localhost:8081/auth/verify \
  -H "Authorization: Bearer <token>"
```

### Profile Service

```bash
# Get profile
curl http://localhost:8082/profiles/123456789

# Create profile
curl -X POST http://localhost:8082/profiles \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": 123456789,
    "name": "John Doe",
    "birth_date": "1995-05-15",
    "gender": "male",
    "orientation": "heterosexual",
    "city": "Moscow"
  }'
```

### Discovery Service

```bash
# Get candidates
curl "http://localhost:8083/discovery/candidates?user_id=123456789&limit=5"

# Like profile
curl -X POST http://localhost:8083/discovery/like \
  -H "Content-Type: application/json" \
  -d '{"user_id": 123456789, "target_id": 987654321}'
```

### Media Service

```bash
# Upload photo
curl -X POST http://localhost:8084/media/upload \
  -F "file=@photo.jpg"

# Download photo
curl http://localhost:8084/media/{file_id} -o photo.jpg
```

### Via API Gateway

All requests can go through the gateway:

```bash
# Through gateway (recommended)
curl http://localhost:8080/auth/verify \
  -H "Authorization: Bearer <token>"

curl http://localhost:8080/profiles/123456789

curl "http://localhost:8080/discovery/candidates?user_id=123456789"
```

## 🔍 Troubleshooting

### Service Won't Start

```bash
# 1. Check logs
docker compose -f docker-compose.microservices.yml logs service-name

# 2. Rebuild service
docker compose -f docker-compose.microservices.yml build --no-cache service-name

# 3. Restart service
docker compose -f docker-compose.microservices.yml up -d service-name
```

### Database Issues

```bash
# Check database
docker compose -f docker-compose.microservices.yml ps db

# Connect to database
docker compose -f docker-compose.microservices.yml exec db psql -U dating dating

# Run migrations
docker compose -f docker-compose.microservices.yml exec telegram-bot alembic upgrade head
```

### Port Already in Use

```bash
# Find what's using the port
sudo lsof -i :8080

# Change port in docker-compose.microservices.yml
# From: "8080:8080"
# To:   "8090:8080"
```

### Reset Everything

```bash
# Stop and remove everything
docker compose -f docker-compose.microservices.yml down -v

# Remove all containers and images
docker system prune -a

# Start fresh
docker compose -f docker-compose.microservices.yml up -d
```

## 📚 Required Environment Variables

Minimal `.env` configuration:

```env
# Required
BOT_TOKEN=your-telegram-bot-token
JWT_SECRET=your-jwt-secret-key
POSTGRES_PASSWORD=secure-password

# Optional (defaults provided)
POSTGRES_DB=dating
POSTGRES_USER=dating
POSTGRES_PORT=5432

# Production (optional)
DOMAIN=your-domain.com
ACME_EMAIL=admin@your-domain.com
WEBAPP_URL=https://your-domain.com
```

Generate secure secrets:

```bash
# JWT secret
openssl rand -hex 32

# Database password
openssl rand -base64 24
```

## 📖 Documentation

- **Full API Reference**: [docs/MICROSERVICES_API.md](docs/MICROSERVICES_API.md)
- **Deployment Guide**: [docs/MICROSERVICES_DEPLOYMENT.md](docs/MICROSERVICES_DEPLOYMENT.md)
- **Architecture**: [docs/ARCHITECTURE_MIGRATION_GUIDE.md](docs/ARCHITECTURE_MIGRATION_GUIDE.md)
- **Services README**: [services/README.md](services/README.md)

## 🎯 Next Steps

1. ✅ Deploy microservices
2. ✅ Test API endpoints
3. 📋 Set up monitoring (Prometheus/Grafana)
4. 📋 Configure backups
5. 📋 Set up CI/CD pipeline
6. 📋 Implement service mesh (optional)
7. 📋 Split database per service (Phase 5)

## 💡 Tips

- **Development**: Use `docker compose -f docker-compose.microservices.yml` for testing
- **Production**: Use automated deployment script or CI/CD
- **Monitoring**: Check health endpoints regularly
- **Scaling**: Scale services independently based on load
- **Debugging**: Use `docker compose logs -f service-name` to debug issues
- **Performance**: Monitor resource usage with `docker stats`

## 🆘 Getting Help

If you encounter issues:

1. Check logs: `docker compose -f docker-compose.microservices.yml logs`
2. Review documentation in `/docs`
3. Open an issue on GitHub
4. Check health endpoints: `curl http://localhost:8080/health`

---

**Status**: ✅ Phase 4 Complete - Microservices deployed and ready for production!
