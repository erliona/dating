# Engineering Rules TL;DR

## 🚫 Red Lines (Critical Prohibitions)

### NO DIRECT SERVER/CONTAINER EDITS
- NEVER edit files directly on server or in containers
- ONLY use Git workflow: branch → PR → review → merge
- ALL changes MUST go through GitHub: Local → GitHub → Server

### NO PUBLIC ROUTE CHANGES WITHOUT OPENAPI
- NEVER change public API routes without updating OpenAPI specs
- ALWAYS update OpenAPI documentation before route changes
- MUST run tests after OpenAPI updates

### NO ALEMBIC REVISION EDITS
- NEVER edit `revision` or `down_revision` in merged migrations
- ONLY create new migrations for schema changes
- Use `alembic merge` for conflicting migrations

### NO DEPENDENCIES WITHOUT JUSTIFICATION
- NEVER add dependencies without clear business justification
- MUST update `requirements.txt` or `requirements-dev.txt`
- Document WHY each dependency is needed

### NO UNRELATED FILE CHANGES
- NEVER touch unrelated files/services in same commit
- Keep changes focused on single feature/fix
- One commit = one logical change

### NO HARDCODED VALUES
- NEVER hardcode ports, URLs, or secrets
- ALWAYS use environment variables from `.env`/`.env.example`

### NO DOCKER SERVICE/NETWORK RENAMES
- NEVER change service names in docker-compose.yml
- NEVER change network names in docker-compose.yml
- Update dependent files: .env files, reverse proxies (e.g., Nginx), and monitoring configs

### NO SECRETS OR BINARIES IN GIT
- NEVER commit secrets (passwords, tokens, keys)
- NEVER commit binary files (images, executables, databases)

### NO LOG SCHEMA CHANGES WITHOUT COORDINATION
- NEVER change log schema/format (JSON fields, levels) without coordination
- Changes break alerts and dashboards - coordinate with observability team

---

## ✅ Golden Path

### Migrations
- Use `alembic revision -m "descriptive message"` (auto-generates hash)
- Migrations must be idempotent (safe to run multiple times)
- Migrations must be backward compatible until deployment is confirmed
- Test migrations on production-like dataset before deploying

### Config
- Maintain `.env.example` with all required variables documented
- Maintain `.env.schema` for validation (or use dotenv-linter)
- Ensure required variables are documented and checked in CI

---

## 🧪 Quality Gates

### Coverage Thresholds
- Absolute coverage must be ≥ 85%
- CI fails on relative drop > 2% vs main branch
- Use `pytest-cov` with `--cov-fail-under=85`

### Required Gates
- OpenAPI validation against schemas
- Migration chain integrity checks
- Single migrator service (RUN_DB_MIGRATIONS=true once)
- Docker build + Trivy security scanning
- SBOM generation
- Immutable container image tags

---

## 🛠 Local Dev

### Quick Commands
```bash
# Run tests inside Docker
docker compose exec api pytest -q --maxfail=1

# Start development
docker compose up -d
```

### Prerequisites
- Requires GNU Make on system
- macOS users: ensure `make` is available or install via `brew install make`

---

## 🔁 PR Checklist

- [ ] Migration file has descriptive name
- [ ] Revision ID is auto-generated hash (not manually edited)
- [ ] Test migration locally: `alembic upgrade head`
- [ ] Test rollback: `alembic downgrade -1` then `alembic upgrade head`
- [ ] README/docs updated if setup or commands changed
- [ ] Verified backward compatibility for existing clients (API/SDK/CLI)
- [ ] Documented breaking changes + migration path (if any)

---

## 🚢 Deployment

### Deployment Order (Blue/Green or Rolling)
- Run DB migrations (exactly once) BEFORE scaling up new app version
- Prevents schema mismatch between old and new application versions
- Use migration service or init container, not application startup
- Verify migration completion before proceeding with deployment

---

## 🧯 Incident Response

### Incident Management
- Create timestamped incident doc in `incident/` directory
- Assign an incident owner/commander
- Capture logs, metrics, and impact assessment
- Follow the communications tree for stakeholder updates
- Conduct post-incident review within 48 hours

### Incident Doc Template
```markdown
# Incident: [Brief Description]
- Date/Time: YYYY-MM-DD HH:MM UTC
- Owner: [Name]
- Severity: [P0/P1/P2/P3]
- Status: [Investigating/Mitigating/Resolved]

## Impact
- Affected services:
- User impact:
- Data impact:

## Timeline
- HH:MM - Incident detected
- HH:MM - Owner assigned
- HH:MM - Root cause identified
- HH:MM - Mitigation applied
- HH:MM - Incident resolved

## Root Cause
[Analysis]

## Action Items
- [ ] Task 1
- [ ] Task 2
```

---

## 📋 Output Style (What Cursor Must Return)

1) **Plan (5–10 bullets) + list of files** to change (before coding)
2) **Minimal diffs** only for the promised files (don't refactor unrelated code)
3) **Tests** (pytest) + how to run them locally
4) **OpenAPI/docs** updates for any public API change
5) **Commands** for build/test/deploy + **post-deploy checks**

> If more than **5 files** are needed, stop and propose splitting into multiple PRs.

---

*Last Updated: 2025-01-26*
*Version: 3.0*
*Status: Active*
