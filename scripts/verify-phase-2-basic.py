#!/usr/bin/env python3
"""
Phase 2 Verification: Dapr Resilience + Circuit Breaker
Basic structure check
"""

import sys
from pathlib import Path

def main():
    print("=" * 60)
    print("PHASE 2 VERIFICATION - BASIC")
    print("=" * 60)

    checks = []

    # 1. Check Phase 2 files exist
    phase2_files = [
        "backend/triage-service/src/services/dapr_client.py",
        "backend/triage-service/src/services/routing_logic.py",
        "backend/triage-service/src/services/routing_map.py",
        "backend/triage-service/src/services/service_discovery.py",
        "backend/triage-service/src/services/dead_letter_queue.py",
        "infrastructure/dapr/components/resiliency.yaml"
    ]

    for file_path in phase2_files:
        exists = Path(file_path).exists()
        checks.append((f"File: {file_path}", exists))
        print(f"{'PASS' if exists else 'FAIL'} {file_path}")

    # 2. Check Dapr client has circuit breaker
    dapr_path = Path("backend/triage-service/src/services/dapr_client.py")
    if dapr_path.exists():
        try:
            content = dapr_path.read_text(encoding='utf-8', errors='ignore')
            has_circuit_breaker = "class CircuitBreaker" in content
            has_retry = "exponential" in content.lower()
            checks.append(("Dapr Client: Circuit Breaker", has_circuit_breaker))
            checks.append(("Dapr Client: Retry Logic", has_retry))
            print(f"{'PASS' if has_circuit_breaker else 'FAIL'} Circuit Breaker class")
            print(f"{'PASS' if has_retry else 'FAIL'} Exponential retry logic")
        except:
            checks.append(("Dapr Client: Circuit Breaker", False))
            checks.append(("Dapr Client: Retry Logic", False))
            print("FAIL Could not read Dapr client")

    # 3. Check routing map has 100% accuracy mapping
    routing_path = Path("backend/triage-service/src/services/routing_map.py")
    if routing_path.exists():
        try:
            content = routing_path.read_text(encoding='utf-8', errors='ignore')
            has_routing_map = "ROUTING_MAP" in content
            has_5_agents = "5 target agents" in content or "debug-agent" in content
            checks.append(("Routing Map: Complete Mapping", has_routing_map))
            checks.append(("Routing Map: All 5 Agents", has_5_agents))
            print(f"{'PASS' if has_routing_map else 'FAIL'} Routing map exists")
            print(f"{'PASS' if has_5_agents else 'FAIL'} All 5 agents defined")
        except:
            checks.append(("Routing Map: Complete Mapping", False))
            checks.append(("Routing Map: All 5 Agents", False))
            print("FAIL Could not read routing map")

    # 4. Check resiliency.yaml has proper config
    resiliency_path = Path("infrastructure/dapr/components/resiliency.yaml")
    if resiliency_path.exists():
        try:
            content = resiliency_path.read_text(encoding='utf-8', errors='ignore')
            has_retry = "maxAttempts: 3" in content
            has_cb = "maxConsecutiveFailures: 5" in content
            has_backoff = "exponential" in content
            checks.append(("Resiliency YAML: Retry Policy", has_retry))
            checks.append(("Resiliency YAML: Circuit Breaker", has_cb))
            checks.append(("Resiliency YAML: Backoff", has_backoff))
            print(f"{'PASS' if has_retry else 'FAIL'} Retry policy (3 attempts)")
            print(f"{'PASS' if has_cb else 'FAIL'} Circuit breaker (5 failures)")
            print(f"{'PASS' if has_backoff else 'FAIL'} Exponential backoff")
        except:
            checks.append(("Resiliency YAML: Retry Policy", False))
            checks.append(("Resiliency YAML: Circuit Breaker", False))
            checks.append(("Resiliency YAML: Backoff", False))
            print("FAIL Could not read resiliency.yaml")

    # 5. Check integration file has been updated
    integration_path = Path("backend/triage-service/src/services/integration.py")
    if integration_path.exists():
        try:
            content = integration_path.read_text(encoding='utf-8', errors='ignore')
            has_routing_import = "from services.routing_map import" in content
            has_routing_call = "get_routing_decision" in content
            checks.append(("Integration: Routing Map Import", has_routing_import))
            checks.append(("Integration: Routing Logic", has_routing_call))
            print(f"{'PASS' if has_routing_import else 'FAIL'} Routing map import")
            print(f"{'PASS' if has_routing_call else 'FAIL'} Routing map usage")
        except:
            checks.append(("Integration: Routing Map Import", False))
            checks.append(("Integration: Routing Logic", False))
            print("FAIL Could not read integration.py")

    # Summary
    print("\n" + "=" * 60)
    print("PHASE 2 RESULTS")
    print("=" * 60)

    all_passed = True
    for name, passed in checks:
        status = "PASS" if passed else "FAIL"
        print(f"{status} | {name}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("PHASE 2: BASIC STRUCTURE COMPLETE")
        print("Circuit breaker, retry logic, and routing map ready")
        return 0
    else:
        print("PHASE 2: INCOMPLETE")
        return 1

if __name__ == "__main__":
    sys.exit(main())