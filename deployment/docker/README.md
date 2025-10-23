# Docker Build Configuration

This directory contains Docker build assets for the RentFlow application.

## Files

- **Dockerfile** - Production container image definition
- **nginx.conf** - NGINX reverse proxy configuration

**Note**: Docker Compose orchestration files are located at the project root:
- `docker-compose.local.yml` - Local development
- `docker-compose.staging.yml` - Staging environment
- `docker-compose.production.yml` - Production deployment

## Running the Application

### Local Development
```bash
# Start services
docker compose -f docker-compose.local.yml up -d

# View logs
docker compose -f docker-compose.local.yml logs -f

# Stop services
docker compose -f docker-compose.local.yml down
```

### Staging Environment
```bash
docker compose -f docker-compose.staging.yml --env-file .env.staging up -d
```

### Production Environment
```bash
docker compose -f docker-compose.production.yml --env-file .env up -d
```

### Using Helper Script
For production deployments:
```bash
./deploy.sh
```

## Services

### 1. PostgreSQL (db)
- **Image**: postgres:16-alpine
- **Internal Port**: 5432
- **Data**: Persistent volume `postgres_data`
- **Health Check**: Automatic readiness checks

### 2. Redis (redis)
- **Image**: redis:7-alpine
- **Internal Port**: 6379
- **Data**: Persistent volume `redis_data`
- **Purpose**: Rate limiting and caching

### 3. Flask Application (web)
- **Build**: Custom image from Dockerfile
- **Port**: 8000 (exposed to host)
- **Dependencies**: PostgreSQL, Redis
- **Volumes**: instance/, logs/, uploads/

### 4. NGINX (nginx)
- **Image**: nginx:alpine
- **Ports**: 80 (HTTP), 443 (HTTPS)
- **Purpose**: Reverse proxy and SSL termination
- **Config**: deployment/nginx/

## Environment Variables

Create a `.env` file in the project root with:

```bash
# Required
SECRET_KEY=your-secure-random-key
POSTGRES_PASSWORD=your-secure-db-password

# Optional (with defaults)
POSTGRES_DB=rentflow
POSTGRES_USER=rentflow_user
GUNICORN_WORKERS=4
GUNICORN_THREADS=2
```

See `.env.example` for complete configuration options.

## Logging

All services include automatic log rotation:
- **Max Size**: 10MB per file
- **Max Files**: 3 files retained
- **Driver**: json-file

Application logs are stored in `logs/` directory.

## Health Checks

All services include health checks:
- **db**: `pg_isready` command
- **redis**: `redis-cli ping`
- **web**: HTTP request to `/health`
- **nginx**: Inherits from web service

## Troubleshooting

### Check Service Status
```bash
docker compose -f docker-compose.local.yml ps
```

### View Service Logs
```bash
# All services
docker compose -f docker-compose.local.yml logs

# Specific service
docker compose -f docker-compose.local.yml logs web
docker compose -f docker-compose.local.yml logs db
```

### Rebuild After Code Changes
```bash
docker compose -f docker-compose.local.yml up -d --build web
```

### Database Migrations
```bash
docker compose -f docker-compose.local.yml run --rm web flask db upgrade
```

### Access Database
```bash
docker compose -f docker-compose.local.yml exec db psql -U rentflow_user -d rentflow
```

## Path Structure

Docker Compose files are at the project root:

```
re2/                                    # <- Run docker-compose from here
├── docker-compose.local.yml           # <- Local development
├── docker-compose.staging.yml         # <- Staging environment
├── docker-compose.production.yml      # <- Production deployment
├── deployment/
│   ├── docker/
│   │   ├── Dockerfile                 # <- Build configuration
│   │   └── nginx.conf                 # <- NGINX config
│   ├── nginx/                         # <- Mounted to nginx container
│   └── scripts/                       # <- Deployment scripts
├── instance/                          # <- Mounted to web container
├── logs/                              # <- Mounted to web container
└── uploads/                           # <- Mounted to web container
```

## Production Deployment

Production deployment is automated via GitHub Actions:
- Push to `main` branch triggers production deployment
- Push to `develop` branch triggers staging deployment

For manual deployment:

```bash
cd /path/to/rentflow
git pull origin main
./deploy.sh
```

The deployment script provides:
- Pre-deployment checks
- Database backups
- Zero-downtime updates
- Health verification
