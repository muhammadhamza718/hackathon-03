#!/bin/bash
#
# Mastery Engine Health Check Script
# ================================
# Kubernetes health check script for liveness and readiness probes
# Handles both liveness and readiness checks based on K8S probe type

set -euo pipefail

# Configuration
SERVICE_NAME="mastery-engine"
NAMESPACE="${NAMESPACE:-learnflow}"
PORT="${PORT:-8005}"
TIMEOUT="${TIMEOUT:-5}"
MAX_RETRIES="${MAX_RETRIES:-3}"
WAIT_BETWEEN_RETRIES="${WAIT_BETWEEN_RETRIES:-2}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $(date '+%Y-%m-%d %H:%M:%S') - $1"
}

# Determine probe type from environment (used by Kubernetes)
PROBE_TYPE="${1:-}"

# Local service URL for checks
SERVICE_URL="http://localhost:${PORT}"

# Function to check service health
check_service_health() {
    local url="$1"
    local endpoint="$2"
    local description="$3"

    log_info "Checking $description at ${url}${endpoint}"

    response=$(curl -s \
        --max-time "$TIMEOUT" \
        --connect-timeout "$TIMEOUT" \
        -w "%{http_code}" \
        "${url}${endpoint}" \
        -o /dev/null 2>/dev/null || echo "000")

    if [[ "$response" == "200" ]]; then
        log_info "✓ $description check PASSED (HTTP $response)"
        return 0
    else
        log_error "✗ $description check FAILED (HTTP $response)"
        return 1
    fi
}

# Function to check detailed readiness (includes dependencies)
check_readiness_detailed() {
    local url="$1"

    log_info "Running comprehensive readiness check..."

    # Check /ready endpoint which verifies dependencies
    response=$(curl -s \
        --max-time "$TIMEOUT" \
        --connect-timeout "$TIMEOUT" \
        -w "%{http_code}" \
        -o /tmp/ready_response.json \
        "${url}/ready" 2>/dev/null || echo "000")

    if [[ "$response" == "200" ]]; then
        log_info "✓ Service ready check PASSED"

        # Parse the response for dependency details
        if command -v jq >/dev/null 2>&1; then
            dependencies=$(jq -r '.dependencies | keys[]' /tmp/ready_response.json 2>/dev/null || echo "")
            for dep in $dependencies; do
                status=$(jq -r ".dependencies.\"$dep\"" /tmp/ready_response.json)
                if [[ "$status" == "true" ]]; then
                    log_info "  ✓ Dependency $dep: HEALTHY"
                else
                    log_warn "  ⚠ Dependency $dep: UNHEALTHY"
                fi
            done
        fi

        rm -f /tmp/ready_response.json
        return 0
    else
        log_error "✗ Service ready check FAILED (HTTP $response)"

        # Try to get error details
        curl -s --max-time "$TIMEOUT" "${url}/ready" 2>/dev/null | head -200
        return 1
    fi
}

# Function to check liveness (basic service is running)
check_liveness() {
    local url="$1"

    log_info "Running liveness check..."

    # Use /health for liveness (lightweight)
    if check_service_health "$url" "/health" "liveness"; then
        log_info "✓ Liveness probe PASSED"
        return 0
    else
        log_error "✗ Liveness probe FAILED"
        return 1
    fi
}

# Function to check readiness (service + dependencies)
check_readiness() {
    local url="$1"

    log_info "Running readiness check..."

    # First check basic health
    if ! check_service_health "$url" "/health" "basic health"; then
        return 1
    fi

    # Then check comprehensive readiness
    if check_readiness_detailed "$url"; then
        log_info "✓ Readiness probe PASSED"
        return 0
    else
        log_error "✗ Readiness probe FAILED"
        return 1
    fi
}

# Function to check metrics endpoint
check_metrics() {
    local url="$1"

    log_info "Running metrics check..."

    if check_service_health "$url" "/metrics" "metrics endpoint"; then
        log_info "✓ Metrics endpoint accessible"
        return 0
    else
        log_warn "⚠ Metrics endpoint not accessible (may be optional)"
        return 0  # Don't fail readiness if metrics fail
    fi
}

