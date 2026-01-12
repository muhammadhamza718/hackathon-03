"""
Integration Tests: Kafka Audit Logging
Elite Implementation Standard v2.0.0

Tests Kafka audit logging integration and event streaming.
"""

import sys
import pytest
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add backend to path
backend_path = Path(__file__).parent.parent.parent
sys.path.insert(0, str(backend_path / "src"))

from services.audit_logger import TriageAudit, AuditEvent
from services.kafka_publisher import KafkaPublisher
from services.security_reporter import SecurityReporter


class TestKafkaPublisher:
    """Test Kafka publisher functionality"""

    def test_publisher_creation(self):
        """Test Kafka publisher creation"""
        publisher = KafkaPublisher()

        assert publisher is not None
        assert publisher.mock_mode is True  # Default to mock in tests

    def test_publish_audit_event_mock(self):
        """Test publishing audit event in mock mode"""
        publisher = KafkaPublisher()

        event = AuditEvent(
            event_type="TRIAGE_COMPLETE",
            student_id="student-12345",
            timestamp=datetime.utcnow().isoformat(),
            details={"target_agent": "debug-agent"}
        )

        # Mock mode should work without real Kafka
        result = publisher.publish_audit_event(event)
        assert result is True

        # Check event was "published" to mock queue
        assert len(publisher.mock_events) == 1
        assert publisher.mock_events[0]["event_type"] == "TRIAGE_COMPLETE"

    def test_publish_security_event_mock(self):
        """Test publishing security event in mock mode"""
        publisher = KafkaPublisher()

        security_event = {
            "event_type": "AUTH_FAILURE",
            "student_id": "student-123",
            "timestamp": datetime.utcnow().isoformat(),
            "details": {"reason": "missing_header"}
        }

        result = publisher.publish_security_event(security_event)
        assert result is True
        assert len(publisher.mock_events) == 1

    def test_event_format_validation(self):
        """Test event format validation"""
        publisher = KafkaPublisher()

        # Valid event
        valid_event = AuditEvent(
            event_type="TEST",
            student_id="student-12345",
            timestamp=datetime.utcnow().isoformat(),
            details={"test": True}
        )

        # Should validate without error
        result = publisher.publish_audit_event(valid_event)
        assert result is True


class TestTriageAuditIntegration:
    """Test TriageAudit integration with Kafka"""

    def setup_method(self):
        """Setup test audit logger"""
        self.audit = TriageAudit()
        self.audit.kafka_enabled = False  # Use mock mode

    def test_record_triage_complete_event(self):
        """Test recording triage completion event"""
        event = self.audit.record_event(
            event_type="TRIAGE_COMPLETE",
            student_id="student-12345",
            routing_decision={
                "target_agent": "debug-agent",
                "confidence": 0.95,
                "intent": "syntax_help"
            },
            metrics={
                "tokens_used": 19,
                "efficiency": 98.7,
                "processing_ms": 15.5
            }
        )

        assert event.event_type == "TRIAGE_COMPLETE"
        assert event.student_id == "student-12345"
        assert "routing_decision" in event.details
        assert event.details["routing_decision"]["target_agent"] == "debug-agent"

    def test_record_security_event(self):
        """Test recording security event"""
        event = self.audit.record_event(
            event_type="AUTH_FAILURE",
            student_id="student-123",
            details={"reason": "missing_jwt"}
        )

        assert event.event_type == "AUTH_FAILURE"
        assert event.student_id == "student-123"
        assert event.details["reason"] == "missing_jwt"

    def test_record_performance_metrics(self):
        """Test recording performance metrics"""
        event = self.audit.record_event(
            event_type="PERFORMANCE_METRICS",
            student_id="student-12345",
            details={
                "efficiency": 98.7,
                "latency_ms": 15.5,
                "tokens_saved": 1481
            }
        )

        assert event.event_type == "PERFORMANCE_METRICS"
        assert event.details["efficiency"] == 98.7

    def test_batch_event_processing(self):
        """Test batch processing of multiple events"""
        events = []
        for i in range(5):
            event = self.audit.record_event(
                event_type=f"TEST_EVENT_{i}",
                student_id=f"student-{i:03d}",
                details={"index": i}
            )
            events.append(event)

        assert len(events) == 5

        # Verify each event has proper structure
        for i, event in enumerate(events):
            assert event.event_type == f"TEST_EVENT_{i}"
            assert event.student_id == f"student-{i:03d}"


