"""
Dapr Tracing Middleware
Elite Implementation Standard v2.0.0

Injects W3C Trace Context headers for distributed tracing across services.
"""

import time
import uuid
from typing import Optional
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware


class DaprTracingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that injects Dapr tracing headers (traceparent, tracestate)
    into every request and response for distributed tracing.
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Process request and inject tracing headers.

        Args:
            request: FastAPI request object
            call_next: Next middleware or endpoint handler

        Returns:
            Response with tracing headers
        """
        # Extract existing trace context or create new
        traceparent = request.headers.get("traceparent")
        tracestate = request.headers.get("tracestate")

        # Generate new trace ID if not present
        if not traceparent:
            trace_id = self._generate_trace_id()
            span_id = self._generate_span_id()
            traceparent = f"00-{trace_id}-{span_id}-01"
            tracestate = "learnflow=00"
        else:
            # Extract trace_id and generate new span_id
            parts = traceparent.split("-")
            if len(parts) == 4:
                trace_id = parts[1]
                span_id = self._generate_span_id()
                traceparent = f"00-{trace_id}-{span_id}-01"
            else:
                # Fallback to new trace
                trace_id = self._generate_trace_id()
                span_id = self._generate_span_id()
                traceparent = f"00-{trace_id}-{span_id}-01"

        # Add trace context to request state for use in services
        request.state.traceparent = traceparent
        request.state.tracestate = tracestate
        request.state.trace_id = trace_id
        request.state.span_id = span_id

        # Process request
        start_time = time.time()
        response = await call_next(request)
        duration = (time.time() - start_time) * 1000  # ms

        # Add tracing headers to response
        response.headers["traceparent"] = traceparent
        response.headers["tracestate"] = tracestate
        response.headers["X-Trace-ID"] = trace_id
        response.headers["X-Span-ID"] = span_id
        response.headers["X-Trace-Duration"] = f"{duration:.2f}ms"

        # Add correlation ID if not present
        if "X-Correlation-ID" not in response.headers:
            correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))
            response.headers["X-Correlation-ID"] = correlation_id

        return response

    def _generate_trace_id(self) -> str:
        """Generate 32-character hex trace ID"""
        return f"{uuid.uuid4().hex}{uuid.uuid4().hex}"

    def _generate_span_id(self) -> str:
        """Generate 16-character hex span ID"""
        return uuid.uuid4().hex[:16]


async def tracing_middleware(request: Request, call_next):
    """
    Functional middleware wrapper for Dapr tracing.

    Args:
        request: FastAPI request
        call_next: Next handler

    Returns:
        Response with tracing
    """
    # Check if already processed by class-based middleware
    if hasattr(request.state, 'traceparent'):
        return await call_next(request)

    # Generate trace context
    trace_id = f"{uuid.uuid4().hex}{uuid.uuid4().hex}"
    span_id = uuid.uuid4().hex[:16]
    traceparent = f"00-{trace_id}-{span_id}-01"
    tracestate = "learnflow=00"

    # Store in request state
    request.state.traceparent = traceparent
    request.state.tracestate = tracestate
    request.state.trace_id = trace_id
    request.state.span_id = span_id

    # Call next handler
    start_time = time.time()
    response = await call_next(request)
    duration = (time.time() - start_time) * 1000

    # Add headers to response
    response.headers["traceparent"] = traceparent
    response.headers["tracestate"] = tracestate
    response.headers["X-Trace-ID"] = trace_id
    response.headers["X-Span-ID"] = span_id
    response.headers["X-Trace-Duration"] = f"{duration:.2f}ms"

    return response


def get_trace_context(request: Request) -> dict:
    """
    Extract trace context from request.

    Args:
        request: FastAPI request

    Returns:
        Dictionary with trace context
    """
    return {
        "traceparent": getattr(request.state, 'traceparent', None),
        "tracestate": getattr(request.state, 'tracestate', None),
        "trace_id": getattr(request.state, 'trace_id', None),
        "span_id": getattr(request.state, 'span_id', None),
        "correlation_id": request.headers.get("X-Correlation-ID")
    }


def inject_dapr_headers(traceparent: str, tracestate: str, student_id: str) -> dict:
    """
    Generate Dapr metadata headers for service invocation.

    Args:
        traceparent: W3C traceparent header
        tracestate: W3C tracestate header
        student_id: Student identifier

    Returns:
        Dictionary of Dapr metadata headers
    """
    return {
        "traceparent": traceparent,
        "tracestate": tracestate,
        "student_id": student_id,
        "user-agent": "learnflow-triage-service/1.0.0",
        "content-type": "application/json"
    }