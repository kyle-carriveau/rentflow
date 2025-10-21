# Production SSL/HTTPS Setup Guide

**Domain:** `rentflow.cloud`
**SSL Provider:** Let's Encrypt (Free, Automated, Trusted)

This guide explains the production-ready SSL setup for RentFlow.

---

## Overview

The SSL setup is **fully automated** after initial configuration. Here's how it works:

### First Deployment (One-Time Setup)
1. Deploy application via GitHub Actions or manual deployment
2. SSL init script automatically runs
3. Obtains Let's Encrypt certificates
4. HTTPS enabled automatically

### Ongoing Operation
- Certificates auto-renew every 90 days (handled by certbot container)
- Zero manual intervention required
- Deployments work seamlessly with existing certificates

---

## Automated Setup (Recommended)

### Method 1: GitHub Actions (Fully Automated)

**Just push to main** - SSL setup happens automatically:

```bash
git push origin main
```

GitHub Actions will:
1. ✅ Deploy the application
2. ✅ Check if SSL certificates exist
3. ✅ If not, run SSL initialization automatically
4. ✅ Enable HTTPS

**No manual steps required!**

### Method 2: Manual Trigger on VPS

If deploying manually or want to trigger SSL setup:

```bash
# SSH to VPS
ssh root@93.127.197.136

# Navigate to app directory
cd /home/ubuntu/rentflow

# Run SSL initialization (safe to run multiple times)
./deployment/scripts/init-ssl.sh
```

The script is **idempotent** - safe to run multiple times, skips setup if certificates already exist.

---

## What The Script Does

1. **Checks Prerequisites**
   - Validates DNS points to server
   - Checks Docker is installed
   - Verifies domain resolves correctly

2. **Checks Existing Certificates**
   - If certificates exist → validates and exits
   - If not → proceeds with setup

3. **Creates Infrastructure**
   - Generates DH parameters for strong encryption
   - Creates temporary dummy certificates (so NGINX can start)

4. **Obtains Real Certificates**
   - Starts required services (DB, Redis, Web, NGINX)
   - Requests Let's Encrypt certificates
   - Replaces dummy certificates with real ones
   - Reloads NGINX

5. **Verifies Setup**
   - Confirms HTTPS is working
   - Displays success message

**Total time:** 3-5 minutes (mostly DH parameter generation)

---

## Configuration

### Update Email Address (Recommended)

Edit `deployment/scripts/init-ssl.sh`:

```bash
EMAIL="admin@rentflow.cloud"  # Change to your actual email
```

This email receives expiration warnings (though auto-renewal should prevent expiration).

### Testing Mode (Staging Certificates)

To test without hitting rate limits:

```bash
# Edit script
nano deployment/scripts/init-ssl.sh

# Change line
STAGING=0  # to  STAGING=1

# Run script
./deployment/scripts/init-ssl.sh
```

Staging certificates won't be trusted by browsers but let you test the process.

---

## Automatic Renewal

Certificates are **automatically renewed** by the certbot container.

- **Renewal Frequency:** Checked every 12 hours
- **Certificate Lifetime:** 90 days
- **Renewal Trigger:** 30 days before expiration
- **No manual action required**

### Check Renewal Status

```bash
# View certbot container logs
docker compose -f deployment/docker/docker-compose.yml --env-file .env logs certbot

# Test renewal process (dry run)
docker compose -f deployment/docker/docker-compose.yml --env-file .env \
  run --rm certbot renew --dry-run
```

---

## Troubleshooting

### Issue: "DNS resolution failed"

**Cause:** Domain doesn't point to VPS IP

**Fix:**
```bash
# Check DNS
dig +short rentflow.cloud

# Should return: 93.127.197.136
```

Update DNS A record if incorrect.

### Issue: "Failed to obtain SSL certificates"

**Causes:**
- Ports 80/443 not open in firewall
- Another service using port 80
- Domain not propagated yet

**Fix:**
```bash
# Check ports
sudo ufw status
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Check what's using port 80
sudo netstat -tlnp | grep :80

# Wait for DNS propagation (up to 48 hours)
```

