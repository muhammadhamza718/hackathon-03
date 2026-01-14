"""
Kafka Consumer Service
Concepts Agent - Event Stream Processing
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ConceptKafkaConsumer:
    """
    Service for consuming Kafka events related to concept learning requests
    """

    def __init__(self):
        self.kafka_enabled = os.getenv("KAFKA_ENABLED", "true").lower() == "true"
        self.broker = os.getenv("KAFKA_BROKER", "localhost:9092")
        self.topic = os.getenv("KAFKA_TOPIC", "learning.events")
        self.running = False

    async def start_consuming(self):
        """Start consuming concept-related events"""
        if not self.kafka_enabled:
            logger.info("Kafka consumer disabled - mock mode for Concepts Agent")
            return

        self.running = True
        logger.info(f"Concepts Agent consuming from {self.topic}")

        while self.running:
            await asyncio.sleep(1)
            logger.debug("Concepts agent consuming events...")

    async def stop_consuming(self):
        """Stop the consumer"""
        self.running = False

    def process_concept_request(self, event_data: Dict[str, Any]):
        """
        Process concept explanation request from Kafka
        """
        try:
            student_id = event_data.get("student_id")
            concept = event_data.get("concept")
            level = event_data.get("level", "beginner")

            logger.info(f"Processing concept request: {student_id} - {concept}")

            # Generate explanation (simulated)
            from .explanation_generator import generate_explanation_with_mcp

            explanation = generate_explanation_with_mcp(
                concept=concept,
                level=level,
                context={},
                style="simple"
            )

            return {
                "student_id": student_id,
                "concept": concept,
                "explanation": explanation,
                "processed_at": "2026-01-14T10:30:00Z"
            }

        except Exception as e:
            logger.error(f"Failed to process concept request: {e}")
            return None

    def process_concept_mapping_request(self, event_data: Dict[str, Any]):
        """
        Process concept mapping request from Kafka
        """
        try:
            student_id = event_data.get("student_id")
            target_concept = event_data.get("concept")

            logger.info(f"Processing mapping request: {student_id} - {target_concept}")

            # Get learning path
            from .concept_mapping import concept_mapper

            learning_path = concept_mapper.get_learning_path(target_concept)
            related = concept_mapper.get_related_concepts(target_concept)

            return {
                "student_id": student_id,
                "target_concept": target_concept,
                "learning_path": learning_path,
                "related_concepts": related,
                "processed_at": "2026-01-14T10:30:00Z"
            }

        except Exception as e:
            logger.error(f"Failed to process mapping request: {e}")
            return None

    def validate_event_schema(self, event_data: Dict[str, Any]) -> bool:
        """
        Validate event against expected schema for concept events
        """
        required_fields = ["student_id", "timestamp", "concept"]
        return all(field in event_data for field in required_fields)

# Global consumer instance
concept_consumer = ConceptKafkaConsumer()