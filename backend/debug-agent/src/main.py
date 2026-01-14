"""
Debug Agent - Syntax Analysis and Error Detection Microservice
Elite Implementation Standard v2.0.0
"""

from fastapi import FastAPI, HTTPException, status
from contextlib import asynccontextmanager
import asyncio
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan manager for startup/shutdown"""
    logger.info("Debug Agent starting up...")

    # Initialize services
    try:
        logger.info("Debug Agent services initialized")
    except Exception as e:
        logger.warning(f"Service initialization failed: {e}")

    asyncio.create_task(health_check_loop())

    yield

    logger.info("Debug Agent shutting down...")

app = FastAPI(
    title="Debug Agent",
    description="Syntax analysis and error detection agent for LearnFlow",
    version="1.0.0",
    lifespan=lifespan
)

@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "debug-agent",
        "timestamp": asyncio.get_event_loop().time()
    }

@app.get("/ready", status_code=status.HTTP_200_OK)
async def readiness_check():
    """Readiness check"""
    return {
        "status": "ready",
        "service": "debug-agent"
    }

@app.get("/", status_code=status.HTTP_200_OK)
async def root():
    """API information endpoint"""
    return {
        "service": "debug-agent",
        "version": "1.0.0",
        "endpoints": [
            "/analyze",
            "/patterns",
            "/suggestions",
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
    port = int(os.getenv("PORT", 8001))
    uvicorn.run(app, host="0.0.0.0", port=port)