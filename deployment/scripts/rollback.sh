#!/bin/bash
# RentFlow Rollback Script
# Emergency rollback to old directory structure

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

print_status() {
    echo -e "${GREEN}==>${NC} $1"
}

print_error() {
    echo -e "${RED}ERROR:${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}WARNING:${NC} $1"
}

echo -e "${YELLOW}========================================${NC}"
echo -e "${YELLOW}  RentFlow Emergency Rollback${NC}"
echo -e "${YELLOW}========================================${NC}"
echo ""

print_warning "This script will rollback to the OLD directory structure"
print_warning "This is only for emergency situations"
echo ""

# Check if old files exist
if [ ! -f "docker-compose.yml" ]; then
    print_error "Old docker-compose.yml not found in root directory"
    print_error "Cannot rollback - old structure may have been removed"
    exit 1
fi

print_status "Checking current deployment..."

# Check if services are running with new structure
NEW_RUNNING=false
if docker compose -f deployment/docker/docker-compose.yml ps 2>/dev/null | grep -q "Up"; then
    NEW_RUNNING=true
    print_status "Services running with NEW structure"
fi

# Confirm rollback
echo ""
read -p "Are you sure you want to rollback? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    print_status "Rollback cancelled"
    exit 0
fi

echo ""
print_status "Starting rollback process..."

# Stop new structure services if running
if [ "$NEW_RUNNING" = true ]; then
    print_status "Stopping services using NEW structure..."
    docker compose -f deployment/docker/docker-compose.yml down || print_warning "Could not stop new services"
fi

# Start old structure services
print_status "Starting services with OLD structure..."
docker compose -f docker-compose.yml up -d

# Wait for services
print_status "Waiting for services to start..."
sleep 10

# Check service status
print_status "Checking service status..."
docker compose ps

# Check application health
print_status "Checking application health..."
if curl -f http://localhost:8000/health &> /dev/null; then
    echo ""
    print_status "${GREEN}✓${NC} Rollback successful!"
    print_status "Application is running with OLD structure"
    echo ""
    print_warning "IMPORTANT: Update deployment scripts to use old structure:"
    print_warning "  - Revert deploy.sh changes"
    print_warning "  - Update GitHub Actions workflow"
    print_warning "  - Or fix issues and redeploy new structure"
    echo ""
else
    print_error "Health check failed after rollback!"
    print_status "Showing recent logs..."
    docker compose logs --tail=50 web
    exit 1
fi
