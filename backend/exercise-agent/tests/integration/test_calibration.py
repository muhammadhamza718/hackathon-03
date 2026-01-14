"""
Integration tests for difficulty calibration
Exercise Agent
"""

import pytest
import sys
import os
import asyncio

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from services.difficulty_calibration import calibrate_difficulty_with_mcp, assess_readiness

def test_difficulty_calibration_beginner_to_intermediate():
    """Test calibration from beginner to intermediate level"""
    result = asyncio.run(calibrate_difficulty_with_mcp(
        mastery=0.6,
        success_rate=0.7
    ))

    assert result == "intermediate"

def test_difficulty_calibration_intermediate_to_advanced():
    """Test calibration to advanced level"""
    result = asyncio.run(calibrate_difficulty_with_mcp(
        mastery=0.85,
        success_rate=0.8
    ))

    assert result == "advanced"

def test_difficulty_calibration_stay_beginner():
    """Test calibration stays beginner level"""
    result = asyncio.run(calibrate_difficulty_with_mcp(
        mastery=0.3,
        success_rate=0.4
    ))

    assert result == "beginner"

def test_difficulty_calibration_edge_cases():
    """Test calibration with edge case values"""
    # Maximum values
    result_max = asyncio.run(calibrate_difficulty_with_mcp(1.0, 1.0))
    assert result_max == "advanced"

    # Minimum values
    result_min = asyncio.run(calibrate_difficulty_with_mcp(0.0, 0.0))
    assert result_min == "beginner"

def test_readiness_assessment_ready():
    """Test readiness assessment for ready student"""
    assessment = asyncio.run(assess_readiness(0.7, "intermediate"))

    assert assessment["ready_to_learn"] is True
    assert assessment["readiness_score"] >= 1.0

def test_readiness_assessment_not_ready():
    """Test readiness assessment for not ready student"""
    assessment = asyncio.run(assess_readiness(0.4, "intermediate"))

    assert assessment["ready_to_learn"] is False
    assert assessment["readiness_score"] < 1.0
    assert assessment["estimated_preparation_time"] > 0

def test_readiness_assessment_advanced_target():
    """Test readiness for advanced target"""
    assessment = asyncio.run(assess_readiness(0.75, "advanced"))

    assert assessment["ready_to_learn"] is False  # 0.75 < 0.8
    assert assessment["required_mastery"] == 0.8

def test_calibration_consistency():
    """Test that calibration is consistent for similar inputs"""
    results = []
    for i in range(5):
        result = asyncio.run(calibrate_difficulty_with_mcp(0.65, 0.75))
        results.append(result)

    # All should be intermediate
    assert all(r == "intermediate" for r in results)

def test_adaptive_learning_engine():
    """Test the full adaptive learning engine"""
    from services.difficulty_calibration import AdaptiveLearningEngine

    engine = AdaptiveLearningEngine()

    # Test student profile
    student_profile = {
        "mastery": 0.6,
        "success_rate": 0.75,
        "completed_concepts": ["loops", "conditionals"]
    }

    path = asyncio.run(engine.generate_learning_path(student_profile))

    assert "current_level" in path
    assert "next_concepts" in path
    assert "practice_focus" in path
    assert path["current_level"] == "intermediate"

def test_performance_trend_analysis():
    """Test difficulty adjustment based on performance trends"""
    from services.difficulty_calibration import AdaptiveLearningEngine

    engine = AdaptiveLearningEngine()

    # Improving trend
    improving = [0.4, 0.5, 0.6, 0.7, 0.8]
    result = engine.calculate_difficulty_adjustment(improving)
    assert result == "increase"

    # Declining trend
    declining = [0.8, 0.7, 0.6, 0.5, 0.4]
    result = engine.calculate_difficulty_adjustment(declining)
    assert result == "decrease"

    # Stable trend
    stable = [0.7, 0.75, 0.73, 0.72, 0.74]
    result = engine.calculate_difficulty_adjustment(stable)
    assert result == "stable"

if __name__ == "__main__":
    pytest.main([__file__])