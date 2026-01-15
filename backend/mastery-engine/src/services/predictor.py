"""
Predictive Analytics Service
=============================

Mastery prediction using linear regression and confidence scoring.
Provides 7-day mastery projections and intervention flagging.
"""

import logging
import numpy as np
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple
from statistics import mean, stdev

from src.models.mastery import (
    MasteryResult,
    PredictionResult,
    TrajectoryResult,
    TrajectoryPoint,
    PredictionModelConfig,
    ComponentScores,
    MasteryLevel,
    StateKeyPatterns
)
from src.services.state_manager import StateManager

logger = logging.getLogger(__name__)


class PredictorService:
    """Predictive analytics service for mastery forecasting"""

    def __init__(self, state_manager: StateManager, config: Optional[PredictionModelConfig] = None):
        self.state_manager = state_manager
        self.config = config or PredictionModelConfig()
        self.model_version = "1.0.0"

    async def predict_next_week(self, student_id: str) -> PredictionResult:
        """
        Predict mastery score 7 days from now using linear regression

        Args:
            student_id: Student identifier

        Returns:
            PredictionResult with predicted score, confidence, and intervention flags
        """
        logger.info(f"Predicting 7-day mastery for {student_id}")

        # Get historical data
        historical_data = await self._get_historical_mastery(student_id)
        if len(historical_data) < self.config.min_history_days:
            logger.warning(f"Insufficient history for {student_id}: {len(historical_data)} days")
            return await self._generate_insufficient_history_prediction(student_id)

        # Extract scores and timestamps
        scores = [result.mastery_score for result in historical_data]
        days = list(range(len(scores)))  # Day indices

        # Perform linear regression
        slope, intercept, confidence = self._linear_regression_with_confidence(days, scores)

        # Predict 7 days ahead
        future_day = len(scores) + 7
        predicted_score = slope * future_day + intercept

        # Clamp score to valid range
        predicted_score = max(0.0, min(1.0, predicted_score))

        # Determine trend
        trend = "improving" if slope > 0.01 else "declining" if slope < -0.01 else "stable"

        # Check intervention needed
        intervention_needed = predicted_score < self.config.intervention_threshold

        # Project components (simple proportional scaling)
        latest_components = historical_data[-1].components
        components_projection = self._project_components(
            latest_components,
            predicted_score - historical_data[-1].mastery_score
        )

        # Determine predicted level
        predicted_level = self._score_to_mastery_level(predicted_score)

        prediction = PredictionResult(
            student_id=student_id,
            predicted_score=round(predicted_score, 3),
            confidence=round(confidence, 3),
            trend=trend,
            intervention_needed=intervention_needed,
            timeframe_days=7,
            predicted_level=predicted_level,
            components_projection=components_projection,
            metadata={
                "model_version": self.model_version,
                "historical_days": len(historical_data),
                "slope": round(slope, 4),
                "intercept": round(intercept, 4),
                "latest_score": historical_data[-1].mastery_score
            }
        )

        # Cache prediction
        await self._cache_prediction(student_id, 7, prediction)

        # Track accuracy metric for future verification
        await self._track_prediction_accuracy(student_id, prediction)

        logger.info(f"Prediction complete for {student_id}: {predicted_score:.3f} (confidence: {confidence:.3f})")
        return prediction

    async def predict_trajectory(self, student_id: str) -> TrajectoryResult:
        """
        Predict mastery trajectory over the next 14 days

        Args:
            student_id: Student identifier

        Returns:
            TrajectoryResult with day-by-day projections
        """
        logger.info(f"Predicting 14-day trajectory for {student_id}")

        # Get historical data
        historical_data = await self._get_historical_mastery(student_id)
        if len(historical_data) < self.config.min_history_days:
            logger.warning(f"Insufficient history for trajectory {student_id}: {len(historical_data)} days")
            return await self._generate_insufficient_history_trajectory(student_id)

        # Extract scores and perform regression
        scores = [result.mastery_score for result in historical_data]
        days = list(range(len(scores)))
        slope, intercept, base_confidence = self._linear_regression_with_confidence(days, scores)

        # Generate 14-day trajectory
        trajectory_points = []
        intervention_points = []
        confidence_over_time = []

        for day_offset in range(1, 15):  # 1-14 days in future
            future_day = len(scores) + day_offset
            predicted_score = slope * future_day + intercept
            predicted_score = max(0.0, min(1.0, predicted_score))

            # Confidence decays over time
            confidence = base_confidence * (self.config.confidence_decay_rate ** day_offset)

            level = self._score_to_mastery_level(predicted_score)

            point = TrajectoryPoint(
                days_from_now=day_offset,
                predicted_score=round(predicted_score, 3),
                confidence=round(confidence, 3),
                level=level
            )
            trajectory_points.append(point)
            confidence_over_time.append(round(confidence, 3))

            # Track intervention points
            if predicted_score < self.config.intervention_threshold:
                intervention_points.append(day_offset)

        # Determine overall trend
        if len(trajectory_points) >= 2:
            first_score = trajectory_points[0].predicted_score
            last_score = trajectory_points[-1].predicted_score
            trend = "improving" if last_score > first_score + 0.05 else "declining" if last_score < first_score - 0.05 else "stable"
        else:
            trend = "stable"

        trajectory = TrajectoryResult(
            student_id=student_id,
            trajectory=trajectory_points,
            confidence_over_time=confidence_over_time,
            intervention_points=intervention_points,
            overall_trend=trend,
            metadata={
                "model_version": self.model_version,
                "historical_days": len(historical_data),
                "slope": round(slope, 4),
                "intercept": round(intercept, 4)
            }
        )

        # Cache trajectory
        await self._cache_trajectory(student_id, trajectory)

        logger.info(f"Trajectory prediction complete for {student_id}: {len(trajectory_points)} points")
        return trajectory

    async def _get_historical_mastery(self, student_id: str) -> List[MasteryResult]:
        """Retrieve historical mastery data for student"""
        try:
            # Get last 30 days of mastery data
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=self.config.max_history_days)

            historical_data = []
            current_date = start_date

            while current_date <= end_date:
                # Try to get daily snapshot
                key = StateKeyPatterns.daily_snapshot(student_id, current_date)
                mastery_data = await self.state_manager.get(key)

                if mastery_data:
                    mastery_result = MasteryResult(**mastery_data)
                    historical_data.append(mastery_result)

                current_date += timedelta(days=1)

            # If no snapshots found, try to get current mastery as fallback
            if not historical_data:
                current_mastery = await self.state_manager.get_mastery_score(student_id)
                if current_mastery:
                    historical_data.append(current_mastery)

            return historical_data

        except Exception as e:
            logger.error(f"Error retrieving historical data for {student_id}: {e}")
            return []

    def _linear_regression_with_confidence(self, x: List[float], y: List[float]) -> Tuple[float, float, float]:
        """
        Perform linear regression and calculate confidence score

        Returns:
            Tuple of (slope, intercept, confidence)
        """
        if len(x) < 2 or len(y) < 2:
            return 0.0, mean(y) if y else 0.5, 0.1  # Very low confidence

        # Convert to numpy arrays
        x_array = np.array(x)
        y_array = np.array(y)

        # Perform linear regression
        try:
            # Use least squares
            A = np.vstack([x_array, np.ones(len(x_array))]).T
            slope, intercept = np.linalg.lstsq(A, y_array, rcond=None)[0]

            # Calculate R-squared (coefficient of determination)
            y_pred = slope * x_array + intercept
            ss_res = np.sum((y_array - y_pred) ** 2)
            ss_tot = np.sum((y_array - np.mean(y_array)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0

            # Calculate confidence based on:
            # 1. R-squared (quality of fit)
            # 2. Number of data points
            # 3. Data consistency (inverse of standard deviation)

            data_consistency = 1.0 / (1.0 + np.std(y_array))  # Lower std = higher consistency
            sample_size_factor = min(1.0, len(x) / 7.0)  # Full confidence with 7+ data points

            confidence = r_squared * data_consistency * sample_size_factor
            confidence = max(0.1, min(1.0, confidence))  # Clamp between 0.1 and 1.0

            return float(slope), float(intercept), float(confidence)

        except Exception as e:
            logger.error(f"Regression calculation error: {e}")
            # Fallback: simple average trend
            if len(y) >= 2:
                slope = (y[-1] - y[0]) / (len(y) - 1) if len(y) > 1 else 0.0
                intercept = y[0] - slope * x[0]
                return slope, intercept, 0.3  # Low confidence fallback
            return 0.0, mean(y) if y else 0.5, 0.1

    def _project_components(self, current: ComponentScores, score_change: float) -> ComponentScores:
        """
        Project component scores based on overall score change

        Args:
            current: Current component scores
            score_change: Predicted change in overall mastery score

        Returns:
            Projected component scores
        """
        # Simple proportional projection - adjust components toward target
        # Weight components by their importance in mastery formula
        weights = [0.4, 0.3, 0.2, 0.1]  # completion, quiz, quality, consistency

        current_values = [current.completion, current.quiz, current.quality, current.consistency]
        target_values = [max(0.0, min(1.0, v + score_change * weights[i])) for i, v in enumerate(current_values)]

        return ComponentScores(
            completion=round(target_values[0], 3),
            quiz=round(target_values[1], 3),
            quality=round(target_values[2], 3),
            consistency=round(target_values[3], 3)
        )

    def _score_to_mastery_level(self, score: float) -> MasteryLevel:
        """Convert mastery score to MasteryLevel enum"""
        if score < 0.4:
            return MasteryLevel.NOVICE
        elif score < 0.6:
            return MasteryLevel.DEVELOPING
        elif score < 0.8:
            return MasteryLevel.PROFICIENT
        else:
            return MasteryLevel.MASTER

    async def _generate_insufficient_history_prediction(self, student_id: str) -> PredictionResult:
        """Generate conservative prediction when insufficient history exists"""
        current_mastery = await self.state_manager.get_mastery_score(student_id)

        if current_mastery:
            base_score = current_mastery.mastery_score
            # Conservative prediction: slight decline or minimal improvement
            predicted_score = max(0.0, min(1.0, base_score + 0.05))
            confidence = 0.2  # Very low confidence
        else:
            # No data at all - assume beginner level
            predicted_score = 0.3
            confidence = 0.1

        return PredictionResult(
            student_id=student_id,
            predicted_score=round(predicted_score, 3),
            confidence=confidence,
            trend="stable",
            intervention_needed=predicted_score < self.config.intervention_threshold,
            timeframe_days=7,
            predicted_level=self._score_to_mastery_level(predicted_score),
            components_projection=ComponentScores(
                completion=predicted_score,
                quiz=predicted_score,
                quality=predicted_score,
                consistency=predicted_score
            ),
            metadata={
                "model_version": self.model_version,
                "warning": "insufficient_history",
                "historical_days": 0
            }
        )

    async def _generate_insufficient_history_trajectory(self, student_id: str) -> TrajectoryResult:
        """Generate conservative trajectory when insufficient history exists"""
        current_mastery = await self.state_manager.get_mastery_score(student_id)
        base_score = current_mastery.mastery_score if current_mastery else 0.3

        trajectory_points = []
        confidence_over_time = []
        intervention_points = []

        for day in range(1, 15):
            # Conservative: very slight improvement
            predicted_score = min(1.0, base_score + (day * 0.005))
            confidence = 0.1 * (0.95 ** day)  # Low confidence decaying over time

            point = TrajectoryPoint(
                days_from_now=day,
                predicted_score=round(predicted_score, 3),
                confidence=round(confidence, 3),
                level=self._score_to_mastery_level(predicted_score)
            )
            trajectory_points.append(point)
            confidence_over_time.append(round(confidence, 3))

            if predicted_score < self.config.intervention_threshold:
                intervention_points.append(day)

        return TrajectoryResult(
            student_id=student_id,
            trajectory=trajectory_points,
            confidence_over_time=confidence_over_time,
            intervention_points=intervention_points,
            overall_trend="stable",
            metadata={
                "model_version": self.model_version,
                "warning": "insufficient_history",
                "historical_days": 0
            }
        )

    async def _cache_prediction(self, student_id: str, days: int, prediction: PredictionResult):
        """Cache prediction in state store"""
        try:
            key = StateKeyPatterns.prediction(student_id, days)
            await self.state_manager.save(key, prediction.model_dump(), ttl_hours=1)
        except Exception as e:
            logger.warning(f"Failed to cache prediction for {student_id}: {e}")

    async def _cache_trajectory(self, student_id: str, trajectory: TrajectoryResult):
        """Cache trajectory in state store"""
        try:
            key = StateKeyPatterns.trajectory(student_id)
            await self.state_manager.save(key, trajectory.model_dump(), ttl_hours=1)
        except Exception as e:
            logger.warning(f"Failed to cache trajectory for {student_id}: {e}")

    async def _track_prediction_accuracy(self, student_id: str, prediction: PredictionResult):
        """Track prediction for future accuracy verification"""
        try:
            accuracy_metric = {
                "student_id": student_id,
                "prediction_timestamp": datetime.utcnow().isoformat(),
                "predicted_score": prediction.predicted_score,
                "days_until_verification": 7,
                "model_version": self.model_version
            }
            key = StateKeyPatterns.prediction_accuracy(student_id, datetime.utcnow())
            await self.state_manager.save(key, accuracy_metric, ttl_hours=24 * 30)  # 30 days
        except Exception as e:
            logger.warning(f"Failed to track prediction accuracy for {student_id}: {e}")


class AdaptivePredictor(PredictorService):
    """Enhanced predictor with adaptive learning"""

    def __init__(self, state_manager: StateManager, config: Optional[PredictionModelConfig] = None):
        super().__init__(state_manager, config)
        self.model_version = "2.0.0"  # Adaptive version

    async def predict_with_intervention_impact(self, student_id: str, intervention_type: str) -> PredictionResult:
        """
        Predict mastery with expected intervention impact

        Args:
            student_id: Student identifier
            intervention_type: Type of intervention ("tutoring", "practice", "review")

        Returns:
            PredictionResult accounting for intervention impact
        """
        base_prediction = await self.predict_next_week(student_id)

        # Apply intervention impact factors
        intervention_factors = {
            "tutoring": 0.15,    # 15% improvement
            "practice": 0.10,    # 10% improvement
            "review": 0.05,      # 5% improvement
        }

        factor = intervention_factors.get(intervention_type, 0.0)
        adjusted_score = base_prediction.predicted_score + (factor * (1.0 - base_prediction.predicted_score))
        adjusted_score = min(1.0, adjusted_score)  # Cap at 1.0

        base_prediction.predicted_score = round(adjusted_score, 3)
        base_prediction.predicted_level = self._score_to_mastery_level(adjusted_score)
        base_prediction.metadata["intervention_impact"] = factor
        base_prediction.metadata["intervention_type"] = intervention_type

        return base_prediction

    def _linear_regression_with_confidence(self, x: List[float], y: List[float]) -> Tuple[float, float, float]:
        """
        Enhanced regression with outlier detection and removal
        """
        if len(x) < 3:  # Need more data for outlier detection
            return super()._linear_regression_with_confidence(x, y)

        # Remove outliers using IQR method
        Q1 = np.percentile(y, 25)
        Q3 = np.percentile(y, 75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR

        filtered_data = [(xi, yi) for xi, yi in zip(x, y) if lower_bound <= yi <= upper_bound]
        if len(filtered_data) < 3:  # Too many outliers removed
            return super()._linear_regression_with_confidence(x, y)

        filtered_x, filtered_y = zip(*filtered_data)

        # Use parent method on filtered data
        return super()._linear_regression_with_confidence(list(filtered_x), list(filtered_y))