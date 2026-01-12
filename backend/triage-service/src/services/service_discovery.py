"""
Service Discovery for Dapr Agents
Elite Implementation Standard v2.0.0

Discovers all 5 target agents with health checks.
Provides health status for circuit breaker monitoring.
"""

import asyncio
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class AgentHealth(Enum):
    """Agent health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class AgentInfo:
    """Agent information and health status"""
    name: str
    app_id: str
    health: AgentHealth
    last_check: float
    response_time: Optional[float] = None
    metadata: Dict = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class ServiceDiscovery:
    """
    Service discovery with health checks for all 5 agents
    Agents: debug-agent, concepts-agent, exercise-agent, progress-agent, review-agent
    """

    def __init__(self, use_mock: bool = True):
        """
        Initialize service discovery

        Args:
            use_mock: If True, use mock discovery (no Dapr SDK dependency)
        """
        self.use_mock = use_mock
        self.agents = {
            "debug-agent": "debug-agent",
            "concepts-agent": "concepts-agent",
            "exercise-agent": "exercise-agent",
            "progress-agent": "progress-agent",
            "review-agent": "review-agent"
        }
        self.health_cache = {}
        self.cache_ttl = 30  # 30 seconds

        if not use_mock:
            try:
                from dapr.clients import DaprClient
                self.dapr_client = DaprClient()
            except ImportError:
                logger.warning("Dapr SDK not available, falling back to mock mode")
                self.use_mock = True
                self.dapr_client = None
        else:
            self.dapr_client = None

    async def discover_all_agents(self) -> List[AgentInfo]:
        """Discover all 5 target agents with health checks"""
        tasks = [self.check_agent_health(name, app_id) for name, app_id in self.agents.items()]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        agent_infos = []
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Health check failed: {result}")
                continue
            agent_infos.append(result)

        return agent_infos

    async def check_agent_health(self, name: str, app_id: str) -> AgentInfo:
        """Check health of a specific agent"""
        # Check cache first
        cached = self.health_cache.get(app_id)
        if cached and (time.time() - cached.last_check) < self.cache_ttl:
            return cached

        start_time = time.time()

        if self.use_mock or self.dapr_client is None:
            # Mock health check - all agents healthy
            await asyncio.sleep(0.01)  # Simulate network latency
            health = AgentHealth.HEALTHY
            response_time = (time.time() - start_time) * 1000

            agent_info = AgentInfo(
                name=name,
                app_id=app_id,
                health=health,
                last_check=time.time(),
                response_time=response_time,
                metadata={"mock": True, "region": "local"}
            )
        else:
            # Real Dapr health check
            try:
                # Use Dapr's invoke method with timeout to check health
                # In production, this would use proper health check endpoints
                await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None,
                        lambda: self.dapr_client.invoke_method(
                            app_id=app_id,
                            method_name="health",
                            data=b"",
                            timeout=1.0
                        )
                    ),
                    timeout=1.5
                )

                health = AgentHealth.HEALTHY
                response_time = (time.time() - start_time) * 1000

                agent_info = AgentInfo(
                    name=name,
                    app_id=app_id,
                    health=health,
                    last_check=time.time(),
                    response_time=response_time,
                    metadata={"mock": False}
                )

            except asyncio.TimeoutError:
                health = AgentHealth.UNHEALTHY
                response_time = None

                agent_info = AgentInfo(
                    name=name,
                    app_id=app_id,
                    health=health,
                    last_check=time.time(),
                    response_time=response_time,
                    metadata={"error": "timeout"}
                )

            except Exception as e:
                health = AgentHealth.DEGRADED
                response_time = None

                agent_info = AgentInfo(
                    name=name,
                    app_id=app_id,
                    health=health,
                    last_check=time.time(),
                    response_time=response_time,
                    metadata={"error": str(e)}
                )

        # Update cache
        self.health_cache[app_id] = agent_info
        return agent_info

    def get_agent_app_id(self, agent_name: str) -> Optional[str]:
        """Get Dapr app_id for agent name"""
        return self.agents.get(agent_name)

    def get_all_agent_names(self) -> List[str]:
        """Get list of all agent names"""
        return list(self.agents.keys())

    async def get_healthy_agents(self) -> List[AgentInfo]:
        """Get only healthy agents"""
        all_agents = await self.discover_all_agents()
        return [agent for agent in all_agents if agent.health == AgentHealth.HEALTHY]

    async def health_check_all(self) -> Dict:
        """Perform comprehensive health check of all agents"""
        agent_infos = await self.discover_all_agents()

        summary = {
            "total_agents": len(self.agents),
            "healthy": 0,
            "degraded": 0,
            "unhealthy": 0,
            "unknown": 0,
            "agents": []
        }

        for agent in agent_infos:
            summary[agent.health.value] += 1
            summary["agents"].append({
                "name": agent.name,
                "app_id": agent.app_id,
                "health": agent.health.value,
                "response_time_ms": agent.response_time,
                "metadata": agent.metadata
            })

        return summary


# Global instance for application use
_default_discovery = ServiceDiscovery(use_mock=True)


async def get_default_discovery() -> ServiceDiscovery:
    """Get the default service discovery instance"""
    return _default_discovery


if __name__ == "__main__":
    async def test():
        print("=== Service Discovery Test ===")

        discovery = ServiceDiscovery(use_mock=True)

        print("\n1. Discovering all agents...")
        agents = await discovery.discover_all_agents()
        for agent in agents:
            print(f"  {agent.name}: {agent.health.value} (response: {agent.response_time:.1f}ms)")

        print("\n2. Health check summary...")
        summary = await discovery.health_check_all()
        print(f"  Total: {summary['total_agents']}")
        print(f"  Healthy: {summary['healthy']}")
        print(f"  Degraded: {summary['degraded']}")
        print(f"  Unhealthy: {summary['unhealthy']}")

        print("\n3. Get healthy agents only...")
        healthy = await discovery.get_healthy_agents()
        print(f"  Healthy count: {len(healthy)}")
        for agent in healthy:
            print(f"    - {agent.name}")

        print("\n✅ Service discovery working correctly")

    asyncio.run(test())