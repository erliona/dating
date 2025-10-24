# Versioning & Release Management

## Overview

This document defines the versioning strategy, release process, and artifact management for the dating application project.

## Semantic Versioning

### Version Format

**Pattern:** `vMAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes (API changes, database schema changes)
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Version Examples

```
v1.0.0  - Initial release
v1.1.0  - New feature: JWT refresh tokens
v1.1.1  - Bug fix: resolve auth timeout
v1.2.0  - New feature: admin panel
v2.0.0  - Breaking: API v2, new database schema
```

### Pre-release Versions

```
v1.2.0-alpha.1    - Alpha release
v1.2.0-beta.1     - Beta release
v1.2.0-rc.1       - Release candidate
v1.2.0            - Final release
```

## Release Process

### 1. Development Workflow

```bash
# Feature development
git checkout -b feature/jwt-refresh
# ... make changes ...
git commit -m "feat(auth): add JWT refresh endpoint"
git push origin feature/jwt-refresh

# Create PR
# ... review and merge to main ...

# Release preparation
git checkout main
git pull origin main
```

### 2. Automated Release Process

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    branches: [main]
    tags: [v*]

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Setup Git
        run: |
          git config --global user.name "Release Bot"
          git config --global user.email "bot@dating.serge.cc"
      
      - name: Generate Changelog
        run: |
          git cliff --output CHANGELOG.md
          git add CHANGELOG.md
          git commit -m "chore: update changelog" || exit 0
      
      - name: Create Release
        uses: actions/create-release@v1
        with:
          tag_name: ${{ github.ref_name }}
          release_name: Release ${{ github.ref_name }}
          body_path: CHANGELOG.md
          draft: false
          prerelease: ${{ contains(github.ref_name, 'alpha') || contains(github.ref_name, 'beta') || contains(github.ref_name, 'rc') }}
```

### 3. Manual Release Process

```bash
# 1. Update version in pyproject.toml
# 2. Generate changelog
git cliff --output CHANGELOG.md

# 3. Create release commit
git add CHANGELOG.md pyproject.toml
git commit -m "chore: release v1.2.0"

# 4. Create tag
git tag -a v1.2.0 -m "Release v1.2.0"
git push origin v1.2.0

# 5. Create GitHub release
gh release create v1.2.0 --title "Release v1.2.0" --notes-file CHANGELOG.md
```

## Artifact Management

### Docker Images

#### Registry Configuration

```yaml
# docker-compose.yml
services:
  api-gateway:
    image: ghcr.io/erliona/dating/api-gateway:v1.2.0
    build:
      context: .
      dockerfile: services/api-gateway/Dockerfile
      tags:
        - ghcr.io/erliona/dating/api-gateway:latest
        - ghcr.io/erliona/dating/api-gateway:v1.2.0
        - ghcr.io/erliona/dating/api-gateway:v1.2
        - ghcr.io/erliona/dating/api-gateway:v1
```

#### Image Tagging Strategy

```bash
# Production images
ghcr.io/erliona/dating/api-gateway:v1.2.0    # Specific version
ghcr.io/erliona/dating/api-gateway:v1.2      # Minor version
ghcr.io/erliona/dating/api-gateway:v1        # Major version
ghcr.io/erliona/dating/api-gateway:latest    # Latest stable

# Development images
ghcr.io/erliona/dating/api-gateway:main      # Latest from main branch
ghcr.io/erliona/dating/api-gateway:feature/jwt-refresh  # Feature branch
```

#### Registry Locations

| Service | Registry | Repository | Tags |
|---------|----------|------------|------|
| API Gateway | `ghcr.io/erliona/dating` | `api-gateway` | `v1.2.0`, `latest` |
| Auth Service | `ghcr.io/erliona/dating` | `auth-service` | `v1.2.0`, `latest` |
| Profile Service | `ghcr.io/erliona/dating` | `profile-service` | `v1.2.0`, `latest` |
| Discovery Service | `ghcr.io/erliona/dating` | `discovery-service` | `v1.2.0`, `latest` |
| Media Service | `ghcr.io/erliona/dating` | `media-service` | `v1.2.0`, `latest` |
| Chat Service | `ghcr.io/erliona/dating` | `chat-service` | `v1.2.0`, `latest` |
| Admin Service | `ghcr.io/erliona/dating` | `admin-service` | `v1.2.0`, `latest` |
| Telegram Bot | `ghcr.io/erliona/dating` | `telegram-bot` | `v1.2.0`, `latest` |
| Webapp | `ghcr.io/erliona/dating` | `webapp` | `v1.2.0`, `latest` |

