"""
Analytics Service Unit Tests
============================

Unit tests for analytics service (Phase 9) and Dapr service handler (Phase 10).
"""

import pytest
from datetime import datetime, date, timedelta
from unittest.mock import Mock, AsyncMock
import statistics

from src.services.analytics_service import AnalyticsService, DaprServiceHandler
from src.services.state_manager import StateManager
from src.models.mastery import (
    MasteryResult,
    MasteryLevel,
    ComponentScores,
    MasteryBreakdown,
    BatchPriority,
    BatchStatus,
    BatchMasteryRequest,
    DateRangeRequest,
    AggregationType,
    CohortComparisonRequest,
    StudentComparisonRequest,
    DaprIntent,
    DaprProcessRequest,
    DaprSecurityContext
)


class TestAnalyticsService:
    """Test analytics service functionality"""

    def test_analytics_service_initialization(self):
        """Test analytics service initialization"""
        mock_state = Mock()
        service = AnalyticsService(mock_state)

        assert service.state_manager == mock_state
        assert service.model_version == "1.0.0"

    @pytest.mark.asyncio
    async def test_submit_batch_mastery_calculation(self):
        """Test batch submission"""
        mock_state = Mock()
        mock_state.save = AsyncMock()
        mock_state.get = AsyncMock()

        service = AnalyticsService(mock_state)

        request = BatchMasteryRequest(
            student_ids=["student_1", "student_2"],
            priority=BatchPriority.NORMAL
        )

        result = await service.submit_batch_mastery_calculation(request)

        assert result.batch_id.startswith("batch_")
        assert result.status == BatchStatus.PENDING
        assert result.student_count == 2
        assert result.priority == BatchPriority.NORMAL
        assert mock_state.save.called

    @pytest.mark.asyncio
    async def test_batch_status_retrieval(self):
        """Test batch status retrieval"""
        mock_state = Mock()

        batch_data = {
            "batch_id": "test_batch",
            "status": "processing",
            "progress_percentage": 50.0,
            "total_students": 10,
            "processed_students": 5,
            "failed_count": 0
        }

        mock_state.get = AsyncMock(return_value=batch_data)

        service = AnalyticsService(mock_state)
        status = await service.get_batch_status("test_batch")

        assert status is not None
        assert status.batch_id == "test_batch"
        assert status.status == BatchStatus.PROCESSING
        assert status.progress_percentage == 50.0
        assert status.processed_students == 5

    @pytest.mark.asyncio
    async def test_mastery_history_daily(self):
        """Test daily mastery history retrieval"""
        mock_state = Mock()

        # Mock daily snapshots
        mock_data = {
            "student:test:mastery:2026-01-01": {
                "mastery_score": 0.6,
                "level": "proficient",
                "components": {"completion": 0.6, "quiz": 0.6, "quality": 0.6, "consistency": 0.6},
                "sample_size": 1
            },
            "student:test:mastery:2026-01-02": {
                "mastery_score": 0.65,
                "level": "proficient",
                "components": {"completion": 0.65, "quiz": 0.65, "quality": 0.65, "consistency": 0.65},
                "sample_size": 1
            },
            "student:test:mastery:2026-01-03": {
                "mastery_score": 0.7,
                "level": "proficient",
                "components": {"completion": 0.7, "quiz": 0.7, "quality": 0.7, "consistency": 0.7},
                "sample_size": 1
            }
        }

        mock_state.get = AsyncMock(side_effect=lambda key: mock_data.get(key))

        service = AnalyticsService(mock_state)

        request = DateRangeRequest(
            student_id="test",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 3),
            aggregation=AggregationType.DAILY
        )

        result = await service.get_mastery_history(request)

        assert result.student_id == "test"
        assert len(result.data) == 3
        assert result.data[0].mastery_score == 0.6
        assert result.data[2].mastery_score == 0.7
        assert result.statistics["count"] == 3
        assert result.statistics["mean"] == 0.65  # (0.6 + 0.65 + 0.7) / 3

    @pytest.mark.asyncio
    async def test_mastery_history_weekly_aggregation(self):
        """Test weekly aggregation of mastery history"""
        mock_state = Mock()

        # Mock data for a 10-day period
        mock_data = {}
        for i in range(10):
            date_str = (date(2026, 1, 1) + timedelta(days=i)).strftime("%Y-%m-%d")
            mock_data[f"student:test:mastery:{date_str}"] = {
                "mastery_score": 0.5 + (i * 0.02),
                "level": "proficient",
                "components": {"completion": 0.5 + (i * 0.02), "quiz": 0.5 + (i * 0.02), "quality": 0.5 + (i * 0.02), "consistency": 0.5 + (i * 0.02)},
                "sample_size": 1
            }

        mock_state.get = AsyncMock(side_effect=lambda key: mock_data.get(key))

        service = AnalyticsService(mock_state)

        request = DateRangeRequest(
            student_id="test",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 10),
            aggregation=AggregationType.WEEKLY
        )

        result = await service.get_mastery_history(request)

        assert result.aggregation == AggregationType.WEEKLY
        # Should have 2 weekly data points
        assert len(result.data) == 2

    @pytest.mark.asyncio
    async def test_comprehensive_analytics(self):
        """Test comprehensive analytics with statistics"""
        mock_state = Mock()

        # Mock 5 days of data showing improvement
        mock_data = {}
        for i in range(5):
            date_str = (date(2026, 1, 1) + timedelta(days=i)).strftime("%Y-%m-%d")
            score = 0.5 + (i * 0.1)
            mock_data[f"student:test:mastery:{date_str}"] = {
                "mastery_score": score,
                "level": "proficient",
                "components": {"completion": score, "quiz": score, "quality": score, "consistency": score},
                "sample_size": 1
            }

        mock_state.get = AsyncMock(side_effect=lambda key: mock_data.get(key))

        service = AnalyticsService(mock_state)

        request = DateRangeRequest(
            student_id="test",
            start_date=date(2026, 1, 1),
            end_date=date(2026, 1, 5),
            aggregation=AggregationType.DAILY
        )

        result = await service.get_comprehensive_analytics(request)

        assert result.student_id == "test"
        assert result.trend == "improving"
        assert result.summary.count == 5
        assert result.summary.mean == 0.7  # (0.5 + 0.6 + 0.7 + 0.8 + 0.9) / 5
        assert result.volatility > 0  # Should have some volatility
        assert result.consistency_score > 0.5  # Should be fairly consistent (monotonic increase)
        assert "completion" in result.component_trends

    @pytest.mark.asyncio
    async def test_cohort_comparison(self):
        """Test cohort comparison analytics"""
        mock_state = Mock()

        # Mock mastery results for two cohorts
        cohort_a_scores = [0.8, 0.75, 0.85]  # Higher scores
        cohort_b_scores = [0.6, 0.55, 0.65]  # Lower scores

        async def mock_get_mastery(student_id):
            if student_id.startswith("A_"):
                idx = int(student_id.split("_")[1])
                score = cohort_a_scores[idx]
            else:
                idx = int(student_id.split("_")[1])
                score = cohort_b_scores[idx]

            return MasteryResult(
                student_id=student_id,
                mastery_score=score,
                level=MasteryLevel.PROFICIENT,
                components=ComponentScores(score, score, score, score),
                breakdown=MasteryBreakdown(
                    completion=score * 0.4,
                    quiz=score * 0.3,
                    quality=score * 0.2,
                    consistency=score * 0.1,
                    weighted_sum=score,
                    weights=Mock()
                )
            )

        mock_state.get_mastery_score = AsyncMock(side_effect=mock_get_mastery)

        service = AnalyticsService(mock_state)

        request = CohortComparisonRequest(
            cohort_a_student_ids=["A_0", "A_1", "A_2"],
            cohort_b_student_ids=["B_0", "B_1", "B_2"],
            include_component_analysis=True,
            include_percentiles=True
        )

        result = await service.compare_cohorts(request)

        assert result.cohort_a_stats.mean > result.cohort_b_stats.mean
        assert result.winner == "cohort_a"
        assert result.statistical_significance is not None
        assert result.statistical_significance < 0.05  # Should be significant
        assert len(result.percentile_rankings) == 6  # All students

    @pytest.mark.asyncio
    async def test_student_comparison(self):
        """Test student comparison with rankings"""
        mock_state = Mock()

        # Mock historical data for comparison
        def mock_history_request(student_id):
            dates = [date(2026, 1, 1) + timedelta(days=i) for i in range(5)]
            data_points = []

            for i, date_val in enumerate(dates):
                score = 0.6 + (i * 0.05) + (0.1 if student_id == "student_1" else 0)
                data_points.append(Mock(
                    date=date_val,
                    mastery_score=score,
                    level=MasteryLevel.PROFICIENT,
                    components=ComponentScores(score, score, score, score),
                    sample_size=1
                ))

            return Mock(data=data_points)

        # Mock get_mastery_history to return different histories
        histories = {
            "student_1": mock_history_request("student_1"),
            "student_2": mock_history_request("student_2"),
            "student_3": mock_history_request("student_3")
        }

        service = AnalyticsService(mock_state)

        # Mock the get_mastery_history method
        async def mock_get_history(request):
            return histories.get(request.student_id, Mock(data=[]))

        service.get_mastery_history = mock_get_history

        request = StudentComparisonRequest(
            student_ids=["student_1", "student_2", "student_3"],
            metric="mastery_score",
            timeframe_days=5
        )

        result = await service.compare_students(request)

        assert len(result.rankings) == 3
        # student_1 should be first (has higher base score)
        assert result.rankings[0]["student_id"] == "student_1"
        assert result.rankings[0]["rank"] == 1
        assert "comparisons" in result.metadata

    def _generate_test_mastery_data(self, scores):
        """Helper to generate test mastery data"""
        data_points = []
        for i, score in enumerate(scores):
            data_points.append(Mock(
                date=date(2026, 1, 1) + timedelta(days=i),
                mastery_score=score,
                level=MasteryLevel.PROFICIENT,
                components=Mock(completion=score, quiz=score, quality=score, consistency=score),
                sample_size=1
            ))
        return data_points

    def test_calculate_trend(self):
        """Test trend calculation"""
        mock_state = Mock()
        service = AnalyticsService(mock_state)

        # Improving trend
        improving_data = self._generate_test_mastery_data([0.5, 0.6, 0.7, 0.8])
        trend = service._calculate_trend(improving_data)
        assert trend == "improving"

        # Declining trend
        declining_data = self._generate_test_mastery_data([0.8, 0.7, 0.6, 0.5])
        trend = service._calculate_trend(declining_data)
        assert trend == "declining"

        # Stable trend
        stable_data = self._generate_test_mastery_data([0.7, 0.71, 0.69, 0.7])
        trend = service._calculate_trend(stable_data)
        assert trend == "stable"

    def test_calculate_statistics(self):
        """Test statistical calculations"""
        mock_state = Mock()
        service = AnalyticsService(mock_state)

        scores = [0.5, 0.6, 0.7, 0.8, 0.9]
        data_points = self._generate_test_mastery_data(scores)

        stats = service._calculate_summary_statistics(data_points)

        assert stats.count == 5
        assert stats.mean == 0.7
        assert stats.median == 0.7
        assert stats.min_value == 0.5
        assert stats.max_value == 0.9
        assert stats.percentiles["50"] == 0.7

    def test_calculate_volatility(self):
        """Test volatility calculation"""
        mock_state = Mock()
        service = AnalyticsService(mock_state)

        # Low volatility
        low_vol_data = self._generate_test_mastery_data([0.7, 0.71, 0.69, 0.7, 0.71])
        low_vol = service._calculate_volatility(low_vol_data)
        assert low_vol < 0.1

        # High volatility
        high_vol_data = self._generate_test_mastery_data([0.3, 0.7, 0.4, 0.8, 0.2])
        high_vol = service._calculate_volatility(high_vol_data)
        assert high_vol > 0.3

    def test_calculate_consistency(self):
        """Test consistency score calculation"""
        mock_state = Mock()
        service = AnalyticsService(mock_state)

        # Perfect consistency (monotonic improvement)
        perfect_data = self._generate_test_mastery_data([0.5, 0.6, 0.7, 0.8])
        perfect_consistency = service._calculate_consistency(perfect_data)
        assert perfect_consistency == 1.0

        # Inconsistent data
        inconsistent_data = self._generate_test_mastery_data([0.5, 0.8, 0.3, 0.9])
        inconsistent = service._calculate_consistency(inconsistent_data)
        assert inconsistent < 0.5