# Function to check service info
check_service_info() {
    local url="$1"

    log_info "Retrieving service info..."

    response=$(curl -s \
        --max-time "$TIMEOUT" \
        --connect-timeout "$TIMEOUT" \
        "${url}/" 2>/dev/null || echo "")

    if [[ -n "$response" ]]; then
        log_info "Service info:"
        echo "$response" | sed 's/^/  /'
        return 0
    else
        log_warn "Could not retrieve service info"
        return 1
    fi
}

# Main execution based on probe type or arguments
main() {
    log_info "Mastery Engine Health Check Script"
    log_info "=================================="
    log_info "Probe Type: ${PROBE_TYPE:-manual}"
    log_info "Service URL: ${SERVICE_URL}"
    log_info ""

    # Wait for service to be available
    log_info "Waiting for service to be available on ${SERVICE_URL}..."
    retry_count=0
    while [[ $retry_count -lt $MAX_RETRIES ]]; do
        if curl -s --max-time 2 "${SERVICE_URL}/health" >/dev/null 2>&1; then
            log_info "Service is responding"
            break
        fi
        retry_count=$((retry_count + 1))
        if [[ $retry_count -lt $MAX_RETRIES ]]; then
            log_warn "Service not ready, retrying in ${WAIT_BETWEEN_RETRIES}s... ($retry_count/$MAX_RETRIES)"
            sleep "$WAIT_BETWEEN_RETRIES"
        fi
    done

    if [[ $retry_count -eq $MAX_RETRIES ]]; then
        log_error "Service did not become ready after $MAX_RETRIES attempts"
        exit 1
    fi

    # Execute appropriate checks based on probe type
    case "${PROBE_TYPE}" in
        "liveness")
            check_liveness "$SERVICE_URL"
            ;;
        "readiness")
            check_readiness "$SERVICE_URL"
            ;;
        "startup")
            # Startup probe checks if service can start successfully
            check_liveness "$SERVICE_URL" && check_readiness "$SERVICE_URL"
            ;;
        "metrics")
            check_metrics "$SERVICE_URL"
            ;;
        "info")
            check_service_info "$SERVICE_URL"
            ;;
        "")
            # Default: run all checks (for manual testing)
            log_info "Running comprehensive health check..."

            check_liveness "$SERVICE_URL"
            liveness_ok=$?

            check_readiness "$SERVICE_URL"
            readiness_ok=$?

            check_metrics "$SERVICE_URL"
            metrics_ok=$?

            check_service_info "$SERVICE_URL"
            info_ok=$?

            echo ""
            log_info "=== SUMMARY ==="

            if [[ $liveness_ok -eq 0 ]]; then
                log_info "✓ Liveness: PASS"
            else
                log_error "✗ Liveness: FAIL"
            fi

            if [[ $readiness_ok -eq 0 ]]; then
                log_info "✓ Readiness: PASS"
            else
                log_error "✗ Readiness: FAIL"
            fi

            if [[ $metrics_ok -eq 0 ]]; then
                log_info "✓ Metrics: PASS"
            else
                log_warn "⚠ Metrics: WARN"
            fi

            if [[ $info_ok -eq 0 ]]; then
                log_info "✓ Info: PASS"
            else
                log_warn "⚠ Info: WARN"
            fi

            # Overall exit code
            if [[ $liveness_ok -eq 0 && $readiness_ok -eq 0 ]]; then
                log_info "Overall: HEALTHY"
                exit 0
            else
                log_error "Overall: UNHEALTHY"
                exit 1
            fi
            ;;
        *)
            log_error "Unknown probe type: $PROBE_TYPE"
            log_info "Valid types: liveness, readiness, startup, metrics, info"
            exit 1
            ;;
    esac
}

# Handle termination signals for clean exit
cleanup() {
    log_info "Cleaning up..."
    exit 143  # 128 + 15 (SIGTERM)
}

trap cleanup SIGTERM SIGINT

# Run main function
main "$@"
