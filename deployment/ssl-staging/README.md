# Staging SSL Certificates

This directory contains **self-signed SSL certificates** for the staging environment.

## Files

- `staging.crt` - Self-signed SSL certificate (1 year validity)
- `staging.key` - Private key for the certificate

## Certificate Details

- **Subject**: CN=staging.rentflow.local, OU=Staging, O=RentFlow
- **Type**: Self-signed (not trusted by browsers, expected for staging)
- **Validity**: 365 days from generation
- **Key Size**: RSA 2048-bit

## Usage

These certificates are mounted into the NGINX staging container:

```yaml
volumes:
  - ./deployment/ssl-staging:/etc/nginx/ssl:ro
```

## Browser Warning

⚠️ **Expected Behavior**: Browsers will show "Your connection is not private" warning when accessing staging via HTTPS. This is normal for self-signed certificates.

**To bypass**: Click "Advanced" → "Proceed to site (unsafe)" or add exception.

## Regenerating Certificates

If certificates expire or need to be regenerated:

```bash
cd deployment/ssl-staging

# Generate new self-signed certificate (365 days)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout staging.key \
  -out staging.crt \
  -subj "/C=US/ST=State/L=City/O=RentFlow/OU=Staging/CN=staging.rentflow.local"

# Restart NGINX to load new certificate
docker compose -f docker-compose.staging.yml restart nginx
```

## Production vs Staging

| Environment | Certificate Type | Trusted by Browsers |
|-------------|-----------------|---------------------|
| **Production** | Cloudflare Origin Certificate | ✅ Yes (via Cloudflare) |
| **Staging** | Self-signed | ❌ No (requires manual exception) |

## Security Note

🔒 **Important**: The staging private key (`staging.key`) is committed to git for convenience in staging deployments. This is acceptable for staging but **NEVER** commit production private keys to version control.
