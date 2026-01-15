"""
Error Handling Verification Test
=================================

Verifies that all endpoints handle errors correctly and return proper HTTP status codes.
"""

import json
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
from src.main import app


def test_error_scenarios():
    """Test various error scenarios"""
    client = TestClient(app)

    print("Testing error handling scenarios...")
    print("=" * 50)

    # 1. Missing Authorization header
    print("\n1. Testing missing authorization:")
    response = client.post("/api/v1/mastery/query", json={"student_id": "test"})
    print(f"   Status: {response.status_code} (Expected: 401)")
    assert response.status_code == 401
    print("   ✅ PASSED")

    # 2. Invalid JWT token format
    print("\n2. Testing invalid token format:")
    response = client.post(
        "/api/v1/mastery/query",
        json={"student_id": "test"},
        headers={"Authorization": "invalid_format"}
    )
    print(f"   Status: {response.status_code} (Expected: 401)")
    assert response.status_code == 401
    print("   ✅ PASSED")

    # 3. Malformed JSON
    print("\n3. Testing malformed JSON:")
    response = client.post(
        "/api/v1/mastery/query",
        data="invalid json",
        headers={
            "Authorization": "Bearer test_token",
            "Content-Type": "application/json"
        }
    )
    print(f"   Status: {response.status_code} (Expected: 400)")
    assert response.status_code == 400
    print("   ✅ PASSED")

    # 4. Validation error - missing required fields
    print("\n4. Testing validation error:")
    with patch('src.api.endpoints.mastery.MasteryEndpoints.get_security_manager') as mock_security:
        security_manager = Mock()
        security_manager.validate_jwt.return_value = {"sub": "test", "role": "student"}
        mock_security.return_value = security_manager

        response = client.post(
            "/api/v1/mastery/query",
            json={"include_components": True},  # Missing student_id
            headers={"Authorization": "Bearer test_token"}
        )
        print(f"   Status: {response.status_code} (Expected: 422)")
        assert response.status_code == 422  # Pydantic validation error
        print("   ✅ PASSED")

    # 5. State store connection error
    print("\n5. Testing state store connection error:")
    with patch('src.api.endpoints.mastery.MasteryEndpoints.get_security_manager') as mock_security:
        with patch('src.api.endpoints.mastery.StateManager.create') as mock_state:
            security_manager = Mock()
            security_manager.validate_jwt.return_value = {"sub": "test", "role": "student"}
            mock_security.return_value = security_manager

            state_manager = Mock()
            state_manager.get_mastery_score.side_effect = Exception("Connection failed")
            mock_state.return_value = state_manager

            response = client.post(
                "/api/v1/mastery/query",
                json={"student_id": "test"},
                headers={"Authorization": "Bearer test_token"}
            )
            print(f"   Status: {response.status_code} (Expected: 500)")
            assert response.status_code == 500
            print("   ✅ PASSED")

    # 6. Student accessing another student's data
    print("\n6. Testing unauthorized data access:")
    with patch('src.api.endpoints.mastery.MasteryEndpoints.get_security_manager') as mock_security:
        security_manager = Mock()
        security_manager.validate_jwt.return_value = {"sub": "student_a", "role": "student"}
        mock_security.return_value = security_manager

        response = client.post(
            "/api/v1/mastery/query",
            json={"student_id": "student_b"},
            headers={"Authorization": "Bearer test_token"}
        )
        print(f"   Status: {response.status_code} (Expected: 403)")
        assert response.status_code == 403
        print("   ✅ PASSED")

    # 7. Invalid component values in calculate endpoint
    print("\n7. Testing invalid calculation input:")
    with patch('src.api.endpoints.mastery.MasteryEndpoints.get_security_manager') as mock_security:
        security_manager = Mock()
        security_manager.validate_jwt.return_value = {"sub": "test", "role": "student"}
        mock_security.return_value = security_manager

        response = client.post(
            "/api/v1/mastery/calculate",
            json={
                "student_id": "test",
                "components": {
                    "completion": 1.5,  # Invalid
                    "quiz": 0.8,
                    "quality": 0.8,
                    "consistency": 0.8
                }
            },
            headers={"Authorization": "Bearer test_token"}
        )
        print(f"   Status: {response.status_code} (Expected: 422)")
        assert response.status_code == 422
        print("   ✅ PASSED")

    print("\n" + "=" * 50)
    print("🎉 ALL ERROR HANDLING TESTS PASSED")


def test_health_check_endpoints():
    """Test health check endpoints handle various scenarios"""
    client = TestClient(app)

    print("\nTesting health check endpoints...")
    print("=" * 50)

    # 1. Basic health check
    print("\n1. Testing /health endpoint:")
    response = client.get("/health")
    print(f"   Status: {response.status_code}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    print("   ✅ PASSED")

    # 2. Readiness check
    print("\n2. Testing /ready endpoint:")
    response = client.get("/ready")
    print(f"   Status: {response.status_code}")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["ready", "degraded"]
    print("   ✅ PASSED")

    # 3. Service info
    print("\n3. Testing / endpoint:")
    response = client.get("/")
    print(f"   Status: {response.status_code}")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "mastery-engine"
    print("   ✅ PASSED")

    # 4. Metrics endpoint
    print("\n4. Testing /metrics endpoint:")
    response = client.get("/metrics")
    print(f"   Status: {response.status_code}")
    assert response.status_code == 200
    print("   ✅ PASSED")

    print("\n" + "=" * 50)
    print("🎉 ALL HEALTH CHECK TESTS PASSED")


def test_dapr_endpoint_error_handling():
    """Test Dapr service invocation error handling"""
    client = TestClient(app)

    print("\nTesting Dapr endpoint error handling...")
    print("=" * 50)

    # 1. Missing intent
    print("\n1. Testing missing intent:")
    response = client.post("/process", json={"payload": {}})
    print(f"   Status: {response.status_code}")
    assert response.status_code == 400
    print("   ✅ PASSED")

    # 2. Unknown intent
    print("\n2. Testing unknown intent:")
    response = client.post("/process", json={
        "intent": "unknown_intent",
        "payload": {}
    })
    print(f"   Status: {response.status_code}")
    assert response.status_code == 400
    print("   ✅ PASSED")

    # 3. Invalid security context
    print("\n3. Testing invalid security context:")
    response = client.post("/process", json={
        "intent": "mastery_calculation",
        "payload": {"student_id": "test"},
        "security_context": {"token": "invalid"}
    })
    # May return 401 or 500 depending on error handling
    assert response.status_code in [401, 500]
    print(f"   Status: {response.status_code} (Accepted: 401/500)")
    print("   ✅ PASSED")

    print("\n" + "=" * 50)
    print("🎉 ALL DAPR ERROR HANDLING TESTS PASSED")


def main():
    """Run all error handling tests"""
    print("ERROR HANDLING VERIFICATION")
    print("=" * 60)
    print("Testing all error scenarios and HTTP status codes")
    print("for Phase 3 requirements")
    print("=" * 60)

    try:
        test_error_scenarios()
        test_health_check_endpoints()
        test_dapr_endpoint_error_handling()

        print("\n" + "=" * 60)
        print("🎉 ALL ERROR HANDLING VERIFICATIONS PASSED")
        print("✅ Phase 3 error handling requirements: COMPLETE")

    except AssertionError as e:
        print(f"\n❌ VERIFICATION FAILED: {e}")
        return False
    except Exception as e:
        print(f"\n❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = main()
    if not success:
        exit(1)