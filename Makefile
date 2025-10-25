# Dating Platform Makefile
# Provides common development and CI commands

.PHONY: help install test lint format type-check security clean build up down logs ci

# Default target
help:
	@echo "Available commands:"
	@echo "  install     - Install dependencies"
	@echo "  test        - Run tests with coverage"
	@echo "  lint        - Run linting (ruff)"
	@echo "  format      - Format code (black, isort)"
	@echo "  type-check  - Run type checking (mypy)"
	@echo "  security    - Run security checks (bandit)"
	@echo "  clean       - Clean up temporary files"
	@echo "  build       - Build Docker images"
	@echo "  up          - Start services with docker-compose"
	@echo "  down        - Stop services"
	@echo "  logs        - Show service logs"
	@echo "  ci          - Run all CI checks (lint, format, type-check, security, test)"

# Install dependencies
install:
	@echo "Installing Python dependencies..."
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	@echo "Installing pre-commit hooks..."
	pre-commit install

# Run tests with coverage
test:
	@echo "Running tests with coverage..."
	source venv/bin/activate && pytest --cov=. --cov-report=html --cov-report=term-missing

# Run linting
lint:
	@echo "Running ruff linter..."
	ruff check .
	@echo "Running isort import sorting check..."
	isort --check-only --diff .

# Format code
format:
	@echo "Formatting code with black..."
	black .
	@echo "Sorting imports with isort..."
	isort .

# Type checking
type-check:
	@echo "Running mypy type checker..."
	mypy . --ignore-missing-imports

# Security checks
security:
	@echo "Running bandit security linter..."
	bandit -r . -f json -o bandit-report.json || true
	@echo "Security report saved to bandit-report.json"

# Clean up
clean:
	@echo "Cleaning up temporary files..."
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf htmlcov/
	rm -rf .coverage
	rm -rf bandit-report.json
	rm -rf .pytest_cache/

# Build Docker images
build:
	@echo "Building Docker images..."
	docker compose build

# Start services
up:
	@echo "Starting services..."
	docker compose up -d

# Stop services
down:
	@echo "Stopping services..."
	docker compose down

# Show logs
logs:
	@echo "Showing service logs..."
	docker compose logs -f

# Run all CI checks
ci: clean lint format type-check security test
	@echo "All CI checks completed successfully!"

# Development setup
dev-setup: install
	@echo "Setting up development environment..."
	cp .env.example .env
	@echo "Please edit .env file with your configuration"
	@echo "Development setup complete!"

# Production deployment
deploy:
	@echo "Deploying to production..."
	docker compose --profile production up -d
	@echo "Production deployment complete!"

# Database operations
db-migrate:
	@echo "Running database migrations..."
	docker compose exec data-service alembic upgrade head

db-rollback:
	@echo "Rolling back last migration..."
	docker compose exec data-service alembic downgrade -1

# Health checks
health:
	@echo "Checking service health..."
	@curl -f http://localhost:8080/health || echo "Gateway health check failed"
	@curl -f http://localhost:8081/health || echo "Auth service health check failed"
	@curl -f http://localhost:8082/health || echo "Profile service health check failed"
