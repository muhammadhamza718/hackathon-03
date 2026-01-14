"""
Kafka Consumer Service
Exercise Agent - Event Stream Processing
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any

logger = logging.getLogger(__name__)

class ExerciseKafkaConsumer:
    """
    Service for consuming Kafka events related to exercise generation requests
    """

    def __init__(self):
        self.kafka_enabled = os.getenv("KAFKA_ENABLED", "true").lower() == "true"
        self.broker = os.getenv("KAFKA_BROKER", "localhost:9092")
        self.topic = os.getenv("KAFKA_TOPIC", "learning.events")
        self.running = False

    async def start_consuming(self):
        """Start consuming exercise-related events"""
        if not self.kafka_enabled:
            logger.info("Kafka consumer disabled - mock mode for Exercise Agent")
            return

        self.running = True
        logger.info(f"Exercise Agent consuming from {self.topic}")

        while self.running:
            await asyncio.sleep(1)
            logger.debug("Exercise agent consuming events...")

    async def stop_consuming(self):
        """Stop the consumer"""
        self.running = False

    def process_exercise_request(self, event_data: Dict[str, Any]):
        """
        Process exercise generation request from Kafka
        """
        try:
            student_id = event_data.get("student_id")
            topic = event_data.get("topic")
            difficulty = event_data.get("difficulty", "auto")
            student_level = event_data.get("level", "beginner")

            logger.info(f"Processing exercise request: {student_id} - {topic}")

            # Generate exercise (simulated)
            from .problem_generator import generate_problem_with_mcp

            # For Kafka events, auto-calibrate difficulty if not specified
            if difficulty == "auto":
                from .difficulty_calibration import calibrate_difficulty_with_mcp
                # Use student level to estimate mastery
                mastery_map = {"beginner": 0.3, "intermediate": 0.6, "advanced": 0.8}
                mastery = mastery_map.get(student_level, 0.5)
                difficulty = asyncio.run(calibrate_difficulty_with_mcp(mastery, mastery))

            problem = asyncio.run(generate_problem_with_mcp(
                topic=topic,
                difficulty=difficulty,
                student_progress={"student_level": student_level, "student_id": student_id}
            ))

            return {
                "student_id": student_id,
                "topic": topic,
                "difficulty": difficulty,
                "problem": problem,
                "processed_at": "2026-01-14T10:30:00Z"
            }

        except Exception as e:
            logger.error(f"Failed to process exercise request: {e}")
            return None

    def process_calibration_request(self, event_data: Dict[str, Any]):
        """
        Process difficulty calibration request from Kafka
        """
        try:
            student_id = event_data.get("student_id")
            concept = event_data.get("concept")
            performance_data = event_data.get("performance_data", {})

            logger.info(f"Processing calibration request: {student_id} - {concept}")

            # Generate calibration
            from .difficulty_calibration import calibrate_difficulty_with_mcp

            mastery = performance_data.get("mastery", 0.5)
            success_rate = performance_data.get("success_rate", 0.6)

            difficulty = asyncio.run(calibrate_difficulty_with_mcp(mastery, success_rate))

            return {
                "student_id": student_id,
                "concept": concept,
                "recommended_difficulty": difficulty,
                "mastery": mastery,
                "success_rate": success_rate,
                "processed_at": "2026-01-14T10:30:00Z"
            }

        except Exception as e:
            logger.error(f"Failed to process calibration request: {e}")
            return None

    def validate_event_schema(self, event_data: Dict[str, Any]) -> bool:
        """
        Validate event against expected schema for exercise events
        """
        required_fields = ["student_id", "timestamp", "topic"]  # For exercise requests
        alt_required_fields = ["student_id", "timestamp", "concept"]  # For calibration requests

        has_exercise_fields = all(field in event_data for field in required_fields)
        has_calibration_fields = all(field in event_data for field in alt_required_fields)

        return has_exercise_fields or has_calibration_fields

    def process_exercise_solution_submitted(self, event_data: Dict[str, Any]):
        """
        Process event when student submits a solution
        """
        try:
            student_id = event_data.get("student_id")
            topic = event_data.get("topic")
            correctness = event_data.get("correctness", False)
            time_taken = event_data.get("time_taken", 0)
            attempts = event_data.get("attempts", 1)

            logger.info(f"Solution submitted: {student_id} - {topic} - Correct: {correctness}")

            # Update student profile based on performance
            # This would typically update a state store
            performance_update = {
                "student_id": student_id,
                "topic": topic,
                "performance_update": {
                    "success": correctness,
                    "time_taken": time_taken,
                    "attempts": attempts,
                    "timestamp": "2026-01-14T10:30:00Z"
                }
            }

            # Emit updated student progress event (would go to Kafka)
            logger.info(f"Would emit progress update: {json.dumps(performance_update, indent=2)}")

            return performance_update

        except Exception as e:
            logger.error(f"Failed to process solution submission: {e}")
            return None

# Global consumer instance
exercise_consumer = ExerciseKafkaConsumer()