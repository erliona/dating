# GitHub Configuration

This directory contains GitHub-specific configuration for the Dating App project.

## Contents

### Workflows (`workflows/`)
- **`test.yml`** - Automated testing pipeline (unit, integration, e2e tests)

### Documentation
- **`SECRETS_SETUP.md`** - Guide for configuring GitHub Secrets for CI/CD

## Quick Start

### 1. Setup GitHub Secrets
Before running workflows, configure required secrets:
```
TEST_JWT_SECRET     - JWT secret for tests
TEST_BOT_TOKEN      - Telegram bot token for tests  
CODECOV_TOKEN       - Coverage upload token
```

See [SECRETS_SETUP.md](SECRETS_SETUP.md) for detailed instructions.

### 2. Run Tests Locally
```bash
# Unit tests (fast, ~2 seconds)
pytest tests/unit/ -v -m unit

# Integration tests (medium, ~4 seconds)  
pytest tests/integration/ -v -m integration

# E2E tests (slow, ~3 seconds)
pytest tests/e2e/ -v -m e2e

# All tests with coverage
pytest --cov=bot --cov=core --cov=services --cov-report=html
```

### 3. CI/CD Pipeline

Tests run automatically on:
- **Push** to `main` or `develop` branches
- **Pull requests** to `main` or `develop` branches  
- **E2E tests** only run on push to main/develop OR when PR has `e2e` label

## Test Pipeline Stages

1. **Unit Tests** (10 min timeout)
   - Fast, isolated component tests
   - No external dependencies
   - Coverage: bot, core modules

2. **Integration Tests** (15 min timeout)
   - Component interaction tests
   - PostgreSQL database required
   - Database migrations applied
   - Coverage: bot, core, services

3. **E2E Tests** (20 min timeout)
   - Complete user flow tests
   - Full system integration
   - Only runs on main/develop or with `e2e` label
   - Coverage: entire application

## Coverage Reports

Coverage reports are uploaded to [Codecov](https://codecov.io) automatically.

View coverage:
- Badge: See main README.md
- Dashboard: https://codecov.io/gh/erliona/dating
- PR Comments: Codecov bot comments on PRs with coverage changes

## Adding New Workflows

When adding new workflows:
1. Create `.github/workflows/your-workflow.yml`
2. Follow naming convention: `kebab-case.yml`
3. Add concurrency groups to prevent conflicts
4. Document in this README
5. Test workflow before merging to main

## Troubleshooting

### Tests fail in CI but pass locally
- Check Python version (CI uses 3.11)
- Verify all dependencies in requirements.txt
- Check environment variables
- Review GitHub Actions logs

### Secret not found
- Verify secrets are added in repository settings
- Check secret names match exactly
- See [SECRETS_SETUP.md](SECRETS_SETUP.md)

### Coverage upload fails  
- Verify CODECOV_TOKEN is set
- Check repository is registered on codecov.io
- Review Codecov action logs

## Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [pytest Documentation](https://docs.pytest.org/)
- [Project Testing Guide](../tests/README.md)

