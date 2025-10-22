# Git Branching Strategy - RentFlow

## Overview

RentFlow uses a **simplified GitFlow** branching model with three main branches and automatic deployments to each environment.

```
feature/* → develop → staging → main → production
  (dev)      (QA)      (test)    (prod)
```

## Branch Structure

### 🔧 `main` - Production Branch
- **Purpose**: Production-ready code
- **Protection**: Fully protected
- **Deployment**: Auto-deploys to **production** via GitHub Actions
- **Merges From**: `develop` only (via Pull Request)
- **URL**: https://yourdomain.com

**Rules:**
- ✅ Requires pull request review (1+ approvals)
- ✅ Requires status checks to pass (tests, builds)
- ✅ No direct commits allowed
- ✅ No force pushes allowed
- ✅ Include administrators in restrictions

### 🧪 `develop` - Staging/Integration Branch
- **Purpose**: Integration branch for testing features together
- **Protection**: Protected
- **Deployment**: Auto-deploys to **staging** via GitHub Actions
- **Merges From**: `feature/*` branches (via Pull Request)
- **Merges To**: `main` (via Pull Request)
- **URL**: https://staging.yourdomain.com (or http://your-ip:8080)

**Rules:**
- ✅ Requires status checks to pass (tests)
- ✅ Pull requests recommended (can be bypassed by core team)
- ❌ Force pushes allowed (for integration fixes)

### 🌿 `feature/*` - Feature Branches
- **Purpose**: Individual feature development
- **Protection**: None
- **Deployment**: Local development only
- **Merges From**: `develop` (to stay up-to-date)
- **Merges To**: `develop` (via Pull Request)

**Naming Convention:**
- `feature/user-authentication`
- `feature/add-reporting-module`
- `bugfix/fix-lease-calculation`
- `hotfix/security-patch`

## Development Workflow

### Standard Feature Development

```bash
# 1. Start from develop
git checkout develop
git pull origin develop

# 2. Create feature branch
git checkout -b feature/my-new-feature

# 3. Develop locally
# ... make changes ...
make dev-up          # Start local environment
make dev-migrate     # Run migrations
make dev-test        # Run tests

# 4. Commit changes
git add .
git commit -m "Add new feature: description"

# 5. Push feature branch
git push origin feature/my-new-feature

# 6. Create Pull Request to develop
# - Go to GitHub
# - Create PR: feature/my-new-feature → develop
# - Request review
# - Wait for CI tests to pass

# 7. Merge to develop (auto-deploys to staging)
# - PR gets approved and merged
# - GitHub Actions automatically deploys to staging
# - QA team tests on staging environment

# 8. After staging approval, create PR to main
# - Create PR: develop → main
# - Requires manual approval
# - Merging deploys to production
```

### Hotfix Workflow (Urgent Production Fixes)

```bash
# 1. Create hotfix from main
git checkout main
git pull origin main
git checkout -b hotfix/critical-security-fix

# 2. Make the fix
# ... fix the issue ...
make dev-test  # Verify fix

# 3. Commit and push
git add .
git commit -m "Hotfix: description of fix"
git push origin hotfix/critical-security-fix

# 4. Create PR to main (expedited review)
# - Get immediate review
# - Merge to main → deploys to production

# 5. Backport to develop
git checkout develop
git merge hotfix/critical-security-fix
git push origin develop
```

## Deployment Pipeline

### Automatic Deployments

| Branch    | Environment | Trigger          | Auto-Deploy | Approval Required |
|-----------|-------------|------------------|-------------|-------------------|
| `feature/*` | Local     | Developer action | No          | N/A               |
| `develop` | Staging     | Push to develop  | ✅ Yes      | No                |
| `main`    | Production  | Push to main     | ✅ Yes      | Yes (PR approval) |

### Deployment Flow

