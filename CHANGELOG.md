# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- **Documentation Complete Refresh (2025-01)** - Comprehensive update of all project documentation
  - Updated README.md with accurate stats: Python 3.12, 380+ tests, 7 microservices
  - Updated tech stack documentation: Next.js 15, React 19, Tailwind CSS v4
  - Updated CONTRIBUTING.md with Python 3.12 requirement
  - Updated ROADMAP.md with implemented features section (Chat Service, Admin Panel)
  - Updated docs/TEST_REFACTORING_2024.md with current test count
  - Clarified microservices architecture with all 7 services and ports
  - Updated Frontend stack to reflect Next.js 15 webapp alongside Telegram Mini App
  - All documentation now reflects current project state accurately

### Fixed
- **Timezone Issue Across All Tables** - Fixed timezone-aware datetime handling for ALL database models
  - Updated ALL models (User, Profile, Photo, Interaction, Match, Favorite, Admin) to use `DateTime(timezone=True)`
  - Created migration `005_fix_profile_tables_timezone.py` to convert users, profiles, and photos tables from TIMESTAMP to TIMESTAMPTZ
  - Created migration `006_fix_discovery_tables_timezone.py` to convert interactions, matches, and favorites tables from TIMESTAMP to TIMESTAMPTZ
  - Previous migration `004_fix_admin_timezone.py` already fixed admins table
  - Resolved PostgreSQL/asyncpg error in admin panel statistics: "can't subtract offset-naive and offset-aware datetimes"
  - Fixed admin panel crashing when querying user statistics with `WHERE users.created_at >= $1::TIMESTAMP WITHOUT TIME ZONE`
  - Added comprehensive unit tests for all models (15 tests total covering all 7 database tables)

### Changed
- **Legacy Documentation Cleanup** - Archived completed refactoring and summary documentation
  - Moved 13 legacy summary files to `docs/archive/`
  - Updated archive README with comprehensive categorization
  - Root directory now contains only active project documentation

### Fixed
- **Deployment Port Allocation Errors** - Fixed persistent port 8080 race condition
  - Enhanced cleanup procedure with 8 comprehensive steps
  - Added docker network pruning to force release of port bindings
  - Increased wait time from 15s to 25s for docker-proxy processes
  - Added explicit port killing logic using `ss` and `kill -9`
  - Implemented retry logic (3 attempts) for `docker compose up`
  - Fixed deployment failures in runs #13-17
  - Documented in `docs/archive/BUG_FIX_DEPLOYMENT_PORT_8080_RACE.md`
- **Documentation Accuracy** - Corrected test counts and coverage percentages
  - Updated test count from 162-254 (claimed) to 293 (actual)
  - Updated coverage from 76-82% (claimed) to 81% (actual)
  - Documented Epic C implementation (was marked as "planned")
- **Feature Documentation** - Added missing feature documentation
  - Epic C: Discovery & Matching system (fully implemented)
  - Cache layer (97% coverage, 11 tests)
  - Rate limiting and security features
- **Old Stack References** - Updated references from old deployment model
  - Fixed `dating-bot-1` container reference in `verify-idempotency.sh` to use current `telegram-bot` service

### Changed
- Updated `README.md` with Epic C features and correct test counts
- Updated `PROJECT_STATUS.md` with accurate implementation status
- Updated `DOCUMENTATION.md` with correct test statistics
- Updated `docs/TESTING.md` with complete test breakdown (17 test files)
- Updated `ISSUE_COMPLETION_SUMMARY.md` with accurate metrics
- **Codebase Cleanup** - Organized historical documentation
  - Created `docs/archive/` directory with README
  - Moved 16 completed summary and bug fix documents to archive

### Removed
- Removed deprecated `docker-compose.monitoring.yml` file (monitoring now fully integrated via profiles)
- Removed unused PostgreSQL service from CI workflow (no tests currently exist)
- **Cleaned up root directory** - Moved outdated documentation files:
  - All port conflict fix documentation (5432, 8080) → `docs/archive/`
  - All deployment fix summaries → `docs/archive/`
  - Feature completion summaries (Admin Panel, Integration, MiniApp, Monitoring) → `docs/archive/`