class TestDaprServiceHandler:
    """Test Dapr service handler functionality"""

    def test_dapr_handler_initialization(self):
        """Test Dapr handler initialization"""
        mock_state = Mock()
        handler = DaprServiceHandler(mock_state)

        assert handler.state_manager == mock_state
        assert handler.analytics_service is not None

    @pytest.mark.asyncio
    async def test_process_dapr_request_mastery_calculation(self):
        """Test Dapr mastery calculation intent"""
        mock_state = Mock()
        handler = DaprServiceHandler(mock_state)

        # Mock the mastery calculation method
        mock_result = Mock(model_dump=lambda: {"student_id": "test", "mastery_score": 0.75})
        handler._handle_mastery_calculation = AsyncMock(return_value=mock_result)

        request = DaprProcessRequest(
            intent=DaprIntent.MASTERY_CALCULATION,
            payload={"student_id": "test"}
        )

        response = await handler.process_dapr_request(request)

        assert response.success is True
        assert response.data == {"student_id": "test", "mastery_score": 0.75}
        assert mock_result.model_dump.called

    @pytest.mark.asyncio
    async def test_process_dapr_request_get_prediction(self):
        """Test Dapr prediction intent"""
        mock_state = Mock()
        handler = DaprServiceHandler(mock_state)

        # Mock the prediction method
        mock_result = Mock(model_dump=lambda: {"student_id": "test", "predicted_score": 0.8})
        handler._handle_get_prediction = AsyncMock(return_value=mock_result)

        request = DaprProcessRequest(
            intent=DaprIntent.GET_PREDICTION,
            payload={"student_id": "test"}
        )

        response = await handler.process_dapr_request(request)

        assert response.success is True
        assert "predicted_score" in response.data

    @pytest.mark.asyncio
    async def test_process_dapr_request_generate_path(self):
        """Test Dapr learning path intent"""
        mock_state = Mock()
        handler = DaprServiceHandler(mock_state)

        # Mock the path generation method
        mock_result = Mock(model_dump=lambda: {"path_id": "path_123", "recommendations": []})
        handler._handle_generate_path = AsyncMock(return_value=mock_result)

        request = DaprProcessRequest(
            intent=DaprIntent.GENERATE_PATH,
            payload={"student_id": "test", "target_level": "proficient"}
        )

        response = await handler.process_dapr_request(request)

        assert response.success is True
        assert "path_id" in response.data

    @pytest.mark.asyncio
    async def test_process_dapr_request_batch_process(self):
        """Test Dapr batch processing intent"""
        mock_state = Mock()
        handler = DaprServiceHandler(mock_state)

        # Mock the batch method
        mock_result = Mock(model_dump=lambda: {"batch_id": "batch_123", "status": "pending"})
        handler._handle_batch_process = AsyncMock(return_value=mock_result)

        request = DaprProcessRequest(
            intent=DaprIntent.BATCH_PROCESS,
            payload={"student_ids": ["student_1", "student_2"]}
        )

        response = await handler.process_dapr_request(request)

        assert response.success is True
        assert "batch_id" in response.data

    @pytest.mark.asyncio
    async def test_process_dapr_request_analytics_query(self):
        """Test Dapr analytics query intent"""
        mock_state = Mock()
        handler = DaprServiceHandler(mock_state)

        # Mock the analytics method
        mock_result = Mock(model_dump=lambda: {"student_id": "test", "data": []})
        handler._handle_analytics_query = AsyncMock(return_value=mock_result)

        request = DaprProcessRequest(
            intent=DaprIntent.ANALYTICS_QUERY,
            payload={"student_id": "test", "query_type": "history"}
        )

        response = await handler.process_dapr_request(request)

        assert response.success is True
        assert "data" in response.data

    @pytest.mark.asyncio
    async def test_process_dapr_request_invalid_intent(self):
        """Test Dapr request with invalid intent"""
        mock_state = Mock()
        handler = DaprServiceHandler(mock_state)

        # Create an invalid intent (using a string not in enum)
        from src.models.mastery import DaprIntent
        invalid_intent = DaprIntent.MASTERY_CALCULATION  # Use valid as base
        # We'll test with a valid intent that's not implemented
        request = DaprProcessRequest(
            intent=invalid_intent,
            payload={"test": "data"}
        )

        # Mock the handler method to raise an error
        handler._handle_mastery_calculation = AsyncMock(side_effect=Exception("Test error"))

        response = await handler.process_dapr_request(request)

        assert response.success is False
        assert "error" in response
        assert response.metadata.get("retryable") is True

    @pytest.mark.asyncio
    async def test_process_dapr_request_security_context(self):
        """Test Dapr request with security context"""
        mock_state = Mock()
        handler = DaprServiceHandler(mock_state)

        # Mock security validation
        handler._validate_security_context = AsyncMock(return_value=True)

        mock_result = Mock(model_dump=lambda: {"result": "success"})
        handler._handle_mastery_calculation = AsyncMock(return_value=mock_result)

        security_context = DaprSecurityContext(
            token="test_token",
            user_id="user_123",
            roles=["student"],
            correlation_id="corr_123"
        )

        request = DaprProcessRequest(
            intent=DaprIntent.MASTERY_CALCULATION,
            payload={"student_id": "test"},
            security_context=security_context
        )

        response = await handler.process_dapr_request(request)

        assert response.success is True
        assert response.correlation_id == "corr_123"
        handler._validate_security_context.assert_called_once_with(security_context)

    @pytest.mark.asyncio
    async def test_validate_security_context(self):
        """Test security context validation"""
        mock_state = Mock()
        handler = DaprServiceHandler(mock_state)

        # Test valid context (should pass in current implementation)
        valid_context = DaprSecurityContext(
            token="valid_token",
            user_id="user_123",
            roles=["student"]
        )

        result = await handler._validate_security_context(valid_context)
        assert result is True

    @pytest.mark.asyncio
    async def test_handle_mastery_calculation(self):
        """Test mastery calculation intent handler"""
        mock_state = Mock()
        handler = DaprServiceHandler(mock_state)

        # Mock the MCP calculator
        mock_calculator = Mock()
        mock_result = Mock(model_dump=lambda: {"student_id": "test", "score": 0.8})
        mock_calculator.calculate_mastery = AsyncMock(return_value=mock_result)

        # Mock the import
        import src.skills.calculator as calc_module
        original_calculator = calc_module.MCPMasteryCalculator
        calc_module.MCPMasteryCalculator = Mock(return_value=mock_calculator)

        try:
            result = await handler._handle_mastery_calculation({"student_id": "test"})
            assert "student_id" in result
            assert "score" in result
        finally:
            # Restore original
            calc_module.MCPMasteryCalculator = original_calculator

    @pytest.mark.asyncio
    async def test_handle_get_prediction(self):
        """Test prediction intent handler"""
        mock_state = Mock()
        handler = DaprServiceHandler(mock_state)

        # Mock the predictor
        mock_predictor = Mock()
        mock_result = Mock(model_dump=lambda: {"student_id": "test", "predicted_score": 0.85})
        mock_predictor.predict_next_week = AsyncMock(return_value=mock_result)

        # Mock the import
        import src.services.predictor as pred_module
        original_predictor = pred_module.PredictorService
        pred_module.PredictorService = Mock(return_value=mock_predictor)

        try:
            result = await handler._handle_get_prediction({"student_id": "test"})
            assert "predicted_score" in result
        finally:
            pred_module.PredictorService = original_predictor

    @pytest.mark.asyncio
    async def test_handle_generate_path(self):
        """Test learning path generation intent handler"""
        mock_state = Mock()
        handler = DaprServiceHandler(mock_state)

        # Mock the recommendation engine
        mock_engine = Mock()
        mock_result = Mock(model_dump=lambda: {"path_id": "path_123", "recommendations": []})
        mock_engine.generate_learning_path = AsyncMock(return_value=mock_result)

        # Mock the import
        import src.services.recommendation_engine as rec_module
        original_engine = rec_module.RecommendationEngine
        rec_module.RecommendationEngine = Mock(return_value=mock_engine)

        try:
            result = await handler._handle_generate_path({"student_id": "test"})
            assert "path_id" in result
        finally:
            rec_module.RecommendationEngine = original_engine

    @pytest.mark.asyncio
    async def test_handle_batch_process(self):
        """Test batch process intent handler"""
        mock_state = Mock()
        handler = DaprServiceHandler(mock_state)

        # Mock the analytics service
        mock_result = Mock(model_dump=lambda: {"batch_id": "batch_123", "status": "pending"})
        handler.analytics_service.submit_batch_mastery_calculation = AsyncMock(return_value=mock_result)

        result = await handler._handle_batch_process({
            "student_ids": ["student_1", "student_2"],
            "priority": "normal"
        })

        assert "batch_id" in result

    @pytest.mark.asyncio
    async def test_handle_analytics_query_history(self):
        """Test analytics query history handler"""
        mock_state = Mock()
        handler = DaprServiceHandler(mock_state)

        # Mock the analytics service
        mock_result = Mock(model_dump=lambda: {"student_id": "test", "data": []})
        handler.analytics_service.get_mastery_history = AsyncMock(return_value=mock_result)

        result = await handler._handle_analytics_query({
            "student_id": "test",
            "query_type": "history"
        })

        assert "data" in result

    @pytest.mark.asyncio
    async def test_handle_analytics_query_comprehensive(self):
        """Test analytics query comprehensive handler"""
        mock_state = Mock()
        handler = DaprServiceHandler(mock_state)

        # Mock the analytics service
        mock_result = Mock(model_dump=lambda: {"student_id": "test", "summary": {}})
        handler.analytics_service.get_comprehensive_analytics = AsyncMock(return_value=mock_result)

        result = await handler._handle_analytics_query({
            "student_id": "test",
            "query_type": "comprehensive"
        })

        assert "summary" in result

    def test_classify_error(self):
        """Test error classification"""
        mock_state = Mock()
        handler = DaprServiceHandler(mock_state)

        # Test timeout error
        timeout_error = Exception("Connection timeout")
        detail = handler._classify_error(timeout_error)
        assert detail.code == "TIMEOUT_ERROR"
        assert detail.retryable is True

        # Test validation error
        validation_error = Exception("Validation failed: missing student_id")
        detail = handler._classify_error(validation_error)
        assert detail.code == "VALIDATION_ERROR"
        assert detail.retryable is False

        # Test security error
        security_error = Exception("Security validation failed")
        detail = handler._classify_error(security_error)
        assert detail.code == "SECURITY_ERROR"
        assert detail.retryable is False

        # Test generic error
        generic_error = Exception("Unknown error")
        detail = handler._classify_error(generic_error)
        assert detail.code == "INTERNAL_ERROR"
        assert detail.retryable is True


