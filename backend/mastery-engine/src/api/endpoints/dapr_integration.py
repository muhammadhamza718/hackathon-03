"""
Dapr Integration Endpoints
==========================

Phase 10: Dapr service invocation endpoints for inter-service communication.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse

from src.security import SecurityManager
from src.services.state_manager import StateManager
from src.services.analytics_service import DaprServiceHandler
from src.models.mastery import (
    DaprProcessRequest,
    DaprProcessResponse,
    DaprSecurityContext
)

logger = logging.getLogger(__name__)

# Create router for Dapr endpoints
dapr_router = APIRouter(prefix="/process", tags=["Dapr"])


class DaprEndpoints:
    """Collection of Dapr service invocation endpoints"""

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
    async def get_dapr_service(state_manager: StateManager) -> DaprServiceHandler:
        """Dependency injection for DaprServiceHandler"""
        return DaprServiceHandler(state_manager)


@dapr_router.post("/process", response_model=DaprProcessResponse)
async def dapr_process(
    request: Request,
    process_request: DaprProcessRequest,
    security_manager: SecurityManager = Depends(DaprEndpoints.get_security_manager),
    state_manager: StateManager = Depends(DaprEndpoints.get_state_manager),
    dapr_service: DaprServiceHandler = Depends(DaprEndpoints.get_dapr_service)
):
    """
    Dapr service invocation endpoint

    **Auth**: Dapr service account or authenticated user
    **Rate Limit**: 100 requests per minute
    **Dapr Integration**: Service-to-service communication

    Standardized endpoint for Dapr service invocation with intent routing
    and security context propagation.

    Request format:
    ```json
    {
        "intent": "mastery_calculation",
        "payload": {"student_id": "student_123"},
        "security_context": {
            "token": "jwt_token_here",
            "user_id": "user_123",
            "roles": ["student"],
            "correlation_id": "req_123"
        }
    }
    ```

    Supported intents:
    - `mastery_calculation`: Calculate mastery for a student
    - `get_prediction`: Get mastery prediction
    - `generate_path`: Generate learning path
    - `batch_process`: Submit batch job
    - `analytics_query`: Query historical analytics

    Response format:
    ```json
    {
        "success": true,
        "data": {...},
        "metadata": {...},
        "correlation_id": "req_123"
    }
    ```
    """
    correlation_id = request.state.correlation_id if hasattr(request.state, 'correlation_id') else "unknown"

    try:
        # Extract security context from request or Dapr metadata
        security_context = process_request.security_context

        # If no security context provided, try to extract from Dapr metadata
        if not security_context:
            # In Dapr environment, metadata would be in headers
            # For now, create from available info
            security_context = DaprSecurityContext(
                correlation_id=str(correlation_id)
            )

        logger.info(
            f"Dapr request: intent={process_request.intent.value}",
            extra={
                "correlation_id": correlation_id,
                "intent": process_request.intent.value,
                "has_security": security_context is not None
            }
        )

        # Process the request
        response = await dapr_service.process_dapr_request(process_request, security_context)

        # Audit the request
        if security_context and security_context.user_id:
            security_manager.audit_access(
                user_id=security_context.user_id,
                action=f"DAPR_{process_request.intent.value.upper()}",
                resource="dapr:service_invocation",
                details={
                    "correlation_id": correlation_id,
                    "intent": process_request.intent.value,
                    "success": response.success
                }
            )

        # Log result
        if response.success:
            logger.info(
                f"Dapr request successful: {process_request.intent.value}",
                extra={"correlation_id": correlation_id, "intent": process_request.intent.value}
            )
        else:
            logger.warning(
                f"Dapr request failed: {response.error}",
                extra={"correlation_id": correlation_id, "intent": process_request.intent.value}
            )

        return response

    except Exception as e:
        logger.error(
            f"Dapr endpoint error: {e}",
            extra={"correlation_id": correlation_id, "intent": process_request.intent.value if process_request else "unknown"},
            exc_info=True
        )

        # Return standardized error response
        return DaprProcessResponse(
            success=False,
            error=str(e),
            metadata={
                "error_code": "ENDPOINT_ERROR",
                "retryable": True
            },
            correlation_id=str(correlation_id)
        )


@dapr_router.post("/process/mastery", response_model=DaprProcessResponse)
async def dapr_mastery_endpoint(
    request: Request,
    process_request: DaprProcessRequest,
    security_manager: SecurityManager = Depends(DaprEndpoints.get_security_manager),
    state_manager: StateManager = Depends(DaprEndpoints.get_state_manager),
    dapr_service: DaprServiceHandler = Depends(DaprEndpoints.get_dapr_service)
):
    """
    Dapr mastery calculation endpoint (optimized)

    **Auth**: Dapr service account or authenticated user
    **Rate Limit**: 100 requests per minute

    Simplified endpoint for mastery calculation specifically.
    This is a convenience endpoint that sets intent automatically.
    """
    correlation_id = request.state.correlation_id if hasattr(request.state, 'correlation_id') else "unknown"

    try:
        # Auto-set intent to mastery calculation
        from src.models.mastery import DaprIntent
        process_request.intent = DaprIntent.MASTERY_CALCULATION

        # Process through main handler
        return await dapr_process(request, process_request, security_manager, state_manager, dapr_service)

    except Exception as e:
        logger.error(f"Dapr mastery endpoint error: {e}", extra={"correlation_id": correlation_id})
        return DaprProcessResponse(
            success=False,
            error=str(e),
            correlation_id=str(correlation_id)
        )


@dapr_router.post("/process/prediction", response_model=DaprProcessResponse)
async def dapr_prediction_endpoint(
    request: Request,
    process_request: DaprProcessRequest,
    security_manager: SecurityManager = Depends(DaprEndpoints.get_security_manager),
    state_manager: StateManager = Depends(DaprEndpoints.get_state_manager),
    dapr_service: DaprServiceHandler = Depends(DaprEndpoints.get_dapr_service)
):
    """
    Dapr prediction endpoint (optimized)

    **Auth**: Dapr service account or authenticated user
    **Rate Limit**: 100 requests per minute

    Convenience endpoint for prediction requests.
    """
    correlation_id = request.state.correlation_id if hasattr(request.state, 'correlation_id') else "unknown"

    try:
        from src.models.mastery import DaprIntent
        process_request.intent = DaprIntent.GET_PREDICTION

        return await dapr_process(request, process_request, security_manager, state_manager, dapr_service)

    except Exception as e:
        logger.error(f"Dapr prediction endpoint error: {e}", extra={"correlation_id": correlation_id})
        return DaprProcessResponse(
            success=False,
            error=str(e),
            correlation_id=str(correlation_id)
        )


@dapr_router.post("/process/path", response_model=DaprProcessResponse)
async def dapr_path_endpoint(
    request: Request,
    process_request: DaprProcessRequest,
    security_manager: SecurityManager = Depends(DaprEndpoints.get_security_manager),
    state_manager: StateManager = Depends(DaprEndpoints.get_state_manager),
    dapr_service: DaprServiceHandler = Depends(DaprEndpoints.get_dapr_service)
):
    """
    Dapr learning path endpoint (optimized)

    **Auth**: Dapr service account or authenticated user
    **Rate Limit**: 100 requests per minute

    Convenience endpoint for learning path generation.
    """
    correlation_id = request.state.correlation_id if hasattr(request.state, 'correlation_id') else "unknown"

    try:
        from src.models.mastery import DaprIntent
        process_request.intent = DaprIntent.GENERATE_PATH

        return await dapr_process(request, process_request, security_manager, state_manager, dapr_service)

    except Exception as e:
        logger.error(f"Dapr path endpoint error: {e}", extra={"correlation_id": correlation_id})
        return DaprProcessResponse(
            success=False,
            error=str(e),
            correlation_id=str(correlation_id)
        )


# Health check for Dapr integration
@dapr_router.get("/health")
async def dapr_health_check(
    request: Request,
    state_manager: StateManager = Depends(DaprEndpoints.get_state_manager)
):
    """
    Dapr integration health check

    **Auth**: None (service-to-service)
    **Rate Limit**: 200 requests per minute

    Simple health check to verify Dapr integration is working.
    """
    try:
        # Test basic state store operation
        test_key = "health:dapr:check"
        test_data = {"timestamp": datetime.utcnow().isoformat(), "service": "mastery-engine"}
        await state_manager.save(test_key, test_data, ttl_hours=1)

        # Verify we can read it back
        result = await state_manager.get(test_key)
        await state_manager.delete(test_key)

        if result:
            return {
                "status": "healthy",
                "dapr_integration": "active",
                "state_store": "available",
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "status": "degraded",
                "dapr_integration": "active",
                "state_store": "unavailable",
                "timestamp": datetime.utcnow().isoformat()
            }

    except Exception as e:
        logger.error(f"Dapr health check failed: {e}")
        return {
            "status": "unhealthy",
            "dapr_integration": "failed",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


# Global error handler for Dapr endpoints
@dapr_router.exception_handler(Exception)
async def dapr_exception_handler(request: Request, exc: Exception):
    """Global exception handler for Dapr endpoints"""
    logger.error(f"Dapr endpoint error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "success": False,
            "error": "Dapr operation failed",
            "metadata": {"error_code": "INTERNAL_ERROR"}
        }
    )


# Import datetime for health check
from datetime import datetime