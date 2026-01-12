"""
Security Compliance Reporting
Elite Implementation Standard v2.0.0

Tracks auth failures, schema violations, and circuit breaker events.
Generates comprehensive security compliance reports.
"""

import json
import time
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from collections import defaultdict


@dataclass
class SecurityEvent:
    """Security event record"""
    event_type: str
    timestamp: str
    student_id: str
    severity: str
    details: Dict
    correlation_id: Optional[str] = None


class SecurityReporter:
    """
    Security compliance and monitoring reporter

    Tracks and reports on:
    - Authentication failures
    - Authorization violations
    - Schema validation failures
    - Circuit breaker events
    - Rate limiting violations
    - Dapr invocation failures
    """

    def __init__(self):
        self.events: List[SecurityEvent] = []
        self.alert_thresholds = {
            "auth_failures_per_minute": 10,
            "schema_violations_per_hour": 20,
            "circuit_breaker_opens_per_hour": 5,
            "rate_limit_violations_per_hour": 50
        }

    def record_auth_failure(self, student_id: str, reason: str, details: Dict) -> SecurityEvent:
        """Record authentication failure"""
        event = SecurityEvent(
            event_type="AUTH_FAILURE",
            timestamp=datetime.utcnow().isoformat(),
            student_id=student_id,
            severity="high",
            details={
                "reason": reason,
                **details
            }
        )
        self.events.append(event)
        return event

    def record_authorization_violation(self, student_id: str, attempted_action: str, required_permission: str) -> SecurityEvent:
        """Record authorization violation"""
        event = SecurityEvent(
            event_type="AUTHZ_VIOLATION",
            timestamp=datetime.utcnow().isoformat(),
            student_id=student_id,
            severity="medium",
            details={
                "attempted_action": attempted_action,
                "required_permission": required_permission
            }
        )
        self.events.append(event)
        return event

    def record_schema_violation(self, student_id: str, validation_errors: List[str], raw_input: str) -> SecurityEvent:
        """Record schema validation failure"""
        event = SecurityEvent(
            event_type="SCHEMA_VIOLATION",
            timestamp=datetime.utcnow().isoformat(),
            student_id=student_id,
            severity="low",
            details={
                "errors": validation_errors,
                "input_length": len(raw_input),
                "input_sample": raw_input[:100]
            }
        )
        self.events.append(event)
        return event

    def record_circuit_breaker_event(self, student_id: str, target_agent: str, event_type: str, state_change: Dict) -> SecurityEvent:
        """Record circuit breaker state change"""
        event = SecurityEvent(
            event_type="CIRCUIT_BREAKER",
            timestamp=datetime.utcnow().isoformat(),
            student_id=student_id,
            severity="medium",
            details={
                "target_agent": target_agent,
                "event_type": event_type,  # OPEN, HALF_OPEN, CLOSED
                "state_change": state_change,
                "consecutive_failures": state_change.get("failure_count", 0)
            }
        )
        self.events.append(event)
        return event

    def record_rate_limit_violation(self, student_id: str, current_count: int, limit: int) -> SecurityEvent:
        """Record rate limit violation"""
        event = SecurityEvent(
            event_type="RATE_LIMIT",
            timestamp=datetime.utcnow().isoformat(),
            student_id=student_id,
            severity="medium",
            details={
                "current_count": current_count,
                "limit": limit,
                "violation_percentage": (current_count / limit) * 100
            }
        )
        self.events.append(event)
        return event

    def record_dapr_failure(self, student_id: str, target_agent: str, error: str, retry_count: int) -> SecurityEvent:
        """Record Dapr invocation failure"""
        event = SecurityEvent(
            event_type="DAPR_FAILURE",
            timestamp=datetime.utcnow().isoformat(),
            student_id=student_id,
            severity="high",
            details={
                "target_agent": target_agent,
                "error": error,
                "retry_count": retry_count,
                "action_required": "Check agent health and circuit breaker state"
            }
        )
        self.events.append(event)
        return event

    def get_recent_events(self, minutes: int = 60, event_type: Optional[str] = None) -> List[SecurityEvent]:
        """Get events from last N minutes, optionally filtered by type"""
        cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)

        return [
            event for event in self.events
            if datetime.fromisoformat(event.timestamp) > cutoff_time
            and (event_type is None or event.event_type == event_type)
        ]

    def get_event_counts(self, minutes: int = 60) -> Dict[str, int]:
        """Get counts of different event types"""
        recent_events = self.get_recent_events(minutes)
        counts = defaultdict(int)

        for event in recent_events:
            counts[event.event_type] += 1

        return dict(counts)

    def check_alert_thresholds(self, minutes: int = 60) -> Dict:
        """Check if any thresholds have been exceeded"""
        counts = self.get_event_counts(minutes)
        alerts = []

        # Convert minutes to appropriate units
        if minutes >= 60:
            time_unit = "hour"
            multiplier = 60 / minutes
        else:
            time_unit = "minute"
            multiplier = 1

        for threshold_name, threshold_value in self.alert_thresholds.items():
            # Parse threshold name: "auth_failures_per_hour" -> "AUTH_FAILURE", threshold_per_hour
            parts = threshold_name.split("_per_")
            if len(parts) != 2:
                continue

            event_key = parts[0].upper().replace("_", "_")
            if event_key == "AUTH":  # Special case
                event_key = "AUTH_FAILURE"
            elif event_key == "AUTHZ":  # Special case
                event_key = "AUTHZ_VIOLATION"
            elif event_key == "CIRCUIT":  # Special case
                event_key = "CIRCUIT_BREAKER"
            elif event_key == "RATE":  # Special case
                event_key = "RATE_LIMIT"
            elif event_key == "SCHEMA":  # Special case
                event_key = "SCHEMA_VIOLATION"

            # Count actual events
            actual_count = counts.get(event_key, 0)

            # Adjust to per-hour or per-minute basis
            if time_unit == "minute":
                # Threshold is per minute, already matches
                adjusted_actual = actual_count
                adjusted_threshold = threshold_value
            else:
                # Threshold is per hour, need to adjust actual to hourly
                adjusted_actual = actual_count * multiplier
                adjusted_threshold = threshold_value

            if adjusted_actual > adjusted_threshold:
                alerts.append({
                    "threshold": threshold_name,
                    "required_max": adjusted_threshold,
                    "actual": adjusted_actual,
                    "severity": "high" if adjusted_actual > adjusted_threshold * 2 else "medium"
                })

        return {
            "alerts": alerts,
            "thresholds_checked": len(self.alert_thresholds),
            "violations": len(alerts),
            "time_period_minutes": minutes
        }

    def generate_compliance_report(self, hours: int = 24) -> Dict:
        """Generate comprehensive security compliance report"""
        minutes = hours * 60

        # Get recent events
        recent_events = self.get_recent_events(minutes=minutes)

        # Event breakdown by type
        event_breakdown = self.get_event_counts(minutes)

        # Alert status
        alert_check = self.check_alert_thresholds(minutes=minutes)

        # Student-level summary
        student_summary = defaultdict(lambda: {"events": 0, "types": set()})

        for event in recent_events:
            student_summary[event.student_id]["events"] += 1
            student_summary[event.student_id]["types"].add(event.event_type)

        # Convert to serializable format
        student_summary_serializable = {
            student_id: {
                "total_events": data["events"],
                "event_types": list(data["types"])
            }
            for student_id, data in student_summary.items()
        }

        # Risk assessment
        risk_score = self._calculate_risk_score(recent_events, alert_check)

        return {
            "report_id": f"security-report-{int(time.time())}",
            "generated_at": datetime.utcnow().isoformat(),
            "period_hours": hours,
            "summary": {
                "total_events": len(recent_events),
                "event_breakdown": event_breakdown,
                "unique_students": len(student_summary),
                "alert_status": {
                    "violations": alert_check["violations"],
                    "alerts": alert_check["alerts"]
                },
                "risk_score": risk_score
            },
            "details": {
                "recent_events": len(recent_events),
                "most_common_event": max(event_breakdown, key=event_breakdown.get) if event_breakdown else "none",
                "students_with_events": student_summary_serializable
            },
            "recommendations": self._generate_recommendations(recent_events, alert_check)
        }

    def generate_audit_trail(self, student_id: Optional[str] = None, hours: int = 24) -> List[Dict]:
        """Generate detailed audit trail for compliance"""
        minutes = hours * 60
        events = self.get_recent_events(minutes=minutes)

        if student_id:
            events = [e for e in events if e.student_id == student_id]

        audit_trail = []

        for event in events:
            audit_record = {
                "timestamp": event.timestamp,
                "event_type": event.event_type,
                "student_id": event.student_id,
                "severity": event.severity,
                "details": event.details
            }
            audit_trail.append(audit_record)

        # Sort by timestamp
        audit_trail.sort(key=lambda x: x["timestamp"])

        return audit_trail

    def get_high_risk_students(self, threshold: int = 5) -> Dict[str, Dict]:
        """Identify students with suspicious activity"""
        event_counts = defaultdict(int)

        for event in self.events:
            # Consider high/medium severity events
            if event.severity in ["high", "medium"]:
                event_counts[event.student_id] += 1

        high_risk = {}
        for student_id, count in event_counts.items():
            if count >= threshold:
                high_risk[student_id] = {
                    "event_count": count,
                    "risk_level": "HIGH" if count >= threshold * 2 else "MEDIUM"
                }

        return high_risk

    def _calculate_risk_score(self, events: List[SecurityEvent], alert_check: Dict) -> str:
        """Calculate overall security risk score"""
        if not events:
            return "LOW"

        high_severity = sum(1 for e in events if e.severity == "high")
        medium_severity = sum(1 for e in events if e.severity == "medium")
        alert_violations = alert_check["violations"]

        # Risk factors
        risk_score = (
            high_severity * 3 +
            medium_severity * 1 +
            alert_violations * 2
        )

        if risk_score >= 10:
            return "CRITICAL"
        elif risk_score >= 5:
            return "HIGH"
        elif risk_score >= 2:
            return "MEDIUM"
        else:
            return "LOW"

    def _generate_recommendations(self, events: List[SecurityEvent], alert_check: Dict) -> List[str]:
        """Generate security recommendations"""
        recommendations = []

        if not events:
            recommendations.append("No security events detected in period")
            return recommendations

        event_types = set(e.event_type for e in events)

        if "AUTH_FAILURE" in event_types:
            recommendations.append("Review JWT validation and Kong configuration")
            recommendations.append("Monitor for credential stuffing attacks")

        if "AUTHZ_VIOLATION" in event_types:
            recommendations.append("Review permission assignments")
            recommendations.append("Implement additional RBAC training")

        if "SCHEMA_VIOLATION" in event_types:
            recommendations.append("Enhance input validation")
            recommendations.append("Review API documentation")

        if "CIRCUIT_BREAKER" in event_types:
            recommendations.append("Investigate agent health and dependencies")
            recommendations.append("Review circuit breaker thresholds")

        if "RATE_LIMIT" in event_types:
            recommendations.append("Consider raising rate limits for legitimate users")
            recommendations.append("Implement progressive rate limiting")

        if "DAPR_FAILURE" in event_types:
            recommendations.append("Check Dapr service health and network connectivity")
            recommendations.append("Review timeout and retry configurations")

        if alert_check["violations"] > 0:
            recommendations.append("URGENT: Threshold violations detected - investigate immediately")

        return recommendations

    def export_for_compliance_system(self, hours: int = 24) -> Dict:
        """Export data in format suitable for external compliance systems"""
        report = self.generate_compliance_report(hours)

        return {
            "compliance_framework": "SOC2",
            "timestamp": report["generated_at"],
            "period": report["period_hours"],
            "findings": self._convert_to_findings(report),
            "evidence": self._get_evidence_packets(hours),
            "risk_assessment": report["summary"]["risk_score"]
        }

    def _convert_to_findings(self, report: Dict) -> List[Dict]:
        """Convert report to compliance findings format"""
        findings = []

        if report["summary"]["alert_status"]["violations"] > 0:
            for alert in report["summary"]["alert_status"]["alerts"]:
                findings.append({
                    "type": "ALERT_THRESHOLD_VIOLATION",
                    "severity": alert["severity"],
                    "description": f"Threshold {alert['threshold']} exceeded",
                    "evidence": {
                        "threshold": alert["required_max"],
                        "actual": alert["actual"]
                    }
                })

        return findings

    def _get_evidence_packets(self, hours: int) -> List[Dict]:
        """Get evidence packets for compliance audit"""
        events = self.get_recent_events(minutes=hours * 60)

        evidence_packets = []

        for event in events[:50]:  # Limit to most recent 50
            packet = {
                "event_type": event.event_type,
                "timestamp": event.timestamp,
                "student_id": event.student_id,
                "severity": event.severity,
                "details": event.details,
                "evidence_id": f"ev-{hash(event.timestamp + event.student_id) % 10000}"
            }
            evidence_packets.append(packet)

        return evidence_packets