```
Developer                GitHub Actions          Staging            Production
    │                          │                     │                   │
    │──Push to feature/*──>   │                     │                   │
    │                          │                     │                   │
    │──PR to develop──────>   │                     │                   │
    │                          │                     │                   │
    │──Merge────────────────> │──Run Tests──>      │                   │
    │                          │                     │                   │
    │                          │──Build Images──>   │                   │
    │                          │                     │                   │
    │                          │──Deploy────────>   │ (staging ready)   │
    │                          │                     │                   │
    │                          │                     │                   │
    │──QA Approval───────────────────────────────>  │                   │
    │                          │                     │                   │
    │──PR to main─────────>   │                     │                   │
    │                          │                     │                   │
    │──Manual Approval────>   │                     │                   │
    │                          │                     │                   │
    │──Merge────────────────> │──Run Tests──>      │                   │
    │                          │                     │                   │
    │                          │──Backup DB──>      │                   │
    │                          │                     │                   │
    │                          │──Deploy──────────────────────────────> │
    │                          │                     │                   │
    │                          │──Health Checks─────────────────────>  │
    │                          │                     │                   │
    │                          │<─Success/Failure──────────────────────│
```

## Environment URLs

| Environment | URL | Branch | Purpose |
|-------------|-----|--------|---------|
| **Local** | http://localhost:5000 | `feature/*` | Development |
| **Staging** | https://staging.yourdomain.com | `develop` | QA/Testing |
| **Production** | https://yourdomain.com | `main` | Live |

## Best Practices

### ✅ DO

- Create feature branches from `develop`
- Keep feature branches small and focused
- Write descriptive commit messages
- Run tests locally before pushing
- Update `develop` regularly in your feature branch
- Delete feature branches after merging
- Use Pull Requests for all merges to `develop` and `main`
- Test in staging before promoting to production
- Document breaking changes in PR description

### ❌ DON'T

- Commit directly to `main`
- Force push to `main` or `develop`
- Merge without code review
- Deploy to production without staging verification
- Create long-lived feature branches (>2 weeks)
- Commit secrets or sensitive data
- Skip tests before merging
- Merge breaking changes without migration guide

## Commit Message Format

Use conventional commit format for clear history:

```
type(scope): subject

body (optional)

footer (optional)
```

**Types:**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation changes
- `style:` Code style changes (formatting)
- `refactor:` Code refactoring
- `perf:` Performance improvements
- `test:` Adding/updating tests
- `chore:` Maintenance tasks
- `ci:` CI/CD changes

**Examples:**
```
feat(auth): add two-factor authentication

fix(lease): correct rent calculation for partial months

docs(deployment): update staging setup instructions

chore(deps): upgrade Flask to 3.0.0
```

## Branch Protection Setup

See [GITHUB_SETUP.md](GITHUB_SETUP.md) for detailed GitHub branch protection configuration.

## Migration from Current Setup

If you're currently working with only a `main` branch:

```bash
# 1. Create develop from main
git checkout main
git pull origin main
git checkout -b develop
git push origin develop

# 2. Set develop as default branch in GitHub
# Settings → Branches → Default branch → develop

# 3. Update local repository
git branch --set-upstream-to=origin/develop develop

# 4. All future features branch from develop
git checkout develop
git checkout -b feature/my-feature
```

## Troubleshooting

### Merge Conflicts

```bash
# Update your feature branch with latest develop
git checkout feature/my-feature
git fetch origin
git merge origin/develop

# Resolve conflicts
# ... edit conflicting files ...
git add .
git commit -m "Merge develop into feature/my-feature"
```

### Accidentally Committed to Wrong Branch

```bash
# If you committed to develop instead of feature branch
git checkout develop
git reset --soft HEAD~1  # Undo last commit, keep changes

# Create proper feature branch
git checkout -b feature/my-feature
git commit -m "Proper commit message"
git push origin feature/my-feature
```

### Staging Deployment Failed

```bash
# Check GitHub Actions logs
# Fix the issue in your branch
git add .
git commit -m "Fix deployment issue"
git push origin feature/my-feature

# Re-merge to develop after fix
```

## Additional Resources

- [GitHub Flow Documentation](https://guides.github.com/introduction/flow/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [Branch Protection Rules](GITHUB_SETUP.md)
- [Local Development Guide](DEVELOPMENT.md)
- [Deployment Guide](DEPLOYMENT.md)

---

**Last Updated**: 2025-10-22
**Maintained By**: Development Team
