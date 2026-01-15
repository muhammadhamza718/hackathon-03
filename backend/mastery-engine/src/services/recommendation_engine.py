"""
Recommendation Engine Service
==============================

Adaptive learning recommendation generation based on mastery analysis.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Tuple

from src.models.recommendations import (
    AdaptiveRecommendation,
    LearningPath,
    RecommendationQuery,
    LearningPathQuery,
    ComponentThresholdAnalysis,
    RecommendationConfig,
    ActionType,
    PriorityLevel,
    ComponentArea
)
from src.models.mastery import MasteryResult, ComponentScores, MasteryLevel, StateKeyPatterns
from src.services.state_manager import StateManager

logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Adaptive recommendation generation engine"""

    def __init__(self, state_manager: StateManager, config: Optional[RecommendationConfig] = None):
        self.state_manager = state_manager
        self.config = config or RecommendationConfig()
        self.model_version = "1.0.0"

    async def generate_adaptive_recommendations(
        self,
        student_id: str,
        limit: int = 5,
        priority_filter: Optional[PriorityLevel] = None,
        component_filter: Optional[List[ComponentArea]] = None
    ) -> List[AdaptiveRecommendation]:
        """
        Generate adaptive recommendations based on current mastery state

        Args:
            student_id: Student identifier
            limit: Maximum number of recommendations
            priority_filter: Optional priority filter
            component_filter: Optional component area filter

        Returns:
            List of personalized recommendations
        """
        logger.info(f"Generating recommendations for {student_id}")

        # Get current mastery
        current_mastery = await self.state_manager.get_mastery_score(student_id)
        if not current_mastery:
            logger.warning(f"No mastery data found for {student_id}")
            return await self._generate_default_recommendations(student_id, limit)

        # Analyze components
        analyses = self._analyze_component_thresholds(current_mastery.components)

        # Filter by component if specified
        if component_filter:
            analyses = [a for a in analyses if a.component in component_filter]

        # Sort by gap size (largest gaps first)
        analyses.sort(key=lambda x: x.gap, reverse=True)

        # Generate recommendations
        recommendations = []
        for analysis in analyses[:limit]:
            if analysis.needs_attention:
                recommendation = self._convert_analysis_to_recommendation(analysis, current_mastery)
                recommendations.append(recommendation)

        # Apply priority filter if specified
        if priority_filter:
            recommendations = [r for r in recommendations if r.priority == priority_filter]

        # Add some general recommendations if we need more
        if len(recommendations) < limit:
            general_recs = await self._generate_general_recommendations(
                current_mastery, limit - len(recommendations)
            )
            recommendations.extend(general_recs)

        # Cache the recommendations
        await self._cache_recommendations(student_id, recommendations)

        logger.info(f"Generated {len(recommendations)} recommendations for {student_id}")
        return recommendations

    async def generate_learning_path(
        self,
        student_id: str,
        target_level: Optional[str] = None,
        max_duration_minutes: Optional[int] = None
    ) -> LearningPath:
        """
        Generate a comprehensive learning path

        Args:
            student_id: Student identifier
            target_level: Target mastery level
            max_duration_minutes: Maximum path duration

        Returns:
            Complete learning path
        """
        logger.info(f"Generating learning path for {student_id}")

        # Get current mastery
        current_mastery = await self.state_manager.get_mastery_score(student_id)
        if not current_mastery:
            raise ValueError(f"No mastery data found for {student_id}")

        # Determine target level
        if target_level:
            target_enum = getattr(MasteryLevel, target_level.upper(), MasteryLevel.MASTER)
        else:
            target_enum = self._determine_target_level(current_mastery.level)

        # Generate recommendations
        all_recommendations = await self.generate_adaptive_recommendations(student_id, limit=10)

        # Sort by priority and estimated time
        sorted_recs = self._sort_recommendations_for_path(all_recommendations)

        # Filter by duration if specified
        if max_duration_minutes:
            filtered_recs = []
            total_time = 0
            for rec in sorted_recs:
                if rec.estimated_time and (total_time + rec.estimated_time) <= max_duration_minutes:
                    filtered_recs.append(rec)
                    total_time += rec.estimated_time
            recommendations = filtered_recs
        else:
            recommendations = sorted_recs
            total_time = sum(r.estimated_time or 0 for r in recommendations)

        # Calculate estimated completion
        # Assume 2 hours of learning per day
        daily_minutes = 120
        days_needed = max(1, total_time // daily_minutes)
        completion_date = datetime.utcnow() + timedelta(days=days_needed)

        # Determine priority areas
        priority_areas = self._extract_priority_areas(recommendations)

        path = LearningPath(
            student_id=student_id,
            path_id=f"path_{student_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M')}",
            recommendations=recommendations,
            estimated_completion=completion_date,
            total_time_estimate=total_time,
            priority_areas=priority_areas,
            metadata={
                "target_level": target_enum.value,
                "current_level": current_mastery.level.value,
                "days_estimate": days_needed,
                "model_version": self.model_version
            }
        )

        # Cache learning path
        await self._cache_learning_path(student_id, path)

        logger.info(f"Generated learning path for {student_id}: {len(recommendations)} recommendations, {total_time} minutes")
        return path

    def _analyze_component_thresholds(self, components: ComponentScores) -> List[ComponentThresholdAnalysis]:
        """Analyze which components need attention based on thresholds"""
        analyses = []

        # Define thresholds and corresponding actions
        component_specs = {
            ComponentArea.COMPLETION: {
                "threshold": self.config.completion_threshold,
                "primary_action": ActionType.PRACTICE,
                "secondary_action": ActionType.SCHEDULE
            },
            ComponentArea.QUIZ: {
                "threshold": self.config.quiz_threshold,
                "primary_action": ActionType.REVIEW,
                "secondary_action": ActionType.ASSESS
            },
            ComponentArea.QUALITY: {
                "threshold": self.config.quality_threshold,
                "primary_action": ActionType.REFACTOR,
                "secondary_action": ActionType.LEARN_NEW
            },
            ComponentArea.CONSISTENCY: {
                "threshold": self.config.consistency_threshold,
                "primary_action": ActionType.SCHEDULE,
                "secondary_action": ActionType.PRACTICE
            }
        }

        # Component values
        component_values = {
            ComponentArea.COMPLETION: components.completion,
            ComponentArea.QUIZ: components.quiz,
            ComponentArea.QUALITY: components.quality,
            ComponentArea.CONSISTENCY: components.consistency
        }

        for area, value in component_values.items():
            spec = component_specs[area]
            gap = max(0, spec["threshold"] - value)
            needs_attention = gap > 0

            # Determine priority
            if gap >= self.config.high_gap_threshold:
                priority = PriorityLevel.HIGH
            elif gap >= self.config.medium_gap_threshold:
                priority = PriorityLevel.MEDIUM
            else:
                priority = PriorityLevel.LOW

            # Determine action based on gap size
            action = spec["primary_action"] if gap > 0.1 else spec["secondary_action"]

            # Estimate time
            time_estimate = self._estimate_time(action, gap)

            analysis = ComponentThresholdAnalysis(
                component=area,
                current_score=round(value, 3),
                gap=round(gap, 3),
                needs_attention=needs_attention,
                recommended_action=action,
                priority=priority,
                estimated_time_to_threshold=time_estimate
            )

            analyses.append(analysis)

        return analyses

    def _convert_analysis_to_recommendation(
        self,
        analysis: ComponentThresholdAnalysis,
        current_mastery: MasteryResult
    ) -> AdaptiveRecommendation:
        """Convert threshold analysis to adaptive recommendation"""
        description = self._generate_description(analysis, current_mastery)
        difficulty = self._determine_difficulty(analysis.current_score)

        return AdaptiveRecommendation(
            action=analysis.recommended_action,
            area=analysis.component,
            priority=analysis.priority,
            description=description,
            estimated_time=analysis.estimated_time_to_threshold,
            resources=self._get_resources(analysis.component, analysis.recommended_action),
            difficulty=difficulty,
            score_gap=analysis.gap,
            confidence=0.8
        )

    def _generate_description(self, analysis: ComponentThresholdAnalysis, mastery: MasteryResult) -> str:
        """Generate human-readable recommendation description"""
        component_names = {
            ComponentArea.COMPLETION: "exercise completion rate",
            ComponentArea.QUIZ: "quiz performance",
            ComponentArea.QUALITY: "work quality",
            ComponentArea.CONSISTENCY: "learning consistency"
        }

        action_descriptions = {
            ActionType.PRACTICE: "Practice more exercises",
            ActionType.REVIEW: "Review concepts and materials",
            ActionType.REFACTOR: "Refactor and improve existing work",
            ActionType.SCHEDULE: "Schedule regular study sessions",
            ActionType.LEARN_NEW: "Learn new concepts",
            ActionType.ASSESS: "Take assessment to gauge understanding"
        }

        component_name = component_names[analysis.component]
        action_desc = action_descriptions[analysis.recommended_action]

        return f"{action_desc} to improve {component_name} from {analysis.current_score:.2f} to at least 0.7"

    def _estimate_time(self, action: ActionType, gap: float) -> int:
        """Estimate time needed based on action type and gap"""
        base_times = {
            ActionType.PRACTICE: self.config.practice_time_per_gap,
            ActionType.REVIEW: self.config.review_time_per_gap,
            ActionType.REFACTOR: self.config.refactor_time_per_gap,
            ActionType.SCHEDULE: self.config.learn_new_time,
            ActionType.LEARN_NEW: self.config.learn_new_time,
            ActionType.ASSESS: 15  # Fixed 15 minutes for assessment
        }

        base_time = base_times.get(action, 20)
        # Scale by gap size, min 15 minutes
        estimated = max(15, int(base_time * (gap / 0.1)))
        return estimated

    def _determine_difficulty(self, current_score: float) -> str:
        """Determine difficulty level based on current score"""
        if current_score < 0.4:
            return "beginner"
        elif current_score < 0.7:
            return "intermediate"
        else:
            return "advanced"

    def _get_resources(self, area: ComponentArea, action: ActionType) -> List[str]:
        """Get relevant learning resources based on area and action"""
        base_resources = {
            ComponentArea.COMPLETION: {
                ActionType.PRACTICE: ["Practice exercises", "Coding challenges", "Project work"],
                ActionType.SCHEDULE: ["Study calendar", "Reminders", "Progress tracker"]
            },
            ComponentArea.QUIZ: {
                ActionType.REVIEW: ["Quiz summaries", "Concept notes", "Flashcards"],
                ActionType.ASSESS: ["Practice quizzes", "Self-assessment tools"]
            },
            ComponentArea.QUALITY: {
                ActionType.REFACTOR: ["Code review checklist", "Quality standards", "Peer review"],
                ActionType.LEARN_NEW: ["Best practices guide", "Design patterns", "Quality metrics"]
            },
            ComponentArea.CONSISTENCY: {
                ActionType.SCHEDULE: ["Habit tracker", "Daily reminders", "Study plan"],
                ActionType.PRACTICE: ["Daily exercises", "Quick wins", "Short sessions"]
            }
        }

        return base_resources.get(area, {}).get(action, ["General learning resources"])

    def _sort_recommendations_for_path(self, recommendations: List[AdaptiveRecommendation]) -> List[AdaptiveRecommendation]:
        """Sort recommendations for optimal learning path"""
        priority_weight = {PriorityLevel.HIGH: 3, PriorityLevel.MEDIUM: 2, PriorityLevel.LOW: 1}

        # Sort by priority (descending) and then by estimated time (ascending)
        return sorted(
            recommendations,
            key=lambda r: (priority_weight.get(r.priority, 0), -r.estimated_time if r.estimated_time else 0),
            reverse=True
        )

    def _extract_priority_areas(self, recommendations: List[AdaptiveRecommendation]) -> List[ComponentArea]:
        """Extract priority areas from recommendations"""
        areas = {}
        for rec in recommendations:
            if rec.area not in areas:
                areas[rec.area] = 0
            priority_weight = {PriorityLevel.HIGH: 3, PriorityLevel.MEDIUM: 2, PriorityLevel.LOW: 1}
            areas[rec.area] += priority_weight.get(rec.priority, 0)

        # Return top 3 areas
        sorted_areas = sorted(areas.items(), key=lambda x: x[1], reverse=True)
        return [area for area, score in sorted_areas[:3]]

    def _determine_target_level(self, current_level: MasteryLevel) -> MasteryLevel:
        """Determine appropriate target level based on current level"""
        if current_level == MasteryLevel.NOVICE:
            return MasteryLevel.DEVELOPING
        elif current_level == MasteryLevel.DEVELOPING:
            return MasteryLevel.PROFICIENT
        elif current_level == MasteryLevel.PROFICIENT:
            return MasteryLevel.MASTER
        else:
            return MasteryLevel.MASTER  # Already at master level

    async def _generate_default_recommendations(self, student_id: str, limit: int) -> List[AdaptiveRecommendation]:
        """Generate default recommendations when no mastery data exists"""
        return [
            AdaptiveRecommendation(
                action=ActionType.PRACTICE,
                area=ComponentArea.COMPLETION,
                priority=PriorityLevel.HIGH,
                description="Start with basic exercises to build completion rate",
                estimated_time=30,
                resources=["Beginner exercises", "Getting started guide"],
                difficulty="beginner",
                confidence=0.5
            ),
            AdaptiveRecommendation(
                action=ActionType.SCHEDULE,
                area=ComponentArea.CONSISTENCY,
                priority=PriorityLevel.HIGH,
                description="Establish regular study schedule for consistency",
                estimated_time=15,
                resources=["Study plan template", "Habit tracker"],
                difficulty="beginner",
                confidence=0.6
            )
        ][:limit]

    async def _generate_general_recommendations(
        self,
        mastery: MasteryResult,
        count: int
    ) -> List[AdaptiveRecommendation]:
        """Generate general recommendations based on overall mastery"""
        general_recs = []

        if mastery.mastery_score < 0.5:
            general_recs.append(AdaptiveRecommendation(
                action=ActionType.PRACTICE,
                area=ComponentArea.COMPLETION,
                priority=PriorityLevel.MEDIUM,
                description="Focus on consistent practice to build foundation",
                estimated_time=45,
                resources=["Practice sets", "Daily challenges"],
                difficulty="beginner"
            ))
        elif mastery.level == MasteryLevel.PROFICIENT:
            general_recs.append(AdaptiveRecommendation(
                action=ActionType.REFACTOR,
                area=ComponentArea.QUALITY,
                priority=PriorityLevel.MEDIUM,
                description="Work on improving code quality and efficiency",
                estimated_time=30,
                resources=["Quality guidelines", "Refactoring techniques"],
                difficulty="intermediate"
            ))

        return general_recs[:count]

    async def _cache_recommendations(self, student_id: str, recommendations: List[AdaptiveRecommendation]):
        """Cache recommendations in state store"""
        try:
            for i, rec in enumerate(recommendations):
                timestamp = datetime.utcnow() + timedelta(seconds=i)
                key = StateKeyPatterns.recommendation(student_id, timestamp)
                await self.state_manager.save(key, rec.model_dump(), ttl_hours=24)
        except Exception as e:
            logger.warning(f"Failed to cache recommendations for {student_id}: {e}")

    async def _cache_learning_path(self, student_id: str, path: LearningPath):
        """Cache learning path in state store"""
        try:
            key = StateKeyPatterns.learning_path(student_id)
            await self.state_manager.save(key, path.model_dump(), ttl_hours=72)  # 3 days
        except Exception as e:
            logger.warning(f"Failed to cache learning path for {student_id}: {e}")


class MCPRecommendationSkill:
    """
    MCP Skill for efficient recommendation generation

    This skill implements the MCP pattern for token efficiency.
    """

    def __init__(self, engine: RecommendationEngine):
        self.engine = engine

    async def execute_recommendation_analysis(
        self,
        student_id: str,
        current_mastery: MasteryResult
    ) -> Dict[str, Any]:
        """
        Execute recommendation analysis via MCP skill

        Token-efficient analysis using predefined algorithms
        """
        # Perform threshold analysis (minimal tokens)
        analyses = self.engine._analyze_component_thresholds(current_mastery.components)

        # Convert to efficient response format
        return {
            "student_id": student_id,
            "timestamp": datetime.utcnow().isoformat(),
            "priority_areas": [
                {
                    "component": analysis.component.value,
                    "gap": analysis.gap,
                    "action": analysis.recommended_action.value,
                    "priority": analysis.priority.value
                }
                for analysis in analyses
                if analysis.needs_attention
            ],
            "overall_score": current_mastery.mastery_score,
            "current_level": current_mastery.level.value
        }

    async def generate_efficient_path(
        self,
        student_id: str,
        priority_areas: List[ComponentArea]
    ) -> Dict[str, Any]:
        """
        Generate efficient learning path recommendation

        Uses pattern matching and predefined logic
        """
        # Pattern-based recommendations
        path_elements = []
        for area in priority_areas[:3]:  # Top 3 areas
            if area == ComponentArea.COMPLETION:
                path_elements.append({
                    "action": "practice",
                    "area": "completion",
                    "description": "Complete daily exercises",
                    "time": 30
                })
            elif area == ComponentArea.QUIZ:
                path_elements.append({
                    "action": "review",
                    "area": "quiz",
                    "description": "Review quiz concepts",
                    "time": 20
                })
            elif area == ComponentArea.QUALITY:
                path_elements.append({
                    "action": "refactor",
                    "area": "quality",
                    "description": "Improve code quality",
                    "time": 25
                })
            elif area == ComponentArea.CONSISTENCY:
                path_elements.append({
                    "action": "schedule",
                    "area": "consistency",
                    "description": "Establish study routine",
                    "time": 15
                })

        total_time = sum(item["time"] for item in path_elements)

        return {
            "student_id": student_id,
            "path": path_elements,
            "total_time": total_time,
            "daily_commitment": "30-45 minutes",
            "estimated_completion_days": max(1, total_time // 45)
        }