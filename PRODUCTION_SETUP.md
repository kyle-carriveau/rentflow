# Production Setup Guide

## Critical: Environment Variables Configuration

Your deployment is failing because the `.env` file is missing on the VPS. This file contains sensitive production secrets required by Docker Compose.

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

# Secure the .env file (only owner can read)
chmod 600 .env

# Verify the file was created
echo "✓ .env file created successfully"
ls -lah .env

# Show the file (SAVE THESE VALUES SOMEWHERE SAFE!)
echo ""
echo "IMPORTANT: Save these credentials in a secure password manager:"
cat .env
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
# This should show your variables (be careful, this reveals secrets!)
cat .env

# Verify Docker Compose can read them
docker compose -f deployment/docker/docker-compose.yml config | grep POSTGRES_PASSWORD
```

## Security Notes

1. **Never commit .env to git** - It's already in .gitignore
2. **Keep .env permissions at 600** - Only owner can read
3. **Store credentials in a password manager** - Save the generated values
4. **Use different secrets for dev/staging/prod** - Never reuse production secrets

## Troubleshooting

If deployment still fails after creating .env:

```bash
# Check if .env exists
ls -la /home/ubuntu/rentflow/.env

# Verify file contents (WARNING: Shows secrets!)
cat /home/ubuntu/rentflow/.env

# Check Docker Compose can read it
cd /home/ubuntu/rentflow
docker compose -f deployment/docker/docker-compose.yml config

# View container logs
docker compose -f deployment/docker/docker-compose.yml logs db
```

## GitHub Secrets Alternative

Instead of storing .env on VPS, you can use GitHub Secrets:

1. Go to GitHub Repository → Settings → Secrets → Actions
2. Add these secrets:
   - `POSTGRES_PASSWORD`
   - `SECRET_KEY`
   - `POSTGRES_USER`
   - `POSTGRES_DB`

3. Update `.github/workflows/deploy.yml` to create .env during deployment:

```yaml
- name: Create .env file
  run: |
    echo "POSTGRES_PASSWORD=${{ secrets.POSTGRES_PASSWORD }}" > .env
    echo "SECRET_KEY=${{ secrets.SECRET_KEY }}" >> .env
    echo "POSTGRES_USER=${{ secrets.POSTGRES_USER }}" >> .env
    echo "POSTGRES_DB=${{ secrets.POSTGRES_DB }}" >> .env
    chmod 600 .env
```

This approach keeps secrets in GitHub and creates .env during each deployment.
