"""
Health Endpoint Unit Tests
===========================

Unit tests for health monitoring endpoints and structured logging.
"""

import pytest
import json
import logging
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from fastapi.testclient import TestClient
from src.main import app, JSONFormatter, performance_metrics


@pytest.fixture
def client():
    """Test client for health endpoint tests"""
    return TestClient(app)


class TestHealthEndpoint:
    """Test /health endpoint"""

    def test_health_endpoint_returns_200(self, client):
        """Test health endpoint returns 200 status"""
        response = client.get("/health")

        assert response.status_code == 200

    def test_health_endpoint_structure(self, client):
        """Test health endpoint response structure"""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert "timestamp" in data
        assert "version" in data
        assert "service" in data

    def test_health_endpoint_content(self, client):
        """Test health endpoint returns expected content"""
        response = client.get("/health")
        data = response.json()

        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert data["service"] == "mastery-engine"
        assert data["timestamp"] is not None

    def test_health_endpoint_timestamp_format(self, client):
        """Test health endpoint timestamp is valid ISO format"""
        response = client.get("/health")
        data = response.json()

        # Should be parseable as ISO format
        timestamp = data["timestamp"]
        assert datetime.fromisoformat(timestamp.replace('Z', '+00:00'))


class TestReadinessEndpoint:
    """Test /ready endpoint"""

    def test_ready_endpoint_ready_state(self, client):
        """Test ready endpoint when application is ready"""
        with patch('src.main.app_state') as mock_app_state:
            mock_app_state.__getitem__ = lambda self, key: {
                "ready": True,
                "state_manager": Mock(health_check=AsyncMock(return_value=True)),
                "health_report": {"state_store": True, "kafka": False, "dapr": True}
            }[key]

            response = client.get("/ready")
            assert response.status_code == 200

            data = response.json()
            assert data["status"] == "ready"

    def test_ready_endpoint_not_ready(self, client):
        """Test ready endpoint when application is not ready"""
        with patch('src.main.app_state') as mock_app_state:
            mock_app_state.__getitem__ = lambda self, key: {
                "ready": False,
                "state_manager": None,
                "health_report": {}
            }[key]

            response = client.get("/ready")
            assert response.status_code == 503

            data = response.json()
            assert data["status"] == "not_ready"

    def test_ready_endpoint_degraded_state(self, client):
        """Test ready endpoint when dependencies are degraded"""
        with patch('src.main.app_state') as mock_app_state:
            mock_state_manager = Mock()
            mock_state_manager.health_check.side_effect = Exception("Connection failed")

            mock_app_state.__getitem__ = lambda self, key: {
                "ready": True,
                "state_manager": mock_state_manager,
                "health_report": {"state_store": False, "kafka": False, "dapr": False}
            }[key]

            response = client.get("/ready")
            assert response.status_code == 503

            data = response.json()
            assert data["status"] == "degraded"
            assert data["dependencies"]["state_store"] is False

    def test_ready_endpoint_response_structure(self, client):
        """Test ready endpoint response structure"""
        with patch('src.main.app_state') as mock_app_state:
            mock_app_state.__getitem__ = lambda self, key: {
                "ready": True,
                "state_manager": Mock(health_check=AsyncMock(return_value=True)),
                "health_report": {"state_store": True, "kafka": False, "dapr": True}
            }[key]

            response = client.get("/ready")
            data = response.json()

            required_fields = ["status", "dependencies", "timestamp", "version", "environment"]
            for field in required_fields:
                assert field in data

            assert "state_store" in data["dependencies"]
            assert "kafka" in data["dependencies"]
            assert "dapr" in data["dependencies"]


class TestMetricsEndpoint:
    """Test /metrics endpoint"""

    def test_metrics_endpoint_returns_200(self, client):
        """Test metrics endpoint returns 200"""
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_endpoint_structure(self, client):
        """Test metrics endpoint response structure"""
        response = client.get("/metrics")
        data = response.json()

        assert "mastery_engine_info" in data
        assert "up" in data
        assert "performance" in data
        assert "dependencies" in data

    def test_metrics_endpoint_content(self, client):
        """Test metrics endpoint returns expected content"""
        response = client.get("/metrics")
        data = response.json()

        assert data["mastery_engine_info"]["version"] == "1.0.0"
        assert data["up"] == 1
        assert data["performance"]["requests_total"] == 0  # Fresh metrics
        assert "state_store" in data["dependencies"]

    def test_metrics_with_requests(self, client):
        """Test metrics reflects actual request data"""
        # Make some requests first
        client.get("/health")
        client.get("/metrics")

        response = client.get("/metrics")
        data = response.json()

        # Should have recorded some requests
        assert data["performance"]["requests_total"] >= 1
        assert "/health" in data["performance"]["requests_per_endpoint"]
        assert "/metrics" in data["performance"]["requests_per_endpoint"]

    def test_metrics_average_latency(self, client):
        """Test metrics calculates average latency"""
        # Make requests to generate metrics
        for _ in range(5):
            client.get("/health")

        response = client.get("/metrics")
        data = response.json()

        assert data["performance"]["average_latency_ms"] >= 0
        assert data["performance"]["latency_count"] >= 5


