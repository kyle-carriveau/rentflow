# Docker Deployment Configuration

This directory contains all Docker-related files for the RentFlow application.

## Files

- **Dockerfile** - Production container image definition
- **docker-compose.yml** - Multi-service orchestration configuration
- **.dockerignore** - Files to exclude from Docker build context

## Running the Application

### From Project Root (Recommended)
```bash
# Start services
docker-compose -f deployment/docker/docker-compose.yml up -d

# View logs
docker-compose -f deployment/docker/docker-compose.yml logs -f

# Stop services
docker-compose -f deployment/docker/docker-compose.yml down

# Rebuild and restart
docker-compose -f deployment/docker/docker-compose.yml up -d --build
```

### Using Helper Script
Use the deployment script from project root:
```bash
./deployment/scripts/deploy.sh
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
docker-compose -f deployment/docker/docker-compose.yml ps
```

### View Service Logs
```bash
# All services
docker-compose -f deployment/docker/docker-compose.yml logs

# Specific service
docker-compose -f deployment/docker/docker-compose.yml logs web
docker-compose -f deployment/docker/docker-compose.yml logs db
```

### Rebuild After Code Changes
```bash
docker-compose -f deployment/docker/docker-compose.yml up -d --build web
```

### Database Migrations
```bash
docker-compose -f deployment/docker/docker-compose.yml run --rm web flask db upgrade
```

### Access Database
```bash
docker-compose -f deployment/docker/docker-compose.yml exec db psql -U rentflow_user -d rentflow
```

## Path Structure

The docker-compose.yml expects to be run from the project root:

```
re2/                                    # <- Run docker-compose from here
├── deployment/
│   ├── docker/
│   │   ├── Dockerfile
│   │   ├── docker-compose.yml         # <- Using -f flag
│   │   └── .dockerignore
│   ├── nginx/                         # <- Mounted to nginx container
│   └── ssl/                           # <- SSL certificates
├── instance/                          # <- Mounted to web container
├── logs/                              # <- Mounted to web container
└── uploads/                           # <- Mounted to web container
```

## Production Deployment

For production deployments, use the GitHub Actions workflow or the deployment script:

```bash
cd /path/to/rentflow
git pull origin main
./deployment/scripts/deploy.sh
```

See `deployment/scripts/deploy.sh` for automated deployment with:
- Pre-deployment checks
- Database backups
- Zero-downtime updates
- Health verification
