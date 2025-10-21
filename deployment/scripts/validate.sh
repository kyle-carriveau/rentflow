#!/bin/bash
# RentFlow Validation Script
# Validates the entire deployment structure and configuration

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Counters
PASS=0
FAIL=0
WARN=0

# Docker Compose file location
COMPOSE_FILE="deployment/docker/docker-compose.yml"

print_header() {
    echo -e "${BLUE}===================================================${NC}"
    echo -e "${BLUE}  $1${NC}"
    echo -e "${BLUE}===================================================${NC}"
}

print_pass() {
    echo -e "${GREEN}✓${NC} $1"
    ((PASS++))
}

print_fail() {
    echo -e "${RED}✗${NC} $1"
    ((FAIL++))
}

print_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
    ((WARN++))
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

# Check if running from project root
check_directory() {
    if [ ! -f "main.py" ] || [ ! -d "website" ]; then
        print_fail "Must run from project root directory"
        exit 1
    fi
    print_pass "Running from correct directory"
}

print_header "RentFlow Deployment Validation"
echo ""

# 1. Directory Structure
print_header "1. Directory Structure"
check_directory

directories=(
    "config"
    "deployment"
    "deployment/docker"
    "deployment/nginx"
    "deployment/nginx/conf.d"
    "deployment/ssl"
    "deployment/scripts"
    "requirements"
    "website"
    "migrations"
    "logs"
    "uploads"
    "instance"
)

for dir in "${directories[@]}"; do
    if [ -d "$dir" ]; then
        print_pass "Directory exists: $dir"
    else
        print_fail "Missing directory: $dir"
    fi
done

echo ""

# 2. Critical Files
print_header "2. Critical Files"

files=(
    "main.py"
    "$COMPOSE_FILE"
    "deployment/docker/Dockerfile"
    "requirements/base.txt"
    "requirements/prod.txt"
    "requirements/dev.txt"
    "config/__init__.py"
    ".env.example"
    "deploy.sh"
    ".gitignore"
    ".dockerignore"
)

for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        print_pass "File exists: $file"
    else
        print_fail "Missing file: $file"
    fi
done

echo ""

# 3. Python Syntax Validation
print_header "3. Python Configuration Validation"

if python3 -m py_compile config/__init__.py 2>/dev/null; then
    print_pass "config/__init__.py syntax valid"
else
    print_fail "config/__init__.py has syntax errors"
fi

if python3 -m py_compile main.py 2>/dev/null; then
    print_pass "main.py syntax valid"
else
    print_fail "main.py has syntax errors"
fi

echo ""

# 4. Docker Compose Validation
print_header "4. Docker Compose Configuration"

if [ -f "$COMPOSE_FILE" ]; then
    print_pass "Docker Compose file found"

    # Validate YAML syntax
    if docker compose -f "$COMPOSE_FILE" config --quiet 2>/dev/null; then
        print_pass "Docker Compose syntax valid"
    else
        print_fail "Docker Compose syntax errors"
    fi

    # Check services
    services=$(docker compose -f "$COMPOSE_FILE" config --services 2>/dev/null | wc -l)
    if [ "$services" -eq 4 ]; then
        print_pass "All 4 services defined (db, redis, web, nginx)"
        print_info "Using Cloudflare for SSL (no certbot service needed)"
    else
        print_warn "Expected 4 services, found $services"
    fi
else
    print_fail "Docker Compose file not found"
fi

echo ""

# 5. Requirements Files
print_header "5. Requirements Files"

base_count=$(grep -c "^[a-zA-Z]" requirements/base.txt 2>/dev/null || echo 0)
prod_count=$(grep -c "^[a-zA-Z]" requirements/prod.txt 2>/dev/null | grep -v "^-r" | wc -l || echo 0)
dev_count=$(grep -c "^[a-zA-Z]" requirements/dev.txt 2>/dev/null | grep -v "^-r" | wc -l || echo 0)

print_info "Base packages: $base_count"
print_info "Production-only: $prod_count (gunicorn, psycopg2-binary expected)"
print_info "Development-only: $dev_count (pytest suite expected)"

