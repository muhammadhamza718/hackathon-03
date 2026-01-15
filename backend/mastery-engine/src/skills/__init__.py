"""
Skills Module
=============

MCP skills for efficient, algorithmic calculations.
High token efficiency (95% reduction) via pre-built scripts.
"""

from .calculator import calculate_mastery, determine_mastery_level, generate_recommendations
from .pattern_matcher import detect_learning_patterns
from .adaptive_engine import generate_adaptive_path

__all__ = [
    "calculate_mastery",
    "determine_mastery_level",
    "generate_recommendations",
    "detect_learning_patterns",
    "generate_adaptive_path"
]