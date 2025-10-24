#!/bin/bash
# Setup Code Quality Tools Script
# Installs and configures pre-commit hooks, linting, and formatting tools

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

# Error handling
error_exit() {
    log "${RED}ERROR: $1${NC}"
    exit 1
}

# Success message
success() {
    log "${GREEN}✅ $1${NC}"
}

# Warning message
warning() {
    log "${YELLOW}⚠️  $1${NC}"
}

# Check if running in correct directory
check_directory() {
    if [ ! -f "pyproject.toml" ] || [ ! -f ".pre-commit-config.yaml" ]; then
        error_exit "Please run this script from the project root directory"
    fi
    success "Running in correct directory"
}

# Check Python version
check_python() {
    local python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
    local required_version="3.11"
    
    if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
        error_exit "Python 3.11+ required, found $python_version"
    fi
    success "Python version check passed ($python_version)"
}

# Install development dependencies
install_dependencies() {
    log "📦 Installing development dependencies..."
    
    # Install pre-commit
    pip install pre-commit
    
    # Install other dev tools
    pip install black isort ruff mypy bandit yamllint commitizen
    
    success "Development dependencies installed"
}

# Install pre-commit hooks
install_pre_commit() {
    log "🔧 Installing pre-commit hooks..."
    
    # Install the git hook scripts
    pre-commit install
    
    # Install commit-msg hook for commitlint
    pre-commit install --hook-type commit-msg
    
    success "Pre-commit hooks installed"
}

# Run initial checks
run_initial_checks() {
    log "🔍 Running initial code quality checks..."
    
    # Check if there are any issues
    if pre-commit run --all-files; then
        success "All code quality checks passed"
    else
        warning "Some code quality issues found - they will be fixed automatically on next commit"
    fi
}

# Setup commitizen
setup_commitizen() {
    log "📝 Setting up commitizen for conventional commits..."
    
    # Initialize commitizen if not already done
    if [ ! -f ".cz.yaml" ]; then
        cz init --name "cz_conventional_commits" --tag-format "v$version" --version-scheme "pep440"
    fi
    
    success "Commitizen configured"
}

# Create git aliases for common tasks
setup_git_aliases() {
    log "🔗 Setting up git aliases for code quality..."
    
    # Add useful git aliases
    git config alias.format "!pre-commit run black isort --all-files"
    git config alias.lint "!pre-commit run ruff mypy --all-files"
    git config alias.check "!pre-commit run --all-files"
    git config alias.commit "!cz commit"
    
    success "Git aliases configured"
}

# Create VS Code settings for consistent formatting
setup_vscode() {
    log "⚙️  Setting up VS Code settings..."
    
    mkdir -p .vscode
    
    cat > .vscode/settings.json << 'EOF'
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.formatting.provider": "black",
    "python.formatting.blackArgs": ["--line-length=88"],
    "python.linting.enabled": true,
    "python.linting.ruffEnabled": true,
    "python.linting.mypyEnabled": true,
    "python.linting.banditEnabled": true,
    "python.linting.lintOnSave": true,
    "python.sortImports.args": ["--profile", "black"],
    "editor.formatOnSave": true,
    "editor.codeActionsOnSave": {
        "source.organizeImports": true
    },
    "files.trimTrailingWhitespace": true,
    "files.insertFinalNewline": true,
    "files.trimFinalNewlines": true,
    "[yaml]": {
        "editor.formatOnSave": true,
        "editor.defaultFormatter": "redhat.vscode-yaml"
    },
    "[json]": {
        "editor.formatOnSave": true
    },
    "[markdown]": {
        "editor.formatOnSave": true
    }
}
EOF

    success "VS Code settings configured"
}

# Create Makefile for common tasks
create_makefile() {
    log "📋 Creating Makefile for common tasks..."
    
    cat > Makefile << 'EOF'
# Makefile for code quality tasks

.PHONY: help install format lint check test clean

help: ## Show this help message
	@echo "Available commands:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'

install: ## Install development dependencies and pre-commit hooks
	pip install -r requirements-dev.txt
	pre-commit install
	pre-commit install --hook-type commit-msg

format: ## Format code with black and isort
	black .
	isort .

lint: ## Run linting with ruff and mypy
	ruff check .
	ruff format --check .
	mypy core/ services/ gateway/ bot/

check: ## Run all code quality checks
	pre-commit run --all-files

test: ## Run tests
	pytest

test-unit: ## Run unit tests
	pytest tests/unit/ -v

test-integration: ## Run integration tests
	pytest tests/integration/ -v

test-e2e: ## Run end-to-end tests
	pytest tests/e2e/ -v

clean: ## Clean up temporary files
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -delete
	rm -rf .pytest_cache
	rm -rf .coverage
	rm -rf htmlcov
	rm -rf dist
	rm -rf build

security: ## Run security checks
	bandit -r . -f json -o bandit-report.json
	yamllint .github/ docker-compose.yml

commit: ## Make a conventional commit
	cz commit

update: ## Update dependencies
	pip install --upgrade pip
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pre-commit autoupdate
EOF

    success "Makefile created"
}

# Main setup function
main() {
    log "🚀 Setting up code quality tools..."
    
    check_directory
    check_python
    install_dependencies
    install_pre_commit
    setup_commitizen
    setup_git_aliases
    setup_vscode
    create_makefile
    run_initial_checks
    
    success "Code quality setup completed!"
    
    echo ""
    log "📚 Available commands:"
    echo "  make help          - Show all available commands"
    echo "  make format        - Format code with black and isort"
    echo "  make lint          - Run linting with ruff and mypy"
    echo "  make check         - Run all code quality checks"
    echo "  make commit        - Make a conventional commit"
    echo "  git format         - Format staged files"
    echo "  git lint           - Lint staged files"
    echo "  git check          - Run all checks on staged files"
    echo ""
    log "🔧 Pre-commit hooks are now active!"
    log "All commits will be automatically checked for code quality."
}

# Run main function
main "$@"
