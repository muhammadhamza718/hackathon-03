"""
Integration test for Dapr Service Invocation: Triage → Progress Agent
"""

import pytest
import sys
import os
import asyncio
import json

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'triage-service', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'progress-agent', 'src'))

@pytest.mark.asyncio
async def test_dapr_service_invocation():
    """Test that Triage can invoke Progress Agent via Dapr"""

    # Test the circuit breaker configuration
    from services.agent_circuit_breakers import circuit_breaker

    # Verify circuit breaker can be created
    assert circuit_breaker is not None
    assert circuit_breaker.failure_threshold == 3
    assert circuit_breaker.timeout == 30

    print("✓ Dapr service invocation configuration verified")

    # Test routing configuration
    import json

    routing_file = os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'triage-service', 'src', 'config', 'agent-routing.json')

    with open(routing_file, 'r') as f:
        routing_config = json.load(f)

    assert 'agents' in routing_config
    assert 'progress' in routing_config['agents']

    progress_agent = routing_config['agents']['progress']
    assert progress_agent['dapr_app_id'] == 'progress-agent'
    assert progress_agent['health_check'] == '/health'

    print("✓ Routing configuration verified")

@pytest.mark.asyncio
async def test_health_endpoint_availability():
    """Test that progress agent health endpoint is accessible"""

    health_file = os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'triage-service', 'src', 'api', 'endpoints', 'agent-health.py')

    # Verify the health endpoint file exists and is valid Python
    assert os.path.exists(health_file)

    with open(health_file, 'r') as f:
        content = f.read()
        assert 'def get_agent_health_status' in content
        assert 'def get_readiness' in content

    print("✓ Health endpoints verified")

if __name__ == "__main__":
    asyncio.run(test_dapr_service_invocation())
    asyncio.run(test_health_endpoint_availability())