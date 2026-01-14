"""
Exercise Agent - Adaptive Problem Generation Microservice
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
from api.endpoints.generate import router as generate_router
from api.endpoints.calibrate import router as calibrate_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for startup/shutdown"""
    logger.info("Exercise Agent starting up...")

    # Initialize services
    try:
        logger.info("Exercise Agent services initialized")
    except Exception as e:
        logger.warning(f"Service initialization failed: {e}")

    asyncio.create_task(health_check_loop())

    yield

    logger.info("Exercise Agent shutting down...")

app = FastAPI(
    title="Exercise Agent",
    description="Adaptive exercise generation and difficulty calibration agent for LearnFlow",
    version="1.0.0",
    lifespan=lifespan
)

# Include routers
app.include_router(generate_router, prefix="/generate")
app.include_router(calibrate_router, prefix="/calibrate")

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
        if intent == "practice_exercises":
            # Generate adaptive problems
            topic = student_context.get("topic", query)
            student_level = student_context.get("student_level", "beginner")
            difficulty = student_context.get("difficulty", "auto")

            from services.problem_generator import generate_problem_with_mcp
            from services.difficulty_calibration import calibrate_difficulty_with_mcp

            # Calibrate difficulty if needed
            if difficulty == "auto":
                difficulty = await calibrate_difficulty_with_mcp(
                    student_context.get("mastery", 0.5),
                    student_context.get("success_rate", 0.6)
                )

            # Generate problem
            problem = await generate_problem_with_mcp(
                topic=topic,
                difficulty=difficulty,
                student_progress=student_context
            )

            return {
                "status": "success",
                "agent": "exercise-agent",
                "result": {
                    "topic": topic,
                    "difficulty": difficulty,
                    "problem": problem,
                    "intent": intent,
                    "confidence": confidence
                },
                "processed_at": "2026-01-14T10:30:00Z"
            }

        elif intent == "difficulty_calibration":
            # Calibrate difficulty based on student performance
            mastery = student_context.get("mastery", 0.5)
            success_rate = student_context.get("success_rate", 0.6)

            from services.difficulty_calibration import calibrate_difficulty_with_mcp
            difficulty = await calibrate_difficulty_with_mcp(mastery, success_rate)

            return {
                "status": "success",
                "agent": "exercise-agent",
                "result": {
                    "difficulty": difficulty,
                    "mastery": mastery,
                    "success_rate": success_rate,
                    "intent": intent,
                    "confidence": confidence
                },
                "processed_at": "2026-01-14T10:30:00Z"
            }

        else:
            return {
                "status": "error",
                "agent": "exercise-agent",
                "error": f"Unknown intent: {intent}",
                "supported_intents": ["practice_exercises", "difficulty_calibration"]
            }

    except Exception as e:
        logger.error(f"Dapr handler error: {e}")
        return {
            "status": "error",
            "agent": "exercise-agent",
            "error": str(e),
            "data_received": data
        }

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "exercise-agent",
        "timestamp": asyncio.get_event_loop().time()
    }

@app.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check():
    """Readiness check"""
    return {
        "status": "ready",
        "service": "exercise-agent"
    }

@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    """API information endpoint"""
    return {
        "service": "exercise-agent",
        "version": "1.0.0",
        "endpoints": [
            "/generate",
            "/calibrate",
            "/process",
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
    port = int(os.getenv("PORT", 8003))
    uvicorn.run(app, host="0.0.0.0", port=port)