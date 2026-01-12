"""
Audit Logger Service - Security Handshake Audit
Elite Implementation Standard v2.0.0

Creates TriageAudit with all required fields for compliance.
Provides detailed audit trail for every triage operation.
"""

import json
import time
import uuid
from typing import Dict, Optional, List
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class AuditEventType(Enum):
    """Audit event types"""
    TRIAGE_REQUEST = "triage_request"
    INTENT_CLASSIFICATION = "intent_classification"
    ROUTING_DECISION = "routing_decision"
    DAPR_INVOCATION = "dapr_invocation"
    CIRCUIT_BREAKER_EVENT = "circuit_breaker_event"
    AUTHORIZATION_SUCCESS = "authorization_success"
    AUTHORIZATION_FAILURE = "authorization_failure"
    SCHEMA_VALIDATION_FAILURE = "schema_validation_failure"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"


@dataclass
class TriageAudit:
    """Complete audit record for triage operation"""

    # Core identifiers
    audit_id: str
    request_id: str
    student_id: str
    timestamp: str

    # Request details
    query: str
    query_length: int
    query_hash: str

    # Security context
    role: str
    auth_method: str
    consumer_id: Optional[str]

    # Classification results
    intent: str
    confidence: float
    classification_time_ms: float
    tokens_used: int
    efficiency_percentage: float

    # Routing decisions
    target_agent: str
    priority: int
    circuit_breaker_state: str
    retry_count: int

    # Dapr invocation
    dapr_app_id: str
    dapr_latency_ms: float
    dapr_success: bool
    dapr_error: Optional[str]

    # Performance metrics
    total_processing_ms: float
    classification_overhead_ms: float
    routing_overhead_ms: float

    # Security metrics
    schema_validation_passed: bool
    rate_limit_check_passed: bool
    authorization_passed: bool

    # Resilience events
    circuit_breaker_events: List[Dict]
    retry_events: List[Dict]

    # Metadata
    version: str = "1.0"
    environment: str = "production"
    service_name: str = "triage-service"


