# RentFlow - Quick Start Guide

**Multi-Environment Deployment Pipeline - Implementation Complete** ✅

This guide provides a quick reference for getting started with RentFlow's development environment and understanding the deployment pipeline.

---

## 🚀 Quick Start Guide

### For New Developers

Get up and running in 3 steps:

```bash
# 1. Clone and setup
git checkout develop
git pull origin develop

# 2. One-command setup (includes test data)
./scripts/local-dev-setup.sh --seed-data

# 3. Access application
# Open: http://localhost:5000
# Login: user1@test.example.com / TestPassword123!
```

That's it! Your local development environment is ready.

---

## 📦 Common Development Commands

### Daily Workflow

```bash
# Start environment
make dev-up

# View logs
make dev-logs

# Run tests
make dev-test

# Stop environment
make dev-down
```

### Database Operations

```bash
# Run migrations
make dev-migrate

# Backup database
make dev-db-backup

# Seed test data
make dev-db-seed

# Reset database (deletes all data!)
make dev-db-reset
```

### Git Workflow

```bash
# Create feature branch
make feature NAME=my-feature

# Sync with develop
make sync-develop
```

### See All Commands

```bash
# Display full list of available commands
make help
```

---

## 📁 Complete File Structure

```
rentflow/
├── .github/workflows/
│   ├── deploy.yml              # ✅ Production deployment (updated)
│   ├── deploy-staging.yml      # ✅ Staging deployment (new)
│   └── test.yml                # ✅ CI testing (new)
│
├── scripts/
│   ├── db-backup.sh            # ✅ Database backup
│   ├── db-restore.sh           # ✅ Database restore
│   ├── db-sync-to-staging.sh   # ✅ Prod→Staging sync + PII sanitization
│   ├── db-seed.sh              # ✅ Test data seeding (bash wrapper)
│   ├── db-seed.py              # ✅ Test data seeding (Python script)
│   ├── local-dev-setup.sh      # ✅ Automated setup
│   └── validate-environment.sh # ✅ Environment validation
│
├── config/
│   └── __init__.py             # ✅ Multi-environment configuration classes
│
├── docker-compose.local.yml        # ✅ Local development
├── docker-compose.staging.yml      # ✅ Staging environment
├── docker-compose.production.yml   # ✅ Production (at root)
│
├── Makefile                    # ✅ Development commands (50+ shortcuts)
│
├── QUICKSTART.md               # ✅ This file
├── DEVELOPMENT.md              # ✅ Comprehensive development guide
├── BRANCHING.md                # ✅ Git workflow and branching strategy
├── GITHUB_SETUP.md             # ✅ GitHub configuration guide
├── DEPLOYMENT.md               # ✅ Deployment instructions
├── README.md                   # ✅ Project overview
├── CLAUDE.md                   # ✅ Project context for AI
│
├── .env.local.example          # ✅ Local environment template
├── .env.staging.example        # ✅ Staging environment template
└── .env.production.example     # ✅ Production environment template
```

---

## 🔄 Deployment Pipeline Flow

```
Developer → feature/* → develop → staging → main → production
            (local)     (staging)  (test)   (prod)
```

### GitHub Actions Triggers

| Event | Workflow | Action |
|-------|----------|--------|
| **PR to develop/main** | `test.yml` | Runs full test suite, linting, security scans |
| **Push to develop** | `deploy-staging.yml` | Auto-deploy to staging environment |
| **Push to main** | `deploy.yml` | Auto-deploy to production environment |

### Environment URLs

| Environment | URL | Branch | Auto-Deploy |
|-------------|-----|--------|-------------|
| **Local** | http://localhost:5000 | `feature/*` | No (manual) |
| **Staging** | http://your-ip:8080 | `develop` | ✅ Yes |
| **Production** | https://yourdomain.com | `main` | ✅ Yes |

---

## 📋 Next Steps / Recommended Actions

### 1. Test Local Setup

Verify your local environment works correctly:

```bash
./scripts/local-dev-setup.sh --seed-data
make dev-test
./scripts/validate-environment.sh local
```

### 2. Validate Environments

Check environment health before deployment:

```bash
# Local validation
./scripts/validate-environment.sh local

# Later: Staging validation (run on VPS)
./scripts/validate-environment.sh staging

# Later: Production validation (run on VPS)
./scripts/validate-environment.sh production
```

### 3. Set Up GitHub Secrets (for CI/CD)

Follow the detailed instructions in `GITHUB_SETUP.md`:

- Add VPS SSH keys (`VPS_SSH_KEY`, `VPS_HOST`, `VPS_USERNAME`)
- Configure staging/production environments
- Set up branch protection rules
- Test deployment workflows

### 4. Create Staging Environment on VPS

Set up staging on your VPS:

```bash
# On VPS
cd /home/ubuntu/rentflow

# Create staging environment file
cp .env.staging.example .env.staging
nano .env.staging  # Edit with actual values

# Start staging environment
docker compose -f docker-compose.staging.yml up -d

# Configure firewall (if needed)
sudo ufw allow 8080/tcp
sudo ufw allow 8443/tcp
```

### 5. Test Staging Deployment

Verify automatic staging deployment:

```bash
# Create a test change
git checkout develop
git pull origin develop
echo "# Test" >> TEST.md
git add TEST.md
git commit -m "test: trigger staging deployment"
git push origin develop

# Watch GitHub Actions at:
# https://github.com/yourusername/rentflow/actions
```

### 6. Documentation Review

Share these resources with your team:

- **QUICKSTART.md** (this file) - Quick reference
- **DEVELOPMENT.md** - Comprehensive development guide
- **BRANCHING.md** - Git workflow and strategy
- **GITHUB_SETUP.md** - Repository configuration
- **DEPLOYMENT.md** - Deployment procedures

---

## ⚠️ Important Notes

### 1. Database Scripts Are Production-Safe

All database scripts have multiple safety layers:

- **Local**: No confirmation required
- **Staging**: Text confirmation required (`RESTORE STAGING`)
- **Production**: Explicit confirmation + automatic safety backup

Example production restore:
```bash
./scripts/db-restore.sh production backup.sql
# Prompts: "Type EXACTLY: 'RESTORE PRODUCTION DATABASE' to proceed"
# Creates automatic safety backup first
# Stops web container during restore
```

### 2. PII Sanitization

`db-sync-to-staging.sh` automatically sanitizes all sensitive data:

| Data Type | Production | Staging (Sanitized) |
|-----------|-----------|---------------------|
| **User emails** | `john.doe@gmail.com` | `user1@example.com` |
| **User passwords** | Various hashed passwords | `StagingPassword123!` |
| **Tenant emails** | Real emails | `tenant1@example.com` |
| **Tenant phones** | Real phone numbers | `(555) 000-0001` |
| **Addresses** | Real addresses | `1 Test Street, Test City, CA 90000` |
| **Payment info** | Real payment data | `Test Payment` (cleared) |
| **Company info** | Real business data | `Test Company 1` |

**Always review the script before running in production!**

### 3. Environment Files Not Committed

For security, environment files are excluded from git:

```bash
# These files are in .gitignore:
.env
.env.local
.env.staging
.env.production
```

**Never commit real credentials!** Use the `.example` templates to create your environment files.

### 4. Makefile Requires `make`

The Makefile provides convenient shortcuts:

- **macOS/Linux**: `make` is pre-installed
- **Windows**: Install via [Chocolatey](https://chocolatey.org/) or [GNU Make for Windows](http://gnuwin32.sourceforge.net/packages/make.htm)
- **Alternative**: Use Docker Compose commands directly (see `DEVELOPMENT.md`)

---

## 🎯 Key Features Implemented

### ✅ All Phases Complete

- ✅ **Multi-environment configuration** (DEV/STAGING/PROD)
- ✅ **Docker Compose** for all environments
- ✅ **Database management** (backup, restore, sync, seed)
- ✅ **PII sanitization** for staging
- ✅ **Automated CI/CD pipeline** with GitHub Actions
- ✅ **Comprehensive testing workflow** (unit, integration, coverage)
- ✅ **One-command developer setup** (`local-dev-setup.sh`)
- ✅ **50+ Makefile shortcuts** for common tasks
- ✅ **Environment validation tools** (`validate-environment.sh`)
- ✅ **Complete documentation** (this file + 5 other guides)

---

## 🛠️ Troubleshooting

### Common Issues

#### Port Already in Use

```bash
# Find process using port 5000
lsof -i :5000

# Kill the process
kill -9 <PID>

# Or change port in .env.local
FLASK_PORT=5001
```

#### Docker Not Running

```bash
# Start Docker Desktop
# Then verify:
docker info
```

#### Database Connection Failed

```bash
# Restart database container
make dev-restart

# Check database logs
make dev-logs-db

# Verify connection
docker compose -f docker-compose.local.yml exec db pg_isready
```

#### Reset Everything

If all else fails, start fresh:

```bash
# Nuclear option - removes everything
make clean

# Remove local config
rm .env.local

# Start fresh
./scripts/local-dev-setup.sh --seed-data
```

For more troubleshooting, see **DEVELOPMENT.md**.

---

## 📚 Additional Resources

### Documentation

- **QUICKSTART.md** (this file) - Quick reference guide
- **DEVELOPMENT.md** - Detailed development guide
- **BRANCHING.md** - Git workflow and branching strategy
- **GITHUB_SETUP.md** - GitHub configuration instructions
- **DEPLOYMENT.md** - Deployment procedures
- **README.md** - Project overview
- **CLAUDE.md** - Project context for AI assistance

### External Links

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)

### Getting Help

- **Check documentation** in the files listed above
- **Review logs**: `make dev-logs`
- **Validate environment**: `./scripts/validate-environment.sh local`
- **Contact team**: Reach out to the development team

---

## 🎉 You're Ready!

The multi-environment deployment pipeline is complete and ready to use.

**Next actions:**
1. ✅ Run `./scripts/local-dev-setup.sh --seed-data`
2. ✅ Explore the application at http://localhost:5000
3. ✅ Read `DEVELOPMENT.md` for detailed workflow
4. ✅ Set up GitHub secrets for CI/CD
5. ✅ Start building features!

**Happy coding!** 🚀

---

**Last Updated**: 2025-10-22
**Version**: 1.0.0
**Maintained By**: Development Team
