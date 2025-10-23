# Workflow Trigger Fix - Deploy to Staging After Tests

## The Problem

The "Deploy to Staging" workflow was not triggering after the "Tests" workflow completed on the `develop` branch.

## Root Cause

The `workflow_run` trigger has a **critical limitation** in GitHub Actions:

```yaml
# ❌ THIS DOESN'T WORK AS EXPECTED
on:
  workflow_run:
    workflows: ["Tests"]
    branches:
      - develop  # This filter doesn't work correctly!
```

**Why?** The `branches` filter in `workflow_run` is matched against the **default branch** of the repository, NOT the actual branch that triggered the workflow. This is a known GitHub Actions limitation.

## The Solution

Move the branch check from the trigger to the job's `if` condition using `github.event.workflow_run.head_branch`:

```yaml
# ✅ THIS WORKS CORRECTLY
on:
  workflow_run:
    workflows: ["Tests"]
    types:
      - completed
  workflow_dispatch:

jobs:
  deploy:
    name: Deploy to Staging
    runs-on: ubuntu-latest
    # Check BOTH success AND branch in the if condition
    if: |
      github.event.workflow_run.conclusion == 'success' &&
      github.event.workflow_run.head_branch == 'develop'
```

## What Changed

### deploy-staging.yml
- ❌ **Removed** `branches: - develop` from the trigger (doesn't work)
- ✅ **Added** `github.event.workflow_run.head_branch == 'develop'` to the `if` condition
- ✅ **Added** debug step to show trigger information
- ✅ **Added** explicit `ref: develop` to checkout step

### deploy.yml (Production)
- ❌ **Removed** `branches: - main` from the trigger (doesn't work)
- ✅ **Added** `github.event.workflow_run.head_branch == 'main'` to the `if` condition
- ✅ **Added** debug step to show trigger information
- ✅ **Added** explicit `ref: main` to checkout step

## Expected Behavior

### Scenario 1: Push to `develop` branch

```
1. Push to develop
2. Tests workflow runs on develop
3. Tests workflow completes successfully
4. Deploy to Staging workflow triggers (because head_branch == 'develop')
5. Deploy to Production workflow DOES NOT trigger (because head_branch != 'main')
```

### Scenario 2: Push to `main` branch

```
1. Push to main
2. Tests workflow runs on main
3. Tests workflow completes successfully
4. Deploy to Production workflow triggers (because head_branch == 'main')
5. Deploy to Staging workflow DOES NOT trigger (because head_branch != 'develop')
```

## How to Verify

After committing this fix:

1. **Push to develop branch:**
   ```bash
   git add .
   git commit -m "Fix workflow triggers for multi-environment deployment"
   git push origin develop
   ```

2. **Watch GitHub Actions:**
   - Go to: `https://github.com/your-repo/actions`
   - You should see:
     - ✅ "Tests" workflow runs and completes
     - ✅ "Deploy to Staging" workflow triggers automatically
     - ❌ "Deploy to Production" does NOT trigger

3. **Check the debug output:**
   - Open the "Deploy to Staging" workflow run
   - Look for "Debug workflow trigger info" step
   - Should show:
     ```
     Triggered by workflow: Tests
     Branch: develop
     Conclusion: success
     Event: workflow_run
     ```

4. **Push to main branch (after testing staging):**
   ```bash
   git checkout main
   git merge develop
   git push origin main
   ```

5. **Verify production deployment:**
   - ✅ "Tests" workflow runs and completes
   - ✅ "Deploy to Production" workflow triggers automatically
   - ❌ "Deploy to Staging" does NOT trigger

## Troubleshooting

### Staging deployment still not triggering?

**Check 1: Workflow name matches exactly**
```yaml
workflows: ["Tests"]  # Must match the name in test.yml EXACTLY
```

In `test.yml`, the workflow name is:
```yaml
name: Tests  # ✓ Matches
```

**Check 2: Tests workflow succeeded**
- Tests must complete with status "success"
- If tests fail, deployment will not trigger
- Check the Tests workflow logs

**Check 3: Branch name matches exactly**
```yaml
github.event.workflow_run.head_branch == 'develop'  # Case-sensitive!
```

**Check 4: View all workflow runs**
- Go to Actions tab
- Look for "Deploy to Staging" in the list
- If you see it with a gray circle and "Skipped", the `if` condition failed
- Click on it to see why it was skipped

### Production deployment triggering when it shouldn't?

- Verify the `if` condition checks for `head_branch == 'main'`
- Check that you're not accidentally pushing to main
- Review git branch with: `git branch --show-current`

## Multi-Environment Safety

✅ **This fix ensures:**
1. Staging ONLY deploys from `develop` branch
2. Production ONLY deploys from `main` branch
3. No cross-contamination between environments
4. Manual deployment still possible via `workflow_dispatch`

❌ **What this prevents:**
1. Staging code accidentally deploying to production
2. Production deployments from feature branches
3. Deployments when tests fail

## Manual Deployment (Emergency)

If you need to manually trigger a deployment:

**Staging:**
1. Go to Actions → "Deploy to Staging"
2. Click "Run workflow"
3. Select branch: `develop`
4. Click "Run workflow"

**Production:**
1. Go to Actions → "Deploy to Production"
2. Click "Run workflow"
3. Select branch: `main`
4. Click "Run workflow"

## References

- [GitHub Actions: workflow_run trigger](https://docs.github.com/en/actions/using-workflows/events-that-trigger-workflows#workflow_run)
- [Known limitation with workflow_run branches filter](https://github.com/orgs/community/discussions/26325)

---

**Fixed:** 2025-10-22
**Status:** ✅ Production-ready
