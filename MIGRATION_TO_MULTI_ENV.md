# Migration to Multi-Environment Setup

**From**: Single production environment
**To**: Local → Staging → Production pipeline
**Goal**: Add lower environments without disrupting production

---

## 📋 Overview

You currently have:
- ✅ Production environment running on VPS
- ✅ Code on `main` branch

You need to add:
- 🎯 Local development environments (for all developers)
- 🎯 Staging environment (on same VPS as production)
- 🎯 CI/CD automation via GitHub Actions

---

## 🚨 Safety First

**CRITICAL**: We will NOT touch your running production environment until staging is validated.

**Migration Strategy**:
1. Set up `develop` branch (already done ✅)
2. Configure GitHub repository and secrets
3. Set up staging environment on VPS (non-disruptive)
4. Test staging thoroughly
5. Roll out to developers
6. Validate CI/CD pipeline
7. Optionally update production to new structure (backwards compatible)

---

## Phase 1: GitHub Repository Configuration

### Step 1.1: Create and Push Develop Branch

```bash
# On your local machine
cd /path/to/rentflow

# Ensure you're on main and up-to-date
git checkout main
git pull origin main

# Create develop branch from main (if not already done)
git checkout -b develop
git push origin develop
```

✅ **Status**: This is already done based on git history.

### Step 1.2: Set Default Branch to Develop

**In GitHub Web Interface:**

1. Go to: `Settings` → `Branches`
2. Under "Default branch", click the switch icon
3. Select `develop`
4. Click "Update" and confirm

**Why**: New PRs and clones will default to `develop` instead of `main`.

### Step 1.3: Configure GitHub Secrets

**Path**: `Settings` → `Secrets and variables` → `Actions`

Add these repository secrets:

#### Production VPS Access (Required)

| Secret Name | Value | Where to Get It |
|-------------|-------|-----------------|
| `VPS_HOST` | Your VPS IP address | `123.45.67.89` (your Hostinger VPS IP) |
| `VPS_USERNAME` | SSH username | Usually `ubuntu` or `root` |
| `VPS_SSH_KEY` | Private SSH key | See instructions below |
| `VPS_PORT` | SSH port | `22` (default) |

#### Generate SSH Key for GitHub Actions

```bash
# On your local machine
ssh-keygen -t ed25519 -C "github-actions@rentflow" -f ~/.ssh/rentflow_github_actions

# Copy public key to VPS
ssh-copy-id -i ~/.ssh/rentflow_github_actions.pub ubuntu@YOUR_VPS_IP

# Test connection
ssh -i ~/.ssh/rentflow_github_actions ubuntu@YOUR_VPS_IP

# If successful, copy PRIVATE key for GitHub
cat ~/.ssh/rentflow_github_actions
```

**Copy the ENTIRE private key output** (including the BEGIN/END lines) and add it as `VPS_SSH_KEY` secret in GitHub.

#### Optional: Separate Staging Secrets

If you want different credentials for staging (recommended for security):

| Secret Name | Value |
|-------------|-------|
| `STAGING_VPS_HOST` | Same as `VPS_HOST` (same server) |
| `STAGING_VPS_USERNAME` | `ubuntu` |
| `STAGING_VPS_SSH_KEY` | Same SSH key (can reuse) |
| `STAGING_VPS_PORT` | `22` |

**Note**: Since staging runs on the same VPS, you can reuse the production secrets. The workflows will fall back to `VPS_*` if `STAGING_VPS_*` aren't set.

### Step 1.4: Set Up Branch Protection Rules

See detailed instructions in `GITHUB_SETUP.md`, but here's the quick version:

**For `main` branch:**

1. Go to: `Settings` → `Branches` → `Add branch protection rule`
2. Branch name pattern: `main`
3. Enable:
   - ✅ Require pull request before merging (1 approval)
   - ✅ Require status checks to pass (select `test` job)
   - ✅ Require conversation resolution
   - ✅ Do not allow bypassing
4. Save

**For `develop` branch:**

1. Add another protection rule
2. Branch name pattern: `develop`
3. Enable:
   - ✅ Require status checks to pass (select `test` job)
   - ⚪ Pull request approvals: 0 (allows self-merge for core team)
4. Save

---

## Phase 2: Set Up Staging Environment on VPS

### Step 2.1: SSH into Your VPS

```bash
ssh ubuntu@YOUR_VPS_IP
cd /home/ubuntu/rentflow
```

### Step 2.2: Pull Latest Code

```bash
# Ensure you have the latest code with all new files
git fetch origin
git checkout main
git pull origin main

# Verify new files exist
ls -la docker-compose.staging.yml
ls -la scripts/
```

### Step 2.3: Create Staging Environment File

