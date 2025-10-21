#!/bin/bash
# Initialize Let's Encrypt SSL Certificates for RentFlow
# This script obtains initial SSL certificates from Let's Encrypt

set -e

# Configuration
DOMAIN="rentflow.cloud"
EMAIL="admin@rentflow.cloud"  # Change this to your email
COMPOSE_FILE="deployment/docker/docker-compose.yml"
STAGING=0  # Set to 1 for testing, 0 for production certificates

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}==>${NC} $1"
}

print_error() {
    echo -e "${RED}ERROR:${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}WARNING:${NC} $1"
}

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  Let's Encrypt SSL Setup${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""
echo "Domain: $DOMAIN"
echo "Email: $EMAIL"
echo "Staging: $([ $STAGING -eq 1 ] && echo 'Yes (test certificates)' || echo 'No (production certificates)')"
echo ""

# Confirm
read -p "Continue with SSL certificate setup? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    print_status "Setup cancelled"
    exit 0
fi

print_status "Creating certificate directories..."
mkdir -p certbot/conf/live/$DOMAIN
mkdir -p certbot/www

print_status "Generating DH parameters (this may take a few minutes)..."
if [ ! -f "certbot/conf/ssl-dhparams.pem" ]; then
    openssl dhparam -out certbot/conf/ssl-dhparams.pem 2048
    print_status "✓ DH parameters generated"
else
    print_status "✓ DH parameters already exist"
fi

print_status "Creating dummy certificates for initial NGINX startup..."
if [ ! -d "certbot/conf/live/$DOMAIN" ]; then
    mkdir -p certbot/conf/live/$DOMAIN
fi

openssl req -x509 -nodes -newkey rsa:2048 -days 1 \
    -keyout certbot/conf/live/$DOMAIN/privkey.pem \
    -out certbot/conf/live/$DOMAIN/fullchain.pem \
    -subj "/CN=$DOMAIN" 2>/dev/null

cp certbot/conf/live/$DOMAIN/fullchain.pem certbot/conf/live/$DOMAIN/chain.pem

print_status "✓ Dummy certificates created"

print_status "Starting NGINX to handle ACME challenge..."
docker compose -f "$COMPOSE_FILE" --env-file .env up -d nginx

print_status "Waiting for NGINX to be ready..."
sleep 5

print_status "Removing dummy certificates..."
docker compose -f "$COMPOSE_FILE" --env-file .env run --rm --entrypoint "\
    rm -rf /etc/letsencrypt/live/$DOMAIN && \
    rm -rf /etc/letsencrypt/archive/$DOMAIN && \
    rm -rf /etc/letsencrypt/renewal/$DOMAIN.conf" certbot

print_status "Requesting Let's Encrypt certificate..."

# Set staging flag if testing
STAGING_ARG=""
if [ $STAGING -eq 1 ]; then
    STAGING_ARG="--staging"
    print_warning "Using Let's Encrypt STAGING server (test certificates)"
fi

# Request certificate
docker compose -f "$COMPOSE_FILE" --env-file .env run --rm --entrypoint "\
    certbot certonly --webroot -w /var/www/certbot \
    $STAGING_ARG \
    --email $EMAIL \
    --agree-tos \
    --no-eff-email \
    --force-renewal \
    -d $DOMAIN -d www.$DOMAIN" certbot

if [ $? -eq 0 ]; then
    print_status "✓ SSL certificates obtained successfully!"
else
    print_error "Failed to obtain SSL certificates"
    print_status "Check that:"
    print_status "  1. Domain $DOMAIN points to this server"
    print_status "  2. Ports 80 and 443 are open in firewall"
    print_status "  3. No other service is using port 80"
    exit 1
fi

print_status "Reloading NGINX with new certificates..."
docker compose -f "$COMPOSE_FILE" --env-file .env exec nginx nginx -s reload

print_status "${GREEN}✓${NC} SSL setup complete!"
print_status ""
print_status "Your site is now secured with HTTPS:"
print_status "  https://$DOMAIN"
print_status "  https://www.$DOMAIN"
print_status ""
print_status "Certificates will auto-renew via the certbot container."
print_status "Check renewal with: docker compose -f $COMPOSE_FILE logs certbot"
