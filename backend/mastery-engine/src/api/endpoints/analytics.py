"""
Analytics and Predictions Endpoints
====================================

Predictive analytics endpoints for mastery forecasting and trajectory projection.
"""

import logging
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import JSONResponse

from src.security import SecurityManager, Permission
from src.services.state_manager import StateManager
from src.services.predictor import PredictorService, AdaptivePredictor
from src.models.mastery import (
    PredictionResult,
    TrajectoryResult,
    PredictionModelConfig
)

logger = logging.getLogger(__name__)

# Create router for analytics endpoints
analytics_router = APIRouter(prefix="/analytics", tags=["Analytics"])


class AnalyticsEndpoints:
    """Collection of analytics and prediction endpoints"""

    @staticmethod
    async def get_security_manager() -> SecurityManager:
        """Dependency injection for SecurityManager"""
        from src.main import app_state
        return app_state["security_manager"]

    @staticmethod
    async def get_state_manager() -> StateManager:
        """Dependency injection for StateManager"""
        return StateManager.create()

    @staticmethod
    async def get_predictor_service(state_manager: StateManager) -> PredictorService:
        """Dependency injection for PredictorService"""
        return PredictorService(state_manager)

    @staticmethod
    async def get_adaptive_predictor(state_manager: StateManager) -> AdaptivePredictor:
        """Dependency injection for AdaptivePredictor"""
        return AdaptivePredictor(state_manager)

    @staticmethod
    def validate_student_access(claims: dict, student_id: str):
        """Ensure student can only access their own data"""
        user_role = claims.get("role")
        user_id = claims.get("sub")

        if user_role == "student" and user_id != student_id:
            raise HTTPException(status_code=403, detail="Cannot access other students' data")


@analytics_router.post("/predictions/next-week", response_model=PredictionResult)
async def predict_next_week(
    request: Request,
    prediction_request: dict,  # Using dict to avoid circular imports
    claims: dict = Depends(AnalyticsEndpoints.get_security_manager),
    security_manager: SecurityManager = Depends(AnalyticsEndpoints.get_security_manager),
    state_manager: StateManager = Depends(AnalyticsEndpoints.get_state_manager),
    predictor: PredictorService = Depends(AnalyticsEndpoints.get_predictor_service)
):
    """
    Predict mastery trajectory for the next 7 days

    **Auth**: Student (own data), Teacher, Admin
    **Rate Limit**: 20 requests per minute

    Returns prediction with confidence scoring and intervention flags.

    Request body:
    ```json
    {
        "student_id": "student_123"
    }
    ```

    Response includes:
    - Predicted mastery score in 7 days
    - Confidence level (0-1)
    - Trend (improving/declining/stable)
    - Intervention needed flag
    - Projected component scores
    """
    correlation_id = str(request.state.correlation_id) if hasattr(request.state, 'correlation_id') else "unknown"

    try:
        # Extract and validate request
        student_id = prediction_request.get("student_id")
        if not student_id:
            raise HTTPException(status_code=400, detail="student_id is required")

        # Security check
        AnalyticsEndpoints.validate_student_access(claims, student_id)

        # Audit the prediction request
        security_manager.audit_access(
            user_id=claims["sub"],
            action="PREDICT",
            resource=f"prediction:{student_id}:7days",
            details={
                "correlation_id": correlation_id,
                "model": "predictor_service"
            }
        )

        # Generate prediction
        prediction = await predictor.predict_next_week(student_id)

        # Log the prediction
        logger.info(
            f"Prediction generated for {student_id}: {prediction.predicted_score:.3f} (confidence: {prediction.confidence:.3f})",
            extra={"correlation_id": correlation_id, "student_id": student_id}
        )

        return prediction

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Prediction failed for student: {e}",
            extra={"correlation_id": correlation_id},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")


@analytics_router.post("/predictions/trajectory", response_model=TrajectoryResult)
async def predict_trajectory(
    request: Request,
    prediction_request: dict,
    claims: dict = Depends(AnalyticsEndpoints.get_security_manager),
    security_manager: SecurityManager = Depends(AnalyticsEndpoints.get_security_manager),
    state_manager: StateManager = Depends(AnalyticsEndpoints.get_state_manager),
    predictor: PredictorService = Depends(AnalyticsEndpoints.get_predictor_service)
):
    """
    Predict mastery trajectory for the next 14 days

    **Auth**: Student (own data), Teacher, Admin
    **Rate Limit**: 15 requests per minute

    Returns day-by-day trajectory projection with confidence decay.

    Request body:
    ```json
    {
        "student_id": "student_123"
    }
    ```

    Response includes:
    - Daily projections for 14 days
    - Confidence over time
    - Intervention points
    - Overall trend
    """
    correlation_id = str(request.state.correlation_id) if hasattr(request.state, 'correlation_id') else "unknown"

    try:
        student_id = prediction_request.get("student_id")
        if not student_id:
            raise HTTPException(status_code=400, detail="student_id is required")

        # Security check
        AnalyticsEndpoints.validate_student_access(claims, student_id)

        # Audit
        security_manager.audit_access(
            user_id=claims["sub"],
            action="TRAJECTORY",
            resource=f"trajectory:{student_id}",
            details={
                "correlation_id": correlation_id,
                "model": "predictor_service"
            }
        )

        # Generate trajectory
        trajectory = await predictor.predict_trajectory(student_id)

        logger.info(
            f"Trajectory prediction for {student_id}: {len(trajectory.trajectory)} points",
            extra={"correlation_id": correlation_id, "student_id": student_id}
        )

        return trajectory

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Trajectory prediction failed: {e}",
            extra={"correlation_id": correlation_id},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Trajectory prediction failed: {str(e)}")


