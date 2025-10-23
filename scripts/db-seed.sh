#!/bin/bash
# Database Seeding Wrapper Script
# Creates comprehensive test data for development and staging environments
#
# Usage:
#   ./scripts/db-seed.sh [environment] [size]
#
# Arguments:
#   environment: local, staging (default: local)
#   size: small, medium, large (default: small)
#
# Examples:
#   ./scripts/db-seed.sh local small
#   ./scripts/db-seed.sh staging medium
#   ./scripts/db-seed.sh local large
#
# ⚠️ WARNING: This will create test data in the target database!
# Production environment is blocked for safety.
#
# Data Size Guidelines:
#   small:  2 companies, ~15 total records
#   medium: 5 companies, ~75 total records
#   large:  10 companies, ~200 total records

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Parse arguments
ENVIRONMENT="${1:-local}"
SIZE="${2:-small}"

# Function to print colored output
print_info() {
    echo -e "${BLUE}ℹ${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(local|staging)$ ]]; then
    print_error "Invalid environment: $ENVIRONMENT"
    echo "Valid environments: local, staging"
    exit 1
fi

# Validate size
if [[ ! "$SIZE" =~ ^(small|medium|large)$ ]]; then
    print_error "Invalid size: $SIZE"
    echo "Valid sizes: small, medium, large"
    exit 1
fi

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required but not found"
    exit 1
fi

# Load environment variables for local
if [ "$ENVIRONMENT" == "local" ]; then
    if [ -f "$PROJECT_ROOT/.env.local" ]; then
        export $(cat "$PROJECT_ROOT/.env.local" | grep -v '^#' | xargs)
    fi
elif [ "$ENVIRONMENT" == "staging" ]; then
    if [ -f "$PROJECT_ROOT/.env.staging" ]; then
        export $(cat "$PROJECT_ROOT/.env.staging" | grep -v '^#' | xargs)
    fi
fi

# Run Python seeding script
python3 "$SCRIPT_DIR/db-seed.py" "$ENVIRONMENT" "$SIZE"

exit $?
