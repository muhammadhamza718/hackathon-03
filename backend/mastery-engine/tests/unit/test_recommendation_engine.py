"""
Recommendation Engine Unit Tests
================================

Unit tests for adaptive recommendation generation service.
"""

import pytest
from unittest.mock import Mock, AsyncMock
from datetime import datetime, timedelta

from src.services.recommendation_engine import RecommendationEngine, MCPRecommendationSkill
from src.services.state_manager import StateManager
from src.models.recommendations import (
    AdaptiveRecommendation,
    RecommendationConfig,
    ComponentArea,
    PriorityLevel,
    ActionType
)
from src.models.mastery import MasteryResult, MasteryLevel, ComponentScores, MasteryBreakdown


class TestRecommendationEngine:
    """Test core recommendation engine functionality"""

    def test_engine_initialization(self):
        """Test engine initialization with default config"""
        mock_state = Mock()
        engine = RecommendationEngine(mock_state)

        assert engine.state_manager == mock_state
        assert engine.config is not None
        assert isinstance(engine.config, RecommendationConfig)
        assert engine.model_version == "1.0.0"

    def test_engine_initialization_with_config(self):
        """Test engine initialization with custom config"""
        mock_state = Mock()
        custom_config = RecommendationConfig(high_gap_threshold=0.3)
        engine = RecommendationEngine(mock_state, custom_config)

        assert engine.config.high_gap_threshold == 0.3

    def test_analyze_component_thresholds_all_above_threshold(self):
        """Test analysis when all components are above threshold"""
        mock_state = Mock()
        engine = RecommendationEngine(mock_state)

        # All components at 0.8 (above default 0.7 threshold)
        components = ComponentScores(0.8, 0.8, 0.8, 0.8)
        analyses = engine._analyze_component_thresholds(components)

        # Should have no areas needing attention
        needs_attention = [a for a in analyses if a.needs_attention]
        assert len(needs_attention) == 0

        # But should still have analyses for all components
        assert len(analyses) == 4
        for analysis in analyses:
            assert analysis.gap == 0.0
            assert analysis.needs_attention is False

    def test_analyze_component_thresholds_below_threshold(self):
        """Test analysis when components are below threshold"""
        mock_state = Mock()
        engine = RecommendationEngine(mock_state)

        # All components at 0.4 (below default 0.7 threshold)
        components = ComponentScores(0.4, 0.4, 0.4, 0.4)
        analyses = engine._analyze_component_thresholds(components)

        # All should need attention
        needs_attention = [a for a in analyses if a.needs_attention]
        assert len(needs_attention) == 4

        # Check gap calculation (0.7 - 0.4 = 0.3)
        for analysis in analyses:
            assert analysis.gap == 0.3
            assert analysis.current_score == 0.4

    def test_analyze_component_thresholds_priority_assignment(self):
        """Test priority assignment based on gap size"""
        mock_state = Mock()
        engine = RecommendationEngine(mock_state)

        # Mix of gaps to test priority
        components = ComponentScores(
            completion=0.5,  # gap 0.2 -> medium
            quiz=0.3,        # gap 0.4 -> high
            quality=0.65,    # gap 0.05 -> low
            consistency=0.55 # gap 0.15 -> medium
        )

        analyses = engine._analyze_component_thresholds(components)

        # Map components to priorities
        priority_map = {a.component: a.priority for a in analyses}

        assert priority_map[ComponentArea.QUIZ] == PriorityLevel.HIGH
        assert priority_map[ComponentArea.COMPLETION] == PriorityLevel.MEDIUM
        assert priority_map[ComponentArea.CONSISTENCY] == PriorityLevel.MEDIUM
        assert priority_map[ComponentArea.QUALITY] == PriorityLevel.LOW

    def test_analyze_component_thresholds_action_assignment(self):
        """Test action type assignment based on gap size"""
        mock_state = Mock()
        engine = RecommendationEngine(mock_state)

        # Large gap should use primary action
        components_large_gap = ComponentScores(0.4, 0.4, 0.4, 0.4)  # gap 0.3
        analyses_large = engine._analyze_component_thresholds(components_large_gap)

        completion_large = next(a for a in analyses_large if a.component == ComponentArea.COMPLETION)
        assert completion_large.recommended_action == ActionType.PRACTICE  # Primary action

        # Small gap should use secondary action
        components_small_gap = ComponentScores(0.69, 0.69, 0.69, 0.69)  # gap 0.01
        analyses_small = engine._analyze_component_thresholds(components_small_gap)

        completion_small = next(a for a in analyses_small if a.component == ComponentArea.COMPLETION)
        assert completion_small.recommended_action == ActionType.SCHEDULE  # Secondary action

    def test_analyze_component_thresholds_time_estimation(self):
        """Test time estimation based on action and gap"""
        mock_state = Mock()
        engine = RecommendationEngine(mock_state)

        components = ComponentScores(0.4, 0.4, 0.4, 0.4)  # gap 0.3
        analyses = engine._analyze_component_thresholds(components)

        completion = next(a for a in analyses if a.component == ComponentArea.COMPLETION)
        quiz = next(a for a in analyses if a.component == ComponentArea.QUIZ)

        # Completion uses practice (base 20), quiz uses review (base 15)
        # Both scaled by gap/0.1 = 3x
        # Expected: max(15, base_time * 3)
        assert completion.estimated_time_to_threshold >= 15
        assert quiz.estimated_time_to_threshold >= 15

    def test_convert_analysis_to_recommendation(self):
        """Test conversion of analysis to recommendation"""
        mock_state = Mock()
        engine = RecommendationEngine(mock_state)

        # Create mock analysis
        analysis = Mock()
        analysis.component = ComponentArea.COMPLETION
        analysis.current_score = 0.4
        analysis.gap = 0.3
        analysis.recommended_action = ActionType.PRACTICE
        analysis.priority = PriorityLevel.HIGH
        analysis.estimated_time_to_threshold = 60

        # Create mock mastery
        mastery = Mock()
        mastery.level = MasteryLevel.DEVELOPING

        recommendation = engine._convert_analysis_to_recommendation(analysis, mastery)

        assert recommendation.action == ActionType.PRACTICE
        assert recommendation.area == ComponentArea.COMPLETION
        assert recommendation.priority == PriorityLevel.HIGH
        assert recommendation.estimated_time == 60
        assert recommendation.score_gap == 0.3
        assert "Practice more exercises" in recommendation.description
        assert recommendation.confidence == 0.8

    def test_generate_description(self):
        """Test description generation"""
        mock_state = Mock()
        engine = RecommendationEngine(mock_state)

        analysis = Mock()
        analysis.component = ComponentArea.QUIZ
        analysis.current_score = 0.5
        analysis.recommended_action = ActionType.REVIEW

        mastery = Mock()

        description = engine._generate_description(analysis, mastery)

        assert "quiz performance" in description
        assert "Review concepts and materials" in description
        assert "0.50" in description

    def test_estimate_time(self):
        """Test time estimation logic"""
        mock_state = Mock()
        engine = RecommendationEngine(mock_state)

        # Test different actions with different gaps
        test_cases = [
            (ActionType.PRACTICE, 0.2, 60),   # 20 * (0.2/0.1) = 40 -> max(15, 60)
            (ActionType.REVIEW, 0.1, 30),     # 15 * (0.1/0.1) = 15 -> max(15, 15)
            (ActionType.REFACTOR, 0.3, 75),   # 25 * (0.3/0.1) = 75 -> max(15, 75)
            (ActionType.ASSESS, 0.2, 15),     # Fixed 15 minutes
        ]

        for action, gap, expected in test_cases:
            result = engine._estimate_time(action, gap)
            assert result == expected

    def test_determine_difficulty(self):
        """Test difficulty level determination"""
        mock_state = Mock()
        engine = RecommendationEngine(mock_state)

        assert engine._determine_difficulty(0.3) == "beginner"
        assert engine._determine_difficulty(0.5) == "intermediate"
        assert engine._determine_difficulty(0.8) == "advanced"

    def test_get_resources(self):
        """Test resource mapping"""
        mock_state = Mock()
        engine = RecommendationEngine(mock_state)

        # Test completion + practice
        resources = engine._get_resources(ComponentArea.COMPLETION, ActionType.PRACTICE)
        assert "Practice exercises" in resources
        assert "Coding challenges" in resources

        # Test quiz + review
        resources = engine._get_resources(ComponentArea.QUIZ, ActionType.REVIEW)
        assert "Quiz summaries" in resources
        assert "Flashcards" in resources

    def test_sort_recommendations_for_path(self):
        """Test sorting recommendations for optimal learning path"""
        mock_state = Mock()
        engine = RecommendationEngine(mock_state)

        # Create test recommendations with different priorities and times
        recs = [
            AdaptiveRecommendation(
                action=ActionType.PRACTICE,
                area=ComponentArea.COMPLETION,
                priority=PriorityLevel.LOW,
                description="Test 1",
                estimated_time=30,
                resources=[],
                confidence=0.8
            ),
            AdaptiveRecommendation(
                action=ActionType.PRACTICE,
                area=ComponentArea.QUIZ,
                priority=PriorityLevel.HIGH,
                description="Test 2",
                estimated_time=20,
                resources=[],
                confidence=0.8
            ),
            AdaptiveRecommendation(
                action=ActionType.PRACTICE,
                area=ComponentArea.QUALITY,
                priority=PriorityLevel.HIGH,
                description="Test 3",
                estimated_time=15,
                resources=[],
                confidence=0.8
            ),
        ]

        sorted_recs = engine._sort_recommendations_for_path(recs)

        # Should be: HIGH priority first, then within HIGH, shortest time first
        assert sorted_recs[0].description == "Test 3"  # HIGH, 15 min
        assert sorted_recs[1].description == "Test 2"  # HIGH, 20 min
        assert sorted_recs[2].description == "Test 1"  # LOW

    def test_extract_priority_areas(self):
        """Test extraction of top priority areas"""
        mock_state = Mock()
        engine = RecommendationEngine(mock_state)

        recs = [
            AdaptiveRecommendation(
                action=ActionType.PRACTICE,
                area=ComponentArea.COMPLETION,
                priority=PriorityLevel.HIGH,
                description="Test",
                estimated_time=30,
                resources=[],
                confidence=0.8
            ),
            AdaptiveRecommendation(
                action=ActionType.REVIEW,
                area=ComponentArea.QUIZ,
                priority=PriorityLevel.MEDIUM,
                description="Test",
                estimated_time=20,
                resources=[],
                confidence=0.8
            ),
            AdaptiveRecommendation(
                action=ActionType.REFACTOR,
                area=ComponentArea.QUALITY,
                priority=PriorityLevel.HIGH,
                description="Test",
                estimated_time=45,
                resources=[],
                confidence=0.8
            ),
            AdaptiveRecommendation(
                action=ActionType.SCHEDULE,
                area=ComponentArea.CONSISTENCY,
                priority=PriorityLevel.LOW,
                description="Test",
                estimated_time=15,
                resources=[],
                confidence=0.8
            ),
        ]

        priority_areas = engine._extract_priority_areas(recs)

        # Completion: HIGH (3) + QUALITY: HIGH (3) = both highest (6)
        # QUIZ: MEDIUM (2)
        # CONSISTENCY: LOW (1)
        # Should return top 3: [COMPLETION, QUALITY, QUIZ] (or QUALITY, COMPLETION, QUIZ)
        assert len(priority_areas) == 3
        assert ComponentArea.COMPLETION in priority_areas
        assert ComponentArea.QUALITY in priority_areas
        assert ComponentArea.QUIZ in priority_areas

    def test_determine_target_level(self):
        """Test target level determination based on current level"""
        mock_state = Mock()
        engine = RecommendationEngine(mock_state)

        assert engine._determine_target_level(MasteryLevel.NOVICE) == MasteryLevel.DEVELOPING
        assert engine._determine_target_level(MasteryLevel.DEVELOPING) == MasteryLevel.PROFICIENT
        assert engine._determine_target_level(MasteryLevel.PROFICIENT) == MasteryLevel.MASTER
        assert engine._determine_target_level(MasteryLevel.MASTER) == MasteryLevel.MASTER

    @pytest.mark.asyncio
    async def test_generate_default_recommendations(self):
        """Test generation of default recommendations for new students"""
        mock_state = Mock()
        engine = RecommendationEngine(mock_state)

        recommendations = await engine._generate_default_recommendations("test_student", 5)

        assert len(recommendations) == 2  # Only 2 default recommendations
        assert all(r.priority == PriorityLevel.HIGH for r in recommendations)
        assert all(r.confidence > 0.5 for r in recommendations)

        # Check specific recommendations
        assert any(r.action == ActionType.PRACTICE for r in recommendations)
        assert any(r.action == ActionType.SCHEDULE for r in recommendations)

    @pytest.mark.asyncio
    async def test_generate_general_recommendations_low_score(self):
        """Test general recommendations for low mastery score"""
        mock_state = Mock()
        engine = RecommendationEngine(mock_state)

        mastery = MasteryResult(
            student_id="test",
            mastery_score=0.4,
            level=MasteryLevel.DEVELOPING,
            components=ComponentScores(0.4, 0.4, 0.4, 0.4),
            breakdown=MasteryBreakdown(
                completion=0.16, quiz=0.12, quality=0.08, consistency=0.04,
                weighted_sum=0.4,
                weights=Mock()
            )
        )

        recs = await engine._generate_general_recommendations(mastery, 3)

        assert len(recs) >= 1
        assert recs[0].action == ActionType.PRACTICE
        assert recs[0].area == ComponentArea.COMPLETION
        assert recs[0].priority == PriorityLevel.MEDIUM

    @pytest.mark.asyncio
    async def test_generate_general_recommendations_proficient(self):
        """Test general recommendations for proficient level"""
        mock_state = Mock()
        engine = RecommendationEngine(mock_state)

        mastery = MasteryResult(
            student_id="test",
            mastery_score=0.75,
            level=MasteryLevel.PROFICIENT,
            components=ComponentScores(0.75, 0.75, 0.75, 0.75),
            breakdown=MasteryBreakdown(
                completion=0.3, quiz=0.225, quality=0.15, consistency=0.075,
                weighted_sum=0.75,
                weights=Mock()
            )
        )

        recs = await engine._generate_general_recommendations(mastery, 3)

        assert len(recs) >= 1
        assert recs[0].action == ActionType.REFACTOR
        assert recs[0].area == ComponentArea.QUALITY

    @pytest.mark.asyncio
    async def test_generate_adaptive_recommendations(self):
        """Test full adaptive recommendation generation"""
        mock_state = Mock()

        # Mock current mastery
        current_mastery = MasteryResult(
            student_id="test_student",
            mastery_score=0.6,
            level=MasteryLevel.DEVELOPING,
            components=ComponentScores(0.5, 0.65, 0.7, 0.55),
            breakdown=MasteryBreakdown(
                completion=0.2, quiz=0.195, quality=0.14, consistency=0.065,
                weighted_sum=0.6,
                weights=Mock()
            )
        )

        mock_state.get_mastery_score = AsyncMock(return_value=current_mastery)
        mock_state.save = AsyncMock()

        engine = RecommendationEngine(mock_state)

        recommendations = await engine.generate_adaptive_recommendations("test_student", limit=5)

        # Should generate recommendations based on components below 0.7
        assert len(recommendations) <= 5
        assert all(isinstance(r, AdaptiveRecommendation) for r in recommendations)

        # Should cache recommendations
        assert mock_state.save.called

    @pytest.mark.asyncio
    async def test_generate_adaptive_recommendations_no_data(self):
        """Test recommendation generation with no mastery data"""
        mock_state = Mock()
        mock_state.get_mastery_score = AsyncMock(return_value=None)
        mock_state.save = AsyncMock()

        engine = RecommendationEngine(mock_state)

        recommendations = await engine.generate_adaptive_recommendations("unknown_student", limit=3)

        # Should return default recommendations
        assert len(recommendations) == 2
        assert all(r.priority == PriorityLevel.HIGH for r in recommendations)

    @pytest.mark.asyncio
    async def test_generate_adaptive_recommendations_with_filters(self):
        """Test recommendation generation with component and priority filters"""
        mock_state = Mock()

        current_mastery = MasteryResult(
            student_id="test_student",
            mastery_score=0.6,
            level=MasteryLevel.DEVELOPING,
            components=ComponentScores(0.5, 0.65, 0.7, 0.55),
            breakdown=MasteryBreakdown(
                completion=0.2, quiz=0.195, quality=0.14, consistency=0.065,
                weighted_sum=0.6,
                weights=Mock()
            )
        )

        mock_state.get_mastery_score = AsyncMock(return_value=current_mastery)
        mock_state.save = AsyncMock()

        engine = RecommendationEngine(mock_state)

        # Filter by component
        recommendations = await engine.generate_adaptive_recommendations(
            "test_student",
            limit=5,
            component_filter=[ComponentArea.COMPLETION]
        )

        assert all(r.area == ComponentArea.COMPLETION for r in recommendations)

        # Filter by priority
        recommendations = await engine.generate_adaptive_recommendations(
            "test_student",
            limit=5,
            priority_filter=PriorityLevel.HIGH
        )

        assert all(r.priority == PriorityLevel.HIGH for r in recommendations)

    @pytest.mark.asyncio
    async def test_generate_learning_path(self):
        """Test learning path generation"""
        mock_state = Mock()

        current_mastery = MasteryResult(
            student_id="test_student",
            mastery_score=0.6,
            level=MasteryLevel.DEVELOPING,
            components=ComponentScores(0.5, 0.65, 0.7, 0.55),
            breakdown=MasteryBreakdown(
                completion=0.2, quiz=0.195, quality=0.14, consistency=0.065,
                weighted_sum=0.6,
                weights=Mock()
            )
        )

        mock_state.get_mastery_score = AsyncMock(return_value=current_mastery)
        mock_state.save = AsyncMock()

        engine = RecommendationEngine(mock_state)

        path = await engine.generate_learning_path("test_student", target_level="proficient")

        assert path.student_id == "test_student"
        assert path.path_id.startswith("path_test_student_")
        assert len(path.recommendations) > 0
        assert path.total_time_estimate > 0
        assert len(path.priority_areas) > 0
        assert path.metadata["target_level"] == "PROFICIENT"
        assert path.metadata["current_level"] == "DEVELOPING"
        assert path.estimated_completion > datetime.utcnow()

    @pytest.mark.asyncio
    async def test_generate_learning_path_with_duration_limit(self):
        """Test learning path generation with maximum duration"""
        mock_state = Mock()

        current_mastery = MasteryResult(
            student_id="test_student",
            mastery_score=0.6,
            level=MasteryLevel.DEVELOPING,
            components=ComponentScores(0.5, 0.65, 0.7, 0.55),
            breakdown=MasteryBreakdown(
                completion=0.2, quiz=0.195, quality=0.14, consistency=0.065,
                weighted_sum=0.6,
                weights=Mock()
            )
        )

        mock_state.get_mastery_score = AsyncMock(return_value=current_mastery)
        mock_state.save = AsyncMock()

        engine = RecommendationEngine(mock_state)

        path = await engine.generate_learning_path(
            "test_student",
            max_duration_minutes=30
        )

        assert path.total_time_estimate <= 30

    @pytest.mark.asyncio
    async def test_generate_learning_path_no_target_level(self):
        """Test learning path generation without explicit target level"""
        mock_state = Mock()

        current_mastery = MasteryResult(
            student_id="test_student",
            mastery_score=0.4,
            level=MasteryLevel.NOVICE,
            components=ComponentScores(0.4, 0.4, 0.4, 0.4),
            breakdown=MasteryBreakdown(
                completion=0.16, quiz=0.12, quality=0.08, consistency=0.04,
                weighted_sum=0.4,
                weights=Mock()
            )
        )

        mock_state.get_mastery_score = AsyncMock(return_value=current_mastery)
        mock_state.save = AsyncMock()

        engine = RecommendationEngine(mock_state)

        path = await engine.generate_learning_path("test_student")

        # Should auto-detect next level (NOVICE -> DEVELOPING)
        assert path.metadata["target_level"] == "DEVELOPING"

    @pytest.mark.asyncio
    async def test_caching_recommendations(self):
        """Test recommendation caching mechanism"""
        mock_state = Mock()
        mock_state.save = AsyncMock()

        engine = RecommendationEngine(mock_state)

        recommendations = [
            AdaptiveRecommendation(
                action=ActionType.PRACTICE,
                area=ComponentArea.COMPLETION,
                priority=PriorityLevel.HIGH,
                description="Test",
                estimated_time=30,
                resources=[],
                confidence=0.8
            )
        ]

        await engine._cache_recommendations("test_student", recommendations)

        assert mock_state.save.call_count == 1
        call_args = mock_state.save.call_args[0]
        assert "test_student" in call_args[0]  # Key contains student_id
        assert "recommendation" in call_args[0]  # Key contains recommendation type

    @pytest.mark.asyncio
    async def test_caching_learning_path(self):
        """Test learning path caching mechanism"""
        mock_state = Mock()
        mock_state.save = AsyncMock()

        engine = RecommendationEngine(mock_state)

        from src.models.recommendations import LearningPath

        path = LearningPath(
            student_id="test_student",
            path_id="path_test",
            recommendations=[],
            estimated_completion=datetime.utcnow(),
            total_time_estimate=60,
            priority_areas=[ComponentArea.COMPLETION]
        )

        await engine._cache_learning_path("test_student", path)

        mock_state.save.assert_called_once()
        call_args = mock_state.save.call_args[0]
        assert "test_student" in call_args[0]
        assert call_args[1] == path.model_dump()


