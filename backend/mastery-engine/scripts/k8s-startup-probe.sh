#!/bin/bash
#
# Kubernetes Startup Probe Script
# ==============================
# Used by Kubernetes startupProbe to determine when the application has started successfully
# This is more lenient than readiness/liveness probes during initial startup

set -euo pipefail

# Configuration
PORT="${PORT:-8005}"
SERVICE_URL="http://localhost:${PORT}"
MAX_STARTUP_TIME="${MAX_STARTUP_TIME:-120}"  # Maximum time to wait for startup (seconds)
CHECK_INTERVAL="${CHECK_INTERVAL:-5}"        # How often to check (seconds)
MAX_RETRIES="${MAX_RETRIES:-5}"             # Retries per health check attempt

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[STARTUP-PROBE]${NC} $(date '+%H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[STARTUP-PROBE]${NC} $(date '+%H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[STARTUP-PROBE]${NC} $(date '+%H:%M:%S') - $1"
}

# Function to check if service is ready
check_service_ready() {
    local url="$1"

    # Check basic health endpoint
    response=$(curl -s \
        --max-time 5 \
        --connect-timeout 3 \
        -w "%{http_code}" \
        "${url}/health" \
        -o /dev/null 2>/dev/null || echo "000")

    if [[ "$response" == "200" ]]; then
        # Also check ready endpoint to ensure dependencies are healthy
        ready_response=$(curl -s \
            --max-time 5 \
            --connect-timeout 3 \
            -w "%{http_code}" \
            "${url}/ready" \
            -o /tmp/ready.json 2>/dev/null || echo "000")

        if [[ "$ready_response" == "200" ]]; then
            # Check if state store is healthy in the response
            if command -v jq >/dev/null 2>&1; then
                state_store=$(jq -r '.dependencies.state_store' /tmp/ready.json 2>/dev/null || echo "false")
                if [[ "$state_store" == "true" ]]; then
                    rm -f /tmp/ready.json
                    return 0
                else
                    log_warn "State store not yet healthy"
                    rm -f /tmp/ready.json
                    return 1
                fi
            else
                # If jq not available, just check HTTP status
                rm -f /tmp/ready.json
                return 0
            fi
        fi
    fi

    return 1
}

# Main startup probe logic
main() {
    log_info "Starting Kubernetes startup probe"
    log_info "Service URL: ${SERVICE_URL}"
    log_info "Max startup time: ${MAX_STARTUP_TIME}s"
    log_info "Check interval: ${CHECK_INTERVAL}s"
    log_info ""

    local start_time=$(date +%s)
    local attempt=1

    while true; do
        local current_time=$(date +%s)
        local elapsed=$((current_time - start_time))

        if [[ $elapsed -gt $MAX_STARTUP_TIME ]]; then
            log_error "Startup timeout exceeded (${MAX_STARTUP_TIME}s)"
            log_error "Application failed to start within expected time"
            exit 1
        fi

        log_info "Startup check #$attempt (elapsed: ${elapsed}s)..."

        # Try multiple times for each check to handle temporary failures
        local check_success=false
        for retry in $(seq 1 $MAX_RETRIES); do
            if check_service_ready "$SERVICE_URL"; then
                check_success=true
                break
            fi

            if [[ $retry -lt $MAX_RETRIES ]]; then
                log_warn "Check failed, retrying in 1s... ($retry/$MAX_RETRIES)"
                sleep 1
            fi
        done

        if [[ "$check_success" == "true" ]]; then
            log_info "✓ Service is ready and dependencies are healthy"
            log_info "✓ Startup probe PASSED after ${elapsed}s"
            log_info "✓ Application is ready to accept traffic"
            exit 0
        else
            log_warn "Check failed, retrying in ${CHECK_INTERVAL}s..."
            sleep "$CHECK_INTERVAL"
            attempt=$((attempt + 1))
        fi
    done
}

# Handle signals
cleanup() {
    log_info "Startup probe interrupted"
    exit 143
}

trap cleanup SIGTERM SIGINT

# Run main function
main "$@"
