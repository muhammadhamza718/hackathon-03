"""
Analytics & Batch Endpoints
===========================

Phase 9: Batch processing, historical analytics, and cohort comparison endpoints.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import JSONResponse

from src.security import SecurityManager
from src.services.state_manager import StateManager
from src.services.analytics_service import AnalyticsService
from src.models.mastery import (
    BatchMasteryRequest,
    BatchMasteryResponse,
    BatchJobStatus,
    DateRangeRequest,
    MasteryHistoryResponse,
    MasteryAnalyticsResponse,
    CohortComparisonRequest,
    CohortComparisonResult,
    StudentComparisonRequest,
    StudentComparisonResult,
    AnalyticsConfigResponse,
    BatchStatusQuery
)

logger = logging.getLogger(__name__)

# Create router for analytics endpoints
analytics_router = APIRouter(prefix="/analytics", tags=["Analytics"])


class AnalyticsEndpoints:
    """Collection of analytics and batch endpoints"""

    @staticmethod
    async def get_security_manager() -> SecurityManager:
        """Dependency injection for SecurityManager"""
        from src.main import app_state
        return app_state["security_manager"]

    @staticmethod
    async def get_state_manager() -> StateManager:
        """Dependency injection for StateManager"""
        from src.main import app_state
        return app_state["state_manager"]

    @staticmethod
    async def get_analytics_service(state_manager: StateManager) -> AnalyticsService:
        """Dependency injection for AnalyticsService"""
        return AnalyticsService(state_manager)

    @staticmethod
    def validate_student_access(claims: dict, student_id: str):
        """Ensure student can only access their own data"""
        user_role = claims.get("role")
        user_id = claims.get("sub")

        if user_role == "student" and user_id != student_id:
            raise HTTPException(status_code=403, detail="Cannot access other students' data")

    @staticmethod
    def validate_cohort_access(claims: dict, cohort_ids: list):
        """Ensure student can only access their own data in cohorts"""
        user_role = claims.get("role")
        user_id = claims.get("sub")

        if user_role == "student" and user_id not in cohort_ids:
            raise HTTPException(status_code=403, detail="Cannot access other students' data")


@analytics_router.post("/batch/mastery", response_model=BatchMasteryResponse)
async def batch_mastery_calculation(
    request: Request,
    batch_request: BatchMasteryRequest,
    claims: dict = Depends(AnalyticsEndpoints.get_security_manager),
    security_manager: SecurityManager = Depends(AnalyticsEndpoints.get_security_manager),
    state_manager: StateManager = Depends(AnalyticsEndpoints.get_state_manager),
    analytics_service: AnalyticsService = Depends(AnalyticsEndpoints.get_analytics_service)
):
    """
    Submit batch mastery calculation job

    **Auth**: Admin only
    **Rate Limit**: 10 requests per minute
    **Batch Size**: Up to 1000 student IDs

    Processes mastery calculations for multiple students asynchronously.
    Returns immediately with batch ID for status tracking.

    Request body:
    ```json
    {
        "student_ids": ["student_123", "student_456"],
        "priority": "normal",
        "callback_url": "https://example.com/webhook"
    }
    ```
    """
    correlation_id = str(request.state.correlation_id) if hasattr(request.state, 'correlation_id') else "unknown"

    try:
        # Security check - only admins can submit batch jobs
        user_role = claims.get("role")
        if user_role != "admin":
            raise HTTPException(status_code=403, detail="Batch processing requires admin role")

        # Validate batch size
        if len(batch_request.student_ids) > 1000:
            raise HTTPException(status_code=400, detail="Maximum batch size is 1000 students")

        # Audit
        security_manager.audit_access(
            user_id=claims["sub"],
            action="BATCH_PROCESSING",
            resource="batch:mastery",
            details={
                "correlation_id": correlation_id,
                "student_count": len(batch_request.student_ids),
                "priority": batch_request.priority.value
            }
        )

        # Submit batch job
        result = await analytics_service.submit_batch_mastery_calculation(batch_request)

        logger.info(
            f"Submitted batch job {result.batch_id} for {len(batch_request.student_ids)} students",
            extra={"correlation_id": correlation_id, "batch_id": result.batch_id}
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Batch submission failed: {e}",
            extra={"correlation_id": correlation_id},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Batch submission failed: {str(e)}")


@analytics_router.get("/batch/mastery/{batch_id}", response_model=BatchJobStatus)
async def get_batch_status(
    batch_id: str,
    request: Request,
    claims: dict = Depends(AnalyticsEndpoints.get_security_manager),
    security_manager: SecurityManager = Depends(AnalyticsEndpoints.get_security_manager),
    analytics_service: AnalyticsService = Depends(AnalyticsEndpoints.get_analytics_service)
):
    """
    Get status of batch processing job

    **Auth**: Admin or batch owner (teacher/admin who submitted)
    **Rate Limit**: 30 requests per minute

    Returns current status, progress, and estimated completion time.
    """
    correlation_id = str(request.state.correlation_id) if hasattr(request.state, 'correlation_id') else "unknown"

    try:
        # Security check - admins can view all, others can only view their own
        user_role = claims.get("role")
        if user_role != "admin":
            # In production, we'd check if the user submitted this batch
            # For now, require admin role
            raise HTTPException(status_code=403, detail="Viewing batch status requires admin role")

        # Get batch status
        status = await analytics_service.get_batch_status(batch_id)

        if not status:
            raise HTTPException(status_code=404, detail=f"Batch job {batch_id} not found")

        # Audit
        security_manager.audit_access(
            user_id=claims["sub"],
            action="BATCH_STATUS",
            resource=f"batch:{batch_id}",
            details={"correlation_id": correlation_id}
        )

        logger.info(
            f"Retrieved status for batch {batch_id}",
            extra={"correlation_id": correlation_id, "batch_id": batch_id}
        )

        return status

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to get batch status: {e}",
            extra={"correlation_id": correlation_id, "batch_id": batch_id},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Failed to get batch status: {str(e)}")


@analytics_router.post("/mastery-history", response_model=MasteryHistoryResponse)
async def get_mastery_history(
    request: Request,
    history_request: DateRangeRequest,
    claims: dict = Depends(AnalyticsEndpoints.get_security_manager),
    security_manager: SecurityManager = Depends(AnalyticsEndpoints.get_security_manager),
    analytics_service: AnalyticsService = Depends(AnalyticsEndpoints.get_analytics_service)
):
    """
    Get historical mastery data with aggregation

    **Auth**: Student (own data), Teacher, Admin
    **Rate Limit**: 60 requests per minute

    Retrieves mastery history for a student within a date range,
    aggregated by daily, weekly, or monthly intervals.

    Request body:
    ```json
    {
        "student_id": "student_123",
        "start_date": "2026-01-01",
        "end_date": "2026-01-14",
        "aggregation": "daily"
    }
    ```
    """
    correlation_id = str(request.state.correlation_id) if hasattr(request.state, 'correlation_id') else "unknown"

    try:
        # Security check
        AnalyticsEndpoints.validate_student_access(claims, history_request.student_id)

        # Audit
        security_manager.audit_access(
            user_id=claims["sub"],
            action="HISTORY_QUERY",
            resource=f"history:{history_request.student_id}",
            details={
                "correlation_id": correlation_id,
                "start_date": history_request.start_date.isoformat(),
                "end_date": history_request.end_date.isoformat(),
                "aggregation": history_request.aggregation.value
            }
        )

        # Get historical data
        result = await analytics_service.get_mastery_history(history_request)

        logger.info(
            f"Retrieved mastery history for {history_request.student_id}: {len(result.data)} data points",
            extra={"correlation_id": correlation_id, "student_id": history_request.student_id}
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to get mastery history: {e}",
            extra={"correlation_id": correlation_id, "student_id": history_request.student_id},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Failed to get mastery history: {str(e)}")


@analytics_router.post("/comprehensive", response_model=MasteryAnalyticsResponse)
async def get_comprehensive_analytics(
    request: Request,
    analytics_request: DateRangeRequest,
    claims: dict = Depends(AnalyticsEndpoints.get_security_manager),
    security_manager: SecurityManager = Depends(AnalyticsEndpoints.get_security_manager),
    analytics_service: AnalyticsService = Depends(AnalyticsEndpoints.get_analytics_service)
):
    """
    Get comprehensive analytics with trends and statistics

    **Auth**: Student (own data), Teacher, Admin
    **Rate Limit**: 50 requests per minute

    Provides detailed analytics including:
    - Statistical summary (mean, median, std dev, percentiles)
    - Trend analysis (improving/declining/stable)
    - Volatility and consistency scores
    - Component-level trends
    """
    correlation_id = str(request.state.correlation_id) if hasattr(request.state, 'correlation_id') else "unknown"

    try:
        # Security check
        AnalyticsEndpoints.validate_student_access(claims, analytics_request.student_id)

        # Audit
        security_manager.audit_access(
            user_id=claims["sub"],
            action="COMPREHENSIVE_ANALYTICS",
            resource=f"analytics:{analytics_request.student_id}",
            details={
                "correlation_id": correlation_id,
                "start_date": analytics_request.start_date.isoformat(),
                "end_date": analytics_request.end_date.isoformat()
            }
        )

        # Get comprehensive analytics
        result = await analytics_service.get_comprehensive_analytics(analytics_request)

        logger.info(
            f"Retrieved comprehensive analytics for {analytics_request.student_id}",
            extra={"correlation_id": correlation_id, "student_id": analytics_request.student_id}
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Failed to get comprehensive analytics: {e}",
            extra={"correlation_id": correlation_id, "student_id": analytics_request.student_id},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Failed to get analytics: {str(e)}")


@analytics_router.post("/compare/cohorts", response_model=CohortComparisonResult)
async def compare_cohorts(
    request: Request,
    comparison_request: CohortComparisonRequest,
    claims: dict = Depends(AnalyticsEndpoints.get_security_manager),
    security_manager: SecurityManager = Depends(AnalyticsEndpoints.get_security_manager),
    analytics_service: AnalyticsService = Depends(AnalyticsEndpoints.get_analytics_service)
):
    """
    Compare two cohorts of students

    **Auth**: Teacher, Admin
    **Rate Limit**: 20 requests per minute

    Performs statistical comparison between two groups of students,
    including significance testing and component-level analysis.

    Request body:
    ```json
    {
        "cohort_a_student_ids": ["student_1", "student_2", "student_3"],
        "cohort_b_student_ids": ["student_4", "student_5", "student_6"],
        "comparison_date": "2026-01-15",
        "include_component_analysis": true,
        "include_percentiles": true
    }
    ```
    """
    correlation_id = str(request.state.correlation_id) if hasattr(request.state, 'correlation_id') else "unknown"

    try:
        # Security check - only teachers and admins
        user_role = claims.get("role")
        if user_role not in ["teacher", "admin"]:
            raise HTTPException(status_code=403, detail="Cohort comparison requires teacher or admin role")

        # Validate cohorts
        if len(comparison_request.cohort_a_student_ids) < 2:
            raise HTTPException(status_code=400, detail="Cohort A must have at least 2 students")
        if len(comparison_request.cohort_b_student_ids) < 2:
            raise HTTPException(status_code=400, detail="Cohort B must have at least 2 students")

        # Audit
        security_manager.audit_access(
            user_id=claims["sub"],
            action="COHORT_COMPARISON",
            resource="comparison:cohorts",
            details={
                "correlation_id": correlation_id,
                "cohort_a_size": len(comparison_request.cohort_a_student_ids),
                "cohort_b_size": len(comparison_request.cohort_b_student_ids),
                "include_component_analysis": comparison_request.include_component_analysis
            }
        )

        # Perform cohort comparison
        result = await analytics_service.compare_cohorts(comparison_request)

        logger.info(
            f"Completed cohort comparison: A({len(comparison_request.cohort_a_student_ids)}) vs B({len(comparison_request.cohort_b_student_ids)})",
            extra={"correlation_id": correlation_id, "winner": result.winner}
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Cohort comparison failed: {e}",
            extra={"correlation_id": correlation_id},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Cohort comparison failed: {str(e)}")


@analytics_router.post("/compare/students", response_model=StudentComparisonResult)
async def compare_students(
    request: Request,
    comparison_request: StudentComparisonRequest,
    claims: dict = Depends(AnalyticsEndpoints.get_security_manager),
    security_manager: SecurityManager = Depends(AnalyticsEndpoints.get_security_manager),
    analytics_service: AnalyticsService = Depends(AnalyticsEndpoints.get_analytics_service)
):
    """
    Compare specific students or groups

    **Auth**: Student (own data only), Teacher, Admin
    **Rate Limit**: 30 requests per minute

    Compares multiple students on a specific metric with rankings.
    Students can only compare themselves, teachers/admins can compare any students.

    Request body:
    ```json
    {
        "student_ids": ["student_123", "student_456", "student_789"],
        "metric": "mastery_score",
        "timeframe_days": 30
    }
    ```
    """
    correlation_id = str(request.state.correlation_id) if hasattr(request.state, 'correlation_id') else "unknown"

    try:
        # Security check
        user_role = claims.get("role")
        user_id = claims.get("sub")

        if user_role == "student":
            # Students can only compare themselves
            if user_id not in comparison_request.student_ids:
                raise HTTPException(status_code=403, detail="Students can only compare their own data")
            if len(comparison_request.student_ids) > 1:
                raise HTTPException(status_code=403, detail="Students can only compare themselves")

        # Audit
        security_manager.audit_access(
            user_id=claims["sub"],
            action="STUDENT_COMPARISON",
            resource="comparison:students",
            details={
                "correlation_id": correlation_id,
                "student_count": len(comparison_request.student_ids),
                "metric": comparison_request.metric
            }
        )

        # Perform student comparison
        result = await analytics_service.compare_students(comparison_request)

        logger.info(
            f"Completed student comparison for {len(comparison_request.student_ids)} students",
            extra={"correlation_id": correlation_id, "metric": comparison_request.metric}
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Student comparison failed: {e}",
            extra={"correlation_id": correlation_id},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Student comparison failed: {str(e)}")


@analytics_router.get("/config", response_model=AnalyticsConfigResponse)
async def get_analytics_config(
    request: Request,
    claims: dict = Depends(AnalyticsEndpoints.get_security_manager),
    security_manager: SecurityManager = Depends(AnalyticsEndpoints.get_security_manager)
):
    """
    Get current analytics configuration

    **Auth**: Student, Teacher, Admin
    **Rate Limit**: 50 requests per minute

    Returns configuration parameters for batch processing,
    aggregation, and statistical analysis.
    """
    correlation_id = str(request.state.correlation_id) if hasattr(request.state, 'correlation_id') else "unknown"

    try:
        # Audit
        security_manager.audit_access(
            user_id=claims["sub"],
            action="VIEW_CONFIG",
            resource="analytics_config",
            details={"correlation_id": correlation_id}
        )

        config = {
            "batch": {
                "max_batch_size": 1000,
                "priority_levels": ["low", "normal", "high"],
                "concurrent_processing": {
                    "high": 10,
                    "normal": 5,
                    "low": 2
                }
            },
            "aggregation": {
                "supported_types": ["daily", "weekly", "monthly"],
                "max_history_days": 90
            },
            "statistics": {
                "min_sample_size": 2,
                "volatility_threshold": 0.02,
                "consistency_threshold": 0.8
            },
            "comparison": {
                "max_cohort_size": 50,
                "min_cohort_size": 2,
                "confidence_level": 0.95
            }
        }

        return AnalyticsConfigResponse(
            model_version="1.0.0",
            config=config,
            notes="Analytics service configuration for batch processing, historical analysis, and cohort comparison"
        )

    except Exception as e:
        logger.error(f"Failed to retrieve analytics config: {e}", extra={"correlation_id": correlation_id})
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