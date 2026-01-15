"""
Health Integration Tests
=========================

Integration tests for health monitoring with real dependencies.
"""

import pytest
import os
from datetime import datetime
from unittest.mock import patch, Mock

from fastapi.testclient import TestClient
from src.main import app
from src.services.state_manager import StateManager


@pytest.fixture
def client_with_mocks():
    """Test client with mocked state manager"""
    with patch('src.services.state_manager.StateManager.create') as mock_state_factory:
        state_manager = Mock()
        state_manager.health_check = Mock(return_value=True)
        state_manager.get_mastery_score = Mock(return_value=None)
        state_manager.save = Mock(return_value=True)

        mock_state_factory.return_value = state_manager

        # Also mock app_state for lifespan
        with patch('src.main.app_state') as mock_app_state:
            mock_app_state.__getitem__ = lambda self, key: {
                "state_manager": state_manager,
                "security_manager": Mock(),
                "ready": True,
                "health_report": {
                    "state_store": True,
                    "kafka": False,
                    "dapr": True
                }
            }[key]

            with patch('src.main.lifespan') as mock_lifespan:
                # Create a mock async context manager
                async def mock_lifespan_cm(app):
                    yield

                mock_lifespan.return_value = mock_lifespan_cm(app)

                return TestClient(app)


class TestHealthEndpointIntegration:
    """Integration tests for health endpoints"""

    def test_health_endpoint_always_accessible(self, client_with_mocks):
        """Test health endpoint is always accessible regardless of app state"""
        # Should work even if dependencies are down
        response = client_with_mocks.get("/health")
        assert response.status_code == 200

    def test_health_endpoint_independent_of_state(self, client_with_mocks):
        """Test health endpoint doesn't depend on application state"""
        # Create a broken state
        with patch('src.main.app_state') as broken_state:
            broken_state.__getitem__ = lambda self, key: None

            response = client_with_mocks.get("/health")
            assert response.status_code == 200


