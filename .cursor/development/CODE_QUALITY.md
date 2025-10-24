# Code Quality Standards & Enforcement

## Overview

This document defines the code quality standards, automated enforcement tools, and development workflows for maintaining consistent, high-quality code across the dating application project.

## Quality Tools Stack

### Core Tools

| Tool | Purpose | Configuration | Enforcement |
|------|---------|---------------|-------------|
| **Black** | Code formatting | `pyproject.toml` | Pre-commit + CI |
| **Ruff** | Fast linting | `pyproject.toml` | Pre-commit + CI |
| **MyPy** | Type checking | `pyproject.toml` | Pre-commit + CI |
| **isort** | Import sorting | `pyproject.toml` | Pre-commit + CI |
| **Bandit** | Security scanning | `pyproject.toml` | Pre-commit + CI |
| **yamllint** | YAML validation | `.yamllint` | Pre-commit + CI |
| **Commitizen** | Conventional commits | `pyproject.toml` | Pre-commit |

## Setup Instructions

### 1. Install Development Environment

```bash
# Run the setup script
./scripts/setup-code-quality.sh

# Or manually install
pip install -r requirements-dev.txt
pre-commit install
pre-commit install --hook-type commit-msg
```

### 2. Verify Installation

```bash
# Check all tools are working
make check

# Run specific checks
make format  # Format code
make lint    # Run linting
make test    # Run tests
```

## Code Formatting Standards

### Black Configuration

```toml
[tool.black]
line-length = 88
target-version = ['py311']
include = '\.pyi?$'
```

**Rules:**
- Line length: 88 characters
- Target Python 3.11+
- Exclude migrations and test fixtures
- Auto-format on commit

### Import Organization (isort)

```toml
[tool.isort]
profile = "black"
line_length = 88
multi_line_output = 3
include_trailing_comma = true
```

**Import order:**
1. Standard library imports
2. Third-party imports
3. Local application imports

## Linting Standards

### Ruff Configuration

```toml
[tool.ruff]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "B",   # flake8-bugbear
    "C4",  # flake8-comprehensions
    "UP",  # pyupgrade
    "SIM", # flake8-simplify
    "Q",   # flake8-quotes
    "RUF", # ruff-specific rules
]
```

**Key rules:**
- No unused imports or variables
- Consistent quote usage
- Simplified comprehensions
- Modern Python syntax
- Security best practices

## Type Checking Standards

### MyPy Configuration

```toml
[tool.mypy]
python_version = "3.11"
warn_return_any = true
disallow_untyped_defs = true
disallow_incomplete_defs = true
check_untyped_defs = true
```

**Strict mode for core services:**
- `core/` - Core utilities
- `services/` - Microservices
- `gateway/` - API Gateway

**Type annotations required:**
- All function parameters
- All return values
- Class attributes
- Module-level variables

## Security Standards

### Bandit Security Scanning

```toml
[tool.bandit]
exclude_dirs = ["tests", "migrations", "venv", "env"]
skips = ["B101", "B601"]
```

**Security checks:**
- SQL injection vulnerabilities
- Hardcoded passwords
- Insecure random number generation
- Shell injection risks
- Cryptographic issues

## Commit Standards

### Conventional Commits

**Format:** `type(scope): description`

**Types:**
- `feat` - New features
- `fix` - Bug fixes
- `docs` - Documentation
- `style` - Code formatting
- `refactor` - Code refactoring
- `perf` - Performance improvements
- `test` - Tests
- `build` - Build system
- `ci` - CI/CD
- `chore` - Maintenance

**Scopes:**
- `bot` - Telegram bot
- `core` - Core utilities
- `gateway` - API Gateway
- `auth` - Authentication
- `profile` - Profile service
- `discovery` - Discovery service
- `media` - Media service
- `chat` - Chat service
- `admin` - Admin service
- `webapp` - Frontend
- `monitoring` - Observability
- `database` - Database
- `docker` - Docker
- `security` - Security
- `config` - Configuration

**Examples:**
```bash
feat(auth): add JWT token refresh endpoint
fix(bot): resolve telegram webhook timeout issue
docs(api): update authentication documentation
style(core): format code with black
refactor(gateway): simplify routing logic
perf(database): optimize user query performance
test(auth): add unit tests for JWT validation
build(docker): update base image to python 3.11
ci(github): add static code analysis job
chore(deps): update aiohttp to latest version
security(jwt): implement key rotation policy
```

## Pre-commit Hooks

### Automatic Enforcement

