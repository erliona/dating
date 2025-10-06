# CI/CD Guide

This document describes the continuous integration and deployment setup for the Dating application.

## Overview

The CI/CD pipeline is built using GitHub Actions and includes:

1. **Automated Testing** - Run tests on every push and pull request
2. **Code Quality Checks** - Linting, formatting, and security scanning
3. **Docker Build Validation** - Ensure all services can be built
4. **Automated Deployment** - Deploy to production on main branch
5. **Health Monitoring** - Periodic health checks of production services

## Workflows

### 1. Test Workflow (`test.yml`)

**Triggers:** Push to main/develop, Pull Requests

**Purpose:** Run all unit and integration tests

**Steps:**
- Set up Python 3.12
- Install dependencies
- Run PostgreSQL test database
- **Wait for PostgreSQL to be ready** (explicit health check)
- **Apply database migrations** (alembic upgrade head)
- Execute pytest with coverage
- Upload coverage reports to Codecov

**Configuration:**
```yaml
env:
  DATABASE_URL: postgresql+asyncpg://dating:test_password@localhost:5432/dating_test
  BOT_DATABASE_URL: postgresql+asyncpg://dating:test_password@localhost:5432/dating_test
  BOT_TOKEN: test:token
  JWT_SECRET: test-secret-key-for-testing-32chars
  API_GATEWAY_URL: http://localhost:8080
```

**Important:** The workflow now includes explicit database readiness checks and applies migrations before running tests to prevent tests from hanging on database connection issues.

### 2. Code Quality Workflow (`lint.yml`)

**Triggers:** Push to main/develop, Pull Requests

**Purpose:** Ensure code quality and security

**Checks:**
- **Black** - Code formatting
- **isort** - Import sorting
- **flake8** - Linting and style checks
- **mypy** - Type checking
- **pip-audit** - Security vulnerability scanning

**Usage:**
```bash
# Fix formatting issues locally
black .
isort .
```

### 3. Docker Build Workflow (`docker-build.yml`)

**Triggers:** Push to main/develop, Pull Requests

**Purpose:** Validate that all Docker images can be built successfully

**Services Validated:**
- auth-service
- profile-service
- discovery-service
- media-service
- chat-service
- api-gateway
- telegram-bot

**Features:**
- Parallel builds using matrix strategy
- Docker layer caching for faster builds
- docker-compose.yml validation

### 4. PR Validation Workflow (`pr-validation.yml`)

**Triggers:** Pull Request events (opened, synchronize, reopened)

**Purpose:** Comprehensive validation before merging

**Includes:**
- All code quality checks
- Full test suite
- Docker configuration validation
- Security vulnerability scanning
- Automated summary in PR comments

### 5. Deployment Workflow (`deploy-microservices.yml`)

**Triggers:** 
- Push to main branch
- Manual trigger (workflow_dispatch)

**Purpose:** Deploy application to production server

**Pipeline Stages:**

1. **Test Stage** - Run full test suite
2. **Build Stage** - Validate Docker builds
3. **Deploy Stage** - Deploy to production server
4. **Verify Stage** - Health checks and validation

**Required Secrets:**
| Secret | Description | Example |
|--------|-------------|---------|
| `DEPLOY_HOST` | Server IP or hostname | `123.45.67.89` |
| `DEPLOY_USER` | SSH user with sudo | `ubuntu` |
| `DEPLOY_SSH_KEY` | Private SSH key | `-----BEGIN RSA...` |
| `BOT_TOKEN` | Telegram bot token | `123456789:ABC...` |
| `JWT_SECRET` | JWT signing secret | `random-secret-32+` |
| `DOMAIN` | Domain for HTTPS (optional) | `dating.example.com` |
| `ACME_EMAIL` | Let's Encrypt email (optional) | `admin@example.com` |
| `POSTGRES_PASSWORD` | Database password (optional, auto-generated if not set) | `secure-password` |

**Deployment Process:**
1. Create deployment archive (excludes .git, __pycache__, etc.)
2. Copy files to server via SSH
3. Generate/update .env configuration
4. Install Docker if needed
5. Stop existing services cleanly
6. Build new images
7. Start services with docker-compose
8. Wait for services to stabilize
9. Run health checks
10. Verify all services are running

**Post-Deployment Verification:**
- Container status check
- Health endpoint checks (ports 8080-8085)
- Service running validation

### 6. Health Check Workflow (`health-check.yml`)

**Triggers:** 
- Schedule (every 6 hours)
- Manual trigger

**Purpose:** Monitor production service health

**Checks:**
- Container status
- Health endpoints availability
- Service uptime
- Resource usage

**Features:**
- Automatic issue creation on failure
- Detailed health reports in job summary
- SSH-based remote monitoring

## Setting Up CI/CD

### 1. Configure GitHub Secrets

Go to **Settings → Secrets and variables → Actions** and add:

**Required for deployment:**
- `DEPLOY_HOST`
- `DEPLOY_USER`
- `DEPLOY_SSH_KEY`
- `BOT_TOKEN`
- `JWT_SECRET`

**Optional for HTTPS:**
- `DOMAIN`
- `ACME_EMAIL`