class AuditLogger:
    """
    Audit logging service for security compliance

    Logs all triage operations with full context for:
    - Security auditing
    - Performance monitoring
    - Compliance reporting
    - Debugging and troubleshooting
    """

    def __init__(self, use_mock: bool = True):
        self.use_mock = use_mock
        self.audit_buffer = []  # For mock mode
        self.max_buffer_size = 1000

        if not use_mock:
            try:
                from kafka import KafkaProducer
                self.producer = KafkaProducer(
                    bootstrap_servers=['localhost:9092'],
                    value_serializer=lambda v: json.dumps(v).encode('utf-8')
                )
                self.topic = "learning.events.audit.triage"
            except ImportError:
                print("Kafka not available, using mock audit logger")
                self.use_mock = True
                self.producer = None
        else:
            self.producer = None

    def log_triage_event(
        self,
        request_id: str,
        student_id: str,
        query: str,
        role: str,
        auth_context: Dict,
        classification_result: Dict,
        routing_decision: Dict,
        dapr_response: Dict,
        performance_metrics: Dict,
        security_validation: Dict,
        resilience_events: Dict
    ) -> TriageAudit:
        """
        Create and log complete triage audit event

        Args:
            request_id: Unique request identifier
            student_id: Student identifier
            query: Original query text
            role: User role
            auth_context: Authentication context
            classification_result: Intent classification results
            routing_decision: Routing decision metadata
            dapr_response: Dapr invocation response
            performance_metrics: Timing and performance data
            security_validation: Validation results
            resilience_events: Circuit breaker and retry events

        Returns:
            TriageAudit object
        """
        timestamp = datetime.utcnow().isoformat()

        # Calculate query hash for privacy (anonymized logging)
        query_hash = str(hash(query))  # Simple hash for correlation

        # Extract circuit breaker events
        cb_events = resilience_events.get("circuit_breaker", [])
        retry_events = resilience_events.get("retries", [])

        # Create audit record
        audit = TriageAudit(
            audit_id=str(uuid.uuid4()),
            request_id=request_id,
            student_id=student_id,
            timestamp=timestamp,

            query=query,
            query_length=len(query),
            query_hash=query_hash,

            role=role,
            auth_method=auth_context.get("auth_method", "kong-jwt"),
            consumer_id=auth_context.get("consumer_id"),

            intent=classification_result.get("intent"),
            confidence=classification_result.get("confidence"),
            classification_time_ms=classification_result.get("processing_time_ms"),
            tokens_used=classification_result.get("tokens_used"),
            efficiency_percentage=classification_result.get("efficiency_percentage"),

            target_agent=routing_decision.get("target_agent"),
            priority=routing_decision.get("priority"),
            circuit_breaker_state=routing_decision.get("circuit_breaker_state", "CLOSED"),
            retry_count=dapr_response.get("retry_count", 0),

            dapr_app_id=routing_decision.get("dapr_app_id"),
            dapr_latency_ms=dapr_response.get("latency_ms"),
            dapr_success=dapr_response.get("success", False),
            dapr_error=dapr_response.get("error"),

            total_processing_ms=performance_metrics.get("total_processing_ms"),
            classification_overhead_ms=performance_metrics.get("classification_overhead_ms", 0),
            routing_overhead_ms=performance_metrics.get("routing_overhead_ms", 0),

            schema_validation_passed=security_validation.get("schema_validation", False),
            rate_limit_check_passed=security_validation.get("rate_limit", False),
            authorization_passed=security_validation.get("authorization", False),

            circuit_breaker_events=cb_events,
            retry_events=retry_events
        )

        # Log the audit event
        self._write_audit_event(audit)

        return audit

    def _write_audit_event(self, audit: TriageAudit):
        """Write audit event to storage/stream"""
        audit_dict = asdict(audit)

        if self.use_mock or self.producer is None:
            # Mock mode - buffer in memory
            self.audit_buffer.append(audit_dict)
            if len(self.audit_buffer) > self.max_buffer_size:
                # Rotate buffer
                self.audit_buffer = self.audit_buffer[-self.max_buffer_size:]

            # Print for visibility
            print(f"AUDIT_LOG: {json.dumps(audit_dict, indent=2)}")
        else:
            # Send to Kafka
            try:
                self.producer.send(self.topic, audit_dict)
                self.producer.flush()
            except Exception as e:
                print(f"Failed to send audit to Kafka: {e}")
                # Fallback to mock logging
                self.audit_buffer.append(audit_dict)

    def get_audit_logs(self, limit: int = 100) -> List[Dict]:
        """Get recent audit logs (mock mode)"""
        if limit >= len(self.audit_buffer):
            return self.audit_buffer
        return self.audit_buffer[-limit:]

    def search_by_student(self, student_id: str, limit: int = 50) -> List[Dict]:
        """Search audit logs by student_id"""
        return [
            log for log in self.audit_buffer
            if log.get("student_id") == student_id
        ][:limit]

    def search_by_intent(self, intent: str, limit: int = 50) -> List[Dict]:
        """Search audit logs by intent"""
        return [
            log for log in self.audit_buffer
            if log.get("intent") == intent
        ][:limit]

    def get_performance_stats(self) -> Dict:
        """Calculate performance statistics from audit logs"""
        if not self.audit_buffer:
            return {}

        total_requests = len(self.audit_buffer)
        successful_requests = sum(1 for log in self.audit_buffer if log.get("dapr_success"))
        failed_requests = total_requests - successful_requests

        # Calculate averages
        avg_processing_time = sum(
            log.get("total_processing_ms", 0) for log in self.audit_buffer
        ) / total_requests if total_requests > 0 else 0

        avg_token_usage = sum(
            log.get("tokens_used", 0) for log in self.audit_buffer
        ) / total_requests if total_requests > 0 else 0

        avg_efficiency = sum(
            log.get("efficiency_percentage", 0) for log in self.audit_buffer
        ) / total_requests if total_requests > 0 else 0

        # Intent distribution
        intent_counts = {}
        for log in self.audit_buffer:
            intent = log.get("intent")
            intent_counts[intent] = intent_counts.get(intent, 0) + 1

        # Agent distribution
        agent_counts = {}
        for log in self.audit_buffer:
            agent = log.get("target_agent")
            agent_counts[agent] = agent_counts.get(agent, 0) + 1

        return {
            "total_requests": total_requests,
            "successful_requests": successful_requests,
            "failed_requests": failed_requests,
            "success_rate": (successful_requests / total_requests * 100) if total_requests > 0 else 0,
            "avg_processing_time_ms": avg_processing_time,
            "avg_token_usage": avg_token_usage,
            "avg_efficiency_percentage": avg_efficiency,
            "intent_distribution": intent_counts,
            "agent_distribution": agent_counts
        }

    def get_security_events(self) -> List[Dict]:
        """Get security-related audit events"""
        security_events = []

        for log in self.audit_buffer:
            # Authorization failures
            if log.get("authorization_passed") is False:
                security_events.append({
                    "type": "AUTHORIZATION_FAILURE",
                    "student_id": log.get("student_id"),
                    "timestamp": log.get("timestamp"),
                    "query": log.get("query")[:50]  # Truncated
                })

            # Rate limit violations
            if log.get("rate_limit_check_passed") is False:
                security_events.append({
                    "type": "RATE_LIMIT_VIOLATION",
                    "student_id": log.get("student_id"),
                    "timestamp": log.get("timestamp")
                })

            # Circuit breaker events
            if log.get("circuit_breaker_events"):
                for event in log.get("circuit_breaker_events", []):
                    security_events.append({
                        "type": "CIRCUIT_BREAKER",
                        "event": event,
                        "student_id": log.get("student_id"),
                        "timestamp": log.get("timestamp")
                    })

            # Dapr failures
            if log.get("dapr_success") is False:
                security_events.append({
                    "type": "DAPR_FAILURE",
                    "student_id": log.get("student_id"),
                    "timestamp": log.get("timestamp"),
                    "error": log.get("dapr_error")
                })

        return security_events

    def export_compliance_report(self) -> Dict:
        """Generate compliance report"""
        stats = self.get_performance_stats()
        security_events = self.get_security_events()

        return {
            "report_id": str(uuid.uuid4()),
            "generated_at": datetime.utcnow().isoformat(),
            "period": "last_24_hours",  # Could be configurable
            "summary": {
                "total_triage_operations": stats.get("total_requests", 0),
                "success_rate": stats.get("success_rate", 0),
                "performance": {
                    "avg_response_time": stats.get("avg_processing_time_ms", 0),
                    "token_efficiency": stats.get("avg_efficiency_percentage", 0)
                },
                "security": {
                    "total_events": len(security_events),
                    "auth_failures": sum(1 for e in security_events if e["type"] == "AUTHORIZATION_FAILURE"),
                    "rate_limit_violations": sum(1 for e in security_events if e["type"] == "RATE_LIMIT_VIOLATION"),
                    "system_failures": sum(1 for e in security_events if e["type"] in ["CIRCUIT_BREAKER", "DAPR_FAILURE"])
                }
            },
            "intent_breakdown": stats.get("intent_distribution", {}),
            "agent_breakdown": stats.get("agent_distribution", {})
        }


