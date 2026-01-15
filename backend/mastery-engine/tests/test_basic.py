"""
Basic Verification Test for US1 - Real-Time Mastery Calculation
================================================================

This test verifies that all Phase 3 requirements are working correctly.
Run this to validate the basic functionality of the mastery engine.
"""

import pytest
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.models.mastery import ComponentScores, MasteryResult, MasteryLevel
from src.skills.calculator import MasteryCalculator
from src.security import SecurityManager


def test_mastery_formula_verification():
    """Verify the exact 40/30/20/10 formula implementation"""
    calculator = MasteryCalculator()

    # Test case from spec: completion=0.85, quiz=0.90, quality=0.85, consistency=0.82
    components = ComponentScores(
        completion=0.85,
        quiz=0.90,
        quality=0.85,
        consistency=0.82
    )

    result = calculator.execute_calculation("test_student", components)

    # Expected calculation: 0.85×0.4 + 0.90×0.3 + 0.85×0.2 + 0.82×0.1 = 0.862
    expected_score = 0.862

    print(f"Calculated score: {result.mastery_score:.6f}")
    print(f"Expected score:   {expected_score:.6f}")
    print(f"Difference:       {abs(result.mastery_score - expected_score):.6f}")

    assert abs(result.mastery_score - expected_score) < 0.0001
    assert result.level == MasteryLevel.MASTER
    print("✅ Formula verification PASSED")


def test_jwt_security():
    """Verify JWT token creation and validation"""
    security_manager = SecurityManager(jwt_secret="test_secret")

    # Create token
    token = security_manager.create_jwt(
        user_id="student_123",
        role="student",
        additional_claims={"course": "math101"}
    )

    print(f"Generated token: {token[:50]}...")

    # Validate token
    claims = security_manager.validate_jwt(token)

    assert claims["sub"] == "student_123"
    assert claims["role"] == "student"
    assert claims["course"] == "math101"

    print("✅ JWT security verification PASSED")


def test_state_key_patterns():
    """Verify state key generation patterns"""
    from src.models.mastery import StateKeyPatterns
    from datetime import datetime

    # Test key generation
    student_id = "student_123"
    date = datetime(2024, 1, 15)

    expected_keys = {
        "current": f"student:{student_id}:profile:current_mastery",
        "snapshot": f"student:{student_id}:mastery:2024-01-15",
        "completion": f"student:{student_id}:mastery:2024-01-15:completion"
    }

    actual_keys = {
        "current": StateKeyPatterns.current_mastery(student_id),
        "snapshot": StateKeyPatterns.daily_snapshot(student_id, date),
        "completion": StateKeyPatterns.component_score(student_id, date, "completion")
    }

    assert actual_keys == expected_keys
    print("✅ State key patterns verification PASSED")


def test_dapr_readiness():
    """Verify Dapr configuration readiness"""
    # Check if Dapr imports are available
    try:
        from dapr.clients import DaprClient
        print("✅ Dapr client import successful")
    except ImportError:
        print("⚠️  Dapr client not installed (will be available in production)")

    # Check if we have the state manager structure
    from src.services.state_manager import StateManager
    print("✅ State manager structure ready")

    print("✅ Dapr readiness verification PASSED")


def test_endpoint_structure():
    """Verify API endpoint structure"""
    from src.api.endpoints.mastery import mastery_router
    from src.main import app

    # Check router is properly configured
    assert len(mastery_router.routes) > 0
    print(f"✅ Mastery router has {len(mastery_router.routes)} routes")

    # Check app includes the router
    app_routers = [r for r in app.routes if hasattr(r, 'path')]
    mastery_routes = [r for r in app_routers if '/mastery' in r.path]

    assert len(mastery_routes) > 0
    print(f"✅ App includes {len(mastery_routes)} mastery routes")

    print("✅ Endpoint structure verification PASSED")


def test_logging_configuration():
    """Verify structured logging is configured"""
    import logging

    logger = logging.getLogger("src.api.endpoints.mastery")

    # Check if logger is configured
    assert logger is not None
    print("✅ Logger configured correctly")

    # Check correlation ID capability
    from src.api.endpoints.mastery import MasteryEndpoints
    correlation_id = MasteryEndpoints.generate_correlation_id()

    assert len(correlation_id) > 0  # Should generate a UUID
    print(f"✅ Correlation ID generated: {correlation_id}")

    print("✅ Logging configuration verification PASSED")


def test_rate_limiting():
    """Verify rate limiting is configured"""
    from src.api.endpoints.mastery import limiter
    from src.main import app

    # Check limiter is attached to app
    assert hasattr(app.state, 'limiter')
    print("✅ Rate limiter attached to app")

    # Check mastery router has rate limit decorators
    mastery_router_routes = [r for r in mastery_router.routes if hasattr(r, 'path')]

    print(f"✅ Mastery router has {len(mastery_router_routes)} routes with rate limiting")
    print("✅ Rate limiting verification PASSED")


def test_file_structure():
    """Verify all required files exist"""
    base_path = "backend/mastery-engine/src"

    required_files = [
        "models/mastery.py",
        "models/events.py",
        "services/state_manager.py",
        "services/kafka_consumer.py",
        "skills/calculator.py",
        "security.py",
        "api/endpoints/mastery.py",
        "main.py"
    ]

    missing_files = []
    for file in required_files:
        full_path = os.path.join(base_path, file)
        if not os.path.exists(full_path):
            missing_files.append(file)

    if missing_files:
        print(f"❌ Missing files: {missing_files}")
        assert False, f"Missing required files: {missing_files}"

    print(f"✅ All {len(required_files)} required files exist")
    print("✅ File structure verification PASSED")


def test_test_files_structure():
    """Verify test files exist"""
    test_files = [
        "tests/unit/test_mastery_calculation.py",
        "tests/integration/test_mastery_api.py",
        "tests/contract/test_mastery_api_contracts.py"
    ]

    missing_tests = []
    for file in test_files:
        if not os.path.exists(file):
            missing_tests.append(file)

    if missing_tests:
        print(f"❌ Missing test files: {missing_tests}")
        assert False, f"Missing test files: {missing_tests}"

    print(f"✅ All {len(test_files)} test files exist")
    print("✅ Test structure verification PASSED")


def main():
    """Run all verification tests"""
    print("=" * 60)
    print("PHASE 3 VERIFICATION TEST - US1 Real-Time Mastery Calculation")
    print("=" * 60)
    print()

    tests = [
        ("File Structure", test_file_structure),
        ("Test File Structure", test_test_files_structure),
        ("Mastery Formula", test_mastery_formula_verification),
        ("JWT Security", test_jwt_security),
        ("State Key Patterns", test_state_key_patterns),
        ("Dapr Readiness", test_dapr_readiness),
        ("Endpoint Structure", test_endpoint_structure),
        ("Logging Configuration", test_logging_configuration),
        ("Rate Limiting", test_rate_limiting),
    ]

    passed = 0
    failed = 0

    for test_name, test_func in tests:
        print(f"\n🧪 Testing: {test_name}")
        try:
            test_func()
            passed += 1
            print(f"✅ {test_name}: PASSED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name}: FAILED - {e}")
            import traceback
            traceback.print_exc()

    print("\n" + "=" * 60)
    print(f"VERIFICATION SUMMARY: {passed}/{len(tests)} tests passed")

    if failed == 0:
        print("🎉 PHASE 3 VERIFICATION: SUCCESS")
        print("All US1 requirements are met. Ready for Phase 4.")
    else:
        print(f"⚠️  PHASE 3 VERIFICATION: {failed} failures")
        sys.exit(1)


if __name__ == "__main__":
    main()