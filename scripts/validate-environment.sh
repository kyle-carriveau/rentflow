#!/bin/bash
# Environment Validation Script
# Validates that an environment is properly configured and ready for deployment
#
# Usage:
#   ./scripts/validate-environment.sh [environment]
#
# Arguments:
#   environment: local, staging, production (default: local)
#
# Examples:
#   ./scripts/validate-environment.sh local
#   ./scripts/validate-environment.sh staging
#   ./scripts/validate-environment.sh production
#
# Exit codes:
#   0 - All checks passed
#   1 - Critical error (environment not ready)
#   2 - Warning (environment may work but has issues)

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
ENVIRONMENT="${1:-local}"

# Counters
CHECKS_PASSED=0
CHECKS_FAILED=0
CHECKS_WARNING=0
TOTAL_CHECKS=0

# Function to print colored output
print_header() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_check() {
    echo -e "${BLUE}→${NC} Checking: $1"
}

print_pass() {
    echo -e "${GREEN}✓${NC} $1"
    CHECKS_PASSED=$((CHECKS_PASSED + 1))
}

print_fail() {
    echo -e "${RED}✗${NC} $1"
    CHECKS_FAILED=$((CHECKS_FAILED + 1))
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
    CHECKS_WARNING=$((CHECKS_WARNING + 1))
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Banner
clear
echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║         ${GREEN}Environment Validation Report${CYAN}                  ║${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
print_info "Environment: ${ENVIRONMENT^^}"
print_info "Date: $(date '+%Y-%m-%d %H:%M:%S')"
print_info "Host: $(hostname)"
echo ""

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(local|staging|production)$ ]]; then
    print_fail "Invalid environment: $ENVIRONMENT"
    echo "Valid environments: local, staging, production"
    exit 1
fi

# Set environment-specific variables
case "$ENVIRONMENT" in
    local)
        COMPOSE_FILE="docker-compose.local.yml"
        ENV_FILE=".env.local"
        REQUIRED_DIRS=("instance" "logs" "uploads" "backups")
        EXPECTED_SERVICES=("web" "db" "redis")
        ;;
    staging)
        COMPOSE_FILE="docker-compose.staging.yml"
        ENV_FILE=".env.staging"
        REQUIRED_DIRS=("instance-staging" "logs-staging" "uploads-staging" "backups")
        EXPECTED_SERVICES=("web" "db" "redis" "nginx")
        ;;
    production)
        if [ -f "docker-compose.production.yml" ]; then
            COMPOSE_FILE="docker-compose.production.yml"
        else
            COMPOSE_FILE="deployment/docker/docker-compose.yml"
        fi
        ENV_FILE=".env.production"
        if [ ! -f "$ENV_FILE" ]; then
            ENV_FILE=".env"
        fi
        REQUIRED_DIRS=("instance" "logs" "uploads" "backups" "deployment/ssl")
        EXPECTED_SERVICES=("web" "db" "redis" "nginx")
        ;;
esac

cd "$PROJECT_ROOT" || exit 1

# ═══════════════════════════════════════════════════════════
# System Requirements
# ═══════════════════════════════════════════════════════════

print_header "System Requirements"

print_check "Docker installation"
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
    print_pass "Docker installed: $DOCKER_VERSION"
else
    print_fail "Docker is not installed"
fi

print_check "Docker Compose installation"
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if docker compose version &> /dev/null; then
    COMPOSE_VERSION=$(docker compose version --short 2>/dev/null || docker compose version | awk '{print $4}')
    print_pass "Docker Compose installed: $COMPOSE_VERSION"
else
    print_fail "Docker Compose is not installed"
fi

print_check "Docker daemon"
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if docker info &> /dev/null; then
    print_pass "Docker daemon is running"
else
    print_fail "Docker daemon is not running"
fi

print_check "Git installation"
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if command -v git &> /dev/null; then
    GIT_VERSION=$(git --version | awk '{print $3}')
    print_pass "Git installed: $GIT_VERSION"
else
    print_warning "Git is not installed (optional for local)"
fi

# ═══════════════════════════════════════════════════════════
# Project Structure
# ═══════════════════════════════════════════════════════════

print_header "Project Structure"

print_check "Docker Compose file"
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if [ -f "$COMPOSE_FILE" ]; then
    print_pass "Compose file found: $COMPOSE_FILE"

    # Validate compose file syntax
    print_check "Compose file syntax"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if docker compose -f "$COMPOSE_FILE" config > /dev/null 2>&1; then
        print_pass "Compose file syntax is valid"
    else
        print_fail "Compose file has syntax errors"
        docker compose -f "$COMPOSE_FILE" config 2>&1 | head -n 5
    fi
else
    print_fail "Compose file not found: $COMPOSE_FILE"
fi

print_check "Environment file"
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if [ -f "$ENV_FILE" ]; then
    print_pass "Environment file found: $ENV_FILE"
