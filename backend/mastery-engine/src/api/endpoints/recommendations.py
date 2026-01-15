"""
Adaptive Recommendations Endpoints
===================================

Personalized learning recommendations and adaptive learning paths.
"""

import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, Request, Query
from fastapi.responses import JSONResponse

from src.security import SecurityManager
from src.services.state_manager import StateManager
from src.services.recommendation_engine import RecommendationEngine, MCPRecommendationSkill
from src.models.recommendations import (
    AdaptiveRecommendation,
    LearningPath,
    RecommendationQuery,
    LearningPathQuery,
    ComponentArea,
    PriorityLevel
)

logger = logging.getLogger(__name__)

# Create router for recommendations endpoints
recommendations_router = APIRouter(prefix="/recommendations", tags=["Recommendations"])


class RecommendationEndpoints:
    """Collection of adaptive recommendation endpoints"""

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
    async def get_recommendation_engine(state_manager: StateManager) -> RecommendationEngine:
        """Dependency injection for RecommendationEngine"""
        return RecommendationEngine(state_manager)

    @staticmethod
    async def get_mcp_skill(engine: RecommendationEngine) -> MCPRecommendationSkill:
        """Dependency injection for MCP Recommendation Skill"""
        return MCPRecommendationSkill(engine)

    @staticmethod
    def validate_student_access(claims: dict, student_id: str):
        """Ensure student can only access their own data"""
        user_role = claims.get("role")
        user_id = claims.get("sub")

        if user_role == "student" and user_id != student_id:
            raise HTTPException(status_code=403, detail="Cannot access other students' data")


@recommendations_router.post("/adaptive", response_model=List[AdaptiveRecommendation])
async def get_adaptive_recommendations(
    request: Request,
    recommendation_request: dict,
    claims: dict = Depends(RecommendationEndpoints.get_security_manager),
    security_manager: SecurityManager = Depends(RecommendationEndpoints.get_security_manager),
    state_manager: StateManager = Depends(RecommendationEndpoints.get_state_manager),
    engine: RecommendationEngine = Depends(RecommendationEndpoints.get_recommendation_engine)
):
    """
    Get adaptive learning recommendations based on current mastery state

    **Auth**: Student (own data), Teacher, Admin
    **Rate Limit**: 20 requests per minute

    Analyzes current mastery scores and generates personalized recommendations
    targeting the weakest areas with appropriate priorities.

    Request body:
    ```json
    {
        "student_id": "student_123",
        "limit": 5,
        "priority": "high",
        "component_filter": ["completion", "quiz"]
    }
    ```

    Response:
    - List of prioritized recommendations
    - Each includes action type, target area, estimated time, and resources
    """
    correlation_id = str(request.state.correlation_id) if hasattr(request.state, 'correlation_id') else "unknown"

    try:
        # Extract parameters
        student_id = recommendation_request.get("student_id")
        limit = recommendation_request.get("limit", 5)
        priority = recommendation_request.get("priority")
        component_filter = recommendation_request.get("component_filter")

        if not student_id:
            raise HTTPException(status_code=400, detail="student_id is required")

        # Convert string priority to enum
        priority_enum = None
        if priority:
            try:
                priority_enum = PriorityLevel(priority)
            except ValueError:
                raise HTTPException(status_code=400, detail=f"Invalid priority: {priority}")

        # Convert component filter strings to enums
        component_enums = None
        if component_filter:
            try:
                component_enums = [ComponentArea(c) for c in component_filter]
            except ValueError as e:
                raise HTTPException(status_code=400, detail=f"Invalid component filter: {e}")

        # Security check
        RecommendationEndpoints.validate_student_access(claims, student_id)

        # Audit
        security_manager.audit_access(
            user_id=claims["sub"],
            action="GENERATE_RECOMMENDATIONS",
            resource=f"recommendations:{student_id}",
            details={
                "correlation_id": correlation_id,
                "limit": limit,
                "priority": priority,
                "components": component_filter
            }
        )

        # Generate recommendations
        recommendations = await engine.generate_adaptive_recommendations(
            student_id=student_id,
            limit=limit,
            priority_filter=priority_enum,
            component_filter=component_enums
        )

        logger.info(
            f"Generated {len(recommendations)} adaptive recommendations for {student_id}",
            extra={"correlation_id": correlation_id, "student_id": student_id}
        )

        return recommendations

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Recommendation generation failed: {e}",
            extra={"correlation_id": correlation_id},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Recommendation generation failed: {str(e)}")


