"""
Analytics Service
=================

Phase 9: Batch processing, historical analytics, and cohort comparison services.
Phase 10: Dapr service invocation handling.

Implements all business logic for analytics features.
"""

import logging
import asyncio
import uuid
import statistics
from datetime import datetime, date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict
import numpy as np

from src.models.mastery import (
    MasteryResult,
    ComponentScores,
    MasteryLevel,
    BatchPriority,
    BatchStatus,
    BatchMasteryRequest,
    BatchMasteryItem,
    BatchMasteryResponse,
    BatchJobStatus,
    AggregationType,
    DateRangeRequest,
    MasteryHistoryData,
    MasteryHistoryResponse,
    SummaryStatistics,
    MasteryAnalyticsResponse,
    CohortComparisonRequest,
    CohortComparisonResult,
    StudentComparisonRequest,
    StudentComparisonResult,
    DaprIntent,
    DaprSecurityContext,
    DaprProcessRequest,
    DaprProcessResponse,
    DaprErrorDetail,
    StateKeyPatterns
)
from src.services.state_manager import StateManager

logger = logging.getLogger(__name__)


class AnalyticsService:
    """Core analytics service for batch processing and historical analysis"""

    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
        self.model_version = "1.0.0"

    # ==================== BATCH PROCESSING ====================

    async def submit_batch_mastery_calculation(
        self,
        request: BatchMasteryRequest
    ) -> BatchMasteryResponse:
        """
        Submit batch mastery calculation job

        Args:
            request: Batch request with student IDs and priority

        Returns:
            BatchMasteryResponse with job status
        """
        batch_id = f"batch_{uuid.uuid4().hex[:8]}"
        created_at = datetime.utcnow()

        # Store batch job metadata
        batch_data = {
            "batch_id": batch_id,
            "student_ids": request.student_ids,
            "priority": request.priority.value,
            "status": BatchStatus.PENDING.value,
            "created_at": created_at.isoformat(),
            "callback_url": request.callback_url,
            "processed_count": 0,
            "failed_count": 0,
            "model_version": self.model_version
        }

        await self.state_manager.save(StateKeyPatterns.batch_job(batch_id), batch_data, ttl_hours=24)

        # Start async processing (fire and forget)
        asyncio.create_task(self._process_batch_job(batch_id, request))

        return BatchMasteryResponse(
            batch_id=batch_id,
            status=BatchStatus.PENDING,
            student_count=len(request.student_ids),
            priority=request.priority,
            created_at=created_at
        )

    async def _process_batch_job(self, batch_id: str, request: BatchMasteryRequest):
        """Process batch job asynchronously"""
        try:
            # Update status to processing
            batch_data = await self.state_manager.get(StateKeyPatterns.batch_job(batch_id))
            if not batch_data:
                return

            batch_data["status"] = BatchStatus.PROCESSING.value
            await self.state_manager.save(StateKeyPatterns.batch_job(batch_id), batch_data, ttl_hours=24)

            # Process students based on priority
            results = []
            processed_count = 0
            failed_count = 0

            # Determine concurrency based on priority
            if request.priority == BatchPriority.HIGH:
                batch_size = 10
                delay = 0.01
            elif request.priority == BatchPriority.NORMAL:
                batch_size = 5
                delay = 0.05
            else:  # LOW
                batch_size = 2
                delay = 0.1

            # Process in batches to avoid overwhelming the system
            for i in range(0, len(request.student_ids), batch_size):
                batch = request.student_ids[i:i + batch_size]

                # Process batch concurrently
                tasks = [self._calculate_student_mastery(student_id) for student_id in batch]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)

                for result in batch_results:
                    if isinstance(result, Exception):
                        logger.error(f"Batch processing error: {result}")
                        failed_count += 1
                    else:
                        results.append(result)
                        if result.success:
                            processed_count += 1
                        else:
                            failed_count += 1

                # Update progress
                batch_data["processed_count"] = processed_count
                batch_data["failed_count"] = failed_count
                batch_data["progress_percentage"] = (processed_count + failed_count) / len(request.student_ids) * 100
                await self.state_manager.save(StateKeyPatterns.batch_job(batch_id), batch_data, ttl_hours=24)

                # Store individual results
                for result in batch_results:
                    if isinstance(result, BatchMasteryItem):
                        await self.state_manager.save(
                            StateKeyPatterns.batch_result(batch_id, result.student_id),
                            result.model_dump(),
                            ttl_hours=24
                        )

                # Delay for priority-based throttling
                if delay > 0:
                    await asyncio.sleep(delay)

            # Mark as completed
            batch_data["status"] = BatchStatus.COMPLETED.value
            batch_data["completed_at"] = datetime.utcnow().isoformat()
            await self.state_manager.save(StateKeyPatterns.batch_job(batch_id), batch_data, ttl_hours=24)

            # Trigger callback if provided
            if request.callback_url:
                await self._trigger_callback(request.callback_url, batch_id, batch_data)

        except Exception as e:
            logger.error(f"Batch job failed: {e}")
            batch_data = await self.state_manager.get(StateKeyPatterns.batch_job(batch_id))
            if batch_data:
                batch_data["status"] = BatchStatus.FAILED.value
                batch_data["error"] = str(e)
                await self.state_manager.save(StateKeyPatterns.batch_job(batch_id), batch_data, ttl_hours=24)

    async def _calculate_student_mastery(self, student_id: str) -> BatchMasteryItem:
        """Calculate mastery for a single student in batch"""
        try:
            mastery = await self.state_manager.get_mastery_score(student_id)

            if mastery is None:
                return BatchMasteryItem(
                    student_id=student_id,
                    success=False,
                    error_message="No mastery data found"
                )

            return BatchMasteryItem(
                student_id=student_id,
                success=True,
                mastery_result=mastery
            )

        except Exception as e:
            return BatchMasteryItem(
                student_id=student_id,
                success=False,
                error_message=str(e)
            )

    async def get_batch_status(self, batch_id: str) -> Optional[BatchJobStatus]:
        """Get current status of batch job"""
        batch_data = await self.state_manager.get(StateKeyPatterns.batch_job(batch_id))
        if not batch_data:
            return None

        return BatchJobStatus(
            batch_id=batch_id,
            status=BatchStatus(batch_data["status"]),
            progress_percentage=batch_data.get("progress_percentage", 0.0),
            total_students=batch_data.get("student_count", 0),
            processed_students=batch_data.get("processed_count", 0),
            failed_count=batch_data.get("failed_count", 0),
            metadata=batch_data
        )

    async def get_batch_results(self, batch_id: str, limit: int = 100) -> List[BatchMasteryItem]:
        """Get results for completed batch job"""
        # In a real implementation, this would query all keys matching the pattern
        # For now, we'll return empty list (would need to track keys in production)
        return []

    async def _trigger_callback(self, url: str, batch_id: str, batch_data: Dict[str, Any]):
        """Trigger webhook callback (simplified implementation)"""
        # In production, this would make an HTTP request
        logger.info(f"Would trigger callback to {url} for batch {batch_id}")
        pass

    # ==================== HISTORICAL ANALYTICS ====================

    async def get_mastery_history(
        self,
        request: DateRangeRequest
    ) -> MasteryHistoryResponse:
        """
        Get historical mastery data for a student with aggregation

        Args:
            request: Date range and aggregation parameters

        Returns:
            Historical mastery data
        """
        start_date = request.start_date
        end_date = request.end_date
        aggregation = request.aggregation

        # Generate list of dates based on aggregation
        dates = self._generate_date_range(start_date, end_date, aggregation)

        # Fetch mastery data for each date
        data_points = []
        for date_val in dates:
            if aggregation == AggregationType.DAILY:
                key = StateKeyPatterns.daily_snapshot(request.student_id, date_val)
                mastery_data = await self.state_manager.get(key)

                if mastery_data:
                    data_points.append(MasteryHistoryData(
                        date=date_val,
                        mastery_score=mastery_data["mastery_score"],
                        level=MasteryLevel(mastery_data["level"]),
                        components=ComponentScores(**mastery_data["components"]),
                        sample_size=mastery_data.get("sample_size", 1)
                    ))

            elif aggregation in [AggregationType.WEEKLY, AggregationType.MONTHLY]:
                # Aggregate multiple days
                aggregated = await self._aggregate_period(request.student_id, date_val, aggregation)
                if aggregated:
                    data_points.append(aggregated)

        # Calculate statistics and trends
        if data_points:
            summary = self._calculate_summary_statistics(data_points)
            trend = self._calculate_trend(data_points)
            component_trends = self._calculate_component_trends(data_points)
            volatility = self._calculate_volatility(data_points)
            consistency = self._calculate_consistency(data_points)
        else:
            summary = SummaryStatistics(count=0, mean=0.0, median=0.0, std_dev=0.0, min_value=0.0, max_value=0.0)
            trend = "inconsistent"
            component_trends = {}
            volatility = 0.0
            consistency = 0.0

        return MasteryHistoryResponse(
            student_id=request.student_id,
            start_date=start_date,
            end_date=end_date,
            aggregation=aggregation,
            data=data_points,
            statistics=summary.model_dump(),
            metadata={
                "model_version": self.model_version,
                "total_days": len(data_points)
            }
        )

    async def get_comprehensive_analytics(
        self,
        request: DateRangeRequest
    ) -> MasteryAnalyticsResponse:
        """
        Get comprehensive analytics with trends and statistics

        Args:
            request: Date range parameters

        Returns:
            Comprehensive analytics response
        """
        history = await self.get_mastery_history(request)

        if not history.data:
            return MasteryAnalyticsResponse(
                student_id=request.student_id,
                period=request,
                summary=SummaryStatistics(count=0, mean=0.0, median=0.0, std_dev=0.0, min_value=0.0, max_value=0.0),
                trend="inconsistent",
                volatility=0.0,
                consistency_score=0.0
            )

        summary = SummaryStatistics(**history.statistics)
        trend = self._calculate_trend(history.data)
        volatility = self._calculate_volatility(history.data)
        consistency = self._calculate_consistency(history.data)
        component_trends = self._calculate_component_trends(history.data)

        return MasteryAnalyticsResponse(
            student_id=request.student_id,
            period=request,
            summary=summary,
            trend=trend,
            volatility=volatility,
            consistency_score=consistency,
            component_trends=component_trends,
            metadata={
                "model_version": self.model_version,
                "data_points": len(history.data)
            }
        )

    # ==================== COHORT COMPARISON ====================

    async def compare_cohorts(
        self,
        request: CohortComparisonRequest
    ) -> CohortComparisonResult:
        """
        Compare two cohorts of students

        Args:
            request: Cohort comparison parameters

        Returns:
            Comparison results with statistics
        """
        # Get current mastery for all students in both cohorts
        cohort_a_results = []
        cohort_b_results = []

        # Process cohorts in parallel
        tasks_a = [self.state_manager.get_mastery_score(student_id) for student_id in request.cohort_a_student_ids]
        tasks_b = [self.state_manager.get_mastery_score(student_id) for student_id in request.cohort_b_student_ids]

        results_a = await asyncio.gather(*tasks_a, return_exceptions=True)
        results_b = await asyncio.gather(*tasks_b, return_exceptions=True)

        # Filter successful results
        for result in results_a:
            if isinstance(result, MasteryResult):
                cohort_a_results.append(result.mastery_score)
        for result in results_b:
            if isinstance(result, MasteryResult):
                cohort_b_results.append(result.mastery_score)

        if len(cohort_a_results) < 2 or len(cohort_b_results) < 2:
            raise ValueError("Both cohorts must have at least 2 valid students")

        # Calculate statistics
        cohort_a_stats = self._calculate_summary_statistics_from_scores(cohort_a_results)
        cohort_b_stats = self._calculate_summary_statistics_from_scores(cohort_b_results)

        # Calculate statistical significance (simplified t-test)
        statistical_significance = self._calculate_statistical_significance(cohort_a_results, cohort_b_results)

        # Determine winner
        winner = None
        if statistical_significance and statistical_significance < 0.05:
            mean_a = cohort_a_stats.mean
            mean_b = cohort_b_stats.mean
            if mean_a > mean_b:
                winner = "cohort_a"
            elif mean_b > mean_a:
                winner = "cohort_b"

        # Component analysis if requested
        component_comparison = {}
        if request.include_component_analysis:
            component_comparison = await self._compare_cohort_components(
                request.cohort_a_student_ids,
                request.cohort_b_student_ids
            )

        # Percentile rankings if requested
        percentile_rankings = {}
        if request.include_percentiles:
            percentile_rankings = self._calculate_percentiles(
                cohort_a_results + cohort_b_results,
                request.cohort_a_student_ids + request.cohort_b_student_ids
            )

        return CohortComparisonResult(
            cohort_a_stats=cohort_a_stats,
            cohort_b_stats=cohort_b_stats,
            statistical_significance=statistical_significance,
            winner=winner,
            component_comparison=component_comparison,
            percentile_rankings=percentile_rankings,
            metadata={
                "model_version": self.model_version,
                "cohort_a_size": len(cohort_a_results),
                "cohort_b_size": len(cohort_b_results)
            }
        )

    async def compare_students(
        self,
        request: StudentComparisonRequest
    ) -> StudentComparisonResult:
        """
        Compare specific students or groups

        Args:
            request: Student comparison parameters

        Returns:
            Comparison results with rankings
        """
        lookback_date = datetime.utcnow().date() - timedelta(days=request.timeframe_days)

        # Get historical data for each student
        student_data = {}
        for student_id in request.student_ids:
            history_request = DateRangeRequest(
                student_id=student_id,
                start_date=lookback_date,
                end_date=datetime.utcnow().date(),
                aggregation=AggregationType.DAILY
            )
            history = await self.get_mastery_history(history_request)

            if history.data:
                # Get the metric requested
                if request.metric == "mastery_score":
                    values = [data.mastery_score for data in history.data]
                else:
                    # For component metrics
                    values = self._extract_component_values(history.data, request.metric)

                if values:
                    student_data[student_id] = {
                        "mean": statistics.mean(values),
                        "median": statistics.median(values),
                        "std_dev": statistics.stdev(values) if len(values) > 1 else 0.0,
                        "latest": values[-1],
                        "trend": self._calculate_trend_from_values(values)
                    }

        # Rank students
        rankings = []
        sorted_students = sorted(student_data.items(), key=lambda x: x[1]["mean"], reverse=True)

        for rank, (student_id, data) in enumerate(sorted_students, 1):
            rankings.append({
                "student_id": student_id,
                "rank": rank,
                "mean": data["mean"],
                "median": data["median"],
                "std_dev": data["std_dev"],
                "latest": data["latest"],
                "trend": data["trend"]
            })

        # Create comparison matrix
        comparisons = {}
        for student_a in student_data:
            comparisons[student_a] = {}
            for student_b in student_data:
                if student_a != student_b:
                    comparisons[student_a][student_b] = {
                        "difference": student_data[student_a]["mean"] - student_data[student_b]["mean"],
                        "ratio": student_data[student_a]["mean"] / max(student_data[student_b]["mean"], 0.001),
                        "relative_performance": "better" if student_data[student_a]["mean"] > student_data[student_b]["mean"] else "worse"
                    }

        return StudentComparisonResult(
            rankings=rankings,
            comparisons=comparisons,
            metadata={
                "metric": request.metric,
                "timeframe_days": request.timeframe_days,
                "total_students": len(student_data)
            }
        )

    # ==================== UTILITY METHODS ====================

    def _generate_date_range(self, start_date: date, end_date: date, aggregation: AggregationType) -> List[date]:
        """Generate list of dates based on aggregation"""
        dates = []
        current = start_date

        if aggregation == AggregationType.DAILY:
            while current <= end_date:
                dates.append(current)
                current += timedelta(days=1)
        elif aggregation == AggregationType.WEEKLY:
            while current <= end_date:
                dates.append(current)
                current += timedelta(weeks=1)
        elif aggregation == AggregationType.MONTHLY:
            while current <= end_date:
                dates.append(current)
                # Move to next month
                if current.month == 12:
                    current = date(current.year + 1, 1, 1)
                else:
                    current = date(current.year, current.month + 1, 1)

        return dates

    async def _aggregate_period(
        self,
        student_id: str,
        period_start: date,
        aggregation: AggregationType
    ) -> Optional[MasteryHistoryData]:
        """Aggregate mastery data for a period"""
        if aggregation == AggregationType.WEEKLY:
            period_end = min(period_start + timedelta(days=6), datetime.utcnow().date())
            days_to_check = 7
        else:  # MONTHLY
            if period_start.month == 12:
                period_end = min(date(period_start.year + 1, 1, 1) - timedelta(days=1), datetime.utcnow().date())
            else:
                period_end = min(date(period_start.year, period_start.month + 1, 1) - timedelta(days=1), datetime.utcnow().date())
            days_to_check = 31

        scores = []
        components_sum = defaultdict(float)
        sample_size = 0

        current = period_start
        while current <= period_end:
            key = StateKeyPatterns.daily_snapshot(student_id, current)
            mastery_data = await self.state_manager.get(key)

            if mastery_data:
                scores.append(mastery_data["mastery_score"])
                for comp, value in mastery_data["components"].items():
                    components_sum[comp] += value
                sample_size += mastery_data.get("sample_size", 1)

            current += timedelta(days=1)

        if not scores:
            return None

        # Calculate averages
        avg_score = statistics.mean(scores)
        components = {comp: total / len(scores) for comp, total in components_sum.items()}

        return MasteryHistoryData(
            date=period_start,
            mastery_score=avg_score,
            level=MasteryLevel.NOVICE if avg_score < 0.4 else MasteryLevel.DEVELOPING if avg_score < 0.6 else MasteryLevel.PROFICIENT if avg_score < 0.8 else MasteryLevel.MASTER,
            components=ComponentScores(**components),
            sample_size=sample_size
        )

    def _calculate_summary_statistics(self, data_points: List[MasteryHistoryData]) -> SummaryStatistics:
        """Calculate summary statistics from data points"""
        scores = [point.mastery_score for point in data_points]

        return self._calculate_summary_statistics_from_scores(scores)

    def _calculate_summary_statistics_from_scores(self, scores: List[float]) -> SummaryStatistics:
        """Calculate summary statistics from raw scores"""
        if not scores:
            return SummaryStatistics(count=0, mean=0.0, median=0.0, std_dev=0.0, min_value=0.0, max_value=0.0)

        count = len(scores)
        mean = statistics.mean(scores)
        median = statistics.median(scores)
        std_dev = statistics.stdev(scores) if count > 1 else 0.0
        min_value = min(scores)
        max_value = max(scores)

        # Calculate percentiles
        sorted_scores = sorted(scores)
        percentiles = {}
        for p in [25, 50, 75, 90, 95]:
            idx = (p / 100) * (count - 1)
            lower = int(idx)
            upper = min(lower + 1, count - 1)
            if lower == upper:
                value = sorted_scores[lower]
            else:
                value = sorted_scores[lower] + (sorted_scores[upper] - sorted_scores[lower]) * (idx - lower)
            percentiles[str(p)] = value

        return SummaryStatistics(
            count=count,
            mean=mean,
            median=median,
            std_dev=std_dev,
            min_value=min_value,
            max_value=max_value,
            percentiles=percentiles
        )

    def _calculate_trend(self, data_points: List[MasteryHistoryData]) -> str:
        """Calculate overall trend from data points"""
        if len(data_points) < 2:
            return "inconsistent"

        scores = [point.mastery_score for point in data_points]
        return self._calculate_trend_from_values(scores)

    def _calculate_trend_from_values(self, values: List[float]) -> str:
        """Calculate trend from a list of values"""
        if len(values) < 2:
            return "inconsistent"

        first_half = values[:len(values)//2]
        second_half = values[len(values)//2:]

        avg_first = statistics.mean(first_half)
        avg_second = statistics.mean(second_half)

        diff = avg_second - avg_first

        if abs(diff) < 0.02:  # Threshold for significant change
            return "stable"
        elif diff > 0:
            return "improving"
        else:
            return "declining"

    def _calculate_component_trends(self, data_points: List[MasteryHistoryData]) -> Dict[str, str]:
        """Calculate trends for each component"""
        if len(data_points) < 2:
            return {}

        component_values = defaultdict(list)
        for point in data_points:
            component_values["completion"].append(point.components.completion)
            component_values["quiz"].append(point.components.quiz)
            component_values["quality"].append(point.components.quality)
            component_values["consistency"].append(point.components.consistency)

        trends = {}
        for component, values in component_values.items():
            trends[component] = self._calculate_trend_from_values(values)

        return trends

    def _calculate_volatility(self, data_points: List[MasteryHistoryData]) -> float:
        """Calculate volatility (normalized standard deviation)"""
        if len(data_points) < 2:
            return 0.0

        scores = [point.mastery_score for point in data_points]
        std_dev = statistics.stdev(scores) if len(scores) > 1 else 0.0
        mean = statistics.mean(scores)

        if mean == 0:
            return 0.0

        return min(std_dev / mean, 1.0)

    def _calculate_consistency(self, data_points: List[MasteryHistoryData]) -> float:
        """Calculate consistency score (0-1)"""
        if len(data_points) < 2:
            return 0.0

        scores = [point.mastery_score for point in data_points]
        # Calculate how many consecutive points stay within a small range
        consistent_count = 0
        threshold = 0.05  # Within 5%

        for i in range(1, len(scores)):
            if abs(scores[i] - scores[i-1]) <= threshold:
                consistent_count += 1

        return consistent_count / (len(scores) - 1)

    async def _compare_cohort_components(self, cohort_a_ids: List[str], cohort_b_ids: List[str]) -> Dict[str, Dict[str, float]]:
        """Compare components between cohorts"""
        component_comparison = {}

        for cohort_name, cohort_ids in [("cohort_a", cohort_a_ids), ("cohort_b", cohort_b_ids)]:
            component_averages = defaultdict(list)

            for student_id in cohort_ids:
                mastery = await self.state_manager.get_mastery_score(student_id)
                if mastery:
                    component_averages["completion"].append(mastery.components.completion)
                    component_averages["quiz"].append(mastery.components.quiz)
                    component_averages["quality"].append(mastery.components.quality)
                    component_averages["consistency"].append(mastery.components.consistency)

            if component_averages:
                component_comparison[cohort_name] = {
                    comp: statistics.mean(values) if values else 0.0
                    for comp, values in component_averages.items()
                }

        return component_comparison

    def _calculate_statistical_significance(self, cohort_a: List[float], cohort_b: List[float]) -> Optional[float]:
        """Calculate p-value for difference between cohorts (simplified)"""
        if len(cohort_a) < 2 or len(cohort_b) < 2:
            return None

        # This is a simplified calculation. In production, use scipy.stats.ttest_ind
        # For now, use effect size as a proxy
        mean_a = statistics.mean(cohort_a)
        mean_b = statistics.mean(cohort_b)
        std_a = statistics.stdev(cohort_a) if len(cohort_a) > 1 else 0.1
        std_b = statistics.stdev(cohort_b) if len(cohort_b) > 1 else 0.1

        # Pooled standard deviation
        pooled_std = ((std_a ** 2 + std_b ** 2) / 2) ** 0.5

        if pooled_std == 0:
            return None

        # Effect size (Cohen's d)
        effect_size = abs(mean_a - mean_b) / pooled_std

        # Convert effect size to approximate p-value (inverse relationship)
        # This is a rough approximation
        if effect_size > 0.8:
            p_value = 0.001
        elif effect_size > 0.5:
            p_value = 0.01
        elif effect_size > 0.2:
            p_value = 0.05
        else:
            p_value = 0.1

        return p_value

    def _calculate_percentiles(self, scores: List[float], student_ids: List[str]) -> Dict[str, float]:
        """Calculate percentile rankings for students"""
        if not scores:
            return {}

        sorted_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
        percentiles = {}

        for i, idx in enumerate(sorted_indices):
            percentile = (i / len(scores)) * 100
            percentiles[student_ids[idx]] = percentile

        return percentiles

    def _extract_component_values(self, data_points: List[MasteryHistoryData], component: str) -> List[float]:
        """Extract specific component values from data points"""
        component_map = {
            "completion": lambda c: c.completion,
            "quiz": lambda c: c.quiz,
            "quality": lambda c: c.quality,
            "consistency": lambda c: c.consistency
        }

        extractor = component_map.get(component)
        if not extractor:
            return []

        return [extractor(point.components) for point in data_points]


class DaprServiceHandler:
    """Handles Dapr service invocation requests (Phase 10)"""

    def __init__(self, state_manager: StateManager):
        self.state_manager = state_manager
        self.analytics_service = AnalyticsService(state_manager)
        self.logger = logging.getLogger(__name__)

    async def process_dapr_request(
        self,
        request: DaprProcessRequest,
        security_context: Optional[DaprSecurityContext] = None
    ) -> DaprProcessResponse:
        """
        Process Dapr service invocation request

        Args:
            request: Dapr request with intent and payload
            security_context: Security context from Dapr

        Returns:
            Standardized Dapr response
        """
        try:
            # Validate security context if provided
            if security_context and not await self._validate_security_context(security_context):
                return DaprProcessResponse(
                    success=False,
                    error="Security validation failed",
                    metadata={"error_code": "SECURITY_ERROR"}
                )

            # Route by intent
            if request.intent == DaprIntent.MASTERY_CALCULATION:
                result = await self._handle_mastery_calculation(request.payload)
            elif request.intent == DaprIntent.GET_PREDICTION:
                result = await self._handle_get_prediction(request.payload)
            elif request.intent == DaprIntent.GENERATE_PATH:
                result = await self._handle_generate_path(request.payload)
            elif request.intent == DaprIntent.BATCH_PROCESS:
                result = await self._handle_batch_process(request.payload)
            elif request.intent == DaprIntent.ANALYTICS_QUERY:
                result = await self._handle_analytics_query(request.payload)
            else:
                return DaprProcessResponse(
                    success=False,
                    error=f"Unknown intent: {request.intent}",
                    metadata={"error_code": "INVALID_INTENT"}
                )

            return DaprProcessResponse(
                success=True,
                data=result,
                correlation_id=security_context.correlation_id if security_context else None
            )

        except Exception as e:
            self.logger.error(f"Dapr processing error: {e}", exc_info=True)

            # Determine if error is retryable
            error_detail = self._classify_error(e)

            return DaprProcessResponse(
                success=False,
                error=str(e),
                metadata={
                    "error_code": error_detail.code,
                    "retryable": error_detail.retryable,
                    "details": error_detail.details
                },
                correlation_id=security_context.correlation_id if security_context else None
            )

    async def _validate_security_context(self, context: DaprSecurityContext) -> bool:
        """Validate security context from Dapr"""
        # In production, this would validate JWT tokens and roles
        # For now, basic validation

        if context.token:
            # Validate JWT token (simplified)
            try:
                # In real implementation: from src.security import SecurityManager
                # security = SecurityManager()
                # security.validate_jwt(context.token)
                pass
            except Exception:
                return False

        return True

    async def _handle_mastery_calculation(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle mastery calculation intent"""
        from src.skills.calculator import MCPMasteryCalculator

        student_id = payload.get("student_id")
        if not student_id:
            raise ValueError("student_id required")

        # Use MCP skill for calculation
        calculator = MCPMasteryCalculator(self.state_manager)
        result = await calculator.calculate_mastery(student_id)

        return result.model_dump() if result else {}

    async def _handle_get_prediction(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle get prediction intent"""
        from src.services.predictor import PredictorService

        student_id = payload.get("student_id")
        if not student_id:
            raise ValueError("student_id required")

        predictor = PredictorService(self.state_manager)
        result = await predictor.predict_next_week(student_id)

        return result.model_dump()

    async def _handle_generate_path(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle generate learning path intent"""
        from src.services.recommendation_engine import RecommendationEngine

        student_id = payload.get("student_id")
        if not student_id:
            raise ValueError("student_id required")

        target_level = payload.get("target_level")
        max_duration = payload.get("max_duration_minutes")

        engine = RecommendationEngine(self.state_manager)
        result = await engine.generate_learning_path(student_id, target_level, max_duration)

        return result.model_dump()

    async def _handle_batch_process(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle batch process intent"""
        student_ids = payload.get("student_ids", [])
        priority = payload.get("priority", "normal")

        request = BatchMasteryRequest(
            student_ids=student_ids,
            priority=BatchPriority(priority)
        )

        result = await self.analytics_service.submit_batch_mastery_calculation(request)
        return result.model_dump()

    async def _handle_analytics_query(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Handle analytics query intent"""
        student_id = payload.get("student_id")
        if not student_id:
            raise ValueError("student_id required")

        query_type = payload.get("query_type", "history")

        if query_type == "history":
            start_date = payload.get("start_date")
            end_date = payload.get("end_date")
            aggregation = payload.get("aggregation", "daily")

            request = DateRangeRequest(
                student_id=student_id,
                start_date=date.fromisoformat(start_date) if start_date else datetime.utcnow().date() - timedelta(days=30),
                end_date=date.fromisoformat(end_date) if end_date else datetime.utcnow().date(),
                aggregation=AggregationType(aggregation)
            )

            result = await self.analytics_service.get_mastery_history(request)
            return result.model_dump()

        elif query_type == "comprehensive":
            start_date = payload.get("start_date")
            end_date = payload.get("end_date")

            request = DateRangeRequest(
                student_id=student_id,
                start_date=date.fromisoformat(start_date) if start_date else datetime.utcnow().date() - timedelta(days=30),
                end_date=date.fromisoformat(end_date) if end_date else datetime.utcnow().date(),
                aggregation=AggregationType.DAILY
            )

            result = await self.analytics_service.get_comprehensive_analytics(request)
            return result.model_dump()

        else:
            raise ValueError(f"Unknown query_type: {query_type}")

    def _classify_error(self, error: Exception) -> DaprErrorDetail:
        """Classify error and determine retryability"""
        error_str = str(error).lower()

        if "timeout" in error_str or "connection" in error_str:
            return DaprErrorDetail(
                code="TIMEOUT_ERROR",
                message="Request timeout or connection error",
                details={"original_error": str(error)},
                retryable=True
            )
        elif "validation" in error_str or "required" in error_str:
            return DaprErrorDetail(
                code="VALIDATION_ERROR",
                message="Invalid request data",
                details={"original_error": str(error)},
                retryable=False
            )
        elif "security" in error_str or "auth" in error_str:
            return DaprErrorDetail(
                code="SECURITY_ERROR",
                message="Security validation failed",
                details={"original_error": str(error)},
                retryable=False
            )
        else:
            return DaprErrorDetail(
                code="INTERNAL_ERROR",
                message="Internal processing error",
                details={"original_error": str(error)},
                retryable=True
            )