### Previous Changes
- Moved completed summary files to archive:
  - `BUGFIX_SUMMARY.md` → `docs/archive/`
  - `WEBAPP_REBUILD_SUMMARY.md` → `docs/archive/`
  - `docs/ONBOARDING_UPDATE.md` → `docs/archive/`
  - `docs/WEBAPP_UX_IMPROVEMENTS.md` → `docs/archive/`
- Updated documentation references to reflect current state
- Optimized CI/CD workflows for better efficiency

## [0.3.1] - 2024-12-21

### Changed
- Major documentation refactoring for better readability and structure
- Monitoring stack now integrated into main docker-compose.yml using profiles
- Deprecated docker-compose.monitoring.yml (removed in next version)

### Added
- New comprehensive documentation structure in `docs/` directory
  - GETTING_STARTED.md - step-by-step setup guide
  - ARCHITECTURE.md - detailed system architecture
  - DEPLOYMENT.md - complete deployment guide
  - TESTING.md - testing guide for developers
- ROADMAP.md - planned features and enhancements
- CONTRIBUTING.md - contribution guidelines
- CHANGELOG.md - project history tracking
- Archive folder for old documentation files

### Fixed
- Data persistence ensured through named Docker volumes
- Monitoring stack now starts automatically during CI/CD deployment

## [0.3.0] - 2024-12-20

### Added
- Enhanced matching algorithm with weighted scoring (interests 40%, location 30%, goals 20%, age 10%)
- Analytics system with engagement metrics
- User preferences and settings management
- Match history with detailed profiles
- Performance indexes for database queries
- Comprehensive test coverage (136+ tests)

### Changed
- Improved WebApp UI/UX
- Optimized database queries with indexes
- Enhanced security with rate limiting

## [0.2.0] - 2024-12-15

### Added
- User interactions tracking (likes/dislikes)
- Match creation system
- User settings and preferences
- In-memory profile caching
- Security features (rate limiting, input validation)

### Changed
- Database schema enhancements
- Improved error handling

## [0.1.0] - 2024-06-11

### Added
- Initial project setup
- Telegram bot with basic commands (/start, /cancel, /reset)
- WebApp for profile creation
- PostgreSQL database with profiles table
- Docker and Docker Compose configuration
- Traefik reverse proxy with HTTPS support
- CI/CD pipeline with GitHub Actions
- Basic documentation

### Technical Stack
- Python 3.11+ with aiogram 3.x
- PostgreSQL 15 with asyncpg
- Docker & Docker Compose
- Traefik for HTTPS
- GitHub Actions for CI/CD

---

## Version History Summary

| Version | Date | Key Features |
|---------|------|--------------|
| 0.1.0 | 2024-06-11 | Initial release with basic bot functionality |
| 0.2.0 | 2024-12-15 | Matching system and user interactions |
| 0.3.0 | 2024-12-20 | Enhanced algorithm, analytics, comprehensive tests |
| 0.3.1 | 2024-12-21 | Documentation refactoring, monitoring integration |
| Current | 2025-01 | Repository cleanup, CI/CD optimization |

---

## Upgrade Notes

### Upgrading to latest version

```bash
# Pull latest changes
git pull origin main

# Update environment file if needed
cp .env.example .env.new
# Merge any new variables into your .env

# Rebuild and restart with monitoring
docker compose --profile monitoring up -d --build

# Run database migrations (automatic if RUN_DB_MIGRATIONS=true)
docker compose exec bot alembic upgrade head
```

### Breaking Changes

None in recent versions. All changes are backward compatible.

---

## Migration Guide

### From docker-compose.monitoring.yml to profiles

**Old way** (deprecated and removed):
```bash
docker compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d
```

**New way** (use this):
```bash
docker compose --profile monitoring up -d
```

The monitoring stack is now fully integrated into the main docker-compose.yml file using profiles. The separate monitoring file has been removed.

---

## Future Releases

See [ROADMAP.md](ROADMAP.md) for planned features:
- ML-based recommendations
- In-app chat
- Video calls
- Profile verification
- Premium subscriptions
- Native mobile apps

---

[Unreleased]: https://github.com/erliona/dating/compare/v0.3.1...HEAD
[0.3.1]: https://github.com/erliona/dating/compare/v0.3.0...v0.3.1
[0.3.0]: https://github.com/erliona/dating/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/erliona/dating/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/erliona/dating/releases/tag/v0.1.0
