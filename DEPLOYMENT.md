# RentFlow Production Deployment Guide

This guide covers deploying RentFlow to a production Ubuntu server using Docker, NGINX, and PostgreSQL with full CI/CD via GitHub Actions.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Server Setup](#server-setup)
3. [Initial Deployment](#initial-deployment)
4. [CI/CD Setup](#cicd-setup)
5. [Database Management](#database-management)
6. [Monitoring & Maintenance](#monitoring--maintenance)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Server Requirements
- Ubuntu 20.04 LTS or higher
- Minimum 2GB RAM
- 20GB disk space
- Root or sudo access
- Domain name pointed to server IP

### Local Requirements
- Git installed
- SSH access to server
- GitHub account with repository access

---

## Server Setup

### 1. Install Docker

```bash
# Update package list
sudo apt update && sudo apt upgrade -y

# Install dependencies
sudo apt install -y apt-transport-https ca-certificates curl software-properties-common

# Add Docker GPG key
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

# Add Docker repository
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin

# Add ubuntu user to docker group
sudo usermod -aG docker ubuntu

# Logout and login again for group changes to take effect
```

### 2. Install Docker Compose

```bash
# Install Docker Compose v2
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Verify installation
docker --version
docker-compose --version
```

### 3. Configure Firewall

```bash
# Allow SSH
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable
sudo ufw status
```

### 4. Setup SSL Certificates

Option A: Using Let's Encrypt (Recommended)

```bash
# Install Certbot
sudo apt install -y certbot python3-certbot-nginx

# Generate certificate
sudo certbot certonly --standalone -d your-domain.com -d www.your-domain.com

# Certificates will be in /etc/letsencrypt/live/your-domain.com/
```

Option B: Self-signed (Development Only)

```bash
# Generate self-signed certificate
sudo mkdir -p /home/ubuntu/rentflow/ssl
sudo openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
  -keyout /home/ubuntu/rentflow/ssl/key.pem \
  -out /home/ubuntu/rentflow/ssl/cert.pem
```

---

## Initial Deployment

### 1. Clone Repository

```bash
# Navigate to home directory
cd /home/ubuntu

# Clone repository
git clone https://github.com/kyle-carriveau/rentflow.git
cd rentflow
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit environment file
nano .env
```

**Required Environment Variables:**

```bash
# Flask Configuration
SECRET_KEY=your-super-secret-key-generate-with-openssl-rand-hex-32
FLASK_ENV=production
DEBUG=False

# Database Configuration
DATABASE_URL=postgresql://rentflow_user:your_secure_password@db:5432/rentflow
POSTGRES_DB=rentflow
POSTGRES_USER=rentflow_user
POSTGRES_PASSWORD=your_secure_password

# Security
SESSION_COOKIE_SECURE=True

# Rate Limiting
RATELIMIT_STORAGE_URL=redis://redis:6379/0
```

**Generate Secure SECRET_KEY:**

```bash
python3 -c 'import secrets; print(secrets.token_hex(32))'
```

### 3. Update NGINX Configuration

```bash
# Edit NGINX site configuration
nano nginx/conf.d/rentflow.conf

# Replace 'your-domain.com' with your actual domain
# Update SSL certificate paths if using Let's Encrypt:
# ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
# ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
```

### 4. Deploy Application

```bash
# Run deployment script
./deploy.sh
```

The script will:
- Build Docker images
- Run database migrations
- Start all services (PostgreSQL, Redis, Flask, NGINX)
- Verify deployment health

### 5. Verify Deployment

```bash
# Check running containers
docker-compose ps

# View logs
docker-compose logs -f web

# Test health endpoint
curl http://localhost:8000/health

# Test via NGINX
curl http://localhost
```

---

## CI/CD Setup

### 1. Configure GitHub Secrets

Go to your GitHub repository → Settings → Secrets and variables → Actions

Add the following secrets:

- `VPS_HOST`: Your server IP address or domain
- `VPS_USERNAME`: SSH username (usually `ubuntu`)
- `VPS_SSH_KEY`: Private SSH key for server access
- `VPS_PORT`: SSH port (default: 22)

**Generate SSH Key (if needed):**

```bash
# On your local machine
ssh-keygen -t ed25519 -C "github-actions-deploy" -f ~/.ssh/rentflow_deploy

# Copy public key to server
ssh-copy-id -i ~/.ssh/rentflow_deploy.pub ubuntu@your-server-ip

# Copy private key content for GitHub secret
cat ~/.ssh/rentflow_deploy
```

### 2. Enable GitHub Actions

The workflow is already configured in `.github/workflows/deploy.yml`

**Workflow Trigger:**
- Automatically on push to `main` branch
- Manually via GitHub Actions tab

**What it does:**
1. Runs tests
2. SSH to server
3. Pull latest code
4. Backup database
5. Build Docker images
6. Run migrations
7. Restart services
8. Verify health

### 3. Test Deployment

```bash
# Make a change and commit
git add .
git commit -m "Test deployment"
git push origin main

# Watch deployment in GitHub Actions tab
```

---

## Database Management

### Running Migrations

```bash
# On server
cd /home/ubuntu/rentflow

# Create new migration
docker-compose run --rm web flask db migrate -m "Description of changes"

# Apply migrations
docker-compose run --rm web flask db upgrade

# Revert last migration
docker-compose run --rm web flask db downgrade
```

### Backup Database

```bash
# Manual backup
docker-compose exec db pg_dump -U rentflow_user rentflow > backup_$(date +%Y%m%d).sql

# Automated daily backups (add to crontab)
crontab -e

# Add line:
0 2 * * * cd /home/ubuntu/rentflow && docker-compose exec -T db pg_dump -U rentflow_user rentflow > backups/backup_$(date +\%Y\%m\%d).sql
```

### Restore Database

```bash
# Stop application
docker-compose down

# Restore backup
cat backup_20241015.sql | docker-compose exec -T db psql -U rentflow_user rentflow

# Start application
docker-compose up -d
```

---

## Monitoring & Maintenance

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f web
docker-compose logs -f nginx
docker-compose logs -f db

# Last 100 lines
docker-compose logs --tail=100 web
```

### Check Resource Usage

```bash
# Container stats
docker stats

# Disk usage
df -h
docker system df

# Database size
docker-compose exec db psql -U rentflow_user rentflow -c "SELECT pg_size_pretty(pg_database_size('rentflow'));"
```

### Restart Services

```bash
# Restart all services
docker-compose restart

# Restart specific service
docker-compose restart web
docker-compose restart nginx

# Full restart (rebuild)
docker-compose down && docker-compose up -d --build
```

### Update Application

```bash
# Pull latest code
cd /home/ubuntu/rentflow
git pull origin main

# Rebuild and restart
./deploy.sh
```

### Clean Up

```bash
# Remove unused Docker resources
docker system prune -a --volumes

# Remove old log files
find logs/ -name "*.log" -mtime +30 -delete
```

---

## Troubleshooting

### Application Won't Start

```bash
# Check logs
docker-compose logs web

# Check environment variables
docker-compose exec web env

# Verify database connection
docker-compose exec web python -c "from website import create_app, db; app = create_app(); app.app_context().push(); print('DB connection:', db.engine.url)"
```

### Database Connection Issues

```bash
# Check if database is running
docker-compose ps db

# Check database logs
docker-compose logs db

# Test connection
docker-compose exec db psql -U rentflow_user -d rentflow -c "SELECT version();"
```

### NGINX Issues

```bash
# Check NGINX configuration
docker-compose exec nginx nginx -t

# Check NGINX logs
docker-compose logs nginx

# Restart NGINX
docker-compose restart nginx
```

### SSL Certificate Issues

```bash
# Check certificate expiry
echo | openssl s_client -servername your-domain.com -connect your-domain.com:443 2>/dev/null | openssl x509 -noout -dates

# Renew Let's Encrypt certificate
sudo certbot renew

# Restart NGINX after renewal
docker-compose restart nginx
```

### Performance Issues

```bash
# Check resource usage
docker stats

# Scale web workers (in docker-compose.yml)
# Change GUNICORN_WORKERS in .env

# Restart with new configuration
docker-compose up -d --scale web=2
```

### Migration Issues

```bash
# Check migration status
docker-compose exec web flask db current

# View migration history
docker-compose exec web flask db history

# Fix migration conflicts
docker-compose exec web flask db stamp head
```

---

## Security Best Practices

1. **Keep secrets secure**: Never commit `.env` file
2. **Regular updates**: Update Docker images monthly
3. **Monitor logs**: Set up log monitoring (e.g., ELK stack)
4. **Backup regularly**: Automate daily database backups
5. **SSL certificates**: Renew certificates before expiry
6. **Firewall**: Only open necessary ports
7. **User permissions**: Run containers as non-root user
8. **Rate limiting**: Configure NGINX rate limits appropriately

---

## Useful Commands Reference

```bash
# View all containers
docker-compose ps

# Stop all services
docker-compose down

# Start services
docker-compose up -d

# Rebuild and start
docker-compose up -d --build

# View logs
docker-compose logs -f

# Execute command in container
docker-compose exec web flask shell

# Database shell
docker-compose exec db psql -U rentflow_user rentflow

# Clean up everything
docker-compose down -v
docker system prune -a --volumes -f
```

---

## Support

For issues or questions:
- GitHub Issues: https://github.com/kyle-carriveau/rentflow/issues
- Documentation: [README.md](README.md)