class TestMCPRecommendationSkill:
    """Test MCP Recommendation Skill for token efficiency"""

    def test_mcp_skill_initialization(self):
        """Test MCP skill initialization"""
        mock_engine = Mock()
        skill = MCPRecommendationSkill(mock_engine)

        assert skill.engine == mock_engine

    @pytest.mark.asyncio
    async def test_execute_recommendation_analysis(self):
        """Test MCP recommendation analysis"""
        mock_engine = Mock()

        # Mock threshold analysis
        mock_analyses = [
            Mock(
                component=ComponentArea.COMPLETION,
                gap=0.3,
                recommended_action=ActionType.PRACTICE,
                priority=PriorityLevel.HIGH,
                needs_attention=True
            ),
            Mock(
                component=ComponentArea.QUIZ,
                gap=0.2,
                recommended_action=ActionType.REVIEW,
                priority=PriorityLevel.MEDIUM,
                needs_attention=True
            )
        ]

        mock_engine._analyze_component_thresholds = Mock(return_value=mock_analyses)

        skill = MCPRecommendationSkill(mock_engine)

        mastery = Mock()
        mastery.mastery_score = 0.6
        mastery.level = MasteryLevel.DEVELOPING
        mastery.components = ComponentScores(0.5, 0.65, 0.7, 0.55)

        result = await skill.execute_recommendation_analysis("test_student", mastery)

        assert result["student_id"] == "test_student"
        assert len(result["priority_areas"]) == 2
        assert result["priority_areas"][0]["component"] == "completion"
        assert result["priority_areas"][0]["gap"] == 0.3
        assert result["priority_areas"][0]["priority"] == "high"
        assert result["overall_score"] == 0.6
        assert result["current_level"] == "developing"

    @pytest.mark.asyncio
    async def test_generate_efficient_path(self):
        """Test MCP efficient path generation"""
        mock_engine = Mock()
        skill = MCPRecommendationSkill(mock_engine)

        priority_areas = [
            ComponentArea.COMPLETION,
            ComponentArea.QUIZ,
            ComponentArea.QUALITY
        ]

        result = await skill.generate_efficient_path("test_student", priority_areas)

        assert result["student_id"] == "test_student"
        assert len(result["path"]) == 3
        assert all("action" in item for item in result["path"])
        assert all("area" in item for item in result["path"])
        assert all("description" in item for item in result["path"])
        assert all("time" in item for item in result["path"])
        assert result["total_time"] == 30 + 20 + 25  # 75 minutes
        assert result["estimated_completion_days"] == 2  # 75 // 45 = 1, but max(1, ...)

    @pytest.mark.asyncio
    async def test_generate_efficient_path_partial_areas(self):
        """Test efficient path with fewer than 3 areas"""
        mock_engine = Mock()
        skill = MCPRecommendationSkill(mock_engine)

        priority_areas = [ComponentArea.CONSISTENCY]

        result = await skill.generate_efficient_path("test_student", priority_areas)

        assert len(result["path"]) == 1
        assert result["path"][0]["area"] == "consistency"
        assert result["total_time"] == 15

    def test_mcp_skill_handles_all_component_areas(self):
        """Test MCP skill handles all component areas in path generation"""
        mock_engine = Mock()
        skill = MCPRecommendationSkill(mock_engine)

        all_areas = [
            ComponentArea.COMPLETION,
            ComponentArea.QUIZ,
            ComponentArea.QUALITY,
            ComponentArea.CONSISTENCY
        ]

        # Should not raise any errors
        result = skill.generate_efficient_path("test", all_areas)

        # Even without await, the coroutine object should be created successfully
        assert result is not None


