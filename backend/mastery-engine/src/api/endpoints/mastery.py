"""
Mastery API Endpoints
====================

FastAPI endpoints for real-time mastery calculation and querying.
Includes JWT security, rate limiting, and structured logging.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Request, Query
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.models.mastery import (
    MasteryQueryRequest, MasteryCalculateRequest, MasteryQueryResponse,
    ComponentScores, MasteryWeights, MasteryResult
)
from src.services.state_manager import StateManager
from src.skills.calculator import MasteryCalculator
from src.security import SecurityManager

# Configure logging
logger = logging.getLogger(__name__)

# Create router
mastery_router = APIRouter(prefix="/mastery", tags=["Mastery"])

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)


class MasteryEndpoints:
    """
    Collection of mastery calculation endpoints
    """

    @staticmethod
    async def get_state_manager() -> StateManager:
        """Dependency injection for StateManager"""
        return StateManager.create()

    @staticmethod
    async def get_security_manager() -> SecurityManager:
        """Dependency injection for SecurityManager"""
        # In production, this would be configured properly
        from src.main import app_state
        return app_state["security_manager"]

    @staticmethod
    def generate_correlation_id() -> str:
        """Generate unique correlation ID for request tracing"""
        return str(uuid.uuid4())

    @staticmethod
    def validate_jwt_token(
        authorization: Optional[str] = Header(None, description="JWT token in format: Bearer <token>"),
        security_manager: SecurityManager = Depends(get_security_manager)
    ) -> dict:
        """
        Validate JWT token and return decoded claims
        """
        if not authorization:
            raise HTTPException(status_code=401, detail="Missing authorization header")

        try:
            # Extract token from "Bearer <token>"
            if not authorization.startswith("Bearer "):
                raise HTTPException(status_code=401, detail="Invalid authorization format")

            token = authorization[7:]  # Remove "Bearer "
            claims = security_manager.validate_jwt(token)
            return claims

        except Exception as e:
            logger.error(f"JWT validation failed: {e}")
            raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")


# ==================== Main Endpoints ====================

@mastery_router.post("/query", response_model=MasteryQueryResponse)
@limiter.limit("50/minute")
async def query_mastery(
    request: MasteryQueryRequest,
    request_context: Request,
    claims: dict = Depends(MasteryEndpoints.validate_jwt_token),
    state_manager: StateManager = Depends(MasteryEndpoints.get_state_manager)
):
    """
    Query current mastery state for a student

    **Rate Limit**: 50 requests per minute
    **Auth**: JWT token required
    **Role**: student, teacher, or admin

    Returns current mastery score with optional historical data.
    """
    correlation_id = MasteryEndpoints.generate_correlation_id()

    try:
        # Security check: role-based access
        user_role = claims.get("role")
        user_id = claims.get("sub")

        if user_role == "student" and request.student_id != user_id:
            logger.warning(
                f"Access denied: student {user_id} attempted to access {request.student_id}",
                extra={"correlation_id": correlation_id}
            )
            raise HTTPException(status_code=403, detail="Cannot access other students' data")

        # Log request
        logger.info(
            f"Mastery query for {request.student_id}",
            extra={
                "correlation_id": correlation_id,
                "student_id": request.student_id,
                "role": user_role,
                "include_components": request.include_components,
                "include_history": request.include_history
            }
        )

        # Get current mastery
        current_mastery = await state_manager.get_mastery_score(request.student_id)

        if not current_mastery:
            # No data available - return empty response
            logger.warning(
                f"No mastery data found for {request.student_id}",
                extra={"correlation_id": correlation_id}
            )
            return MasteryQueryResponse(
                success=False,
                data=None,
                metadata={"correlation_id": correlation_id, "message": "No data available"}
            )

        # Get historical data if requested
        historical_data = None
        historical_average = None
        trend = None

        if request.include_history:
            history = await state_manager.get_mastery_history(
                request.student_id,
                days=request.days_history
            )

            if history:
                # Calculate historical average
                historical_scores = [h.mastery_score for h in history]
                historical_average = sum(historical_scores) / len(historical_scores)

                # Determine trend
                if len(historical_scores) >= 2:
                    if historical_scores[-1] > historical_scores[0] + 0.02:
                        trend = "improving"
                    elif historical_scores[-1] < historical_scores[0] - 0.02:
                        trend = "declining"
                    else:
                        trend = "stable"

        # Build response
        response = MasteryQueryResponse(
            success=True,
            data=current_mastery,
            historical_average=historical_average,
            trend=trend,
            metadata={
                "correlation_id": correlation_id,
                "query_time": datetime.utcnow().isoformat(),
                "student_id": request.student_id
            }
        )

        logger.info(
            f"Mastery query successful for {request.student_id}",
            extra={
                "correlation_id": correlation_id,
                "score": current_mastery.mastery_score,
                "level": current_mastery.level.value
            }
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error in mastery query: {e}",
            extra={"correlation_id": correlation_id},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@mastery_router.post("/calculate", response_model=MasteryQueryResponse)
@limiter.limit("30/minute")
async def calculate_mastery(
    request: MasteryCalculateRequest,
    request_context: Request,
    claims: dict = Depends(MasteryEndpoints.validate_jwt_token),
    state_manager: StateManager = Depends(MasteryEndpoints.get_state_manager)
):
    """
    Calculate new mastery score from current component values

    **Rate Limit**: 30 requests per minute
    **Auth**: JWT token required
    **Role**: student, teacher, or admin

    Performs calculation and saves result to state store.
    """
    correlation_id = MasteryEndpoints.generate_correlation_id()

    try:
        # Security check: role-based access
        user_role = claims.get("role")
        user_id = claims.get("sub")

        if user_role == "student" and request.student_id != user_id:
            logger.warning(
                f"Access denied: student {user_id} attempted to calculate for {request.student_id}",
                extra={"correlation_id": correlation_id}
            )
            raise HTTPException(status_code=403, detail="Cannot calculate for other students")

        # Log request
        logger.info(
            f"Mastery calculation for {request.student_id}",
            extra={
                "correlation_id": correlation_id,
                "student_id": request.student_id,
                "components": request.components.model_dump(),
                "role": user_role
            }
        )

        # Initialize calculator with custom weights if provided
        calculator = MasteryCalculator(request.weights or MasteryWeights())

        # Perform calculation
        result = calculator.execute_calculation(
            request.student_id,
            request.components
        )

        # Save to state store
        save_success = await state_manager.save_mastery_score(result)

        if not save_success:
            logger.error(
                f"Failed to save mastery score for {request.student_id}",
                extra={"correlation_id": correlation_id}
            )
            raise HTTPException(status_code=500, detail="Failed to persist calculation result")

        # Get historical data for trend analysis
        history = await state_manager.get_mastery_history(request.student_id, days=7)
        historical_average = None
        trend = None

        if history:
            historical_scores = [h.mastery_score for h in history]
            historical_average = sum(historical_scores) / len(historical_scores)

            if len(historical_scores) >= 2:
                if historical_scores[-1] > historical_scores[0] + 0.02:
                    trend = "improving"
                elif historical_scores[-1] < historical_scores[0] - 0.02:
                    trend = "declining"
                else:
                    trend = "stable"

        # Build response
        response = MasteryQueryResponse(
            success=True,
            data=result,
            historical_average=historical_average,
            trend=trend,
            metadata={
                "correlation_id": correlation_id,
                "calculated_at": result.calculated_at.isoformat(),
                "saved": save_success,
                "weights_used": calculator.weights.model_dump()
            }
        )

        logger.info(
            f"Mastery calculation successful for {request.student_id}",
            extra={
                "correlation_id": correlation_id,
                "score": result.mastery_score,
                "level": result.level.value,
                "saved": save_success
            }
        )

        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error in mastery calculation: {e}",
            extra={"correlation_id": correlation_id},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")


@mastery_router.post("/ingest", status_code=202)
@limiter.limit("100/minute")
async def ingest_learning_event(
    request: Request,
    claims: dict = Depends(MasteryEndpoints.validate_jwt_token),
    state_manager: StateManager = Depends(MasteryEndpoints.get_state_manager)
):
    """
    Submit learning event for asynchronous processing

    **Rate Limit**: 100 requests per minute
    **Auth**: JWT token required
    **Status**: 202 Accepted (async processing)

    This endpoint accepts learning events that will be processed asynchronously
    via Kafka to update mastery scores. Validates events before queuing.
    """
    from src.services.event_validator import create_event_validation_service
    from src.models.events import create_learning_event
    import json

    correlation_id = MasteryEndpoints.generate_correlation_id()

    try:
        # Parse request body
        event_data = await request.json()

        logger.info(
            f"Ingesting learning event for {claims.get('sub')}",
            extra={
                "correlation_id": correlation_id,
                "event_type": event_data.get("event_type"),
                "student_id": claims.get("sub")
            }
        )

        # Security check
        user_id = claims.get("sub")
        event_student_id = event_data.get("student_id")

        if event_student_id and event_student_id != user_id:
            logger.warning(
                f"Student {user_id} tried to ingest event for {event_student_id}",
                extra={"correlation_id": correlation_id}
            )
            return JSONResponse(
                status_code=403,
                content={
                    "status": "error",
                    "message": "Cannot ingest events for other students",
                    "correlation_id": correlation_id
                }
            )

        # Set student_id from JWT if not provided
        if not event_student_id:
            event_data["student_id"] = user_id

        # Validate event structure
        validator = create_event_validation_service()
        structure_result = validator.validate_event_structure(event_data)

        if not structure_result.valid:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "Event validation failed",
                    "errors": structure_result.errors,
                    "warnings": structure_result.warnings,
                    "correlation_id": correlation_id
                }
            )

        # Validate business rules
        business_result = validator.validate_event_business_rules(event_data)

        if not business_result.valid:
            return JSONResponse(
                status_code=400,
                content={
                    "status": "error",
                    "message": "Business rule validation failed",
                    "errors": business_result.errors,
                    "warnings": business_result.warnings,
                    "correlation_id": correlation_id
                }
            )

        # Sanitize event data
        sanitized_data = validator.sanitize_event_data(event_data)

        # Check for duplicate event_id (idempotency)
        event_id = sanitized_data["event_id"]
        is_duplicate = await state_manager.is_event_processed(event_id)

        if is_duplicate:
            logger.info(
                f"Duplicate event {event_id} rejected",
                extra={"correlation_id": correlation_id}
            )
            return JSONResponse(
                status_code=202,
                content={
                    "status": "accepted",
                    "message": "Event already processed (idempotent)",
                    "event_id": event_id,
                    "correlation_id": correlation_id
                }
            )

        # Save event for Kafka processing (in real implementation, this would publish to Kafka)
        # For now, we'll process immediately as a preview
        try:
            # Create event object
            learning_event = create_learning_event(
                event_type=sanitized_data["event_type"],
                student_id=sanitized_data["student_id"],
                data=sanitized_data.get("data", {}),
                event_id=event_id,
                correlation_id=correlation_id
            )

            # Save to event log
            await state_manager.append_event_log(sanitized_data["student_id"], learning_event)

            # Mark as processed
            await state_manager.save_learning_event(learning_event)

            logger.info(
                f"Event {event_id} queued successfully",
                extra={
                    "correlation_id": correlation_id,
                    "event_type": learning_event.event_type,
                    "student_id": learning_event.student_id
                }
            )

            return JSONResponse(
                status_code=202,
                content={
                    "status": "accepted",
                    "message": "Event queued for processing",
                    "event_id": event_id,
                    "correlation_id": correlation_id,
                    "note": "In production, this would be published to Kafka topic 'mastery.requests'"
                }
            )

        except Exception as e:
            logger.error(
                f"Failed to process event {event_id}: {e}",
                extra={"correlation_id": correlation_id},
                exc_info=True
            )
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": "Failed to queue event",
                    "error": str(e),
                    "correlation_id": correlation_id
                }
            )

    except json.JSONDecodeError:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": "Invalid JSON",
                "correlation_id": correlation_id
            }
        )
    except Exception as e:
        logger.error(
            f"Unexpected error in event ingestion: {e}",
            extra={"correlation_id": correlation_id},
            exc_info=True
        )
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "Internal server error",
                "correlation_id": correlation_id
            }
        )


@mastery_router.get("/history/{student_id}")
@limiter.limit("20/minute")
async def get_mastery_history(
    student_id: str,
    days: int = Query(7, ge=1, le=90, description="Number of days to retrieve"),
    claims: dict = Depends(MasteryEndpoints.validate_jwt_token),
    state_manager: StateManager = Depends(MasteryEndpoints.get_state_manager)
):
    """
    Get historical mastery scores

    **Rate Limit**: 20 requests per minute
    **Auth**: JWT token required
    """
    correlation_id = MasteryEndpoints.generate_correlation_id()

    try:
        # Security check
        user_role = claims.get("role")
        user_id = claims.get("sub")

        if user_role == "student" and student_id != user_id:
            raise HTTPException(status_code=403, detail="Cannot access other students' data")

        # Get history
        history = await state_manager.get_mastery_history(student_id, days)

        return {
            "success": True,
            "student_id": student_id,
            "days": days,
            "history_count": len(history),
            "history": [h.model_dump() for h in history],
            "correlation_id": correlation_id
        }

    except Exception as e:
        logger.error(f"Failed to get history for {student_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@mastery_router.get("/statistics/{student_id}")
@limiter.limit("10/minute")
async def get_mastery_statistics(
    student_id: str,
    claims: dict = Depends(MasteryEndpoints.validate_jwt_token),
    state_manager: StateManager = Depends(MasteryEndpoints.get_state_manager)
):
    """
    Get comprehensive mastery statistics

    **Rate Limit**: 10 requests per minute
    **Auth**: JWT token required
    """
    correlation_id = MasteryEndpoints.generate_correlation_id()

    try:
        # Security check
        user_role = claims.get("role")
        user_id = claims.get("sub")

        if user_role == "student" and student_id != user_id:
            raise HTTPException(status_code=403, detail="Cannot access other students' data")

        # Get statistics
        stats = await state_manager.get_mastery_statistics(student_id)

        return {
            "success": True,
            "statistics": stats,
            "correlation_id": correlation_id
        }

    except Exception as e:
        logger.error(f"Failed to get statistics for {student_id}: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@mastery_router.get("/metrics/prometheus", tags=["Monitoring"])
@limiter.limit("10/minute")
async def get_prometheus_metrics(
    claims: dict = Depends(MasteryEndpoints.validate_jwt_token),
    state_manager: StateManager = Depends(MasteryEndpoints.get_state_manager)
):
    """
    Get Prometheus-format metrics for mastery engine

    **Rate Limit**: 10 requests per minute
    **Auth**: JWT token required

    Returns metrics in Prometheus text format for monitoring.
    """
    from prometheus_client import generate_latest, Counter, Gauge, Histogram
    import io

    # Create metrics
    requests_total = Counter('mastery_engine_requests_total', 'Total requests', ['endpoint', 'method'])
    calculation_duration = Histogram('mastery_calculation_duration_seconds', 'Time spent calculating')
    mastery_scores = Gauge('mastery_score_average', 'Average mastery score')
    event_queue_depth = Gauge('mastery_event_queue_depth', 'Current event queue depth')

    # For now, return a basic metrics response
    # In production, you would gather actual metrics
    metrics_data = {
        "mastery_engine_info": {
            "version": "1.0.0",
            "environment": os.getenv("ENVIRONMENT", "development")
        },
        "up": 1,
        "mastery_score_average": 0.0,  # Would calculate from state
        "requests_total": 0,
        "calculation_duration_seconds_histogram": {
            "count": 0,
            "sum": 0.0
        },
        "event_queue_depth": 0,
        "timestamp": datetime.utcnow().isoformat()
    }

    # Return in Prometheus text format (simplified)
    prometheus_text = f"""
