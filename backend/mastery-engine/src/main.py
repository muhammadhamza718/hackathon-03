"""
Mastery Engine FastAPI Application
===================================

Main application entry point with Dapr integration and lifecycle management.
"""

import logging
import os
import json
from contextlib import asynccontextmanager
from datetime import datetime
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.util import get_remote_address

from src.api.endpoints.mastery import mastery_router
from src.api.endpoints.compliance import compliance_router
from src.api.endpoints.analytics import analytics_router
from src.api.endpoints.recommendations import recommendations_router
from src.security import SecurityManager
from src.services.state_manager import StateManager
# Kafka consumer will be added in Phase 4
# from src.services.kafka_consumer import KafkaConsumer
from tls_config import TLSConfig

# Configure structured logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s [%(levelname)8s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

# Enhanced structured JSON logger
class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging"""
    def format(self, record):
        log_obj = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "correlation_id": getattr(record, 'correlation_id', 'unknown'),
            "endpoint": getattr(record, 'endpoint', 'unknown'),
            "user_id": getattr(record, 'user_id', 'unknown')
        }
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj, default=str)

# Setup JSON handler for production
if os.getenv("ENVIRONMENT", "development") == "production":
    json_handler = logging.StreamHandler()
    json_handler.setFormatter(JSONFormatter())
    logger.addHandler(json_handler)

# Rate limiter
limiter = Limiter(key_func=get_remote_address)

# Global state for application lifespan
app_state = {
    "state_manager": None,
    "security_manager": None,
    "ready": False
}

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application startup and shutdown lifecycle"""

    # Startup
    logger.info("🚀 Starting Mastery Engine...")

    try:
        # Initialize security manager
        app_state["security_manager"] = SecurityManager(
            jwt_secret=os.getenv("JWT_SECRET", "dev-secret-change-me")
        )
        logger.info("✅ Security manager initialized")

        # Initialize state manager
        app_state["state_manager"] = StateManager.create()
        logger.info("✅ State manager initialized")

        # Verify dependencies
        await verify_dependencies()

        # Mark as ready
        app_state["ready"] = True
        logger.info("✅ Mastery Engine ready for requests")

    except Exception as e:
        logger.error(f"❌ Startup failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("🛑 Shutting down Mastery Engine...")
    logger.info("✅ Shutdown complete")

async def verify_dependencies():
    """Verify all external dependencies are accessible"""
    logger.info("🔍 Verifying dependencies...")

    health_report = {
        "state_store": False,
        "kafka": False,
        "dapr": False,
        "timestamp": datetime.utcnow().isoformat()
    }

    # Check state store (Redis via Dapr)
    try:
        await app_state["state_manager"].health_check()
        health_report["state_store"] = True
        logger.info("✅ State store (Redis) is accessible")
    except Exception as e:
        logger.error(f"❌ State store health check failed: {e}")
        health_report["state_store_error"] = str(e)

    # Check Dapr sidecar (basic connectivity)
    try:
        # Try a simple state operation to verify Dapr connectivity
        test_key = "health:check:dapr"
        test_data = {"test": True, "timestamp": datetime.utcnow().isoformat()}
        success = await app_state["state_manager"].save(test_key, test_data, ttl_hours=1)

        if success:
            health_report["dapr"] = True
            logger.info("✅ Dapr sidecar is accessible")
            # Clean up test data
            await app_state["state_manager"].delete(test_key)
        else:
            logger.warning("⚠️ Dapr connectivity test failed")
    except Exception as e:
        logger.warning(f"⚠️ Dapr health check failed: {e}")
        # Dapr is optional for basic operations, don't raise

    # Check Kafka (will be enabled in Phase 4)
    health_report["kafka"] = False
    logger.info("ℹ️ Kafka not yet configured (Phase 4)")

    # Store health report
    app_state["health_report"] = health_report

    # Check overall health
    if not health_report["state_store"]:
        raise Exception("Critical dependency (state store) unavailable")

    logger.info("✅ Dependencies verified successfully")

# Create FastAPI application
app = FastAPI(
    title="Mastery Engine",
    description="Stateful microservice for student learning progress tracking and mastery calculation",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ALLOWED_ORIGINS", "*").split(","),
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
)

# Add rate limiting
app.state.limiter = limiter

# Security headers middleware (registered first for proper layering)
@app.middleware("http")
async def security_headers_middleware(request: Request, call_next):
    """Add security headers to all responses"""
    response = await call_next(request)

    # Add security headers
    security_headers = TLSConfig.get_security_headers()
    for header, value in security_headers.items():
        response.headers[header] = value

    # Add custom headers
    response.headers["X-Request-ID"] = str(request.state.correlation_id) if hasattr(request.state, 'correlation_id') else str(uuid.uuid4())
    response.headers["X-Service-Name"] = "mastery-engine"
    response.headers["X-API-Version"] = "1.0.0"

    return response

# Performance monitoring middleware (registered after CORS)
@app.middleware("http")
async def performance_metrics_middleware(request: Request, call_next):
    """Track performance metrics for all requests"""
    import time

    start_time = time.time()

    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        status_code = 500
        raise
    finally:
        latency_ms = (time.time() - start_time) * 1000

        # Update global metrics
        performance_metrics["requests_total"] += 1
        performance_metrics["latency_sum"] += latency_ms
        performance_metrics["latency_count"] += 1

        # Track per endpoint
        endpoint = request.url.path
        if endpoint not in performance_metrics["requests_per_endpoint"]:
            performance_metrics["requests_per_endpoint"][endpoint] = 0
        performance_metrics["requests_per_endpoint"][endpoint] += 1

        # Track errors
        if status_code >= 400:
            performance_metrics["errors_total"] += 1

    return response

# Include routers
app.include_router(mastery_router, prefix="/api/v1", tags=["Mastery"])
app.include_router(compliance_router, prefix="/api/v1", tags=["GDPR Compliance"])
app.include_router(analytics_router, prefix="/api/v1", tags=["Analytics"])
app.include_router(recommendations_router, prefix="/api/v1", tags=["Recommendations"])

# Performance metrics tracking
performance_metrics = {
    "requests_total": 0,
    "requests_per_endpoint": {},
    "latency_sum": 0.0,
    "latency_count": 0,
    "errors_total": 0,
    "last_reset": datetime.utcnow().isoformat()
}

# Health check endpoints
@app.get("/health", tags=["Monitoring"])
async def health_check():
    """
    Lightweight health check for load balancers

    Returns minimal status for quick health verification.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0",
        "service": "mastery-engine"
    }

@app.get("/ready", tags=["Monitoring"])
async def readiness_check():
    """Full readiness check including dependencies"""
    if not app_state["ready"]:
        return JSONResponse(
            status_code=503,
            content={
                "status": "not_ready",
                "message": "Application starting up or dependencies unavailable",
                "timestamp": datetime.utcnow().isoformat()
            }
        )

    # Use cached health report from startup verification
    health_report = app_state.get("health_report", {})

    # Real-time verification of state store
    state_store_healthy = False
    try:
        if app_state["state_manager"]:
            await app_state["state_manager"].health_check()
            state_store_healthy = True
    except Exception:
        state_store_healthy = False

    # Determine overall status
    all_healthy = state_store_healthy
    status_code = 200 if all_healthy else 503
    status = "ready" if all_healthy else "degraded"

    return JSONResponse(
        status_code=status_code,
        content={
            "status": status,
            "dependencies": {
                "state_store": state_store_healthy,
                "kafka": health_report.get("kafka", False),
                "dapr": health_report.get("dapr", False)
            },
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "environment": os.getenv("ENVIRONMENT", "development")
        }
    )

@app.get("/", tags=["Monitoring"])
async def service_info():
    """Service information and metadata"""
    return {
        "name": "mastery-engine",
        "version": "1.0.0",
        "environment": os.getenv("ENVIRONMENT", "development"),
        "description": "Student learning progress tracking and mastery calculation",
        "endpoints": {
            "health": "/health",
            "ready": "/ready",
            "docs": "/docs",
            "metrics": "/metrics"
        }
    }

@app.get("/metrics", tags=["Monitoring"])
async def metrics():
    """Prometheus-style metrics endpoint"""
    # Calculate average latency if we have requests
    avg_latency = 0.0
    if performance_metrics["latency_count"] > 0:
        avg_latency = performance_metrics["latency_sum"] / performance_metrics["latency_count"]

    return {
        "mastery_engine_info": {
            "version": "1.0.0",
            "environment": os.getenv("ENVIRONMENT", "development")
        },
        "up": 1,
        "performance": {
            "requests_total": performance_metrics["requests_total"],
            "errors_total": performance_metrics["errors_total"],
            "average_latency_ms": round(avg_latency, 3),
            "requests_per_endpoint": performance_metrics["requests_per_endpoint"],
            "uptime_since": performance_metrics["last_reset"]
        },
        "dependencies": {
            "state_store": 1 if app_state.get("state_manager") else 0,
            "kafka": 0,  # Will be enabled in Phase 4
            "dapr": app_state["health_report"].get("dapr", False) if "health_report" in app_state else 0
        }
    }

# Dapr service invocation endpoint
@app.post("/process", tags=["Dapr"])
async def dapr_process(request: Request):
    """Dapr service invocation endpoint"""
    try:
        data = await request.json()
        intent = data.get("intent")
        payload = data.get("payload")
        security_context = data.get("security_context")

        # Validate security context
        if security_context:
            token = security_context.get("token")
            if token:
                try:
                    app_state["security_manager"].validate_jwt(token)
                except Exception as e:
                    return JSONResponse(
                        status_code=401,
                        content={"error": f"Security validation failed: {e}"}
                    )

        # Route by intent
        if intent == "mastery_calculation":
            # Delegate to mastery endpoint logic
            from src.api.endpoints.mastery import calculate_mastery
            return await calculate_mastery(payload)

        elif intent == "get_prediction":
            from src.api.endpoints.analytics import get_prediction
            return await get_prediction(payload)

        elif intent == "generate_path":
            from src.api.endpoints.recommendations import get_learning_path
            return await get_learning_path(payload)

        else:
            return JSONResponse(
                status_code=400,
                content={"error": f"Unknown intent: {intent}"}
            )

    except Exception as e:
        logger.error(f"Dapr processing error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )

# Global error handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": str(exc) if os.getenv("ENVIRONMENT") == "development" else "Something went wrong"
        }
    )

if __name__ == "__main__":
    from tls_config import get_uvicorn_config
    import uvicorn

    config = get_uvicorn_config()

    # Log TLS configuration status
    if TLSConfig.is_production_tls_enabled():
        logger.info("🚀 Starting Mastery Engine with TLS enabled")
    else:
        logger.warning("⚠️  Starting without TLS (development mode)")

    uvicorn.run(
        "src.main:app",
        **config
    )