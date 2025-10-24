# Environment Configuration

## Overview

This project supports exactly **two environments**:

1. **Development** - Local development on your machine
2. **Production** - Live server deployment

## Environment Detection

The application uses the `ENVIRONMENT` variable to distinguish between environments:

- `ENVIRONMENT=development` - Local development
- `ENVIRONMENT=production` - Production server

## Development Environment

### Setup

1. **Clone repository**:
   ```bash
   git clone https://github.com/erliona/dating.git
   cd dating
   ```

2. **Create environment file**:
   ```bash
   cp .env.example .env
   ```

3. **Configure environment variables**:
   ```bash
   # Edit .env file with your local values
   nano .env
   ```

4. **Required local configuration**:
   ```bash
   ENVIRONMENT=development
   BOT_TOKEN=your_telegram_bot_token
   JWT_SECRET=your_jwt_secret
   POSTGRES_PASSWORD=your_local_password
   ```

### Running Development

```bash
# Start all services (without monitoring)
docker compose up -d

# View logs
docker compose logs -f

# Stop services
docker compose down
```

### Development Features

- **Hot reload** for code changes
- **External database access** (port 5433)
- **Debug logging** enabled
- **No monitoring stack** (Prometheus, Grafana, Loki)
- **Local domain**: `localhost`

## Production Environment

### Setup

1. **Server preparation**:
   ```bash
   # On production server
   git clone https://github.com/erliona/dating.git
   cd dating
   ```

2. **Create production environment**:
   ```bash
   cp .env.example .env
   # Edit .env with production values
   ```

3. **Required production configuration**:
   ```bash
   ENVIRONMENT=production
   BOT_TOKEN=your_production_bot_token
   JWT_SECRET=your_production_jwt_secret
   POSTGRES_PASSWORD=your_strong_production_password
   DOMAIN=your-domain.com
   ACME_EMAIL=your-email@domain.com
   ```

### Running Production

```bash
# Deploy with monitoring stack
docker compose --profile production up --build -d

# Check status
docker compose --profile production ps

# View logs
docker compose --profile production logs -f
```

### Production Features

- **Full monitoring stack** (Prometheus, Grafana, Loki)
- **SSL certificates** (Let's Encrypt)
- **Security hardening** enabled
- **Production domain**: `your-domain.com`
- **Optimized for performance**

## Environment-Specific Configurations

### Development Only

- **External database port**: `5433`
- **Debug mode**: Enabled
- **Hot reload**: Enabled
- **Local domain**: `localhost`
- **No SSL**: HTTP only

### Production Only

- **Monitoring stack**: Prometheus, Grafana, Loki
- **SSL certificates**: Let's Encrypt
- **Security headers**: Enabled
- **Production domain**: Custom domain
- **HTTPS**: Required

## Switching Between Environments

### From Development to Production

1. **Update environment variables**:
   ```bash
   export ENVIRONMENT=production
   ```

2. **Deploy with monitoring**:
   ```bash
   docker compose --profile production up --build -d
   ```

### From Production to Development

1. **Update environment variables**:
   ```bash
   export ENVIRONMENT=development
   ```

2. **Deploy without monitoring**:
   ```bash
   docker compose up -d
   ```

## Environment Variables Reference

### Required for Both Environments

| Variable | Development | Production | Description |
|----------|-------------|------------|-------------|
| `ENVIRONMENT` | `development` | `production` | Environment identifier |
| `BOT_TOKEN` | Your test bot | Your production bot | Telegram bot token |
| `JWT_SECRET` | Generated secret | Strong secret | JWT signing secret |
| `POSTGRES_PASSWORD` | Local password | Strong password | Database password |

### Development Only

| Variable | Value | Description |
|----------|-------|-------------|
| `POSTGRES_EXTERNAL_PORT` | `5433` | External database access |
| `DOMAIN` | `localhost` | Local development domain |
| `WEBAPP_URL` | `http://localhost:3000` | Local webapp URL |

### Production Only

| Variable | Value | Description |
|----------|-------|-------------|
| `DOMAIN` | `your-domain.com` | Production domain |
| `ACME_EMAIL` | `your-email@domain.com` | SSL certificate email |
| `GRAFANA_ADMIN_PASSWORD` | Strong password | Grafana admin password |

## Quick Commands

### Development

```bash
# Start development
./scripts/dev-start.sh

# View logs
./scripts/dev-logs.sh

# Stop development
./scripts/dev-stop.sh
```

### Production

```bash
# Deploy to production
./scripts/deploy-production.sh

# Check production status
docker compose --profile production ps

# View production logs
docker compose --profile production logs -f
```

## Troubleshooting

### Common Issues

1. **Environment not detected**:
   - Check `ENVIRONMENT` variable in `.env`
   - Restart services after changing environment

2. **Monitoring not starting**:
   - Ensure `ENVIRONMENT=production`
   - Use `--profile production` flag

3. **Database connection issues**:
   - Check `POSTGRES_PASSWORD` in `.env`
   - Verify database service is running

4. **SSL certificate issues**:
   - Check `DOMAIN` and `ACME_EMAIL` variables
   - Ensure domain points to server

### Debug Commands

```bash
# Check environment
echo $ENVIRONMENT

# Check running services
docker compose ps

# Check service logs
docker compose logs service-name

# Check environment variables
docker compose config
```

## Best Practices

### Development

- Always use `ENVIRONMENT=development`
- Keep `.env` file in `.gitignore`
- Use strong passwords even locally
- Test changes before committing

### Production

- Always use `ENVIRONMENT=production`
- Use strong, unique passwords
- Enable monitoring stack
- Regular backups
- Security updates

### General

- Never commit `.env` files
- Use different tokens for dev/prod
- Test locally before production
- Keep secrets secure
- Document environment changes
