"""
Circuit Breaker Health Monitoring Service
Elite Implementation Standard v2.0.0

Monitors circuit breaker states and triggers alerts when circuits open.
"""

import time
import asyncio
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


@dataclass
class CircuitBreakerStatus:
    """Real-time circuit breaker status"""
    agent_name: str
    state: CircuitState
    failure_count: int
    last_failure_time: Optional[float]
    next_retry_time: Optional[float]
    threshold: int
    timeout_seconds: int

    def to_dict(self) -> Dict:
        """Convert to serializable dictionary"""
        return {
            "agent_name": self.agent_name,
            "state": self.state.value,
            "failure_count": self.failure_count,
            "last_failure_time": self.last_failure_time,
            "next_retry_time": self.next_retry_time,
            "threshold": self.threshold,
            "timeout_seconds": self.timeout_seconds,
            "can_attempt": self.state != CircuitState.OPEN or (
                self.next_retry_time and time.time() >= self.next_retry_time
            )
        }


@dataclass
class Alert:
    """Alert for circuit breaker events"""
    severity: AlertSeverity
    agent_name: str
    event_type: str
    message: str
    timestamp: float
    metadata: Optional[Dict] = None

    def to_dict(self) -> Dict:
        return {
            "severity": self.severity.value,
            "agent_name": self.agent_name,
            "event_type": self.event_type,
            "message": self.message,
            "timestamp": datetime.fromtimestamp(self.timestamp).isoformat(),
            "metadata": self.metadata or {}
        }


