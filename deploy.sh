#!/bin/bash
# RentFlow Deployment Script
# This script deploys the application using Docker Compose

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}==>${NC} $1"
}

print_error() {
    echo -e "${RED}ERROR:${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}WARNING:${NC} $1"
}

# Check if .env file exists
if [ ! -f .env ]; then
    print_error ".env file not found!"
    print_status "Creating .env from .env.example..."
    if [ -f .env.example ]; then
        cp .env.example .env
        print_warning "Please edit .env file with your actual configuration before continuing"
        exit 1
    else
        print_error ".env.example not found!"
        exit 1
    fi
fi

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

print_status "Starting RentFlow deployment..."

# Pull latest changes (if in git repo)
if [ -d .git ]; then
    print_status "Pulling latest changes from git..."
    git pull origin main || print_warning "Could not pull latest changes (continuing anyway)"
fi

# Create backups directory
mkdir -p backups

# Backup PostgreSQL database if running
if docker-compose ps db | grep -q "Up"; then
    BACKUP_FILE="backups/backup-$(date +%Y%m%d-%H%M%S).sql"
    print_status "Backing up PostgreSQL database to $BACKUP_FILE..."
    docker-compose exec -T db pg_dump -U rentflow_user rentflow > "$BACKUP_FILE" || print_warning "Database backup failed (might not exist yet)"
else
    print_warning "Database not running, skipping backup"
fi

# Build Docker images (with cache for faster builds)
print_status "Building Docker images..."
docker-compose build

# Stop web application (but keep DB/Redis running for migrations)
print_status "Stopping web application..."
docker-compose stop web

# Run database migrations
print_status "Running database migrations..."
docker-compose run --rm web flask db upgrade

# Start all services
print_status "Starting all services..."
docker-compose up -d

# Wait for services to start
print_status "Waiting for services to start..."
sleep 10

# Check service status
print_status "Checking service status..."
docker-compose ps

# Check application health
print_status "Checking application health..."
if curl -f http://localhost:8000/health &> /dev/null; then
    print_status "${GREEN}✓${NC} Application is healthy!"
else
    print_error "Application health check failed!"
    print_status "Showing recent logs..."
    docker-compose logs --tail=50 web
    exit 1
fi

# Clean up old images
print_status "Cleaning up old Docker images..."
docker image prune -f

print_status "${GREEN}✓${NC} Deployment completed successfully!"
print_status "Application is running at http://localhost"
print_status "To view logs: docker-compose logs -f"
print_status "To stop: docker-compose down"
