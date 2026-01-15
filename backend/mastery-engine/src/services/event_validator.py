"""
Event Validation Service
========================

Validates learning events against schemas and business rules.
Handles both structure validation and semantic validation.
"""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta

from src.models.events import (
    LearningEvent, EventType, ExerciseCompletedEvent, QuizCompletedEvent,
    LessonViewedEvent, ContentRatedEvent, MilestoneReachedEvent,
    EventValidationResult
)
from src.models.mastery import ComponentScores

logger = logging.getLogger(__name__)


class EventValidationService:
    """
    Validates learning events for structure, business rules, and sanity
    """

    def __init__(self):
        self.min_timestamp = datetime.utcnow() - timedelta(days=90)
        self.max_timestamp = datetime.utcnow() + timedelta(hours=1)

    def validate_event_structure(self, event_data: Dict[str, any]) -> EventValidationResult:
        """
        Validate basic event structure and required fields
        """
        errors = []
        warnings = []

        # Check required fields
        required_fields = ["event_id", "event_type", "student_id", "timestamp"]
        for field in required_fields:
            if field not in event_data:
                errors.append(f"Missing required field: {field}")

        if errors:
            return EventValidationResult(valid=False, errors=errors, warnings=warnings)

        # Validate event_id format
        event_id = event_data["event_id"]
        if not isinstance(event_id, str) or len(event_id) < 8:
            errors.append("event_id must be a valid UUID string")

        # Validate event_type
        try:
            event_type = EventType(event_data["event_type"])
        except ValueError:
            valid_types = [e.value for e in EventType]
            errors.append(f"Invalid event_type. Must be one of: {valid_types}")

        # Validate student_id
        student_id = event_data["student_id"]
        if not isinstance(student_id, str) or not student_id.strip():
            errors.append("student_id must be a non-empty string")

        # Validate timestamp
        try:
            if isinstance(event_data["timestamp"], str):
                timestamp = datetime.fromisoformat(event_data["timestamp"].replace('Z', '+00:00'))
            else:
                timestamp = event_data["timestamp"]

            if timestamp < self.min_timestamp:
                errors.append(f"Timestamp too old: {timestamp}")
            elif timestamp > self.max_timestamp:
                errors.append(f"Timestamp in the future: {timestamp}")
        except (ValueError, TypeError):
            errors.append("Invalid timestamp format")

        # Validate data field
        if "data" not in event_data:
            warnings.append("Missing data field")
        elif not isinstance(event_data["data"], dict):
            errors.append("data field must be a dictionary")

        valid = len(errors) == 0
        return EventValidationResult(valid=valid, errors=errors, warnings=warnings)

    def validate_event_business_rules(self, event_data: Dict[str, any]) -> EventValidationResult:
        """
        Validate event-specific business rules and data constraints
        """
        errors = []
        warnings = []

        try:
            event_type = EventType(event_data["event_type"])
            data = event_data.get("data", {})

            # Route to specific validator
            if event_type == EventType.EXERCISE_COMPLETED:
                self._validate_exercise_completed(data, errors, warnings)
            elif event_type == EventType.QUIZ_COMPLETED:
                self._validate_quiz_completed(data, errors, warnings)
            elif event_type == EventType.LESSON_VIEWED:
                self._validate_lesson_viewed(data, errors, warnings)
            elif event_type == EventType.CONTENT_RATED:
                self._validate_content_rated(data, errors, warnings)
            elif event_type == EventType.MILESTONE_REACHED:
                self._validate_milestone_reached(data, errors, warnings)

        except Exception as e:
            errors.append(f"Business rule validation error: {str(e)}")

        valid = len(errors) == 0
        return EventValidationResult(valid=valid, errors=errors, warnings=warnings)

    def _validate_exercise_completed(self, data: Dict, errors: List, warnings: List):
        """Validate exercise completed event data"""
        required = ["exercise_id", "difficulty", "time_spent_seconds", "completion_rate", "correctness"]
        for field in required:
            if field not in data:
                errors.append(f"Exercise event missing: {field}")

        if "difficulty" in data and data["difficulty"] not in ["easy", "medium", "hard", "expert"]:
            errors.append("difficulty must be: easy/medium/hard/expert")

        if "completion_rate" in data:
            if not 0.0 <= data["completion_rate"] <= 1.0:
                errors.append("completion_rate must be between 0.0 and 1.0")

        if "correctness" in data:
            if not 0.0 <= data["correctness"] <= 1.0:
                errors.append("correctness must be between 0.0 and 1.0")

        if "time_spent_seconds" in data:
            if data["time_spent_seconds"] < 0:
                errors.append("time_spent_seconds cannot be negative")
            if data["time_spent_seconds"] > 3600 * 24:  # 24 hours
                warnings.append("time_spent_seconds unusually high")

    def _validate_quiz_completed(self, data: Dict, errors: List, warnings: List):
        """Validate quiz completed event data"""
        required = ["quiz_id", "score", "questions_total", "questions_correct", "time_spent_seconds"]
        for field in required:
            if field not in data:
                errors.append(f"Quiz event missing: {field}")

        if "score" in data and not 0.0 <= data["score"] <= 1.0:
            errors.append("score must be between 0.0 and 1.0")

        if "questions_total" in data and "questions_correct" in data:
            if data["questions_correct"] > data["questions_total"]:
                errors.append("questions_correct cannot exceed questions_total")
            if data["questions_correct"] < 0 or data["questions_total"] < 0:
                errors.append("question counts cannot be negative")

        if "time_spent_seconds" in data:
            if data["time_spent_seconds"] < 0:
                errors.append("time_spent_seconds cannot be negative")

    def _validate_lesson_viewed(self, data: Dict, errors: List, warnings: List):
        """Validate lesson viewed event data"""
        required = ["lesson_id", "duration_seconds", "completion_percentage"]
        for field in required:
            if field not in data:
                errors.append(f"Lesson event missing: {field}")

        if "completion_percentage" in data:
            if not 0.0 <= data["completion_percentage"] <= 100.0:
                errors.append("completion_percentage must be between 0.0 and 100.0")

        if "duration_seconds" in data and data["duration_seconds"] < 0:
            errors.append("duration_seconds cannot be negative")

    def _validate_content_rated(self, data: Dict, errors: List, warnings: List):
        """Validate content rated event data"""
        required = ["content_id", "content_type", "rating"]
        for field in required:
            if field not in data:
                errors.append(f"Content rated event missing: {field}")

        if "rating" in data:
            if not 1 <= data["rating"] <= 5:
                errors.append("rating must be between 1 and 5")

        if "content_type" in data:
            valid_types = ["exercise", "lesson", "quiz", "article"]
            if data["content_type"] not in valid_types:
                errors.append(f"content_type must be one of: {valid_types}")

        if "comment" in data:
            comment = data["comment"]
            if comment and len(comment) > 1000:
                warnings.append("Comment exceeds 1000 characters")

    def _validate_milestone_reached(self, data: Dict, errors: List, warnings: List):
        """Validate milestone reached event data"""
        required = ["milestone_type", "milestone_value", "message"]
        for field in required:
            if field not in data:
                errors.append(f"Milestone event missing: {field}")

        if "milestone_value" in data and data["milestone_value"] < 0:
            errors.append("milestone_value cannot be negative")

        if "milestone_type" in data:
            valid_types = ["streak", "consecutive_days", "total_exercises", "total_quizzes", "mastery_level"]
            if data["milestone_type"] not in valid_types:
                warnings.append(f"Unknown milestone_type: {data['milestone_type']}")

    def validate_against_mastery_state(self, event_data: Dict, current_mastery: Optional[Dict]) -> EventValidationResult:
        """
        Validate event against current student mastery state for consistency
        """
        warnings = []

        if not current_mastery:
            # First event for student, no baseline
            return EventValidationResult(valid=True, warnings=warnings)

        event_type = event_data["event_type"]

        # Check for suspicious patterns
        if event_type == "exercise.completed":
            completion_rate = event_data.get("data", {}).get("completion_rate", 0)
            correctness = event_data.get("data", {}).get("correctness", 0)

            # High completion but low correctness might indicate gaming
            if completion_rate > 0.9 and correctness < 0.3:
                warnings.append("Suspicious pattern: high completion but low correctness")

        elif event_type == "quiz.completed":
            score = event_data.get("data", {}).get("score", 0)
            if score < 0.1:
                warnings.append("Very low quiz score, possible outlier")

        return EventValidationResult(valid=True, warnings=warnings)

    def validate_batch_consistency(self, events: List[Dict]) -> Tuple[bool, List[str]]:
        """
        Validate a batch of events for consistency
        """
        errors = []
        event_ids = set()

        for event_data in events:
            # Check for duplicate event_ids in batch
            event_id = event_data.get("event_id")
            if event_id in event_ids:
                errors.append(f"Duplicate event_id in batch: {event_id}")
            event_ids.add(event_id)

            # Check timestamp ordering
            if "timestamp" in event_data:
                try:
                    if isinstance(event_data["timestamp"], str):
                        timestamp = datetime.fromisoformat(event_data["timestamp"].replace('Z', '+00:00'))
                    else:
                        timestamp = event_data["timestamp"]

                    # First event in batch
                    if events.index(event_data) == 0:
                        first_timestamp = timestamp
                    else:
                        if timestamp < first_timestamp:
                            errors.append(f"Event {event_id} has timestamp before first event")
                except:
                    pass

        return len(errors) == 0, errors

    def get_event_complexity_score(self, event_data: Dict) -> float:
        """
        Calculate a complexity score for event (higher = more complex)
        Used for monitoring and alerting
        """
        score = 1.0

        event_type = event_data.get("event_type")
        data = event_data.get("data", {})

        # Type complexity
        complexity_map = {
            "lesson.viewed": 0.5,
            "content.rated": 0.7,
            "exercise.completed": 1.0,
            "quiz.completed": 1.2,
            "milestone.reached": 1.5
        }
        score *= complexity_map.get(event_type, 1.0)

        # Data complexity
        if "topic_ids" in data and len(data.get("topic_ids", [])) > 3:
            score += 0.3

        if data.get("hints_used", 0) > 5:
            score += 0.2

        if data.get("retries", 0) > 3:
            score += 0.2

        return min(score, 3.0)  # Cap at 3.0

    def sanitize_event_data(self, event_data: Dict) -> Dict:
        """
        Sanitize event data to prevent injection attacks
        """
        sanitized = event_data.copy()

        def sanitize_string(value):
            if isinstance(value, str):
                # Remove potential injection vectors
                value = value.replace("<script>", "").replace("</script>", "")
                value = value.replace("javascript:", "")
                value = value.strip()
                # Limit length
                if len(value) > 1000:
                    value = value[:1000]
            return value

        def sanitize_dict(d):
            if not isinstance(d, dict):
                return d
            sanitized = {}
            for k, v in d.items():
                if isinstance(k, str):
                    k = sanitize_string(k)
                if isinstance(v, str):
                    v = sanitize_string(v)
                elif isinstance(v, dict):
                    v = sanitize_dict(v)
                elif isinstance(v, list):
                    v = [sanitize_string(item) if isinstance(item, str) else item for item in v]
                sanitized[k] = v
            return sanitized

        return sanitize_dict(sanitized)


# Factory function
def create_event_validation_service() -> EventValidationService:
    """Create event validation service instance"""
    return EventValidationService()