```bash
# Copy staging example
cp .env.staging.example .env.staging

# Edit with your staging configuration
nano .env.staging
```

**Required values for `.env.staging`:**

```bash
# Flask Configuration
FLASK_ENV=staging
DEBUG=False
SECRET_KEY=your-staging-secret-key-change-this-32chars-min

# Database (different from production!)
DATABASE_URL=postgresql://rentflow_staging:staging_password_change_this@db:5432/rentflow_staging
POSTGRES_DB=rentflow_staging
POSTGRES_USER=rentflow_staging
POSTGRES_PASSWORD=staging_password_change_this

# Redis
REDIS_URL=redis://redis:6379/1

# Ports (different from production to avoid conflicts!)
NGINX_HTTP_PORT=8080
NGINX_HTTPS_PORT=8443
FLASK_PORT=9000
POSTGRES_PORT=5433
REDIS_PORT=6380
```

**Important**:
- Use different database name/credentials than production
- Use different ports to avoid conflicts with production
- Generate new `SECRET_KEY`: `python3 -c "import secrets; print(secrets.token_hex(32))"`

### Step 2.4: Create Staging Directories

```bash
# Create staging-specific directories
mkdir -p logs-staging uploads-staging instance-staging backups

# Set permissions
chmod 777 logs-staging uploads-staging instance-staging
```

### Step 2.5: Configure Firewall for Staging Ports

```bash
# Allow staging HTTP/HTTPS ports
sudo ufw allow 8080/tcp comment 'Staging HTTP'
sudo ufw allow 8443/tcp comment 'Staging HTTPS'

# Verify firewall rules
sudo ufw status numbered
```

### Step 2.6: Start Staging Environment

```bash
# Build and start staging containers
docker compose -f docker-compose.staging.yml --env-file .env.staging up -d

# Watch the startup process
docker compose -f docker-compose.staging.yml --env-file .env.staging logs -f
```

**Expected output:**
```
✓ Container rentflow-db-staging-1     Started
✓ Container rentflow-redis-staging-1  Started
✓ Container rentflow-web-staging-1    Started
✓ Container rentflow-nginx-staging-1  Started
```

Press `Ctrl+C` to exit logs.

### Step 2.7: Run Database Migrations (Staging)

```bash
# Run migrations to create database schema
docker compose -f docker-compose.staging.yml --env-file .env.staging exec web flask db upgrade
```

**Expected output:**
```
INFO  [alembic.runtime.migration] Running upgrade -> <revision>, <description>
✓ Migrations completed
```

### Step 2.8: Verify Staging is Running

```bash
# Check container status
docker compose -f docker-compose.staging.yml --env-file .env.staging ps

# Test staging health endpoint
curl http://localhost:9000/health

# Check staging via NGINX
curl http://localhost:8080/health
```

**Expected responses:**
```json
{"status": "healthy"}
```

### Step 2.9: Seed Staging with Test Data (Optional)

```bash
# Seed staging with test data for QA testing
./scripts/db-seed.sh staging small
```

Or sync sanitized production data:

```bash
# This will backup production, sanitize, and restore to staging
./scripts/db-sync-to-staging.sh
```

### Step 2.10: Access Staging Environment

**From anywhere:**
```
http://YOUR_VPS_IP:8080
```

**Test credentials** (if you seeded data):
- Email: `user1@test.example.com`
- Password: `TestPassword123!`

---

## Phase 3: Verify Production Still Works

### Step 3.1: Check Production Status

```bash
# On VPS
cd /home/ubuntu/rentflow

# Check if production is using new or old compose file location
if [ -f "docker-compose.production.yml" ]; then
    PROD_COMPOSE="docker-compose.production.yml"
    PROD_ENV=".env.production"
    if [ ! -f "$PROD_ENV" ]; then
        PROD_ENV=".env"
    fi
else
    PROD_COMPOSE="deployment/docker/docker-compose.yml"
    PROD_ENV=".env"
fi

echo "Production compose: $PROD_COMPOSE"
echo "Production env: $PROD_ENV"

# Check production containers
docker compose -f "$PROD_COMPOSE" --env-file "$PROD_ENV" ps
```

### Step 3.2: Verify Production is Healthy

```bash
# Test production health
curl http://localhost:8000/health
curl https://yourdomain.com/health
```

**Production should still be running normally** - we haven't touched it!

---

## Phase 4: Test Staging Deployment via GitHub Actions

### Step 4.1: Make a Test Change on Develop

```bash
# On your local machine
git checkout develop
git pull origin develop

# Make a small test change
echo "# Staging Deployment Test" >> STAGING_TEST.md
git add STAGING_TEST.md
git commit -m "test: verify staging auto-deployment"
git push origin develop
```

### Step 4.2: Watch GitHub Actions

