"""Services Package"""
from .quality_scoring import assess_code_quality_with_mcp, check_mcp_connection as check_quality_mcp
from .hint_generator import generate_hint_with_mcp, check_mcp_connection as check_hint_mcp
from .kafka_consumer import review_consumer

__all__ = [
    "assess_code_quality_with_mcp",
    "check_quality_mcp",
    "generate_hint_with_mcp",
    "check_hint_mcp",
    "review_consumer"
]