else
    if [ "$ENVIRONMENT" == "local" ]; then
        print_warning "Environment file not found: $ENV_FILE (will use defaults)"
        if [ -f "${ENV_FILE}.example" ]; then
            print_info "Create with: cp ${ENV_FILE}.example $ENV_FILE"
        fi
    else
        print_fail "Environment file not found: $ENV_FILE (required)"
    fi
fi

print_check "Required directories"
for dir in "${REQUIRED_DIRS[@]}"; do
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if [ -d "$dir" ]; then
        print_pass "Directory exists: $dir/"
    else
        print_warning "Directory missing: $dir/ (will be created)"
        print_info "Create with: mkdir -p $dir"
    fi
done

# ═══════════════════════════════════════════════════════════
# Environment Variables
# ═══════════════════════════════════════════════════════════

print_header "Environment Variables"

if [ -f "$ENV_FILE" ]; then
    # Load environment file
    export $(cat "$ENV_FILE" | grep -v '^#' | xargs) 2>/dev/null || true

    # Check critical variables
    CRITICAL_VARS=("SECRET_KEY" "DATABASE_URL")
    for var in "${CRITICAL_VARS[@]}"; do
        print_check "$var"
        TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
        if [ -n "${!var}" ]; then
            # Mask the value for security
            MASKED_VALUE="${!var:0:10}..."
            print_pass "$var is set ($MASKED_VALUE)"
        else
            print_fail "$var is not set"
        fi
    done

    # Check optional variables
    OPTIONAL_VARS=("REDIS_URL" "FLASK_ENV" "DEBUG")
    for var in "${OPTIONAL_VARS[@]}"; do
        print_check "$var"
        TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
        if [ -n "${!var}" ]; then
            print_pass "$var is set (${!var})"
        else
            print_warning "$var is not set (optional)"
        fi
    done

    # Production-specific checks
    if [ "$ENVIRONMENT" == "production" ]; then
        print_check "DEBUG mode (should be False in production)"
        TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
        if [ "${DEBUG,,}" == "false" ] || [ -z "$DEBUG" ]; then
            print_pass "DEBUG is disabled"
        else
            print_fail "DEBUG is enabled in production!"
        fi

        print_check "SECRET_KEY strength"
        TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
        if [ ${#SECRET_KEY} -ge 32 ]; then
            print_pass "SECRET_KEY has good length (${#SECRET_KEY} chars)"
        else
            print_warning "SECRET_KEY may be too short (${#SECRET_KEY} chars)"
        fi
    fi
else
    print_warning "Skipping environment variable checks (no env file)"
fi

# ═══════════════════════════════════════════════════════════
# Docker Services
# ═══════════════════════════════════════════════════════════

print_header "Docker Services"

print_check "Service definitions"
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if [ -f "$COMPOSE_FILE" ]; then
    DEFINED_SERVICES=$(docker compose -f "$COMPOSE_FILE" config --services 2>/dev/null || echo "")
    if [ -n "$DEFINED_SERVICES" ]; then
        print_pass "Services defined in compose file:"
        echo "$DEFINED_SERVICES" | while read service; do
            echo "    - $service"
        done

        # Check if expected services are defined
        for service in "${EXPECTED_SERVICES[@]}"; do
            print_check "Service: $service"
            TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
            if echo "$DEFINED_SERVICES" | grep -q "^${service}$"; then
                print_pass "Service '$service' is defined"
            else
                print_warning "Service '$service' not found in compose file"
            fi
        done
    else
        print_fail "No services defined in compose file"
    fi
else
    print_fail "Cannot check services (compose file missing)"
fi

print_check "Running containers"
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if [ -f "$COMPOSE_FILE" ]; then
    RUNNING_SERVICES=$(docker compose -f "$COMPOSE_FILE" ps --services --filter "status=running" 2>/dev/null || echo "")
    if [ -n "$RUNNING_SERVICES" ]; then
        print_pass "Running services:"
        echo "$RUNNING_SERVICES" | while read service; do
            STATUS=$(docker compose -f "$COMPOSE_FILE" ps "$service" --format "{{.Status}}" 2>/dev/null || echo "unknown")
            echo "    - $service: $STATUS"
        done
    else
        print_warning "No containers are running"
        print_info "Start with: make dev-up  OR  docker compose -f $COMPOSE_FILE up -d"
    fi
fi

# ═══════════════════════════════════════════════════════════
# Database Connectivity
# ═══════════════════════════════════════════════════════════

print_header "Database Connectivity"

print_check "Database container"
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if docker compose -f "$COMPOSE_FILE" ps db 2>/dev/null | grep -q "Up"; then
    print_pass "Database container is running"

    print_check "Database connection"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if docker compose -f "$COMPOSE_FILE" exec -T db pg_isready &> /dev/null; then
        print_pass "Database is accepting connections"
    else
        print_fail "Database is not ready"
    fi
else
    print_warning "Database container is not running"
    print_info "Start with: docker compose -f $COMPOSE_FILE up -d db"
fi

# ═══════════════════════════════════════════════════════════
# Redis Connectivity
# ═══════════════════════════════════════════════════════════

print_header "Redis Connectivity"

print_check "Redis container"
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if docker compose -f "$COMPOSE_FILE" ps redis 2>/dev/null | grep -q "Up"; then
    print_pass "Redis container is running"

    print_check "Redis connection"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if docker compose -f "$COMPOSE_FILE" exec -T redis redis-cli ping 2>&1 | grep -q "PONG"; then
        print_pass "Redis is responding"
    else
        print_fail "Redis is not responding"
    fi
else
    print_warning "Redis container is not running"
    print_info "Start with: docker compose -f $COMPOSE_FILE up -d redis"
fi

# ═══════════════════════════════════════════════════════════
# Production-Specific Checks
# ═══════════════════════════════════════════════════════════

if [ "$ENVIRONMENT" == "production" ]; then
    print_header "Production-Specific Checks"

    print_check "SSL certificates"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if [ -d "deployment/ssl" ]; then
        CERT_COUNT=$(find deployment/ssl -name "*.crt" -o -name "*.pem" | wc -l)
        if [ "$CERT_COUNT" -gt 0 ]; then
            print_pass "SSL certificates found ($CERT_COUNT files)"
        else
            print_warning "No SSL certificates found in deployment/ssl/"
            print_info "See DEPLOYMENT.md for SSL setup instructions"
        fi
    else
        print_warning "SSL directory not found: deployment/ssl/"
    fi

    print_check "Backup directory"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if [ -d "backups" ]; then
        BACKUP_COUNT=$(find backups -name "*.sql" 2>/dev/null | wc -l)
        print_pass "Backup directory exists ($BACKUP_COUNT backups)"
    else
        print_warning "Backup directory not found"
    fi

    print_check "NGINX configuration"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if [ -f "deployment/nginx/nginx.conf" ]; then
        print_pass "NGINX config found"
    else
        print_fail "NGINX config not found: deployment/nginx/nginx.conf"
    fi
fi

# ═══════════════════════════════════════════════════════════
# Application Health
# ═══════════════════════════════════════════════════════════

print_header "Application Health"

print_check "Web application container"
TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
if docker compose -f "$COMPOSE_FILE" ps web 2>/dev/null | grep -q "Up"; then
    print_pass "Web application container is running"

    # Determine port based on environment
    case "$ENVIRONMENT" in
        local)
            APP_PORT=5000
            ;;
        staging)
            APP_PORT=8080
            ;;
        production)
            APP_PORT=80
            ;;
    esac

    print_check "Application health endpoint"
    TOTAL_CHECKS=$((TOTAL_CHECKS + 1))
    if curl -f -s "http://localhost:${APP_PORT}/health" > /dev/null 2>&1; then
        print_pass "Application health check passed"
    else
        print_warning "Application health check failed (may still be starting)"
        print_info "Check with: curl http://localhost:${APP_PORT}/health"
    fi