# HELP mastery_engine_info Mastery Engine version information
# TYPE mastery_engine_info gauge
mastery_engine_info{{version="1.0.0",environment="{os.getenv("ENVIRONMENT", "development")}"}} 1

# HELP up Service health status
# TYPE up gauge
up {metrics_data["up"]}

# HELP mastery_score_average Average mastery score across all students
# TYPE mastery_score_average gauge
mastery_score_average {metrics_data["mastery_score_average"]}

# HELP mastery_event_queue_depth Current depth of event processing queue
# TYPE mastery_event_queue_depth gauge
mastery_event_queue_depth {metrics_data["event_queue_depth"]}

# HELP mastery_calculation_duration_seconds Time spent in mastery calculation
# TYPE mastery_calculation_duration_seconds histogram
mastery_calculation_duration_seconds_bucket{{le="0.1"}} 0
mastery_calculation_duration_seconds_bucket{{le="0.5"}} 0
mastery_calculation_duration_seconds_bucket{{le="1.0"}} 0
mastery_calculation_duration_seconds_bucket{{le="+Inf"}} 0
mastery_calculation_duration_seconds_sum 0
mastery_calculation_duration_seconds_count 0
"""

    return prometheus_text


# ==================== Error Handlers ====================

@limiter.request_filter
async def rate_limit_error_handler(request, exc):
    """Custom rate limit error handler"""
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "detail": "Too many requests. Please slow down.",
            "retry_after": exc.retry_after if hasattr(exc, 'retry_after') else None
        },
        headers={"Retry-After": str(exc.retry_after) if hasattr(exc, 'retry_after') else "60"}
    )


# Global exception handler for this router
@mastery_router.exception_handler(Exception)
async def mastery_exception_handler(request: Request, exc: Exception):
    """Global exception handler for mastery endpoints"""
    correlation_id = MasteryEndpoints.generate_correlation_id()
    logger.error(
        f"Unhandled exception in mastery endpoint: {exc}",
        extra={
            "correlation_id": correlation_id,
            "path": request.url.path,
            "method": request.method
        },
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Internal server error",
            "message": "An unexpected error occurred",
            "correlation_id": correlation_id
        }
    )


# Helper function for direct endpoint calls (used by Dapr)
async def calculate_mastery(payload: dict) -> dict:
    """
    Direct calculation function for Dapr service invocation

    Args:
        payload: Dictionary with student_id and components

    Returns:
        Calculation result as dictionary
    """
    try:
        # Validate payload
        if "student_id" not in payload or "components" not in payload:
            raise ValueError("Missing student_id or components")

        student_id = payload["student_id"]
        components_data = payload["components"]

        # Create components object
        components = ComponentScores(**components_data)

        # Create weights if provided
        weights = None
        if "weights" in payload:
            weights = MasteryWeights(**payload["weights"])

        # Calculate
        calculator = MasteryCalculator(weights)
        result = calculator.execute_calculation(student_id, components)

        # Save to state (async)
        state_manager = StateManager.create()
        await state_manager.save_mastery_score(result)

        return {
            "success": True,
            "result": result.model_dump(),
            "student_id": student_id
        }

    except Exception as e:
        logger.error(f"Dapr calculation error: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }