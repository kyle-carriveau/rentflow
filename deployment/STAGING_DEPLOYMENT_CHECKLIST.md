# Staging Deployment Checklist

This checklist should be completed before deploying staging to VPS.

## ✅ Local Validation (Completed)

- [x] Docker Compose staging file syntax is valid
- [x] NGINX staging configuration created
- [x] SSL certificates generated (self-signed)
- [x] Environment template exists (.env.staging.example)
- [x] Build context paths corrected
- [x] Volume paths use relative paths (not ../..)

## 🔧 VPS Pre-Deployment Steps

Before running staging deployment on VPS, complete these steps:

### 1. Create Staging Environment File

```bash
# On VPS
cd /home/ubuntu/rentflow
cp .env.staging.example .env.staging

# Edit with staging-specific values
nano .env.staging
```

**Required variables**:
- `SECRET_KEY` - Generate unique key: `openssl rand -hex 32`
- `POSTGRES_PASSWORD` - Strong password (different from production!)
- `POSTGRES_DB=rentflow_staging`
- `POSTGRES_USER=rentflow_staging`

### 2. Create Staging Data Directories

```bash
# On VPS
cd /home/ubuntu/rentflow
mkdir -p instance-staging logs-staging uploads-staging backups
chmod 777 instance-staging logs-staging uploads-staging
mkdir -p logs-staging/nginx
```

### 3. Verify Docker Network Isolation

```bash
# Ensure staging and production use different networks
docker network ls | grep rentflow

# Should see:
# rentflow_network (production)
# rentflow_staging_network (staging)
```

### 4. Test Staging Deployment

```bash
# Build images
docker compose -f docker-compose.staging.yml --env-file .env.staging build

# Start services
docker compose -f docker-compose.staging.yml --env-file .env.staging up -d

# Check service health
docker compose -f docker-compose.staging.yml --env-file .env.staging ps

# View logs
docker compose -f docker-compose.staging.yml --env-file .env.staging logs -f web

# Test health endpoint
curl http://localhost:9000/health

# Test NGINX
curl http://localhost:8080/health
```

## 🔍 Validation Tests

After deployment, verify these work:

### Service Health
- [ ] PostgreSQL container is healthy
- [ ] Redis container is healthy
- [ ] Flask web container is healthy
- [ ] NGINX container is healthy

### Network Connectivity
- [ ] Web can connect to database
- [ ] Web can connect to Redis
- [ ] NGINX can proxy to web
- [ ] External HTTP access works (port 8080)
- [ ] External HTTPS access works (port 8443, with SSL warning expected)

### Application Functionality
- [ ] `/health` endpoint returns 200 OK
- [ ] Homepage loads
- [ ] Can create user account
- [ ] Can log in
- [ ] Database migrations applied successfully

### Environment Isolation
- [ ] Staging uses separate database (`rentflow_staging`)
- [ ] Staging uses separate volumes
- [ ] Staging does NOT interfere with production
- [ ] Production still accessible on ports 80/443

## 🚨 Troubleshooting

### Issue: "Cannot start service nginx: driver failed"
**Solution**: Check SSL certificate paths exist:
```bash
ls -la deployment/ssl-staging/staging.crt deployment/ssl-staging/staging.key
```

### Issue: "Error: No such file or directory: .env.staging"
**Solution**: Create .env.staging from template:
```bash
cp .env.staging.example .env.staging
```

### Issue: Port already in use (8080, 8443, 9000)
**Solution**: Check what's using the port:
```bash
lsof -i :8080
lsof -i :8443
lsof -i :9000
```

### Issue: Database migration fails
**Solution**: Check database connectivity:
```bash
docker compose -f docker-compose.staging.yml exec db psql -U rentflow_staging -d rentflow_staging -c "SELECT 1;"
```

## 📋 Next Steps After Successful Deployment

1. **Configure GitHub Actions Secrets** (if not already done)
   - Ensure VPS_HOST, VPS_USERNAME, VPS_SSH_KEY, VPS_PORT are set

2. **Test Auto-Deployment**
   - Push to `develop` branch
   - Verify GitHub Actions triggers deployment
   - Check staging environment updates

3. **Set Up Monitoring**
   - Monitor staging logs
   - Set up alerts for failures (optional)

4. **Document Staging URL**
   - Update team documentation with staging access URL
   - Share staging credentials with QA team

## ⚠️ Important Notes

- **SSL Warning Expected**: Self-signed certificates will show browser warnings - this is normal
- **Different Credentials**: Never use production credentials in staging
- **Data Isolation**: Staging and production must remain completely isolated
- **Resource Usage**: Monitor VPS resources - running both environments requires adequate RAM/CPU
