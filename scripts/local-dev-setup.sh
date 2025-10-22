#!/bin/bash
# Local Development Environment Setup Script
# One-command setup for new developers
#
# Usage:
#   ./scripts/local-dev-setup.sh [--seed-data]
#
# Options:
#   --seed-data    Automatically seed database with test data after setup
#   --no-seed      Skip database seeding (default)
#
# This script will:
#   1. Check prerequisites (Docker, Python)
#   2. Create .env.local configuration
#   3. Create necessary directories
#   4. Build and start Docker containers
#   5. Run database migrations
#   6. Optionally seed test data
#   7. Provide access instructions

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
SEED_DATA=false

# Parse arguments
for arg in "$@"; do
    case $arg in
        --seed-data)
            SEED_DATA=true
            shift
            ;;
        --no-seed)
            SEED_DATA=false
            shift
            ;;
        *)
            # Unknown option
            ;;
    esac
done

# Function to print colored output
print_step() {
    echo ""
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  $1${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
}

print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_success() {
    echo -e "${GREEN}✓${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_action() {
    echo -e "${MAGENTA}→${NC} $1"
}

# Error handler
error_exit() {
    print_error "$1"
    echo ""
    print_warning "Setup failed. Please check the error message above."
    print_info "For help, see DEVELOPMENT.md or contact the development team"
    exit 1
}

# Banner
clear
echo ""
echo -e "${CYAN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}║          ${GREEN}RentFlow Local Development Setup${CYAN}              ║${NC}"
echo -e "${CYAN}║                                                            ║${NC}"
echo -e "${CYAN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""
print_info "This script will set up your local development environment"
print_info "Estimated time: 3-5 minutes"
echo ""

# Ask for confirmation
read -p "Continue with setup? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    print_warning "Setup cancelled by user"
    exit 0
fi

# ═══════════════════════════════════════════════════════════
# STEP 1: Check Prerequisites
# ═══════════════════════════════════════════════════════════

print_step "STEP 1: Checking Prerequisites"

# Check Docker
print_action "Checking Docker installation..."
if ! command -v docker &> /dev/null; then
    error_exit "Docker is not installed. Please install Docker Desktop: https://www.docker.com/products/docker-desktop"
fi
DOCKER_VERSION=$(docker --version | awk '{print $3}' | sed 's/,//')
print_success "Docker $DOCKER_VERSION installed"

# Check Docker Compose
print_action "Checking Docker Compose installation..."
if ! docker compose version &> /dev/null; then
    error_exit "Docker Compose is not installed. Please install Docker Desktop which includes Compose."
fi
COMPOSE_VERSION=$(docker compose version | awk '{print $4}')
print_success "Docker Compose $COMPOSE_VERSION installed"

# Check if Docker is running
print_action "Checking if Docker is running..."
if ! docker info &> /dev/null; then
    error_exit "Docker is not running. Please start Docker Desktop."
fi
print_success "Docker daemon is running"

# Check Python
print_action "Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    error_exit "Python 3 is not installed. Please install Python 3.12+: https://www.python.org/downloads/"
fi
PYTHON_VERSION=$(python3 --version | awk '{print $2}')
print_success "Python $PYTHON_VERSION installed"

# Check Git
print_action "Checking Git installation..."
if ! command -v git &> /dev/null; then
    print_warning "Git is not installed (optional but recommended)"
else
    GIT_VERSION=$(git --version | awk '{print $3}')
    print_success "Git $GIT_VERSION installed"
fi

# Check Make (optional)
if command -v make &> /dev/null; then
    MAKE_VERSION=$(make --version | head -n1 | awk '{print $3}')
    print_success "Make $MAKE_VERSION installed (optional)"
else
    print_warning "Make is not installed (optional - enables convenient shortcuts)"
fi

print_success "All required prerequisites are installed!"

# ═══════════════════════════════════════════════════════════
# STEP 2: Environment Configuration
# ═══════════════════════════════════════════════════════════

print_step "STEP 2: Environment Configuration"

cd "$PROJECT_ROOT" || error_exit "Failed to change to project directory"

# Create .env.local if it doesn't exist
if [ -f ".env.local" ]; then
    print_warning ".env.local already exists - skipping creation"
    print_info "To recreate, delete .env.local and run this script again"
else
    print_action "Creating .env.local from template..."
    if [ ! -f ".env.local.example" ]; then
        error_exit ".env.local.example not found!"
    fi
    cp .env.local.example .env.local
    print_success ".env.local created"
    print_info "Using default configuration for local development"
fi

# ═══════════════════════════════════════════════════════════
# STEP 3: Create Required Directories
# ═══════════════════════════════════════════════════════════

print_step "STEP 3: Creating Required Directories"

REQUIRED_DIRS=(
    "instance"
    "logs"
    "uploads"
    "backups"
)

for dir in "${REQUIRED_DIRS[@]}"; do
    if [ ! -d "$dir" ]; then
        print_action "Creating $dir/..."
        mkdir -p "$dir"
        touch "$dir/.gitkeep"
        print_success "Created $dir/"
    else
        print_info "$dir/ already exists"
    fi
done

print_success "All required directories created"

# ═══════════════════════════════════════════════════════════
# STEP 4: Build Docker Images
# ═══════════════════════════════════════════════════════════

print_step "STEP 4: Building Docker Images"

print_info "This may take several minutes on first run..."
print_action "Building containers..."

if docker compose -f docker-compose.local.yml build; then
    print_success "Docker images built successfully"
else
    error_exit "Failed to build Docker images"
fi

# ═══════════════════════════════════════════════════════════
# STEP 5: Start Development Environment
# ═══════════════════════════════════════════════════════════

print_step "STEP 5: Starting Development Environment"

print_action "Starting containers..."

if docker compose -f docker-compose.local.yml up -d; then
    print_success "Containers started successfully"
else
    error_exit "Failed to start containers"
fi

# Wait for database to be ready
print_action "Waiting for database to be ready..."
sleep 5

MAX_RETRIES=30
RETRY_COUNT=0

while ! docker compose -f docker-compose.local.yml exec -T db pg_isready -U rentflow_dev &> /dev/null; do
    RETRY_COUNT=$((RETRY_COUNT + 1))
    if [ $RETRY_COUNT -ge $MAX_RETRIES ]; then
        error_exit "Database failed to start after $MAX_RETRIES attempts"
    fi
    echo -n "."
    sleep 1
done
echo ""
print_success "Database is ready"

# ═══════════════════════════════════════════════════════════
# STEP 6: Initialize Database
# ═══════════════════════════════════════════════════════════

print_step "STEP 6: Initializing Database"

# Check if Flask-Migrate is initialized
print_action "Checking database migration status..."
if docker compose -f docker-compose.local.yml exec -T web test -d migrations; then
    print_info "Migrations directory exists"
else
    print_warning "Migrations directory not found - initializing Flask-Migrate"
    if docker compose -f docker-compose.local.yml exec -T web flask db init; then
        print_success "Flask-Migrate initialized"
    else
        print_warning "Flask-Migrate initialization failed (may already be initialized)"
    fi
fi

# Run migrations
print_action "Running database migrations..."
if docker compose -f docker-compose.local.yml exec -T web flask db upgrade; then
    print_success "Database migrations completed"
else
    error_exit "Failed to run database migrations"
fi

# ═══════════════════════════════════════════════════════════
# STEP 7: Seed Test Data (Optional)
# ═══════════════════════════════════════════════════════════

if [ "$SEED_DATA" = true ]; then
    print_step "STEP 7: Seeding Test Data"

    print_action "Creating test data (small dataset)..."
    if "$SCRIPT_DIR/db-seed.sh" local small; then
        print_success "Test data seeded successfully"
        echo ""
        print_info "Test credentials:"
        echo "  Email:    user1@test.example.com (or any user ID)"
        echo "  Password: TestPassword123!"
    else
        print_warning "Failed to seed test data (you can run 'make dev-db-seed' later)"
    fi
else
    print_info "Skipping test data seeding (use --seed-data flag to seed)"
fi

# ═══════════════════════════════════════════════════════════
# STEP 8: Verify Installation
# ═══════════════════════════════════════════════════════════

print_step "STEP 8: Verifying Installation"

# Check if web container is healthy
print_action "Checking web application health..."
sleep 2

if curl -f http://localhost:5000/health &> /dev/null || curl -f http://localhost:5000/ &> /dev/null; then
    print_success "Web application is running"
else
    print_warning "Web application health check failed (may still be starting)"
fi

# Show container status
print_action "Container status:"
docker compose -f docker-compose.local.yml ps

# ═══════════════════════════════════════════════════════════
# Setup Complete!
# ═══════════════════════════════════════════════════════════

echo ""
echo -e "${GREEN}╔════════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}║              ✓ Setup Complete!                             ║${NC}"
echo -e "${GREEN}║                                                            ║${NC}"
echo -e "${GREEN}╚════════════════════════════════════════════════════════════╝${NC}"
echo ""

print_success "Your local development environment is ready!"
echo ""

echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  Access Your Application${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "  🌐 Web Application:    http://localhost:5000"
echo "  🐘 PostgreSQL:         localhost:5432"
echo "  📮 Redis:              localhost:6379"
echo ""

if [ "$SEED_DATA" = true ]; then
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${CYAN}  Test Credentials${NC}"
    echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
    echo ""
    echo "  Email:    user1@test.example.com"
    echo "  Password: TestPassword123!"
    echo ""
fi

echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  Useful Commands${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""

if command -v make &> /dev/null; then
    echo "  make dev-logs           # View application logs"
    echo "  make dev-shell          # Access web container shell"
    echo "  make dev-shell-db       # Access database shell"
    echo "  make dev-test           # Run tests"
    echo "  make dev-db-seed        # Seed test data"
    echo "  make dev-down           # Stop environment"
    echo "  make dev-restart        # Restart environment"
    echo "  make help               # Show all available commands"
else
    echo "  docker compose -f docker-compose.local.yml logs -f    # View logs"
    echo "  docker compose -f docker-compose.local.yml exec web bash   # Shell access"
    echo "  docker compose -f docker-compose.local.yml down       # Stop environment"
    echo ""
    echo "  💡 Tip: Install 'make' for convenient shortcuts!"
fi

echo ""
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${CYAN}  Next Steps${NC}"
echo -e "${CYAN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "  1. Open http://localhost:5000 in your browser"
echo "  2. Read DEVELOPMENT.md for detailed development guide"
echo "  3. Read BRANCHING.md for Git workflow"
if [ "$SEED_DATA" = false ]; then
    echo "  4. Run 'make dev-db-seed' to add test data"
fi
echo ""

print_info "For help and documentation, see:"
echo "  - DEVELOPMENT.md  (Development guide)"
echo "  - BRANCHING.md    (Git workflow)"
echo "  - DEPLOYMENT.md   (Deployment guide)"
echo "  - README.md       (Project overview)"
echo ""

print_success "Happy coding! 🚀"
echo ""

exit 0
