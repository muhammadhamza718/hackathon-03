"""
Services Module
===============

Contains business logic, external integrations, and domain operations.
"""

from .mastery_calculator import MasteryCalculator
from .state_manager import StateManager
from .kafka_consumer import KafkaConsumer
from .predictor import Predictor
from .recommendation_engine import RecommendationEngine

__all__ = [
    "MasteryCalculator",
    "StateManager",
    "KafkaConsumer",
    "Predictor",
    "RecommendationEngine"
]