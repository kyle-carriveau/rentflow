#!/bin/bash
# Database Restore Script - Multi-Environment Support
# Restores PostgreSQL databases to local, staging, or production environments
#
# Usage:
#   ./scripts/db-restore.sh [environment] [backup_file]
#
# Examples:
#   ./scripts/db-restore.sh local backups/local-backup-20250122-143000.sql
#   ./scripts/db-restore.sh staging backups/production-backup-20250122-120000.sql
#   ./scripts/db-restore.sh production backups/production-backup-20250122-120000.sql
#
# ⚠️ WARNING: This will OVERWRITE the target database!
# Always backup before restoring to production or staging.

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

# Function to show usage
usage() {
    cat << EOF
Database Restore Script

Usage:
    $0 [environment] [backup_file]

Arguments:
    environment     Target environment (local, staging, production)
    backup_file     Path to SQL backup file

Examples:
    $0 local backups/local-backup-20250122-143000.sql
    $0 staging backups/staging-backup-20250122-120000.sql
    $0 production backups/production-backup-20250122-120000.sql

⚠️  WARNING: This will REPLACE ALL DATA in the target database!

Safety:
    - Local: No confirmation required
    - Staging: Requires confirmation
    - Production: Requires EXPLICIT confirmation and backup creation

EOF
    exit 1
}

# Function to confirm action
confirm() {
    local prompt="$1"
    local confirmation_text="$2"

    echo ""
    print_warning "$prompt"
    echo -e "${YELLOW}Type '$confirmation_text' to continue:${NC}"
    read -r response

    if [ "$response" != "$confirmation_text" ]; then
        print_error "Confirmation failed. Aborting."
        exit 1
    fi
}

# Parse arguments
ENVIRONMENT="${1}"
BACKUP_FILE="${2}"

# Validate arguments
if [ -z "$ENVIRONMENT" ] || [ -z "$BACKUP_FILE" ]; then
    print_error "Missing required arguments"
    usage
fi

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(local|staging|production)$ ]]; then
    print_error "Invalid environment: $ENVIRONMENT"
    echo "Valid environments: local, staging, production"
    usage
fi

# Validate backup file exists
if [ ! -f "$BACKUP_FILE" ]; then
    print_error "Backup file not found: $BACKUP_FILE"
    exit 1
fi

# Get backup file info
FILE_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)

print_info "Database Restore Operation"
echo ""
echo "  Environment:  ${ENVIRONMENT^^}"
echo "  Backup File:  $BACKUP_FILE"
echo "  File Size:    $FILE_SIZE"
echo ""

# Environment-specific confirmation
case "$ENVIRONMENT" in
    local)
        print_info "Restoring to local development database..."
        ;;

    staging)
        confirm "You are about to OVERWRITE the STAGING database!" "RESTORE STAGING"
        ;;

    production)
        print_warning "═════════════════════════════════════════════════════"
        print_warning "  ⚠️  PRODUCTION DATABASE RESTORE  ⚠️"
        print_warning "═════════════════════════════════════════════════════"
        echo ""
        print_warning "This will PERMANENTLY REPLACE all production data!"
        echo ""

        # Create automatic backup before production restore
        print_info "Creating automatic safety backup first..."
        SAFETY_BACKUP="$PROJECT_ROOT/backups/production-pre-restore-$(date +%Y%m%d-%H%M%S).sql"

        if "$SCRIPT_DIR/db-backup.sh" production "$SAFETY_BACKUP"; then
            print_success "Safety backup created: $SAFETY_BACKUP"
        else
            print_error "Failed to create safety backup. Aborting restore."
            exit 1
        fi

        echo ""
        confirm "Type EXACTLY: 'RESTORE PRODUCTION DATABASE' to proceed" "RESTORE PRODUCTION DATABASE"
        ;;
esac

echo ""
print_info "Starting database restore..."

