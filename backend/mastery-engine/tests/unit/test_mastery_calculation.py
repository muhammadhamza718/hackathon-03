"""
Unit Tests for Mastery Calculation
===================================

Tests for mastery calculator MCP skill and models.
"""

import pytest
from datetime import datetime

from src.models.mastery import (
    ComponentScores, MasteryWeights, MasteryResult, MasteryLevel,
    MasteryBreakdown
)
from src.skills.calculator import MasteryCalculator, calculate_mastery_student


class TestComponentScores:
    """Test ComponentScores model"""

    def test_valid_components(self):
        """Test valid component scores"""
        components = ComponentScores(
            completion=0.85,
            quiz=0.90,
            quality=0.75,
            consistency=0.80
        )
        assert components.completion == 0.85
        assert components.quiz == 0.90
        assert components.quality == 0.75
        assert components.consistency == 0.80

    def test_boundary_values(self):
        """Test boundary values (0.0 and 1.0)"""
        min_components = ComponentScores(0.0, 0.0, 0.0, 0.0)
        max_components = ComponentScores(1.0, 1.0, 1.0, 1.0)

        assert min_components.completion == 0.0
        assert max_components.consistency == 1.0

    def test_invalid_values(self):
        """Test invalid values raise errors"""
        with pytest.raises(ValueError):
            ComponentScores(completion=1.5, quiz=0.5, quality=0.5, consistency=0.5)

        with pytest.raises(ValueError):
            ComponentScores(completion=-0.1, quiz=0.5, quality=0.5, consistency=0.5)


class TestMasteryWeights:
    """Test MasteryWeights model"""

    def test_default_weights(self):
        """Test default 40/30/20/10 weights"""
        weights = MasteryWeights()
        assert weights.completion == 0.4
        assert weights.quiz == 0.3
        assert weights.quality == 0.2
        assert weights.consistency == 0.1

    def test_custom_weights(self):
        """Test custom weight assignment"""
        weights = MasteryWeights(
            completion=0.5,
            quiz=0.25,
            quality=0.15,
            consistency=0.10
        )
        assert weights.completion == 0.5

    def test_weights_validation(self):
        """Test weight validation"""
        weights = MasteryWeights()
        # Valid weights
        weights.validate_sum()
        # No error expected

    def test_invalid_weights_sum(self):
        """Test invalid weights that don't sum to 1.0"""
        weights = MasteryWeights(completion=0.4, quiz=0.3, quality=0.2, consistency=0.2)
        with pytest.raises(ValueError):
            weights.validate_sum()


