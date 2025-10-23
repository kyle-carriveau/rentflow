# Zero-Downtime Deployment Testing Guide

This guide explains how to validate that your deployments are truly zero-downtime.

## What is Zero-Downtime Deployment?

Zero-downtime deployment means:
- ✅ Users experience **no interruption** during code deployments
- ✅ Health checks **never fail** during the deployment process
- ✅ Database stays **online and available** throughout
- ✅ Active user sessions are **preserved**
- ✅ No "502 Bad Gateway" or connection errors

## Why This Matters

**Before zero-downtime implementation:**
- Every deployment caused 30-60 seconds of complete outage
- Users saw error pages
- Active sessions were lost
- Database was offline during migrations

**After zero-downtime implementation:**
- Deployments are invisible to users
- No service interruption
- Database migrations run against live database
- Seamless transition from old to new code

## Testing Strategy

### Automated Testing (Recommended)

We've created a test script that continuously monitors the application during deployment.

#### Step 1: SSH to VPS

```bash
ssh ubuntu@your-vps-ip
cd /home/ubuntu/rentflow
```

#### Step 2: Start the Test Script

```bash
# For production
./deployment/scripts/test-zero-downtime.sh production

# For staging
./deployment/scripts/test-zero-downtime.sh staging
```

The script will:
1. Poll the health endpoint every second
2. Record success/failure of each request
3. Continue for 5 minutes (or until Ctrl+C)
4. Generate a detailed report

#### Step 3: Trigger Deployment

While the test script is running, trigger a deployment:

**For Production:**
```bash
# In another terminal or via GitHub
git push origin main
```

**For Staging:**
```bash
git push origin develop
```

#### Step 4: Review Results

The test script will show:
- ✅ **0 failed requests** = Zero-downtime SUCCESS
- ❌ **Any failed requests** = Downtime occurred (needs investigation)

Example output:
```
==========================================
Test Results
==========================================
Duration: 180s
Total Requests: 180
Failed Requests: 0
Success Rate: 100.00%
==========================================

✅ SUCCESS: Zero-downtime deployment verified!
   No requests failed during the test period.
   Your deployment strategy is working correctly.
```

### Manual Testing

If you prefer manual validation:

#### Terminal 1: Continuous Health Check Monitor

```bash
# Production
while true; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health)
    if [ "$STATUS" != "200" ]; then
        echo "[$(date)] ❌ FAILED: HTTP $STATUS"
    else
        echo -ne "\r[$(date)] ✓ OK: HTTP $STATUS"
    fi
    sleep 1
done

# Staging
while true; do
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:9000/health)
    if [ "$STATUS" != "200" ]; then
        echo "[$(date)] ❌ FAILED: HTTP $STATUS"
    else
        echo -ne "\r[$(date)] ✓ OK: HTTP $STATUS"
    fi
    sleep 1
done
```

#### Terminal 2: Watch Docker Container Status

```bash
# Production
watch -n 1 'docker compose -f docker-compose.production.yml ps'

# Staging
watch -n 1 'docker compose -f docker-compose.staging.yml ps'
```

You should see:
1. Old `rentflow_web` container running (healthy)
2. New container starts
3. New container becomes healthy
4. Old container stops
5. **At no point should both be down**

#### Terminal 3: Trigger Deployment

```bash
# Push to appropriate branch or manually run workflow
git push origin main   # production
git push origin develop  # staging
```

## What to Look For

### ✅ Success Indicators

1. **Continuous Service Availability**
   - Health checks return 200 OK throughout deployment
   - No "connection refused" errors
   - No timeouts

2. **Smooth Container Transition**
   - Old container stays healthy while new builds
   - New container starts and becomes healthy
   - Old container stops only after new is healthy
   - Brief period where both containers run simultaneously

3. **Database Stays Online**
   - Database container never stops
   - Migrations complete successfully
   - No database connection errors in logs

4. **Session Persistence**
   - Redis container never stops
   - User sessions maintained
   - No forced logouts

### ❌ Failure Indicators

1. **Service Interruptions**
   - Health checks return 502, 503, or timeout
   - Connection refused errors
   - Any failed requests during deployment

