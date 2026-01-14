"""
Agent Circuit Breaker Configuration
Triage Service - Agent Fleet Resilience
"""

import httpx
from asyncio import Lock
from datetime import datetime, timedelta
from typing import Dict, Optional

class AgentCircuitBreaker:
    def __init__(self, failure_threshold: int = 3, timeout: int = 30):
        self.failure_threshold = failure_threshold
        self.timeout = timeout
        self.failure_count: Dict[str, int] = {}
        self.last_failure: Dict[str, datetime] = {}
        self.state: Dict[str, str] = {}  # "closed", "open", "half-open"
        self.locks: Dict[str, Lock] = {}

    async def call_agent(self, agent_name: str, url: str, method: str = "GET") -> Optional[httpx.Response]:
        """Make a call to agent with circuit breaker protection"""

        if agent_name not in self.locks:
            self.locks[agent_name] = Lock()

        async with self.locks[agent_name]:
            current_state = self.state.get(agent_name, "closed")

            if current_state == "open":
                if datetime.now() - self.last_failure.get(agent_name, datetime.min) > timedelta(seconds=self.timeout):
                    # Transition to half-open
                    self.state[agent_name] = "half-open"
                else:
                    raise Exception(f"Circuit breaker for {agent_name} is OPEN")

        # Make the actual call
        async with httpx.AsyncClient() as client:
            try:
                response = await client.request(method, url, timeout=5.0)

                if response.status_code >= 500:
                    await self._record_failure(agent_name)
                    return None

                # Success - reset failure count
                await self._reset_failure_count(agent_name)
                return response

            except Exception:
                await self._record_failure(agent_name)
                return None

    async def _record_failure(self, agent_name: str):
        """Record a failure and potentially open the circuit"""
        async with self.locks.get(agent_name, Lock()):
            self.failure_count[agent_name] = self.failure_count.get(agent_name, 0) + 1
            self.last_failure[agent_name] = datetime.now()

            if self.failure_count[agent_name] >= self.failure_threshold:
                self.state[agent_name] = "open"

    async def _reset_failure_count(self, agent_name: str):
        """Reset failure count on successful call"""
        async with self.locks.get(agent_name, Lock()):
            self.failure_count[agent_name] = 0
            self.state[agent_name] = "closed"

# Global circuit breaker instance
circuit_breaker = AgentCircuitBreaker(failure_threshold=3, timeout=30)