**Optional for coverage:**
- `CODECOV_TOKEN`

### 2. Prepare SSH Key

```bash
# Generate SSH key pair
ssh-keygen -t rsa -b 4096 -f ~/.ssh/dating_deploy -N ""

# Copy public key to server
ssh-copy-id -i ~/.ssh/dating_deploy.pub user@server

# Add private key to GitHub secrets
cat ~/.ssh/dating_deploy
# Copy the entire output including BEGIN/END lines
```

### 3. Server Requirements

- Ubuntu 20.04+ or similar Linux distribution
- Docker and Docker Compose installed (will be auto-installed if missing)
- Ports 80, 443 (if using HTTPS), 8080-8085 available
- At least 2GB RAM, 20GB disk space

### 4. Test Deployment

```bash
# Trigger manual deployment
# Go to Actions → Deploy to Production → Run workflow
```

## Monitoring and Maintenance

### View Workflow Runs

1. Go to **Actions** tab in GitHub
2. Select a workflow from the left sidebar
3. Click on a specific run to see details

### Check Deployment Status

```bash
# SSH to server
ssh user@your-server

# Check container status
cd /opt/dating-microservices
docker compose ps

# View logs
docker compose logs -f

# Check specific service
docker compose logs -f api-gateway
```

### Manual Deployment

If automated deployment fails:

```bash
# Clone repository on server
git clone https://github.com/erliona/dating.git /opt/dating-microservices
cd /opt/dating-microservices

# Create .env file
cp .env.example .env
nano .env  # Edit with your values

# Deploy
docker compose build
docker compose up -d

# Verify
docker compose ps
```

### Rollback

```bash
# SSH to server
ssh user@your-server
cd /opt/dating-microservices

# Pull previous version
git log --oneline -10  # Find commit hash
git checkout <previous-commit-hash>

# Redeploy
docker compose down
docker compose build
docker compose up -d
```

## Troubleshooting

### Deployment Fails

1. **Check workflow logs** in GitHub Actions
2. **Verify secrets** are configured correctly
3. **SSH to server** and check logs: `docker compose logs`
4. **Check disk space**: `df -h`
5. **Verify ports**: `netstat -tuln | grep LISTEN`

### Tests Failing

1. **Run tests locally**: `pytest tests/ -v`
2. **Check database connection** in test environment
3. **Verify dependencies** are up to date: `pip install -r requirements-dev.txt`
4. **Ensure database is ready**: The test workflow now explicitly waits for PostgreSQL and applies migrations
5. **Check migrations**: If tests hang, migrations may not have been applied: `alembic upgrade head`

### Health Checks Failing

1. **Check service logs**: `docker compose logs <service-name>`
2. **Verify configuration**: `docker compose config`
3. **Test health endpoints**: `curl http://localhost:8080/health`
4. **Restart services**: `docker compose restart`

### Build Failures

1. **Validate Dockerfile syntax**
2. **Check for missing dependencies** in requirements.txt
3. **Test build locally**: `docker compose build <service-name>`
4. **Clear Docker cache**: `docker builder prune`

## Best Practices

### For Developers

1. **Always create a branch** for new features
2. **Run tests locally** before pushing: `pytest tests/`
3. **Format code** before committing: `black . && isort .`
4. **Update tests** when changing functionality
5. **Keep commits focused** and well-documented

### For Deployments

1. **Test in staging** before production (if available)
2. **Monitor logs** during and after deployment
3. **Keep secrets secure** - never commit to repository
4. **Backup database** before major changes
5. **Document configuration changes**

### Security

1. **Rotate secrets** regularly
2. **Use strong passwords** for all services
3. **Keep dependencies updated**: `pip-audit`
4. **Review security alerts** from GitHub
5. **Enable 2FA** on GitHub account

## Performance Optimization

### CI/CD Pipeline

- **Use caching** for pip dependencies (already configured)
- **Run tests in parallel** where possible
- **Skip unnecessary steps** on documentation-only changes

### Docker Builds

- **Use layer caching** (already configured)
- **Optimize Dockerfile** layer ordering
- **Use multi-stage builds** where beneficial
- **.dockerignore** to exclude unnecessary files

## Future Improvements

Potential enhancements to consider:

1. **Staging environment** - Add separate staging deployment
2. **Database migrations** - Automated migration runs
3. **Blue-green deployment** - Zero-downtime deployments
4. **Integration tests** - API endpoint testing
5. **Performance tests** - Load testing automation
6. **Security scanning** - Container vulnerability scanning
7. **Rollback automation** - Automatic rollback on failure
8. **Slack notifications** - Deployment status alerts
9. **Metrics collection** - CI/CD performance tracking
10. **Self-hosted runners** - Faster builds with dedicated hardware

## Support

For issues or questions:

1. Check existing [GitHub Issues](https://github.com/erliona/dating/issues)
2. Review [Deployment Troubleshooting Guide](./DEPLOYMENT_TROUBLESHOOTING.md)
3. Create a new issue with:
   - Workflow run URL
   - Error messages
   - Steps to reproduce
   - Environment details

## References

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Pytest Documentation](https://docs.pytest.org/)
- [Project README](../README.md)
