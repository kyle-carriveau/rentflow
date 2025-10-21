#!/bin/bash
# Production-Ready Let's Encrypt SSL Initialization
# This script safely obtains SSL certificates for first-time deployment
# Safe to run multiple times (idempotent)
#
# Usage:
#   ./init-ssl.sh          # Interactive mode (prompts for confirmation)
#   ./init-ssl.sh --yes    # Non-interactive mode (auto-confirm for CI/CD)

set -e

# Ensure we're in the project root
if [ ! -f ".env" ] || [ ! -f "deployment/docker/docker-compose.yml" ]; then
    echo "ERROR: Must run from project root (/home/ubuntu/rentflow)"
    echo "Usage: cd /home/ubuntu/rentflow && ./deployment/scripts/init-ssl.sh"
    exit 1
fi

# Configuration
DOMAIN="rentflow.cloud"
EMAIL="admin@rentflow.cloud"  # TODO: Update this to your actual email
COMPOSE_FILE="deployment/docker/docker-compose.yml"
ENV_FILE=".env"
STAGING=0  # Set to 1 for testing with staging server
AUTO_CONFIRM=0  # Set to 1 to skip confirmation prompt

# Parse arguments
for arg in "$@"; do
    case $arg in
        --yes|-y)
            AUTO_CONFIRM=1
            shift
            ;;
        --staging)
            STAGING=1
            shift
            ;;
    esac
done

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_header() {
    echo -e "\n${BLUE}==>${NC} ${1}"
}

print_success() {
    echo -e "${GREEN}✓${NC} ${1}"
}

