"""
Mastery Calculator MCP Skill
============================

High-performance mastery calculation using MCP code execution for 95% token efficiency.

This skill implements the core mastery formula and algorithms as pure functions
that can be executed without LLM inference, achieving the 95% token efficiency
target defined in ADR-001.
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime

from src.models.mastery import (
    ComponentScores, MasteryWeights, MasteryResult,
    MasteryLevel, MasteryBreakdown
)

logger = logging.getLogger(__name__)


class MasteryCalculator:
    """
    MCP skill for algorithmic mastery calculation.

    Achieves 95% token efficiency by using mathematical operations
    instead of LLM inference for all calculations.
    """

    def __init__(self, weights: Optional[MasteryWeights] = None):
        """
        Initialize calculator with formula weights.

        Args:
            weights: Optional custom weights (default uses 40/30/20/10)
        """
        self.weights = weights or MasteryWeights()
        self._validate_weights()

    def _validate_weights(self):
        """Validate that weights sum to 1.0"""
        total = (
            self.weights.completion +
            self.weights.quiz +
            self.weights.quality +
            self.weights.consistency
        )
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Weights must sum to 1.0, got {total:.3f}")

    def calculate_mastery_score(self, components: ComponentScores) -> float:
        """
        Calculate weighted mastery score using 40/30/20/10 formula.

        Formula: M = 0.4*C + 0.3*Q + 0.2*Q + 0.1*C

        Args:
            components: Individual component scores (0.0-1.0)

        Returns:
            Mastery score between 0.0 and 1.0
        """
        # Weighted sum using pure mathematical operations
        score = (
            components.completion * self.weights.completion +
            components.quiz * self.weights.quiz +
            components.quality * self.weights.quality +
            components.consistency * self.weights.consistency
        )

        # Clamp to valid range
        return max(0.0, min(1.0, score))

    def determine_mastery_level(self, score: float) -> MasteryLevel:
        """
        Determine mastery level based on score threshold.

        Thresholds:
        - 0.0 - 0.4: NOVICE
        - 0.4 - 0.6: DEVELOPING
        - 0.6 - 0.8: PROFICIENT
        - 0.8 - 1.0: MASTER
        """
        if score < 0.4:
            return MasteryLevel.NOVICE
        elif score < 0.6:
            return MasteryLevel.DEVELOPING
        elif score < 0.8:
            return MasteryLevel.PROFICIENT
        else:
            return MasteryLevel.MASTER

    def calculate_breakdown(self, components: ComponentScores) -> MasteryBreakdown:
        """
        Calculate detailed breakdown showing weighted contributions.
        """
        completion = components.completion * self.weights.completion
        quiz = components.quiz * self.weights.quiz
        quality = components.quality * self.weights.quality
        consistency = components.consistency * self.weights.consistency

        weighted_sum = completion + quiz + quality + consistency

        return MasteryBreakdown(
            completion=completion,
            quiz=quiz,
            quality=quality,
            consistency=consistency,
            weighted_sum=weighted_sum,
            weights=self.weights
        )

    def execute_calculation(
        self,
        student_id: str,
        components: ComponentScores
    ) -> MasteryResult:
        """
        Execute complete mastery calculation pipeline.

        This is the primary MCP skill function - all calculations are
        algorithmic and require zero LLM tokens.
        """
        # Calculate score
        score = self.calculate_mastery_score(components)

        # Determine level
        level = self.determine_mastery_level(score)

        # Calculate breakdown
        breakdown = self.calculate_breakdown(components)

        # Construct result
        result = MasteryResult(
            student_id=student_id,
            mastery_score=score,
            level=level,
            components=components,
            breakdown=breakdown,
            calculated_at=datetime.utcnow()
        )

        logger.info(f"Calculated mastery for {student_id}: {score:.3f} ({level.value})")
        return result

    def calculate_improvement_prediction(
        self,
        current_score: float,
        target_components: ComponentScores
    ) -> Dict[str, any]:
        """
        Predict improvement required to reach target mastery level.

        Returns:
            Dictionary with improvement needed per component
        """
        target_score = self.calculate_mastery_score(target_components)
        improvement = target_score - current_score

        # Calculate what each component contributes to the gap
        component_contributions = {
            "completion": (target_components.completion - (current_score / self.weights.completion if self.weights.completion > 0 else 0)) * self.weights.completion if self.weights.completion > 0 else 0,
            "quiz": (target_components.quiz - (current_score / self.weights.quiz if self.weights.quiz > 0 else 0)) * self.weights.quiz if self.weights.quiz > 0 else 0,
            "quality": (target_components.quality - (current_score / self.weights.quality if self.weights.quality > 0 else 0)) * self.weights.quality if self.weights.quality > 0 else 0,
            "consistency": (target_components.consistency - (current_score / self.weights.consistency if self.weights.consistency > 0 else 0)) * self.weights.consistency if self.weights.consistency > 0 else 0,
        }

        return {
            "current_score": current_score,
            "target_score": target_score,
            "improvement_needed": improvement,
            "component_contributions": component_contributions,
            "achievable": 0.0 <= improvement <= 1.0
        }

    def find_optimal_improvements(
        self,
        current_components: ComponentScores,
        target_level: MasteryLevel,
        max_changes: int = 3
    ) -> List[Dict[str, any]]:
        """
        Find optimal set of component improvements to reach target level.

        Uses simple heuristic to find most impactful changes.
        """
        # Get score threshold for target level
        thresholds = {
            MasteryLevel.NOVICE: 0.0,
            MasteryLevel.DEVELOPING: 0.4,
            MasteryLevel.PROFICIENT: 0.6,
            MasteryLevel.MASTER: 0.8
        }
        target_threshold = thresholds[target_level]
        current_score = self.calculate_mastery_score(current_components)

        if current_score >= target_threshold:
            return []

        # Calculate potential improvements
        improvements = []
        components_list = [
            ("completion", current_components.completion, self.weights.completion),
            ("quiz", current_components.quiz, self.weights.quiz),
            ("quality", current_components.quality, self.weights.quality),
            ("consistency", current_components.consistency, self.weights.consistency),
        ]

        # Sort by potential impact
        for comp_name, current_val, weight in components_list:
            if current_val < 0.95:  # Can be improved
                improvement_needed = (target_threshold - current_score) / weight if weight > 0 else 0
                if improvement_needed > 0:
                    new_val = min(1.0, current_val + improvement_needed)
                    actual_improvement = (new_val - current_val) * weight
                    impact_ratio = actual_improvement / (new_val - current_val + 0.001)

                    improvements.append({
                        "component": comp_name,
                        "current": current_val,
                        "target": new_val,
                        "improvement": new_val - current_val,
                        "score_impact": actual_improvement,
                        "impact_ratio": impact_ratio
                    })

        # Sort by score impact and return top N
        improvements.sort(key=lambda x: x["score_impact"], reverse=True)
        return improvements[:max_changes]

    def analyze_component_weights(self, components: ComponentScores) -> Dict[str, any]:
        """
        Analyze which components contribute most to mastery score.

        Returns:
            Component contribution analysis
        """
        breakdown = self.calculate_breakdown(components)

        contributions = [
            {"component": "completion", "value": breakdown.completion, "weight": self.weights.completion},
            {"component": "quiz", "value": breakdown.quiz, "weight": self.weights.quiz},
            {"component": "quality", "value": breakdown.quality, "weight": self.weights.quality},
            {"component": "consistency", "value": breakdown.consistency, "weight": self.weights.consistency},
        ]

        # Sort by contribution value
        contributions.sort(key=lambda x: x["value"], reverse=True)

        return {
            "total_score": breakdown.weighted_sum,
            "contributions": contributions,
            "strongest_component": contributions[0]["component"] if contributions else None,
            "weakest_component": contributions[-1]["component"] if contributions else None
        }


class AdaptiveMasteryCalculator(MasteryCalculator):
    """
    Enhanced calculator with adaptive learning features.
    Includes dynamic weight adjustment based on learning context.
    """

    def __init__(self, context_weights: Optional[Dict[str, float]] = None):
        """
        Initialize with optional context-aware weight adjustments.

        Args:
            context_weights: Override for specific contexts (e.g., "beginner", "advanced")
        """
        super().__init__()
        self.context_weights = context_weights or {}

    def calculate_with_context(
        self,
        components: ComponentScores,
        context: str = "default"
    ) -> Tuple[MasteryResult, Dict[str, any]]:
        """
        Calculate mastery with context-aware adjustments.

        Contexts:
        - "beginner": Emphasize consistency and completion (60/20/10/10)
        - "advanced": Emphasize quality and quiz (20/40/30/10)
        - "default": Standard 40/30/20/10
        """
        if context == "beginner":
            # Emphasize building good habits
            weights = MasteryWeights(completion=0.6, quiz=0.2, quality=0.1, consistency=0.1)
        elif context == "advanced":
            # Emphasize deeper understanding
            weights = MasteryWeights(completion=0.2, quiz=0.4, quality=0.3, consistency=0.1)
        else:
            weights = self.weights

        # Temporarily override weights
        original_weights = self.weights
        self.weights = weights

        result = self.execute_calculation("adaptive_temp", components)

        # Restore original weights
        self.weights = original_weights

        # Calculate metadata
        metadata = {
            "context": context,
            "weights_used": weights.model_dump(),
            "original_score": self.calculate_mastery_score(components)
        }

        return result, metadata


class StatisticalAnalyzer:
    """
    Statistical analysis tools for mastery data.
    All operations are algorithmic (0 LLM tokens).
    """

    @staticmethod
    def calculate_batch_mastery(results: List[MasteryResult]) -> Dict[str, float]:
        """
        Calculate statistics for a batch of mastery results.
        """
        if not results:
            return {}

        scores = [r.mastery_score for r in results]
        levels = [r.level for r in results]

        return {
            "count": len(scores),
            "mean": np.mean(scores),
            "median": np.median(scores),
            "std_dev": np.std(scores),
            "min": min(scores),
            "max": max(scores),
            "pass_rate": sum(1 for s in scores if s >= 0.6) / len(scores),
            "level_distribution": {
                level.value: sum(1 for l in levels if l == level)
                for level in MasteryLevel
            }
        }

    @staticmethod
    def calculate_progress_trend(
        historical_scores: List[float],
        time_periods: List[datetime]
    ) -> Dict[str, any]:
        """
        Calculate linear regression trend over time.
        """
        if len(historical_scores) < 2:
            return {"trend": "insufficient_data"}

        # Simple linear regression: y = mx + b
        n = len(historical_scores)
        x = range(n)
        y = historical_scores

        # Calculate slope (trend)
        numerator = sum((x[i] - np.mean(x)) * (y[i] - np.mean(y)) for i in range(n))
        denominator = sum((x[i] - np.mean(x)) ** 2 for i in range(n))
        slope = numerator / denominator if denominator != 0 else 0

        # Determine trend direction
        if slope > 0.01:
            trend = "improving"
        elif slope < -0.01:
            trend = "declining"
        else:
            trend = "stable"

        return {
            "trend": trend,
            "slope": slope,
            "projected_next": historical_scores[-1] + slope,
            "r_squared": None  # Could calculate if needed
        }

    @staticmethod
    def identify_component_strengths(analysis: Dict[str, any]) -> List[str]:
        """
        Identify which components are strongest based on contribution analysis.
        """
        if not analysis or "contributions" not in analysis:
            return []

        # Sort by contribution (highest to lowest)
        contributions = sorted(
            analysis["contributions"],
            key=lambda x: x["value"],
            reverse=True
        )

        return [c["component"] for c in contributions[:2]]

    @staticmethod
    def calculate_optimization_path(
        current: ComponentScores,
        target: MasteryLevel,
        weights: MasteryWeights
    ) -> List[Dict[str, any]]:
        """
        Calculate step-by-step optimization path to reach target level.
        """
        calculator = MasteryCalculator(weights)
        current_score = calculator.calculate_mastery_score(current)
        target_threshold = {
            MasteryLevel.NOVICE: 0.0,
            MasteryLevel.DEVELOPING: 0.4,
            MasteryLevel.PROFICIENT: 0.6,
            MasteryLevel.MASTER: 0.8
        }[target]

        if current_score >= target_threshold:
            return []

        improvements = calculator.find_optimal_improvements(current, target)

        # Convert to step-by-step path
        path = []
        running_score = current_score
        for improvement in improvements[:2]:  # Top 2 improvements
            if running_score >= target_threshold:
                break

            gap = target_threshold - running_score
            needed = gap / improvement["score_impact"] if improvement["score_impact"] > 0 else 0
            step_score = min(1.0, running_score + improvement["score_impact"])

            path.append({
                "step": len(path) + 1,
                "improve_component": improvement["component"],
                "target_improvement": improvement["improvement"],
                "expected_score_gain": improvement["score_impact"],
                "projected_score": step_score,
                "still_needed": target_threshold - step_score if step_score < target_threshold else 0
            })

            running_score = step_score

        return path


# Factory function for MCP skill registration
def create_mastery_calculator(weights: Optional[MasteryWeights] = None) -> MasteryCalculator:
    """
    Factory function to create mastery calculator instances.

    This is designed to be called by MCP skill invocation.
    All operations are algorithmic - 0 LLM token cost.
    """
    return MasteryCalculator(weights)


def calculate_mastery_student(
    student_id: str,
    completion: float,
    quiz: float,
    quality: float,
    consistency: float
) -> MasteryResult:
    """
    Convenience function for MCP skill invocation.

    Args:
        student_id: Student identifier
        completion: 0.0-1.0 completion score
        quiz: 0.0-1.0 quiz score
        quality: 0.0-1.0 quality score
        consistency: 0.0-1.0 consistency score

    Returns:
        Complete MasteryResult
    """
    calculator = create_mastery_calculator()
    components = ComponentScores(
        completion=completion,
        quiz=quiz,
        quality=quality,
        consistency=consistency
    )
    return calculator.execute_calculation(student_id, components)