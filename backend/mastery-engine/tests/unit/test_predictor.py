"""
Predictor Unit Tests
====================

Unit tests for predictive analytics service.
"""

import pytest
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from src.services.predictor import PredictorService, AdaptivePredictor
from src.services.state_manager import StateManager
from src.models.mastery import (
    MasteryResult,
    MasteryLevel,
    ComponentScores,
    MasteryBreakdown,
    PredictionResult,
    TrajectoryResult,
    PredictionModelConfig
)


class TestLinearRegression:
    """Test linear regression functionality"""

    def test_linear_regression_perfect_correlation(self):
        """Test with perfect linear data"""
        service = PredictorService(Mock())
        x = [1, 2, 3, 4, 5]
        y = [2, 4, 6, 8, 10]  # y = 2x

        slope, intercept, confidence = service._linear_regression_with_confidence(x, y)

        assert abs(slope - 2.0) < 0.001
        assert abs(intercept - 0.0) < 0.001
        assert confidence > 0.95  # Should be very high for perfect correlation

    def test_linear_regression_declining_trend(self):
        """Test with declining trend"""
        service = PredictorService(Mock())
        x = [1, 2, 3, 4, 5]
        y = [0.8, 0.7, 0.6, 0.5, 0.4]  # Declining

        slope, intercept, confidence = service._linear_regression_with_confidence(x, y)

        assert slope < -0.1  # Should be negative
        assert confidence > 0.9  # Still high confidence for clear trend

    def test_linear_regression_noisy_data(self):
        """Test with noisy data (lower confidence)"""
        service = PredictorService(Mock())
        x = [1, 2, 3, 4, 5, 6, 7]
        y = [0.5, 0.6, 0.55, 0.65, 0.58, 0.62, 0.6]  # Noisy but trending up

        slope, intercept, confidence = service._linear_regression_with_confidence(x, y)

        assert slope > 0  # Upward trend
        assert confidence < 0.8  # Lower confidence due to noise
        assert confidence > 0.3  # But not too low

    def test_linear_regression_insufficient_data(self):
        """Test with insufficient data"""
        service = PredictorService(Mock())
        x = [1]
        y = [0.5]

        slope, intercept, confidence = service._linear_regression_with_confidence(x, y)

        # Should return fallback values
        assert confidence < 0.2  # Very low confidence
        assert slope == 0.0

    def test_linear_regression_flat_line(self):
        """Test with flat data"""
        service = PredictorService(Mock())
        x = [1, 2, 3, 4, 5]
        y = [0.5, 0.5, 0.5, 0.5, 0.5]

        slope, intercept, confidence = service._linear_regression_with_confidence(x, y)

        assert abs(slope) < 0.01  # Nearly flat
        assert confidence > 0.8  # High confidence despite flatness


class TestComponentProjection:
    """Test component projection logic"""

    def test_component_projection_positive_change(self):
        """Test projection with positive score change"""
        service = PredictorService(Mock())
        current = ComponentScores(completion=0.7, quiz=0.75, quality=0.8, consistency=0.6)
        score_change = 0.1  # Improving by 0.1

        projected = service._project_components(current, score_change)

        # All components should improve (but not exceed 1.0)
        assert projected.completion > current.completion
        assert projected.quiz > current.quiz
        assert projected.quality > current.quality
        assert projected.consistency > current.consistency
        assert all(0.0 <= v <= 1.0 for v in [projected.completion, projected.quiz, projected.quality, projected.consistency])

    def test_component_projection_negative_change(self):
        """Test projection with negative score change"""
        service = PredictorService(Mock())
        current = ComponentScores(completion=0.8, quiz=0.85, quality=0.9, consistency=0.8)
        score_change = -0.05  # Declining

        projected = service._project_components(current, score_change)

        # All components should decline
        assert projected.completion < current.completion
        assert projected.quiz < current.quiz
        assert projected.quality < current.quality
        assert projected.consistency < current.consistency
        assert all(0.0 <= v <= 1.0 for v in [projected.completion, projected.quiz, projected.quality, projected.consistency])

    def test_component_projection_bounds(self):
        """Test that projection stays within bounds"""
        service = PredictorService(Mock())
        current = ComponentScores(completion=0.95, quiz=0.95, quality=0.95, consistency=0.95)
        score_change = 0.2  # Large improvement

        projected = service._project_components(current, score_change)

        # Should cap at 1.0
        assert all(v <= 1.0 for v in [projected.completion, projected.quiz, projected.quality, projected.consistency])