1. Go to: `https://github.com/yourusername/rentflow/actions`
2. You should see two workflows running:
   - **Tests** (`test.yml`) - Runs on all pushes
   - **Deploy to Staging** (`deploy-staging.yml`) - Auto-deploys to staging

### Step 4.3: Verify Staging Updated

```bash
# On VPS, check staging logs
docker compose -f docker-compose.staging.yml --env-file .env.staging logs --tail=50 web

# Verify the new commit is deployed
docker compose -f docker-compose.staging.yml --env-file .env.staging exec web git rev-parse --short HEAD
```

**If deployment succeeded:**
- ✅ GitHub Actions shows green checkmark
- ✅ Staging is accessible at `http://YOUR_VPS_IP:8080`
- ✅ Latest commit is deployed

---

## Phase 5: Roll Out Local Development to Team

### Step 5.1: Update Team on Changes

Share this message with your development team:

---

**📢 Team Announcement: New Development Workflow**

We've implemented a professional multi-environment pipeline! 🎉

**What's changed:**
- New `develop` branch is now the default (not `main`)
- Local development setup is now automated
- Staging environment for QA testing
- CI/CD automation via GitHub Actions

**New workflow:**
1. Branch from `develop` (not `main`)
2. Create feature branches: `feature/my-feature`
3. PR to `develop` → Auto-deploys to staging
4. After QA approval, `develop` → `main` → Production

**Getting started:**

```bash
# Clone (or update) the repository
git checkout develop
git pull origin develop

# One-command setup
./scripts/local-dev-setup.sh --seed-data

# Access at: http://localhost:5000
# Login: user1@test.example.com / TestPassword123!
```

**Resources:**
- QUICKSTART.md - Quick reference
- DEVELOPMENT.md - Full development guide
- BRANCHING.md - Git workflow

**Questions?** Reach out to the team lead.

---

### Step 5.2: Help Developers Get Set Up

Each developer should:

```bash
# 1. Update local repository
cd /path/to/rentflow
git checkout develop
git pull origin develop

# 2. Run automated setup
./scripts/local-dev-setup.sh --seed-data

# 3. Verify environment
./scripts/validate-environment.sh local

# 4. Start developing!
make dev-up
make dev-test
```

**Common issues:**
- Docker not running: Start Docker Desktop
- Port conflicts: Change port in `.env.local`
- Permission issues: Run `make clean` and retry setup

---

## Phase 6: Validate the Full Pipeline

### Step 6.1: Create a Complete Feature Flow

Test the entire workflow end-to-end:

```bash
# 1. Create feature branch
git checkout develop
git pull origin develop
git checkout -b feature/test-pipeline

# 2. Make a change
echo "# Pipeline Test" >> PIPELINE_TEST.md
git add PIPELINE_TEST.md
git commit -m "feat: test complete pipeline flow"
git push origin feature/test-pipeline
```

### Step 6.2: Create PR to Develop

1. Go to GitHub
2. Create Pull Request: `feature/test-pipeline` → `develop`
3. Watch CI run (tests should pass)
4. Merge PR
5. Watch staging auto-deploy

### Step 6.3: Verify Staging Deployment

```bash
# Access staging
curl http://YOUR_VPS_IP:8080/health

# Check logs
ssh ubuntu@YOUR_VPS_IP
cd /home/ubuntu/rentflow
docker compose -f docker-compose.staging.yml logs --tail=100 web
```

### Step 6.4: Promote to Production (When Ready)

After QA testing in staging:

```bash
# Create PR: develop → main
git checkout develop
git pull origin develop
git checkout main
git pull origin main

# Create PR via GitHub UI
# After approval and merge, production auto-deploys
```

**Production deployment will:**
1. Run tests
2. Backup database automatically
3. Build new images
4. Deploy with zero-downtime
5. Verify health checks

---

## Phase 7: Optional - Migrate Production to New Structure

**This is OPTIONAL** - production will continue working with the current structure. The deployment workflow supports both old and new locations.

### Benefits of Migration:
- Consistency across all environments
- Cleaner project structure
- Easier to understand and maintain

### When to Migrate:
- During a planned maintenance window
- After staging has been stable for 1-2 weeks
- When you have time to verify thoroughly

### Migration Steps (OPTIONAL):

```bash
# On VPS
cd /home/ubuntu/rentflow
git checkout main
git pull origin main

# Create production env file at root
cp .env .env.production  # Backup current .env

# Stop production
docker compose -f deployment/docker/docker-compose.yml --env-file .env down

# Start with new location
docker compose -f docker-compose.production.yml --env-file .env.production up -d

# Verify
curl https://yourdomain.com/health
docker compose -f docker-compose.production.yml ps
```

**If anything goes wrong**, rollback:

