"""
Test for Kafka event publishing from Progress Agent
"""

import pytest
import sys
import os
import asyncio

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'backend', 'progress-agent', 'src'))

@pytest.mark.asyncio
async def test_kafka_consumer_service():
    """Test Kafka consumer service structure"""
    from services.kafka_consumer import KafkaConsumerService, kafka_consumer

    # Verify service can be instantiated
    service = KafkaConsumerService()
    assert service.kafka_enabled is not None
    assert service.topic == "learning.events"

    # Verify global consumer instance exists
    assert kafka_consumer is not None

    print("✓ Kafka consumer service verified")

@pytest.mark.asyncio
async def test_event_processing():
    """Test event processing logic"""
    from services.kafka_consumer import KafkaConsumerService

    service = KafkaConsumerService()
    service.dapr_enabled = False

    # Test event validation
    valid_event = {
        "student_id": "test_student",
        "topic_id": "python_basic",
        "timestamp": "2026-01-14T10:30:00Z",
        "action": "session_completed",
        "score": 85
    }

    assert service.validate_event_schema(valid_event) is True

    # Test processing
    result = service.process_student_progress_event(valid_event)
    assert result is True

    print("✓ Event processing verified")

if __name__ == "__main__":
    asyncio.run(test_kafka_consumer_service())
    asyncio.run(test_event_processing())