class TestMasteryLevelConversion:
    """Test mastery score to level conversion"""

    def test_score_to_level_novice(self):
        service = PredictorService(Mock())
        assert service._score_to_mastery_level(0.2) == MasteryLevel.NOVICE
        assert service._score_to_mastery_level(0.35) == MasteryLevel.NOVICE

    def test_score_to_level_developing(self):
        service = PredictorService(Mock())
        assert service._score_to_mastery_level(0.4) == MasteryLevel.DEVELOPING
        assert service._score_to_mastery_level(0.55) == MasteryLevel.DEVELOPING

    def test_score_to_level_proficient(self):
        service = PredictorService(Mock())
        assert service._score_to_mastery_level(0.6) == MasteryLevel.PROFICIENT
        assert service._score_to_mastery_level(0.75) == MasteryLevel.PROFICIENT

    def test_score_to_level_master(self):
        service = PredictorService(Mock())
        assert service._score_to_mastery_level(0.8) == MasteryLevel.MASTER
        assert service._score_to_mastery_level(0.95) == MasteryLevel.MASTER


class TestPredictionCaching:
    """Test prediction caching mechanisms"""

    @pytest.mark.asyncio
    async def test_prediction_caching_success(self):
        """Test successful prediction caching"""
        mock_state = Mock()
        mock_state.save = AsyncMock()

        service = PredictorService(mock_state)

        prediction = PredictionResult(
            student_id="test_student",
            predicted_score=0.85,
            confidence=0.9,
            trend="improving",
            intervention_needed=False,
            timeframe_days=7,
            predicted_level=MasteryLevel.PROFICIENT,
            components_projection=ComponentScores(0.85, 0.85, 0.85, 0.85)
        )

        await service._cache_prediction("test_student", 7, prediction)

        mock_state.save.assert_called_once()
        call_args = mock_state.save.call_args
        assert "test_student" in call_args[0][0]  # Key contains student_id
        assert call_args[0][1] == prediction.model_dump()  # Data is prediction

    @pytest.mark.asyncio
    async def test_prediction_caching_failure_handling(self):
        """Test that caching failures are handled gracefully"""
        mock_state = Mock()
        mock_state.save = AsyncMock(side_effect=Exception("Cache failed"))

        service = PredictorService(mock_state)

        # Should not raise exception
        await service._cache_prediction(
            "test_student",
            7,
            Mock(model_dump=lambda: {"test": "data"})
        )

        # Just verify it tried to save
        mock_state.save.assert_called_once()


class TestInsufficientHistoryHandling:
    """Test handling of insufficient historical data"""

    @pytest.mark.asyncio
    async def test_insufficient_history_prediction(self):
        """Test prediction generation with insufficient history"""
        mock_state = Mock()
        mock_state.get_mastery_score = AsyncMock(
            return_value=MasteryResult(
                student_id="test_student",
                mastery_score=0.6,
                level=MasteryLevel.PROFICIENT,
                components=ComponentScores(0.6, 0.6, 0.6, 0.6),
                breakdown=MasteryBreakdown(
                    completion=0.24, quiz=0.18, quality=0.12, consistency=0.06,
                    weighted_sum=0.6,
                    weights=Mock()
                )
            )
        )

        service = PredictorService(mock_state)
        prediction = await service._generate_insufficient_history_prediction("test_student")

        assert prediction.confidence < 0.3  # Low confidence
        assert prediction.predicted_score > 0.5  # Conservative improvement
        assert prediction.metadata["warning"] == "insufficient_history"

    @pytest.mark.asyncio
    async def test_insufficient_history_trajectory(self):
        """Test trajectory generation with insufficient history"""
        mock_state = Mock()
        mock_state.get_mastery_score = AsyncMock(
            return_value=MasteryResult(
                student_id="test_student",
                mastery_score=0.4,
                level=MasteryLevel.DEVELOPING,
                components=ComponentScores(0.4, 0.4, 0.4, 0.4),
                breakdown=MasteryBreakdown(
                    completion=0.16, quiz=0.12, quality=0.08, consistency=0.04,
                    weighted_sum=0.4,
                    weights=Mock()
                )
            )
        )

        service = PredictorService(mock_state)
        trajectory = await service._generate_insufficient_history_trajectory("test_student")

        assert len(trajectory.trajectory) == 14
        assert all(point.confidence < 0.2 for point in trajectory.trajectory)
        assert trajectory.metadata["warning"] == "insufficient_history"


