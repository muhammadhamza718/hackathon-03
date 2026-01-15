"""
State Manager Service
=====================

Manages all state store operations using Dapr + Redis.
Handles mastery scores, historical snapshots, activity data, and idempotency.
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any

from dapr.clients import DaprClient
from dapr.serializers import JSONSerializer

from src.models.mastery import (
    MasteryResult, HistoricalSnapshot, StudentActivity,
    StateKeyPatterns, ComponentScores, MasteryBreakdown, MasteryWeights
)
from src.models.events import LearningEvent
from src.services.circuit_breaker import safe_redis_operation, CircuitBreakerConfig
from src.main import redis_operations_total, cache_hits, cache_misses
from src.services.connection_pool import get_redis_pool

logger = logging.getLogger(__name__)


class StateManager:
    """
    State store operations with Dapr + Redis backend
    Implements multi-level caching and event sourcing patterns
    """

    def __init__(self, dapr_client: DaprClient, store_name: str = "statestore"):
        self.dapr = dapr_client
        self.store_name = store_name
        self.serializer = JSONSerializer()
        self.cache = {}  # L1 cache (memory)
        self.cache_ttl = {}  # Track cache expiration
        self.redis_pool = get_redis_pool()  # Connection pool for direct Redis access if needed

    @classmethod
    def create(cls, store_name: str = "statestore") -> 'StateManager':
        """
        Factory method to create StateManager with configured Dapr client
        """
        dapr_client = DaprClient()
        return cls(dapr_client, store_name)

    async def health_check(self) -> bool:
        """
        Verify state store connectivity and connection pool health
        Returns True if store is accessible
        """
        try:
            # Check Dapr state store
            await self.get("health:check:test")

            # Check connection pool health (if available)
            try:
                pool_healthy = await self.redis_pool.health_check()
                if not pool_healthy:
                    logger.warning("Redis connection pool health check failed")
                    return False
            except Exception:
                # Connection pool check is optional
                pass

            return True
        except Exception as e:
            logger.error(f"State store health check failed: {e}")
            raise

    # ==================== Mastery Operations ====================

    async def save_mastery_score(self, result: MasteryResult, ttl_days: int = 90) -> bool:
        """
        Save mastery calculation result to state store
        Also saves daily snapshot and component scores
        """
        try:
            # Save current mastery profile
            profile_key = StateKeyPatterns.current_mastery(result.student_id)
            await self.save(profile_key, result.model_dump())

            # Save daily snapshot
            snapshot_key = StateKeyPatterns.daily_snapshot(
                result.student_id, result.calculated_at
            )
            snapshot = HistoricalSnapshot(
                date=result.calculated_at,
                mastery_score=result.mastery_score,
                level=result.level,
                components=result.components
            )
            await self.save(snapshot_key, snapshot.model_dump(), ttl_days)

            # Save individual component scores for granular queries
            components = result.components
            await self.save(
                StateKeyPatterns.component_score(result.student_id, result.calculated_at, "completion"),
                components.completion,
                ttl_days
            )
            await self.save(
                StateKeyPatterns.component_score(result.student_id, result.calculated_at, "quiz"),
                components.quiz,
                ttl_days
            )
            await self.save(
                StateKeyPatterns.component_score(result.student_id, result.calculated_at, "quality"),
                components.quality,
                ttl_days
            )
            await self.save(
                StateKeyPatterns.component_score(result.student_id, result.calculated_at, "consistency"),
                components.consistency,
                ttl_days
            )

            logger.info(f"Saved mastery score for student {result.student_id}: {result.mastery_score:.3f}")
            return True

        except Exception as e:
            logger.error(f"Failed to save mastery score for {result.student_id}: {e}")
            return False

    async def get_mastery_score(self, student_id: str) -> Optional[MasteryResult]:
        """
        Retrieve current mastery score for a student
        """
        try:
            profile_key = StateKeyPatterns.current_mastery(student_id)
            data = await self.get(profile_key)

            if not data:
                return None

            # Reconstruct MasteryResult from stored data
            return MasteryResult(**data)

        except Exception as e:
            logger.error(f"Failed to get mastery score for {student_id}: {e}")
            return None

    async def get_mastery_history(self, student_id: str, days: int = 7) -> List[HistoricalSnapshot]:
        """
        Get historical mastery snapshots for a student
        """
        try:
            snapshots = []
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)

            current_date = start_date
            while current_date <= end_date:
                snapshot_key = StateKeyPatterns.daily_snapshot(student_id, current_date)
                data = await self.get(snapshot_key)

                if data:
                    snapshot = HistoricalSnapshot(**data)
                    snapshots.append(snapshot)

                current_date += timedelta(days=1)

            return sorted(snapshots, key=lambda s: s.date)

        except Exception as e:
            logger.error(f"Failed to get history for {student_id}: {e}")
            return []

    # ==================== Event Sourcing ====================

    async def save_learning_event(self, event: LearningEvent) -> bool:
        """
        Save learning event and check for idempotency
        Returns True if event was processed (new), False if duplicate
        """
        try:
            # Check idempotency
            idempotency_key = StateKeyPatterns.idempotency_check(event.event_id)
            existing = await self.get(idempotency_key)

            if existing:
                logger.info(f"Duplicate event detected: {event.event_id}")
                return False

            # Mark as processed
            await self.save(idempotency_key, {
                "event_id": event.event_id,
                "processed_at": datetime.utcnow().isoformat(),
                "event_type": event.event_type
            }, ttl_days=7)

            logger.info(f"Saved learning event: {event.event_id} for {event.student_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to save learning event {event.event_id}: {e}")
            return False

    async def is_event_processed(self, event_id: str) -> bool:
        """
        Check if an event has already been processed (idempotency check)
        """
        try:
            key = StateKeyPatterns.idempotency_check(event_id)
            data = await self.get(key)
            return data is not None
        except Exception as e:
            logger.error(f"Idempotency check failed for {event_id}: {e}")
            return False

    async def append_event_log(self, student_id: str, event: LearningEvent) -> bool:
        """
        Append event to student's event log (immutable event sourcing)
        """
        try:
            # This would typically be stored in a dedicated event store
            # For MVP, we'll store a compact version in state store
            log_key = f"student:{student_id}:events:log"

            current_log = await self.get(log_key) or []
            if not isinstance(current_log, list):
                current_log = []

            # Append compact event representation
            compact_event = {
                "event_id": event.event_id,
                "event_type": event.event_type,
                "timestamp": event.timestamp.isoformat(),
                "data_hash": event.get_data_hash()[:16]  # First 16 chars
            }
            current_log.append(compact_event)

            # Keep only last 1000 events to prevent unbounded growth
            if len(current_log) > 1000:
                current_log = current_log[-1000:]

            await self.save(log_key, current_log, ttl_days=90)
            return True

        except Exception as e:
            logger.error(f"Failed to append event log for {student_id}: {e}")
            return False

    # ==================== Activity Tracking ====================

    async def update_activity_data(self, student_id: str, event: LearningEvent) -> bool:
        """
        Update student's recent activity summary
        """
        try:
            key = StateKeyPatterns.activity_data(student_id)
            current = await self.get(key)

            if current:
                activity = StudentActivity(**current)
                # Update based on event type
                if event.event_type == "exercise.completed":
                    activity.recent_exercises += 1
                elif event.event_type == "quiz.completed":
                    activity.recent_quizzes += 1

                # Update last seen
                activity.last_updated = datetime.utcnow()
                activity.days_active = min(activity.days_active + 1, 90)
            else:
                # Create new activity record
                activity = StudentActivity(
                    student_id=student_id,
                    last_updated=datetime.utcnow(),
                    recent_exercises=1 if event.event_type == "exercise.completed" else 0,
                    recent_quizzes=1 if event.event_type == "quiz.completed" else 0,
                    avg_session_duration=0.0,
                    days_active=1
                )

            await self.save(key, activity.model_dump(), ttl_days=30)
            return True

        except Exception as e:
            logger.error(f"Failed to update activity for {student_id}: {e}")
            return False

    async def get_activity_data(self, student_id: str) -> Optional[StudentActivity]:
        """
        Get recent activity summary for a student
        """
        try:
            key = StateKeyPatterns.activity_data(student_id)
            data = await self.get(key)

            if data:
                return StudentActivity(**data)
            return None

        except Exception as e:
            logger.error(f"Failed to get activity for {student_id}: {e}")
            return None

    # ==================== Prediction Cache ====================

    async def save_prediction(self, student_id: str, days: int, prediction_data: Dict[str, any]) -> bool:
        """
        Cache prediction results to reduce computation
        """
        try:
            key = StateKeyPatterns.prediction(student_id, days)
            # Store with 1 hour TTL as predictions become stale
            await self.save(key, prediction_data, ttl_hours=1)
            return True
        except Exception as e:
            logger.error(f"Failed to save prediction for {student_id}: {e}")
            return False

    async def get_prediction(self, student_id: str, days: int) -> Optional[Dict[str, any]]:
        """
        Get cached prediction result
        """
        try:
            key = StateKeyPatterns.prediction(student_id, days)
            return await self.get(key)
        except Exception as e:
            logger.error(f"Failed to get prediction for {student_id}: {e}")
            return None

    # ==================== Core Storage Operations ====================

    async def save(self, key: str, value: Any, ttl_days: int = None, ttl_hours: int = None) -> bool:
        """
        Core save operation with optional TTL and circuit breaker protection
        """
        async def _save_operation():
            # Calculate TTL in seconds
            ttl_seconds = None
            if ttl_days:
                ttl_seconds = ttl_days * 24 * 60 * 60
            elif ttl_hours:
                ttl_seconds = ttl_hours * 60 * 60

            # Save to Dapr state store
            state = [{"key": key, "value": value}]
            self.dapr.save_state(
                store_name=self.store_name,
                states=state,
                metadata={"ttlInSeconds": str(ttl_seconds)} if ttl_seconds else {}
            )

            # Update L1 cache
            self.cache[key] = value
            if ttl_seconds:
                self.cache_ttl[key] = datetime.utcnow() + timedelta(seconds=ttl_seconds)
            else:
                self.cache_ttl.pop(key, None)

            # Update Prometheus metrics
            redis_operations_total.labels(operation="set", status="success").inc()

            return True

        async def _fallback():
            """Fallback: Keep data in cache only"""
            logger.warning(f"Redis save failed, using cache fallback for key: {key}")
            self.cache[key] = value
            self.cache_ttl.pop(key, None)  # No TTL in cache-only mode
            redis_operations_total.labels(operation="set", status="fallback").inc()
            return True

        try:
            # Execute with circuit breaker
            return await safe_redis_operation(_save_operation, _fallback)

        except Exception as e:
            logger.error(f"Failed to save state key {key}: {e}")
            return False

    async def get(self, key: str) -> Optional[Any]:
        """
        Core get operation with L1 cache and circuit breaker protection
        """
        # Check L1 cache first (no circuit breaker for cache)
        if key in self.cache:
            # Check if cache entry is still valid
            if key in self.cache_ttl:
                if datetime.utcnow() < self.cache_ttl[key]:
                    cache_hits.inc()  # Prometheus metric
                    return self.cache[key]
                else:
                    # Cache expired
                    del self.cache[key]
                    del self.cache_ttl[key]
            else:
                cache_hits.inc()  # Prometheus metric
                return self.cache[key]

        cache_misses.inc()  # Prometheus metric

        async def _get_operation():
            # Get from Dapr state store
            response = self.dapr.get_state(
                store_name=self.store_name,
                key=key
            )

            if response.data:
                # Parse JSON data
                value = json.loads(response.data.decode('utf-8'))

                # Update cache
                self.cache[key] = value

                # Update Prometheus metrics
                redis_operations_total.labels(operation="get", status="success").inc()

                return value
            else:
                redis_operations_total.labels(operation="get", status="not_found").inc()
                return None

        async def _fallback():
            """Fallback: Return None (cache miss)"""
            logger.warning(f"Redis get failed, returning cache miss for key: {key}")
            redis_operations_total.labels(operation="get", status="fallback").inc()
            return None

        try:
            # Execute with circuit breaker
            return await safe_redis_operation(_get_operation, _fallback)

        except Exception as e:
            logger.error(f"Failed to get state key {key}: {e}")
            return None

    async def delete(self, key: str) -> bool:
        """
        Delete a key from state store
        """
        try:
            self.dapr.delete_state(
                store_name=self.store_name,
                key=key
            )

            # Remove from cache
            self.cache.pop(key, None)
            self.cache_ttl.pop(key, None)

            return True

        except Exception as e:
            logger.error(f"Failed to delete state key {key}: {e}")
            return False

    async def get_bulk(self, keys: List[str]) -> Dict[str, Any]:
        """
        Get multiple keys efficiently
        """
        results = {}
        for key in keys:
            results[key] = await self.get(key)
        return results

    async def get_mastery_statistics(self, student_id: str) -> Dict[str, any]:
        """
        Get comprehensive statistics for a student
        """
        try:
            # Get current mastery
            current = await self.get_mastery_score(student_id)

            # Get recent activity
            activity = await self.get_activity_data(student_id)

            # Get history (7 days)
            history = await self.get_mastery_history(student_id, days=7)

            # Calculate trends
            historical_scores = [h.mastery_score for h in history]
            trend = "stable"
            if len(historical_scores) >= 2:
                if historical_scores[-1] > historical_scores[0] + 0.02:
                    trend = "improving"
                elif historical_scores[-1] < historical_scores[0] - 0.02:
                    trend = "declining"

            # Calculate average
            avg_score = sum(h.mastery_score for h in history) / len(history) if history else 0.0

            return {
                "student_id": student_id,
                "current_mastery": current,
                "historical_average": avg_score,
                "trend": trend,
                "activity": activity,
                "history_length": len(history)
            }

        except Exception as e:
            logger.error(f"Failed to get statistics for {student_id}: {e}")
            return {}

    def clear_cache(self):
        """Clear L1 cache (useful for testing)"""
        self.cache.clear()
        self.cache_ttl.clear()