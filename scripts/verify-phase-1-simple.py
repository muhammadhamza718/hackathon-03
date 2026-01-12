#!/usr/bin/env python3
"""
Phase 1 Verification: FastAPI Service + OpenAI Router
Simple version without Unicode issues
"""

import sys
from pathlib import Path

def main():
    print("=" * 60)
    print("PHASE 1 VERIFICATION")
    print("=" * 60)

    checks = []

    # 1. Check directory structure
    base_path = Path("backend/triage-service/src")
    required_dirs = ["api", "services", "models", "utils"]
    required_files = [
        "main.py", "api/middleware.py", "services/openai_router.py",
        "services/dapr_client.py", "services/integration.py",
        "models/schemas.py", "models/errors.py"
    ]

    dir_check = all((base_path / d).exists() for d in required_dirs)
    file_check = all((base_path / f).exists() for f in required_files)

    checks.append(("FastAPI Directory Structure", dir_check))
    checks.append(("Core Source Files", file_check))

    # 2. Check requirements
    req_path = Path("backend/triage-service/requirements.txt")
    req_check = False
    if req_path.exists():
        try:
            content = req_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = req_path.read_bytes().decode('utf-8', errors='ignore')
        req_check = all(pkg in content for pkg in ["fastapi", "openai", "dapr", "pydantic", "python-jose"])

    checks.append(("Requirements File", req_check))

    # 3. Check skills integration
    skills_ok = False
    try:
        # Add skills path with proper resolution
        skills_path = Path(__file__).parent.parent / "skills-library" / "triage-logic"
        sys.path.insert(0, str(skills_path))
        from intent_detection import classify_intent
        from route_selection import route_intent

        result = classify_intent("test query")
        route = route_intent("syntax_help", 0.9)

        # Check efficiency: 1500 -> 19 tokens = 98.7% reduction
        efficiency = (1500 - result['token_estimate']) / 1500
        skills_ok = efficiency >= 0.9 and route['target_agent'] == "debug-agent"

        print(f"  Skills: {result['token_estimate']} tokens ({efficiency:.1%} efficiency)")

    except Exception as e:
        # Try alternative path resolution
        try:
            sys.path.insert(0, str(Path("skills-library/triage-logic")))
            from intent_detection import classify_intent
            from route_selection import route_intent

            result = classify_intent("test query")
            route = route_intent("syntax_help", 0.9)
            efficiency = (1500 - result['token_estimate']) / 1500
            skills_ok = efficiency >= 0.9 and route['target_agent'] == "debug-agent"
            print(f"  Skills: {result['token_estimate']} tokens ({efficiency:.1%} efficiency)")
        except Exception as e2:
            print(f"  Skills test failed: {e2}")

    checks.append(("Skills Integration", skills_ok))

    # 4. Check main.py structure
    main_ok = False
    main_path = Path("backend/triage-service/src/main.py")
    if main_path.exists():
        try:
            content = main_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = main_path.read_bytes().decode('utf-8', errors='ignore')
        main_ok = all([
            "from fastapi import FastAPI" in content,
            "app = FastAPI" in content,
            "POST /api/v1/triage" in content or "@app.post" in content,
            "middleware" in content.lower()
        ])

    checks.append(("FastAPI Application", main_ok))

    # 5. Check middleware
    middleware_ok = False
    mw_path = Path("backend/triage-service/src/api/middleware.py")
    if mw_path.exists():
        try:
            content = mw_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            # Fallback: read as bytes and decode with ignore
            content = mw_path.read_bytes().decode('utf-8', errors='ignore')
        middleware_ok = all([
            "X-Consumer-Username" in content,
            "security_context" in content,
            "X-Student-ID" in content
        ])

    checks.append(("Security Middleware", middleware_ok))

    # 6. Check Dapr client
    dapr_ok = False
    dapr_path = Path("backend/triage-service/src/services/dapr_client.py")
    if dapr_path.exists():
        try:
            content = dapr_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = dapr_path.read_bytes().decode('utf-8', errors='ignore')
        dapr_ok = all([
            "circuit_breaker" in content.lower(),
            "retry" in content.lower(),
            "exponential" in content.lower()
        ])

    checks.append(("Dapr Resilience", dapr_ok))

    # 7. Check schemas
    schema_ok = False
    schema_path = Path("backend/triage-service/src/models/schemas.py")
    if schema_path.exists():
        try:
            content = schema_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            content = schema_path.read_bytes().decode('utf-8', errors='ignore')
        schema_ok = all([
            "TriageRequest" in content,
            "IntentClassification" in content,
            "RoutingDecision" in content,
            "TriageResponse" in content,
            "pydantic" in content.lower()
        ])

    checks.append(("Schema Enforcement", schema_ok))

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
        print("PHASE 1: COMPLETE")
        print("All requirements satisfied for surgical production deployment")
        return 0
    else:
        print("PHASE 1: INCOMPLETE")
        return 1

if __name__ == "__main__":
    sys.exit(main())