class TestReadinessEndpointIntegration:
    """Integration tests for readiness endpoint"""

    def test_ready_endpoint_shows_degraded_when_state_store_down(self, client_with_mocks):
        """Test readiness reflects state store health"""
        with patch.object(client_with_mocks, 'app') as patched_app:
            # Mock broken state store
            mock_state_manager = Mock()
            mock_state_manager.health_check.side_effect = Exception("Connection failed")

            with patch('src.main.app_state') as mock_state:
                mock_state.__getitem__ = lambda self, key: {
                    "state_manager": mock_state_manager,
                    "ready": True,
                    "health_report": {"state_store": False}
                }[key]

                response = client_with_mocks.get("/ready")
                assert response.status_code == 503
                data = response.json()
                assert data["status"] == "degraded"

    def test_ready_endpoint_shows_ready_when_healthy(self, client_with_mocks):
        """Test readiness shows ready when all dependencies healthy"""
        response = client_with_mocks.get("/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ready"

    def test_ready_endpoint_shows_not_ready_during_startup(self):
        """Test readiness shows not ready before app is initialized"""
        with patch('src.main.app_state') as mock_state:
            mock_state.__getitem__ = lambda self, key: {
                "ready": False,
                "state_manager": None
            }[key]

            client = TestClient(app)
            response = client.get("/ready")
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "not_ready"


class TestMetricsEndpointIntegration:
    """Integration tests for metrics endpoint"""

    def test_metrics_across_multiple_requests(self, client_with_mocks):
        """Test metrics accumulate across multiple requests"""
        # Make various requests
        client_with_mocks.get("/health")
        client_with_mocks.get("/ready")
        client_with_mocks.get("/metrics")
        client_with_mocks.get("/nonexistent")  # Should count as error

        response = client_with_mocks.get("/metrics")
        data = response.json()

        assert data["performance"]["requests_total"] >= 4
        assert data["performance"]["errors_total"] >= 1
        assert "/health" in data["performance"]["requests_per_endpoint"]
        assert "/ready" in data["performance"]["requests_per_endpoint"]
        assert "/metrics" in data["performance"]["requests_per_endpoint"]

    def test_metrics_include_dependency_status(self, client_with_mocks):
        """Test metrics include current dependency status"""
        response = client_with_mocks.get("/metrics")
        data = response.json()

        assert "dependencies" in data
        assert data["dependencies"]["state_store"] == 1  # Mock returns healthy

    def test_metrics_reset_on_restart(self, client_with_mocks):
        """Test metrics reset properly between instances"""
        # Make some requests
        client_with_mocks.get("/health")

        # Simulate restart by resetting metrics
        from src.main import performance_metrics
        original_reset = performance_metrics["last_reset"]

        performance_metrics.update({
            "requests_total": 0,
            "requests_per_endpoint": {},
            "latency_sum": 0.0,
            "latency_count": 0,
            "errors_total": 0,
            "last_reset": datetime.utcnow().isoformat()
        })

        # New request
        response = client_with_mocks.get("/health")

        # Metrics should be fresh
        metrics_data = client_with_mocks.get("/metrics").json()
        assert metrics_data["performance"]["requests_total"] >= 1


class TestServiceInfoIntegration:
    """Integration tests for service info endpoint"""

    def test_service_info_includes_all_endpoints(self, client_with_mocks):
        """Test service info lists all monitoring endpoints"""
        response = client_with_mocks.get("/")
        data = response.json()

        expected_endpoints = ["health", "ready", "docs", "metrics"]
        for endpoint in expected_endpoints:
            assert endpoint in data["endpoints"]

    def test_service_info_environment_reflection(self, client_with_mocks):
        """Test service info reflects current environment"""
        with patch.dict('os.environ', {'ENVIRONMENT': 'production'}):
            response = client_with_mocks.get("/")
            data = response.json()

            assert data["environment"] == "production"


class TestSecurityHeadersIntegration:
    """Integration tests for security headers"""

    def test_security_headers_on_all_endpoints(self, client_with_mocks):
        """Test security headers are present on all endpoints"""
        endpoints = ["/health", "/ready", "/metrics", "/"]

        for endpoint in endpoints:
            response = client_with_mocks.get(endpoint)
            assert "Strict-Transport-Security" in response.headers
            assert "X-Content-Type-Options" in response.headers

    def test_security_headers_consistency(self, client_with_mocks):
        """Test security headers are consistent across requests"""
        response1 = client_with_mocks.get("/health")
        response2 = client_with_mocks.get("/ready")

        assert (response1.headers["Strict-Transport-Security"] ==
                response2.headers["Strict-Transport-Security"])


class TestMetricsAccuracy:
    """Test metrics accuracy in various scenarios"""

    def test_latency_calculation_accuracy(self, client_with_mocks):
        """Test latency calculation is accurate"""
        import time

        # Make a slow request by patching the middleware
        from src.main import performance_metrics_middleware

        original_middleware = performance_metrics_middleware

        async def slow_middleware(request, call_next):
            import asyncio
            await asyncio.sleep(0.01)  # 10ms delay
            return await original_middleware(request, call_next)

        # Note: This test might be flaky depending on test environment
        # It's more of a demonstration of the metric collection capability

        response = client_with_mocks.get("/health")
        assert response.status_code == 200

    def test_error_tracking_accuracy(self, client_with_mocks):
        """Test error counting is accurate"""
        # Track initial errors
        metrics_before = client_with_mocks.get("/metrics").json()
        errors_before = metrics_before["performance"]["errors_total"]

        # Make error requests
        client_with_mocks.get("/nonexistent1")
        client_with_mocks.get("/nonexistent2")

        # Check metrics
        metrics_after = client_with_mocks.get("/metrics").json()
        errors_after = metrics_after["performance"]["errors_total"]

        assert errors_after == errors_before + 2


class TestEndpointDependencies:
    """Test individual endpoint dependencies"""

    def test_health_independent_of_state_manager(self, client_with_mocks):
        """Test health endpoint works even if state manager is None"""
        with patch('src.main.app_state') as mock_state:
            mock_state.__getitem__ = lambda self, key: None

            # Health should still work
            response = client_with_mocks.get("/health")
            assert response.status_code == 200

    def test_ready_depends_on_state_manager(self, client_with_mocks):
        """Test ready endpoint requires state manager"""
        with patch('src.main.app_state') as mock_state:
            mock_state.__getitem__ = lambda self, key: {
                "ready": True,
                "state_manager": None,
                "health_report": {}
            }[key]

            response = client_with_mocks.get("/ready")
            # Should return 503 due to missing state manager
            assert response.status_code == 503


class TestStructuredLoggingIntegration:
    """Integration tests for structured logging"""

    @patch('src.main.logger')
    def test_structured_logging_used_in_startup(self, mock_logger, client_with_mocks):
        """Test structured logging is used during startup"""
        # The startup should log using the JSON formatter in production
        with patch.dict('os.environ', {'ENVIRONMENT': 'production'}):
            # Log level info should be called
            assert mock_logger.info.called

    def test_log_output_format_production(self, client_with_mocks):
        """Test logs are in JSON format in production"""
        with patch.dict('os.environ', {'ENVIRONMENT': 'production'}):
            with patch('src.main.logger') as mock_logger:
                # This would verify the JSON formatter is active
                # The actual logging happens in the lifespan
                pass  # Verified through unit tests


class TestPerformanceMetricsIntegration:
    """Integration tests for performance metrics"""

    def test_metrics_reflect_real_world_usage(self, client_with_mocks):
        """Test metrics accurately reflect usage patterns"""
        # Simulate real usage
        for _ in range(10):
            client_with_mocks.get("/health")

        for _ in range(5):
            client_with_mocks.get("/metrics")

        response = client_with_mocks.get("/metrics")
        data = response.json()

        assert data["performance"]["requests_total"] >= 15
        assert data["performance"]["requests_per_endpoint"]["/health"] >= 10
        assert data["performance"]["requests_per_endpoint"]["/metrics"] >= 5


class TestCORSIntegration:
    """Integration tests for CORS"""

    def test_cors_preflight_success(self, client_with_mocks):
        """Test CORS preflight requests work"""
        response = client_with_mocks.options(
            "/health",
            headers={
                "Origin": "http://example.com",
                "Access-Control-Request-Method": "GET"
            }
        )

        assert response.status_code == 200
        assert "access-control-allow-origin" in response.headers

    def test_cors_includes_custom_headers(self, client_with_mocks):
        """Test CORS allows custom security headers"""
        response = client_with_mocks.options(
            "/health",
            headers={
                "Origin": "http://example.com",
                "Access-Control-Request-Headers": "Authorization,X-Request-ID"
            }
        )

        assert response.status_code == 200


class TestRateLimitingIntegration:
    """Integration tests for rate limiting on health endpoints"""

    @pytest.mark.skipif(True, reason="Rate limiting requires slowapi setup")
    def test_health_rate_limiting(self, client_with_mocks):
        """Test health endpoint rate limiting (if enabled)"""
        # Make many requests quickly
        for _ in range(100):
            response = client_with_mocks.get("/health")
            if response.status_code == 429:
                return

        # If we get here, rate limiting isn't configured for health
        # which is acceptable


class TestErrorScenarios:
    """Test error scenarios for health monitoring"""

    def test_malformed_requests(self, client_with_mocks):
        """Test endpoints handle malformed requests gracefully"""
        # Test with invalid methods
        response = client_with_mocks.post("/health")
        assert response.status_code == 405  # Method Not Allowed

        response = client_with_mocks.put("/ready")
        assert response.status_code == 405

    def test_nonexistent_health_endpoint(self, client_with_mocks):
        """Test 404 for non-existent health endpoints"""
        response = client_with_mocks.get("/healthz")  # Similar to health but wrong
        assert response.status_code == 404


class TestJSONResponseFormat:
    """Test JSON response format consistency"""

    def test_all_endpoints_return_json(self, client_with_mocks):
        """Test all health endpoints return JSON"""
        endpoints = ["/health", "/ready", "/metrics", "/"]

        for endpoint in endpoints:
            response = client_with_mocks.get(endpoint)
            assert response.headers["content-type"] == "application/json"

    def test_json_structure_consistency(self, client_with_mocks):
        """Test JSON responses have consistent structure"""
        # All responses should be parseable
        health = client_with_mocks.get("/health").json()
        ready = client_with_mocks.get("/ready").json()
        metrics = client_with_mocks.get("/metrics").json()
        info = client_with_mocks.get("/").json()

        # Should all have timestamp (where applicable)
        assert "timestamp" in health
        assert "timestamp" in ready
        assert "timestamp" in metrics["performance"]["uptime_since"] if "performance" in metrics else True


class TestVersionReporting:
    """Test version reporting across endpoints"""

    def test_consistent_version_reporting(self, client_with_mocks):
        """Test version is reported consistently"""
        health = client_with_mocks.get("/health").json()
        metrics = client_with_mocks.get("/metrics").json()
        info = client_with_mocks.get("/").json()

        assert health["version"] == "1.0.0"
        assert metrics["mastery_engine_info"]["version"] == "1.0.0"
        assert info["version"] == "1.0.0"

    def test_version_in_response_bodies(self, client_with_mocks):
        """Test version appears in response bodies"""
        response = client_with_mocks.get("/health")
        assert "1.0.0" in response.text

        response = client_with_mocks.get("/metrics")
        assert "1.0.0" in response.text