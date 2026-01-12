#!/usr/bin/env python3
"""
Phase 1 Verification: Basic Structure Check
Simple check without imports or Unicode issues
"""

import sys
from pathlib import Path

def main():
    print("=" * 60)
    print("PHASE 1 VERIFICATION - BASIC")
    print("=" * 60)

    checks = []

    # 1. Check directory structure
    base_path = Path("backend/triage-service/src")
    required_dirs = ["api", "services", "models", "utils"]
    required_files = [
        "main.py",
        "api/middleware.py",
        "services/openai_router.py",
        "services/dapr_client.py",
        "services/integration.py",
        "models/schemas.py",
        "models/errors.py"
    ]

    dir_check = all((base_path / d).exists() for d in required_dirs)
    file_check = all((base_path / f).exists() for f in required_files)

    checks.append(("FastAPI Directory Structure", dir_check))
    checks.append(("Core Source Files", file_check))

    # 2. Check requirements.txt
    req_path = Path("backend/triage-service/requirements.txt")
    req_check = req_path.exists()
    checks.append(("Requirements File", req_check))

    # 3. Check main.py content
    main_ok = False
    main_path = Path("backend/triage-service/src/main.py")
    if main_path.exists():
        try:
            content = main_path.read_text(encoding='utf-8', errors='ignore')
            main_ok = all([
                "from fastapi import FastAPI" in content,
                "app = FastAPI" in content,
                "@app.post" in content,
                "middleware" in content.lower()
            ])
        except:
            main_ok = False
    checks.append(("FastAPI Application", main_ok))

    # 4. Check middleware
    middleware_ok = False
    mw_path = Path("backend/triage-service/src/api/middleware.py")
    if mw_path.exists():
        try:
            content = mw_path.read_text(encoding='utf-8', errors='ignore')
            middleware_ok = all([
                "X-Consumer-Username" in content,
                "security_context" in content,
                "X-Student-ID" in content
            ])
        except:
            middleware_ok = False
    checks.append(("Security Middleware", middleware_ok))

    # 5. Check Dapr client
    dapr_ok = False
    dapr_path = Path("backend/triage-service/src/services/dapr_client.py")
    if dapr_path.exists():
        try:
            content = dapr_path.read_text(encoding='utf-8', errors='ignore')
            dapr_ok = all([
                "circuit_breaker" in content.lower(),
                "retry" in content.lower(),
                "exponential" in content.lower()
            ])
        except:
            dapr_ok = False
    checks.append(("Dapr Resilience", dapr_ok))

    # 6. Check schemas
    schema_ok = False
    schema_path = Path("backend/triage-service/src/models/schemas.py")
    if schema_path.exists():
        try:
            content = schema_path.read_text(encoding='utf-8', errors='ignore')
            schema_ok = all([
                "TriageRequest" in content,
                "IntentClassification" in content,
                "RoutingDecision" in content,
                "TriageResponse" in content,
                "pydantic" in content.lower()
            ])
        except:
            schema_ok = False
    checks.append(("Schema Enforcement", schema_ok))

    # 7. Check openai_router
    router_ok = False
    router_path = Path("backend/triage-service/src/services/openai_router.py")
    if router_path.exists():
        try:
            content = router_path.read_text(encoding='utf-8', errors='ignore')
            router_ok = all([
                "OpenAIRouter" in content,
                "classify_intent" in content,
                "skills-first" in content.lower()
            ])
        except:
            router_ok = False
    checks.append(("OpenAI Router", router_ok))

    # 8. Check integration
    integration_ok = False
    integration_path = Path("backend/triage-service/src/services/integration.py")
    if integration_path.exists():
        try:
            content = integration_path.read_text(encoding='utf-8', errors='ignore')
            integration_ok = all([
                "TriageOrchestrator" in content,
                "execute_triage" in content,
                "orchestrate" in content.lower()
            ])
        except:
            integration_ok = False
    checks.append(("Integration Orchestrator", integration_ok))

    # Summary
    print("\n" + "=" * 60)
    print("PHASE 1 RESULTS")
    print("=" * 60)

    all_passed = True
    for name, passed in checks:
        status = "PASS" if passed else "FAIL"
        print(f"{status} | {name}")
        if not passed:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("PHASE 1: BASIC STRUCTURE COMPLETE")
        print("All core files and structure in place")
        return 0
    else:
        print("PHASE 1: INCOMPLETE")
        return 1

if __name__ == "__main__":
    sys.exit(main())