@recommendations_router.post("/learning-path", response_model=LearningPath)
async def get_learning_path(
    request: Request,
    path_request: dict,
    claims: dict = Depends(RecommendationEndpoints.get_security_manager),
    security_manager: SecurityManager = Depends(RecommendationEndpoints.get_security_manager),
    state_manager: StateManager = Depends(RecommendationEndpoints.get_state_manager),
    engine: RecommendationEngine = Depends(RecommendationEndpoints.get_recommendation_engine)
):
    """
    Generate a comprehensive adaptive learning path

    **Auth**: Student (own data), Teacher, Admin
    **Rate Limit**: 10 requests per minute

    Creates a sequenced learning path with dependencies, time estimates,
    and clear progression toward mastery goals.

    Request body:
    ```json
    {
        "student_id": "student_123",
        "target_level": "proficient",
        "max_duration_minutes": 300
    }
    ```

    Valid target levels: "novice", "developing", "proficient", "master"
    max_duration_minutes: Optional limit on total path length
    """
    correlation_id = str(request.state.correlation_id) if hasattr(request.state, 'correlation_id') else "unknown"

    try:
        student_id = path_request.get("student_id")
        target_level = path_request.get("target_level")
        max_duration = path_request.get("max_duration_minutes")

        if not student_id:
            raise HTTPException(status_code=400, detail="student_id is required")

        # Validate target level if provided
        if target_level:
            valid_levels = ["novice", "developing", "proficient", "master"]
            if target_level not in valid_levels:
                raise HTTPException(
                    status_code=400,
                    detail=f"target_level must be one of: {', '.join(valid_levels)}"
                )

        # Security check
        RecommendationEndpoints.validate_student_access(claims, student_id)

        # Audit
        security_manager.audit_access(
            user_id=claims["sub"],
            action="GENERATE_LEARNING_PATH",
            resource=f"learning_path:{student_id}",
            details={
                "correlation_id": correlation_id,
                "target_level": target_level,
                "max_duration": max_duration
            }
        )

        # Generate learning path
        learning_path = await engine.generate_learning_path(
            student_id=student_id,
            target_level=target_level,
            max_duration_minutes=max_duration
        )

        logger.info(
            f"Generated learning path for {student_id}: {len(learning_path.recommendations)} recommendations, "
            f"{learning_path.total_time_estimate} minutes",
            extra={"correlation_id": correlation_id, "student_id": student_id}
        )

        return learning_path

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"Learning path generation failed: {e}",
            extra={"correlation_id": correlation_id},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"Learning path generation failed: {str(e)}")


