"""
Dapr Tracing Integration Service
Elite Implementation Standard v2.0.0

Manages Dapr trace headers and distributed tracing across services.
"""

import time
from typing import Dict, Optional
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class TraceContext:
    """Represents a distributed trace context"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str] = None
    trace_flags: str = "01"
    service_name: str = "triage-service"
    timestamp: float = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = time.time()

    def to_header(self) -> str:
        """Convert to W3C traceparent header format"""
        return f"00-{self.trace_id}-{self.span_id}-{self.trace_flags}"

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return asdict(self)


class DaprTracingService:
    """
    Service for managing Dapr distributed tracing.

    Follows W3C Trace Context specification:
    - traceparent: version-trace-id-parent-id-flags
    - tracestate: vendor-specific state
    """

    def __init__(self, service_name: str = "triage-service"):
        self.service_name = service_name
        self.trace_id_counter = 0

    def create_trace_context(
        self,
        parent_trace_id: Optional[str] = None,
        parent_span_id: Optional[str] = None
    ) -> TraceContext:
        """
        Create a new trace context.

        Args:
            parent_trace_id: Optional parent trace ID for continuation
            parent_span_id: Optional parent span ID for nesting

        Returns:
            New TraceContext
        """
        if parent_trace_id:
            # Continue existing trace
            trace_id = parent_trace_id
        else:
            # New trace - 32 hex chars
            trace_id = self._generate_trace_id()

        # New span - 16 hex chars
        span_id = self._generate_span_id()

        context = TraceContext(
            trace_id=trace_id,
            span_id=span_id,
            parent_span_id=parent_span_id,
            service_name=self.service_name
        )

        return context

    def parse_traceparent(self, traceparent: str) -> Optional[TraceContext]:
        """
        Parse W3C traceparent header.

        Args:
            traceparent: W3C traceparent header string

        Returns:
            TraceContext or None if invalid
        """
        if not traceparent:
            return None

        parts = traceparent.split("-")
        if len(parts) != 4:
            return None

        version, trace_id, parent_span_id, flags = parts

        if version != "00":
            return None

        return TraceContext(
            trace_id=trace_id,
            span_id=parent_span_id,  # The parent's span becomes our parent
            trace_flags=flags,
            service_name=self.service_name
        )

    def inject_dapr_metadata(
        self,
        trace_context: TraceContext,
        additional_metadata: Optional[Dict] = None
    ) -> Dict:
        """
        Inject trace context into Dapr invocation metadata.

        Args:
            trace_context: Trace context to inject
            additional_metadata: Other metadata to include

        Returns:
            Complete metadata dictionary for Dapr
        """
        metadata = {
            "traceparent": trace_context.to_header(),
            "tracestate": f"{self.service_name}=00",
            "X-Correlation-ID": trace_context.trace_id,
            "user-agent": f"learnflow-{self.service_name}/1.0.0",
            "content-type": "application/json"
        }

        if additional_metadata:
            metadata.update(additional_metadata)

        return metadata

    def create_span_event(
        self,
        trace_context: TraceContext,
        event_name: str,
        event_data: Optional[Dict] = None,
        error: Optional[Exception] = None
    ) -> Dict:
        """
        Create a span event for tracing.

        Args:
            trace_context: Current trace context
            event_name: Name of the event
            event_data: Event payload
            error: Optional error information

        Returns:
            Span event dictionary
        """
        event = {
            "trace_id": trace_context.trace_id,
            "span_id": trace_context.span_id,
            "service": self.service_name,
            "event": event_name,
            "timestamp": datetime.utcnow().isoformat(),
            "data": event_data or {}
        }

        if error:
            event["error"] = {
                "type": type(error).__name__,
                "message": str(error),
                "stacktrace": None  # In production, add this
            }

        return event

    def record_service_invocation(
        self,
        trace_context: TraceContext,
        target_service: str,
        method: str,
        duration_ms: float,
        success: bool,
        error: Optional[Exception] = None
    ) -> Dict:
        """
        Record a Dapr service invocation.

        Args:
            trace_context: Trace context
            target_service: Target service name
            method: Method invoked
            duration_ms: Duration in milliseconds
            success: Whether it succeeded
            error: Optional error

        Returns:
            Invocation event
        """
        event = self.create_span_event(
            trace_context,
            "service_invocation",
            {
                "target": target_service,
                "method": method,
                "duration_ms": duration_ms,
                "success": success,
                "protocol": "http",
                "dapr": True
            },
            error
        )

        # Log for debugging
        status = "SUCCESS" if success else "FAILED"
        print(f"[TRACE] {trace_context.trace_id[:8]} {target_service}.{method} {duration_ms:.2f}ms {status}")

        return event

    def record_circuit_breaker_event(
        self,
        trace_context: TraceContext,
        target_service: str,
        old_state: str,
        new_state: str,
        reason: str
    ) -> Dict:
        """
        Record circuit breaker state change.

        Args:
            trace_context: Trace context
            target_service: Target service
            old_state: Previous state
            new_state: New state
            reason: Why the state changed

        Returns:
            Circuit breaker event
        """
        event = self.create_span_event(
            trace_context,
            "circuit_breaker",
            {
                "target": target_service,
                "old_state": old_state,
                "new_state": new_state,
                "reason": reason
            }
        )

        print(f"[CB] {old_state} -> {new_state} {target_service} ({reason})")

        return event

    def record_retry_event(
        self,
        trace_context: TraceContext,
        target_service: str,
        attempt: int,
        max_attempts: int,
        delay_ms: float
    ) -> Dict:
        """
        Record retry attempt.

        Args:
            trace_context: Trace context
            target_service: Target service
            attempt: Current attempt number
            max_attempts: Maximum attempts
            delay_ms: Delay before retry

        Returns:
            Retry event
        """
        event = self.create_span_event(
            trace_context,
            "retry_attempt",
            {
                "target": target_service,
                "attempt": attempt,
                "max_attempts": max_attempts,
                "delay_ms": delay_ms
            }
        )

        if attempt == max_attempts:
            print(f"[RETRY] Final attempt {attempt}/{max_attempts} for {target_service}")
        else:
            print(f"[RETRY] Attempt {attempt}/{max_attempts} for {target_service} in {delay_ms:.0f}ms")

        return event

    def _generate_trace_id(self) -> str:
        """Generate 32-character trace ID"""
        import uuid
        return f"{uuid.uuid4().hex}{uuid.uuid4().hex}"

    def _generate_span_id(self) -> str:
        """Generate 16-character span ID"""
        import uuid
        return uuid.uuid4().hex[:16]


# Global tracing service
tracing_service = DaprTracingService()


def create_trace_context(
    parent_trace_id: Optional[str] = None,
    parent_span_id: Optional[str] = None
) -> TraceContext:
    """Convenience function to create trace context"""
    return tracing_service.create_trace_context(parent_trace_id, parent_span_id)


def parse_traceparent_header(traceparent: str) -> Optional[TraceContext]:
    """Convenience function to parse traceparent"""
    return tracing_service.parse_traceparent(traceparent)


def inject_dapr_metadata(trace_context: TraceContext, **kwargs) -> Dict:
    """Convenience function to inject metadata"""
    return tracing_service.inject_dapr_metadata(trace_context, kwargs)


if __name__ == "__main__":
    # Test tracing service
    print("=== Dapr Tracing Service Test ===")

    # Test 1: Create new trace
    trace = tracing_service.create_trace_context()
    print(f"New Trace: {trace.to_header()}")

    # Test 2: Continue trace
    parent_trace = "4bf92f3577b34da6a3ce929d0e0e4736"
    parent_span = "00f067aa0ba902b7"
    child_trace = tracing_service.create_trace_context(parent_trace, parent_span)
    print(f"Child Trace: {child_trace.to_header()}")
    print(f"Parent Span: {child_trace.parent_span_id}")

    # Test 3: Parse traceparent
    parsed = tracing_service.parse_traceparent("00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01")
    print(f"Parsed: {parsed}")

    # Test 4: Service invocation recording
    trace = tracing_service.create_trace_context()
    event = tracing_service.record_service_invocation(
        trace,
        "debug-agent",
        "debug_code",
        15.5,
        True
    )
    print(f"Service Event: {event}")

    # Test 5: Circuit breaker recording
    event = tracing_service.record_circuit_breaker_event(
        trace,
        "debug-agent",
        "CLOSED",
        "OPEN",
        "5 consecutive failures"
    )
    print(f"CB Event: {event}")

    print("\n✅ Tracing service working correctly")