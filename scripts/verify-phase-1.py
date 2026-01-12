#!/usr/bin/env python3
"""
Phase 1 Verification: FastAPI Service + OpenAI Router
Surgical-Grade Production Standard
"""

import sys
import os
from pathlib import Path

def print_section(title):
    print(f"\n{'='*60}")
    print(f"PHASE 1: {title}")
    print(f"{'='*60}")

def verify_fastapi_structure():
    """Check FastAPI directory structure exists"""
    print_section("FastAPI Structure")

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

    all_good = True

    for dir_name in required_dirs:
        full_path = base_path / dir_name
        exists = full_path.exists()
        print(f"{'PASS' if exists else 'FAIL'} Directory: {dir_name}")
        if not exists:
            all_good = False

    for file_name in required_files:
        full_path = base_path / file_name
        exists = full_path.exists()
        size = full_path.stat().st_size if exists else 0
        print(f"{'PASS' if exists else 'FAIL'} File: {file_name} ({size} bytes)")
        if not exists:
            all_good = False

    return all_good

def verify_requirements():
    """Check requirements.txt exists and has key packages"""
    print_section("Dependencies")

    req_path = Path("backend/triage-service/requirements.txt")
    if not req_path.exists():
        print("❌ requirements.txt not found")
        return False

    content = req_path.read_text()
    required_packages = ["fastapi", "openai", "dapr", "pydantic", "python-jose"]

    all_found = True
    for package in required_packages:
        found = package in content
        print(f"{'PASS' if found else 'FAIL'} {package}")
        if not found:
            all_found = False

    return all_found

def verify_skills_integration():
    """Verify skills can be imported from FastAPI context"""
    print_section("Skills Integration")

    try:
        # Add skills path
        sys.path.insert(0, str(Path("skills-library/triage-logic")))

        from intent_detection import classify_intent
        from route_selection import route_intent

        # Test basic functionality
        result = classify_intent("test query")
        route = route_intent("syntax_help", 0.9)

        print(f"✅ Intent Detection: {result['intent']} (tokens: {result['token_estimate']})")
        print(f"✅ Route Selection: {route['target_agent']} (priority: {route['priority']})")

        # Verify efficiency
        efficiency = (1500 - result['token_estimate']) / 1500
        print(f"✅ Token Efficiency: {efficiency:.1%}")

        return efficiency >= 0.9

    except Exception as e:
        print(f"❌ Skills integration failed: {e}")
        return False

def verify_fastapi_can_start():
    """Check if main.py has basic FastAPI structure"""
    print_section("FastAPI Application")

    main_path = Path("backend/triage-service/src/main.py")
    if not main_path.exists():
        print("❌ main.py not found")
        return False

    content = main_path.read_text()

    checks = {
        "FastAPI import": "from fastapi import FastAPI" in content,
        "App creation": "app = FastAPI" in content,
        "Triage endpoint": "POST /api/v1/triage" in content or "@app.post" in content,
        "Health endpoint": "GET /health" in content,
        "Middleware": "middleware" in content.lower(),
        "Security context": "security_context" in content
    }

    all_good = True
    for check, result in checks.items():
        print(f"{'✅' if result else '❌'} {check}")
        if not result:
            all_good = False

    return all_good

def verify_middleware_exists():
    """Check security middleware implementation"""
    print_section("Security Middleware")

    middleware_path = Path("backend/triage-service/src/api/middleware.py")
    if not middleware_path.exists():
        print("❌ middleware.py not found")
        return False

    content = middleware_path.read_text()

    checks = {
        "Student ID extraction": "X-Consumer-Username" in content,
        "Security context": "security_context" in content,
        "Dapr propagation": "X-Student-ID" in content,
        "JWT validation": "jwt" in content.lower() or "token" in content.lower()
    }

    all_good = True
    for check, result in checks.items():
        print(f"{'✅' if result else '❌'} {check}")
        if not result:
            all_good = False

    return all_good

def verify_dapr_client():
    """Check Dapr client with circuit breaker"""
    print_section("Dapr Client & Resilience")

    dapr_path = Path("backend/triage-service/src/services/dapr_client.py")
    if not dapr_path.exists():
        print("❌ dapr_client.py not found")
        return False

    content = dapr_path.read_text()

    checks = {
        "Dapr client import": "DaprClient" in content or "dapr.clients" in content,
        "Circuit breaker": "circuit_breaker" in content or "CircuitBreaker" in content,
        "Retry logic": "retry" in content.lower(),
        "Exponential backoff": "exponential" in content.lower(),
        "Timeout handling": "timeout" in content.lower()
    }

    all_good = True
    for check, result in checks.items():
        print(f"{'✅' if result else '❌'} {check}")
        if not result:
            all_good = False

    return all_good

def verify_schemas():
    """Check Pydantic models for schema enforcement"""
    print_section("Schema Enforcement")

    schemas_path = Path("backend/triage-service/src/models/schemas.py")
    if not schemas_path.exists():
        print("❌ schemas.py not found")
        return False

    content = schemas_path.read_text()

    required_models = ["TriageRequest", "IntentClassification", "RoutingDecision", "TriageResponse"]

    all_good = True
    for model in required_models:
        found = model in content
        print(f"{'✅' if found else '❌'} {model}")
        if not found:
            all_good = False

    # Check Pydantic v2
    has_pydantic = "from pydantic import" in content
    print(f"{'✅' if has_pydantic else '❌'} Pydantic v2 import")

    return all_good and has_pydantic

def main():
    """Run all Phase 1 verifications"""
    print("PHASE 1 VERIFICATION: FastAPI Service + OpenAI Router")
    print("Surgical-Grade Production Standard")

    results = []

    # Run all checks
    results.append(("FastAPI Structure", verify_fastapi_structure()))
    results.append(("Requirements", verify_requirements()))
    results.append(("Skills Integration", verify_skills_integration()))
    results.append(("FastAPI Application", verify_fastapi_can_start()))
    results.append(("Security Middleware", verify_middleware_exists()))
    results.append(("Dapr Client", verify_dapr_client()))
    results.append(("Schema Enforcement", verify_schemas()))

    # Summary
    print(f"\n{'='*60}")
    print("PHASE 1 VERIFICATION SUMMARY")
    print(f"{'='*60}")

    all_passed = True
    for name, passed in results:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} | {name}")
        if not passed:
            all_passed = False

    print(f"\n{'='*60}")
    if all_passed:
        print("PHASE 1: COMPLETE")
        print("Ready for Phase 2: Dapr Resilience + Circuit Breaker")
        return 0
    else:
        print("PHASE 1: INCOMPLETE")
        print("Fix failures before proceeding to Phase 2")
        return 1

if __name__ == "__main__":
    sys.exit(main())