# Global audit logger instance
audit_logger = AuditLogger(use_mock=True)


def create_audit_log(
    request_id: str,
    student_id: str,
    query: str,
    role: str,
    auth_context: Dict,
    classification_result: Dict,
    routing_decision: Dict,
    dapr_response: Dict,
    performance_metrics: Dict,
    security_validation: Dict,
    resilience_events: Dict
) -> TriageAudit:
    """Convenience function to create audit log"""
    return audit_logger.log_triage_event(
        request_id, student_id, query, role, auth_context,
        classification_result, routing_decision, dapr_response,
        performance_metrics, security_validation, resilience_events
    )


if __name__ == "__main__":
    # Test audit logger
    print("=== Audit Logger Test ===")

    # Create sample audit entry
    audit = audit_logger.log_triage_event(
        request_id="req-12345",
        student_id="student-67890",
        query="How do I fix a syntax error in my Python function?",
        role="student",
        auth_context={"auth_method": "kong-jwt", "consumer_id": "consumer-uuid"},
        classification_result={
            "intent": "syntax_help",
            "confidence": 0.95,
            "processing_time_ms": 4.5,
            "tokens_used": 19,
            "efficiency_percentage": 98.7
        },
        routing_decision={
            "target_agent": "debug-agent",
            "priority": 1,
            "circuit_breaker_state": "CLOSED",
            "dapr_app_id": "debug-agent"
        },
        dapr_response={
            "success": True,
            "latency_ms": 15.2,
            "retry_count": 0,
            "error": None
        },
        performance_metrics={
            "total_processing_ms": 25.0,
            "classification_overhead_ms": 5.0,
            "routing_overhead_ms": 0.1
        },
        security_validation={
            "schema_validation": True,
            "rate_limit": True,
            "authorization": True
        },
        resilience_events={
            "circuit_breaker": [],
            "retries": []
        }
    )

    print(f"Audit ID: {audit.audit_id}")
    print(f"Efficiency: {audit.efficiency_percentage}%")

    # Get stats
    stats = audit_logger.get_performance_stats()
    print(f"\nPerformance Stats: {json.dumps(stats, indent=2)}")

    # Get security events
    security_events = audit_logger.get_security_events()
    print(f"\nSecurity Events: {len(security_events)}")

    # Get compliance report
    report = audit_logger.export_compliance_report()
    print(f"\nCompliance Report Generated: {report['report_id']}")