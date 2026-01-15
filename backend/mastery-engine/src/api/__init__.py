"""
API Module
===========

Contains FastAPI application setup, routes, and middleware.
"""

from .endpoints.mastery import mastery_router
from .endpoints.recommendations import recommendations_router
from .endpoints.analytics import analytics_router

__all__ = [
    "mastery_router",
    "recommendations_router",
    "analytics_router"
]