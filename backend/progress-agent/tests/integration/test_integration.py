"""
Integration tests for full service integration
"""

import pytest
import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'src'))

@pytest.mark.asyncio
async def test_full_progress_flow():
    """Test complete flow: save progress, retrieve, update"""
    from services.state_store import StateStoreService
    from services.mastery_calculator import calculate_mastery_with_mcp

    # Calculate mastery using MCP
    result = calculate_mastery_with_mcp(
        student_id="test_student",
        topic_id="python_basic",
        session_data={"score": 85, "time": 45}
    )

    assert result["mastery_level"] >= 0
    assert "recommendations" in result

    # Save to state store
    state_service = StateStoreService()
    state_service.dapr_enabled = False

    saved = await state_service.save_progress("test_student", "python_basic", result)
    assert saved is True

    # Retrieve and verify
    retrieved = await state_service.get_progress("test_student", "python_basic")
    assert retrieved is not None
    assert retrieved["mastery_level"] == result["mastery_level"]