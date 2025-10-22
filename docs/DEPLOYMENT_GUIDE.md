# 🚀 Deployment Guide

## 📋 Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Local Development](#local-development)
- [Production Deployment](#production-deployment)
- [Service Configuration](#service-configuration)
- [Monitoring Setup](#monitoring-setup)
- [Troubleshooting](#troubleshooting)
- [Maintenance](#maintenance)

---

## 🎯 Overview

This guide covers deploying the Dating application in both local development and production environments. The application uses Docker Compose for orchestration and can be deployed on any system that supports Docker.

### Deployment Options

1. **Local Development** - Full stack with hot reload
2. **Production** - Optimized for performance and security
3. **Staging** - Production-like environment for testing

---

## 📋 Prerequisites

### System Requirements

**Minimum Requirements**:
- CPU: 2 cores
- RAM: 4GB
- Storage: 20GB free space
- Network: Internet connection

**Recommended for Production**:
- CPU: 4+ cores
- RAM: 8GB+
- Storage: 50GB+ SSD
- Network: Stable internet connection

### Software Requirements

- **Docker** 20.10+
- **Docker Compose** 2.0+
- **Git** (for cloning repository)
- **Node.js** 20+ (for WebApp development)

### Domain and SSL

For production deployment:
- Domain name pointing to your server
- SSL certificate (automatically handled by Let's Encrypt)

---

## 🔧 Environment Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd dating
```

### 2. Environment Configuration

Create environment file:

```bash
cp .env.example .env
```

Edit `.env` file with your configuration:

```bash
# Database Configuration
POSTGRES_DB=dating
POSTGRES_USER=dating
POSTGRES_PASSWORD=your_secure_password_here

# JWT Configuration
JWT_SECRET=your_jwt_secret_here

# Telegram Bot Configuration
BOT_TOKEN=your_telegram_bot_token_here

# Domain Configuration (for production)
DOMAIN=your-domain.com
ACME_EMAIL=admin@your-domain.com

# Port Configuration
HTTP_PORT=80
HTTPS_PORT=443
TRAEFIK_DASHBOARD_PORT=8091

# Service Ports
AUTH_SERVICE_PORT=8081
PROFILE_SERVICE_PORT=8082
DISCOVERY_SERVICE_PORT=8083
MEDIA_SERVICE_PORT=8084
CHAT_SERVICE_PORT=8085
NOTIFICATION_SERVICE_PORT=8086
ADMIN_SERVICE_PORT=8087
DATA_SERVICE_PORT=8088

# WebApp Configuration
WEBAPP_URL=https://your-domain.com

# Monitoring Configuration
NSFW_THRESHOLD=0.7
LOG_LEVEL=INFO
```

### 3. Generate Secure Secrets

```bash
# Generate JWT secret
openssl rand -base64 32

# Generate database password
openssl rand -base64 16
```

---

## 💻 Local Development

### Quick Start

```bash
# Start all services
docker compose up -d

# Check service status
docker compose ps

# View logs
docker compose logs -f
```

### Development Workflow

#### 1. Backend Development

```bash
# Start only infrastructure services
docker compose up -d db traefik

# Run individual services locally
cd services/auth
python -m services.auth.main

# Or run all services
docker compose up -d
```

#### 2. Frontend Development

```bash
cd webapp

# Install dependencies
npm install

# Start development server
npm run dev

# Run tests
npm test
```

#### 3. Database Management

```bash
# Run migrations
docker compose exec db alembic upgrade head

# Access database
docker compose exec db psql -U dating -d dating

# Create admin user
python scripts/create_admin.py
```

### Development Tools

#### Useful Commands

```bash
# View service logs
docker compose logs -f <service-name>

# Restart specific service
docker compose restart <service-name>

# Rebuild and restart service
docker compose up -d --build <service-name>

# Access service shell
docker compose exec <service-name> /bin/bash

# Check service health
curl http://localhost:8080/health
```

#### Testing

```bash
# Run all tests
pytest

# Run specific test category
pytest tests/unit/
pytest tests/integration/
pytest tests/e2e/

# Run with coverage
pytest --cov=bot --cov=services --cov-report=html
```

---

## 🌐 Production Deployment

### 1. Server Preparation

#### Update System

```bash
sudo apt update && sudo apt upgrade -y
```

#### Install Docker

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Add user to docker group
sudo usermod -aG docker $USER
```

#### Configure Firewall

```bash
# Allow SSH
sudo ufw allow ssh

# Allow HTTP and HTTPS
sudo ufw allow 80
sudo ufw allow 443

# Allow Traefik dashboard (optional)
sudo ufw allow 8091

# Enable firewall
sudo ufw enable
```

### 2. Application Deployment

#### Clone and Configure

```bash
# Clone repository
git clone <repository-url>
cd dating

# Create production environment
cp .env.example .env.production
# Edit .env.production with production values

# Set environment file
export ENV_FILE=.env.production
```

#### Deploy Application

```bash
# Pull latest images
docker compose pull

# Start all services
docker compose --env-file .env.production up -d

# Check deployment status
docker compose ps
```

#### Verify Deployment

```bash
# Check service health
curl https://your-domain.com/health

# Check SSL certificate
curl -I https://your-domain.com

# View logs
docker compose logs -f
```

### 3. SSL Certificate Setup

SSL certificates are automatically managed by Traefik with Let's Encrypt:

```yaml
# In docker-compose.yml
traefik:
  command:
    - "--certificatesresolvers.letsencrypt.acme.email=${ACME_EMAIL}"
    - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    - "--certificatesresolvers.letsencrypt.acme.httpchallenge=true"
```

### 4. Database Setup

#### Initial Migration

```bash
# Run database migrations
docker compose exec db alembic upgrade head

# Create admin user
docker compose exec webapp python scripts/create_admin.py
```

#### Database Backup

```bash
# Create backup
docker compose exec db pg_dump -U dating dating > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
docker compose exec -T db psql -U dating dating < backup_file.sql
```

---

## ⚙️ Service Configuration

### Traefik Configuration

Traefik handles SSL termination and request routing:

```yaml
traefik:
  image: traefik:v2.11
  command:
    - "--api.dashboard=true"
    - "--providers.docker=true"
    - "--entrypoints.web.address=:80"
    - "--entrypoints.websecure.address=:443"
    - "--certificatesresolvers.letsencrypt.acme.email=${ACME_EMAIL}"
    - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
    - "--certificatesresolvers.letsencrypt.acme.httpchallenge=true"
```

### Database Configuration

PostgreSQL configuration for production:

```yaml
db:
  image: postgres:15-alpine
  environment:
    POSTGRES_DB: ${POSTGRES_DB}
    POSTGRES_USER: ${POSTGRES_USER}
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
  volumes:
    - postgres_data:/var/lib/postgresql/data
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
    interval: 10s
    timeout: 5s
    retries: 5
```

### Service Health Checks

All services include health check endpoints:

```yaml
healthcheck:
  test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8081/health').read()"]
  interval: 30s
  timeout: 10s
  retries: 3
```

---

## 📊 Monitoring Setup

### Prometheus Configuration

Prometheus collects metrics from all services:

```yaml
prometheus:
  image: prom/prometheus:v2.51.0
  command:
    - "--config.file=/etc/prometheus/prometheus.yml"
    - "--storage.tsdb.path=/prometheus"
    - "--web.console.libraries=/etc/prometheus/console_libraries"
    - "--web.console.templates=/etc/prometheus/consoles"
    - "--web.enable-lifecycle"
```

### Grafana Dashboards

Grafana provides visualization of system metrics:

```yaml
grafana:
  image: grafana/grafana:10.4.0
  environment:
    GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_PASSWORD:-admin}
  volumes:
    - grafana_data:/var/lib/grafana
    - ./monitoring/grafana/provisioning:/etc/grafana/provisioning
    - ./monitoring/grafana/dashboards:/var/lib/grafana/dashboards
```

### Log Aggregation

Loki collects and aggregates logs:

```yaml
loki:
  image: grafana/loki:3.0.0
  command: -config.file=/etc/loki/local-config.yaml
  volumes:
    - loki_data:/loki
    - ./monitoring/loki/loki-config.yml:/etc/loki/local-config.yaml
```

### Accessing Monitoring

- **Grafana**: `https://your-domain.com:3000`
- **Prometheus**: `https://your-domain.com:9090`
- **Traefik Dashboard**: `https://your-domain.com:8091`

---

## 🔧 Troubleshooting

### Common Issues

#### 1. Service Won't Start

```bash
# Check service logs
docker compose logs <service-name>

# Check service status
docker compose ps

# Restart service
docker compose restart <service-name>
```

#### 2. Database Connection Issues

```bash
# Check database status
docker compose exec db pg_isready -U dating

# Check database logs
docker compose logs db

# Test connection
docker compose exec db psql -U dating -d dating -c "SELECT 1;"
```

#### 3. SSL Certificate Issues

```bash
# Check certificate status
curl -I https://your-domain.com

# Check Traefik logs
docker compose logs traefik

# Force certificate renewal
docker compose restart traefik
```

#### 4. High Memory Usage

```bash
# Check resource usage
docker stats

# Check service logs for memory leaks
docker compose logs <service-name>

# Restart services
docker compose restart
```

### Debugging Commands

```bash
# View all service logs
docker compose logs -f

# Check service health
curl http://localhost:8080/health

# Access service shell
docker compose exec <service-name> /bin/bash

# Check network connectivity
docker compose exec <service-name> ping <other-service>

# View Traefik configuration
docker compose exec traefik cat /etc/traefik/traefik.yml
```

### Performance Optimization

#### Database Optimization

```sql
-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Check index usage
SELECT schemaname, tablename, attname, n_distinct, correlation 
FROM pg_stats 
WHERE schemaname = 'public';
```

#### Service Optimization

```bash
# Check service resource usage
docker stats

# Monitor service logs
docker compose logs -f --tail=100

# Check service health
curl http://localhost:8080/health
```

---

## 🔄 Maintenance

### Regular Maintenance Tasks

#### Daily

- Check service health
- Monitor error logs
- Check disk space

#### Weekly

- Review system metrics
- Check SSL certificate expiration
- Update dependencies

#### Monthly

- Database maintenance
- Security updates
- Performance review

### Backup Strategy

#### Database Backups

```bash
#!/bin/bash
# Daily backup script

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
DB_NAME="dating"

# Create backup
docker compose exec db pg_dump -U dating $DB_NAME > $BACKUP_DIR/backup_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/backup_$DATE.sql

# Remove old backups (keep 30 days)
find $BACKUP_DIR -name "backup_*.sql.gz" -mtime +30 -delete
```

#### Configuration Backups

```bash
# Backup configuration files
tar -czf config_backup_$(date +%Y%m%d).tar.gz .env docker-compose.yml monitoring/
```

### Updates and Upgrades

#### Application Updates

```bash
# Pull latest changes
git pull origin main

# Rebuild and restart services
docker compose up -d --build

# Run database migrations
docker compose exec db alembic upgrade head
```

#### System Updates

```bash
# Update system packages
sudo apt update && sudo apt upgrade -y

# Update Docker
sudo apt install docker-ce docker-ce-cli containerd.io

# Restart services
docker compose restart
```

### Security Maintenance

#### SSL Certificate Monitoring

```bash
# Check certificate expiration
openssl s_client -connect your-domain.com:443 -servername your-domain.com 2>/dev/null | openssl x509 -noout -dates
```

#### Security Updates

```bash
# Update base images
docker compose pull

# Rebuild services
docker compose up -d --build

# Check for vulnerabilities
docker scout cves
```

---

## 📚 Additional Resources

### Documentation

- [Architecture Overview](ARCHITECTURE.md)
- [API Documentation](API_DOCUMENTATION.md)
- [Getting Started](GETTING_STARTED.md)
- [Monitoring Setup](MONITORING_SETUP.md)

### Support

- GitHub Issues: [Repository Issues](https://github.com/your-repo/issues)
- Documentation: [Project Documentation](https://your-domain.com/docs)
- Community: [Discord/Telegram Channel]

---

*Last updated: January 2025*