class TestMasteryCalculator:
    """Test MasteryCalculator MCP skill"""

    def test_default_calculation(self):
        """Test calculation with default weights"""
        calculator = MasteryCalculator()
        components = ComponentScores(
            completion=0.85,
            quiz=0.90,
            quality=0.85,
            consistency=0.82
        )

        result = calculator.execute_calculation("test_student", components)

        # Expected: 0.85*0.4 + 0.90*0.3 + 0.85*0.2 + 0.82*0.1 = 0.862
        expected_score = 0.862
        assert abs(result.mastery_score - expected_score) < 0.001
        assert result.student_id == "test_student"
        assert result.level == MasteryLevel.MASTER

    def test_calculation_boundary_levels(self):
        """Test mastery level determination at boundaries"""
        calculator = MasteryCalculator()

        # Novice (below 0.4)
        result_novice = calculator.execute_calculation(
            "student1",
            ComponentScores(0.2, 0.2, 0.2, 0.2)
        )
        assert result_novice.level == MasteryLevel.NOVICE

        # Developing (0.4 - 0.6)
        result_developing = calculator.execute_calculation(
            "student2",
            ComponentScores(0.5, 0.5, 0.5, 0.5)
        )
        assert result_developing.level == MasteryLevel.DEVELOPING

        # Proficient (0.6 - 0.8)
        result_proficient = calculator.execute_calculation(
            "student3",
            ComponentScores(0.7, 0.7, 0.7, 0.7)
        )
        assert result_proficient.level == MasteryLevel.PROFICIENT

        # Master (0.8+)
        result_master = calculator.execute_calculation(
            "student4",
            ComponentScores(0.9, 0.9, 0.9, 0.9)
        )
        assert result_master.level == MasteryLevel.MASTER

    def test_custom_weights(self):
        """Test calculation with custom weights"""
        custom_weights = MasteryWeights(
            completion=0.5,
            quiz=0.25,
            quality=0.15,
            consistency=0.10
        )
        calculator = MasteryCalculator(custom_weights)

        components = ComponentScores(
            completion=1.0,
            quiz=0.0,
            quality=0.0,
            consistency=0.0
        )

        result = calculator.execute_calculation("test", components)
        # Should be 1.0 * 0.5 = 0.5
        assert abs(result.mastery_score - 0.5) < 0.001

    def test_breakdown_calculation(self):
        """Test detailed breakdown calculation"""
        calculator = MasteryCalculator()
        components = ComponentScores(
            completion=1.0,
            quiz=1.0,
            quality=1.0,
            consistency=1.0
        )

        result = calculator.execute_calculation("test", components)

        assert result.breakdown.completion == 0.4  # 1.0 * 0.4
        assert result.breakdown.quiz == 0.3       # 1.0 * 0.3
        assert result.breakdown.quality == 0.2    # 1.0 * 0.2
        assert result.breakdown.consistency == 0.1 # 1.0 * 0.1
        assert result.breakdown.weighted_sum == 1.0
        assert result.breakdown.weights.completion == 0.4

    def test_calculate_mastery_score(self):
        """Test direct score calculation"""
        calculator = MasteryCalculator()
        components = ComponentScores(
            completion=0.5,
            quiz=0.5,
            quality=0.5,
            consistency=0.5
        )

        score = calculator.calculate_mastery_score(components)
        # 0.5*0.4 + 0.5*0.3 + 0.5*0.2 + 0.5*0.1 = 0.5
        assert score == 0.5

    def test_find_optimal_improvements(self):
        """Test improvement recommendations"""
        calculator = MasteryCalculator()
        components = ComponentScores(
            completion=0.3,
            quiz=0.4,
            quality=0.5,
            consistency=0.6
        )

        improvements = calculator.find_optimal_improvements(
            components,
            MasteryLevel.PROFICIENT,
            max_changes=2
        )

        assert len(improvements) <= 2
        if improvements:
            assert "component" in improvements[0]
            assert "improvement" in improvements[0]

    def test_analyze_component_weights(self):
        """Test component contribution analysis"""
        calculator = MasteryCalculator()
        components = ComponentScores(
            completion=0.9,
            quiz=0.8,
            quality=0.7,
            consistency=0.6
        )

        analysis = calculator.analyze_component_weights(components)

        assert "total_score" in analysis
        assert "contributions" in analysis
        assert "strongest_component" in analysis
        assert "weakest_component" in analysis

        # Completion should be strongest due to highest individual value and weight
        assert analysis["strongest_component"] == "completion"


class TestFactoryFunction:
    """Test factory and convenience functions"""

    def test_create_mastery_calculator(self):
        """Test factory function"""
        calculator = calculate_mastery_student("test", 0.8, 0.7, 0.6, 0.5)

        assert isinstance(calculator, MasteryResult)
        assert calculator.student_id == "test"
        assert 0.0 <= calculator.mastery_score <= 1.0


