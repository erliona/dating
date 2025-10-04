# CI/CD Workflows Overview

## Workflow Triggers

```
┌─────────────────────────────────────────────────────────────────┐
│                         GitHub Events                            │
└─────────────────────────────────────────────────────────────────┘
                              │
            ┌─────────────────┼─────────────────┐
            │                 │                 │
            ▼                 ▼                 ▼
     ┌──────────┐      ┌──────────┐     ┌──────────┐
     │   Push   │      │    PR    │     │ Schedule │
     │  (main)  │      │  Events  │     │ (cron)   │
     └──────────┘      └──────────┘     └──────────┘
            │                 │                 │
            └─────────────────┼─────────────────┘
                              ▼
          ┌───────────────────────────────────────┐
          │        Workflow Execution             │
          └───────────────────────────────────────┘
```

## Workflow Matrix

| Workflow | Push (main) | Push (develop) | Pull Request | Schedule | Manual |
|----------|------------|----------------|--------------|----------|--------|
| **test.yml** | ✅ | ✅ | ✅ | ❌ | ❌ |
| **lint.yml** | ✅ | ✅ | ✅ | ❌ | ❌ |
| **docker-build.yml** | ✅ | ✅ | ✅ | ❌ | ❌ |
| **pr-validation.yml** | ❌ | ❌ | ✅ | ❌ | ❌ |
| **deploy-microservices.yml** | ✅ | ❌ | ❌ | ❌ | ✅ |
| **health-check.yml** | ❌ | ❌ | ❌ | ✅ (6h) | ✅ |

## Pipeline Flow

### On Pull Request

```
Pull Request Created/Updated
    │
    ├─→ [test.yml] Run Tests
    │   ├─ Setup Python & PostgreSQL
    │   ├─ Install dependencies
    │   ├─ Run pytest
    │   └─ Upload coverage
    │
    ├─→ [lint.yml] Code Quality
    │   ├─ Black (formatting)
    │   ├─ isort (imports)
    │   ├─ flake8 (linting)
    │   ├─ mypy (type checking)
    │   └─ pip-audit (security)
    │
    ├─→ [docker-build.yml] Build Validation
    │   ├─ Validate docker-compose.yml
    │   └─ Build all services (parallel)
    │
    └─→ [pr-validation.yml] Comprehensive Check
        ├─ All quality checks
        ├─ Full test suite
        ├─ Security scan
        └─ Generate PR summary
```

### On Push to Main

```
Push to main branch
    │
    ├─→ [test.yml] Tests (parallel)
    ├─→ [lint.yml] Code Quality (parallel)
    └─→ [docker-build.yml] Build (parallel)
    
    If all pass ↓
    
    [deploy-microservices.yml] Deployment Pipeline
    │
    ├─ Stage 1: Test
    │  ├─ Setup environment
    │  ├─ Run full test suite
    │  └─ Verify tests pass
    │
    ├─ Stage 2: Build
    │  ├─ Validate docker-compose
    │  └─ Build all Docker images
    │
    ├─ Stage 3: Deploy
    │  ├─ Setup SSH connection
    │  ├─ Create deployment archive
    │  ├─ Copy files to server
    │  ├─ Generate configuration
    │  ├─ Stop old services
    │  ├─ Build new images
    │  ├─ Start services
    │  └─ Wait for stabilization
    │
    └─ Stage 4: Verify
       ├─ Check container status
       ├─ Health endpoint checks
       ├─ Service validation
       └─ Generate summary
```

### Scheduled Health Checks

```
Every 6 hours (or manual trigger)
    │
    └─→ [health-check.yml] Monitor Production
        │
        ├─ Connect to server via SSH
        ├─ Check container status
        ├─ Test health endpoints
        ├─ Verify all services running
        ├─ Check resource usage
        │
        ├─ If healthy: ✅ Log success
        └─ If unhealthy: ❌ Create GitHub issue
```

## Workflow Details

### 1. test.yml - Testing
- **Purpose**: Run all unit and integration tests
- **Duration**: ~5-10 minutes
- **Key Steps**:
  - PostgreSQL test database
  - Python 3.12 setup
  - Pytest with coverage
  - Codecov upload

