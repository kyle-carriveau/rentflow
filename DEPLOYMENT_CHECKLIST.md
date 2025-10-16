# RentFlow Deployment Checklist

Use this checklist to ensure a smooth deployment to production.

## Pre-Deployment Checklist

### Server Preparation
- [ ] Ubuntu 20.04+ server provisioned
- [ ] Domain name configured and pointing to server IP
- [ ] SSH access configured
- [ ] Firewall rules configured (ports 22, 80, 443)
- [ ] Docker installed
- [ ] Docker Compose installed

### SSL Certificates
- [ ] SSL certificates obtained (Let's Encrypt or other)
- [ ] Certificates placed in correct location
- [ ] Certificate paths updated in NGINX config

### Application Configuration
- [ ] Repository cloned to `/home/ubuntu/rentflow`
- [ ] `.env` file created from `.env.example`
- [ ] `SECRET_KEY` generated and set
- [ ] Database credentials configured
- [ ] Domain name updated in NGINX config
- [ ] Email settings configured (if using email features)

---

## Initial Deployment

### Step 1: Environment Setup
```bash
cd /home/ubuntu/rentflow
cp .env.example .env
nano .env  # Edit with actual values
```

- [ ] SECRET_KEY set
- [ ] DATABASE_URL configured
- [ ] POSTGRES credentials set
- [ ] SESSION_COOKIE_SECURE=True
- [ ] DEBUG=False
- [ ] FLASK_ENV=production

### Step 2: Database Setup
```bash
# Migrations will run automatically with deploy script
```

- [ ] Database migrations ready
- [ ] Initial migration created

### Step 3: Deploy
```bash
chmod +x deploy.sh
./deploy.sh
```

- [ ] Docker images built successfully
- [ ] Database migrations applied
- [ ] All containers started
- [ ] Health check passes

### Step 4: Verify
```bash
# Check services
docker-compose ps

# Test health endpoint
curl http://localhost:8000/health

# Test via NGINX
curl http://localhost
curl https://your-domain.com
```

- [ ] All containers running
- [ ] Health endpoint responds
- [ ] Application accessible via domain
- [ ] HTTPS working correctly

---

## CI/CD Setup

### GitHub Secrets Configuration
Go to: Repository Settings → Secrets and variables → Actions

- [ ] `VPS_HOST` - Server IP or domain
- [ ] `VPS_USERNAME` - SSH username (usually 'ubuntu')
- [ ] `VPS_SSH_KEY` - Private SSH key content
- [ ] `VPS_PORT` - SSH port (default: 22)

### SSH Key Setup
```bash
# On local machine
ssh-keygen -t ed25519 -C "github-actions" -f ~/.ssh/rentflow_deploy
ssh-copy-id -i ~/.ssh/rentflow_deploy.pub ubuntu@your-server-ip
```

- [ ] SSH key pair generated
- [ ] Public key added to server
- [ ] Private key added to GitHub secrets
- [ ] SSH connection tested

### Test Workflow
```bash
# Make a test commit
git add .
git commit -m "Test deployment"
git push origin main
```

- [ ] GitHub Actions workflow triggers
- [ ] Tests pass
- [ ] Deployment completes
- [ ] Application restarts successfully

---

## Post-Deployment

### Security
- [ ] Change default passwords
- [ ] Review firewall rules
- [ ] Enable automatic security updates
- [ ] Set up SSL certificate auto-renewal
- [ ] Review NGINX security headers

### Monitoring
- [ ] Set up log rotation
- [ ] Configure backup schedule
- [ ] Test backup restoration process
- [ ] Set up monitoring (optional: ELK, Prometheus)
- [ ] Configure alerting (optional)

### Backup Schedule
```bash
# Add to crontab
crontab -e

# Daily database backup at 2 AM
0 2 * * * cd /home/ubuntu/rentflow && docker-compose exec -T db pg_dump -U rentflow_user rentflow > backups/backup_$(date +\%Y\%m\%d).sql
```

- [ ] Backup directory created
- [ ] Automated backup scheduled
- [ ] Backup restoration tested

### Performance
- [ ] Database indexes optimized
- [ ] Static files cached properly
- [ ] Gzip compression enabled
- [ ] Resource limits set appropriately
- [ ] Load testing completed (optional)

---

## Maintenance Checklist

### Weekly
- [ ] Review application logs
- [ ] Check disk space
- [ ] Review error reports
- [ ] Check SSL certificate expiry

### Monthly
- [ ] Update Docker images
- [ ] Review and rotate logs
- [ ] Test backup restoration
- [ ] Review database performance
- [ ] Update dependencies (if needed)

### Quarterly
- [ ] Security audit
- [ ] Performance review
- [ ] Capacity planning review
- [ ] Update documentation

---

## Emergency Procedures

### Application Down
```bash
# Check status
docker-compose ps

# View logs
docker-compose logs --tail=100 web

# Restart services
docker-compose restart

# Full restart if needed
docker-compose down && docker-compose up -d
```

### Database Issues
```bash
# Check database status
docker-compose exec db pg_isready -U rentflow_user

# View database logs
docker-compose logs db

# Restore from backup
cat backups/backup_YYYYMMDD.sql | docker-compose exec -T db psql -U rentflow_user rentflow
```

### Rollback Deployment
```bash
# Revert to previous git commit
git log --oneline  # Find commit hash
git reset --hard <commit-hash>

# Redeploy
./deploy.sh
```

---

## Quick Reference Commands

```bash
# View logs
docker-compose logs -f web

# Restart application
docker-compose restart web

# Run migrations
docker-compose run --rm web flask db upgrade

# Database shell
docker-compose exec db psql -U rentflow_user rentflow

# Application shell
docker-compose exec web flask shell

# Stop all services
docker-compose down

# Start all services
docker-compose up -d

# Full rebuild
docker-compose down && docker-compose up -d --build
```

---

## Troubleshooting

### Container won't start
- Check logs: `docker-compose logs <service>`
- Verify `.env` file configuration
- Check disk space: `df -h`
- Verify port availability: `sudo netstat -tlnp`

### Database connection error
- Verify database is running: `docker-compose ps db`
- Check credentials in `.env`
- Test connection: `docker-compose exec db psql -U rentflow_user rentflow -c "SELECT 1;"`

### NGINX error
- Test config: `docker-compose exec nginx nginx -t`
- Check logs: `docker-compose logs nginx`
- Verify SSL certificates exist
- Check file permissions

---

## Support Resources

- **Full Documentation**: [DEPLOYMENT.md](DEPLOYMENT.md)
- **Application README**: [README.md](README.md)
- **GitHub Issues**: https://github.com/kyle-carriveau/rentflow/issues