Pre-commit hooks run automatically on:
- `git commit` - All staged files
- `git push` - All committed files
- Manual execution: `pre-commit run --all-files`

### Hook Configuration

```yaml
repos:
  - repo: https://github.com/psf/black
    hooks:
      - id: black
        args: [--line-length=88, --target-version=py311]
  
  - repo: https://github.com/astral-sh/ruff-pre-commit
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]
      - id: ruff-format
  
  - repo: https://github.com/pre-commit/mirrors-mypy
    hooks:
      - id: mypy
        args: [--strict]
        files: ^(core/|services/|gateway/).*\.py$
```

## CI/CD Integration

### GitHub Actions Workflow

```yaml
static-checks:
  name: Static Code Analysis
  runs-on: ubuntu-latest
  steps:
    - name: Run Black (code formatting)
      run: black --check --diff .
    
    - name: Run Ruff (linting)
      run: ruff check .
    
    - name: Run MyPy (type checking)
      run: mypy core/ services/ gateway/ bot/
    
    - name: Run Bandit (security)
      run: bandit -r . -f json -o bandit-report.json
```

**Enforcement:**
- All checks must pass for PR approval
- Security reports uploaded as artifacts
- Coverage threshold: 80% minimum

## Development Workflow

### Daily Development

```bash
# 1. Make changes to code
vim src/main.py

# 2. Stage changes
git add src/main.py

# 3. Commit (hooks run automatically)
git commit -m "feat(auth): add JWT validation"

# 4. Push (additional checks)
git push origin feature-branch
```

### Manual Quality Checks

```bash
# Format code
make format

# Run linting
make lint

# Run all checks
make check

# Run tests
make test

# Security scan
make security
```

### Git Aliases

```bash
# Format staged files
git format

# Lint staged files
git lint

# Run all checks
git check

# Make conventional commit
git commit
```

## VS Code Integration

### Settings

```json
{
    "python.formatting.provider": "black",
    "python.linting.ruffEnabled": true,
    "python.linting.mypyEnabled": true,
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    }
}
```

### Extensions

- **Python** - Python language support
- **Ruff** - Fast Python linter
- **Black Formatter** - Code formatting
- **MyPy Type Checker** - Type checking
- **YAML** - YAML language support

## Troubleshooting

### Common Issues

**1. Pre-commit hooks failing:**
```bash
# Update hooks
pre-commit autoupdate

# Run on all files
pre-commit run --all-files
```

**2. MyPy type errors:**
```bash
# Check specific file
mypy src/main.py

# Ignore missing imports
mypy --ignore-missing-imports src/main.py
```

**3. Ruff linting errors:**
```bash
# Auto-fix issues
ruff check --fix .

# Check specific file
ruff check src/main.py
```

**4. Black formatting conflicts:**
```bash
# Format specific file
black src/main.py

# Check formatting
black --check --diff .
```

### Bypassing Hooks (Emergency Only)

```bash
# Skip pre-commit hooks (NOT RECOMMENDED)
git commit --no-verify -m "emergency: fix critical bug"

# Skip specific hook
SKIP=ruff git commit -m "fix: resolve issue"
```

## Quality Metrics

### Coverage Requirements

- **Minimum coverage**: 80%
- **Critical paths**: 95% (auth, payments, data)
- **New code**: 90% minimum

### Performance Targets

- **Test execution**: < 5 minutes
- **Linting**: < 30 seconds
- **Type checking**: < 2 minutes
- **Formatting**: < 10 seconds

### Security Standards

- **Bandit score**: 0 high/critical issues
- **Dependency vulnerabilities**: 0 known CVEs
- **Secret scanning**: 0 exposed secrets

## Best Practices

### Code Organization

1. **Imports**: Use isort for consistent ordering
2. **Formatting**: Let Black handle all formatting
3. **Types**: Add type hints for all public APIs
4. **Documentation**: Use docstrings for all functions
5. **Testing**: Write tests for all new features

### Git Workflow

1. **Branch naming**: `feature/description`, `fix/description`
2. **Commit messages**: Use conventional commits
3. **PR description**: Include testing notes and breaking changes
4. **Review process**: All PRs require approval
5. **Merge strategy**: Squash and merge for clean history

### Continuous Improvement

1. **Regular updates**: Update tools monthly
2. **Rule refinement**: Adjust rules based on team feedback
3. **Performance monitoring**: Track CI execution times
4. **Coverage tracking**: Monitor coverage trends
5. **Security scanning**: Regular dependency audits