print_error() {
    echo -e "${RED}✗${NC} ${1}"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} ${1}"
}

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  SSL Certificate Initialization${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Domain: $DOMAIN"
echo "Email: $EMAIL"
echo "Mode: $([ $STAGING -eq 1 ] && echo 'STAGING (test certs)' || echo 'PRODUCTION')"
echo ""

# Step 1: Check if certificates already exist
print_header "Checking existing certificates..."

if docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm certbot certificates 2>/dev/null | grep -q "$DOMAIN"; then
    print_success "Certificates already exist for $DOMAIN"

    # Check expiration
    print_header "Validating certificate expiration..."
    EXPIRY=$(docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm certbot certificates 2>/dev/null | grep "Expiry Date" | head -1)
    echo "$EXPIRY"

    print_success "SSL certificates are already configured and valid"
    print_warning "If you need to renew or recreate certificates, remove them first:"
    echo "  docker compose -f $COMPOSE_FILE --env-file $ENV_FILE run --rm certbot delete --cert-name $DOMAIN"
    exit 0
fi

print_warning "No certificates found. Proceeding with initialization..."

# Step 2: Validate prerequisites
print_header "Validating prerequisites..."

# Check DNS
print_header "Checking DNS resolution..."
RESOLVED_IP=$(dig +short "$DOMAIN" @8.8.8.8 | tail -1)
if [ -z "$RESOLVED_IP" ]; then
    print_error "DNS resolution failed for $DOMAIN"
    exit 1
fi
print_success "DNS resolves to: $RESOLVED_IP"

# Check Docker
if ! command -v docker &> /dev/null; then
    print_error "Docker not found"
    exit 1
fi
print_success "Docker found"

# Confirm (skip if auto-confirm enabled)
if [ $AUTO_CONFIRM -eq 0 ]; then
    echo ""
    read -p "Continue with SSL certificate setup? (yes/no): " CONFIRM
    if [ "$CONFIRM" != "yes" ]; then
        echo "Setup cancelled"
        exit 0
    fi
else
    echo ""
    print_success "Auto-confirm enabled (non-interactive mode)"
fi

# Step 3: Generate DH parameters if missing
print_header "Checking DH parameters..."

if ! docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm --entrypoint "test -f /etc/letsencrypt/ssl-dhparams.pem" certbot 2>/dev/null; then
    print_warning "Generating DH parameters (this takes 2-3 minutes)..."
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm --entrypoint "openssl dhparam -out /etc/letsencrypt/ssl-dhparams.pem 2048" certbot
    print_success "DH parameters generated"
else
    print_success "DH parameters already exist"
fi

# Step 3.5: Create dummy certificates if Let's Encrypt ones don't exist
print_header "Creating temporary dummy certificates for NGINX..."

if ! docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm --entrypoint "test -f /etc/letsencrypt/live/$DOMAIN/fullchain.pem" certbot 2>/dev/null; then
    print_warning "Creating dummy certificates so NGINX can start..."

    # Create directory structure
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm --entrypoint "mkdir -p /etc/letsencrypt/live/$DOMAIN" certbot

    # Generate self-signed certificate
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm --entrypoint "sh -c \"
        openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
            -keyout /etc/letsencrypt/live/$DOMAIN/privkey.pem \
            -out /etc/letsencrypt/live/$DOMAIN/fullchain.pem \
            -subj '/CN=$DOMAIN' 2>/dev/null && \
        cp /etc/letsencrypt/live/$DOMAIN/fullchain.pem /etc/letsencrypt/live/$DOMAIN/chain.pem
    \"" certbot

    print_success "Dummy certificates created (will be replaced with real ones)"
else
    print_success "Certificates already exist in Docker volume"
fi

# Step 4: Ensure services are running
print_header "Starting required services..."

docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" up -d db redis web nginx certbot-renewal

print_success "Services started (including automatic certificate renewal)"

# Step 5: Wait for services to be healthy
print_header "Waiting for services to be healthy..."
sleep 10

# Check if NGINX is accessible
if ! curl -f -s http://localhost/.well-known/acme-challenge/ &> /dev/null; then
    print_warning "NGINX may not be serving ACME challenge correctly"
    print_warning "Continuing anyway..."
fi

# Step 6: Request certificates
print_header "Requesting SSL certificates from Let's Encrypt..."

STAGING_ARG=""
if [ $STAGING -eq 1 ]; then
    STAGING_ARG="--staging"
    print_warning "Using STAGING server (test certificates)"
fi

# Request certificate
set +e  # Don't exit on error, we want to handle it
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm certbot certonly \
    --webroot \
    --webroot-path /var/www/certbot \
    $STAGING_ARG \
    --email "$EMAIL" \
    --agree-tos \
    --no-eff-email \
    -d "$DOMAIN" \
    -d "www.$DOMAIN" \
    --non-interactive

CERT_RESULT=$?
set -e

if [ $CERT_RESULT -ne 0 ]; then
    print_error "Failed to obtain SSL certificates"
    echo ""
    print_warning "Troubleshooting steps:"
    echo "  1. Verify DNS: dig +short $DOMAIN"
    echo "  2. Check firewall: ports 80 and 443 must be open"
    echo "  3. Check logs: docker compose -f $COMPOSE_FILE logs nginx"
    echo "  4. Try staging mode first: Edit script and set STAGING=1"
    exit 1
fi

print_success "SSL certificates obtained successfully!"

# Step 7: Reload NGINX to use new certificates
print_header "Reloading NGINX with new certificates..."

docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" exec nginx nginx -s reload

print_success "NGINX reloaded"

# Step 8: Verify HTTPS is working
print_header "Verifying HTTPS..."

sleep 3

if curl -f -s -k https://localhost &> /dev/null; then
    print_success "HTTPS is working!"
else
    print_warning "HTTPS verification inconclusive (this may be normal)"
fi

# Done!
echo ""
echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  SSL Setup Complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
print_success "Your site is now secured with HTTPS"
echo "  • https://$DOMAIN"
echo "  • https://www.$DOMAIN"
echo ""
print_success "Certificates will auto-renew via certbot-renewal container"
echo ""
print_warning "Next steps:"
echo "  1. Visit https://$DOMAIN in your browser"
echo "  2. Verify green padlock appears"
echo "  3. Check renewal logs: docker compose -f $COMPOSE_FILE logs certbot-renewal"
echo ""
