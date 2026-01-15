"""
Mastery Engine Microservice
===========================

A stateful microservice for tracking and calculating student learning mastery
across multiple dimensions using Dapr State Store and Kafka event streaming.

Key Features:
- Real-time mastery calculation (40/30/20/10 formula)
- Event-driven processing from multiple learning agents
- Predictive analytics and adaptive recommendations
- GDPR compliance with 90-day data retention
- 95% token efficiency via MCP skills

Architecture:
- FastAPI web framework
- Dapr State Store for persistent storage
- Kafka for event streaming
- MCP skills for algorithmic calculations
"""

__version__ = "1.0.0"
__author__ = "LearnFlow Platform Team"

from .models.mastery import (
    ComponentScores,
    MasteryResult,
    MasteryLevel,
    MasteryProfile,
    BreakdownItem
)
from .models.events import (
    MasteryCalculationRequestEvent,
    MasteryUpdatedEvent,
    EventType,
    EventMetadata
)

__all__ = [
    # Version info
    "__version__",
    "__author__",

    # Mastery models
    "ComponentScores",
    "MasteryResult",
    "MasteryLevel",
    "MasteryProfile",
    "BreakdownItem",

    # Event models
    "MasteryCalculationRequestEvent",
    "MasteryUpdatedEvent",
    "EventType",
    "EventMetadata",
]