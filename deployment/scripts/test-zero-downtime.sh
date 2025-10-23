#!/bin/bash
#
# Zero-Downtime Deployment Test Script
#
# This script simulates user traffic during a deployment to verify
# that zero-downtime deployment is working correctly.
#
# Usage:
#   ./deployment/scripts/test-zero-downtime.sh [production|staging]
#
# What it does:
#   1. Continuously polls the application during deployment
#   2. Records any failed requests (which would indicate downtime)
#   3. Reports success/failure after deployment completes
#

set -e

# Configuration
ENVIRONMENT="${1:-staging}"
TEST_DURATION=300  # 5 minutes
REQUEST_INTERVAL=1  # 1 second between requests

# Environment-specific URLs
if [ "$ENVIRONMENT" = "production" ]; then
    HEALTH_URL="http://localhost:8000/health"
    APP_URL="https://rentflow.cloud"
    ENV_NAME="Production"
elif [ "$ENVIRONMENT" = "staging" ]; then
    HEALTH_URL="http://localhost:9000/health"
    APP_URL="http://localhost:8080"
    ENV_NAME="Staging"
else
    echo "Error: Unknown environment '$ENVIRONMENT'"
    echo "Usage: $0 [production|staging]"
    exit 1
fi

# Output files
LOG_FILE="deployment/zero-downtime-test-$(date +%Y%m%d-%H%M%S).log"
FAILED_REQUESTS=0
TOTAL_REQUESTS=0
START_TIME=$(date +%s)

echo "=========================================="
echo "Zero-Downtime Deployment Test"
echo "=========================================="
echo "Environment: $ENV_NAME"
echo "Health URL: $HEALTH_URL"
echo "Test Duration: ${TEST_DURATION}s"
echo "Request Interval: ${REQUEST_INTERVAL}s"
echo "Log File: $LOG_FILE"
echo "=========================================="
echo ""
echo "🚀 Starting continuous health check monitoring..."
echo "   Deploy your application now in another terminal!"
echo ""
echo "   Production: Push to 'main' branch or run deploy.yml workflow"
echo "   Staging: Push to 'develop' branch or run deploy-staging.yml workflow"
echo ""
echo "Press Ctrl+C to stop the test early"
echo "=========================================="
echo ""

# Initialize log file
echo "Zero-Downtime Deployment Test - $(date)" > "$LOG_FILE"
echo "Environment: $ENV_NAME" >> "$LOG_FILE"
echo "Started at: $(date)" >> "$LOG_FILE"
echo "----------------------------------------" >> "$LOG_FILE"

# Trap Ctrl+C to show results
trap 'show_results' INT TERM

show_results() {
    local end_time=$(date +%s)
    local elapsed=$((end_time - START_TIME))

    echo ""
    echo "=========================================="
    echo "Test Results"
    echo "=========================================="
    echo "Duration: ${elapsed}s"
    echo "Total Requests: $TOTAL_REQUESTS"
    echo "Failed Requests: $FAILED_REQUESTS"

    if [ $TOTAL_REQUESTS -gt 0 ]; then
        local success_rate=$(awk "BEGIN {printf \"%.2f\", (($TOTAL_REQUESTS - $FAILED_REQUESTS) / $TOTAL_REQUESTS) * 100}")
        echo "Success Rate: ${success_rate}%"
    fi

    echo "=========================================="
    echo ""

    if [ $FAILED_REQUESTS -eq 0 ]; then
        echo "✅ SUCCESS: Zero-downtime deployment verified!"
        echo "   No requests failed during the test period."
        echo "   Your deployment strategy is working correctly."
    else
        echo "❌ FAILURE: Downtime detected!"
        echo "   $FAILED_REQUESTS request(s) failed during deployment."
        echo "   This indicates the application experienced downtime."
        echo ""
        echo "Common causes:"
        echo "  - Database was stopped during migration"
        echo "  - Web container was stopped before new one started"
        echo "  - Health checks not passing before traffic switch"
        echo ""
        echo "Review the logs at: $LOG_FILE"
    fi

    echo ""
    echo "Detailed log saved to: $LOG_FILE"
    exit 0
}

# Main monitoring loop
echo "Timestamp,Status,Response_Time,Message" >> "$LOG_FILE"

ELAPSED=0
while [ $ELAPSED -lt $TEST_DURATION ]; do
    TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
    START_REQUEST=$(date +%s%N)

    # Make health check request
    HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "$HEALTH_URL" 2>/dev/null || echo "000")

    END_REQUEST=$(date +%s%N)
    RESPONSE_TIME=$(( (END_REQUEST - START_REQUEST) / 1000000 ))  # Convert to milliseconds

    TOTAL_REQUESTS=$((TOTAL_REQUESTS + 1))

    if [ "$HTTP_CODE" = "200" ]; then
        # Success
        echo -ne "\r[$TIMESTAMP] ✓ Request #${TOTAL_REQUESTS}: HTTP $HTTP_CODE (${RESPONSE_TIME}ms) - Failures: $FAILED_REQUESTS"
        echo "$TIMESTAMP,SUCCESS,$RESPONSE_TIME,HTTP $HTTP_CODE" >> "$LOG_FILE"
    else
        # Failure
        FAILED_REQUESTS=$((FAILED_REQUESTS + 1))
        echo ""
        echo "[$TIMESTAMP] ✗ Request #${TOTAL_REQUESTS}: FAILED (HTTP $HTTP_CODE, ${RESPONSE_TIME}ms)"
        echo "$TIMESTAMP,FAILED,$RESPONSE_TIME,HTTP $HTTP_CODE" >> "$LOG_FILE"
    fi

    sleep $REQUEST_INTERVAL
    ELAPSED=$((ELAPSED + REQUEST_INTERVAL))
done

# Show final results
show_results
