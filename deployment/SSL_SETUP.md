# SSL/HTTPS Setup with Let's Encrypt

This guide explains how to enable HTTPS for RentFlow using free Let's Encrypt SSL certificates.

## Prerequisites

✅ **Domain name** pointing to your VPS IP
- Domain: `rentflow.cloud`
- DNS A Record: `93.127.197.136`

✅ **Ports 80 and 443** open in firewall

✅ **Application deployed** and running

## Initial SSL Certificate Setup

### Step 1: Update Email in Script

Edit `deployment/scripts/init-letsencrypt.sh` and change:
```bash
EMAIL="admin@rentflow.cloud"  # Change to your actual email
```

### Step 2: Run SSL Initialization Script

SSH to your VPS and run:

```bash
cd /home/ubuntu/rentflow

# Run the SSL initialization script
./deployment/scripts/init-letsencrypt.sh
```

This script will:
1. Generate DH parameters for stronger encryption
2. Create temporary dummy certificates
3. Start NGINX to handle ACME challenge
4. Request real certificates from Let's Encrypt
5. Replace dummy certificates with real ones
6. Reload NGINX with new certificates

### Step 3: Verify HTTPS

After successful setup:

```bash
# Check certificate validity
docker compose -f deployment/docker/docker-compose.yml --env-file .env \
  exec certbot certbot certificates

# Test HTTPS access
curl -I https://rentflow.cloud
```

Visit your site:
- https://rentflow.cloud ✅
- https://www.rentflow.cloud ✅

## Automatic Certificate Renewal

Certificates are **automatically renewed** by the certbot container running in the background.

- **Renewal frequency:** Every 12 hours (checks if renewal needed)
- **Certificate lifetime:** 90 days
- **Auto-renewal:** 30 days before expiration

### Check Renewal Status

```bash
# View certbot container logs
docker compose -f deployment/docker/docker-compose.yml --env-file .env logs certbot

# Manually trigger renewal test
docker compose -f deployment/docker/docker-compose.yml --env-file .env \
  exec certbot certbot renew --dry-run
```

## Testing with Staging Certificates

If you want to test the setup without hitting Let's Encrypt rate limits, use staging mode:

1. Edit `deployment/scripts/init-letsencrypt.sh`
2. Set `STAGING=1`
3. Run the script
4. Verify setup works (browser will show "invalid certificate" - this is normal for staging)
5. Set `STAGING=0` and run again for production certificates

## Troubleshooting

### Issue: "Failed to obtain SSL certificates"

**Causes:**
- Domain DNS not propagated yet
- Ports 80/443 blocked by firewall
- Another service using port 80

**Fix:**
```bash
# Check DNS
dig +short rentflow.cloud A

# Check if port 80 is accessible
curl -I http://rentflow.cloud

# Check firewall
sudo ufw status

# Stop any conflicting services
sudo systemctl stop apache2  # if Apache is running
```

### Issue: "Certificate about to expire" warnings

**Fix:**
```bash
# Check certbot container is running
docker ps | grep certbot

# If not running, restart services
docker compose -f deployment/docker/docker-compose.yml --env-file .env up -d

# Manually renew
docker compose -f deployment/docker/docker-compose.yml --env-file .env \
  exec certbot certbot renew --force-renewal
```

### Issue: "NGINX won't start after SSL setup"

**Fix:**
```bash
# Check NGINX configuration
docker compose -f deployment/docker/docker-compose.yml --env-file .env \
  exec nginx nginx -t

# View NGINX logs
docker compose -f deployment/docker/docker-compose.yml --env-file .env \
  logs nginx
```

## Certificate Locations

Certificates are stored in Docker volumes:

- **Certificates:** `/etc/letsencrypt/live/rentflow.cloud/`
  - `fullchain.pem` - Full certificate chain
  - `privkey.pem` - Private key
  - `chain.pem` - Certificate authority chain

- **ACME challenges:** `/var/www/certbot/`

- **Renewal config:** `/etc/letsencrypt/renewal/`

## Production Checklist

After SSL setup:

- [ ] Verify HTTPS works: https://rentflow.cloud
- [ ] Check certificate validity (green padlock in browser)
- [ ] Test automatic redirect HTTP → HTTPS
- [ ] Verify certbot container is running
- [ ] Test certificate renewal: `certbot renew --dry-run`
- [ ] Update application URLs to use `https://`
- [ ] Configure SESSION_COOKIE_SECURE in `.env`

## Security Best Practices

✅ **Implemented:**
- TLS 1.2 and 1.3 only
- Strong cipher suites
- HSTS (HTTP Strict Transport Security)
- 2048-bit DH parameters
- Automatic certificate renewal

✅ **Recommended:**
- Monitor certificate expiration
- Keep certbot container running
- Check logs periodically
- Backup certificates (optional - can regenerate)

## Support

If you encounter issues:

1. Check logs: `docker compose -f deployment/docker/docker-compose.yml logs certbot`
2. Verify DNS: `dig +short rentflow.cloud`
3. Test connectivity: `curl -I http://rentflow.cloud`
4. Check firewall: `sudo ufw status`

For Let's Encrypt rate limits and documentation:
- https://letsencrypt.org/docs/rate-limits/
- https://certbot.eff.org/docs/