class TestMasteryResult:
    """Test MasteryResult model"""

    def test_result_creation(self):
        """Test creating a complete mastery result"""
        components = ComponentScores(0.8, 0.7, 0.6, 0.5)
        breakdown = MasteryBreakdown(
            completion=0.32,
            quiz=0.21,
            quality=0.12,
            consistency=0.05,
            weighted_sum=0.7,
            weights=MasteryWeights()
        )

        result = MasteryResult(
            student_id="test_student",
            mastery_score=0.7,
            level=MasteryLevel.PROFICIENT,
            components=components,
            breakdown=breakdown
        )

        assert result.student_id == "test_student"
        assert result.mastery_score == 0.7
        assert result.level == MasteryLevel.PROFICIENT
        assert isinstance(result.calculated_at, datetime)

    def test_calculate_from_components(self):
        """Test static method for calculation"""
        components = ComponentScores(
            completion=0.85,
            quiz=0.90,
            quality=0.85,
            consistency=0.82
        )

        result = MasteryResult.calculate_from_components("student", components)

        assert result.student_id == "student"
        assert result.level == MasteryLevel.MASTER
        assert abs(result.mastery_score - 0.862) < 0.001


class TestAdaptiveMasteryCalculator:
    """Test adaptive calculator features"""

    def test_beginner_context(self):
        """Test calculation with beginner context"""
        from src.skills.calculator import AdaptiveMasteryCalculator

        calculator = AdaptiveMasteryCalculator()
        components = ComponentScores(
            completion=0.9,
            quiz=0.4,
            quality=0.3,
            consistency=0.8
        )

        result, metadata = calculator.calculate_with_context(components, "beginner")

        assert "context" in metadata
        assert metadata["context"] == "beginner"
        assert result.student_id == "adaptive_temp"

    def test_advanced_context(self):
        """Test calculation with advanced context"""
        from src.skills.calculator import AdaptiveMasteryCalculator

        calculator = AdaptiveMasteryCalculator()
        components = ComponentScores(
            completion=0.4,
            quiz=0.9,
            quality=0.8,
            consistency=0.3
        )

        result, metadata = calculator.calculate_with_context(components, "advanced")

        assert metadata["context"] == "advanced"


class TestStatisticalAnalyzer:
    """Test statistical analysis functions"""

    def test_calculate_batch_mastery(self):
        """Test batch statistics calculation"""
        from src.skills.calculator import StatisticalAnalyzer

        # Create sample results
        results = []
        for score in [0.9, 0.8, 0.7, 0.6, 0.5]:
            components = ComponentScores(score, score, score, score)
            result = MasteryResult.calculate_from_components("test", components)
            results.append(result)

        stats = StatisticalAnalyzer.calculate_batch_mastery(results)

        assert stats["count"] == 5
        assert abs(stats["mean"] - 0.7) < 0.001
        assert stats["min"] == 0.5
        assert stats["max"] == 0.9

    def test_calculate_progress_trend(self):
        """Test trend calculation"""
        from src.skills.calculator import StatisticalAnalyzer

        scores = [0.5, 0.6, 0.7, 0.8]
        from datetime import datetime
        dates = [datetime(2024, 1, i) for i in range(1, 5)]

        trend = StatisticalAnalyzer.calculate_progress_trend(scores, dates)

        assert "trend" in trend
        assert trend["trend"] == "improving"


class TestEdgeCases:
    """Test edge cases and error conditions"""

    def test_zero_weights(self):
        """Test calculation with zero weight components"""
        weights = MasteryWeights(completion=0.0, quiz=0.5, quality=0.5, consistency=0.0)
        calculator = MasteryCalculator(weights)

        components = ComponentScores(
            completion=1.0,  # Shouldn't matter
            quiz=0.5,
            quality=0.5,
            consistency=1.0  # Shouldn't matter
        )

        result = calculator.execute_calculation("test", components)
        expected = 0.5 * 0.5 + 0.5 * 0.5  # 0.5 from quiz + 0.5 from quality

        assert abs(result.mastery_score - expected) < 0.001

    def test_extreme_component_values(self):
        """Test with extreme but valid component values"""
        calculator = MasteryCalculator()

        # All minimums
        result_min = calculator.execute_calculation(
            "min",
            ComponentScores(0.0, 0.0, 0.0, 0.0)
        )
        assert result_min.mastery_score == 0.0

        # All maximums
        result_max = calculator.execute_calculation(
            "max",
            ComponentScores(1.0, 1.0, 1.0, 1.0)
        )
        assert result_max.mastery_score == 1.0