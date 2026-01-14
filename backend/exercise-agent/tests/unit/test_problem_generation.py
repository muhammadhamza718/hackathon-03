"""
Unit tests for problem generation logic
Exercise Agent
"""

import pytest
import sys
import os
import asyncio

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from services.problem_generator import generate_problem_with_mcp

def test_problem_generation_beginner():
    """Test basic problem generation for beginners"""
    result = asyncio.run(generate_problem_with_mcp(
        topic="loops",
        difficulty="beginner",
        student_progress={"student_level": "beginner"}
    ))

    assert "description" in result
    assert "hints" in result
    assert "test_cases" in result
    assert "estimated_time" in result
    assert result["estimated_time"] <= 15  # Should be reasonable time

def test_problem_generation_intermediate():
    """Test intermediate level problem generation"""
    result = asyncio.run(generate_problem_with_mcp(
        topic="functions",
        difficulty="intermediate",
        student_progress={"student_level": "intermediate"}
    ))

    assert "description" in result
    assert len(result["hints"]) > 0  # Should have hints
    assert isinstance(result["test_cases"], list)
    assert result["estimated_time"] >= 10  # More time for intermediate

def test_problem_generation_advanced():
    """Test advanced level problem generation"""
    result = asyncio.run(generate_problem_with_mcp(
        topic="arrays",
        difficulty="advanced",
        student_progress={"student_level": "advanced"}
    ))

    assert "description" in result
    assert len(result["hints"]) > 0
    assert result["estimated_time"] >= 15  # More time for advanced

def test_problem_generation_unknown_topic():
    """Test fallback for unknown topic"""
    result = asyncio.run(generate_problem_with_mcp(
        topic="unknown_concept",
        difficulty="beginner",
        student_progress={}
    ))

    assert "description" in result
    assert "hints" in result
    assert result["estimated_time"] == 15  # Default time

def test_problem_with_student_history():
    """Test that student history influences problem generation"""
    result = asyncio.run(generate_problem_with_mcp(
        topic="loops",
        difficulty="beginner",
        student_progress={
            "student_level": "beginner",
            "previous_attempts": 3,
            "student_id": "test_student"
        }
    ))

    # Should have adjusted hints based on history
    assert "hints" in result
    assert any("Take your time" in hint for hint in result["hints"])

def test_visual_problem_generation():
    """Test visual problem generation enhancement"""
    from services.problem_generator import generate_visual_problem_with_mcp

    result = asyncio.run(generate_visual_problem_with_mcp(
        topic="functions",
        difficulty="intermediate",
        student_progress={}
    ))

    assert "visual_elements" in result
    assert "diagram_type" in result["visual_elements"]
    assert result["visual_elements"]["diagram_type"] == "flowchart"

def test_problem_structure_consistency():
    """Test that all problems have consistent structure"""
    test_cases = [
        ("loops", "beginner"),
        ("functions", "intermediate"),
        ("conditionals", "beginner"),
        ("arrays", "intermediate")
    ]

    for topic, difficulty in test_cases:
        result = asyncio.run(generate_problem_with_mcp(
            topic=topic,
            difficulty=difficulty,
            student_progress={}
        ))

        # Verify all required fields exist
        required_fields = ["description", "hints", "test_cases", "estimated_time"]
        for field in required_fields:
            assert field in result, f"Missing {field} for {topic} ({difficulty})"

        # Verify data types
        assert isinstance(result["description"], str)
        assert isinstance(result["hints"], list)
        assert isinstance(result["test_cases"], list)
        assert isinstance(result["estimated_time"], int)

if __name__ == "__main__":
    pytest.main([__file__])