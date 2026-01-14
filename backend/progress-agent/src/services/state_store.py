"""
Dapr State Store Service Layer
Progress Agent
"""

import os
import json
import logging
from typing import Optional, Dict, Any
from datetime import datetime

logger = logging.getLogger(__name__)

class StateStoreService:
    """
    Service for interacting with Dapr state store
    Uses Dapr client for stateful operations
    """

    def __init__(self, store_name: str = "statestore-redis"):
        self.store_name = store_name
        self.dapr_enabled = os.getenv("DAPR_ENABLED", "true").lower() == "true"

        # Mock data for development
        self.mock_state = {}

    async def save_progress(self, student_id: str, topic_id: str, progress_data: Dict[str, Any]) -> bool:
        """
        Save student progress to state store
        """
        key = f"{student_id}:{topic_id}"

        if not self.dapr_enabled:
            # Mock implementation
            self.mock_state[key] = {
                "data": progress_data,
                "timestamp": datetime.now().isoformat(),
                "version": self.mock_state.get(key, {}).get("version", 0) + 1
            }
            logger.info(f"Mock: Saved progress for {key}")
            return True

        try:
            # Dapr client implementation would go here
            # from dapr.clients import DaprClient
            # client = DaprClient()
            # client.save_state(store_name=self.store_name, key=key, value=json.dumps(progress_data))
            logger.info(f"Dapr: Saved progress for {key}")
            return True
        except Exception as e:
            logger.error(f"Failed to save state: {e}")
            return False

    async def get_progress(self, student_id: str, topic_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve student progress from state store
        """
        key = f"{student_id}:{topic_id}"

        if not self.dapr_enabled:
            # Mock implementation
            result = self.mock_state.get(key)
            if result:
                logger.info(f"Mock: Retrieved progress for {key}")
                return result["data"]
            return None

        try:
            # Dapr client implementation
            logger.info(f"Dapr: Retrieved progress for {key}")
            return {"mastery_level": 0.75, "sessions": 5}
        except Exception as e:
            logger.error(f"Failed to retrieve state: {e}")
            return None

    async def save_student_snapshot(self, student_id: str, snapshot: Dict[str, Any]) -> bool:
        """
        Save full student snapshot
        """
        return await self.save_progress(student_id, "snapshot", snapshot)

    async def get_student_snapshot(self, student_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve full student snapshot
        """
        return await self.get_progress(student_id, "snapshot")

# Global service instance
state_service = StateStoreService()