"""
Dapr Tracing Header Injection
Elite Implementation Standard v2.0.0

Injects traceparent, tracestate into all Dapr calls for distributed tracing.
Implements W3C Trace Context standard.
"""

import uuid
import time
from typing import Dict, Optional
from dataclasses import dataclass


@dataclass
class TraceContext:
    """W3C Trace Context standard"""
    trace_id: str
    span_id: str
    parent_id: Optional[str] = None
    trace_flags: str = "01"  # Sampled

    def get_traceparent(self) -> str:
        """Generate W3C traceparent header"""
        return f"00-{self.trace_id}-{self.span_id}-{self.trace_flags}"

    def get_tracestate(self) -> str:
        """Generate W3C tracestate header"""
        # Could include vendor-specific state
        return f"learnflow=service:triage"


class DaprTracingInjector:
    """
    Injects distributed tracing headers for Dapr service invocation

    Implements W3C Trace Context standard:
    - traceparent: 00-{trace-id}-{span-id}-{trace-flags}
    - tracestate: vendor-specific state
    """

    def __init__(self):
        self.service_name = "triage-service"
        self.version = "1.0.0"

    def create_trace_context(self, request_id: str, parent_trace: Optional[str] = None) -> TraceContext:
        """
        Create new trace context for operation

        Args:
            request_id: Unique request identifier
            parent_trace: Optional parent traceparent for sub-spans
        """
        if parent_trace:
            # Parse parent trace to maintain parent-child relationship
            try:
                parts = parent_trace.split("-")
                if len(parts) == 4 and parts[0] == "00":
                    parent_trace_id = parts[1]
                    parent_span_id = parts[2]
                    # New span ID for this operation
                    span_id = self._generate_span_id()
                    return TraceContext(
                        trace_id=parent_trace_id,
                        span_id=span_id,
                        parent_id=parent_span_id
                    )
            except:
                pass

        # Create completely new trace
        trace_id = self._generate_trace_id()
        span_id = self._generate_span_id()

        return TraceContext(
            trace_id=trace_id,
            span_id=span_id,
            parent_id=None
        )

    def inject_for_dapr_call(
        self,
        target_app_id: str,
        request_id: str,
        operation_name: str,
        parent_context: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        Generate tracing headers for Dapr service invocation

        Args:
            target_app_id: Target Dapr app ID
            request_id: Request identifier
            operation_name: Name of operation being called
            parent_context: Optional parent trace context

        Returns:
            Dictionary of headers to inject
        """
        # Extract parent trace if available
        parent_trace = None
        if parent_context:
            parent_trace = parent_context.get("traceparent")

        # Create trace context
        trace_context = self.create_trace_context(request_id, parent_trace)

        # Base headers
        headers = {
            "traceparent": trace_context.get_traceparent(),
            "tracestate": trace_context.get_tracestate(),
            "X-Request-ID": request_id,
            "X-Operation-Name": operation_name,
            "X-Caller-Service": self.service_name
        }

        # Add baggage for correlation
        baggage = self._create_baggage(target_app_id, operation_name)
        headers.update(baggage)

        return headers

    def inject_for_dapr_publish(
        self,
        topic_name: str,
        request_id: str,
        parent_context: Optional[Dict] = None
    ) -> Dict[str, str]:
        """
        Generate tracing headers for Dapr pub/sub publishing

        Args:
            topic_name: Target topic name
            request_id: Request identifier
            parent_context: Optional parent trace context

        Returns:
            Dictionary of headers to inject
        """
        parent_trace = None
        if parent_context:
            parent_trace = parent_context.get("traceparent")

        trace_context = self.create_trace_context(request_id, parent_trace)

        return {
            "traceparent": trace_context.get_traceparent(),
            "tracestate": trace_context.get_tracestate(),
            "X-Request-ID": request_id,
            "X-Topic": topic_name,
            "X-Publisher": self.service_name,
            "X-Message-Type": "triage-audit"
        }

    def parse_traceparent(self, traceparent: str) -> Optional[TraceContext]:
        """
        Parse traceparent header into TraceContext

        Format: 00-{trace-id}-{span-id}-{trace-flags}
        """
        try:
            parts = traceparent.split("-")
            if len(parts) == 4 and parts[0] == "00":
                return TraceContext(
                    trace_id=parts[1],
                    span_id=parts[2],
                    trace_flags=parts[3]
                )
        except:
            pass
        return None

    def _generate_trace_id(self) -> str:
        """Generate 32-character trace ID"""
        return uuid.uuid4().hex + uuid.uuid4().hex

    def _generate_span_id(self) -> str:
        """Generate 16-character span ID"""
        return uuid.uuid4().hex[:16]

    def _create_baggage(self, target_app_id: str, operation: str) -> Dict[str, str]:
        """Create baggage headers for additional context"""
        return {
            "baggage-service": self.service_name,
            "baggage-target": target_app_id,
            "baggage-operation": operation,
            "baggage-version": self.version,
            "baggage-timestamp": str(int(time.time()))
        }

    def create_span_for_classification(self, request_id: str, query_length: int) -> Dict[str, str]:
        """Create tracing headers for intent classification span"""
        trace_context = self.create_trace_context(request_id)

        headers = {
            "traceparent": trace_context.get_traceparent(),
            "tracestate": trace_context.get_tracestate(),
            "X-Span-Type": "classification",
            "X-Query-Length": str(query_length),
            "X-Classification-Engine": "triage-logic-skills"
        }

        return headers

    def create_span_for_routing(self, request_id: str, intent: str, target_agent: str) -> Dict[str, str]:
        """Create tracing headers for routing decision span"""
        trace_context = self.create_trace_context(request_id)

        headers = {
            "traceparent": trace_context.get_traceparent(),
            "tracestate": trace_context.get_tracestate(),
            "X-Span-Type": "routing",
            "X-Intent": intent,
            "X-Target-Agent": target_agent
        }

        return headers

    def get_trace_summary(self, traceparent: str) -> Dict:
        """Get human-readable trace summary"""
        context = self.parse_traceparent(traceparent)
        if not context:
            return {"error": "Invalid traceparent"}

        return {
            "trace_id": context.trace_id,
            "span_id": context.span_id,
            "trace_flags": context.trace_flags,
            "sampled": context.trace_flags == "01",
            "traceparent": traceparent,
            "service": self.service_name
        }


# Global tracer instance
tracer = DaprTracingInjector()


def inject_dapr_headers(
    target_app_id: str,
    request_id: str,
    operation_name: str,
    parent_context: Optional[Dict] = None
) -> Dict[str, str]:
    """Convenience function to inject headers for Dapr call"""
    return tracer.inject_for_dapr_call(
        target_app_id, request_id, operation_name, parent_context
    )


def inject_pubsub_headers(
    topic_name: str,
    request_id: str,
    parent_context: Optional[Dict] = None
) -> Dict[str, str]:
    """Convenience function to inject headers for Dapr pub/sub"""
    return tracer.inject_for_dapr_publish(
        topic_name, request_id, parent_context
    )


if __name__ == "__main__":
    # Test tracing injection
    print("=== Dapr Tracing Injector Test ===")

    # Test 1: Basic trace injection
    headers = tracer.inject_for_dapr_call(
        target_app_id="debug-agent",
        request_id="req-12345",
        operation_name="process_syntax_query"
    )

    print("Dapr Call Headers:")
    for key, value in headers.items():
        print(f"  {key}: {value}")

    # Test 2: Parse traceparent
    traceparent = headers["traceparent"]
    context = tracer.parse_traceparent(traceparent)

    print(f"\nParsed Context:")
    print(f"  Trace ID: {context.trace_id}")
    print(f"  Span ID: {context.span_id}")
    print(f"  Flags: {context.trace_flags}")

    # Test 3: Parent-child relationship
    print(f"\nParent-Child Test:")
    child_headers = tracer.inject_for_dapr_call(
        target_app_id="concepts-agent",
        request_id="req-12345",
        operation_name="explain_concept",
        parent_context={"traceparent": traceparent}
    )

    parent_span = tracer.parse_traceparent(traceparent)
    child_span = tracer.parse_traceparent(child_headers["traceparent"])

    print(f"  Parent Span: {parent_span.span_id}")
    print(f"  Child Span: {child_span.span_id}")
    print(f"  Same Trace: {parent_span.trace_id == child_span.trace_id}")

    # Test 4: Classification span
    class_headers = tracer.create_span_for_classification("req-12345", len("help with my code"))
    print(f"\nClassification Span Headers:")
    for key, value in class_headers.items():
        print(f"  {key}: {value}")

    print("\n✅ Tracing injection working correctly")