@analytics_router.post("/predictions/next-week/intervention", response_model=PredictionResult)
async def predict_with_intervention(
    request: Request,
    prediction_request: dict,
    claims: dict = Depends(AnalyticsEndpoints.get_security_manager),
    security_manager: SecurityManager = Depends(AnalyticsEndpoints.get_security_manager),
    state_manager: StateManager = Depends(AnalyticsEndpoints.get_state_manager),
    predictor: AdaptivePredictor = Depends(AnalyticsEndpoints.get_adaptive_predictor)
):
    """
    Predict mastery with intervention impact modeling

    **Auth**: Student (own data), Teacher, Admin
    **Rate Limit**: 10 requests per minute

    Predicts mastery with expected improvement from specific intervention types.

    Request body:
    ```json
    {
        "student_id": "student_123",
        "intervention_type": "practice"
    }
    ```

    Valid intervention types:
    - "tutoring": ~15% improvement
    - "practice": ~10% improvement
    - "review": ~5% improvement

    Returns:
    - Prediction with intervention impact factored in
    - Adjusted component projections
    - Confidence scores
    """
    correlation_id = str(request.state.correlation_id) if hasattr(request.state, 'correlation_id') else "unknown"

    try:
        student_id = prediction_request.get("student_id")
        intervention_type = prediction_request.get("intervention_type")

        if not student_id:
            raise HTTPException(status_code=400, detail="student_id is required")
        if not intervention_type:
            raise HTTPException(status_code=400, detail="intervention_type is required")

        valid_types = ["tutoring", "practice", "review"]
        if intervention_type not in valid_types:
            raise HTTPException(
                status_code=400,
                detail=f"intervention_type must be one of: {', '.join(valid_types)}"
            )

        # Security check
        AnalyticsEndpoints.validate_student_access(claims, student_id)

        # Audit
        security_manager.audit_access(
            user_id=claims["sub"],
            action="PREDICT_INTERVENTION",
            resource=f"prediction:{student_id}:intervention",
            details={
                "correlation_id": correlation_id,
                "intervention_type": intervention_type
            }
        )

        # Generate intervention-aware prediction
        prediction = await predictor.predict_with_intervention_impact(student_id, intervention_type)

        logger.info(
            f"Intervention prediction for {student_id}: {prediction.predicted_score:.3f} (type: {intervention_type})",
            extra={"correlation_id": correlation_id, "student_id": student_id, "intervention": intervention_type}
        )

        return prediction

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Intervention prediction failed: {e}",
            extra={"correlation_id": correlation_id},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Intervention prediction failed: {str(e)}")


@analytics_router.get("/predictions/accuracy/{student_id}")
async def get_prediction_accuracy(
    student_id: str,
    request: Request,
    days: int = Query(7, ge=1, le=30, description="Days to look back for predictions"),
    claims: dict = Depends(AnalyticsEndpoints.get_security_manager),
    security_manager: SecurityManager = Depends(AnalyticsEndpoints.get_security_manager),
    state_manager: StateManager = Depends(AnalyticsEndpoints.get_state_manager)
):
    """
    Get prediction accuracy metrics for a student

    **Auth**: Student (own data), Teacher, Admin
    **Rate Limit**: 10 requests per minute

    Returns historical prediction accuracy statistics.
    """
    correlation_id = str(request.state.correlation_id) if hasattr(request.state, 'correlation_id') else "unknown"

    try:
        # Security check
        AnalyticsEndpoints.validate_student_access(claims, student_id)

        # Audit
        security_manager.audit_access(
            user_id=claims["sub"],
            action="ACCURACY_VIEW",
            resource=f"prediction_accuracy:{student_id}",
            details={"correlation_id": correlation_id}
        )

        # In a real implementation, this would query stored accuracy metrics
        # For now, return placeholder data
        accuracy_data = {
            "student_id": student_id,
            "lookback_days": days,
            "metrics": {
                "total_predictions": 0,
                "average_error": 0.0,
                "within_variance_rate": 0.0,
                "recent_accuracy": 0.0
            },
            "model_version": "1.0.0"
        }

        return accuracy_data

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to retrieve accuracy metrics: {e}",
            extra={"correlation_id": correlation_id},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Failed to retrieve accuracy: {str(e)}")


