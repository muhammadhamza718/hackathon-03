"""
Unit tests for Explanation Generation Logic
"""

import pytest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from services.explanation_generator import generate_explanation_with_mcp

def test_explanation_generation_basic():
    """Test basic explanation generation"""
    result = generate_explanation_with_mcp(
        concept="loops",
        level="beginner",
        context={},
        style="simple"
    )

    assert "explanation" in result
    assert "analogies" in result
    assert "examples" in result
    assert "key_points" in result

def test_explanation_generation_intermediate():
    """Test intermediate level explanation"""
    result = generate_explanation_with_mcp(
        concept="functions",
        level="intermediate",
        context={"student_id": "test"},
        style="technical"
    )

    assert result["complexity"] == "intermediate"
    assert len(result["analogies"]) > 0
    assert len(result["examples"]) > 0

def test_explanation_structure():
    """Test explanation response structure"""
    result = generate_explanation_with_mcp(
        concept="variables",
        level="beginner",
        context={},
        style="simple"
    )

    # Verify all expected fields exist
    expected_fields = ["explanation", "analogies", "examples", "key_points", "complexity"]
    for field in expected_fields:
        assert field in result

def test_explanation_with_mcp_fallback():
    """Test MCP fallback mechanism"""
    result = generate_explanation_with_mcp(
        concept="recursion",
        level="advanced",
        context={},
        style="detailed"
    )

    # Should include efficiency note in fallback mode
    assert "token_efficiency_note" in result

if __name__ == "__main__":
    pytest.main([__file__])