#!/bin/bash
# Database Backup Script - Multi-Environment Support
# Backs up PostgreSQL databases from local, staging, or production environments
#
# Usage:
#   ./scripts/db-backup.sh [environment] [output_file]
#
# Examples:
#   ./scripts/db-backup.sh local                              # Backup local DB to backups/
#   ./scripts/db-backup.sh staging                            # Backup staging DB
#   ./scripts/db-backup.sh production                         # Backup production DB
#   ./scripts/db-backup.sh production /path/to/backup.sql     # Custom output path
#
# Environments: local, staging, production

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
BACKUP_DIR="$PROJECT_ROOT/backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)

# Ensure backups directory exists
mkdir -p "$BACKUP_DIR"

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
Database Backup Script

Usage:
    $0 [environment] [output_file]

Arguments:
    environment     Target environment (local, staging, production)
    output_file     Optional: Custom backup file path

Examples:
    $0 local
    $0 staging
    $0 production
    $0 production /tmp/my-backup.sql

Backup Location:
    Default: $BACKUP_DIR/[environment]-backup-YYYYMMDD-HHMMSS.sql

Environment Variables:
    Local:
        POSTGRES_USER (default: rentflow_dev)
        POSTGRES_DB (default: rentflow_dev)

    Staging/Production:
        Uses Docker container on VPS

EOF
    exit 1
}

# Parse arguments
ENVIRONMENT="${1:-local}"
CUSTOM_OUTPUT="$2"

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(local|staging|production)$ ]]; then
    print_error "Invalid environment: $ENVIRONMENT"
    echo "Valid environments: local, staging, production"
    usage
fi

# Determine output file
if [ -n "$CUSTOM_OUTPUT" ]; then
    BACKUP_FILE="$CUSTOM_OUTPUT"
else
    BACKUP_FILE="$BACKUP_DIR/${ENVIRONMENT}-backup-$TIMESTAMP.sql"
fi

# Ensure output directory exists
OUTPUT_DIR=$(dirname "$BACKUP_FILE")
mkdir -p "$OUTPUT_DIR"

print_info "Starting database backup..."
print_info "Environment: $ENVIRONMENT"
print_info "Output: $BACKUP_FILE"
echo ""

# Backup based on environment
case "$ENVIRONMENT" in
    local)
        print_info "Backing up local development database..."

        # Load local environment variables
        if [ -f "$PROJECT_ROOT/.env.local" ]; then
            source "$PROJECT_ROOT/.env.local"
        fi

        # Set defaults
        POSTGRES_USER="${POSTGRES_USER:-rentflow_dev}"
        POSTGRES_DB="${POSTGRES_DB:-rentflow_dev}"

        # Check if local database is running
        if ! docker compose -f "$PROJECT_ROOT/docker-compose.local.yml" ps db | grep -q "Up"; then
            print_error "Local database container is not running"
            print_info "Start with: make dev-up"
            exit 1
        fi

        # Backup from Docker container
        if docker compose -f "$PROJECT_ROOT/docker-compose.local.yml" exec -T db \
            pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > "$BACKUP_FILE" 2>/dev/null; then
            print_success "Local database backed up successfully"
        else
            print_error "Failed to backup local database"
            exit 1
        fi
        ;;

    staging)
        print_info "Backing up staging database..."

        # Check if staging is running
        if ! docker compose -f "$PROJECT_ROOT/docker-compose.staging.yml" ps db | grep -q "Up"; then
            print_error "Staging database container is not running"
            exit 1
        fi

        # Load staging environment
        if [ -f "$PROJECT_ROOT/.env.staging" ]; then
            source "$PROJECT_ROOT/.env.staging"
        fi

        POSTGRES_USER="${POSTGRES_USER:-rentflow_staging}"
        POSTGRES_DB="${POSTGRES_DB:-rentflow_staging}"

        # Backup from Docker container
        if docker compose -f "$PROJECT_ROOT/docker-compose.staging.yml" exec -T db \
            pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > "$BACKUP_FILE" 2>/dev/null; then
            print_success "Staging database backed up successfully"
        else
            print_error "Failed to backup staging database"
            exit 1
        fi
        ;;

    production)
        print_warning "Backing up PRODUCTION database..."
        print_warning "This operation will access your live production data"
        echo ""

        # Check if production is running
        COMPOSE_FILE="$PROJECT_ROOT/docker-compose.production.yml"
        if [ ! -f "$COMPOSE_FILE" ]; then
            COMPOSE_FILE="$PROJECT_ROOT/deployment/docker/docker-compose.yml"
        fi

        if ! docker compose -f "$COMPOSE_FILE" ps db | grep -q "Up"; then
            print_error "Production database container is not running"
            exit 1
        fi

        # Load production environment
        if [ -f "$PROJECT_ROOT/.env.production" ]; then
            source "$PROJECT_ROOT/.env.production"
        elif [ -f "$PROJECT_ROOT/.env" ]; then
            source "$PROJECT_ROOT/.env"
        fi

        POSTGRES_USER="${POSTGRES_USER:-rentflow_user}"
        POSTGRES_DB="${POSTGRES_DB:-rentflow}"

        # Backup from Docker container
        if docker compose -f "$COMPOSE_FILE" exec -T db \
            pg_dump -U "$POSTGRES_USER" "$POSTGRES_DB" > "$BACKUP_FILE" 2>/dev/null; then
            print_success "Production database backed up successfully"
        else
            print_error "Failed to backup production database"
            exit 1
        fi
        ;;
esac

# Verify backup file
if [ ! -f "$BACKUP_FILE" ] || [ ! -s "$BACKUP_FILE" ]; then
    print_error "Backup file is empty or doesn't exist"
    exit 1
fi

# Get file size
FILE_SIZE=$(du -h "$BACKUP_FILE" | cut -f1)

# Print summary
echo ""
print_success "Backup completed successfully!"
echo ""
echo "Backup Information:"
echo "  Environment:  $ENVIRONMENT"
echo "  File:         $BACKUP_FILE"
echo "  Size:         $FILE_SIZE"
echo "  Timestamp:    $TIMESTAMP"
echo ""
print_info "To restore this backup, run:"
echo "  ./scripts/db-restore.sh $ENVIRONMENT $BACKUP_FILE"
echo ""

# Cleanup old backups (keep last 7 days)
print_info "Cleaning up old backups (keeping last 7 days)..."
find "$BACKUP_DIR" -name "${ENVIRONMENT}-backup-*.sql" -type f -mtime +7 -delete 2>/dev/null || true
BACKUP_COUNT=$(find "$BACKUP_DIR" -name "${ENVIRONMENT}-backup-*.sql" -type f 2>/dev/null | wc -l)
print_success "Current backups: $BACKUP_COUNT files"

exit 0
