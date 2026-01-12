"""
Integration Tests: End-to-End Triage Flow
Elite Implementation Standard v2.0.0

Tests complete triage pipeline from HTTP request through security,
classification, routing, Dapr invocation, and audit logging.
"""

import sys
import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path / "src"))

from fastapi import FastAPI
from fastapi.testclient import TestClient

from main import app
from models.schemas import TriageRequest, TriageResponse
from services.integration import TriageOrchestrator
from api.middleware.auth import security_context_middleware
from api.middleware.authorization import authorization_middleware


class TestE2ETriageFlow:
    """Test complete end-to-end triage flow"""

    def setup_method(self):
        """Setup test client"""
        self.client = TestClient(app)

    def test_health_check(self):
        """Test basic health check endpoint"""
        response = self.client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "triage-service"
        assert data["phase"] == "2"

    def test_metrics_endpoint(self):
        """Test metrics endpoint returns expected structure"""
        response = self.client.get("/metrics")
        assert response.status_code == 200
        data = response.json()

        assert data["service"] == "triage-service"
        assert "efficiency" in data
        assert "performance" in data
        assert "resilience" in data
        assert "features" in data

        # Check efficiency metrics
        assert data["efficiency"]["target"] == "98.7%"
        assert data["efficiency"]["vs_llm"] == "1500 → 19 tokens"

    @patch('services.integration.create_triage_orchestrator')
    def test_triage_endpoint_success(self, mock_orchestrator):
        """Test successful triage request"""
        # Mock orchestrator response
        mock_orchestrator_instance = Mock()
        mock_response = Mock()
        mock_response.dict.return_value = {
            "routing_decision": {
                "target_agent": "debug-agent",
                "confidence": 0.95,
                "intent": "syntax_help",
                "priority": 1
            },
            "metrics": {
                "tokens_used": 19,
                "efficiency_percentage": 98.7,
                "total_processing_ms": 15.5
            },
            "audit_id": "audit-12345"
        }
        mock_metrics = Mock()
        mock_metrics.tokens_used = 19
        mock_metrics.efficiency_percentage = 98.7
        mock_metrics.total_processing_ms = 15.5

        mock_orchestrator_instance.execute_triage = AsyncMock(
            return_value=(mock_response, mock_metrics)
        )
        mock_orchestrator.return_value = mock_orchestrator_instance

        # Mock security context
        with patch('main.security_context_middleware') as mock_auth:
            async def mock_middleware(request, call_next):
                # Mock the security context
                class MockRequest:
                    def __init__(self):
                        self.state = Mock()
                        self.state.security_context = {
                            "student_id": "student-12345",
                            "role": "student",
                            "source": "kong"
                        }
                mock_request = MockRequest()
                return await call_next(mock_request)

            mock_auth.side_effect = mock_middleware

            # Make request
            request_data = {
                "query": "What is polymorphism?",
                "user_id": "student-12345",
                "context": {"topic": "OOP"}
            }

            response = self.client.post(
                "/api/v1/triage",
                json=request_data
            )

            assert response.status_code == 200
            data = response.json()

            # Check response structure
            assert "routing_decision" in data
            assert "metrics" in data
            assert "audit_id" in data

            # Check routing decision
            assert data["routing_decision"]["target_agent"] == "debug-agent"
            assert data["routing_decision"]["confidence"] == 0.95

            # Check metrics
            assert data["metrics"]["tokens_used"] == 19
            assert data["metrics"]["efficiency_percentage"] == 98.7

            # Check headers
            assert "x-token-usage" in response.headers
            assert "x-efficiency" in response.headers

    @patch('services.integration.create_triage_orchestrator')
    def test_triage_endpoint_schema_validation_error(self, mock_orchestrator):
        """Test schema validation catches invalid requests"""
        # Invalid request (empty query)
        invalid_data = {
            "query": "",
            "user_id": "student-12345"
        }

        with patch('main.security_context_middleware') as mock_auth:
            async def mock_middleware(request, call_next):
                class MockRequest:
                    def __init__(self):
                        self.state = Mock()
                        self.state.security_context = {"student_id": "student-12345"}
                return await call_next(MockRequest())

            mock_auth.side_effect = mock_middleware

            response = self.client.post(
                "/api/v1/triage",
                json=invalid_data
            )

            assert response.status_code == 422  # Validation error

    @patch('services.integration.create_triage_orchestrator')
    def test_triage_endpoint_missing_auth(self, mock_orchestrator):
        """Test authentication requirement"""
        request_data = {
            "query": "Test query",
            "user_id": "student-12345"
        }

        # Mock auth middleware that doesn't set security context
        with patch('main.security_context_middleware') as mock_auth:
            async def mock_middleware(request, call_next):
                class MockRequest:
                    def __init__(self):
                        self.state = Mock()
                        self.state.security_context = None  # No auth context
                return await call_next(MockRequest())

            mock_auth.side_effect = mock_middleware

            response = self.client.post(
                "/api/v1/triage",
                json=request_data
            )

            assert response.status_code == 401

    def test_circuit_breaker_status_endpoint(self):
        """Test circuit breaker status monitoring"""
        response = self.client.get("/api/v1/triage/circuit-breakers")
        assert response.status_code == 200
        data = response.json()

        assert "circuit_breakers" in data
        assert "summary" in data
        assert "total_agents" in data["summary"]

    def test_agent_health_endpoint(self):
        """Test individual agent health check"""
        response = self.client.get("/api/v1/triage/health/debug-agent")
        assert response.status_code == 200
        data = response.json()

        assert data["target_agent"] == "debug-agent"
        assert "health" in data
        assert "circuit_breaker" in data