class CircuitBreakerMonitor:
    """
    Monitors circuit breaker health and triggers alerts.

    Tracks:
    - Circuit states for all agents
    - Failure patterns
    - Recovery events
    - Alert thresholds
    """

    def __init__(self):
        self.status_map: Dict[str, CircuitBreakerStatus] = {}
        self.alert_history: List[Alert] = []
        self.alert_listeners: List[callable] = []  # Callback functions
        self.thresholds = {
            "failure_rate_warning": 0.3,  # 30% failure rate triggers warning
            "failure_rate_critical": 0.5,  # 50% failure rate triggers critical
            "min_failures_for_alert": 3
        }

    def update_status(
        self,
        agent_name: str,
        state: CircuitState,
        failure_count: int,
        threshold: int = 5,
        timeout_seconds: int = 30,
        next_retry_time: Optional[float] = None
    ) -> CircuitBreakerStatus:
        """
        Update circuit breaker status.

        Args:
            agent_name: Name of the agent
            state: Current state
            failure_count: Number of consecutive failures
            threshold: Failure threshold
            timeout_seconds: Timeout duration
            next_retry_time: When next retry allowed

        Returns:
            Updated status
        """
        if agent_name not in self.status_map:
            self.status_map[agent_name] = CircuitBreakerStatus(
                agent_name=agent_name,
                state=CircuitState.CLOSED,
                failure_count=0,
                last_failure_time=None,
                next_retry_time=None,
                threshold=threshold,
                timeout_seconds=timeout_seconds
            )

        status = self.status_map[agent_name]

        # Track state transitions
        old_state = status.state
        status.state = state
        status.failure_count = failure_count
        status.last_failure_time = time.time() if failure_count > 0 else None
        status.next_retry_time = next_retry_time
        status.threshold = threshold
        status.timeout_seconds = timeout_seconds

        # Generate alerts on state changes
        if old_state != state:
            self._handle_state_transition(agent_name, old_state, state, failure_count)

        return status

    def _handle_state_transition(
        self,
        agent_name: str,
        old_state: CircuitState,
        new_state: CircuitState,
        failure_count: int
    ):
        """Handle circuit state transition and generate alerts"""
        timestamp = time.time()

        if new_state == CircuitState.OPEN:
            # Critical alert - circuit opened
            alert = Alert(
                severity=AlertSeverity.CRITICAL,
                agent_name=agent_name,
                event_type="CIRCUIT_OPENED",
                message=f"Circuit breaker OPENED for {agent_name} after {failure_count} failures",
                timestamp=timestamp,
                metadata={
                    "old_state": old_state.value,
                    "new_state": new_state.value,
                    "failure_count": failure_count
                }
            )
            self._record_alert(alert)

        elif new_state == CircuitState.HALF_OPEN:
            # Warning alert - testing recovery
            alert = Alert(
                severity=AlertSeverity.WARNING,
                agent_name=agent_name,
                event_type="CIRCUIT_HALF_OPEN",
                message=f"Circuit breaker HALF_OPEN for {agent_name} - testing recovery",
                timestamp=timestamp,
                metadata={
                    "old_state": old_state.value,
                    "new_state": new_state.value
                }
            )
            self._record_alert(alert)

        elif new_state == CircuitState.CLOSED and old_state == CircuitState.HALF_OPEN:
            # Info alert - successful recovery
            alert = Alert(
                severity=AlertSeverity.INFO,
                agent_name=agent_name,
                event_type="CIRCUIT_RECOVERED",
                message=f"Circuit breaker RECOVERED for {agent_name} - back to normal",
                timestamp=timestamp,
                metadata={
                    "old_state": old_state.value,
                    "new_state": new_state.value
                }
            )
            self._record_alert(alert)

    def _record_alert(self, alert: Alert):
        """Record alert and notify listeners"""
        self.alert_history.append(alert)

        # Print to console
        print(f"[ALERT] [{alert.severity.value.upper()}] {alert.agent_name}: {alert.message}")

        # Notify listeners
        for listener in self.alert_listeners:
            try:
                listener(alert.to_dict())
            except Exception as e:
                print(f"Alert listener error: {e}")

    def register_alert_listener(self, callback):
        """
        Register a callback for alerts.

        Args:
            callback: Function that takes alert dict
        """
        self.alert_listeners.append(callback)

    def get_status(self, agent_name: str) -> Optional[CircuitBreakerStatus]:
        """Get current status for an agent"""
        return self.status_map.get(agent_name)

    def get_all_status(self) -> Dict[str, CircuitBreakerStatus]:
        """Get all agent statuses"""
        return self.status_map.copy()

    def get_status_summary(self) -> Dict:
        """Get summary of all circuit breaker states"""
        status_map = self.get_all_status()
        total = len(status_map)
        open_count = sum(1 for s in status_map.values() if s.state == CircuitState.OPEN)
        closed_count = sum(1 for s in status_map.values() if s.state == CircuitState.CLOSED)
        half_open_count = sum(1 for s in status_map.values() if s.state == CircuitState.HALF_OPEN)

        return {
            "total_agents": total,
            "closed": closed_count,
            "open": open_count,
            "half_open": half_open_count,
            "degraded": open_count + half_open_count
        }

    def get_recent_alerts(self, limit: int = 10, severity: Optional[AlertSeverity] = None) -> List[Dict]:
        """
        Get recent alerts.

        Args:
            limit: Number of alerts to return
            severity: Filter by severity

        Returns:
            List of alert dictionaries
        """
        alerts = self.alert_history

        if severity:
            alerts = [a for a in alerts if a.severity == severity]

        return [a.to_dict() for a in alerts[-limit:]]

    def analyze_failure_patterns(self, agent_name: str) -> Dict:
        """
        Analyze failure patterns for an agent.

        Args:
            agent_name: Agent to analyze

        Returns:
            Analysis report
        """
        status = self.status_map.get(agent_name)
        if not status or not status.last_failure_time:
            return {"error": "No failure data"}

        # Calculate failure rate over time window
        window_seconds = 300  # 5 minutes
        recent_alerts = [
            a for a in self.alert_history
            if a.agent_name == agent_name
            and time.time() - a.timestamp < window_seconds
            and a.event_type == "CIRCUIT_OPENED"
        ]

        failure_rate = len(recent_alerts) / (window_seconds / 60)  # per minute

        # Determine pattern
        pattern = "stable"
        if failure_rate > 0.5:
            pattern = "degrading"
        elif failure_rate > 1.0:
            pattern = "critical"

        return {
            "agent_name": agent_name,
            "current_state": status.state.value,
            "failure_count": status.failure_count,
            "failure_rate_per_minute": round(failure_rate, 2),
            "pattern": pattern,
            "last_failure": datetime.fromtimestamp(status.last_failure_time).isoformat() if status.last_failure_time else None,
            "recommendation": self._get_recommendation(status, failure_rate)
        }

    def _get_recommendation(self, status: CircuitBreakerStatus, failure_rate: float) -> str:
        """Get recommendation based on state and failure rate"""
        if status.state == CircuitState.OPEN:
            return "Investigate agent health. Check logs and resource usage."
        elif status.state == CircuitState.HALF_OPEN:
            return "Monitoring recovery. Agent should return to service soon."
        elif failure_rate > 0.5:
            return "High failure rate detected. Prepare for circuit opening."
        else:
            return "Stable. No immediate action needed."

    def get_health_score(self) -> Dict:
        """
        Calculate overall health score (0-100).

        Returns:
            Health score with breakdown
        """
        status_map = self.get_all_status()
        if not status_map:
            return {"score": 100, "message": "No agents monitored"}

        total = len(status_map)
        open_count = sum(1 for s in status_map.values() if s.state == CircuitState.OPEN)
        half_open_count = sum(1 for s in status_map.values() if s.state == CircuitState.HALF_OPEN)

        # Calculate score
        if total == 0:
            score = 100
        else:
            degraded_ratio = (open_count + half_open_count * 0.5) / total
            score = max(0, 100 - (degraded_ratio * 100))

        # Determine status
        if score >= 80:
            status = "healthy"
        elif score >= 60:
            status = "degraded"
        else:
            status = "critical"

        return {
            "score": round(score, 1),
            "status": status,
            "total_agents": total,
            "healthy": total - (open_count + half_open_count),
            "degraded": half_open_count,
            "down": open_count,
            "message": f"System {status} - {score}% health"
        }

    def cleanup_old_entries(self, max_age_seconds: int = 3600):
        """
        Clean up old alert history to prevent memory leaks.

        Args:
            max_age_seconds: Maximum age of alerts to keep
        """
        cutoff_time = time.time() - max_age_seconds
        self.alert_history = [
            a for a in self.alert_history
            if a.timestamp > cutoff_time
        ]

        # Also clean up status for agents that haven't been seen in a while
        inactive_agents = [
            name for name, status in self.status_map.items()
            if status.last_failure_time and (time.time() - status.last_failure_time) > max_age_seconds
        ]

        for agent in inactive_agents:
            del self.status_map[agent]