else
    print_warning "Web application container is not running"
fi

# ═══════════════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════════════

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  Validation Summary${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "  Total Checks:    $TOTAL_CHECKS"
echo -e "  ${GREEN}Passed:          $CHECKS_PASSED${NC}"
echo -e "  ${RED}Failed:          $CHECKS_FAILED${NC}"
echo -e "  ${YELLOW}Warnings:        $CHECKS_WARNING${NC}"
echo ""

# Calculate percentage
if [ $TOTAL_CHECKS -gt 0 ]; then
    PASS_PERCENT=$((CHECKS_PASSED * 100 / TOTAL_CHECKS))
    echo "  Success Rate:    ${PASS_PERCENT}%"
    echo ""
fi

# Final verdict
if [ $CHECKS_FAILED -eq 0 ]; then
    if [ $CHECKS_WARNING -eq 0 ]; then
        echo -e "${GREEN}✅ Environment validation PASSED!${NC}"
        echo -e "${GREEN}   The $ENVIRONMENT environment is properly configured.${NC}"
        EXIT_CODE=0
    else
        echo -e "${YELLOW}⚠️  Environment validation passed with WARNINGS${NC}"
        echo -e "${YELLOW}   The $ENVIRONMENT environment may work but has issues.${NC}"
        echo -e "${YELLOW}   Review warnings above and address if needed.${NC}"
        EXIT_CODE=2
    fi
else
    echo -e "${RED}❌ Environment validation FAILED!${NC}"
    echo -e "${RED}   The $ENVIRONMENT environment has critical issues.${NC}"
    echo -e "${RED}   Please fix the failed checks above before deploying.${NC}"
    EXIT_CODE=1
fi

echo ""

exit $EXIT_CODE