class TestServiceInfoEndpoint:
    """Test / endpoint"""

    def test_service_info_returns_200(self, client):
        """Test service info endpoint returns 200"""
        response = client.get("/")
        assert response.status_code == 200

    def test_service_info_structure(self, client):
        """Test service info response structure"""
        response = client.get("/")
        data = response.json()

        required_fields = ["name", "version", "environment", "description", "endpoints"]
        for field in required_fields:
            assert field in data

    def test_service_info_content(self, client):
        """Test service info returns expected content"""
        response = client.get("/")
        data = response.json()

        assert data["name"] == "mastery-engine"
        assert data["version"] == "1.0.0"
        assert "mastery" in data["description"].lower()
        assert "health" in data["endpoints"]
        assert "ready" in data["endpoints"]


class TestJSONFormatter:
    """Test structured JSON logging formatter"""

    def test_json_formatter_basic(self):
        """Test JSON formatter with basic log record"""
        formatter = JSONFormatter()

        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=100,
            msg="Test message",
            args=(),
            exc_info=None
        )

        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        assert parsed["level"] == "INFO"
        assert parsed["logger"] == "test.logger"
        assert parsed["message"] == "Test message"
        assert "timestamp" in parsed

    def test_json_formatter_with_correlation_id(self):
        """Test JSON formatter with correlation ID"""
        formatter = JSONFormatter()

        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=100,
            msg="Test message",
            args=(),
            exc_info=None
        )
        setattr(record, 'correlation_id', 'abc-123')
        setattr(record, 'endpoint', '/test')
        setattr(record, 'user_id', 'user_123')

        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        assert parsed["correlation_id"] == "abc-123"
        assert parsed["endpoint"] == "/test"
        assert parsed["user_id"] == "user_123"

    def test_json_formatter_with_exception(self):
        """Test JSON formatter with exception info"""
        formatter = JSONFormatter()

        try:
            raise ValueError("Test error")
        except:
            exc_info = True

        record = logging.LogRecord(
            name="test.logger",
            level=logging.ERROR,
            pathname="test.py",
            lineno=100,
            msg="Error occurred",
            args=(),
            exc_info=exc_info
        )

        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        assert "exception" in parsed
        assert "ValueError" in parsed["exception"]

    def test_json_formatter_handles_non_json_serializable(self):
        """Test JSON formatter handles non-serializable objects"""
        formatter = JSONFormatter()

        record = logging.LogRecord(
            name="test.logger",
            level=logging.INFO,
            pathname="test.py",
            lineno=100,
            msg="Test with {obj}",
            args=({"obj": object()},),
            exc_info=None
        )

        # Should not raise exception
        formatted = formatter.format(record)
        parsed = json.loads(formatted)

        assert "message" in parsed


class TestPerformanceMetricsMiddleware:
    """Test performance metrics middleware"""

    def test_middleware_tracks_request_count(self, client):
        """Test middleware tracks total requests"""
        initial_count = performance_metrics["requests_total"]

        # Make some requests
        for _ in range(3):
            client.get("/health")

        assert performance_metrics["requests_total"] == initial_count + 3

    def test_middleware_tracks_per_endpoint(self, client):
        """Test middleware tracks requests per endpoint"""
        client.get("/health")
        client.get("/metrics")
        client.get("/health")

        metrics = performance_metrics["requests_per_endpoint"]
        assert metrics["/health"] == 2
        assert metrics["/metrics"] == 1

    def test_middleware_tracks_latency(self, client):
        """Test middleware tracks latency metrics"""
        initial_count = performance_metrics["latency_count"]
        initial_sum = performance_metrics["latency_sum"]

        client.get("/health")

        assert performance_metrics["latency_count"] == initial_count + 1
        assert performance_metrics["latency_sum"] > initial_sum

    def test_middleware_tracks_errors(self, client):
        """Test middleware tracks error count"""
        initial_errors = performance_metrics["errors_total"]

        # Make a request that returns 404
        client.get("/nonexistent")

        assert performance_metrics["errors_total"] == initial_errors + 1

    def test_middleware_resets_on_startup(self):
        """Test metrics are initialized properly"""
        assert performance_metrics["requests_total"] >= 0
        assert performance_metrics["errors_total"] >= 0
        assert performance_metrics["latency_sum"] >= 0.0
        assert performance_metrics["latency_count"] >= 0
        assert "requests_per_endpoint" in performance_metrics
        assert "last_reset" in performance_metrics


