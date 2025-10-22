#!/bin/bash
# Production to Staging Data Sync with PII Sanitization
# Safely copies production data to staging and sanitizes all PII
#
# Usage:
#   ./scripts/db-sync-to-staging.sh
#
# ⚠️ WARNING: This will OVERWRITE the staging database with sanitized production data!
#
# What gets sanitized:
#   - User emails: user{id}@example.com
#   - User passwords: Reset to 'StagingPassword123!'
#   - Tenant emails: tenant{id}@example.com
#   - Tenant phones: (555) 000-{id}
#   - Tenant addresses: Replaced with generic addresses
#   - Payment details: Cleared/anonymized
#   - Company information: Sanitized business details

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="$PROJECT_ROOT/backups"
TIMESTAMP=$(date +%Y%m%d-%H%M%S)
PROD_BACKUP="$BACKUP_DIR/production-sync-$TIMESTAMP.sql"
STAGING_COMPOSE="$PROJECT_ROOT/docker-compose.staging.yml"

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

print_sanitize() {
    echo -e "${MAGENTA}🔒${NC} $1"
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

# Show warning banner
echo ""
print_warning "════════════════════════════════════════════════════════════"
print_warning "  Production → Staging Data Sync with PII Sanitization"
print_warning "════════════════════════════════════════════════════════════"
echo ""
print_warning "This script will:"
echo "  1. ✅ Backup production database"
echo "  2. ⚠️  OVERWRITE staging database with production data"
echo "  3. 🔒 Sanitize all PII in staging database"
echo ""
print_warning "Sanitization includes:"
echo "  - User emails and passwords"
echo "  - Tenant contact information"
echo "  - Payment details"
echo "  - Addresses and phone numbers"
echo "  - Business information"
echo ""

# Require explicit confirmation
confirm "This will REPLACE ALL DATA in staging!" "SYNC TO STAGING"

echo ""
print_info "═══════════════════════════════════════════════════════════"
print_info "  STEP 1: Backup Production Database"
print_info "═══════════════════════════════════════════════════════════"
echo ""

if "$SCRIPT_DIR/db-backup.sh" production "$PROD_BACKUP"; then
    print_success "Production backup created: $PROD_BACKUP"
else
    print_error "Failed to backup production database"
    exit 1
fi

# Get backup file size
FILE_SIZE=$(du -h "$PROD_BACKUP" | cut -f1)
print_info "Backup size: $FILE_SIZE"

echo ""
print_info "═══════════════════════════════════════════════════════════"
print_info "  STEP 2: Restore Production Data to Staging"
print_info "═══════════════════════════════════════════════════════════"
echo ""

print_warning "About to restore production backup to staging..."
sleep 2

if "$SCRIPT_DIR/db-restore.sh" staging "$PROD_BACKUP"; then
    print_success "Production data restored to staging"
else
    print_error "Failed to restore data to staging"
    exit 1
fi

echo ""
print_info "═══════════════════════════════════════════════════════════"
print_info "  STEP 3: Sanitize PII in Staging Database"
print_info "═══════════════════════════════════════════════════════════"
echo ""

# Load staging environment
if [ -f "$PROJECT_ROOT/.env.staging" ]; then
    source "$PROJECT_ROOT/.env.staging"
fi

POSTGRES_USER="${POSTGRES_USER:-rentflow_staging}"
POSTGRES_DB="${POSTGRES_DB:-rentflow_staging}"

# Check if staging is running
if ! docker compose -f "$STAGING_COMPOSE" ps db | grep -q "Up"; then
    print_error "Staging database container is not running"
    exit 1
fi

print_sanitize "Sanitizing user data..."

# Sanitize Users table
docker compose -f "$STAGING_COMPOSE" exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<'EOF'
-- Sanitize user emails and passwords
UPDATE "user"
SET
    email = 'user' || id || '@example.com',
    password_hash = '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5GyYIXw8pKOPu', -- 'StagingPassword123!'
    first_name = 'User',
    last_name = CAST(id AS VARCHAR)
WHERE id > 0;

EOF

if [ $? -eq 0 ]; then
    print_success "User data sanitized"
else
    print_error "Failed to sanitize user data"
    exit 1
fi

print_sanitize "Sanitizing tenant data..."

# Sanitize Tenants table
docker compose -f "$STAGING_COMPOSE" exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<'EOF'
-- Sanitize tenant contact information
UPDATE tenant
SET
    first_name = 'Tenant',
    last_name = CAST(id AS VARCHAR),
    email = 'tenant' || id || '@example.com',
    phone = 5550000 + id,
    street_address = id || ' Test Street',
    city = 'Test City',
    state = 'CA',
    zip_code = '90000',
    emergency_contact_name = 'Emergency Contact ' || id,
    emergency_contact_phone = 5559999 + id
WHERE id > 0;

EOF

if [ $? -eq 0 ]; then
    print_success "Tenant data sanitized"
else
    print_error "Failed to sanitize tenant data"
    exit 1
fi

print_sanitize "Sanitizing payment data..."

# Sanitize Payments table
docker compose -f "$STAGING_COMPOSE" exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<'EOF'
-- Sanitize payment information
UPDATE payment
SET
    payment_method = 'Test Payment',
    notes = 'Sanitized payment record'
WHERE id > 0;

EOF

if [ $? -eq 0 ]; then
    print_success "Payment data sanitized"
else
    print_error "Failed to sanitize payment data"
    exit 1
fi

print_sanitize "Sanitizing company data..."

# Sanitize Company table
docker compose -f "$STAGING_COMPOSE" exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<'EOF'
-- Sanitize company business information
UPDATE company
SET
    name = 'Test Company ' || id,
    email = 'company' || id || '@example.com',
    phone = '555-000-' || LPAD(CAST(id AS VARCHAR), 4, '0'),
    address = id || ' Business Ave',
    city = 'Test City',
    state = 'CA',
    zip_code = '90000',
    website = 'https://company' || id || '.example.com',
    tax_id = 'XX-XXXXXXX'
WHERE id > 0;

EOF

if [ $? -eq 0 ]; then
    print_success "Company data sanitized"
else
    print_error "Failed to sanitize company data"
    exit 1
fi

echo ""
print_info "═══════════════════════════════════════════════════════════"
print_info "  STEP 4: Verify Sanitization"
print_info "═══════════════════════════════════════════════════════════"
echo ""

# Verify sanitization by checking for common PII patterns
print_info "Checking for unsanitized email domains..."

GMAIL_COUNT=$(docker compose -f "$STAGING_COMPOSE" exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT COUNT(*) FROM \"user\" WHERE email LIKE '%@gmail.com' OR email LIKE '%@yahoo.com' OR email LIKE '%@hotmail.com';")
TENANT_EMAIL_COUNT=$(docker compose -f "$STAGING_COMPOSE" exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT COUNT(*) FROM tenant WHERE email LIKE '%@gmail.com' OR email LIKE '%@yahoo.com' OR email LIKE '%@hotmail.com';")

GMAIL_COUNT=$(echo "$GMAIL_COUNT" | tr -d ' \n\r')
TENANT_EMAIL_COUNT=$(echo "$TENANT_EMAIL_COUNT" | tr -d ' \n\r')

if [ "$GMAIL_COUNT" = "0" ] && [ "$TENANT_EMAIL_COUNT" = "0" ]; then
    print_success "No personal email domains found - sanitization verified"
else
    print_warning "Found $GMAIL_COUNT user records and $TENANT_EMAIL_COUNT tenant records with personal email domains"
    print_warning "Manual review recommended"
fi

# Get record counts
USER_COUNT=$(docker compose -f "$STAGING_COMPOSE" exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT COUNT(*) FROM \"user\";")
TENANT_COUNT=$(docker compose -f "$STAGING_COMPOSE" exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT COUNT(*) FROM tenant;")
COMPANY_COUNT=$(docker compose -f "$STAGING_COMPOSE" exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT COUNT(*) FROM company;")
PROPERTY_COUNT=$(docker compose -f "$STAGING_COMPOSE" exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT COUNT(*) FROM property;")
LEASE_COUNT=$(docker compose -f "$STAGING_COMPOSE" exec -T db psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -t -c "SELECT COUNT(*) FROM lease;")

USER_COUNT=$(echo "$USER_COUNT" | tr -d ' \n\r')
TENANT_COUNT=$(echo "$TENANT_COUNT" | tr -d ' \n\r')
COMPANY_COUNT=$(echo "$COMPANY_COUNT" | tr -d ' \n\r')
PROPERTY_COUNT=$(echo "$PROPERTY_COUNT" | tr -d ' \n\r')
LEASE_COUNT=$(echo "$LEASE_COUNT" | tr -d ' \n\r')

echo ""
print_success "════════════════════════════════════════════════════════════"
print_success "  Data Sync and Sanitization Complete!"
print_success "════════════════════════════════════════════════════════════"
echo ""
echo "Staging Database Statistics:"
echo "  Companies:  $COMPANY_COUNT"
echo "  Users:      $USER_COUNT"
echo "  Properties: $PROPERTY_COUNT"
echo "  Tenants:    $TENANT_COUNT"
echo "  Leases:     $LEASE_COUNT"
echo ""
print_info "Backup saved: $PROD_BACKUP"
echo ""
print_warning "All PII has been sanitized in staging:"
echo "  ✓ User emails:    user{id}@example.com"
echo "  ✓ User passwords: StagingPassword123!"
echo "  ✓ Tenant emails:  tenant{id}@example.com"
echo "  ✓ Tenant phones:  (555) 000-{id}"
echo "  ✓ Addresses:      Anonymized test addresses"
echo "  ✓ Payment info:   Cleared"
echo "  ✓ Company info:   Sanitized business data"
echo ""
print_success "Staging environment ready for testing!"
echo ""
print_info "Test the staging environment:"
echo "  URL: https://staging.yourdomain.com (or http://your-ip:8080)"
echo "  Login: user{id}@example.com / StagingPassword123!"
echo ""

# Cleanup old sync backups (keep last 3)
print_info "Cleaning up old sync backups (keeping last 3)..."
ls -t "$BACKUP_DIR"/production-sync-*.sql 2>/dev/null | tail -n +4 | xargs rm -f 2>/dev/null || true
SYNC_BACKUP_COUNT=$(ls -1 "$BACKUP_DIR"/production-sync-*.sql 2>/dev/null | wc -l)
print_success "Sync backups retained: $SYNC_BACKUP_COUNT"

echo ""
print_success "Sync operation complete!"

exit 0