### Issue: "Certificates already exist" but HTTPS not working

**Cause:** NGINX not reloaded with new certificates

**Fix:**
```bash
# Reload NGINX
docker compose -f deployment/docker/docker-compose.yml --env-file .env \
  exec nginx nginx -s reload

# Or restart all services
docker compose -f deployment/docker/docker-compose.yml --env-file .env restart
```

### Issue: Certificate expired

**Cause:** Certbot renewal container not running

**Fix:**
```bash
# Check certbot container status
docker ps | grep certbot

# Restart services to start certbot
docker compose -f deployment/docker/docker-compose.yml --env-file .env up -d

# Force renewal
docker compose -f deployment/docker/docker-compose.yml --env-file .env \
  run --rm certbot renew --force-renewal
```

---

## Production Checklist

After SSL setup:

- [ ] Visit https://rentflow.cloud - verify green padlock
- [ ] Visit https://www.rentflow.cloud - verify works
- [ ] Check certificate details in browser - verify Let's Encrypt issued
- [ ] Verify HTTP redirects to HTTPS
- [ ] Check certbot container is running: `docker ps | grep certbot`
- [ ] Test renewal: `certbot renew --dry-run`

---

## Security Features

✅ **TLS 1.2 and 1.3 only** - No old protocols
✅ **Strong cipher suites** - A+ SSL Labs rating
✅ **HSTS enabled** - Prevents downgrade attacks
✅ **2048-bit DH parameters** - Perfect forward secrecy
✅ **Automatic renewal** - No expired certificates
✅ **Rate limiting** - Protection from attacks
✅ **Security headers** - XSS, clickjacking protection

---

## Advanced Operations

### Remove Certificates (Fresh Start)

```bash
# Delete certificates
docker compose -f deployment/docker/docker-compose.yml --env-file .env \
  run --rm certbot delete --cert-name rentflow.cloud

# Run init script again
./deployment/scripts/init-ssl.sh
```

### Switch from Staging to Production

```bash
# Remove staging certificates
docker compose -f deployment/docker/docker-compose.yml --env-file .env \
  run --rm certbot delete --cert-name rentflow.cloud

# Edit script to use production mode
nano deployment/scripts/init-ssl.sh
# Set: STAGING=0

# Get production certificates
./deployment/scripts/init-ssl.sh
```

### Manual Certificate Renewal

```bash
# Force renewal (not normally needed)
docker compose -f deployment/docker/docker-compose.yml --env-file .env \
  run --rm certbot renew --force-renewal

# Reload NGINX
docker compose -f deployment/docker/docker-compose.yml --env-file .env \
  exec nginx nginx -s reload
```

---

## Files & Locations

**Certificates stored in Docker volume:**
- `certbot_certs` volume → `/etc/letsencrypt/`
- Certificates: `/etc/letsencrypt/live/rentflow.cloud/`

**Scripts:**
- `deployment/scripts/init-ssl.sh` - SSL initialization
- `deployment/scripts/validate.sh` - Pre-deployment validation

**Configuration:**
- `deployment/nginx/conf.d/rentflow.conf` - NGINX SSL config
- `deployment/docker/docker-compose.yml` - Certbot service definition

---

## Support

**Certificate not working after setup?**
1. Check logs: `docker compose logs nginx certbot`
2. Verify DNS: `dig +short rentflow.cloud`
3. Test HTTPS: `curl -I https://rentflow.cloud`
4. Check firewall: `sudo ufw status`

**Need help?**
- Let's Encrypt docs: https://letsencrypt.org/docs/
- Certbot docs: https://eff-certbot.readthedocs.io/
- Check GitHub Actions logs for deployment issues

---

## Summary

✅ **One-time setup:** Automated via GitHub Actions or manual script
✅ **Zero maintenance:** Automatic renewal every 90 days
✅ **Production-ready:** Trusted certificates, A+ security rating
✅ **Fully automated:** No manual intervention after initial setup

Your application is secured with production-grade HTTPS that requires zero ongoing maintenance.
