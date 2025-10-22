# RentFlow Development Guide

Complete guide for local development, testing, and contributing to RentFlow.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Prerequisites](#prerequisites)
3. [Initial Setup](#initial-setup)
4. [Development Workflow](#development-workflow)
5. [Common Tasks](#common-tasks)
6. [Database Management](#database-management)
7. [Testing](#testing)
8. [Debugging](#debugging)
9. [IDE Setup](#ide-setup)
10. [Troubleshooting](#troubleshooting)
11. [Best Practices](#best-practices)

---

## Quick Start

**For new developers - one command setup:**

```bash
./scripts/local-dev-setup.sh --seed-data
```

This script will:
- ✅ Check prerequisites
- ✅ Create configuration files
- ✅ Build Docker containers
- ✅ Start development environment
- ✅ Run database migrations
- ✅ Seed test data

**Access your local environment:**
- Web Application: http://localhost:5000
- PostgreSQL: localhost:5432
- Redis: localhost:6379

**Test credentials** (if seeded):
- Email: `user1@test.example.com`
- Password: `TestPassword123!`

---

## Prerequisites

### Required Software

| Software | Version | Purpose | Download |
|----------|---------|---------|----------|
| **Docker Desktop** | 20.10+ | Container runtime | [Download](https://www.docker.com/products/docker-desktop) |
| **Python** | 3.12+ | Backend runtime | [Download](https://www.python.org/downloads/) |
| **Git** | 2.0+ | Version control | [Download](https://git-scm.com/) |

### Optional but Recommended

| Software | Purpose | Download |
|----------|---------|----------|
| **Make** | Command shortcuts | Pre-installed on macOS/Linux, [Windows](http://gnuwin32.sourceforge.net/packages/make.htm) |
| **VS Code** | IDE with Python support | [Download](https://code.visualstudio.com/) |
| **Postman** | API testing | [Download](https://www.postman.com/) |
| **pgAdmin** | PostgreSQL GUI | [Download](https://www.pgadmin.org/) |

### System Requirements

- **RAM**: 4GB minimum (8GB recommended)
- **Disk Space**: 5GB free space
- **OS**: macOS, Linux, or Windows 10/11 with WSL2

---

## Initial Setup

### Option 1: Automated Setup (Recommended)

Run the automated setup script:

```bash
# Clone repository (if not already done)
git checkout develop
git pull origin develop

# Run automated setup
./scripts/local-dev-setup.sh --seed-data
```

The script will guide you through the complete setup process.

### Option 2: Manual Setup

#### Step 1: Clone and Configure

```bash
# Checkout develop branch
git checkout develop
git pull origin develop

# Create environment configuration
cp .env.local.example .env.local

# Edit .env.local with your preferences (optional)
nano .env.local
```

#### Step 2: Build and Start

```bash
# Using Make (recommended)
make dev-up

# Or using Docker Compose directly
docker compose -f docker-compose.local.yml up -d
```

#### Step 3: Initialize Database

```bash
# Run migrations
make dev-migrate

# Or
docker compose -f docker-compose.local.yml exec web flask db upgrade
```

#### Step 4: Seed Test Data (Optional)

```bash
# Seed small dataset
make dev-db-seed SIZE=small

# Or medium/large dataset
make dev-db-seed SIZE=medium
```

---

## Development Workflow

### Daily Development Cycle

```bash
# 1. Start your day - pull latest changes
git checkout develop
git pull origin develop

# 2. Start development environment
make dev-up

# 3. Create feature branch
make feature NAME=my-new-feature
# This creates: feature/my-new-feature

# 4. Make your changes
# ... code code code ...

# 5. Run tests
make dev-test

# 6. View logs if needed
make dev-logs

# 7. Commit and push
git add .
git commit -m "feat(module): description of changes"
git push origin feature/my-new-feature

# 8. Stop environment when done
make dev-down
```

### Git Workflow

See [BRANCHING.md](BRANCHING.md) for detailed Git workflow, but here's the summary:

```
feature/* → develop → main
  (dev)      (staging) (production)
```

**Creating a Feature:**
```bash
# Start from develop
git checkout develop
git pull origin develop

# Create feature branch
git checkout -b feature/add-reporting

# Work on feature
# ... make changes ...

# Push and create PR to develop
git push origin feature/add-reporting
```

**Syncing with Develop:**
```bash
# While on your feature branch
make sync-develop

# Or manually
git fetch origin
git merge origin/develop
```

---

## Common Tasks

### Starting and Stopping

```bash
# Start local environment
make dev-up

# Stop local environment
make dev-down

# Restart (without rebuilding)
make dev-restart

# Full rebuild and restart
make dev-rebuild
```

### Viewing Logs

```bash
# All services
make dev-logs

# Web application only
make dev-logs-web

# Database only
make dev-logs-db

# Redis only
make dev-logs-redis
```

### Accessing Containers

```bash
# Web application shell
make dev-shell

# Python shell with Flask context
make dev-python

# Database shell (psql)
make dev-shell-db

# Redis CLI
make dev-shell-redis
```

### Running Commands in Containers

```bash
# Run any Flask command
docker compose -f docker-compose.local.yml exec web flask <command>

# Run Python script
docker compose -f docker-compose.local.yml exec web python script.py

# Install Python package
docker compose -f docker-compose.local.yml exec web pip install <package>
```

---

## Database Management

### Migrations

#### Create New Migration

```bash
# After modifying models.py
make dev-migrate-create MSG="add user profile fields"

# Or directly
docker compose -f docker-compose.local.yml exec web flask db migrate -m "description"
```

#### Apply Migrations

```bash
make dev-migrate

# Or
docker compose -f docker-compose.local.yml exec web flask db upgrade
```

#### Rollback Migration

```bash
# Rollback one migration
docker compose -f docker-compose.local.yml exec web flask db downgrade

# Rollback to specific revision
docker compose -f docker-compose.local.yml exec web flask db downgrade <revision>
```

### Backup and Restore

#### Backup Database

```bash
# Backup local database
make dev-db-backup

# Manual backup with custom path
./scripts/db-backup.sh local /path/to/backup.sql
```

#### Restore Database

```bash
# Restore from backup
make dev-db-restore FILE=backups/local-backup-20250122-143000.sql

# Or using script directly
./scripts/db-restore.sh local backups/local-backup-20250122-143000.sql
```

### Seeding Test Data

```bash
# Small dataset (2 companies, ~15 records)
make dev-db-seed SIZE=small

# Medium dataset (5 companies, ~75 records)
make dev-db-seed SIZE=medium

# Large dataset (10 companies, ~200 records)
make dev-db-seed SIZE=large
```

### Reset Database

```bash
# Complete database reset (deletes all data!)
make dev-db-reset
```

This will:
1. Drop the database
2. Recreate the database
3. Run all migrations
4. Leave database empty (ready for seeding)

### Direct Database Access

```bash
# Using psql in container
make dev-shell-db

# Or connect with external tool
Host: localhost
Port: 5432
Database: rentflow_dev
User: rentflow_dev
Password: rentflow_dev_password
```

---

## Testing

### Running Tests

```bash
# Run all tests
make dev-test

# Run unit tests only
make dev-test-unit

# Run integration tests only
make dev-test-integration

# Run with coverage report
make dev-test-coverage
```

### Test Organization

```
tests/
├── unit/              # Unit tests (models, utilities)
├── integration/       # Integration tests (workflows)
├── views/             # Endpoint/view tests
└── fixtures/          # Shared test fixtures
```

### Writing Tests

**Example Unit Test:**
```python
# tests/unit/test_models.py
import pytest
from website.models import Company

def test_company_creation(app):
    with app.app_context():
        company = Company(
            name="Test Company",
            email="test@example.com"
        )
        assert company.name == "Test Company"
```

**Example Integration Test:**
```python
# tests/integration/test_tenant_workflow.py
import pytest
from website.models import Tenant, Lease

def test_create_tenant_and_lease(client, company, property_unit):
    # Create tenant
    response = client.post('/tenant/create', data={
        'first_name': 'John',
        'last_name': 'Doe',
        'email': 'john@example.com'
    })
    assert response.status_code == 302

    # Verify tenant created
    tenant = Tenant.query.filter_by(email='john@example.com').first()
    assert tenant is not None
```

### Test Coverage

Aim for minimum 80% coverage:

```bash
# Generate coverage report
make dev-test-coverage

# View HTML report
open htmlcov/index.html
```

---

## Debugging

### Application Debugging

#### Python Debugger (pdb)

Add breakpoint in code:
```python
import pdb; pdb.set_trace()
```

Then access container:
```bash
make dev-shell
python script_with_breakpoint.py
```

#### VS Code Debugging

See [IDE Setup](#ide-setup) for VS Code remote debugging configuration.

### Logging

#### View Application Logs

```bash
# Follow logs in real-time
make dev-logs-web

# View last 100 lines
docker compose -f docker-compose.local.yml logs --tail=100 web
```

#### Add Custom Logging

```python
import logging

logger = logging.getLogger(__name__)

def my_function():
    logger.info("Starting function")
    logger.debug(f"Variable value: {variable}")
    logger.error("Something went wrong!")
```

### Database Debugging

#### View Query Logs

Enable query logging in `.env.local`:
```bash
SQLALCHEMY_ECHO=True
```

#### Inspect Database

```bash
# Access database shell
make dev-shell-db

# List tables
\dt

# Describe table
\d+ table_name

# Run query
SELECT * FROM "user" LIMIT 10;
```

### Network Debugging

```bash
# Check if services are reachable
curl http://localhost:5000/health

# Test database connection
docker compose -f docker-compose.local.yml exec db pg_isready -U rentflow_dev

# Test Redis connection
docker compose -f docker-compose.local.yml exec redis redis-cli ping
```

---

## IDE Setup

### Visual Studio Code

#### Recommended Extensions

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.vscode-pylance",
    "ms-azuretools.vscode-docker",
    "GitHub.copilot",
    "eamodio.gitlens",
    "ms-python.black-formatter",
    "ms-python.flake8"
  ]
}
```

#### Python Configuration

Create `.vscode/settings.json`:
```json
{
  "python.defaultInterpreterPath": "/usr/local/bin/python3",
  "python.linting.enabled": true,
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "python.testing.unittestEnabled": false,
  "editor.formatOnSave": true,
  "files.exclude": {
    "**/__pycache__": true,
    "**/*.pyc": true
  }
}
```

#### Remote Debugging

Create `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "Python: Remote Attach",
      "type": "python",
      "request": "attach",
      "connect": {
        "host": "localhost",
        "port": 5678
      },
      "pathMappings": [
        {
          "localRoot": "${workspaceFolder}",
          "remoteRoot": "/app"
        }
      ]
    }
  ]
}
```

### PyCharm

#### Docker Compose Interpreter

1. Go to: `Settings` → `Project` → `Python Interpreter`
2. Click gear icon → `Add`
3. Select `Docker Compose`
4. Choose `docker-compose.local.yml`
5. Service: `web`

#### Run Configuration

1. Create new `Python` configuration
2. Script path: `main.py`
3. Interpreter: Docker Compose (web)
4. Environment variables: `FLASK_ENV=development`

---

## Troubleshooting

### Common Issues

#### Port Already in Use

**Problem**: `Error: port is already allocated`

**Solution**:
```bash
# Find process using port
lsof -i :5000
# or
netstat -anp | grep 5000

# Kill the process
kill -9 <PID>

# Or change port in .env.local
FLASK_PORT=5001
```

#### Database Connection Failed

**Problem**: `psycopg2.OperationalError: could not connect to server`

**Solution**:
```bash
# Check if database container is running
docker compose -f docker-compose.local.yml ps db

# Restart database
docker compose -f docker-compose.local.yml restart db

# Check database logs
make dev-logs-db

# Verify connection
docker compose -f docker-compose.local.yml exec db pg_isready
```

#### Permission Denied on Volumes

**Problem**: `Permission denied: '/app/logs'`

**Solution**:
```bash
# Fix permissions
sudo chown -R $USER:$USER logs/ uploads/ instance/

# Or recreate volumes
docker compose -f docker-compose.local.yml down -v
make dev-up
```

#### Docker Out of Space

**Problem**: `no space left on device`

**Solution**:
```bash
# Clean up Docker resources
docker system prune -a --volumes

# Remove old images
docker image prune -a

# Remove unused volumes
docker volume prune
```

#### Migration Conflicts

**Problem**: `Multiple head revisions detected`

**Solution**:
```bash
# Access web container
make dev-shell

# View migration heads
flask db heads

# Merge heads
flask db merge heads -m "merge migration branches"

# Apply merged migration
flask db upgrade
```

### Reset Everything

If all else fails, nuclear option:

```bash
# Stop and remove everything
make clean

# Remove local configuration
rm .env.local

# Start fresh
./scripts/local-dev-setup.sh --seed-data
```

---

## Best Practices

### Code Style

#### Python

- Follow [PEP 8](https://pep8.org/)
- Use [Black](https://black.readthedocs.io/) for formatting
- Maximum line length: 100 characters
- Use type hints where appropriate

```python
# Good
def calculate_rent(unit: Unit, months: int) -> Decimal:
    """Calculate total rent for given period."""
    return unit.rent_amount * Decimal(months)

# Bad
def calc(u, m):
    return u.rent_amount * m
```

#### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Format
type(scope): subject

# Examples
feat(auth): add two-factor authentication
fix(lease): correct rent calculation for partial months
docs(deployment): update staging setup instructions
chore(deps): upgrade Flask to 3.0.0
```

### Database

#### Queries

- Always filter by `company_id` for multi-tenant isolation
- Use SQLAlchemy ORM instead of raw SQL
- Add indexes for frequently queried fields
- Use pagination for large result sets

```python
# Good - filtered by company
properties = Property.query.filter_by(
    company_id=current_user.company_id
).order_by(Property.name).paginate(page=1, per_page=20)

# Bad - missing company filter (security risk!)
properties = Property.query.all()
```

#### Migrations

- Create migration after every model change
- Review migration before applying
- Never edit existing migrations in production
- Use descriptive migration messages

### Testing

- Write tests before fixing bugs (TDD)
- Test multi-tenant isolation
- Test role-based access control
- Mock external services
- Aim for 80%+ coverage

### Security

- Never commit `.env` files
- Always validate user input
- Filter all queries by `company_id`
- Use role decorators for access control
- Hash passwords with Werkzeug

### Performance

- Use database indexes
- Implement pagination
- Cache frequently accessed data
- Optimize N+1 queries with eager loading
- Use Redis for session storage

---

## Environment Variables

### Development (.env.local)

```bash
# Flask Configuration
FLASK_ENV=development
DEBUG=True
SECRET_KEY=dev-secret-key-change-in-production

# Database
DATABASE_URL=postgresql://rentflow_dev:rentflow_dev_password@db:5432/rentflow_dev

# Redis
REDIS_URL=redis://redis:6379/0

# Ports
FLASK_PORT=8000
POSTGRES_PORT=5432
REDIS_PORT=6379
```

### Staging (.env.staging)

See `.env.staging.example` for staging-specific configuration.

### Production (.env.production)

See `.env.production.example` for production-specific configuration.

---

## Additional Resources

### Documentation

- [README.md](README.md) - Project overview
- [BRANCHING.md](BRANCHING.md) - Git workflow
- [GITHUB_SETUP.md](GITHUB_SETUP.md) - Repository configuration
- [DEPLOYMENT.md](DEPLOYMENT.md) - Deployment guide
- [CLAUDE.md](CLAUDE.md) - Project context for AI assistance

### External Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [pytest Documentation](https://docs.pytest.org/)

### Community

- Report issues: [GitHub Issues](https://github.com/yourusername/rentflow/issues)
- Ask questions: Team Slack channel or email

---

## Quick Reference

### Most Used Commands

```bash
# Daily workflow
make dev-up              # Start environment
make dev-logs            # View logs
make dev-test            # Run tests
make dev-shell           # Access container
make dev-down            # Stop environment

# Database
make dev-migrate         # Run migrations
make dev-db-backup       # Backup database
make dev-db-seed         # Seed test data
make dev-db-reset        # Reset database

# Git
make feature NAME=x      # Create feature branch
make sync-develop        # Sync with develop

# See all commands
make help
```

---

**Last Updated**: 2025-10-22
**Maintained By**: Development Team

For questions or issues, contact the development team or refer to this guide.