class TestAdaptivePredictor:
    """Test enhanced adaptive predictor functionality"""

    def test_adaptive_predictor_version(self):
        """Test that adaptive predictor uses higher version"""
        mock_state = Mock()
        predictor = AdaptivePredictor(mock_state)
        assert predictor.model_version == "2.0.0"

    @pytest.mark.asyncio
    async def test_intervention_impact_prediction(self):
        """Test prediction with intervention impact"""
        mock_state = Mock()

        # Mock historical data
        mock_historical = [
            MasteryResult(
                student_id="test",
                mastery_score=0.5 + i * 0.02,
                level=MasteryLevel.PROFICIENT,
                components=ComponentScores(0.5 + i * 0.02, 0.5 + i * 0.02, 0.5 + i * 0.02, 0.5 + i * 0.02),
                breakdown=MasteryBreakdown(
                    completion=0.2, quiz=0.15, quality=0.1, consistency=0.05,
                    weighted_sum=0.5 + i * 0.02,
                    weights=Mock()
                ),
                timestamp=datetime.utcnow() - timedelta(days=10-i)
            )
            for i in range(5)
        ]

        mock_state.get_mastery_score = AsyncMock(
            return_value=mock_historical[-1]
        )

        # Mock the state manager's get method for historical data
        mock_get = AsyncMock()
        mock_get.side_effect = lambda key: mock_historical[int(key.split(':')[-1])].model_dump() if "2024" in key else None
        mock_state.get = mock_get

        predictor = AdaptivePredictor(mock_state)

        # Test different intervention types
        for intervention_type in ["tutoring", "practice", "review"]:
            prediction = await predictor.predict_with_intervention_impact("test", intervention_type)

            # Should have intervention metadata
            assert "intervention_impact" in prediction.metadata
            assert "intervention_type" in prediction.metadata
            assert prediction.metadata["intervention_type"] == intervention_type

            # Impact should be positive
            assert prediction.predicted_score >= 0.5


class TestConfidenceScoring:
    """Test confidence scoring logic"""

    def test_high_confidence_perfect_data(self):
        """High confidence for perfect linear data"""
        service = PredictorService(Mock())
        x = [1, 2, 3, 4, 5]
        y = [0.5, 0.6, 0.7, 0.8, 0.9]

        _, _, confidence = service._linear_regression_with_confidence(x, y)
        assert confidence > 0.9

    def test_low_confidence_sparse_data(self):
        """Low confidence for sparse data"""
        service = PredictorService(Mock())
        x = [1, 2, 3]
        y = [0.5, 0.6, 0.7]

        _, _, confidence = service._linear_regression_with_confidence(x, y)
        assert confidence < 0.8
        assert confidence > 0.3

    def test_confidence_with_outliers(self):
        """Test confidence is reasonable despite outliers"""
        service = PredictorService(Mock())
        x = [1, 2, 3, 4, 5, 6, 7]
        y = [0.5, 0.6, 0.05, 0.7, 0.8, 0.9, 0.85]  # One clear outlier

        _, _, confidence = service._linear_regression_with_confidence(x, y)
        # Adaptive predictor should handle outliers
        assert confidence > 0.4


class TestPredictionAccuracyTracking:
    """Test prediction accuracy tracking"""

    @pytest.mark.asyncio
    async def test_prediction_accuracy_tracking(self):
        """Test that accuracy metrics are created"""
        mock_state = Mock()
        mock_state.save = AsyncMock()

        service = PredictorService(mock_state)

        prediction = PredictionResult(
            student_id="test_student",
            predicted_score=0.85,
            confidence=0.9,
            trend="improving",
            intervention_needed=False,
            timeframe_days=7,
            predicted_level=MasteryLevel.PROFICIENT,
            components_projection=ComponentScores(0.85, 0.85, 0.85, 0.85)
        )

        await service._track_prediction_accuracy("test_student", prediction)

        mock_state.save.assert_called_once()
        call_args = mock_state.save.call_args
        # Verify the accuracy metric structure
        accuracy_data = call_args[0][1]
        assert accuracy_data["student_id"] == "test_student"
        assert accuracy_data["predicted_score"] == 0.85
        assert accuracy_data["days_until_verification"] == 7
        assert "prediction_timestamp" in accuracy_data


class TestEdgeCases:
    """Test various edge cases"""

    def test_regression_with_constant_values(self):
        """Test regression when all y values are the same"""
        service = PredictorService(Mock())
        x = [1, 2, 3, 4, 5]
        y = [0.5, 0.5, 0.5, 0.5, 0.5]

        slope, intercept, confidence = service._linear_regression_with_confidence(x, y)

        assert abs(slope) < 0.01  # Should be essentially flat
        assert abs(intercept - 0.5) < 0.01
        assert confidence > 0.8  # High confidence for consistent data

    def test_regression_with_single_data_point(self):
        """Test regression with just one data point"""
        service = PredictorService(Mock())
        x = [1]
        y = [0.5]

        slope, intercept, confidence = service._linear_regression_with_confidence(x, y)

        # Should handle gracefully with fallback
        assert confidence < 0.2
        assert slope == 0.0

    def test_regression_with_perfect_negative_correlation(self):
        """Test perfect negative correlation"""
        service = PredictorService(Mock())
        x = [1, 2, 3, 4, 5]
        y = [1.0, 0.8, 0.6, 0.4, 0.2]  # Perfect negative correlation

        slope, intercept, confidence = service._linear_regression_with_confidence(x, y)

        assert slope < -0.15
        assert confidence > 0.9