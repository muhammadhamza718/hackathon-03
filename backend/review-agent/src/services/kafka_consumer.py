"""
Kafka Consumer Service
Review Agent - Event Stream Processing
Elite Implementation Standard v2.0.0
"""

import os
import json
import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ReviewKafkaConsumer:
    """
    Service for consuming Kafka events related to code review requests
    Processes events from Triage Service for comprehensive feedback generation
    """

    def __init__(self):
        self.kafka_enabled = os.getenv("KAFKA_ENABLED", "true").lower() == "true"
        self.broker = os.getenv("KAFKA_BROKER", "localhost:9092")
        self.topic = os.getenv("KAFKA_TOPIC", "review.requests")
        self.consumer_group = os.getenv("KAFKA_CONSUMER_GROUP", "review-agent-group")
        self.running = False

    async def start_consuming(self):
        """
        Start consuming review-related events from Kafka
        In production, this would connect to actual Kafka broker
        """
        if not self.kafka_enabled:
            logger.info("Kafka consumer disabled - mock mode for Review Agent")
            return

        self.running = True
        logger.info(f"Review Agent consuming from {self.topic} (group: {self.consumer_group})")

        # Simulate Kafka consumer loop
        while self.running:
            # In production: await consumer.getone() or similar
            await asyncio.sleep(5)  # Poll interval
            logger.debug("Review agent waiting for events...")

    async def stop_consuming(self):
        """Stop the consumer gracefully"""
        self.running = False
        logger.info("Review Agent Kafka consumer stopped")

    def process_code_review_request(self, event_data: Dict[str, Any]):
        """
        Process code review request from Kafka event

        Event structure expected:
        {
            "student_id": "user123",
            "timestamp": "2026-01-14T10:30:00Z",
            "intent": "quality_assessment",  # or "hint_generation", "detailed_feedback"
            "student_code": "def func():...",
            "problem_context": {"topic": "loops", "difficulty": "medium"},
            "error_type": "off_by_one",
            "language": "python"
        }
        """
        try:
            student_id = event_data.get("student_id")
            intent = event_data.get("intent", "detailed_feedback")
            student_code = event_data.get("student_code")
            problem_context = event_data.get("problem_context", {})
            error_type = event_data.get("error_type", "general")
            language = event_data.get("language", "python")

            if not student_code:
                logger.warning(f"No student code provided in event from {student_id}")
                return None

            logger.info(f"Processing review request: {student_id} - {intent}")

            # Route based on intent
            if intent == "quality_assessment":
                result = self._handle_quality_assessment(student_code, problem_context, student_id, language)
            elif intent == "hint_generation":
                result = self._handle_hint_generation(student_code, problem_context, error_type, student_id, language)
            elif intent == "detailed_feedback":
                result = self._handle_detailed_feedback(student_code, problem_context, error_type, student_id, language)
            else:
                logger.warning(f"Unknown intent: {intent}")
                return None

            # Enrich result with event metadata
            if result:
                result.update({
                    "processed_via": "kafka",
                    "original_event": event_data,
                    "processed_at": datetime.utcnow().isoformat()
                })

            return result

        except Exception as e:
            logger.error(f"Failed to process review request: {e}")
            return {
                "status": "error",
                "error": str(e),
                "processed_via": "kafka",
                "original_event": event_data,
                "processed_at": datetime.utcnow().isoformat()
            }

    def _handle_quality_assessment(self, student_code: str, context: Dict[str, Any], student_id: str, language: str):
        """Handle quality assessment intent via Kafka"""
        try:
            from .quality_scoring import assess_code_quality_with_mcp

            assessment = asyncio.run(assess_code_quality_with_mcp(
                student_code=student_code,
                context=context,
                student_id=student_id,
                language=language
            ))

            return {
                "status": "success",
                "agent": "review-agent",
                "result": {
                    "intent": "quality_assessment",
                    "quality_score": assessment["score"],
                    "factors": assessment["factors"],
                    "recommendations": assessment.get("recommendations", []),
                    "student_id": student_id
                }
            }

        except Exception as e:
            logger.error(f"Quality assessment failed: {e}")
            return None

    def _handle_hint_generation(self, student_code: str, context: Dict[str, Any], error_type: str, student_id: str, language: str):
        """Handle hint generation intent via Kafka"""
        try:
            from .hint_generator import generate_hint_with_mcp

            hint = asyncio.run(generate_hint_with_mcp(
                student_code=student_code,
                problem_context=context,
                error_type=error_type,
                student_id=student_id,
                language=language,
                hint_level="medium",
                previous_hints=0
            ))

            return {
                "status": "success",
                "agent": "review-agent",
                "result": {
                    "intent": "hint_generation",
                    "hint": hint["text"],
                    "level": hint["level"],
                    "estimated_time": hint.get("estimated_time"),
                    "student_id": student_id
                }
            }

        except Exception as e:
            logger.error(f"Hint generation failed: {e}")
            return None

    def _handle_detailed_feedback(self, student_code: str, context: Dict[str, Any], error_type: str, student_id: str, language: str):
        """Handle detailed feedback intent via Kafka"""
        try:
            from .quality_scoring import assess_code_quality_with_mcp
            from .hint_generator import generate_hint_with_mcp

            assessment = asyncio.run(assess_code_quality_with_mcp(
                student_code=student_code,
                context=context,
                student_id=student_id,
                language=language
            ))

            hint = asyncio.run(generate_hint_with_mcp(
                student_code=student_code,
                problem_context=context,
                error_type=error_type,
                student_id=student_id,
                language=language,
                hint_level="medium",
                previous_hints=0
            ))

            return {
                "status": "success",
                "agent": "review-agent",
                "result": {
                    "intent": "detailed_feedback",
                    "quality_score": assessment["score"],
                    "feedback": {
                        "strengths": assessment.get("strengths", []),
                        "improvements": assessment.get("improvements", []),
                        "hint": hint["text"],
                        "next_steps": hint.get("next_steps", [])
                    },
                    "student_id": student_id
                }
            }

        except Exception as e:
            logger.error(f"Detailed feedback failed: {e}")
            return None

    def process_performance_update(self, event_data: Dict[str, Any]):
        """
        Process student performance updates for adaptive learning
        Stores performance data for future hint customization
        """
        try:
            student_id = event_data.get("student_id")
            topic = event_data.get("topic")
            correctness = event_data.get("correctness", False)
            time_taken = event_data.get("time_taken", 0)
            attempts = event_data.get("attempts", 1)
            code_quality = event_data.get("quality_score", 0.0)

            logger.info(f"Performance update: {student_id} - {topic} - Quality: {code_quality}")

            # In production, this would update a state store or database
            # For now, log the performance data for adaptive learning
            performance_record = {
                "student_id": student_id,
                "topic": topic,
                "performance": {
                    "correctness": correctness,
                    "time_taken": time_taken,
                    "attempts": attempts,
                    "quality_score": code_quality,
                    "timestamp": datetime.utcnow().isoformat()
                }
            }

            # Store for future hint customization (in production: Redis/Database)
            logger.info(f"Performance record: {json.dumps(performance_record, indent=2)}")

            return performance_record

        except Exception as e:
            logger.error(f"Failed to process performance update: {e}")
            return None

    def process_feedback_response(self, event_data: Dict[str, Any]):
        """
        Process feedback response events from other agents
        Useful for coordinating with Triage Service
        """
        try:
            student_id = event_data.get("student_id")
            request_id = event_data.get("request_id")
            feedback = event_data.get("feedback")

            logger.info(f"Feedback response received: {student_id} - {request_id}")

            # Log for coordination purposes
            logger.info(f"Feedback summary: {feedback.get('summary', 'N/A')}")

            return {
                "status": "acknowledged",
                "request_id": request_id,
                "student_id": student_id,
                "processed_at": datetime.utcnow().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to process feedback response: {e}")
            return None

    def validate_event_schema(self, event_data: Dict[str, Any]) -> tuple[bool, Optional[str]]:
        """
        Validate event against expected schema for review events

        Returns: (is_valid, error_message)
        """
        # Common required fields for all review events
        common_required = ["student_id", "timestamp", "intent"]

        # Check common fields
        for field in common_required:
            if field not in event_data:
                return False, f"Missing required field: {field}"

        # Intent-specific validation
        intent = event_data.get("intent")
        required_by_intent = {
            "quality_assessment": ["student_code"],
            "hint_generation": ["student_code", "error_type"],
            "detailed_feedback": ["student_code", "error_type"],
            "performance_update": ["topic", "correctness"],
            "feedback_response": ["request_id", "feedback"]
        }

        required_fields = required_by_intent.get(intent, [])
        for field in required_fields:
            if field not in event_data:
                return False, f"Intent '{intent}' requires field: {field}"

        # Validate student_code length if present
        if "student_code" in event_data:
            code = event_data["student_code"]
            if not code or len(code.strip()) == 0:
                return False, "Student code cannot be empty"
            if len(code) > 50000:
                return False, "Student code exceeds 50,000 characters"

        return True, None

    def get_consumer_stats(self) -> Dict[str, Any]:
        """
        Get consumer statistics and health metrics
        """
        return {
            "kafka_enabled": self.kafka_enabled,
            "broker": self.broker,
            "topic": self.topic,
            "consumer_group": self.consumer_group,
            "running": self.running,
            "status": "healthy" if self.kafka_enabled and self.running else "inactive"
        }

    async def mock_event_loop(self):
        """
        Mock event processing loop for development/testing
        Simulates receiving events from Kafka
        """
        mock_events = [
            {
                "student_id": "student_001",
                "timestamp": datetime.utcnow().isoformat(),
                "intent": "quality_assessment",
                "student_code": "def sum(a, b):\n    return a + b",
                "problem_context": {"topic": "functions", "difficulty": "easy"},
                "language": "python"
            },
            {
                "student_id": "student_002",
                "timestamp": datetime.utcnow().isoformat(),
                "intent": "hint_generation",
                "student_code": "for i in range(10):\n    print(i)",
                "error_type": "logic",
                "problem_context": {"topic": "loops"},
                "language": "python"
            }
        ]

        for event in mock_events:
            if self.running:
                logger.info(f"Mock event received: {event['intent']}")
                result = self.process_code_review_request(event)
                if result:
                    logger.info(f"Mock processing result: {result['status']}")
                await asyncio.sleep(2)


# Global consumer instance
review_consumer = ReviewKafkaConsumer()