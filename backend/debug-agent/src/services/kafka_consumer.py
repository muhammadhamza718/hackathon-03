"""
Kafka Consumer Service
Debug Agent - Event Stream Processing for Errors
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any

logger = logging.getLogger(__name__)

class DebugKafkaConsumer:
    """
    Service for consuming Kafka events related to debugging and errors
    """

    def __init__(self):
        self.kafka_enabled = os.getenv("KAFKA_ENABLED", "true").lower() == "true"
        self.broker = os.getenv("KAFKA_BROKER", "localhost:9092")
        self.topic = os.getenv("KAFKA_TOPIC", "learning.events")
        self.running = False

    async def start_consuming(self):
        """Start consuming error-related events"""
        if not self.kafka_enabled:
            logger.info("Kafka consumer disabled - mock mode for Debug Agent")
            return

        self.running = True
        logger.info(f"Debug Agent consuming from {self.topic}")

        while self.running:
            await asyncio.sleep(1)
            logger.debug("Debug agent consuming events...")

    async def stop_consuming(self):
        """Stop the consumer"""
        self.running = False

    def process_debug_event(self, event_data: Dict[str, Any]):
        """
        Process error/debug event from Kafka
        """
        try:
            student_id = event_data.get("student_id")
            error_type = event_data.get("error_type")
            code_snippet = event_data.get("code_snippet")

            logger.info(f"Processing debug event: {student_id} - {error_type}")

            # Analyze the error
            from .pattern_matching import pattern_matcher

            pattern = pattern_matcher.detect_pattern(
                error_type,
                event_data.get("stack_trace", "")
            )

            if pattern:
                pattern_name, pattern_data = pattern
                suggestions = pattern_matcher.get_suggestions(pattern_data["pattern_id"])

                return {
                    "student_id": student_id,
                    "pattern_detected": pattern_name,
                    "pattern_id": pattern_data["pattern_id"],
                    "suggestions": suggestions,
                    "processed_at": "2026-01-14T10:30:00Z"
                }

            return {
                "student_id": student_id,
                "pattern_detected": "unknown",
                "suggestions": ["Review error message carefully"]
            }

        except Exception as e:
            logger.error(f"Failed to process debug event: {e}")
            return None

    def validate_event_schema(self, event_data: Dict[str, Any]) -> bool:
        """
        Validate event against expected schema for debug events
        """
        required_fields = ["student_id", "timestamp", "error_type"]
        return all(field in event_data for field in required_fields)

# Global consumer instance
debug_consumer = DebugKafkaConsumer()