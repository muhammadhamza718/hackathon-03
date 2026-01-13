"""
Rate Limiting Middleware
Elite Implementation Standard v2.0.0

Implements token bucket rate limiting per student.
"""

import time
import asyncio
from collections import defaultdict
from typing import Dict, Optional, Tuple
from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
import threading


class TokenBucket:
    """
    Token bucket implementation for rate limiting.

    Algorithm:
    - Each student has a bucket with capacity = max_requests
    - Tokens refill at rate = requests per second
    - Each request consumes 1 token
    - If bucket empty, request is rejected
    """

    def __init__(self, capacity: int, refill_rate: float):
        """
        Initialize token bucket.

        Args:
            capacity: Maximum tokens (requests) bucket can hold
            refill_rate: Tokens per second to add to bucket
        """
        self.capacity = capacity
        self.refill_rate = refill_rate
        self.tokens = capacity
        self.last_refill = time.time()
        self.lock = threading.Lock()

    def consume(self, tokens: int = 1) -> Tuple[bool, float]:
        """
        Consume tokens from bucket.

        Args:
            tokens: Number of tokens to consume

        Returns:
            Tuple of (success, time_until_refill)
        """
        with self.lock:
            now = time.time()

            # Refill bucket
            elapsed = now - self.last_refill
            refill_amount = elapsed * self.refill_rate
            self.tokens = min(self.capacity, self.tokens + refill_amount)
            self.last_refill = now

            # Check if enough tokens
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True, 0.0

            # Calculate time until next refill
            tokens_needed = tokens - self.tokens
            time_needed = tokens_needed / self.refill_rate
            return False, time_needed

    def get_status(self) -> dict:
        """Get current bucket status"""
        with self.lock:
            now = time.time()
            elapsed = now - self.last_refill
            refill_amount = elapsed * self.refill_rate
            current_tokens = min(self.capacity, self.tokens + refill_amount)

            return {
                "current_tokens": round(current_tokens, 2),
                "max_tokens": self.capacity,
                "refill_rate": self.refill_rate,
                "available_percent": round((current_tokens / self.capacity) * 100, 1)
            }


class RateLimitingMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using token bucket algorithm.

    Default: 100 requests per minute per student
    """

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60):
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.buckets: Dict[str, TokenBucket] = defaultdict(
            lambda: TokenBucket(capacity=max_requests, refill_rate=max_requests/window_seconds)
        )
        self._cleanup_task = None

    async def dispatch(self, request: Request, call_next) -> Response:
        """
        Check rate limit before processing request.

        Args:
            request: FastAPI request
            call_next: Next handler

        Returns:
            Response (allowed) or 429 (rate limited)
        """
        # Only apply to POST /api/v1/triage
        if request.method != "POST" or request.url.path != "/api/v1/triage":
            return await call_next(request)

        # Extract student ID from security context
        security_context = getattr(request.state, 'security_context', None)
        student_id = security_context.get('student_id') if security_context else None

        if not student_id:
            # No auth context, skip rate limiting (auth middleware will handle)
            return await call_next(request)

        # Get bucket for this student
        bucket = self.buckets[student_id]

        # Try to consume token
        success, time_until_refill = bucket.consume(1)

        if not success:
            # Rate limit exceeded
            retry_after = int(time_until_refill) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail={
                    "error": "RATE_LIMIT_EXCEEDED",
                    "message": f"Rate limit exceeded. {self.max_requests} requests per {self.window_seconds}s.",
                    "retry_after": retry_after,
                    "student_id": student_id
                },
                headers={
                    "Retry-After": str(retry_after),
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(time.time() + time_until_refill))
                }
            )

        # Allow request and add rate limit headers
        response = await call_next(request)

        status_data = bucket.get_status()
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(int(status_data["current_tokens"]))
        response.headers["X-RateLimit-Reset"] = str(int(time.time() + self.window_seconds))

        return response

    async def get_student_status(self, student_id: str) -> dict:
        """Get rate limit status for specific student"""
        bucket = self.buckets.get(student_id)
        if not bucket:
            return {"error": "No activity for this student yet"}

        return bucket.get_status()

    def cleanup_old_buckets(self, max_age_seconds: int = 3600):
        """
        Clean up old buckets to prevent memory leaks.

        Args:
            max_age_seconds: Maximum age of bucket before removal
        """
        now = time.time()
        to_remove = []

        for student_id, bucket in self.buckets.items():
            with bucket.lock:
                elapsed = now - bucket.last_refill
                if elapsed > max_age_seconds:
                    to_remove.append(student_id)

        for student_id in to_remove:
            del self.buckets[student_id]


# Functional middleware for simpler implementation
class SimpleRateLimiter:
    """
    Simple in-memory rate limiter for testing or lightweight use.
    """

    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = defaultdict(list)
        self.lock = asyncio.Lock()

    async def check_limit(self, key: str) -> Tuple[bool, int]:
        """
        Check if request is within rate limit.

        Args:
            key: Identifier (student_id)

        Returns:
            Tuple of (allowed, remaining_requests)
        """
        async with self.lock:
            now = time.time()
            cutoff = now - self.window_seconds

            # Clean old requests
            self.requests[key] = [
                req_time for req_time in self.requests[key]
                if req_time > cutoff
            ]

            # Check limit
            if len(self.requests[key]) >= self.max_requests:
                return False, 0

            # Record request
            self.requests[key].append(now)
            remaining = self.max_requests - len(self.requests[key])
            return True, remaining


# FastAPI dependency
async def rate_limit_dependency(
    request: Request,
    max_requests: int = 100,
    window_seconds: int = 60
):
    """
    FastAPI dependency for rate limiting.

    Usage:
        @app.post("/endpoint")
        async def endpoint(
            rate_limit: None = Depends(rate_limit_dependency)
        ):
            ...
    """
    # Skip for non-triage endpoints
    if request.method != "POST" or request.url.path != "/api/v1/triage":
        return

    security_context = getattr(request.state, 'security_context', None)
    student_id = security_context.get('student_id') if security_context else None

    if not student_id:
        return

    # Get simple rate limiter (could be enhanced to use main middleware)
    limiter = SimpleRateLimiter(max_requests, window_seconds)
    allowed, remaining = await limiter.check_limit(student_id)

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={
                "error": "RATE_LIMIT_EXCEEDED",
                "message": f"Rate limit: {max_requests} requests per {window_seconds}s"
            },
            headers={"X-RateLimit-Remaining": "0"}
        )


def get_rate_limit_summary() -> dict:
    """
    Get summary of current rate limiting state.

    Returns:
        Dictionary with rate limit configuration and statistics
    """
    return {
        "policy": "token_bucket",
        "max_requests": 100,
        "window_seconds": 60,
        "requests_per_minute": 100,
        "algorithm": "leaky_bucket",
        "description": "100 requests per minute per student",
        "note": "Rate limiting protects against abuse and ensures fair resource allocation"
    }