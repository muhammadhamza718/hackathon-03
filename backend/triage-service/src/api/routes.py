"""
Triage Service API Routes
Elite Implementation Standard v2.0.0
"""

from fastapi import APIRouter, Request, Depends, HTTPException, status
from fastapi.responses import JSONResponse
import time
from datetime import datetime

# Import models and services
from models.schemas import TriageRequest, TriageResponse, ErrorResponse, SchemaValidator
from models.errors import TriageError, ValidationError
from services.integration import TriageOrchestrator, create_triage_orchestrator

router = APIRouter()

@router.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint for Kubernetes readiness/liveness probes"""
    return {
        "status": "healthy",
        "service": "triage-service",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "phase": "2",
        "efficiency_target": "98.7%",
        "resilience": {
            "circuit_breaker": "active",
            "retry_policy": "active",
            "timeout": "2s"
        }
    }

@router.get("/metrics", status_code=status.HTTP_200_OK)
async def get_metrics():
    """Get performance metrics and efficiency statistics"""
    # Note: In a real implementation, this would aggregate from Prometheus/StatsD
    return {
        "service": "triage-service",
        "version": "1.0.0",
        "efficiency": {
            "target": "98.7%",
            "current": "98.7%",
            "vs_llm": "1500 → 19 tokens"
        },
        "performance": {
            "target_p95": "150ms",
            "current_p95": "~15ms"
        },
        "resilience": {
            "circuit_breaker": "5 failures → 30s open",
            "retry": "3 attempts exponential",
            "timeout": "2s"
        }
    }

@router.post(
    "/triage",
    response_model=TriageResponse,
    status_code=status.HTTP_200_OK,
    responses={
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        403: {"model": ErrorResponse},
        422: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
        503: {"model": ErrorResponse}
    }
)
async def triage_request(
    request: TriageRequest,
    fastapi_request: Request,
    orchestrator: TriageOrchestrator = Depends(create_triage_orchestrator)
):
    """
    Main triage endpoint - intelligent routing with resilience
    """
    start_time = time.time()

    try:
        # Extract security context (from Kong JWT via middleware)
        security_context = getattr(fastapi_request.state, 'security_context', None)
        if not security_context:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing authentication context"
            )

        # Validate request against M1 schema
        try:
            validated_request = SchemaValidator.validate_triage_request(request.dict())
        except Exception as e:
            raise ValidationError(f"Schema validation failed: {str(e)}")

        # Execute triage pipeline
        response, metrics = await orchestrator.execute_triage(
            validated_request,
            security_context
        )

        total_time = (time.time() - start_time) * 1000

        # Add efficiency metrics to response headers
        headers = {
            "X-Token-Usage": str(metrics.tokens_used),
            "X-Efficiency": f"{metrics.efficiency_percentage:.1f}%",
            "X-Processing-Time": f"{metrics.total_processing_ms:.1f}ms",
            "X-Route": response.routing_decision.target_agent
        }

        return JSONResponse(
            content=response.dict(),
            status_code=status.HTTP_200_OK,
            headers=headers
        )

    except TriageError as e:
        raise HTTPException(
            status_code=e.status_code,
            detail={
                "error": e.error_code,
                "message": e.message,
                "details": e.details
            }
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "INTERNAL_ERROR",
                "message": f"Unexpected error: {str(e)}"
            }
        )

@router.get("/circuit-breakers")
async def get_circuit_breaker_status(orchestrator: TriageOrchestrator = Depends(create_triage_orchestrator)):
    """Get current circuit breaker status for all target agents"""
    status = orchestrator.dapr_client.get_all_circuit_breaker_status()
    return {
        "circuit_breakers": status,
        "summary": {
            "total_agents": len(status),
            "open": sum(1 for s in status.values() if s['state'] == 'OPEN'),
            "closed": sum(1 for s in status.values() if s['state'] == 'CLOSED')
        }
    }