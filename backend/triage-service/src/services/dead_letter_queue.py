"""
Dead Letter Queue for Failed Routing Events
Elite Implementation Standard v2.0.0

Failed routing events published to Kafka DLQ for analysis and replay.
"""

import json
import time
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class DLQEvent:
    """Dead letter queue event structure"""
    timestamp: str
    original_request: Dict
    routing_decision: Dict
    failure_reason: str
    failure_stage: str  # classification, routing, dapr_invocation
    error_details: Optional[Dict] = None
    retry_count: int = 0
    metadata: Dict = None

    def to_json(self) -> str:
        return json.dumps(self.__dict__, indent=2)


class DeadLetterQueue:
    """
    Kafka DLQ implementation for failed triage events
    Topic: learning.events.dlq.triage-service
    """

    def __init__(self, use_mock: bool = True):
        self.use_mock = use_mock
        self.events = []  # Mock storage

        if not use_mock:
            try:
                from kafka import KafkaProducer
                self.producer = KafkaProducer(
                    bootstrap_servers=['localhost:9092'],
                    value_serializer=lambda v: json.dumps(v).encode('utf-8')
                )
            except ImportError:
                print("Kafka library not available, using mock mode")
                self.use_mock = True
                self.producer = None
        else:
            self.producer = None

    async def publish_failure(
        self,
        original_request: Dict,
        routing_decision: Dict,
        failure_reason: str,
        failure_stage: str,
        error_details: Optional[Dict] = None
    ) -> Dict:
        """
        Publish a failed routing event to DLQ

        Args:
            original_request: The original triage request
            routing_decision: The routing decision that was attempted
            failure_reason: Why the operation failed
            failure_stage: Where in pipeline it failed
            error_details: Additional error information

        Returns:
            DLQ event metadata
        """
        event = DLQEvent(
            timestamp=datetime.utcnow().isoformat(),
            original_request=original_request,
            routing_decision=routing_decision,
            failure_reason=failure_reason,
            failure_stage=failure_stage,
            error_details=error_details,
            retry_count=0
        )

        if self.use_mock or self.producer is None:
            # Mock mode - store in memory
            self.events.append(event)
            print(f"DLQ [MOCK]: {event.to_json()}")
            result = {
                "status": "published",
                "topic": "learning.events.dlq.triage-service",
                "partition": 0,
                "offset": len(self.events) - 1,
                "event_id": f"dlq-{int(time.time())}"
            }
        else:
            # Real Kafka publishing
            try:
                future = self.producer.send(
                    'learning.events.dlq.triage-service',
                    value=event.__dict__
                )
                record_metadata = future.get(timeout=10)
                result = {
                    "status": "published",
                    "topic": record_metadata.topic,
                    "partition": record_metadata.partition,
                    "offset": record_metadata.offset,
                    "event_id": f"dlq-{record_metadata.offset}"
                }
            except Exception as e:
                result = {
                    "status": "failed",
                    "error": str(e)
                }

        return result

    def get_event_count(self) -> int:
        """Get count of events in DLQ"""
        return len(self.events)

    def get_events(self, limit: int = 100) -> list:
        """Get events from DLQ (mock mode)"""
        return self.events[-limit:] if limit < len(self.events) else self.events

    def clear(self):
        """Clear all events (for testing)"""
        self.events.clear()


# Global instance
_default_dlq = DeadLetterQueue(use_mock=True)


async def publish_to_dlq(
    original_request: Dict,
    routing_decision: Dict,
    failure_reason: str,
    failure_stage: str,
    error_details: Optional[Dict] = None
) -> Dict:
    """Convenience function to publish to default DLQ"""
    return await _default_dlq.publish_failure(
        original_request, routing_decision, failure_reason, failure_stage, error_details
    )


if __name__ == "__main__":
    import asyncio

    async def test():
        print("=== Dead Letter Queue Test ===")

        dlq = DeadLetterQueue(use_mock=True)

        # Test publishing a failure
        test_request = {
            "query": "help with my code",
            "student_id": "student-123"
        }

        test_routing = {
            "target_agent": "debug-agent",
            "intent": "syntax_help",
            "confidence": 0.85
        }

        result = await dlq.publish_failure(
            original_request=test_request,
            routing_decision=test_routing,
            failure_reason="Circuit breaker open",
            failure_stage="dapr_invocation",
            error_details={"circuit_state": "OPEN", "last_failure": "timeout"}
        )

        print(f"DLQ Result: {result}")
        print(f"Total events: {dlq.get_event_count()}")

        # Show event details
        events = dlq.get_events()
        for event in events:
            print(f"\nEvent: {event.failure_reason} (stage: {event.failure_stage})")

    asyncio.run(test())