2. **Container Downtime**
   - All containers stop simultaneously
   - Gap where no web container is running
   - Database restarts during migration

3. **Error Logs**
   ```
   # Check for these error patterns
   docker compose logs web | grep -i "error\|failed\|refused"
   ```

## Understanding the Deployment Flow

### Old Approach (HAD DOWNTIME) ❌

```
1. docker compose down          # ❌ Everything stops
2. Build new image
3. Run migrations               # ❌ Against stopped database!
4. docker compose up -d         # Everything starts
5. Wait for health checks

DOWNTIME: 30-60 seconds while services are down
```

### New Approach (ZERO DOWNTIME) ✅

```
1. Build new image              # Old container still serving traffic
2. Ensure DB/Redis are up       # Don't restart if already running
3. Run migrations               # ✅ Against LIVE database
4. Start new web container      # ✅ Old still serving traffic
5. Wait for new container healthy
6. Docker stops old container   # ✅ After new is ready

DOWNTIME: 0 seconds - seamless transition
```

## Common Issues and Solutions

### Issue: Health Checks Fail During Deployment

**Symptoms:**
- Test script shows failed requests
- 502/503 errors in logs

**Causes:**
1. ❌ Old container stopped before new is ready
2. ❌ Database restarted during migration
3. ❌ Health check timeout too short

**Solutions:**
1. Verify `--no-deps` flag is used in deployment script
2. Check that `docker compose down` is NOT called
3. Increase health check timeout in docker-compose.yml
4. Review deployment workflow logs

### Issue: Database Connection Errors During Migration

**Symptoms:**
- Migration fails with "connection refused"
- Database container shows as restarting

**Cause:**
- Database was stopped before migration ran

**Solution:**
- Ensure deployment script starts DB before running migrations:
  ```bash
  docker compose up -d db redis  # Start first
  docker compose run --rm --no-deps web flask db upgrade  # Then migrate
  ```

### Issue: Sessions Lost During Deployment

**Symptoms:**
- Users forced to log in again after deployment
- Redis container restarted

**Cause:**
- Redis was restarted, losing session data

**Solution:**
- Verify Redis container is never stopped:
  ```bash
  docker compose logs redis | grep "Stopped"  # Should be empty
  ```

## Performance Testing

For load testing under deployment:

```bash
# Install apache bench
sudo apt install apache2-utils

# Generate load during deployment (100 concurrent users, 1000 requests)
ab -n 1000 -c 100 http://localhost:8000/health

# Check results
# Look for: Successful requests = 1000 (100%), 0 failed
```

## Validation Checklist

Before considering zero-downtime deployment verified:

- [ ] Automated test script shows 0 failed requests
- [ ] Manual health check monitoring shows no interruptions
- [ ] Docker container logs show smooth transition
- [ ] Database never restarted
- [ ] Redis never restarted
- [ ] No error spikes in application logs
- [ ] User sessions maintained across deployment
- [ ] Deployment completes in < 90 seconds
- [ ] Health checks pass within 30 seconds of new container start
- [ ] No 502/503 errors in NGINX logs

## Success Criteria

Your zero-downtime deployment is working correctly if:

✅ **99.99% success rate** on automated tests (0 failed requests out of 300+)
✅ **No visible impact** to end users during deployment
✅ **Database and Redis** never restart
✅ **Smooth container transition** in docker ps output
✅ **Clean logs** with no connection errors

## Next Steps

After verifying zero-downtime deployment:

1. **Document the process** - Add runbook entry
2. **Train team members** - Ensure everyone knows how to deploy safely
3. **Set up monitoring** - Alert on deployment failures
4. **Schedule regular tests** - Verify zero-downtime monthly
5. **Consider advanced patterns** - Blue-green, canary deployments

## Additional Resources

- [Docker Compose Rolling Updates](https://docs.docker.com/compose/production/)
- [Health Check Best Practices](https://docs.docker.com/engine/reference/builder/#healthcheck)
- [Zero-Downtime Deployments](https://www.martinfowler.com/bliki/BlueGreenDeployment.html)

---

**Last Updated:** 2025-10-22
**Status:** Production-ready zero-downtime deployment implemented