class TestIntegrationOrchestrator:
    """Test TriageOrchestrator integration flow"""

    @pytest.mark.asyncio
    async def test_orchestrator_complete_flow(self):
        """Test orchestrator executes complete flow"""
        # Mock dependencies
        with patch('services.integration.OpenAIRouter') as mock_router, \
             patch('services.integration.DaprClient') as mock_dapr, \
             patch('services.integration.TriageAudit') as mock_audit:

            # Setup mocks
            mock_router_instance = Mock()
            mock_router_instance.classify_intent.return_value = {
                "intent": "syntax_help",
                "confidence": 0.95,
                "token_estimate": 15
            }
            mock_router_instance.route_selection.return_value = {
                "target_agent": "debug-agent",
                "priority": 1,
                "confidence": 0.95,
                "intent": "syntax_help"
            }
            mock_router.return_value = mock_router_instance

            mock_dapr_instance = Mock()
            mock_dapr_instance.invoke_agent = AsyncMock(return_value={
                "result": "success",
                "solution": "Fix your syntax error"
            })
            mock_dapr_instance.get_circuit_breaker_status.return_value = {
                "can_attempt": True,
                "state": "CLOSED"
            }
            mock_dapr.return_value = mock_dapr_instance

            mock_audit_instance = Mock()
            mock_audit_instance.record_event = Mock()
            mock_audit.return_value = mock_audit_instance

            # Create orchestrator
            orchestrator = TriageOrchestrator()

            # Execute flow
            request = {
                "query": "syntax error in for loop",
                "user_id": "student-12345"
            }
            security_context = {
                "student_id": "student-12345",
                "role": "student"
            }

            response, metrics = await orchestrator.execute_triage(
                request, security_context
            )

            # Verify complete flow
            assert response.routing_decision.target_agent == "debug-agent"
            assert response.routing_decision.confidence == 0.95
            assert metrics.tokens_used == 15
            assert metrics.efficiency_percentage > 90

            # Verify audit was called
            assert mock_audit_instance.record_event.called

    @pytest.mark.asyncio
    async def test_orchestrator_circuit_breaker_flow(self):
        """Test orchestrator handles circuit breaker open state"""
        with patch('services.integration.OpenAIRouter'), \
             patch('services.integration.DaprClient') as mock_dapr, \
             patch('services.integration.TriageAudit'):

            mock_dapr_instance = Mock()
            # Circuit breaker is open
            mock_dapr_instance.invoke_agent = AsyncMock(
                side_effect=Exception("Circuit breaker open")
            )
            mock_dapr_instance.get_circuit_breaker_status.return_value = {
                "can_attempt": False,
                "state": "OPEN"
            }
            mock_dapr.return_value = mock_dapr_instance

            orchestrator = TriageOrchestrator()

            request = {"query": "test", "user_id": "student-12345"}
            security_context = {"student_id": "student-12345"}

            # Should handle gracefully
            response, metrics = await orchestrator.execute_triage(
                request, security_context
            )

            # Should still return valid response
            assert response is not None
            assert metrics is not None

    @pytest.mark.asyncio
    async def test_orchestrator_retry_logic(self):
        """Test orchestrator retry logic on transient failures"""
        with patch('services.integration.OpenAIRouter'), \
             patch('services.integration.DaprClient') as mock_dapr, \
             patch('services.integration.TriageAudit'):

            mock_dapr_instance = Mock()

            # Fail first call, succeed on retry
            call_count = 0

            async def mock_invoke(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    raise Exception("Transient error")
                return {"result": "success"}

            mock_dapr_instance.invoke_agent = mock_invoke
            mock_dapr_instance.get_circuit_breaker_status.return_value = {
                "can_attempt": True,
                "state": "CLOSED"
            }
            mock_dapr.return_value = mock_dapr_instance

            orchestrator = TriageOrchestrator()

            request = {"query": "test", "user_id": "student-12345"}
            security_context = {"student_id": "student-12345"}

            response, metrics = await orchestrator.execute_triage(
                request, security_context
            )

            # Should succeed after retry
            assert call_count == 2
            assert metrics.retries == 1


class TestSecurityFlow:
    """Test security middleware integration"""

    def test_security_context_extraction(self):
        """Test security context from Kong headers"""
        from api.middleware.auth import security_context_middleware
        from fastapi import Request
        from unittest.mock import Mock

        # Mock request with Kong headers
        mock_request = Mock(spec=Request)
        mock_request.headers = {
            "X-Consumer-Username": "student-12345",
            "X-Consumer-ID": "consumer-123",
            "X-JWT-Claims": '{"sub": "student-12345", "role": "student", "exp": 9999999999}'
        }

        # Mock call_next
        async def mock_call_next(req):
            return Mock()

        # Test middleware execution
        async def test_middleware():
            response = await security_context_middleware(mock_request, mock_call_next)
            # Should set security_context on request.state
            assert hasattr(mock_request.state, 'security_context')
            context = mock_request.state.security_context
            assert context["student_id"] == "student-12345"
            assert context["role"] == "student"

        # Run async test
        asyncio.run(test_middleware())

    def test_authorization_middleware(self):
        """Test authorization checks"""
        from api.middleware.authorization import authorization_middleware
        from fastapi import Request
        from unittest.mock import Mock

        # Mock request with security context
        mock_request = Mock(spec=Request)
        mock_request.state.security_context = {
            "student_id": "student-12345",
            "role": "student"
        }
        mock_request.method = "POST"
        mock_request.url.path = "/api/v1/triage"

        async def mock_call_next(req):
            return Mock()

        async def test_middleware():
            response = await authorization_middleware(mock_request, mock_call_next)
            # Should pass through for authorized access
            assert response is not None

        asyncio.run(test_middleware())


class TestKafkaAuditIntegration:
    """Test Kafka audit logging integration"""

    def test_audit_event_structure(self):
        """Test audit events have correct structure"""
        from services.audit_logger import TriageAudit

        audit = TriageAudit()

        # Mock Kafka mode
        audit.kafka_enabled = False  # Use mock mode

        event = audit.record_event(
            event_type="TRIAGE_COMPLETE",
            student_id="student-12345",
            routing_decision={
                "target_agent": "debug-agent",
                "confidence": 0.95
            },
            metrics={
                "tokens_used": 19,
                "efficiency": 98.7
            }
        )

        assert event.event_type == "TRIAGE_COMPLETE"
        assert event.student_id == "student-12345"
        assert "timestamp" in event.details
        assert event.details["routing_decision"]["target_agent"] == "debug-agent"

    def test_compliance_report_generation(self):
        """Test security compliance reporting"""
        from services.security_reporter import SecurityReporter

        reporter = SecurityReporter()

        # Generate test events
        reporter.record_auth_failure("student-123", "missing_header", {})
        reporter.record_schema_violation("student-456", ["too_long"], "long_input")

        report = reporter.generate_compliance_report(hours=1)

        assert "report_id" in report
        assert "summary" in report
        assert "event_breakdown" in report["summary"]
        assert report["summary"]["total_events"] >= 2


class TestResilienceScenarios:
    """Test resilience scenarios"""

    @pytest.mark.asyncio
    async def test_service_downtime_handling(self):
        """Test handling when target agent is down"""
        with patch('services.integration.OpenAIRouter'), \
             patch('services.integration.DaprClient') as mock_dapr, \
             patch('services.integration.TriageAudit'):

            mock_dapr_instance = Mock()

            # Simulate service down
            async def mock_invoke_failure(*args, **kwargs):
                raise ConnectionError("Service unavailable")

            mock_dapr_instance.invoke_agent = mock_invoke_failure
            mock_dapr_instance.get_circuit_breaker_status.return_value = {
                "can_attempt": True,
                "state": "CLOSED"
            }
            mock_dapr.return_value = mock_dapr_instance

            orchestrator = TriageOrchestrator()

            request = {"query": "test", "user_id": "student-12345"}
            security_context = {"student_id": "student-12345"}

            # Should handle gracefully without crashing
            response, metrics = await orchestrator.execute_triage(
                request, security_context
            )

            # Should still return valid response structure
            assert response is not None

    @pytest.mark.asyncio
    async def test_timeout_handling(self):
        """Test request timeout handling"""
        with patch('services.integration.OpenAIRouter'), \
             patch('services.integration.DaprClient') as mock_dapr, \
             patch('services.integration.TriageAudit'):

            mock_dapr_instance = Mock()

            async def slow_invoke(*args, **kwargs):
                await asyncio.sleep(5)  # Exceeds timeout
                return {"result": "slow"}

            mock_dapr_instance.invoke_agent = slow_invoke
            mock_dapr.return_value = mock_dapr_instance

            orchestrator = TriageOrchestrator()

            request = {"query": "test", "user_id": "student-12345"}
            security_context = {"student_id": "student-12345"}

            # Should timeout gracefully
            with pytest.raises(asyncio.TimeoutError):
                await asyncio.wait_for(
                    orchestrator.execute_triage(request, security_context),
                    timeout=2.0
                )


if __name__ == "__main__":
    print("=== Running Integration Tests: E2E Triage Flow ===")
    pytest.main([__file__, "-v"])