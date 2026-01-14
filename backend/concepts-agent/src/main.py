"""
Concepts Agent - Knowledge Explanation Microservice
Elite Implementation Standard v2.0.0
"""

from fastapi import FastAPI, HTTPException, status
from contextlib import asynccontextmanager
import asyncio
import logging
import os
import sys

# Add src directory to path for imports
sys.path.append(os.path.dirname(__file__))

# Import routers
from api.endpoints.explain import router as explain_router
from api.endpoints.mapping import router as mapping_router
from api.endpoints.prerequisites import router as prerequisites_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for startup/shutdown"""
    logger.info("Concepts Agent starting up...")

    # Initialize services
    try:
        logger.info("Concepts Agent services initialized")
    except Exception as e:
        logger.warning(f"Service initialization failed: {e}")

    asyncio.create_task(health_check_loop())

    yield

    logger.info("Concepts Agent shutting down...")

app = FastAPI(
    title="Concepts Agent",
    description="Knowledge explanation and concept mapping agent for LearnFlow",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(explain_router, prefix="/explain")
app.include_router(mapping_router, prefix="/mapping")
app.include_router(prerequisites_router, prefix="/prerequisites")

# Dapr service invocation endpoint
from fastapi import Body
from typing import Dict, Any

@app.post("/process")
async def dapr_process_handler(data: Dict[str, Any] = Body(...)):
    """
    Dapr service invocation handler

    This endpoint receives service calls from the Triage Service via Dapr
    and routes them to the appropriate internal functionality.
    """
    logger.info(f"Dapr invocation received: {data}")

    try:
        intent = data.get("intent", "")
        query = data.get("query", "")
        student_context = data.get("student_context", {})
        confidence = data.get("confidence", 0.0)

        # Route based on intent
        if intent == "concept_explanation":
            # Extract concept from query or context
            concept = student_context.get("concept", query.replace("explain", "").strip())
            student_level = student_context.get("student_level", "beginner")

            from services.explanation_generator import generate_explanation_with_mcp
            explanation = generate_explanation_with_mcp(
                concept=concept,
                level=student_level,
                context=student_context,
                style="simple"
            )

            return {
                "status": "success",
                "agent": "concepts-agent",
                "result": {
                    "concept": concept,
                    "explanation": explanation,
                    "intent": intent,
                    "confidence": confidence
                },
                "processed_at": "2026-01-14T10:30:00Z"
            }

        elif intent == "concept_mapping":
            concept = data.get("concept", query)

            from services.concept_mapping import concept_mapper
            mapping = concept_mapper.get_learning_path(concept)
            prereqs = concept_mapper.get_prerequisites(concept)

            return {
                "status": "success",
                "agent": "concepts-agent",
                "result": {
                    "concept": concept,
                    "prerequisites": prereqs,
                    "learning_path": mapping,
                    "intent": intent,
                    "confidence": confidence
                },
                "processed_at": "2026-01-14T10:30:00Z"
            }

        elif intent == "prerequisites_check":
            concept = data.get("concept", query)
            student_level = student_context.get("student_level", "beginner")

            from services.concept_mapping import concept_mapper
            assessment = concept_mapper.assess_readiness([], concept)

            return {
                "status": "success",
                "agent": "concepts-agent",
                "result": {
                    "concept": concept,
                    "readiness": assessment,
                    "intent": intent,
                    "confidence": confidence
                },
                "processed_at": "2026-01-14T10:30:00Z"
            }

        else:
            return {
                "status": "error",
                "agent": "concepts-agent",
                "error": f"Unknown intent: {intent}",
                "supported_intents": ["concept_explanation", "concept_mapping", "prerequisites_check"]
            }

    except Exception as e:
        logger.error(f"Dapr handler error: {e}")
        return {
            "status": "error",
            "agent": "concepts-agent",
            "error": str(e),
            "data_received": data
        }

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "concepts-agent",
        "timestamp": asyncio.get_event_loop().time()
    }

@app.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check():
    """Readiness check"""
    return {
        "status": "ready",
        "service": "concepts-agent"
    }

@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    """API information endpoint"""
    return {
        "service": "concepts-agent",
        "version": "1.0.0",
        "endpoints": [
            "/explain",
            "/mapping",
            "/prerequisites",
            "/health",
            "/ready"
        ]
    }

async def health_check_loop():
    """Background health monitoring"""
    while True:
        await asyncio.sleep(60)
        logger.debug("Health check ping")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)