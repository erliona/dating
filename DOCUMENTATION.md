# Dating App - Complete Documentation

## 📖 Overview

This is a production-ready Telegram Mini App for dating, built with modern infrastructure and best practices.

**Key Features:**
- ✅ Full containerization with Docker
- ✅ Automated HTTPS with Let's Encrypt
- ✅ CI/CD pipeline with GitHub Actions
- ✅ Comprehensive monitoring (Prometheus, Grafana, Loki)
- ✅ PostgreSQL with async SQLAlchemy
- ✅ 254 tests with 82% code coverage

**Current Implementation Status:**
- **Epic A**: Mini App foundation & authentication ✅
- **Epic B**: Profiles, onboarding, photos, geolocation ✅
- **Epic C**: Discovery & matching (planned)
- **Epic D-H**: Additional features (planned)

## 🚀 Quick Start

### Prerequisites
- Docker & Docker Compose v2.0+
- Telegram Bot Token from [@BotFather](https://t.me/BotFather)

### Local Development

```bash
# Clone and setup
git clone https://github.com/erliona/dating.git
cd dating
cp .env.example .env
# Edit .env and set your BOT_TOKEN

# Start services
docker compose -f docker-compose.dev.yml up -d

# Check status
docker compose ps

# View logs
docker compose logs -f bot
```

### With Monitoring

```bash
# Start with monitoring stack
docker compose --profile monitoring up -d

# Access dashboards
# Grafana: http://localhost:3000 (admin/admin)
# Prometheus: http://localhost:9090
```

## 🏗️ Architecture

### Technology Stack

**Backend:**
- Python 3.11+ with asyncio
- aiogram 3.x - Telegram Bot framework
- SQLAlchemy 2.0 - Async ORM
- Alembic - Database migrations
- PostgreSQL 15 - Database

**Infrastructure:**
- Docker & Docker Compose
- Traefik 2.11 - Reverse proxy & SSL
- Let's Encrypt - Automatic SSL certificates
- nginx - Static file serving

**Monitoring:**
- Prometheus - Metrics collection
- Grafana - Dashboards and visualization
- Loki - Log aggregation
- Promtail - Log shipping

### Project Structure

```
dating/
├── bot/                      # Bot application code
│   ├── main.py              # Entry point
│   ├── api.py               # HTTP API for photos
│   ├── config.py            # Configuration
│   ├── db.py                # Database models
│   ├── repository.py        # Data access layer
│   ├── validation.py        # Input validation
│   ├── security.py          # JWT, HMAC, encryption
│   ├── geo.py               # Geolocation processing
│   ├── media.py             # Photo handling
│   └── cache.py             # Caching utilities
├── webapp/                  # Mini App frontend
│   ├── index.html          # Main page
│   ├── js/                 # JavaScript modules
│   └── css/                # Stylesheets
├── migrations/             # Database migrations
├── tests/                  # Test suite (254 tests)
├── monitoring/             # Monitoring configuration
│   ├── grafana/           # 3 dashboards
│   ├── prometheus/        # Metrics config
│   └── loki/             # Logging config
├── docs/                  # Documentation
└── docker-compose.yml    # Production compose file
```

## 🔐 Configuration

### Environment Variables

**Required:**
```bash
BOT_TOKEN=123456789:ABCdef...          # From @BotFather
POSTGRES_DB=dating                     # Database name
POSTGRES_USER=dating                   # Database user
POSTGRES_PASSWORD=secure_password      # Database password
```

**Optional (for HTTPS):**
```bash
DOMAIN=yourdomain.com                  # Your domain
WEBAPP_URL=https://${DOMAIN}           # Mini App URL
ACME_EMAIL=admin@yourdomain.com       # Let's Encrypt email
```

**See `.env.example` for complete list.**

## 💾 Database

### Migrations

```bash
# Run migrations
docker compose exec bot alembic upgrade head

# Create new migration
docker compose exec bot alembic revision --autogenerate -m "Description"

# Check current version
docker compose exec bot alembic current
```

### Password Management

**Automatic Password Migration (New!):**

The system now automatically handles password changes without requiring database resets:

```bash
# Simply update .env and restart
sed -i 's/POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=new_password/' .env
docker compose restart bot

# The bot automatically detects and fixes password mismatches
```

**Features:**
- ✅ Automatic password synchronization
- ✅ Exponential backoff for database connections
- ✅ Enhanced environment variable validation
- ✅ No data loss on password changes

See `docs/DATA_PERSISTENCE.md` for detailed password change procedures.

### Backup & Restore

```bash
# Create backup
docker compose exec db pg_dump -U dating dating > backup.sql

# Restore from backup
docker compose exec -T db psql -U dating dating < backup.sql
```

## 🧪 Testing

### Run Tests

```bash
# All tests
python -m pytest tests/ -v

# With coverage
python -m pytest tests/ --cov=bot --cov-report=html

# Specific test file
python -m pytest tests/test_validation.py -v
```

### Test Coverage

Current coverage: **82%**
- 254 tests passing
- bot/validation.py: 92%
- bot/main.py: 97%
- bot/geo.py: 97%
- bot/db.py: 100%
- bot/cache.py: 100%

## 📊 Monitoring

### Grafana Dashboards

**1. System Overview** - Infrastructure metrics
- Container CPU and memory usage
- PostgreSQL connections
- Network traffic
- All logs with JSON parsing

**2. Application Logs & Events** - Application monitoring
- Bot lifecycle events
- Error and warning counts
- Log levels over time
- Structured event logging

**3. Discovery & Matching** - User interaction metrics
- Discovery actions
- Likes, passes, matches
- User actions distribution

### Accessing Dashboards

```bash
# Start with monitoring
docker compose --profile monitoring up -d

# Access Grafana
open http://localhost:3000  # Default: admin/admin

# Check Prometheus
open http://localhost:9090
```

### Structured Logging

All logs are JSON formatted with:
- Timestamp (ISO 8601)
- Level (INFO, WARNING, ERROR)
- Logger name
- Message
- Module, function, line number
- Custom fields (user_id, event_type, etc.)

## 🚢 Deployment

### Production Deployment

**Using GitHub Actions (Recommended):**

1. Configure GitHub Secrets:
   - `DEPLOY_HOST` - Server IP/hostname
   - `DEPLOY_USER` - SSH user
   - `DEPLOY_SSH_KEY` - Private SSH key
   - `BOT_TOKEN` - Telegram bot token

2. Push to main branch - automatic deployment!

**Manual Deployment:**

```bash
# On server
git pull origin main
docker compose up -d --build

# Check status
docker compose ps

# View logs
docker compose logs -f
```

### Updating

```bash
# Pull latest changes
git pull origin main

# Restart services
docker compose restart bot webapp

# Apply migrations
docker compose exec bot alembic upgrade head
```

## 🛡️ Security

### Best Practices
- ✅ All secrets in environment variables
- ✅ HTTPS everywhere via Traefik
- ✅ JWT authentication for API
- ✅ HMAC validation for Telegram data
- ✅ SQL injection protection via ORM
- ✅ No hardcoded credentials
- ✅ Automated security scanning in CI

### Reporting Security Issues

Email security concerns to the repository owner. Do not create public issues for security vulnerabilities.

## 🐛 Troubleshooting

### Bot Not Responding

```bash
# Check logs
docker compose logs -f bot

# Restart bot
docker compose restart bot

# Check bot status
docker compose ps
```

### Database Connection Issues

```bash
# Check database status
docker compose ps db

# View database logs
docker compose logs db

# Test connection
docker compose exec db psql -U dating -d dating -c "SELECT 1;"
```

### Grafana Not Loading

```bash
# Restart Grafana
docker compose --profile monitoring restart grafana

# Check logs
docker compose logs grafana

# Verify datasources
curl -u admin:admin http://localhost:3000/api/datasources
```

## 📚 Additional Resources

### Documentation
- [Full Documentation Index](docs/INDEX.md)
- [Architecture Details](docs/ARCHITECTURE.md)
- [Deployment Guide](docs/DEPLOYMENT.md)
- [Testing Guide](docs/TESTING.md)
- [API Documentation](docs/PHOTO_UPLOAD_API.md)

### Development
- [Contributing Guidelines](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)
- [Roadmap](ROADMAP.md)
- [Project Status](PROJECT_STATUS.md)

### External Links
- [GitHub Repository](https://github.com/erliona/dating)
- [GitHub Issues](https://github.com/erliona/dating/issues)
- [Telegram Bot API](https://core.telegram.org/bots/api)
- [aiogram Documentation](https://docs.aiogram.dev/)

## 🤝 Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for:
- Code of conduct
- Development setup
- Pull request process
- Coding standards

## 📄 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

## 💬 Support

- **Documentation**: See [docs/](docs/)
- **Bug Reports**: [GitHub Issues](https://github.com/erliona/dating/issues)
- **Questions**: [GitHub Discussions](https://github.com/erliona/dating/discussions)

---

**Made with ❤️ for the community**

*If you find this project useful, please star it on GitHub!* ⭐
