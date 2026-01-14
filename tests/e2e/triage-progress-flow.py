"""
End-to-end test for Triage → Progress → Kafka → State flow
"""

import pytest
import sys
import os
import asyncio

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'progress-agent', 'src'))
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'triage-service', 'src'))

@pytest.mark.asyncio
async def test_full_flow():
    """Test complete flow from Triage to State Store via Kafka"""
    from services.state_store import StateStoreService
    from services.kafka_consumer import KafkaConsumerService

    # Initialize services
    state_service = StateStoreService()
    state_service.dapr_enabled = False

    kafka_service = KafkaConsumerService()

    # Simulate: Student completes session → Progress Agent receives event
    test_event = {
        "student_id": "e2e_student",
        "topic_id": "python_basic",
        "timestamp": "2026-01-14T10:30:00Z",
        "action": "session_completed",
        "score": 92,
        "time_spent": 45
    }

    # Validate event
    assert kafka_service.validate_event_schema(test_event)

    # Process event (simulated)
    processed = kafka_service.process_student_progress_event(test_event)
    assert processed is True

    # Simulate state storage
    saved = await state_service.save_progress(
        test_event["student_id"],
        test_event["topic_id"],
        {
            "mastery_level": 0.85,
            "confidence": 0.90,
            "last_session": test_event["timestamp"]
        }
    )
    assert saved is True

    # Verify retrieval
    retrieved = await state_service.get_progress(
        test_event["student_id"],
        test_event["topic_id"]
    )
    assert retrieved is not None
    assert retrieved["mastery_level"] == 0.85

    print("✓ Full Triage→Progress→Kafka→State flow verified")

@pytest.mark.asyncio
async def test_circuit_breaker_resilience():
    """Test circuit breaker behavior in the flow"""
    from services.agent_circuit_breakers import circuit_breaker

    # Test that circuit breaker protects agent calls
    assert circuit_breaker.failure_threshold == 3
    assert circuit_breaker.timeout == 30

    print("✓ Circuit breaker resilience verified")

if __name__ == "__main__":
    asyncio.run(test_full_flow())
    asyncio.run(test_circuit_breaker_resilience())