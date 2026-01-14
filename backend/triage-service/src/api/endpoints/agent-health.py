"""
Agent Health Check Endpoints
Triage Service - Agent Fleet Health Monitoring
"""

from fastapi import APIRouter, HTTPException
import httpx
from typing import Dict, List

router = APIRouter(prefix="/health/agents", tags=["agent-health"])

@router.get("/status")
async def get_agent_health_status() -> Dict[str, Dict]:
    """Get health status for all agents"""
    agents = {
        "progress": "http://progress-agent:8000/health",
        "debug": "http://debug-agent:8001/health",
        "concepts": "http://concepts-agent:8002/health",
        "exercise": "http://exercise-agent:8003/health",
        "review": "http://review-agent:8004/health"
    }

    results = {}
    async with httpx.AsyncClient() as client:
        for name, url in agents.items():
            try:
                response = await client.get(url, timeout=2.0)
                results[name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "code": response.status_code
                }
            except Exception as e:
                results[name] = {
                    "status": "unreachable",
                    "error": str(e)
                }

    return results

@router.get("/ready")
async def get_readiness() -> List[str]:
    """Get list of ready agents"""
    status = await get_agent_health_status()
    return [name for name, data in status.items() if data["status"] == "healthy"]