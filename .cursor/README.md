# Cursor AI Rules Documentation

## Overview

This directory contains the unified rules and guidelines for the Cursor AI assistant working on the dating application project. All rules have been consolidated into a single, comprehensive file to eliminate contradictions and duplications.

## File Structure

- **`RULES.md`** - Main unified rules file containing all guidelines, standards, and best practices
- **`archive/`** - Contains archived rule files from the previous multi-file structure

## Rule Categories

The unified rules cover:

1. **Critical Workflows** - Code synchronization, Git workflow
2. **Project Identity & Stack** - Technology stack and architecture
3. **Naming Conventions & Standards** - Migrations, routes, services, networks, environment variables
4. **Coding Standards** - Python style, async patterns, type hints, database patterns
5. **Architecture & Boundaries** - Microservices separation, service communication
6. **Security & Configuration** - Secrets management, JWT authentication
7. **Docker & Infrastructure** - Container management, networking, Traefik routing
8. **Database & Migrations** - Alembic best practices, migration naming
9. **Testing & Quality** - pytest patterns, coverage requirements
10. **Deployment & Operations** - Deployment checklist, health checks, monitoring
11. **Troubleshooting & Diagnostics** - Systematic diagnostic approach, common problems
12. **Observability** - Logging standards, metrics patterns, tracing
13. **Example Patterns** - Code skeletons and templates

## Key Standards

### Migration Naming
- Use full filename as revision ID: `"007_create_chat_tables"`
- Never use short IDs like `"007"`
- Always update `down_revision` to full filename of previous migration

### API Route Naming
- Pattern: `/api/v1/<resource>/<action>`
- Public routes: No JWT required (e.g., `/admin/auth/login`)
- Protected routes: JWT required via sub-applications

### Docker Service Naming
- Services: Use kebab-case (e.g., `api-gateway`, `admin-service`)
- Networks: `default`, `monitoring`
- Never use IP addresses in configurations

### Environment Variables
- Format: `SCREAMING_SNAKE_CASE`
- Must be in `.env`, never hardcoded
- Document in `.env.example`
- No duplicates

## Usage

The Cursor AI assistant should follow these rules when:
- Writing or modifying code
- Creating new features
- Debugging issues
- Deploying changes
- Troubleshooting problems

## Migration from Old Structure

The previous multi-file structure has been consolidated into a single `RULES.md` file. Old rule files are preserved in the `archive/` directory for reference.

## Updates

When updating rules:
1. Modify `RULES.md` directly
2. Test changes in development
3. Commit and sync across Local → GitHub → Server
4. Update this README if structure changes

## Contact

For questions about these rules or suggestions for improvements, refer to the project documentation or create an issue in the repository.