### 2. lint.yml - Code Quality
- **Purpose**: Ensure code quality and security
- **Duration**: ~3-5 minutes
- **Tools**:
  - Black (code formatting)
  - isort (import sorting)
  - flake8 (linting)
  - mypy (type checking)
  - pip-audit (security)

### 3. docker-build.yml - Build Validation
- **Purpose**: Validate Docker builds
- **Duration**: ~10-15 minutes
- **Strategy**: Parallel matrix build
- **Services**: 7 services built in parallel

### 4. pr-validation.yml - PR Checks
- **Purpose**: Comprehensive pre-merge validation
- **Duration**: ~10-15 minutes
- **Features**:
  - All quality checks
  - Full test suite
  - Security scan
  - Automated summary

### 5. deploy-microservices.yml - Deployment
- **Purpose**: Deploy to production
- **Duration**: ~15-25 minutes
- **Stages**: Test → Build → Deploy → Verify
- **Features**:
  - Multi-stage pipeline
  - Automatic rollback on failure
  - Health verification
  - Service validation

### 6. health-check.yml - Monitoring
- **Purpose**: Monitor production health
- **Duration**: ~2-3 minutes
- **Schedule**: Every 6 hours
- **Features**:
  - Service health checks
  - Resource monitoring
  - Auto-issue creation on failure

## Success Criteria

### For Pull Requests
✅ All tests pass
✅ Code quality checks pass
✅ Docker builds succeed
✅ No critical security vulnerabilities

### For Deployment
✅ Tests pass (Stage 1)
✅ Builds succeed (Stage 2)
✅ Deployment completes (Stage 3)
✅ All services healthy (Stage 4)

### For Health Checks
✅ All containers running
✅ All health endpoints responding
✅ No stopped services
✅ Resource usage normal

## Failure Handling

### Test Failures
- ❌ Block PR merge
- 📧 Notify developer
- 📝 Show detailed error logs

### Build Failures
- ❌ Block deployment
- 📧 Notify team
- 🔍 Show build logs

### Deployment Failures
- ❌ Stop deployment
- 🔄 Keep previous version running
- 🚨 Alert on-call engineer
- 📝 Detailed failure logs

### Health Check Failures
- 🐛 Create GitHub issue
- 📧 Notify team
- 📊 Include metrics
- 🔗 Link to logs

## Metrics & Monitoring

### Pipeline Metrics
- Test execution time
- Build duration
- Deployment frequency
- Success/failure rates

### Service Metrics
- Service uptime
- Health check status
- Resource usage
- Error rates

## Quick Commands

### Trigger Workflows Manually
```bash
# In GitHub UI:
Actions → Select Workflow → Run workflow

# Using GitHub CLI:
gh workflow run test.yml
gh workflow run lint.yml
gh workflow run deploy-microservices.yml
```

### View Workflow Status
```bash
# Recent runs
gh run list --workflow=test.yml

# Specific run details
gh run view <run-id>

# Watch a running workflow
gh run watch
```

### Check Deployment Status
```bash
# SSH to server
ssh user@server

# Check services
cd /opt/dating-microservices
docker compose ps

# View logs
docker compose logs -f
```

## Best Practices

1. **Always create PRs** - Never push directly to main
2. **Fix failing tests** - Don't merge with failing checks
3. **Review security alerts** - Address pip-audit findings
4. **Monitor deployments** - Watch logs after deploy
5. **Keep secrets secure** - Use GitHub Secrets, never commit

## Troubleshooting

### "Tests failing locally but pass in CI"
- Check Python version (should be 3.12)
- Verify PostgreSQL is running
- Check environment variables

### "Docker build fails in CI"
- Test build locally: `docker compose build`
- Check Dockerfile syntax
- Verify dependencies in requirements.txt

### "Deployment stuck"
- Check server accessibility
- Verify SSH key is correct
- Check server disk space
- Review deployment logs

### "Health checks failing"
- SSH to server and check logs
- Verify services are running
- Test health endpoints manually
- Check resource usage

## References

- [CI/CD Guide](../docs/CI_CD_GUIDE.md)
- [Deployment Troubleshooting](../docs/DEPLOYMENT_TROUBLESHOOTING.md)
- [README](../README.md)
