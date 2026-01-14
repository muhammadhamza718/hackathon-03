"""
Unit tests for Mastery Calculation Logic
"""

import pytest
import sys
import os

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from services.mastery_calculator import calculate_mastery_with_mcp

def test_mastery_calculation_basic():
    """Test basic mastery calculation"""
    result = calculate_mastery_with_mcp(
        student_id="student123",
        topic_id="python_basic",
        session_data={"score": 85, "time": 30}
    )

    assert result["student_id"] == "student123"
    assert result["topic_id"] == "python_basic"
    assert 0 <= result["mastery_level"] <= 1
    assert 0 <= result["confidence"] <= 1
    assert "recommendations" in result
    assert "timestamp" in result

def test_mastery_calculation_boundaries():
    """Test mastery calculation with edge cases"""
    # Empty session data
    result = calculate_mastery_with_mcp("s1", "t1", {})
    assert result["mastery_level"] >= 0

    # High score scenario
    result = calculate_mastery_with_mcp("s1", "t1", {"score": 100, "time": 60})
    assert result["mastery_level"] > 0

def test_mastery_trend_calculation():
    """Test trend calculation"""
    from services.mastery_calculator import get_mastery_trend

    trend = get_mastery_trend("student123", "python_basic", 30)

    assert trend["student_id"] == "student123"
    assert trend["topic_id"] == "python_basic"
    assert "trend_data" in trend
    assert "improvement_rate" in trend
    assert trend["improvement_rate"] > 0

if __name__ == "__main__":
    pytest.main([__file__])