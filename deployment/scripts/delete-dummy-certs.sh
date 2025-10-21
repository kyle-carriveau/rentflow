#!/bin/bash
# Delete Dummy SSL Certificates
# Run this if you have self-signed dummy certificates and need to get real ones

set -e

COMPOSE_FILE="deployment/docker/docker-compose.yml"
ENV_FILE=".env"
DOMAIN="rentflow.cloud"

echo "=========================================="
echo "  Delete Dummy SSL Certificates"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "$ENV_FILE" ] || [ ! -f "$COMPOSE_FILE" ]; then
    echo "ERROR: Must run from project root (/home/ubuntu/rentflow)"
    exit 1
fi

echo "This will delete all certificates for $DOMAIN"
echo "After deletion, you can run init-ssl.sh to get real Let's Encrypt certificates."
echo ""
read -p "Continue? (yes/no): " CONFIRM

if [ "$CONFIRM" != "yes" ]; then
    echo "Cancelled"
    exit 0
fi

echo ""
echo "=== Deleting certificates for $DOMAIN ==="

# Try to delete using certbot
if docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm certbot delete --cert-name "$DOMAIN" --non-interactive 2>&1; then
    echo "✓ Certificates deleted successfully"
else
    echo "⚠️  No certificates found to delete (this is OK if starting fresh)"
fi

echo ""
echo "=== Removing certificate files and corrupted renewal configs ==="

# Remove certificate files, archives, and renewal configs (including corrupted ones)
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm --entrypoint "sh -c \"rm -rf /etc/letsencrypt/live/$DOMAIN /etc/letsencrypt/archive/$DOMAIN /etc/letsencrypt/renewal/$DOMAIN.conf /etc/letsencrypt/renewal/*\"" certbot 2>/dev/null || true

echo "✓ Certificate files and renewal configs removed"

echo ""
echo "=========================================="
echo "  Cleanup Complete"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Run SSL initialization: ./deployment/scripts/init-ssl.sh --yes"
echo "  2. Wait 3-5 minutes for certificate generation"
echo "  3. Visit https://rentflow.cloud to verify"
echo ""
