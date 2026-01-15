"""
API Endpoints Module
====================

Contains all API endpoint routers.
"""

from .mastery import mastery_router
from .recommendations import recommendations_router
from .analytics import analytics_router

__all__ = [
    "mastery_router",
    "recommendations_router",
    "analytics_router"
]