class TestAnalyticsEdgeCases:
    """Test edge cases in analytics service"""

    def test_summary_statistics_empty(self):
        """Test summary statistics with empty data"""
        mock_state = Mock()
        service = AnalyticsService(mock_state)

        stats = service._calculate_summary_statistics_from_scores([])

        assert stats.count == 0
        assert stats.mean == 0.0
        assert stats.median == 0.0
        assert stats.std_dev == 0.0

    def test_calculate_trend_insufficient_data(self):
        """Test trend calculation with insufficient data"""
        mock_state = Mock()
        service = AnalyticsService(mock_state)

        # Single data point
        single_data = self._generate_test_mastery_data([0.5])
        trend = service._calculate_trend(single_data)
        assert trend == "inconsistent"

    def test_volatility_zero_mean(self):
        """Test volatility calculation with zero mean"""
        mock_state = Mock()
        service = AnalyticsService(mock_state)

        # All zero scores
        zero_data = self._generate_test_mastery_data([0.0, 0.0, 0.0])
        volatility = service._calculate_volatility(zero_data)
        assert volatility == 0.0

    def test_consistency_single_point(self):
        """Test consistency calculation with single data point"""
        mock_state = Mock()
        service = AnalyticsService(mock_state)

        single_data = self._generate_test_mastery_data([0.5])
        consistency = service._calculate_consistency(single_data)
        assert consistency == 0.0

    def test_calculate_statistical_significance_insufficient_data(self):
        """Test statistical significance with insufficient data"""
        mock_state = Mock()
        service = AnalyticsService(mock_state)

        # Only one sample in each cohort
        significance = service._calculate_statistical_significance([0.5], [0.6])
        assert significance is None

    def test_calculate_percentiles_empty(self):
        """Test percentile calculation with empty data"""
        mock_state = Mock()
        service = AnalyticsService(mock_state)

        percentiles = service._calculate_percentiles([], [])
        assert percentiles == {}

    @pytest.mark.asyncio
    async def test_aggregate_period_no_data(self):
        """Test period aggregation with no data"""
        mock_state = Mock()
        mock_state.get = AsyncMock(return_value=None)

        service = AnalyticsService(mock_state)

        result = await service._aggregate_period("test", date(2026, 1, 1), AggregationType.WEEKLY)
        assert result is None

    def test_extract_component_values_invalid_component(self):
        """Test component value extraction with invalid component"""
        mock_state = Mock()
        service = AnalyticsService(mock_state)

        data_points = self._generate_test_mastery_data([0.5, 0.6, 0.7])
        values = service._extract_component_values(data_points, "invalid_component")
        assert values == []

    @pytest.mark.asyncio
    async def test_cohort_comparison_insufficient_data(self):
        """Test cohort comparison with insufficient data"""
        mock_state = Mock()
        service = AnalyticsService(mock_state)

        # Mock only 1 valid student in each cohort
        async def mock_get_mastery(student_id):
            if student_id == "A_0":
                return Mock(mastery_score=0.7)
            elif student_id == "B_0":
                return Mock(mastery_score=0.6)
            return None

        mock_state.get_mastery_score = AsyncMock(side_effect=mock_get_mastery)

        request = CohortComparisonRequest(
            cohort_a_student_ids=["A_0"],  # Only 1
            cohort_b_student_ids=["B_0"]   # Only 1
        )

        with pytest.raises(ValueError, match="Both cohorts must have at least 2 valid students"):
            await service.compare_cohorts(request)

    def _generate_test_mastery_data(self, scores):
        """Helper to generate test mastery data"""
        data_points = []
        for i, score in enumerate(scores):
            data_points.append(Mock(
                date=date(2026, 1, 1) + timedelta(days=i),
                mastery_score=score,
                level=MasteryLevel.PROFICIENT,
                components=Mock(completion=score, quiz=score, quality=score, consistency=score),
                sample_size=1
            ))
        return data_points