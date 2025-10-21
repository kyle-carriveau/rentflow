#!/bin/bash
# SSL Certificate Status Check
# This script helps diagnose SSL certificate issues

set -e

COMPOSE_FILE="deployment/docker/docker-compose.yml"
ENV_FILE=".env"
DOMAIN="rentflow.cloud"

echo "=========================================="
echo "  SSL Certificate Status Check"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "$ENV_FILE" ] || [ ! -f "$COMPOSE_FILE" ]; then
    echo "ERROR: Must run from project root (/home/ubuntu/rentflow)"
    exit 1
fi

echo "=== 1. Checking certificate files in Docker volume ==="
echo ""

# Check if certificates exist
if docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm --entrypoint "test -f /etc/letsencrypt/live/$DOMAIN/fullchain.pem" certbot 2>/dev/null; then
    echo "✓ Certificate files found"

    # Show certificate details
    echo ""
    echo "=== 2. Certificate Information ==="
    docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm certbot certificates

    # Check if it's a self-signed (dummy) certificate
    echo ""
    echo "=== 3. Checking if certificate is self-signed (dummy) ==="
    CERT_INFO=$(docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" run --rm --entrypoint "openssl x509 -in /etc/letsencrypt/live/$DOMAIN/fullchain.pem -noout -issuer -dates" certbot 2>/dev/null)

    # Real Let's Encrypt certs have issuer like: "O = Let's Encrypt, CN = R3" or similar
    # Dummy self-signed certs have issuer like: "CN = rentflow.cloud"
    if echo "$CERT_INFO" | grep -q "Let's Encrypt"; then
        echo "✓ This appears to be a real Let's Encrypt certificate"
        echo ""
        echo "$CERT_INFO"
    else
        echo "⚠️  WARNING: This is a DUMMY self-signed certificate!"
        echo ""
        echo "$CERT_INFO"
        echo ""
        echo "Issuer does NOT contain 'Let's Encrypt' - this is self-signed."
        echo "You need to obtain real Let's Encrypt certificates."
    fi
else
    echo "❌ No certificate files found"
fi

echo ""
echo "=== 4. Running Container Status ==="
docker ps --filter "name=certbot" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

echo ""
echo "=== 5. NGINX Status ==="
docker compose -f "$COMPOSE_FILE" --env-file "$ENV_FILE" ps nginx

echo ""
echo "=== 6. Testing HTTPS Connection ==="
if curl -I -k https://localhost 2>&1 | head -5; then
    echo "✓ HTTPS is responding"
else
    echo "❌ HTTPS is not responding"
fi

echo ""
echo "=========================================="
echo "  Diagnosis Summary"
echo "=========================================="
echo ""
echo "Next steps based on findings:"
echo ""
echo "If certificates are DUMMY/self-signed:"
echo "  1. Delete dummy certificates: ./deployment/scripts/delete-dummy-certs.sh"
echo "  2. Run SSL initialization: ./deployment/scripts/init-ssl.sh --yes"
echo ""
echo "If certificates are real Let's Encrypt but HTTPS shows as insecure:"
echo "  1. Reload NGINX: docker compose -f $COMPOSE_FILE exec nginx nginx -s reload"
echo "  2. Check browser certificate details for specific error"
echo ""