### Production Deployment

#### Environment Configuration

```bash
# Production environment variables
PRODUCTION_TAG=v1.2.0
REGISTRY_URL=ghcr.io/erliona/dating
ENVIRONMENT=production
```

#### Deployment Commands

```bash
# Deploy specific version
docker compose -f docker-compose.prod.yml pull
docker compose -f docker-compose.prod.yml up -d

# Deploy latest version
docker compose -f docker-compose.prod.yml pull --ignore-pull-failures
docker compose -f docker-compose.prod.yml up -d

# Rollback to previous version
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml up -d
```

## Changelog Generation

### Git Cliff Configuration

```toml
# cliff.toml
[changelog]
header = "## Changelog"
body = """
## [{{ version }}] - {{ date | date(format="%Y-%m-%d") }}
{% for group, commits in commits | group_by(scope) %}
### {{ group | upper_first }}
{% for commit in commits %}
- {{ commit.message | upper_first }}
{% endfor %}
{% endfor %}
"""
footer = "Full Changelog: https://github.com/erliona/dating/compare/{{ previous_tag }}...{{ tag }}"

[git]
conventional_commits = true
filter_unconventional = true
split_commits = true
commit_parsers = [
    { message = "^feat", group = "Features" },
    { message = "^fix", group = "Bug Fixes" },
    { message = "^docs", group = "Documentation" },
    { message = "^style", group = "Styling" },
    { message = "^refactor", group = "Code Refactoring" },
    { message = "^perf", group = "Performance" },
    { message = "^test", group = "Tests" },
    { message = "^build", group = "Build System" },
    { message = "^ci", group = "Continuous Integration" },
    { message = "^chore", group = "Chores" },
    { message = "^revert", group = "Reverts" },
    { message = "^security", group = "Security" },
    { message = "^deps", group = "Dependencies" },
    { message = "^config", group = "Configuration" },
]
```

### Changelog Example

```markdown
## Changelog

## [1.2.0] - 2024-01-15

### Features
- Add JWT token refresh endpoint
- Implement admin panel user management
- Add photo upload with NSFW detection

### Bug Fixes
- Fix authentication timeout issue
- Resolve database connection pool exhaustion
- Correct Traefik routing for admin panel

### Documentation
- Add comprehensive API documentation
- Update deployment procedures
- Add troubleshooting guide

### Security
- Implement JWT key rotation policy
- Add rate limiting to auth endpoints
- Enhance input validation

### Dependencies
- Update aiohttp to 3.9.0
- Upgrade SQLAlchemy to 2.0.0
- Add new monitoring dependencies
```

## Release Automation

### GitHub Actions Workflow

```yaml
# .github/workflows/release.yml
name: Release

on:
  push:
    branches: [main]
  workflow_dispatch:
    inputs:
      version:
        description: 'Version to release'
        required: true
        default: 'patch'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4
        with:
          fetch-depth: 0
          token: ${{ secrets.GITHUB_TOKEN }}
      
      - name: Setup Git
        run: |
          git config --global user.name "Release Bot"
          git config --global user.email "bot@dating.serge.cc"
      
      - name: Generate Changelog
        run: |
          git cliff --output CHANGELOG.md
          git add CHANGELOG.md
          git commit -m "chore: update changelog" || exit 0
      
      - name: Create Release
        uses: actions/create-release@v1
        with:
          tag_name: ${{ github.ref_name }}
          release_name: Release ${{ github.ref_name }}
          body_path: CHANGELOG.md
          draft: false
          prerelease: ${{ contains(github.ref_name, 'alpha') || contains(github.ref_name, 'beta') || contains(github.ref_name, 'rc') }}
      
      - name: Build and Push Images
        run: |
          docker buildx create --use
          docker buildx build --platform linux/amd64,linux/arm64 \
            --push \
            --tag ghcr.io/erliona/dating/api-gateway:${{ github.ref_name }} \
            --tag ghcr.io/erliona/dating/api-gateway:latest \
            -f services/api-gateway/Dockerfile .
```

