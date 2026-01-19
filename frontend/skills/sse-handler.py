#!/usr/bin/env python3
"""
SSE Handler Skill
Processes Server-Sent Events and transforms them for frontend consumption
Task: T121

Last Updated: 2026-01-15
"""

import json
import logging
import asyncio
from typing import Dict, Any, Optional, List, Callable
from enum import Enum
from dataclasses import dataclass, asdict
from datetime import datetime
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class EventType(Enum):
    """Event type classification"""
    MASTERY_UPDATE = "mastery_update"
    RECOMMENDATION = "recommendation"
    ALERT = "alert"
    PROGRESS = "progress"
    ERROR = "error"
    HEARTBEAT = "heartbeat"


class EventPriority(Enum):
    """Event priority levels"""
    HIGH = "high"
    NORMAL = "normal"
    LOW = "low"


@dataclass
class ProcessedEvent:
    """Processed event data structure"""
    id: str
    type: str
    priority: str
    timestamp: str
    source: str
    data: Dict[str, Any]
    metadata: Dict[str, Any]
    display: Dict[str, Any]


@dataclass
class EventFilter:
    """Event filtering configuration"""
    types: Optional[List[str]] = None
    priorities: Optional[List[str]] = None
    sources: Optional[List[str]] = None
    student_ids: Optional[List[str]] = None
    regex_patterns: Optional[List[str]] = None