# Global security reporter instance
security_reporter = SecurityReporter()


def report_auth_failure(student_id: str, reason: str, details: Dict) -> SecurityEvent:
    return security_reporter.record_auth_failure(student_id, reason, details)


def report_authz_violation(student_id: str, attempted: str, required: str) -> SecurityEvent:
    return security_reporter.record_authorization_violation(student_id, attempted, required)


def report_schema_violation(student_id: str, errors: List[str], raw_input: str) -> SecurityEvent:
    return security_reporter.record_schema_violation(student_id, errors, raw_input)


def report_circuit_breaker(student_id: str, agent: str, event: str, state: Dict) -> SecurityEvent:
    return security_reporter.record_circuit_breaker_event(student_id, agent, event, state)


def report_rate_limit(student_id: str, current: int, limit: int) -> SecurityEvent:
    return security_reporter.record_rate_limit_violation(student_id, current, limit)


def report_dapr_failure(student_id: str, agent: str, error: str, retries: int) -> SecurityEvent:
    return security_reporter.record_dapr_failure(student_id, agent, error, retries)


if __name__ == "__main__":
    # Test security reporter
    print("=== Security Reporter Test ===")

    # Generate test events
    report_auth_failure("student-123", "Missing JWT header", {"header": "X-Consumer-Username"})
    report_authz_violation("student-456", "triage:write", "triage:read")
    report_schema_violation("student-789", ["query too long"], "a" * 2000)
    report_circuit_breaker("student-123", "debug-agent", "OPEN", {"failure_count": 5})
    report_rate_limit("student-456", 150, 100)
    report_dapr_failure("student-789", "concepts-agent", "Connection timeout", 3)

    # Generate compliance report
    report = security_reporter.generate_compliance_report(hours=24)
    print(f"Compliance Report: {json.dumps(report, indent=2)}")

    # Generate audit trail
    audit_trail = security_reporter.generate_audit_trail()
    print(f"\nAudit Trail Entries: {len(audit_trail)}")

    # Check high-risk students
    high_risk = security_reporter.get_high_risk_students(threshold=1)
    print(f"High Risk Students: {json.dumps(high_risk, indent=2)}")

    # Export for compliance system
    export = security_reporter.export_for_compliance_system(hours=24)
    print(f"\nCompliance Export: {export['compliance_framework']} - Risk: {export['risk_assessment']}")

    print("\n✅ Security reporting working correctly")