# Restore based on environment
case "$ENVIRONMENT" in
    local)
        # Load local environment variables
        if [ -f "$PROJECT_ROOT/.env.local" ]; then
            source "$PROJECT_ROOT/.env.local"
        fi

        POSTGRES_USER="${POSTGRES_USER:-rentflow_dev}"
        POSTGRES_DB="${POSTGRES_DB:-rentflow_dev}"

        # Check if local database is running
        if ! docker compose -f "$PROJECT_ROOT/docker-compose.local.yml" ps db | grep -q "Up"; then
            print_error "Local database container is not running"
            print_info "Start with: make dev-up"
            exit 1
        fi

        # Drop existing connections and recreate database
        print_info "Dropping existing database..."
        docker compose -f "$PROJECT_ROOT/docker-compose.local.yml" exec -T db \
            psql -U "$POSTGRES_USER" -d postgres <<EOF
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$POSTGRES_DB' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS "$POSTGRES_DB";
CREATE DATABASE "$POSTGRES_DB";
EOF

        # Restore from backup
        print_info "Restoring database from backup..."
        if cat "$BACKUP_FILE" | docker compose -f "$PROJECT_ROOT/docker-compose.local.yml" exec -T db \
            psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" > /dev/null 2>&1; then
            print_success "Local database restored successfully"
        else
            print_error "Failed to restore local database"
            exit 1
        fi
        ;;

    staging)
        # Load staging environment
        if [ -f "$PROJECT_ROOT/.env.staging" ]; then
            source "$PROJECT_ROOT/.env.staging"
        fi

        POSTGRES_USER="${POSTGRES_USER:-rentflow_staging}"
        POSTGRES_DB="${POSTGRES_DB:-rentflow_staging}"

        # Check if staging is running
        if ! docker compose -f "$PROJECT_ROOT/docker-compose.staging.yml" ps db | grep -q "Up"; then
            print_error "Staging database container is not running"
            exit 1
        fi

        # Drop existing connections and recreate database
        print_info "Dropping existing database..."
        docker compose -f "$PROJECT_ROOT/docker-compose.staging.yml" exec -T db \
            psql -U "$POSTGRES_USER" -d postgres <<EOF
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$POSTGRES_DB' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS "$POSTGRES_DB";
CREATE DATABASE "$POSTGRES_DB";
EOF

        # Restore from backup
        print_info "Restoring database from backup..."
        if cat "$BACKUP_FILE" | docker compose -f "$PROJECT_ROOT/docker-compose.staging.yml" exec -T db \
            psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" > /dev/null 2>&1; then
            print_success "Staging database restored successfully"
        else
            print_error "Failed to restore staging database"
            exit 1
        fi
        ;;

    production)
        # Load production environment
        COMPOSE_FILE="$PROJECT_ROOT/docker-compose.production.yml"
        if [ ! -f "$COMPOSE_FILE" ]; then
            COMPOSE_FILE="$PROJECT_ROOT/deployment/docker/docker-compose.yml"
        fi

        if [ -f "$PROJECT_ROOT/.env.production" ]; then
            source "$PROJECT_ROOT/.env.production"
        elif [ -f "$PROJECT_ROOT/.env" ]; then
            source "$PROJECT_ROOT/.env"
        fi

        POSTGRES_USER="${POSTGRES_USER:-rentflow_user}"
        POSTGRES_DB="${POSTGRES_DB:-rentflow}"

        # Check if production is running
        if ! docker compose -f "$COMPOSE_FILE" ps db | grep -q "Up"; then
            print_error "Production database container is not running"
            exit 1
        fi

        # Stop web container during restore to prevent corruption
        print_info "Stopping web application..."
        docker compose -f "$COMPOSE_FILE" stop web

        # Drop existing connections and recreate database
        print_info "Dropping existing database..."
        docker compose -f "$COMPOSE_FILE" exec -T db \
            psql -U "$POSTGRES_USER" -d postgres <<EOF
SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = '$POSTGRES_DB' AND pid <> pg_backend_pid();
DROP DATABASE IF EXISTS "$POSTGRES_DB";
CREATE DATABASE "$POSTGRES_DB";
EOF

        # Restore from backup
        print_info "Restoring database from backup..."
        if cat "$BACKUP_FILE" | docker compose -f "$COMPOSE_FILE" exec -T db \
            psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" > /dev/null 2>&1; then
            print_success "Production database restored successfully"
        else
            print_error "Failed to restore production database"
            print_warning "Starting web application..."
            docker compose -f "$COMPOSE_FILE" start web
            exit 1
        fi

        # Restart web application
        print_info "Starting web application..."
        docker compose -f "$COMPOSE_FILE" start web

        # Wait for health check
        print_info "Waiting for application to become healthy..."
        sleep 10
        ;;
esac

# Print summary
echo ""
print_success "Database restore completed successfully!"
echo ""
echo "Restore Information:"
echo "  Environment:  $ENVIRONMENT"
echo "  Source File:  $BACKUP_FILE"
echo "  File Size:    $FILE_SIZE"
echo ""

if [ "$ENVIRONMENT" == "production" ]; then
    print_warning "Safety backup saved to: $SAFETY_BACKUP"
    echo ""
    print_info "Verify production application health:"
    echo "  curl https://yourdomain.com/health"
fi

echo ""
print_success "Restore operation complete!"

exit 0