class SSEHandlerSkill:
    """SSE Handler Skill for processing and transforming events"""

    def __init__(self):
        self.logger = logger
        self.event_processors: Dict[str, Callable] = {}
        self.filters: Dict[str, EventFilter] = {}
        self._setup_default_processors()

    def _setup_default_processors(self):
        """Setup default event processors"""
        self.event_processors = {
            EventType.MASTERY_UPDATE.value: self._process_mastery_event,
            EventType.RECOMMENDATION.value: self._process_recommendation_event,
            EventType.ALERT.value: self._process_alert_event,
            EventType.PROGRESS.value: self._process_progress_event,
            EventType.ERROR.value: self._process_error_event,
            EventType.HEARTBEAT.value: self._process_heartbeat_event,
        }

    def process_event(self, raw_event: Dict[str, Any], context: Optional[Dict[str, Any]] = None) -> Optional[ProcessedEvent]:
        """
        Process raw SSE event and transform it for frontend

        Args:
            raw_event: Raw SSE event data
            context: Additional context information

        Returns:
            Processed event or None if filtered out
        """
        try:
            # Extract event data
            event_data = self._extract_event_data(raw_event)
            if not event_data:
                return None

            # Check if event should be filtered
            if not self._should_process_event(event_data, context):
                return None

            # Get event type and processor
            event_type = event_data.get("type", "unknown")
            processor = self.event_processors.get(event_type)

            if processor:
                processed = processor(event_data, context)
            else:
                processed = self._process_generic_event(event_data, context)

            # Add metadata
            processed = self._enrich_with_metadata(processed, raw_event, context)

            self.logger.info(f"Processed event {processed.id} of type {processed.type}")
            return processed

        except Exception as e:
            self.logger.error(f"Error processing event: {e}")
            return self._create_error_event(raw_event, str(e))

    def _extract_event_data(self, raw_event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract event data from raw SSE format"""
        try:
            # Handle different SSE formats
            if "data" in raw_event:
                data = raw_event["data"]
                if isinstance(data, str):
                    try:
                        data = json.loads(data)
                    except json.JSONDecodeError:
                        # Try to extract JSON from string
                        match = re.search(r'\{.*\}', data)
                        if match:
                            data = json.loads(match.group())
                        else:
                            return None
                return data
            elif "event" in raw_event and "payload" in raw_event:
                return raw_event["payload"]
            else:
                return raw_event

        except Exception as e:
            self.logger.error(f"Error extracting event data: {e}")
            return None

    def _should_process_event(self, event_data: Dict[str, Any], context: Optional[Dict[str, Any]]) -> bool:
        """Determine if event should be processed based on filters"""
        if not self.filters:
            return True

        event_id = event_data.get("id", "")
        event_type = event_data.get("type", "")
        event_priority = event_data.get("priority", "normal")
        event_source = event_data.get("source", "")
        student_id = event_data.get("studentId", "")

        for filter_id, event_filter in self.filters.items():
            # Check type filter
            if event_filter.types and event_type not in event_filter.types:
                continue

            # Check priority filter
            if event_filter.priorities and event_priority not in event_filter.priorities:
                continue

            # Check source filter
            if event_filter.sources and event_source not in event_filter.sources:
                continue

            # Check student ID filter
            if event_filter.student_ids and student_id not in event_filter.student_ids:
                continue

            # Check regex patterns
            if event_filter.regex_patterns:
                event_str = json.dumps(event_data)
                if not any(re.search(pattern, event_str) for pattern in event_filter.regex_patterns):
                    continue

            # Event passed all filters
            return True

        return len(self.filters) == 0

    def _process_mastery_event(self, event_data: Dict[str, Any], context: Optional[Dict[str, Any]]) -> ProcessedEvent:
        """Process mastery update events"""
        topic = event_data.get("topic", "unknown")
        score = event_data.get("score", 0)
        previous_score = event_data.get("previousScore", 0)

        # Calculate improvement
        improvement = score - previous_score

        return ProcessedEvent(
            id=event_data.get("id", f"mastery_{datetime.now().isoformat()}"),
            type=EventType.MASTERY_UPDATE.value,
            priority=self._determine_priority(event_data),
            timestamp=event_data.get("timestamp", datetime.now().isoformat()),
            source=event_data.get("source", "backend"),
            data={
                "topic": topic,
                "currentScore": score,
                "previousScore": previous_score,
                "improvement": improvement,
                "trend": "improving" if improvement > 0 else "declining" if improvement < 0 else "stable",
            },
            metadata={
                "confidence": event_data.get("confidence", 0.8),
                "samples": event_data.get("samples", 1),
            },
            display={
                "title": f"Mastery Update: {topic}",
                "message": f"Score: {score:.1%} ({improvement:+.1%})",
                "variant": "success" if improvement > 0 else "info",
                "icon": "📊",
                "duration": 5000,
            },
        )

    def _process_recommendation_event(self, event_data: Dict[str, Any], context: Optional[Dict[str, Any]]) -> ProcessedEvent:
        """Process recommendation events"""
        rec_type = event_data.get("recommendationType", "exercise")
        priority = event_data.get("priority", "medium")
        topic = event_data.get("topic", "unknown")

        return ProcessedEvent(
            id=event_data.get("id", f"rec_{datetime.now().isoformat()}"),
            type=EventType.RECOMMENDATION.value,
            priority=self._determine_priority(event_data),
            timestamp=event_data.get("timestamp", datetime.now().isoformat()),
            source=event_data.get("source", "ai_engine"),
            data={
                "type": rec_type,
                "topic": topic,
                "priority": priority,
                "title": event_data.get("title", "New Recommendation"),
                "description": event_data.get("description", ""),
                "estimatedTime": event_data.get("estimatedTime", 15),
            },
            metadata={
                "confidence": event_data.get("confidence", 0.75),
                "modelVersion": event_data.get("modelVersion", "1.0"),
            },
            display={
                "title": f"🎯 {rec_type.capitalize()} Recommendation",
                "message": f"{topic}: {event_data.get('title', '')}",
                "variant": "info",
                "icon": "🎯",
                "duration": 8000,
                "actions": ["view", "accept", "dismiss"],
            },
        )

    def _process_alert_event(self, event_data: Dict[str, Any], context: Optional[Dict[str, Any]]) -> ProcessedEvent:
        """Process alert events"""
        alert_type = event_data.get("alertType", "info")
        severity = event_data.get("severity", "info")

        return ProcessedEvent(
            id=event_data.get("id", f"alert_{datetime.now().isoformat()}"),
            type=EventType.ALERT.value,
            priority=self._determine_priority(event_data),
            timestamp=event_data.get("timestamp", datetime.now().isoformat()),
            source=event_data.get("source", "system"),
            data={
                "alertType": alert_type,
                "severity": severity,
                "message": event_data.get("message", ""),
                "details": event_data.get("details", {}),
            },
            metadata={
                "requiresAck": event_data.get("requiresAck", False),
                "autoDismiss": event_data.get("autoDismiss", True),
            },
            display={
                "title": f"Alert: {alert_type}",
                "message": event_data.get("message", ""),
                "variant": self._map_severity_to_variant(severity),
                "icon": "⚠️" if severity in ["warning", "error"] else "ℹ️",
                "duration": 10000 if severity == "info" else 15000,
            },
        )

    def _process_progress_event(self, event_data: Dict[str, Any], context: Optional[Dict[str, Any]]) -> ProcessedEvent:
        """Process progress update events"""
        progress = event_data.get("progress", 0)
        total = event_data.get("total", 100)
        current = event_data.get("current", 0)

        return ProcessedEvent(
            id=event_data.get("id", f"progress_{datetime.now().isoformat()}"),
            type=EventType.PROGRESS.value,
            priority=self._determine_priority(event_data),
            timestamp=event_data.get("timestamp", datetime.now().isoformat()),
            source=event_data.get("source", "backend"),
            data={
                "progress": progress,
                "total": total,
                "current": current,
                "percentage": (progress / total * 100) if total > 0 else 0,
                "status": event_data.get("status", "processing"),
                "task": event_data.get("task", "unknown"),
            },
            metadata={
                "estimatedCompletion": event_data.get("estimatedCompletion"),
            },
            display={
                "title": f"Progress: {event_data.get('task', 'Task')}",
                "message": f"{progress}/{total} ({(progress/total*100):.1f}%)",
                "variant": "info",
                "icon": "⏳",
                "duration": 3000,
                "showProgress": True,
            },
        )

    def _process_error_event(self, event_data: Dict[str, Any], context: Optional[Dict[str, Any]]) -> ProcessedEvent:
        """Process error events"""
        error_code = event_data.get("errorCode", "UNKNOWN_ERROR")
        message = event_data.get("message", "An error occurred")

        return ProcessedEvent(
            id=event_data.get("id", f"error_{datetime.now().isoformat()}"),
            type=EventType.ERROR.value,
            priority="high",  # Errors are always high priority
            timestamp=event_data.get("timestamp", datetime.now().isoformat()),
            source=event_data.get("source", "system"),
            data={
                "errorCode": error_code,
                "message": message,
                "details": event_data.get("details", {}),
                "suggestions": event_data.get("suggestions", []),
            },
            metadata={
                "severity": event_data.get("severity", "error"),
                "retryable": event_data.get("retryable", False),
            },
            display={
                "title": f"Error: {error_code}",
                "message": message,
                "variant": "error",
                "icon": "❌",
                "duration": 10000,
                "actions": ["retry", "dismiss", "report"],
            },
        )

    def _process_heartbeat_event(self, event_data: Dict[str, Any], context: Optional[Dict[str, Any]]) -> ProcessedEvent:
        """Process heartbeat events (keep-alive)"""
        return ProcessedEvent(
            id=event_data.get("id", f"heartbeat_{datetime.now().isoformat()}"),
            type=EventType.HEARTBEAT.value,
            priority="low",
            timestamp=event_data.get("timestamp", datetime.now().isoformat()),
            source=event_data.get("source", "system"),
            data={
                "status": "alive",
                "timestamp": event_data.get("timestamp", datetime.now().isoformat()),
            },
            metadata={
                "system": event_data.get("system", "unknown"),
                "version": event_data.get("version", "1.0"),
            },
            display={
                "title": "",
                "message": "",
                "variant": "silent",
                "icon": "",
                "duration": 0,
            },
        )

    def _process_generic_event(self, event_data: Dict[str, Any], context: Optional[Dict[str, Any]]) -> ProcessedEvent:
        """Process generic/unknown event types"""
        return ProcessedEvent(
            id=event_data.get("id", f"generic_{datetime.now().isoformat()}"),
            type=event_data.get("type", "unknown"),
            priority=self._determine_priority(event_data),
            timestamp=event_data.get("timestamp", datetime.now().isoformat()),
            source=event_data.get("source", "unknown"),
            data=event_data.get("data", {}),
            metadata=event_data.get("metadata", {}),
            display={
                "title": event_data.get("title", "Update"),
                "message": event_data.get("message", "New update received"),
                "variant": "info",
                "icon": "🔔",
                "duration": 5000,
            },
        )

    def _enrich_with_metadata(self, processed: ProcessedEvent, raw_event: Dict[str, Any], context: Optional[Dict[str, Any]]) -> ProcessedEvent:
        """Add additional metadata to processed event"""
        processed.metadata.update({
            "rawEventSize": len(json.dumps(raw_event)),
            "processedAt": datetime.now().isoformat(),
            "hasContext": bool(context),
        })

        if context:
            processed.metadata["context"] = context

        return processed

    def _create_error_event(self, raw_event: Dict[str, Any], error_message: str) -> ProcessedEvent:
        """Create error event for processing failures"""
        return ProcessedEvent(
            id=f"processing_error_{datetime.now().isoformat()}",
            type=EventType.ERROR.value,
            priority="high",
            timestamp=datetime.now().isoformat(),
            source="sse_handler",
            data={
                "errorCode": "EVENT_PROCESSING_ERROR",
                "message": f"Failed to process event: {error_message}",
                "rawEvent": raw_event,
            },
            metadata={
                "severity": "error",
                "retryable": False,
            },
            display={
                "title": "Event Processing Error",
                "message": "Failed to process incoming event",
                "variant": "error",
                "icon": "❌",
                "duration": 10000,
            },
        )

    def _determine_priority(self, event_data: Dict[str, Any]) -> str:
        """Determine event priority based on content and context"""
        explicit_priority = event_data.get("priority")
        if explicit_priority:
            return explicit_priority

        event_type = event_data.get("type", "")
        severity = event_data.get("severity", "")

        # High priority events
        if event_type in ["error", "alert"] and severity in ["error", "critical"]:
            return EventPriority.HIGH.value

        # Low priority events
        if event_type in ["heartbeat", "progress"]:
            return EventPriority.LOW.value

        # Default to normal
        return EventPriority.NORMAL.value

    def _map_severity_to_variant(self, severity: str) -> str:
        """Map severity to UI variant"""
        mapping = {
            "critical": "error",
            "error": "error",
            "warning": "warning",
            "info": "info",
            "success": "success",
        }
        return mapping.get(severity, "info")

    def add_filter(self, filter_id: str, event_filter: EventFilter):
        """Add event filter"""
        self.filters[filter_id] = event_filter
        self.logger.info(f"Added filter {filter_id}")

    def remove_filter(self, filter_id: str):
        """Remove event filter"""
        if filter_id in self.filters:
            del self.filters[filter_id]
            self.logger.info(f"Removed filter {filter_id}")

    def clear_filters(self):
        """Clear all filters"""
        self.filters.clear()
        self.logger.info("Cleared all filters")

    def batch_process_events(self, events: List[Dict[str, Any]], context: Optional[Dict[str, Any]] = None) -> List[ProcessedEvent]:
        """Process multiple events in batch"""
        processed_events = []

        for event in events:
            try:
                processed = self.process_event(event, context)
                if processed:
                    processed_events.append(processed)
            except Exception as e:
                self.logger.error(f"Error processing event in batch: {e}")
                continue

        self.logger.info(f"Batch processed {len(processed_events)}/{len(events)} events")
        return processed_events


def main():
    """Main function for testing the skill"""
    skill = SSEHandlerSkill()

    # Test events
    test_events = [
        {
            "id": "mastery_001",
            "type": "mastery_update",
            "priority": "normal",
            "timestamp": "2026-01-15T10:00:00Z",
            "source": "backend",
            "topic": "algebra",
            "score": 0.85,
            "previousScore": 0.75,
            "confidence": 0.9,
            "samples": 10,
        },
        {
            "id": "rec_001",
            "type": "recommendation",
            "priority": "high",
            "timestamp": "2026-01-15T10:01:00Z",
            "source": "ai_engine",
            "recommendationType": "exercise",
            "priority": "high",
            "topic": "calculus",
            "title": "Practice derivatives",
            "description": "Work on derivative problems",
            "estimatedTime": 20,
            "confidence": 0.85,
        },
        {
            "id": "alert_001",
            "type": "alert",
            "priority": "high",
            "timestamp": "2026-01-15T10:02:00Z",
            "source": "system",
            "alertType": "performance",
            "severity": "warning",
            "message": "High memory usage detected",
            "requiresAck": True,
        },
        {
            "id": "progress_001",
            "type": "progress",
            "priority": "low",
            "timestamp": "2026-01-15T10:03:00Z",
            "source": "backend",
            "progress": 75,
            "total": 100,
            "current": 75,
            "status": "processing",
            "task": "Batch Analysis",
            "estimatedCompletion": "2026-01-15T10:05:00Z",
        },
        {
            "id": "error_001",
            "type": "error",
            "priority": "high",
            "timestamp": "2026-01-15T10:04:00Z",
            "source": "system",
            "errorCode": "NETWORK_ERROR",
            "message": "Connection to backend lost",
            "severity": "error",
            "retryable": True,
        },
    ]

    print("=== SSE Handler Skill Test ===\n")

    # Test single event processing
    print("1. Single Event Processing:")
    print("-" * 40)
    for i, event in enumerate(test_events[:3], 1):
        try:
            processed = skill.process_event(event)
            if processed:
                print(f"Event {i}: {processed.type}")
                print(f"  ID: {processed.id}")
                print(f"  Priority: {processed.priority}")
                print(f"  Display: {processed.display}")
                print()
        except Exception as e:
            print(f"Error processing event {i}: {e}\n")

    # Test batch processing
    print("2. Batch Processing:")
    print("-" * 40)
    try:
        processed_batch = skill.batch_process_events(test_events)
        print(f"Processed {len(processed_batch)} events")
        for event in processed_batch:
            print(f"  - {event.type}: {event.display.get('title', 'No title')}")
    except Exception as e:
        print(f"Error in batch processing: {e}")

    # Test filtering
    print("\n3. Event Filtering:")
    print("-" * 40)
    skill.add_filter("high_priority_only", EventFilter(priorities=["high"]))
    high_priority_events = skill.batch_process_events(test_events)
    print(f"Filtered to {len(high_priority_events)} high priority events")

    print("\n" + "=" * 40)


if __name__ == "__main__":
    main()