@recommendations_router.post("/mcp/skill-recommendations")
async def get_mcp_skill_recommendations(
    request: Request,
    skill_request: dict,
    claims: dict = Depends(RecommendationEndpoints.get_security_manager),
    security_manager: SecurityManager = Depends(RecommendationEndpoints.get_security_manager),
    state_manager: StateManager = Depends(RecommendationEndpoints.get_state_manager),
    engine: RecommendationEngine = Depends(RecommendationEndpoints.get_recommendation_engine),
    mcp_skill: MCPRecommendationSkill = Depends(RecommendationEndpoints.get_mcp_skill)
):
    """
    Get recommendations via MCP Skill (token-efficient)

    **Auth**: Student (own data), Teacher, Admin
    **Rate Limit**: 30 requests per minute

    Uses MCP pattern for highly efficient recommendation generation.
    Best for integration with other AI agents or automated systems.

    Request body:
    ```json
    {
        "student_id": "student_123",
        "use_path": false
    }
    ```
    """
    correlation_id = str(request.state.correlation_id) if hasattr(request.state, 'correlation_id') else "unknown"

    try:
        student_id = skill_request.get("student_id")
        use_path = skill_request.get("use_path", False)

        if not student_id:
            raise HTTPException(status_code=400, detail="student_id is required")

        # Security check
        RecommendationEndpoints.validate_student_access(claims, student_id)

        # Get current mastery for analysis
        current_mastery = await state_manager.get_mastery_score(student_id)
        if not current_mastery:
            raise HTTPException(status_code=404, detail="No mastery data found for student")

        # Audit
        security_manager.audit_access(
            user_id=claims["sub"],
            action="MCP_SKILL_RECOMMENDATIONS",
            resource=f"mcp_recommendations:{student_id}",
            details={
                "correlation_id": correlation_id,
                "use_path": use_path
            }
        )

        if use_path:
            # Generate efficient path
            # First get priority areas via efficient analysis
            analysis = await mcp_skill.execute_recommendation_analysis(student_id, current_mastery)
            priority_areas = [ComponentArea(item["component"]) for item in analysis["priority_areas"]]

            result = await mcp_skill.generate_efficient_path(student_id, priority_areas)
        else:
            # Generate just the analysis
            result = await mcp_skill.execute_recommendation_analysis(student_id, current_mastery)

        logger.info(
            f"MCP skill recommendations for {student_id}",
            extra={"correlation_id": correlation_id, "student_id": student_id}
        )

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(
            f"MCP skill recommendations failed: {e}",
            extra={"correlation_id": correlation_id},
            exc_info=True
        )
        raise HTTPException(status_code=500, detail=f"MCP skill recommendations failed: {str(e)}")


@recommendations_router.get("/config", response_model=dict)
async def get_recommendation_config(
    request: Request,
    claims: dict = Depends(RecommendationEndpoints.get_security_manager),
    security_manager: SecurityManager = Depends(RecommendationEndpoints.get_security_manager)
):
    """
    Get current recommendation engine configuration

    **Auth**: Student, Teacher, Admin
    **Rate Limit**: 50 requests per minute

    Returns thresholds, time estimates, and other configuration parameters
    used by the recommendation engine.
    """
    correlation_id = str(request.state.correlation_id) if hasattr(request.state, 'correlation_id') else "unknown"

    try:
        # Audit
        security_manager.audit_access(
            user_id=claims["sub"],
            action="VIEW_CONFIG",
            resource="recommendation_config",
            details={"correlation_id": correlation_id}
        )

        from src.models.recommendations import RecommendationConfig
        config = RecommendationConfig()

        return {
            "model_version": "1.0.0",
            "config": config.model_dump(),
            "notes": "These thresholds determine when recommendations are generated and their priorities"
        }

    except Exception as e:
        logger.error(f"Failed to retrieve config: {e}", extra={"correlation_id": correlation_id})
        raise HTTPException(status_code=500, detail=f"Failed to retrieve config: {str(e)}")