class TestSecurityReporterIntegration:
    """Test SecurityReporter integration with audit system"""

    def setup_method(self):
        """Setup test security reporter"""
        self.reporter = SecurityReporter()

    def test_complete_security_workflow(self):
        """Test complete security event workflow"""
        # Generate various security events
        self.reporter.record_auth_failure(
            "student-123",
            "missing_jwt_header",
            {"header": "X-Consumer-Username"}
        )

        self.reporter.record_authorization_violation(
            "student-456",
            "triage:write",
            "triage:read"
        )

        self.reporter.record_schema_violation(
            "student-789",
            ["query_too_long"],
            "a" * 1000
        )

        self.reporter.record_circuit_breaker_event(
            "student-123",
            "debug-agent",
            "OPEN",
            {"failure_count": 5}
        )

        # Generate compliance report
        report = self.reporter.generate_compliance_report(hours=24)

        assert report["summary"]["total_events"] >= 4
        assert "AUTH_FAILURE" in report["summary"]["event_breakdown"]

        # Generate audit trail
        audit_trail = self.reporter.generate_audit_trail(hours=24)
        assert len(audit_trail) >= 4

    def test_alert_thresholds(self):
        """Test alert threshold detection"""
        # Create events exceeding threshold
        for _ in range(15):  # >10 per minute threshold
            self.reporter.record_auth_failure("student-123", "test", {})

        alerts = self.reporter.check_alert_thresholds(minutes=60)
        assert alerts["violations"] >= 1

        # Check alert details
        alert = alerts["alerts"][0]
        assert alert["threshold"] == "auth_failures_per_minute"
        assert alert["actual"] >= 15

    def test_risk_assessment(self):
        """Test risk score calculation"""
        # High severity events
        for _ in range(3):
            self.reporter.record_auth_failure("student-risk", "test", {})
        for _ in range(3):
            self.reporter.record_dapr_failure("student-risk", "agent", "timeout", 3)

        report = self.reporter.generate_compliance_report(hours=24)
        risk = report["summary"]["risk_score"]

        # Should be high or critical
        assert risk in ["HIGH", "CRITICAL"]


class TestKafkaEndToEnd:
    """Test end-to-end Kafka audit flow"""

    def test_audit_event_propagation(self):
        """Test audit event flows through system components"""
        # Create event through triage audit
        audit = TriageAudit()
        audit.kafka_enabled = False

        event = audit.record_event(
            event_type="TRIAGE_COMPLETE",
            student_id="student-12345",
            routing_decision={"target_agent": "debug-agent"},
            metrics={"tokens_used": 19}
        )

        # Security reporter should be able to process it
        reporter = SecurityReporter()
        # Simulate receiving event
        reporter.events.append(event)

        # Generate report with this event
        report = reporter.generate_compliance_report(hours=24)

        # Should include our event
        assert report["summary"]["total_events"] >= 1

    def test_compliance_export_format(self):
        """Test compliance export format"""
        reporter = SecurityReporter()

        # Add test events
        reporter.record_auth_failure("student-123", "test", {})
        reporter.record_schema_violation("student-456", ["error"], "input")

        export = reporter.export_for_compliance_system(hours=24)

        assert export["compliance_framework"] == "SOC2"
        assert "findings" in export
        assert "evidence" in export
        assert "risk_assessment" in export

        # Verify evidence packets
        assert len(export["evidence"]) >= 2


class TestEventSchema:
    """Test event schema consistency"""

    def test_audit_event_schema(self):
        """Test audit event has required fields"""
        event = AuditEvent(
            event_type="TRIAGE_COMPLETE",
            student_id="student-12345",
            timestamp=datetime.utcnow().isoformat(),
            details={"test": True}
        )

        # All required fields
        assert event.event_type is not None
        assert event.student_id is not None
        assert event.timestamp is not None
        assert event.details is not None

    def test_security_event_schema(self):
        """Test security events have required structure"""
        reporter = SecurityReporter()

        event = reporter.record_auth_failure("student-123", "reason", {"detail": "test"})

        assert hasattr(event, 'event_type')
        assert hasattr(event, 'timestamp')
        assert hasattr(event, 'student_id')
        assert hasattr(event, 'severity')
        assert hasattr(event, 'details')

    def test_compliance_report_schema(self):
        """Test compliance report has required structure"""
        reporter = SecurityReporter()
        report = reporter.generate_compliance_report(hours=24)

        required_fields = [
            "report_id",
            "generated_at",
            "period_hours",
            "summary",
            "details",
            "recommendations"
        ]

        for field in required_fields:
            assert field in report

        assert "total_events" in report["summary"]
        assert "event_breakdown" in report["summary"]


class TestPerformanceScenarios:
    """Test performance under load"""

    def test_high_volume_event_processing(self):
        """Test processing large number of events"""
        reporter = SecurityReporter()

        # Generate 1000 events
        for i in range(1000):
            if i % 3 == 0:
                reporter.record_auth_failure(f"student-{i}", "test", {})
            elif i % 3 == 1:
                reporter.record_schema_violation(f"student-{i}", ["error"], "input")
            else:
                reporter.record_circuit_breaker_event(
                    f"student-{i}", "agent", "OPEN", {}
                )

        report = reporter.generate_compliance_report(hours=24)
        assert report["summary"]["total_events"] == 1000

        # Should handle efficiently
        audit_trail = reporter.generate_audit_trail(hours=24)
        assert len(audit_trail) == 1000

    def test_memory_efficiency(self):
        """Test memory efficiency with many events"""
        import sys

        reporter = SecurityReporter()

        # Add many events
        for i in range(100):
            reporter.record_auth_failure(f"student-{i:03d}", "test", {"detail": "x" * 100})

        # Estimate memory usage
        total_size = sum(sys.getsizeof(e) for e in reporter.events)
        avg_size = total_size / len(reporter.events)

        # Each event should be <1KB
        assert avg_size < 1000


if __name__ == "__main__":
    print("=== Running Integration Tests: Kafka Audit ===")
    pytest.main([__file__, "-v"])