@analytics_router.post("/mastery-history")
async def get_mastery_history(
    request: Request,
    history_request: dict,
    claims: dict = Depends(AnalyticsEndpoints.get_security_manager),
    security_manager: SecurityManager = Depends(AnalyticsEndpoints.get_security_manager),
    state_manager: StateManager = Depends(AnalyticsEndpoints.get_state_manager)
):
    """
    Get historical mastery data with aggregation

    **Auth**: Student (own data), Teacher, Admin
    **Rate Limit**: 20 requests per minute

    Request body:
    ```json
    {
        "student_id": "student_123",
        "start_date": "2026-01-01",
        "end_date": "2026-01-14",
        "aggregation": "daily"
    }
    ```

    Aggregation options:
    - "daily": Daily snapshots
    - "weekly": Weekly averages
    - "monthly": Monthly averages
    """
    correlation_id = str(request.state.correlation_id) if hasattr(request.state, 'correlation_id') else "unknown"

    try:
        student_id = history_request.get("student_id")
        start_date_str = history_request.get("start_date")
        end_date_str = history_request.get("end_date")
        aggregation = history_request.get("aggregation", "daily")

        if not all([student_id, start_date_str, end_date_str]):
            raise HTTPException(status_code=400, detail="student_id, start_date, and end_date are required")

        # Security check
        AnalyticsEndpoints.validate_student_access(claims, student_id)

        # Audit
        security_manager.audit_access(
            user_id=claims["sub"],
            action="HISTORY_VIEW",
            resource=f"history:{student_id}",
            details={
                "correlation_id": correlation_id,
                "aggregation": aggregation
            }
        )

        # Parse dates
        try:
            start_date = datetime.fromisoformat(start_date_str)
            end_date = datetime.fromisoformat(end_date_str)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use ISO format: YYYY-MM-DD")

        if start_date > end_date:
            raise HTTPException(status_code=400, detail="start_date must be before end_date")

        # Get historical data
        history_data = await state_manager.get_mastery_history(student_id, days=90)

        # Filter by date range
        filtered_history = [
            h for h in history_data
            if start_date <= h.timestamp <= end_date
        ]

        # Apply aggregation
        aggregated = await _aggregate_history(filtered_history, aggregation)

        logger.info(
            f"History retrieval for {student_id}: {len(filtered_history)} records",
            extra={"correlation_id": correlation_id, "student_id": student_id}
        )

        return {
            "student_id": student_id,
            "start_date": start_date_str,
            "end_date": end_date_str,
            "aggregation": aggregation,
            "count": len(filtered_history),
            "data": aggregated
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"History retrieval failed: {e}",
            extra={"correlation_id": correlation_id},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"History retrieval failed: {str(e)}")


async def _aggregate_history(history_data, aggregation: str):
    """Aggregate historical data by specified period"""
    if not history_data:
        return []

    if aggregation == "daily":
        return [h.model_dump() for h in history_data]

    # For weekly/monthly, we'd implement aggregation logic
    # This is simplified for now
    return [h.model_dump() for h in history_data]


@analytics_router.post("/predictions/config")
async def get_prediction_config(
    request: Request,
    claims: dict = Depends(AnalyticsEndpoints.get_security_manager),
    security_manager: SecurityManager = Depends(AnalyticsEndpoints.get_security_manager)
):
    """
    Get prediction model configuration

    **Auth**: Student, Teacher, Admin
    **Rate Limit**: 50 requests per minute

    Returns the configuration used for predictions (min history, thresholds, etc.)
    """
    correlation_id = str(request.state.correlation_id) if hasattr(request.state, 'correlation_id') else "unknown"

    try:
        # Audit
        security_manager.audit_access(
            user_id=claims["sub"],
            action="CONFIG_VIEW",
            resource="prediction_config",
            details={"correlation_id": correlation_id}
        )

        config = PredictionModelConfig()

        return {
            "config": config.model_dump(),
            "model_version": "1.0.0",
            "notes": "Configuration may be adjusted based on model performance"
        }

    except Exception as e:
        logger.error(f"Failed to retrieve config: {e}", extra={"correlation_id": correlation_id})
        raise HTTPException(status_code=500, detail=f"Failed to retrieve config: {str(e)}")


# Global error handler for analytics endpoints
@analytics_router.exception_handler(Exception)
async def analytics_exception_handler(request: Request, exc: Exception):
    """Global exception handler for analytics endpoints"""
    logger.error(f"Analytics endpoint error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Analytics operation failed",
            "message": "Internal error during analytics operation"
        }
    )