### Semantic Release Configuration

```json
{
  "branches": [
    "main",
    {
      "name": "beta",
      "prerelease": true
    }
  ],
  "plugins": [
    "@semantic-release/commit-analyzer",
    "@semantic-release/release-notes-generator",
    "@semantic-release/changelog",
    "@semantic-release/git",
    "@semantic-release/github"
  ]
}
```

## Version Management

### Version Bumping

```bash
# Patch version (bug fixes)
npm version patch
git push origin v1.2.1

# Minor version (new features)
npm version minor
git push origin v1.3.0

# Major version (breaking changes)
npm version major
git push origin v2.0.0
```

### Version Validation

```bash
# Check current version
git describe --tags --abbrev=0

# List all versions
git tag --sort=-version:refname

# Check version consistency
docker images | grep ghcr.io/erliona/dating
```

## Release Notes

### Template

```markdown
# Release v1.2.0

## 🚀 New Features
- JWT token refresh endpoint
- Admin panel user management
- Photo upload with NSFW detection

## 🐛 Bug Fixes
- Fix authentication timeout issue
- Resolve database connection pool exhaustion
- Correct Traefik routing for admin panel

## 📚 Documentation
- Add comprehensive API documentation
- Update deployment procedures
- Add troubleshooting guide

## 🔒 Security
- Implement JWT key rotation policy
- Add rate limiting to auth endpoints
- Enhance input validation

## 📦 Dependencies
- Update aiohttp to 3.9.0
- Upgrade SQLAlchemy to 2.0.0
- Add new monitoring dependencies

## 🚨 Breaking Changes
- None

## 📋 Migration Guide
- No migration required

## 🔗 Links
- [Full Changelog](https://github.com/erliona/dating/compare/v1.1.0...v1.2.0)
- [Documentation](https://docs.dating.serge.cc)
- [API Reference](https://api.dating.serge.cc/docs)
```

## Rollback Procedures

### Image Rollback

```bash
# Rollback to previous version
docker compose -f docker-compose.prod.yml down
docker compose -f docker-compose.prod.yml pull ghcr.io/erliona/dating/api-gateway:v1.1.0
docker compose -f docker-compose.prod.yml up -d

# Verify rollback
docker compose -f docker-compose.prod.yml ps
curl http://localhost:8080/health
```

### Database Rollback

```bash
# Rollback database migrations
docker compose exec -T db alembic downgrade -1

# Verify database state
docker compose exec -T db psql -U dating -d dating -c "SELECT version_num FROM alembic_version;"
```

## Monitoring Releases

### Release Metrics

```yaml
# Prometheus metrics
release_deployment_duration_seconds
release_rollback_count_total
release_success_rate
release_failure_rate
```

### Health Checks

```bash
# Post-deployment health check
./scripts/health_check.sh

# Service-specific checks
curl http://localhost:8080/health
curl http://localhost:8080/api/v1/auth/health
curl http://localhost:8080/admin/auth/login
```

## Best Practices

### Release Planning

1. **Feature Freeze**: 1 week before release
2. **Testing**: Comprehensive testing of all features
3. **Documentation**: Update all relevant documentation
4. **Changelog**: Generate and review changelog
5. **Announcement**: Notify team and users

### Quality Gates

1. **All tests pass**: Unit, integration, E2E
2. **Security scan**: No high/critical vulnerabilities
3. **Performance**: Meets SLO requirements
4. **Documentation**: Up-to-date and complete
5. **Monitoring**: All alerts configured

### Communication

1. **Release notes**: Clear and comprehensive
2. **Breaking changes**: Clearly documented
3. **Migration guide**: Step-by-step instructions
4. **Support**: Contact information for issues
5. **Timeline**: Release schedule and maintenance windows