@recommendations_router.post("/feedback")
async def submit_recommendation_feedback(
    request: Request,
    feedback: dict,
    claims: dict = Depends(RecommendationEndpoints.get_security_manager),
    security_manager: SecurityManager = Depends(RecommendationEndpoints.get_security_manager),
    state_manager: StateManager = Depends(RecommendationEndpoints.get_state_manager)
):
    """
    Submit feedback on recommendations (for improvement)

    **Auth**: Student (own data)
    **Rate Limit**: 20 requests per minute

    Helps improve the recommendation algorithm over time.

    Request body:
    ```json
    {
        "recommendation_id": "rec_123",
        "completed": true,
        "time_taken": 25,
        "satisfaction_rating": 4,
        "improvement_score": 0.15
    }
    ```
    """
    correlation_id = str(request.state.correlation_id) if hasattr(request.state, 'correlation_id') else "unknown"

    try:
        recommendation_id = feedback.get("recommendation_id")
        completed = feedback.get("completed", False)
        satisfaction = feedback.get("satisfaction_rating")
        improvement = feedback.get("improvement_score")

        if not recommendation_id:
            raise HTTPException(status_code=400, detail="recommendation_id is required")

        if satisfaction and not (1 <= satisfaction <= 5):
            raise HTTPException(status_code=400, detail="satisfaction_rating must be between 1 and 5")

        # Audit
        security_manager.audit_access(
            user_id=claims["sub"],
            action="SUBMIT_FEEDBACK",
            resource=f"feedback:{recommendation_id}",
            details={
                "correlation_id": correlation_id,
                "completed": completed,
                "satisfaction": satisfaction
            }
        )

        # Store feedback (simplified - in production would store to dedicated feedback system)
        from src.models.recommendations import RecommendationMetric
        from datetime import datetime

        metric = {
            "recommendation_id": recommendation_id,
            "student_id": claims["sub"],
            "generated_at": datetime.utcnow().isoformat(),
            "completed_at": datetime.utcnow().isoformat() if completed else None,
            "satisfaction_rating": satisfaction,
            "improvement_score": improvement,
            "model_version": "1.0.0"
        }

        # Cache for future analysis
        try:
            key = f"feedback:{recommendation_id}:{datetime.utcnow().strftime('%Y-%m-%d-%H-%M')}"
            await state_manager.save(key, metric, ttl_hours=24 * 30)  # 30 days
        except Exception:
            pass  # Non-critical operation

        return {
            "status": "received",
            "message": "Thank you for your feedback - it will help improve recommendations"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Feedback submission failed: {e}", extra={"correlation_id": correlation_id})
        raise HTTPException(status_code=500, detail=f"Feedback submission failed: {str(e)}")


@recommendations_router.get("/recommendations/{student_id}/history")
async def get_recommendation_history(
    student_id: str,
    request: Request,
    days: int = Query(7, ge=1, le=30, description="Days to look back"),
    claims: dict = Depends(RecommendationEndpoints.get_security_manager),
    security_manager: SecurityManager = Depends(RecommendationEndpoints.get_security_manager),
    state_manager: StateManager = Depends(RecommendationEndpoints.get_state_manager)
):
    """
    Get recent recommendations history for a student

    **Auth**: Student (own data), Teacher, Admin
    **Rate Limit**: 15 requests per minute
    """
    correlation_id = str(request.state.correlation_id) if hasattr(request.state, 'correlation_id') else "unknown"

    try:
        # Security check
        RecommendationEndpoints.validate_student_access(claims, student_id)

        # Audit
        security_manager.audit_access(
            user_id=claims["sub"],
            action="VIEW_HISTORY",
            resource=f"recommendation_history:{student_id}",
            details={"correlation_id": correlation_id, "days": days}
        )

        # In a real implementation, this would query stored recommendation history
        # For now, return placeholder
        return {
            "student_id": student_id,
            "days": days,
            "history": [],
            "message": "Recommendation history tracking - feature ready for production implementation"
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"History retrieval failed: {e}", extra={"correlation_id": correlation_id})
        raise HTTPException(status_code=500, detail=f"History retrieval failed: {str(e)}")


# Global error handler for recommendations endpoints
@recommendations_router.exception_handler(Exception)
async def recommendations_exception_handler(request: Request, exc: Exception):
    """Global exception handler for recommendations endpoints"""
    logger.error(f"Recommendations endpoint error: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Recommendations operation failed",
            "message": "Internal error during recommendations operation"
        }
    )