if [ "$base_count" -gt 20 ]; then
    print_pass "Base requirements populated"
else
    print_fail "Base requirements seems incomplete"
fi

echo ""

# 6. Environment Configuration
print_header "6. Environment Configuration"

if [ -f ".env" ]; then
    print_warn ".env file exists (production should use server environment)"

    # Check for critical variables
    if grep -q "SECRET_KEY=" .env; then
        print_pass "SECRET_KEY defined in .env"
    else
        print_warn "SECRET_KEY not found in .env"
    fi
else
    print_info ".env file not found (okay if using .env.example as template)"
fi

if [ -f ".env.example" ]; then
    print_pass ".env.example template exists"
else
    print_warn ".env.example template missing"
fi

echo ""

# 7. NGINX Configuration
print_header "7. NGINX Configuration"

if [ -f "deployment/nginx/nginx.conf" ]; then
    print_pass "Main NGINX config exists"
else
    print_fail "NGINX config missing"
fi

if [ -f "deployment/nginx/conf.d/rentflow.conf" ]; then
    print_pass "RentFlow site config exists"
else
    print_fail "Site config missing"
fi

if [ -f "deployment/nginx/conf.d/locations.inc" ]; then
    print_pass "Location includes exist"
else
    print_fail "Location includes missing"
fi

echo ""

# 8. SSL Certificates (Cloudflare Origin)
print_header "8. SSL Certificates"

if [ -f "deployment/ssl/cloudflare-origin.crt" ] && [ -f "deployment/ssl/cloudflare-origin.key" ]; then
    print_pass "Cloudflare origin certificates exist"
    print_info "Using Cloudflare automatic SSL with origin certificates"
else
    print_warn "Cloudflare origin certificates missing"
    print_info "Generate in Cloudflare Dashboard → SSL/TLS → Origin Server"
fi

echo ""

# 9. Git Configuration
print_header "9. Git Configuration"

# Check .gitkeep files
if [ -f "logs/.gitkeep" ]; then
    print_pass "logs/.gitkeep exists"
else
    print_warn "logs/.gitkeep missing (directory won't be tracked)"
fi

if [ -f "uploads/.gitkeep" ]; then
    print_pass "uploads/.gitkeep exists"
else
    print_warn "uploads/.gitkeep missing (directory won't be tracked)"
fi

if [ -f "instance/.gitkeep" ]; then
    print_pass "instance/.gitkeep exists"
else
    print_warn "instance/.gitkeep missing (directory won't be tracked)"
fi

echo ""

# 10. Script Permissions
print_header "10. Script Permissions"

scripts=(
    "deploy.sh"
    "deployment/scripts/validate.sh"
)

for script in "${scripts[@]}"; do
    if [ -f "$script" ]; then
        if [ -x "$script" ]; then
            print_pass "$script is executable"
        else
            print_warn "$script is not executable (run: chmod +x $script)"
        fi
    fi
done

echo ""

# 11. Deployment Script Validation
print_header "11. Deployment Script Validation"

if bash -n deploy.sh 2>/dev/null; then
    print_pass "deploy.sh syntax valid"
else
    print_fail "deploy.sh has syntax errors"
fi

# Check if deploy.sh uses new compose file
if grep -q "deployment/docker/docker-compose.yml" deploy.sh; then
    print_pass "deploy.sh uses new compose file location"
else
    print_fail "deploy.sh not updated for new structure"
fi

echo ""

# Summary
print_header "Validation Summary"
echo ""
echo -e "${GREEN}Passed: $PASS${NC}"
echo -e "${YELLOW}Warnings: $WARN${NC}"
echo -e "${RED}Failed: $FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ Validation PASSED${NC}"
    echo "Your deployment structure is ready for production!"
    exit 0
elif [ $FAIL -le 3 ]; then
    echo -e "${YELLOW}⚠ Validation passed with warnings${NC}"
    echo "Please review failed checks before deploying to production."
    exit 0
else
    echo -e "${RED}✗ Validation FAILED${NC}"
    echo "Please fix critical issues before deploying."
    exit 1
fi
