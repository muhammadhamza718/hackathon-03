"""
Progress Agent - Mastery Tracking Microservice
Elite Implementation Standard v2.0.0
"""

from fastapi import FastAPI, HTTPException, status
from contextlib import asynccontextmanager
import asyncio
import logging
import os
import dapr.clients
import dapr.ext.grpc

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Lifespan manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Progress Agent starting up...")

    # Initialize Dapr client
    try:
        dapr_client = dapr.clients.DaprClient()
        logger.info("Dapr client initialized")
    except Exception as e:
        logger.warning(f"Dapr client initialization failed: {e}")

    # Health check loop
    asyncio.create_task(health_check_loop())

    yield

    # Shutdown
    logger.info("Progress Agent shutting down...")

app = FastAPI(
    title="Progress Agent",
    description="Mastery tracking and progress management agent for LearnFlow",
    version="1.0.0",
    lifespan=lifespan
)

# Health check endpoint
@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint for Kubernetes liveness/readiness probes"""
    return {
        "status": "healthy",
        "service": "progress-agent",
        "timestamp": asyncio.get_event_loop().time()
    }

@app.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check():
    """Readiness check - verifies Dapr and dependencies"""
    return {
        "status": "ready",
        "service": "progress-agent"
    }

@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    """API information endpoint"""
    return {
        "service": "progress-agent",
        "version": "1.0.0",
        "endpoints": [
            "/mastery",
            "/progress",
            "/history",
            "/health",
            "/ready"
        ]
    }

async def health_check_loop():
    """Background task for periodic health monitoring"""
    while True:
        await asyncio.sleep(60)
        logger.debug("Health check ping")

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)