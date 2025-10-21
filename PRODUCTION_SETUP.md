# Production Setup Guide

## Environment Variables Configuration

The `.env` file must exist at the **root level** of your application directory (`/home/ubuntu/rentflow/.env`). This file contains sensitive production secrets required by Docker Compose.

## Location: Industry Best Practice

```
/home/ubuntu/rentflow/
├── .env                          ← Environment file HERE (root level)
├── deployment/
│   └── docker/
│       └── docker-compose.yml    ← Reads .env from root
```

**Why at root level?**
- ✅ Standard Docker Compose convention
- ✅ Easy to find for operators
- ✅ Works with `--env-file .env` flag
- ✅ Consistent with 99% of Docker Compose projects

## Quick Setup on VPS

SSH to your VPS and run these commands:

```bash
# Navigate to the application directory
cd /home/ubuntu/rentflow

# Generate a secure SECRET_KEY
SECRET_KEY=$(python3 -c 'import secrets; print(secrets.token_hex(32))')

# Generate a secure database password
DB_PASSWORD=$(python3 -c 'import secrets; print(secrets.token_urlsafe(32))')

# Create the .env file with production secrets
cat > .env << EOF
# RentFlow Production Environment Variables
# Generated: $(date)

# Database Configuration
POSTGRES_PASSWORD=$DB_PASSWORD
POSTGRES_USER=rentflow_user
POSTGRES_DB=rentflow

# Flask Secret Key
SECRET_KEY=$SECRET_KEY

# Gunicorn Settings
GUNICORN_WORKERS=4
GUNICORN_THREADS=2
GUNICORN_TIMEOUT=120
EOF

# Secure the .env file (only owner can read/write)
chmod 600 .env

# Verify the file was created with correct permissions
echo "✓ .env file created successfully"
ls -lah .env
# Should show: -rw------- (600 permissions - owner only)

# Show the file (SAVE THESE VALUES SOMEWHERE SAFE!)
echo ""
echo "IMPORTANT: Save these credentials in a secure password manager:"
cat .env
```

**Security Note:** The `.env` file should have **600 permissions** (owner read/write only):
```bash
# Check current permissions
ls -l .env
# Should show: -rw------- 1 user user

# If permissions are too open (like 644), fix them:
chmod 600 .env
```

## Alternative: Manual Setup

If you prefer to set specific values manually:

```bash
cd /home/ubuntu/rentflow

# Create .env file
nano .env
```

Add these variables (replace with your own values):

```bash
POSTGRES_PASSWORD=your_secure_database_password_here
POSTGRES_USER=rentflow_user
POSTGRES_DB=rentflow
SECRET_KEY=your_64_character_hex_secret_key_here
GUNICORN_WORKERS=4
GUNICORN_THREADS=2
GUNICORN_TIMEOUT=120
```

Save and exit (`Ctrl+X`, then `Y`, then `Enter`)

```bash
# Secure the file
chmod 600 .env
```

## After Creating .env File

Once the .env file is created, redeploy:

```bash
# Option 1: Trigger GitHub Actions
# (Push any commit from your local machine)

# Option 2: Manual deployment on VPS
cd /home/ubuntu/rentflow
./deploy.sh
```

## Verification

Check that environment variables are loaded:

```bash
# View .env file (WARNING: Shows secrets!)
cat .env

# Verify Docker Compose can read the .env file
cd /home/ubuntu/rentflow
docker compose -f deployment/docker/docker-compose.yml --env-file .env config | grep POSTGRES_PASSWORD

# Should output something like:
#   POSTGRES_PASSWORD: your_password_here
```

## Security Notes

1. **Never commit .env to git** - It's already in .gitignore
2. **Keep .env permissions at 600** - Only owner can read
3. **Store credentials in a password manager** - Save the generated values
4. **Use different secrets for dev/staging/prod** - Never reuse production secrets

## Troubleshooting

If deployment still fails after creating .env:

```bash
# Check if .env exists and has correct permissions
ls -la /home/ubuntu/rentflow/.env
# Should show: -rw------- (600 permissions)

# Verify file contents (WARNING: Shows secrets!)
cat /home/ubuntu/rentflow/.env

# Check Docker Compose can read the .env file
cd /home/ubuntu/rentflow
docker compose -f deployment/docker/docker-compose.yml --env-file .env config
# Should not show any "variable is not set" warnings

# View container logs
docker compose -f deployment/docker/docker-compose.yml --env-file .env logs db

# Check if database container is healthy
docker compose -f deployment/docker/docker-compose.yml --env-file .env ps db
```

## Common Issues

**Issue: "variable is not set" warnings**
- **Cause:** .env file doesn't exist or isn't being read
- **Fix:** Ensure .env is at `/home/ubuntu/rentflow/.env` (root level, not in deployment/ directory)

**Issue: "container is unhealthy"**
- **Cause:** Database started without password, health check fails
- **Fix:** Ensure `POSTGRES_PASSWORD` is set in .env, then restart: `docker compose -f deployment/docker/docker-compose.yml --env-file .env down && ./deploy.sh`

**Issue: "permission denied" reading .env**
- **Cause:** File permissions too restrictive or wrong owner
- **Fix:** `chmod 600 .env` and ensure file owned by user running docker compose
