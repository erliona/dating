# Cursor AI Rules Structure

This directory contains the Cursor AI rules organized for maximum effectiveness in development, production deployment, and troubleshooting.

## File Structure

### Core Rules
- **`rules`** - Main development rules (coding style, architecture, testing, etc.)
- **`production.rules`** - Production deployment, configuration, and post-deploy validation
- **`troubleshooting.rules`** - Systematic debugging approach and diagnostic commands

### Specialized Rules (MDC)
- **`rules-mdc/deployment-and-monitoring.mdc`** - Integration-specific monitoring and deployment patterns
- **`rules-mdc/git-flow-and-docker.mdc`** - Git workflow and Docker container management
- **`rules-mdc/readonly-state.mdc`** - Rules for read-only operations
- **`rules-mdc/rebuilt.mdc`** - Rules for rebuild operations

## Usage Guidelines

### For Development
- Start with `rules` for coding standards and architecture
- Reference `production.rules` when making deployment-related changes
- Use `troubleshooting.rules` when debugging issues

### For Production Issues
1. Check `troubleshooting.rules` for systematic diagnostic approach
2. Follow patterns in "Common Problem Patterns" section
3. Use diagnostic commands library for quick checks
4. Apply fixes from `production.rules` best practices

### For New Team Members
1. Read `rules` for project understanding
2. Study `production.rules` for deployment procedures
3. Bookmark `troubleshooting.rules` for emergency situations

## Key Improvements

- **Structured Approach**: Clear separation between development, production, and troubleshooting
- **Pattern Recognition**: Common problems with proven solutions
- **Command Library**: Ready-to-use diagnostic commands
- **Prevention Focus**: Rules to avoid problems before they occur
- **Quick Recovery**: Fast path from symptoms to solutions

## Metrics

- **MTTR (Mean Time To Recovery)**: Target < 30 minutes
- **Prevention Rate**: 80% of issues should be prevented by following rules
- **Onboarding Time**: New developers productive within 1 day
- **Consistency**: All deployments follow same checklist
