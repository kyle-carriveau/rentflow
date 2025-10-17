#!/bin/bash
# Generate self-signed SSL certificates for development

set -e

echo "Generating self-signed SSL certificates for development..."

# Create ssl directory if it doesn't exist
mkdir -p ssl

# Generate self-signed certificate
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout ssl/key.pem \
  -out ssl/cert.pem \
  -subj "/C=US/ST=State/L=City/O=RentFlow/CN=localhost"

# Set permissions
chmod 600 ssl/key.pem
chmod 644 ssl/cert.pem

echo "✓ SSL certificates generated in ssl/ directory"
echo "✓ cert.pem and key.pem created"
echo ""
echo "⚠ WARNING: These are self-signed certificates for development only!"
echo "For production, use Let's Encrypt: certbot certonly --standalone -d yourdomain.com"