# Global monitor instance
circuit_breaker_monitor = CircuitBreakerMonitor()


# Convenience functions
def update_circuit_status(
    agent_name: str,
    state: CircuitState,
    failure_count: int,
    threshold: int = 5,
    timeout_seconds: int = 30,
    next_retry_time: Optional[float] = None
) -> CircuitBreakerStatus:
    """Update circuit breaker status"""
    return circuit_breaker_monitor.update_status(
        agent_name, state, failure_count, threshold, timeout_seconds, next_retry_time
    )


def register_alert_handler(callback):
    """Register alert callback"""
    circuit_breaker_monitor.register_alert_listener(callback)


def get_system_health() -> Dict:
    """Get overall system health"""
    return circuit_breaker_monitor.get_health_score()


def analyze_agent(agent_name: str) -> Dict:
    """Analyze specific agent"""
    return circuit_breaker_monitor.analyze_failure_patterns(agent_name)


if __name__ == "__main__":
    # Test circuit breaker monitor
    print("=== Circuit Breaker Monitor Test ===")

    # Test 1: Update status
    status = update_circuit_status("debug-agent", CircuitState.CLOSED, 0)
    print(f"Initial: {status.to_dict()}")

    # Test 2: Simulate failures leading to open
    for i in range(1, 6):
        status = update_circuit_status("debug-agent", CircuitState.CLOSED, i)
        print(f"Failure {i}: {status.to_dict()}")

    # Open circuit
    status = update_circuit_status(
        "debug-agent",
        CircuitState.OPEN,
        5,
        next_retry_time=time.time() + 30
    )
    print(f"OPEN: {status.to_dict()}")

    # Test 3: Half-open
    time.sleep(1)
    status = update_circuit_status("debug-agent", CircuitState.HALF_OPEN, 5)
    print(f"HALF_OPEN: {status.to_dict()}")

    # Test 4: Recovery
    status = update_circuit_status("debug-agent", CircuitState.CLOSED, 0)
    print(f"RECOVERED: {status.to_dict()}")

    # Test 5: Summary
    summary = get_system_health()
    print(f"\nHealth Summary: {summary}")

    # Test 6: Analysis
    analysis = analyze_agent("debug-agent")
    print(f"Analysis: {analysis}")

    # Test 7: Alerts
    alerts = circuit_breaker_monitor.get_recent_alerts()
    print(f"\nRecent Alerts: {len(alerts)}")
    for alert in alerts:
        print(f"  - {alert['message']}")

    print("\n✅ Circuit breaker monitor working correctly")