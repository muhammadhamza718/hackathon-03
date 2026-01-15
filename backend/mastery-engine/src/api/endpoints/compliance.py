"""
Compliance and GDPR Endpoints
=============================

GDPR compliance endpoints for data deletion and export.
Includes consent management and audit logging.
"""

import logging
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import JSONResponse

from src.security import SecurityManager, Permission
from src.services.state_manager import StateManager

logger = logging.getLogger(__name__)

# Create router for compliance endpoints
compliance_router = APIRouter(prefix="/compliance", tags=["GDPR Compliance"])


class ComplianceEndpoints:
    """Collection of compliance and GDPR endpoints"""

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
    def validate_admin_access(claims: dict):
        """Ensure user has admin privileges"""
        if claims.get("role") != "admin":
            raise HTTPException(status_code=403, detail="Admin access required")


@compliance_router.delete("/student/{student_id}")
async def delete_student_data(
    student_id: str,
    request: Request,
    claims: dict = Depends(ComplianceEndpoints.validate_admin_access),
    security_manager: SecurityManager = Depends(ComplianceEndpoints.get_security_manager),
    state_manager: StateManager = Depends(ComplianceEndpoints.get_state_manager)
):
    """
    GDPR Right to Erasure: Delete all student data

    **Auth**: Admin required
    **Rate Limit**: 10 requests per minute

    Deletes all data associated with a student within 24 hours.
    Maintains audit trail of deletion.
    """
    correlation_id = str(request.state.correlation_id) if hasattr(request.state, 'correlation_id') else "unknown"

    try:
        # Audit the deletion request
        security_manager.audit_access(
            user_id=claims["sub"],
            action="DELETE",
            resource=f"student:{student_id}:all_data",
            details={
                "correlation_id": correlation_id,
                "reason": "gdpr_right_to_erasure"
            }
        )

        # Get current data for audit before deletion
        current_mastery = await state_manager.get_mastery_score(student_id)
        activity_data = await state_manager.get_activity_data(student_id)
        history = await state_manager.get_mastery_history(student_id, days=90)

        # Schedule deletion (in production, this would be an async job)
        deletion_tasks = []

        # Delete mastery scores
        if current_mastery:
            deletion_tasks.append(f"mastery_score:{student_id}")
            await state_manager.delete(StateKeyPatterns.current_mastery(student_id))

        # Delete historical data
        for snapshot in history:
            snapshot_key = StateKeyPatterns.daily_snapshot(student_id, snapshot.date)
            deletion_tasks.append(f"snapshot:{snapshot_key}")
            await state_manager.delete(snapshot_key)

        # Delete activity data
        if activity_data:
            deletion_tasks.append(f"activity:{student_id}")
            await state_manager.delete(StateKeyPatterns.activity_data(student_id))

        # Delete event logs
        await state_manager.delete(f"student:{student_id}:events:log")

        # Delete consent records
        consent_keys = [k for k in state_manager.consent_store.keys() if k.startswith(f"{student_id}:")]
        for key in consent_keys:
            state_manager.consent_store.pop(key, None)
            deletion_tasks.append(f"consent:{key}")

        # Create deletion record
        deletion_record = {
            "student_id": student_id,
            "deleted_at": datetime.utcnow().isoformat(),
            "deleted_by": claims["sub"],
            "tasks": deletion_tasks,
            "correlation_id": correlation_id,
            "compliance": "GDPR Article 17"
        }

        # Log deletion in audit trail
        security_manager.audit_access(
            user_id=claims["sub"],
            action="DELETE_COMPLETE",
            resource=f"student:{student_id}",
            details=deletion_record
        )

        logger.info(
            f"GDPR deletion completed for {student_id}",
            extra={"correlation_id": correlation_id, "deletion_record": deletion_record}
        )

        return {
            "status": "success",
            "message": f"All data for student {student_id} has been scheduled for deletion within 24 hours",
            "deleted_tasks": deletion_tasks,
            "correlation_id": correlation_id,
            "compliance": "GDPR Article 17 - Right to Erasure"
        }

    except Exception as e:
        logger.error(
            f"GDPR deletion failed for {student_id}: {e}",
            extra={"correlation_id": correlation_id},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Deletion failed: {str(e)}")


@compliance_router.get("/student/{student_id}/export")
async def export_student_data(
    student_id: str,
    request: Request,
    claims: dict = Depends(ComplianceEndpoints.validate_admin_access),
    state_manager: StateManager = Depends(ComplianceEndpoints.get_state_manager),
    security_manager: SecurityManager = Depends(ComplianceEndpoints.get_security_manager)
):
    """
    GDPR Right to Data Portability: Export all student data

    **Auth**: Admin required
    **Rate Limit**: 5 requests per minute

    Returns complete data export in JSON format.
    """
    correlation_id = str(request.state.correlation_id) if hasattr(request.state, 'correlation_id') else "unknown"

    try:
        # Audit the export request
        security_manager.audit_access(
            user_id=claims["sub"],
            action="EXPORT",
            resource=f"student:{student_id}",
            details={
                "correlation_id": correlation_id,
                "format": "JSON",
                "reason": "gdpr_right_to_portability"
            }
        )

        # Collect all student data
        export_data = {
            "export_version": "1.0",
            "exported_at": datetime.utcnow().isoformat(),
            "exported_by": claims["sub"],
            "student_id": student_id,
            "compliance": "GDPR Article 20 - Right to Data Portability",
            "data": {}
        }

        # Get current mastery
        mastery = await state_manager.get_mastery_score(student_id)
        if mastery:
            export_data["data"]["current_mastery"] = mastery.model_dump()

        # Get historical data
        history = await state_manager.get_mastery_history(student_id, days=90)
        if history:
            export_data["data"]["mastery_history"] = [h.model_dump() for h in history]

        # Get activity data
        activity = await state_manager.get_activity_data(student_id)
        if activity:
            export_data["data"]["activity"] = activity.model_dump()

        # Get event logs
        event_log = await state_manager.get(f"student:{student_id}:events:log")
        if event_log:
            export_data["data"]["event_log"] = event_log

        # Get consent records
        consent_records = [
            consent.to_dict() for consent in security_manager.consent_store.values()
            if consent.student_id == student_id
        ]
        if consent_records:
            export_data["data"]["consent_records"] = consent_records

        # Get audit logs for this student
        audit_logs = security_manager.get_audit_logs(user_id=student_id, limit=1000)
        if audit_logs:
            export_data["data"]["audit_logs"] = audit_logs

        # Compute integrity hash
        data_hash = security_manager.compute_data_hash(export_data["data"])
        export_data["integrity_hash"] = data_hash

        # Log the export
        security_manager.audit_access(
            user_id=claims["sub"],
            action="EXPORT_COMPLETE",
            resource=f"student:{student_id}",
            details={
                "correlation_id": correlation_id,
                "hash": data_hash,
                "size": len(json.dumps(export_data))
            }
        )

        logger.info(
            f"GDPR export completed for {student_id}",
            extra={"correlation_id": correlation_id, "size": len(json.dumps(export_data))}
        )

        return export_data

    except Exception as e:
        logger.error(
            f"GDPR export failed for {student_id}: {e}",
            extra={"correlation_id": correlation_id},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Export failed: {str(e)}")


@compliance_router.post("/consent/{student_id}")
async def record_consent(
    student_id: str,
    consent_type: str = Query(..., description="Type of consent (e.g., data_processing, analytics)"),
    granted: bool = Query(..., description="Whether consent is granted"),
    request: Request,
    claims: dict = Depends(ComplianceEndpoints.get_security_manager),
    security_manager: SecurityManager = Depends(ComplianceEndpoints.get_security_manager)
):
    """
    Record GDPR consent for a student

    **Auth**: Student, Teacher, or Admin
    **Rate Limit**: 20 requests per minute

    Records consent in the consent store.
    """
    correlation_id = str(request.state.correlation_id) if hasattr(request.state, 'correlation_id') else "unknown"

    try:
        # Security check: students can only record their own consent
        user_id = claims.get("sub")
        user_role = claims.get("role")

        if user_role == "student" and user_id != student_id:
            raise HTTPException(status_code=403, detail="Can only record your own consent")

        # Record consent
        consent_record = security_manager.record_consent(student_id, consent_type, granted)

        # Audit trail
        security_manager.audit_access(
            user_id=user_id,
            action="CONSENT_RECORD",
            resource=f"consent:{student_id}:{consent_type}",
            details={
                "granted": granted,
                "correlation_id": correlation_id,
                "version": consent_record.version
            }
        )

        return {
            "status": "success",
            "student_id": student_id,
            "consent_type": consent_type,
            "granted": granted,
            "recorded_at": consent_record.timestamp.isoformat(),
            "correlation_id": correlation_id
        }

    except Exception as e:
        logger.error(f"Consent recording failed: {e}", extra={"correlation_id": correlation_id})
        raise HTTPException(status_code=500, detail=str(e))


@compliance_router.post("/consent/{student_id}/withdraw")
async def withdraw_consent(
    student_id: str,
    consent_type: str = Query(..., description="Type of consent to withdraw"),
    request: Request,
    claims: dict = Depends(ComplianceEndpoints.get_security_manager),
    security_manager: SecurityManager = Depends(ComplianceEndpoints.get_security_manager)
):
    """
    Withdraw GDPR consent

    **Auth**: Student, Teacher, or Admin
    **Rate Limit**: 20 requests per minute

    Marks consent as withdrawn.
    """
    correlation_id = str(request.state.correlation_id) if hasattr(request.state, 'correlation_id') else "unknown"

    try:
        # Security check
        user_id = claims.get("sub")
        user_role = claims.get("role")

        if user_role == "student" and user_id != student_id:
            raise HTTPException(status_code=403, detail="Can only withdraw your own consent")

        # Withdraw consent
        success = security_manager.withdraw_consent(student_id, consent_type)

        if not success:
            raise HTTPException(status_code=404, detail=f"No consent found for {consent_type}")

        # Audit trail
        security_manager.audit_access(
            user_id=user_id,
            action="CONSENT_WITHDRAW",
            resource=f"consent:{student_id}:{consent_type}",
            details={"correlation_id": correlation_id}
        )

        return {
            "status": "success",
            "student_id": student_id,
            "consent_type": consent_type,
            "withdrawn_at": datetime.utcnow().isoformat(),
            "correlation_id": correlation_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Consent withdrawal failed: {e}", extra={"correlation_id": correlation_id})
        raise HTTPException(status_code=500, detail=str(e))


@compliance_router.get("/audit/logs")
async def get_audit_logs(
    request: Request,
    user_id: Optional[str] = Query(None, description="Filter by user ID"),
    resource_type: Optional[str] = Query(None, description="Filter by resource type"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of logs to return"),
    claims: dict = Depends(ComplianceEndpoints.validate_admin_access),
    security_manager: SecurityManager = Depends(ComplianceEndpoints.get_security_manager)
):
    """
    Retrieve audit logs

    **Auth**: Admin required
    **Rate Limit**: 10 requests per minute

    Returns audit trail for compliance monitoring.
    """
    correlation_id = str(request.state.correlation_id) if hasattr(request.state, 'correlation_id') else "unknown"

    try:
        logs = security_manager.get_audit_logs(user_id=user_id, resource_type=resource_type, limit=limit)

        security_manager.audit_access(
            user_id=claims["sub"],
            action="AUDIT_VIEW",
            resource="audit:logs",
            details={
                "correlation_id": correlation_id,
                "filter_user_id": user_id,
                "filter_resource": resource_type,
                "returned_count": len(logs)
            }
        )

        return {
            "logs": logs,
            "total": len(logs),
            "correlation_id": correlation_id
        }

    except Exception as e:
        logger.error(f"Failed to retrieve audit logs: {e}", extra={"correlation_id": correlation_id})
        raise HTTPException(status_code=500, detail=str(e))


@compliance_router.get("/consent/status/{student_id}")
async def get_consent_status(
    student_id: str,
    request: Request,
    claims: dict = Depends(ComplianceEndpoints.get_security_manager),
    security_manager: SecurityManager = Depends(ComplianceEndpoints.get_security_manager)
):
    """
    Check consent status for a student

    **Auth**: Student (own data), Teacher, or Admin
    **Rate Limit**: 20 requests per minute
    """
    correlation_id = str(request.state.correlation_id) if hasattr(request.state, 'correlation_id') else "unknown"

    try:
        user_id = claims.get("sub")
        user_role = claims.get("role")

        if user_role == "student" and user_id != student_id:
            raise HTTPException(status_code=403, detail="Can only check your own consent status")

        # Find all consent records for this student
        consent_records = [
            consent.to_dict() for consent in security_manager.consent_store.values()
            if consent.student_id == student_id
        ]

        security_manager.audit_access(
            user_id=user_id,
            action="CONSENT_CHECK",
            resource=f"consent:{student_id}",
            details={"correlation_id": correlation_id}
        )

        return {
            "student_id": student_id,
            "consent_records": consent_records,
            "correlation_id": correlation_id
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to check consent status: {e}", extra={"correlation_id": correlation_id})
        raise HTTPException(status_code=500, detail=str(e))


# Global error handler for compliance endpoints
@compliance_router.exception_handler(Exception)
async def compliance_exception_handler(request: Request, exc: Exception):
    """Global exception handler for compliance endpoints"""
    logger.error(f"Compliance endpoint error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Compliance operation failed",
            "message": "Internal error during compliance operation",
            "correlation_id": getattr(request.state, 'correlation_id', 'unknown')
        }
    )