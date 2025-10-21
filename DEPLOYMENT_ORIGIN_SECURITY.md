# Origin Security Deployment Guide

This guide implements production-grade security to prevent direct IP access and ensure all traffic comes through Cloudflare.

---

## Security Measures Implemented

✅ **HTTPS Default Server Block** - Blocks direct IP access on port 443
✅ **Authenticated Origin Pulls** - Verifies all HTTPS traffic comes from Cloudflare
✅ **HTTP Default Server Block** - Blocks direct IP access on port 80 (already implemented)

---

## Deployment Steps

### Step 1: Push Code Changes to Repository

On your **local machine**:

```bash
cd /Users/kylecarriveau/Development/re2

# Review changes
git status
git diff deployment/nginx/conf.d/rentflow.conf

# Commit changes
git add deployment/nginx/conf.d/rentflow.conf
git add deployment/ssl/cloudflare-origin-pull-ca.pem
git commit -m "Add production security: block direct IP access and enable Authenticated Origin Pulls"

# Push to GitHub
git push origin main
```

---

### Step 2: Deploy to VPS

SSH to your VPS:

```bash
ssh root@93.127.197.136
cd /home/ubuntu/rentflow
```

Pull latest changes:

```bash
git pull origin main
```

Verify the new certificate file exists:

```bash
ls -l deployment/ssl/
# Should show: cloudflare-origin.crt, cloudflare-origin.key, cloudflare-origin-pull-ca.pem
```

Test NGINX configuration:

```bash
docker compose -f deployment/docker/docker-compose.yml exec nginx nginx -t
```

If services are not running yet, start them:

```bash
docker compose -f deployment/docker/docker-compose.yml --env-file .env up -d
```

Otherwise, reload NGINX:

```bash
docker compose -f deployment/docker/docker-compose.yml exec nginx nginx -s reload
```

---

### Step 3: Enable Authenticated Origin Pulls in Cloudflare

1. Log in to [Cloudflare Dashboard](https://dash.cloudflare.com)
2. Select your domain: `rentflow.cloud`
3. Go to **SSL/TLS** → **Origin Server**
4. Scroll down to **Authenticated Origin Pulls**
5. Toggle **ON** the switch for "Authenticated Origin Pulls"

**Important**: This must be enabled in Cloudflare for the security to work. Without this, NGINX will reject all connections (even from Cloudflare).

---

### Step 4: Verify Security is Working

#### Test 1: Direct IP Access Should Be Blocked

**HTTP (port 80):**
```bash
curl -v http://93.127.197.136
# Expected: Connection closed (no response)
```

**HTTPS (port 443):**
```bash
curl -v -k https://93.127.197.136
# Expected: Connection closed (no response)
```

#### Test 2: Domain Access Should Work

**HTTPS via domain:**
```bash
curl -v https://rentflow.cloud
# Expected: 200 OK response with application content
```

#### Test 3: Verify Authenticated Origin Pulls

Check NGINX logs to confirm client certificate verification:

```bash
docker compose -f deployment/docker/docker-compose.yml logs nginx | grep -i "ssl"
```

You should NOT see any SSL verification errors for legitimate traffic.

---

## How It Works

### Before (Vulnerable)

```
User → https://93.127.197.136 → NGINX → Application ❌ (Direct access works)
User → Cloudflare → https://rentflow.cloud → NGINX → Application ✅
Attacker → Direct to origin → NGINX → Application ❌ (Bypasses Cloudflare security)
```

### After (Secure)

```
User → https://93.127.197.136 → NGINX default_server → 444 Blocked ✅
User → Cloudflare → https://rentflow.cloud → NGINX (verifies CF cert) → Application ✅
Attacker → Direct to origin → NGINX → No client cert → 400 Bad Request ✅
```

---

## Security Layers Explained

### Layer 1: HTTP Default Server (Port 80)
- Blocks direct IP access via HTTP
- Returns HTTP 444 (connection closed)
- Already implemented

### Layer 2: HTTPS Default Server (Port 443) **NEW**
- Blocks direct IP access via HTTPS
- Returns HTTP 444 (connection closed)
- Prevents access to `https://93.127.197.136`

### Layer 3: Authenticated Origin Pulls **NEW**
- NGINX requires Cloudflare's client certificate for HTTPS connections
- Only Cloudflare can present this certificate
- Blocks all non-Cloudflare traffic (even if they know your origin IP)

---

## Troubleshooting

### Issue: Site returns "400 Bad Request" after deployment

**Cause:** Authenticated Origin Pulls not enabled in Cloudflare dashboard

**Fix:**
1. Go to Cloudflare Dashboard → SSL/TLS → Origin Server
2. Enable "Authenticated Origin Pulls"
3. Wait 1-2 minutes for changes to propagate
4. Refresh browser

---

### Issue: Direct IP access still works

**Cause:** NGINX configuration not reloaded

**Fix:**
```bash
docker compose -f deployment/docker/docker-compose.yml exec nginx nginx -s reload
```

Or restart the entire stack:
```bash
docker compose -f deployment/docker/docker-compose.yml restart nginx
```

---

### Issue: Certificate verification failed

**Cause:** Cloudflare Origin Pull CA certificate not found

**Fix:**
```bash
# Verify file exists in container
docker compose -f deployment/docker/docker-compose.yml exec nginx ls -l /etc/nginx/ssl/
# Should show: cloudflare-origin-pull-ca.pem

# If missing, verify it's in your repo
ls -l deployment/ssl/cloudflare-origin-pull-ca.pem

# Restart NGINX to mount the volume
docker compose -f deployment/docker/docker-compose.yml restart nginx
```

---

## Maintenance

### Cloudflare Origin Pull Certificate Expiration

The Cloudflare Origin Pull CA certificate expires **November 1, 2029**.

**Action required before expiration:**
1. Download new certificate from Cloudflare
2. Update `deployment/ssl/cloudflare-origin-pull-ca.pem`
3. Deploy to production
4. Reload NGINX

**Mark your calendar:** Set a reminder for **October 2029** to renew.

---

## Verification Checklist

After deployment, verify:

- [ ] Direct IP HTTP access blocked: `curl http://93.127.197.136` returns nothing
- [ ] Direct IP HTTPS access blocked: `curl -k https://93.127.197.136` returns nothing
- [ ] Domain HTTPS access works: `curl https://rentflow.cloud` returns 200 OK
- [ ] Green padlock in browser when visiting https://rentflow.cloud
- [ ] Authenticated Origin Pulls enabled in Cloudflare dashboard
- [ ] No SSL errors in NGINX logs

---

## Security Benefits

✅ **Prevents DDoS bypass** - Attackers can't bypass Cloudflare's DDoS protection
✅ **Prevents WAF bypass** - Attackers can't bypass Cloudflare's Web Application Firewall
✅ **Prevents rate limit bypass** - Attackers can't bypass Cloudflare's rate limiting
✅ **Hides origin IP** - Even if discovered, origin IP is not accessible
✅ **Enterprise-grade security** - Uses mTLS authentication (mutual TLS)

---

## Summary

Your application is now protected with **enterprise-grade origin security**:

1. **Direct IP access blocked** on both HTTP and HTTPS
2. **Authenticated Origin Pulls** ensures only Cloudflare can connect
3. **Zero maintenance** after initial setup (certificate valid until 2029)

All traffic MUST go through Cloudflare, which provides:
- DDoS protection
- Web Application Firewall
- Rate limiting
- SSL/TLS termination
- Global CDN caching

Your origin server is now invisible to the internet. 🔒