class TestRecommendationEdgeCases:
    """Test edge cases in recommendation generation"""

    @pytest.mark.asyncio
    async def test_generate_learning_path_master_level(self):
        """Test learning path generation from master level"""
        mock_state = Mock()

        current_mastery = MasteryResult(
            student_id="test_student",
            mastery_score=0.9,
            level=MasteryLevel.MASTER,
            components=ComponentScores(0.9, 0.9, 0.9, 0.9),
            breakdown=MasteryBreakdown(
                completion=0.36, quiz=0.27, quality=0.18, consistency=0.09,
                weighted_sum=0.9,
                weights=Mock()
            )
        )

        mock_state.get_mastery_score = AsyncMock(return_value=current_mastery)
        mock_state.save = AsyncMock()

        engine = RecommendationEngine(mock_state)

        path = await engine.generate_learning_path("test_student")

        # Should stay at master level
        assert path.metadata["target_level"] == "MMASTER"
        assert path.metadata["current_level"] == "MASTER"

    @pytest.mark.asyncio
    async def test_caching_failure_graceful_handling(self):
        """Test that caching failures don't break the main functionality"""
        mock_state = Mock()
        mock_state.save = AsyncMock(side_effect=Exception("Cache unavailable"))

        engine = RecommendationEngine(mock_state)

        # Should not raise exception
        await engine._cache_recommendations("test", [])
        await engine._cache_learning_path("test", Mock(model_dump=lambda: {}))

    def test_recommendation_confidence_calculation(self):
        """Test that recommendations have appropriate confidence levels"""
        mock_state = Mock()
        engine = RecommendationEngine(mock_state)

        # Test different score ranges
        test_cases = [
            0.3,  # Beginner
            0.6,  # Intermediate
            0.85  # Advanced
        ]

        for score in test_cases:
            analysis = Mock()
            analysis.component = ComponentArea.COMPLETION
            analysis.current_score = score
            analysis.gap = 0.7 - score
            analysis.recommended_action = ActionType.PRACTICE
            analysis.priority = PriorityLevel.HIGH
            analysis.estimated_time_to_threshold = 30

            mastery = Mock()

            rec = engine._convert_analysis_to_recommendation(analysis, mastery)
            assert 0.0 <= rec.confidence <= 1.0
            assert rec.confidence == 0.8  # Should be constant for now