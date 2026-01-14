"""
Integration tests for State Store Service
"""

import pytest
import sys
import os
import asyncio

# Add project root to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

from services.state_store import StateStoreService

@pytest.mark.asyncio
async def test_save_and_get_progress():
    """Test saving and retrieving progress"""
    service = StateStoreService()
    service.dapr_enabled = False  # Use mock mode for testing

    test_data = {
        "mastery_level": 0.8,
        "sessions": 3,
        "last_updated": "2026-01-14T10:30:00Z"
    }

    # Save progress
    result = await service.save_progress("student123", "python_basic", test_data)
    assert result is True

    # Retrieve progress
    retrieved = await service.get_progress("student123", "python_basic")
    assert retrieved is not None
    assert retrieved["mastery_level"] == 0.8
    assert retrieved["sessions"] == 3

@pytest.mark.asyncio
async def test_student_snapshot():
    """Test student snapshot operations"""
    service = StateStoreService()
    service.dapr_enabled = False

    snapshot = {
        "total_time": 120,
        "topics_completed": 2,
        "total_sessions": 8
    }

    result = await service.save_student_snapshot("student123", snapshot)
    assert result is True

    retrieved = await service.get_student_snapshot("student123")
    assert retrieved is not None
    assert retrieved["total_time"] == 120

if __name__ == "__main__":
    pytest.main([__file__])