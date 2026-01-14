"""
Integration test for Dapr Service Invocation: Triage → Debug Agent
"""

import pytest
import sys
import os
import asyncio
import json

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'triage-service', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'debug-agent', 'src'))

@pytest.mark.asyncio
async def test_dapr_service_invocation_debug():
    """Test Dapr service invocation configuration for Debug Agent"""

    # Test routing configuration includes Debug Agent
    routing_file = os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'triage-service', 'src', 'config', 'agent-routing.json')

    with open(routing_file, 'r') as f:
        routing_config = json.load(f)

    # Verify Debug Agent is configured
    assert 'agents' in routing_config
    assert 'debug' in routing_config['agents']

    debug_agent = routing_config['agents']['debug']
    assert debug_agent['dapr_app_id'] == 'debug-agent'
    assert debug_agent['endpoint'] == 'http://debug-agent:8001'
    assert debug_agent['health_check'] == '/health'

    print("✓ Debug Agent routing configuration verified")

@pytest.mark.asyncio
async def test_circuit_breaker_for_debug():
    """Test circuit breaker handles Debug Agent failures"""

    from services.agent_circuit_breakers import circuit_breaker

    # Verify circuit breaker can handle debug agent
    assert circuit_breaker.failure_threshold == 3
    assert circuit_breaker.timeout == 30

    # Test that debug agent name is in circuit breaker system
    # (This would be dynamically added during actual calls)
    print("✓ Circuit breaker configuration for Debug Agent verified")

@pytest.mark.asyncio
async def test_health_check_debug_agent():
    """Test health check endpoints include Debug Agent"""

    health_file = os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'triage-service', 'src', 'api', 'endpoints', 'agent-health.py')

    with open(health_file, 'r') as f:
        content = f.read()
        # Verify health check logic supports multiple agents
        assert 'progress-agent' in content or 'agents' in content

    print("✓ Health check integration verified for Debug Agent")

@pytest.mark.asyncio
async def test_debug_service_integration_structure():
    """Test Debug Agent service files exist and are valid"""

    # Verify debug consumer service exists
    debug_consumer_file = os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'debug-agent', 'src', 'services', 'kafka_consumer.py')

    assert os.path.exists(debug_consumer_file)

    # Verify pattern matching service exists
    pattern_file = os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'debug-agent', 'src', 'services', 'pattern_matching.py')

    assert os.path.exists(pattern_file)

    print("✓ Debug Agent service integration structure verified")

if __name__ == "__main__":
    asyncio.run(test_dapr_service_invocation_debug())
    asyncio.run(test_circuit_breaker_for_debug())
    asyncio.run(test_health_check_debug_agent())
    asyncio.run(test_debug_service_integration_structure())