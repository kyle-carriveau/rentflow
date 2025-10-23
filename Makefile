# RentFlow Development Makefile
# Simplifies common development tasks across all environments
#
# Quick Start:
#   make dev-up          # Start local development environment
#   make dev-logs        # View logs
#   make dev-migrate     # Run database migrations
#   make dev-test        # Run tests
#
# Usage: make [target]

.PHONY: help
.DEFAULT_GOAL := help

# Colors for output
BLUE := \033[0;34m
GREEN := \033[0;32m
YELLOW := \033[1;33m
NC := \033[0m

##@ General

help: ## Display this help message
	@echo ""
	@echo "$(BLUE)RentFlow Development Commands$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf ""} /^[a-zA-Z_-]+:.*?##/ { printf "  $(GREEN)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(YELLOW)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)
	@echo ""

##@ Local Development Environment

dev-up: ## Start local development environment
	@echo "$(BLUE)Starting local development environment...$(NC)"
	docker compose -f docker-compose.local.yml up -d
	@echo "$(GREEN)✓ Local environment started$(NC)"
	@echo "Access at: http://localhost:5000"

dev-down: ## Stop local development environment
	@echo "$(BLUE)Stopping local development environment...$(NC)"
	docker compose -f docker-compose.local.yml down
	@echo "$(GREEN)✓ Local environment stopped$(NC)"

dev-restart: ## Restart local development environment
	@echo "$(BLUE)Restarting local development environment...$(NC)"
	docker compose -f docker-compose.local.yml restart
	@echo "$(GREEN)✓ Local environment restarted$(NC)"

dev-build: ## Rebuild local development containers
	@echo "$(BLUE)Rebuilding local development containers...$(NC)"
	docker compose -f docker-compose.local.yml build --no-cache
	@echo "$(GREEN)✓ Containers rebuilt$(NC)"

dev-rebuild: dev-down dev-build dev-up ## Full rebuild and restart

dev-ps: ## Show running local containers
	@docker compose -f docker-compose.local.yml ps

dev-logs: ## View local development logs (all services)
	@docker compose -f docker-compose.local.yml logs -f

dev-logs-web: ## View web application logs only
	@docker compose -f docker-compose.local.yml logs -f web

dev-logs-db: ## View database logs only
	@docker compose -f docker-compose.local.yml logs -f db

dev-logs-redis: ## View Redis logs only
	@docker compose -f docker-compose.local.yml logs -f redis

##@ Local Development - Shell Access

dev-shell: ## Access web application shell
	@docker compose -f docker-compose.local.yml exec web /bin/bash

dev-shell-db: ## Access database shell (psql)
	@docker compose -f docker-compose.local.yml exec db psql -U rentflow_dev -d rentflow_dev

dev-shell-redis: ## Access Redis CLI
	@docker compose -f docker-compose.local.yml exec redis redis-cli

dev-python: ## Access Python shell with Flask context
	@docker compose -f docker-compose.local.yml exec web python3 -c "from website import create_app, db; app = create_app('development'); app.app_context().push(); print('Flask app loaded. Use db, models, etc.')"

##@ Local Development - Database

dev-migrate: ## Run database migrations
	@echo "$(BLUE)Running database migrations...$(NC)"
	@docker compose -f docker-compose.local.yml exec web flask db upgrade
	@echo "$(GREEN)✓ Migrations complete$(NC)"

dev-migrate-create: ## Create a new migration (use: make dev-migrate-create MSG="description")
	@if [ -z "$(MSG)" ]; then \
		echo "$(YELLOW)Usage: make dev-migrate-create MSG=\"your migration description\"$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Creating new migration: $(MSG)$(NC)"
	@docker compose -f docker-compose.local.yml exec web flask db migrate -m "$(MSG)"
	@echo "$(GREEN)✓ Migration created$(NC)"

dev-db-backup: ## Backup local database
	@echo "$(BLUE)Backing up local database...$(NC)"
	@./scripts/db-backup.sh local
	@echo "$(GREEN)✓ Backup complete$(NC)"

dev-db-restore: ## Restore local database (use: make dev-db-restore FILE=path/to/backup.sql)
	@if [ -z "$(FILE)" ]; then \
		echo "$(YELLOW)Usage: make dev-db-restore FILE=path/to/backup.sql$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Restoring local database...$(NC)"
	@./scripts/db-restore.sh local $(FILE)
	@echo "$(GREEN)✓ Restore complete$(NC)"

dev-db-seed: ## Seed local database with test data (use: make dev-db-seed SIZE=small|medium|large)
	@SIZE=$${SIZE:-small}; \
	echo "$(BLUE)Seeding local database ($$SIZE dataset)...$(NC)"; \
	./scripts/db-seed.sh local $$SIZE
	@echo "$(GREEN)✓ Database seeded$(NC)"

dev-db-reset: ## Reset local database (drop all data and recreate)
	@echo "$(YELLOW)⚠ WARNING: This will delete ALL local data!$(NC)"
	@read -p "Type 'yes' to continue: " confirm; \
	if [ "$$confirm" != "yes" ]; then \
		echo "Aborted."; \
		exit 1; \
	fi
	@echo "$(BLUE)Resetting local database...$(NC)"
	@docker compose -f docker-compose.local.yml exec db psql -U rentflow_dev -d postgres -c "DROP DATABASE IF EXISTS rentflow_dev;"
	@docker compose -f docker-compose.local.yml exec db psql -U rentflow_dev -d postgres -c "CREATE DATABASE rentflow_dev;"
	@echo "$(GREEN)✓ Database reset complete$(NC)"
	@echo "$(BLUE)Running migrations...$(NC)"
	@$(MAKE) dev-migrate
	@echo "$(GREEN)✓ Database ready$(NC)"

##@ Local Development - Testing

dev-test: ## Run all tests
	@echo "$(BLUE)Running tests...$(NC)"
	@docker compose -f docker-compose.local.yml exec web pytest

dev-test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	@docker compose -f docker-compose.local.yml exec web pytest -m unit

dev-test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(NC)"
	@docker compose -f docker-compose.local.yml exec web pytest -m integration

dev-test-coverage: ## Run tests with coverage report
	@echo "$(BLUE)Running tests with coverage...$(NC)"
	@docker compose -f docker-compose.local.yml exec web pytest --cov=website --cov-report=term-missing --cov-report=html

dev-test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode...$(NC)"
	@docker compose -f docker-compose.local.yml exec web pytest-watch

##@ Staging Environment

staging-up: ## Start staging environment
	@echo "$(BLUE)Starting staging environment...$(NC)"
	docker compose -f docker-compose.staging.yml up -d
	@echo "$(GREEN)✓ Staging environment started$(NC)"
	@echo "Access at: http://localhost:8080"

staging-down: ## Stop staging environment
	@echo "$(BLUE)Stopping staging environment...$(NC)"
	docker compose -f docker-compose.staging.yml down
	@echo "$(GREEN)✓ Staging environment stopped$(NC)"

staging-restart: ## Restart staging environment
	@echo "$(BLUE)Restarting staging environment...$(NC)"
	docker compose -f docker-compose.staging.yml restart
	@echo "$(GREEN)✓ Staging environment restarted$(NC)"

staging-build: ## Rebuild staging containers
	@echo "$(BLUE)Rebuilding staging containers...$(NC)"
	docker compose -f docker-compose.staging.yml build --no-cache
	@echo "$(GREEN)✓ Containers rebuilt$(NC)"

staging-logs: ## View staging logs
	@docker compose -f docker-compose.staging.yml logs -f

staging-ps: ## Show running staging containers
	@docker compose -f docker-compose.staging.yml ps

staging-shell: ## Access staging web application shell
	@docker compose -f docker-compose.staging.yml exec web /bin/bash

staging-db-backup: ## Backup staging database
	@echo "$(BLUE)Backing up staging database...$(NC)"
	@./scripts/db-backup.sh staging
	@echo "$(GREEN)✓ Backup complete$(NC)"

staging-sync: ## Sync production data to staging (with sanitization)
	@echo "$(BLUE)Syncing production to staging...$(NC)"
	@./scripts/db-sync-to-staging.sh
	@echo "$(GREEN)✓ Sync complete$(NC)"

##@ Production Environment (VPS)

prod-deploy: ## Deploy to production (requires VPS access)
	@echo "$(YELLOW)⚠ WARNING: This will deploy to PRODUCTION!$(NC)"
	@read -p "Type 'deploy' to continue: " confirm; \
	if [ "$$confirm" != "deploy" ]; then \
		echo "Aborted."; \
		exit 1; \
	fi
	@echo "$(BLUE)Deploying to production...$(NC)"
	@./deploy.sh
	@echo "$(GREEN)✓ Production deployment complete$(NC)"

prod-backup: ## Backup production database
	@echo "$(BLUE)Backing up production database...$(NC)"
	@./scripts/db-backup.sh production
	@echo "$(GREEN)✓ Backup complete$(NC)"

prod-logs: ## View production logs (requires SSH)
	@echo "$(BLUE)Connecting to production logs...$(NC)"
	@ssh -t ubuntu@$${VPS_HOST} "cd /var/www/rentflow && docker compose -f deployment/docker/docker-compose.yml logs -f"

prod-status: ## Check production status
	@echo "$(BLUE)Checking production status...$(NC)"
	@ssh ubuntu@$${VPS_HOST} "cd /var/www/rentflow && docker compose -f deployment/docker/docker-compose.yml ps"

##@ Code Quality

lint: ## Run code linting
	@echo "$(BLUE)Running linters...$(NC)"
	@docker compose -f docker-compose.local.yml exec web flake8 website/
	@echo "$(GREEN)✓ Linting complete$(NC)"

format: ## Format code with black
	@echo "$(BLUE)Formatting code...$(NC)"
	@docker compose -f docker-compose.local.yml exec web black website/
	@echo "$(GREEN)✓ Formatting complete$(NC)"

format-check: ## Check code formatting
	@echo "$(BLUE)Checking code formatting...$(NC)"
	@docker compose -f docker-compose.local.yml exec web black --check website/

type-check: ## Run type checking with mypy
	@echo "$(BLUE)Running type checks...$(NC)"
	@docker compose -f docker-compose.local.yml exec web mypy website/

##@ Cleanup

clean: ## Remove all containers, volumes, and images
	@echo "$(YELLOW)⚠ WARNING: This will remove ALL Docker resources!$(NC)"
	@read -p "Type 'clean' to continue: " confirm; \
	if [ "$$confirm" != "clean" ]; then \
		echo "Aborted."; \
		exit 1; \
	fi
	@echo "$(BLUE)Cleaning up Docker resources...$(NC)"
	@docker compose -f docker-compose.local.yml down -v --remove-orphans
	@docker compose -f docker-compose.staging.yml down -v --remove-orphans
	@echo "$(GREEN)✓ Cleanup complete$(NC)"

clean-logs: ## Remove all log files
	@echo "$(BLUE)Removing log files...$(NC)"
	@rm -f logs/*.log
	@echo "$(GREEN)✓ Logs removed$(NC)"

clean-cache: ## Remove Python cache files
	@echo "$(BLUE)Removing Python cache...$(NC)"
	@find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@find . -type f -name "*.pyc" -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Cache removed$(NC)"

clean-backups: ## Remove old backup files (keeps last 7 days)
	@echo "$(BLUE)Cleaning old backups...$(NC)"
	@find backups/ -name "*.sql" -type f -mtime +7 -delete 2>/dev/null || true
	@echo "$(GREEN)✓ Old backups removed$(NC)"

##@ Git Workflow

feature: ## Create new feature branch (use: make feature NAME=my-feature)
	@if [ -z "$(NAME)" ]; then \
		echo "$(YELLOW)Usage: make feature NAME=my-feature-name$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)Creating feature branch: feature/$(NAME)$(NC)"
	@git checkout develop
	@git pull origin develop
	@git checkout -b feature/$(NAME)
	@echo "$(GREEN)✓ Feature branch created: feature/$(NAME)$(NC)"

sync-develop: ## Sync current branch with develop
	@echo "$(BLUE)Syncing with develop...$(NC)"
	@git fetch origin
	@git merge origin/develop
	@echo "$(GREEN)✓ Synced with develop$(NC)"

##@ Documentation

docs-serve: ## Serve documentation locally
	@echo "$(BLUE)Serving documentation...$(NC)"
	@python3 -m http.server 8000 --directory .

##@ Utilities

validate: ## Validate environment configuration
	@echo "$(BLUE)Validating environment...$(NC)"
	@./deployment/scripts/validate.sh
	@echo "$(GREEN)✓ Validation complete$(NC)"

health-check: ## Run health checks on local environment
	@echo "$(BLUE)Running health checks...$(NC)"
	@curl -f http://localhost:5000/health || echo "$(YELLOW)⚠ Health check failed$(NC)"

install-hooks: ## Install git pre-commit hooks
	@echo "$(BLUE)Installing git hooks...$(NC)"
	@echo "#!/bin/sh\nmake lint format-check dev-test" > .git/hooks/pre-commit
	@chmod +x .git/hooks/pre-commit
	@echo "$(GREEN)✓ Git hooks installed$(NC)"

env-example: ## Generate .env.local from example
	@if [ -f .env.local ]; then \
		echo "$(YELLOW).env.local already exists. Remove it first or create manually.$(NC)"; \
		exit 1; \
	fi
	@cp .env.local.example .env.local
	@echo "$(GREEN)✓ .env.local created from example$(NC)"
	@echo "$(YELLOW)⚠ Remember to update with your actual values!$(NC)"