class TestSecurityHeadersMiddleware:
    """Test security headers middleware"""

    def test_security_headers_present(self, client):
        """Test security headers are added to responses"""
        response = client.get("/health")

        headers = response.headers

        # Standard security headers
        assert "Strict-Transport-Security" in headers
        assert "X-Content-Type-Options" in headers
        assert "X-Frame-Options" in headers
        assert "X-XSS-Protection" in headers

    def test_security_headers_content(self, client):
        """Test security headers have correct values"""
        response = client.get("/health")
        headers = response.headers

        assert headers["X-Content-Type-Options"] == "nosniff"
        assert headers["X-Frame-Options"] == "DENY"
        assert headers["X-XSS-Protection"] == "1; mode=block"

    def test_custom_headers_present(self, client):
        """Test custom headers are added"""
        response = client.get("/health")
        headers = response.headers

        assert "X-Service-Name" in headers
        assert headers["X-Service-Name"] == "mastery-engine"
        assert "X-API-Version" in headers
        assert headers["X-API-Version"] == "1.0.0"

    def test_request_id_header(self, client):
        """Test request ID is generated"""
        response = client.get("/health")
        headers = response.headers

        assert "X-Request-ID" in headers
        assert headers["X-Request-ID"] is not None


class TestCORSConfiguration:
    """Test CORS configuration"""

    def test_cors_headers_present(self, client):
        """Test CORS headers are present"""
        response = client.options("/health")

        headers = response.headers

        assert "access-control-allow-origin" in headers
        assert "access-control-allow-methods" in headers
        assert "access-control-allow-headers" in headers

    def test_cors_origin_configuration(self, client):
        """Test CORS origin configuration"""
        # Default is "*"
        response = client.options("/health")

        assert response.headers["access-control-allow-origin"] == "*"


class TestGlobalExceptionHandler:
    """Test global exception handler"""

    def test_global_exception_handler_catches_all(self, client):
        """Test global handler catches unhandled exceptions"""
        with patch('src.main.performance_metrics_middleware') as mock_middleware:
            mock_middleware.side_effect = Exception("Unexpected error")

            response = client.get("/health")

            assert response.status_code == 500
            data = response.json()
            assert "error" in data

    def test_global_exception_handler_development_mode(self, client):
        """Test handler shows details in development mode"""
        with patch.dict('os.environ', {'ENVIRONMENT': 'development'}):
            with patch('src.main.performance_metrics_middleware') as mock_middleware:
                mock_middleware.side_effect = Exception("Detailed error")

                response = client.get("/health")
                data = response.json()

                assert "Detailed error" in data["message"]

    def test_global_exception_handler_production_mode(self, client):
        """Test handler hides details in production mode"""
        with patch.dict('os.environ', {'ENVIRONMENT': 'production'}):
            with patch('src.main.performance_metrics_middleware') as mock_middleware:
                mock_middleware.side_effect = Exception("Sensitive error details")

                response = client.get("/health")
                data = response.json()

                assert "Sensitive error" not in data["message"]
                assert data["message"] == "Something went wrong"


class TestHealthCheckDependencies:
    """Test health check dependency verification"""

    @patch('src.main.app_state')
    def test_verify_dependencies_success(self, mock_app_state, client):
        """Test successful dependency verification"""
        # Mock a healthy state
        mock_state_manager = Mock()
        mock_state_manager.health_check = AsyncMock(return_value=True)
        mock_state_manager.save = AsyncMock(return_value=True)
        mock_state_manager.delete = AsyncMock(return_value=True)

        mock_app_state.__getitem__ = lambda self, key: {
            "state_manager": mock_state_manager,
            "ready": True,
            "health_report": {"state_store": True, "kafka": False, "dapr": True}
        }[key]

        response = client.get("/ready")
        assert response.status_code == 200

    @patch('src.main.app_state')
    def test_verify_dependencies_failure(self, mock_app_state, client):
        """Test dependency verification failure"""
        mock_state_manager = Mock()
        mock_state_manager.health_check = AsyncMock(side_effect=Exception("Connection failed"))

        mock_app_state.__getitem__ = lambda self, key: {
            "state_manager": mock_state_manager,
            "ready": True,
            "health_report": {"state_store": False, "kafka": False, "dapr": False}
        }[key]

        response = client.get("/ready")
        assert response.status_code == 503