```bash
docker compose -f docker-compose.production.yml down
docker compose -f deployment/docker/docker-compose.yml --env-file .env up -d
```

---

## 📊 Success Checklist

### GitHub Configuration
- [ ] `develop` branch created and pushed
- [ ] Default branch set to `develop`
- [ ] GitHub secrets configured (`VPS_HOST`, `VPS_USERNAME`, `VPS_SSH_KEY`)
- [ ] Branch protection enabled for `main` and `develop`

### Staging Environment
- [ ] `.env.staging` created with correct values
- [ ] Staging directories created (`logs-staging/`, `uploads-staging/`, etc.)
- [ ] Firewall configured (ports 8080, 8443 open)
- [ ] Staging containers running (`docker compose ps` shows all Up)
- [ ] Staging accessible at `http://YOUR_VPS_IP:8080`
- [ ] Database migrations completed
- [ ] Test data seeded (optional)

### Production Environment
- [ ] Production still running and healthy
- [ ] Production URL still accessible
- [ ] No disruption to production services

### CI/CD Pipeline
- [ ] Push to `develop` triggers staging deployment
- [ ] Tests run on all PRs
- [ ] Staging deployment succeeds via GitHub Actions
- [ ] Production deployment ready (test when ready)

### Developer Experience
- [ ] Team notified of new workflow
- [ ] Developers can run `local-dev-setup.sh` successfully
- [ ] Local environments working for all team members
- [ ] Documentation shared (QUICKSTART.md, DEVELOPMENT.md)

---

## 🆘 Troubleshooting

### Staging Port Conflicts

**Problem**: Staging ports conflict with other services

**Solution**:
```bash
# Edit .env.staging and choose different ports
nano .env.staging

# Change:
NGINX_HTTP_PORT=8090  # Instead of 8080
NGINX_HTTPS_PORT=8453  # Instead of 8443

# Update firewall
sudo ufw allow 8090/tcp
sudo ufw allow 8453/tcp

# Restart staging
docker compose -f docker-compose.staging.yml --env-file .env.staging down
docker compose -f docker-compose.staging.yml --env-file .env.staging up -d
```

### GitHub Actions Failing

**Problem**: Deployment workflows fail with SSH errors

**Solution**:
1. Verify secrets are correct:
   - `VPS_HOST` is your actual IP
   - `VPS_SSH_KEY` includes BEGIN/END lines
   - `VPS_USERNAME` is correct (usually `ubuntu`)

2. Test SSH manually:
   ```bash
   ssh -i ~/.ssh/rentflow_github_actions ubuntu@YOUR_VPS_IP
   ```

3. Check VPS firewall allows SSH from anywhere:
   ```bash
   sudo ufw allow 22/tcp
   ```

### Staging Database Won't Start

**Problem**: Staging database container fails to start

**Solution**:
```bash
# Check logs
docker compose -f docker-compose.staging.yml logs db

# Common fix: Remove old volume and recreate
docker compose -f docker-compose.staging.yml down -v
docker compose -f docker-compose.staging.yml up -d

# Run migrations again
docker compose -f docker-compose.staging.yml exec web flask db upgrade
```

### Production and Staging Both Down

**Problem**: Both environments stop working

**Solution**:
```bash
# Check Docker daemon
sudo systemctl status docker

# Restart Docker
sudo systemctl restart docker

# Restart both environments
docker compose -f deployment/docker/docker-compose.yml --env-file .env up -d
docker compose -f docker-compose.staging.yml --env-file .env.staging up -d
```

---

## 📞 Getting Help

If you run into issues:

1. **Check validation script**: `./scripts/validate-environment.sh staging`
2. **Review logs**: `docker compose -f docker-compose.staging.yml logs`
3. **Consult documentation**: DEVELOPMENT.md, DEPLOYMENT.md
4. **Check GitHub Actions logs**: Actions tab in GitHub
5. **Contact team lead or DevOps**

---

## 🎯 Summary

**What you're doing:**
1. ✅ Configure GitHub (secrets, branch protection)
2. ✅ Set up staging on VPS (same server, different ports)
3. ✅ Test staging deployment via GitHub Actions
4. ✅ Roll out local dev to team
5. ✅ Validate complete pipeline
6. ⚪ (Optional) Migrate production to new structure later

**What's NOT changing:**
- ❌ Production environment (still running as-is)
- ❌ Production URL (still accessible)
- ❌ Existing deployment process (works with both old/new structure)

**Timeline:**
- GitHub setup: 30 minutes
- Staging setup: 1-2 hours
- Team rollout: As developers are available
- Production migration: Optional, when ready

**You're ready to start!** Begin with Phase 1 (GitHub configuration) and work through each phase sequentially.

---

**Last Updated**: 2025-10-22
**Migration Version**: 1.0.0
**Status**: Ready for implementation
