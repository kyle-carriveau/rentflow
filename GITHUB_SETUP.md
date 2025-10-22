# GitHub Repository Setup Guide - RentFlow

Complete guide for configuring GitHub repository settings, branch protection, and CI/CD secrets for the multi-environment deployment pipeline.

## Table of Contents

1. [Initial Repository Setup](#initial-repository-setup)
2. [Branch Protection Rules](#branch-protection-rules)
3. [GitHub Actions Secrets](#github-actions-secrets)
4. [Environment Configuration](#environment-configuration)
5. [Webhooks & Integrations](#webhooks--integrations)
6. [Team Access & Permissions](#team-access--permissions)

---

## Initial Repository Setup

### 1. Create Develop Branch

```bash
# From your local repository
git checkout main
git pull origin main
git checkout -b develop
git push origin develop
```

### 2. Set Default Branch

**GitHub Settings:**
1. Go to: `Settings` → `Branches`
2. Under "Default branch", click the switch icon
3. Select `develop`
4. Click "Update"
5. Confirm the change

**Why**: New pull requests and clones will default to `develop` instead of `main`

### 3. Enable GitHub Actions

**GitHub Settings:**
1. Go to: `Settings` → `Actions` → `General`
2. Under "Actions permissions":
   - Select: ✅ "Allow all actions and reusable workflows"
3. Under "Workflow permissions":
   - Select: ✅ "Read and write permissions"
   - Enable: ✅ "Allow GitHub Actions to create and approve pull requests"
4. Click "Save"

---

## Branch Protection Rules

### Protection Rule for `main` (Production)

**Path**: `Settings` → `Branches` → `Add branch protection rule`

**Branch name pattern**: `main`

#### Required Settings:

✅ **Require a pull request before merging**
- ✅ Require approvals: `1` (minimum)
- ✅ Dismiss stale pull request approvals when new commits are pushed
- ✅ Require review from Code Owners (optional, if you have CODEOWNERS file)

✅ **Require status checks to pass before merging**
- ✅ Require branches to be up to date before merging
- **Required status checks** (select after first CI run):
  - `test` (from test.yml workflow)
  - `deploy / Run Tests` (from deploy-production.yml)

✅ **Require conversation resolution before merging**

✅ **Require signed commits** (recommended but optional)

✅ **Require linear history** (optional - prevents merge commits)

✅ **Do not allow bypassing the above settings**
- ✅ Include administrators (recommended)

✅ **Restrict who can push to matching branches**
- Add only CI/CD service accounts
- Developers must use Pull Requests

✅ **Allow force pushes**: ❌ **DISABLED**

✅ **Allow deletions**: ❌ **DISABLED**

Click "Create" to save the rule.

---

### Protection Rule for `develop` (Staging)

**Path**: `Settings` → `Branches` → `Add branch protection rule`

**Branch name pattern**: `develop`

#### Required Settings:

✅ **Require a pull request before merging**
- Require approvals: `0` (optional - allows self-merge for core team)
- ✅ Require approval of the most recent reviewable push

✅ **Require status checks to pass before merging**
- ✅ Require branches to be up to date before merging
- **Required status checks**:
  - `test` (from test.yml workflow)

✅ **Require conversation resolution before merging**

✅ **Allow force pushes**: ✅ **ENABLED** (for hotfixes)
- Specify who: Only core team members

✅ **Allow deletions**: ❌ **DISABLED**

Click "Create" to save the rule.

---

## GitHub Actions Secrets

Secrets are required for automated deployments to staging and production environments.

### Access Secrets Configuration

**Path**: `Settings` → `Secrets and variables` → `Actions`

### Required Secrets

#### 1. Production VPS Access

| Secret Name | Description | How to Generate |
|-------------|-------------|-----------------|
| `VPS_HOST` | Production server IP or domain | Your Hostinger VPS IP (e.g., `123.45.67.89`) |
| `VPS_USERNAME` | SSH username | Usually `ubuntu` or `root` |
| `VPS_SSH_KEY` | Private SSH key for authentication | See instructions below |
| `VPS_PORT` | SSH port (optional) | Default: `22` |

**Generate SSH Key:**
```bash
# On your local machine (if you don't have one)
ssh-keygen -t ed25519 -C "github-actions@rentflow" -f ~/.ssh/rentflow_deploy

# Copy public key to VPS
ssh-copy-id -i ~/.ssh/rentflow_deploy.pub ubuntu@your-vps-ip

# Test connection
ssh -i ~/.ssh/rentflow_deploy ubuntu@your-vps-ip

# Copy PRIVATE key content for GitHub Secret
cat ~/.ssh/rentflow_deploy
# Copy the entire output including:
# -----BEGIN OPENSSH PRIVATE KEY-----
# ... key content ...
# -----END OPENSSH PRIVATE KEY-----
```

**Add to GitHub:**
1. Go to: `Settings` → `Secrets and variables` → `Actions`
2. Click "New repository secret"
3. Name: `VPS_SSH_KEY`
4. Value: Paste the entire private key
5. Click "Add secret"

#### 2. Staging VPS Access (if separate server)

| Secret Name | Description | Value |
|-------------|-------------|-------|
| `STAGING_VPS_HOST` | Staging server IP | Same as production if using same VPS |
| `STAGING_VPS_USERNAME` | SSH username | Usually `ubuntu` |
| `STAGING_VPS_SSH_KEY` | Private SSH key | Can be same as production |
| `STAGING_VPS_PORT` | SSH port | Default: `22` |

**Note**: If staging runs on the same VPS as production (recommended for cost), you can reuse the production secrets.

#### 3. Environment Secrets (Optional but Recommended)

| Secret Name | Description | Used In |
|-------------|-------------|---------|
| `PRODUCTION_SECRET_KEY` | Flask secret key for production | Production deployment |
| `STAGING_SECRET_KEY` | Flask secret key for staging | Staging deployment |
| `CLOUDFLARE_API_TOKEN` | Cloudflare API token (if needed) | SSL automation |

### Secrets Summary Table

**Production Environment:**
```
VPS_HOST=123.45.67.89
VPS_USERNAME=ubuntu
VPS_SSH_KEY=<private-key-content>
VPS_PORT=22
```

**Staging Environment (same VPS):**
```
STAGING_VPS_HOST=123.45.67.89  (same as production)
STAGING_VPS_USERNAME=ubuntu
STAGING_VPS_SSH_KEY=<same-private-key>
STAGING_VPS_PORT=22
```

---

## Environment Configuration

GitHub Environments provide deployment protection rules and environment-specific secrets.

### Create Environments

**Path**: `Settings` → `Environments`

### 1. Production Environment

1. Click "New environment"
2. Name: `production`
3. Configure protection rules:

#### Protection Rules:
- ✅ **Required reviewers**: Add 1+ reviewers
- ✅ **Wait timer**: 0 minutes (or add delay if desired)
- ✅ **Deployment branches**: Selected branches only
  - Add pattern: `main`

4. Click "Save protection rules"

#### Environment Secrets:
Add production-specific secrets here (optional, overrides repository secrets):
- `SECRET_KEY` (if different from repo secret)
- `DATABASE_URL` (already configured on VPS)

### 2. Staging Environment

1. Click "New environment"
2. Name: `staging`
3. Configure protection rules:

#### Protection Rules:
- ✅ **Deployment branches**: Selected branches only
  - Add pattern: `develop`
- ⚪ Required reviewers: None (auto-deploy)
- ⚪ Wait timer: 0 minutes

4. Click "Save protection rules"

---

## Webhooks & Integrations

### Slack/Discord Notifications (Optional)

1. Go to: `Settings` → `Webhooks`
2. Click "Add webhook"
3. Configure:
   - **Payload URL**: Your Slack/Discord webhook URL
   - **Content type**: `application/json`
   - **Events**: Select specific events:
     - ✅ Workflow runs
     - ✅ Pull requests
     - ✅ Pushes
4. Click "Add webhook"

### Status Badges

Add status badges to README.md:

```markdown
![Tests](https://github.com/YOUR_USERNAME/rentflow/workflows/Tests/badge.svg)
![Production Deploy](https://github.com/YOUR_USERNAME/rentflow/workflows/Deploy%20to%20Production/badge.svg)
![Staging Deploy](https://github.com/YOUR_USERNAME/rentflow/workflows/Deploy%20to%20Staging/badge.svg)
```

---

## Team Access & Permissions

### Recommended Team Structure

**Path**: `Settings` → `Collaborators and teams`

#### Roles:

1. **Owners / Admins**
   - Full access
   - Can modify settings
   - Can override branch protection (if enabled)

2. **Maintainers**
   - Write access
   - Can merge to `develop`
   - Can approve PRs to `main`

3. **Developers**
   - Write access
   - Can create feature branches
   - Can create PRs
   - Cannot merge to `main` directly

4. **QA / Read-only**
   - Read access
   - Can comment on PRs
   - Cannot push code

### Invite Collaborators

1. Go to: `Settings` → `Collaborators and teams`
2. Click "Add people" or "Add teams"
3. Select role: `Write`, `Maintain`, or `Admin`
4. Send invitation

---

## Verification Checklist

After completing setup, verify:

### Branch Protection
- [ ] `main` requires PR approval
- [ ] `main` requires passing tests
- [ ] `main` prevents force pushes
- [ ] `main` prevents direct commits
- [ ] `develop` requires passing tests
- [ ] `develop` is the default branch

### GitHub Actions
- [ ] Actions are enabled
- [ ] Workflow permissions are set
- [ ] VPS secrets are added
- [ ] SSH key works (test manually first)

### Environments
- [ ] `production` environment created
- [ ] `production` requires reviewer approval
- [ ] `production` restricted to `main` branch
- [ ] `staging` environment created
- [ ] `staging` restricted to `develop` branch

### Access Control
- [ ] Team members invited
- [ ] Roles assigned correctly
- [ ] Code owners defined (if using CODEOWNERS)

### Test Deployments
- [ ] Push to `develop` → Staging deploys automatically
- [ ] Create PR to `main` → Requires approval
- [ ] Merge to `main` → Production deploys automatically

---

## Troubleshooting

### GitHub Actions Failing

**SSH Connection Issues:**
```bash
# Test SSH connection manually
ssh -i ~/.ssh/rentflow_deploy ubuntu@your-vps-ip

# Check SSH key format (must be OpenSSH format)
cat ~/.ssh/rentflow_deploy | head -1
# Should show: -----BEGIN OPENSSH PRIVATE KEY-----

# If it shows "BEGIN RSA PRIVATE KEY", convert:
ssh-keygen -p -f ~/.ssh/rentflow_deploy -m PEM
```

**Missing Secrets:**
- Verify secret names match exactly (case-sensitive)
- Check no trailing spaces in secret values
- Ensure secrets are added to correct scope (repo vs environment)

**Branch Protection Issues:**
- Ensure status check names match workflow job names
- Run workflows at least once before adding as required checks
- Verify administrator bypass is disabled if needed

### Deployment Failures

**VPS Not Reachable:**
```bash
# From GitHub Actions logs, check:
# 1. VPS is online
# 2. SSH port is open
# 3. Firewall allows GitHub IP ranges

# On VPS, check if Docker is running:
sudo systemctl status docker
```

**Permission Denied:**
```bash
# Ensure deploy user has Docker permissions
sudo usermod -aG docker ubuntu
# Logout and login for changes to take effect
```

---

## Security Best Practices

1. **Rotate SSH Keys Regularly**
   - Generate new key every 90 days
   - Update GitHub secret

2. **Use Dedicated Deploy Key**
   - Don't use personal SSH key
   - Create specific key for CI/CD

3. **Limit Secret Access**
   - Only add secrets that workflows need
   - Use environment-specific secrets when possible

4. **Review Access Logs**
   - Check: `Settings` → `Access` → `Audit log`
   - Monitor who added/modified secrets

5. **Enable Two-Factor Authentication**
   - Required for all team members
   - Especially for users with admin access

---

## Additional Resources

- [GitHub Branch Protection Docs](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/about-protected-branches)
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [GitHub Environments](https://docs.github.com/en/actions/deployment/targeting-different-environments/using-environments-for-deployment)
- [SSH Key Generation](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/generating-a-new-ssh-key-and-adding-it-to-the-ssh-agent)

---

**Last Updated**: 2025-10-22
**Maintained By**: DevOps Team
