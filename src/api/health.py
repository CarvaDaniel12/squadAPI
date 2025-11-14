"""Health check API endpoints."""

from fastapi import APIRouter, Depends, status
from typing import Optional

from src.models.health import HealthCheckResponse

router = APIRouter(prefix="/health", tags=["health"])


# Global health checker instance (set by main.py)
_health_checker = None


def set_health_checker(checker):
    """Set the health checker instance."""
    global _health_checker
    _health_checker = checker


def get_health_checker():
    """Get the health checker instance."""
    return _health_checker


@router.get(
    "",
    response_model=HealthCheckResponse,
    status_code=status.HTTP_200_OK,
    responses={
        503: {"description": "Service Unhealthy"}
    }
)
async def get_health(
    checker = Depends(get_health_checker)
) -> HealthCheckResponse:
    """
    Get detailed health status of all components.

    Returns:
        - 200: All checks passed, status will be "healthy" or "degraded"
        - 503: Critical component unavailable, status will be "unhealthy"
    """
    from datetime import datetime, timezone

    if not checker:
        return HealthCheckResponse(
            status="unknown",
            timestamp=datetime.now(timezone.utc),
            uptime_seconds=0,
            version="unknown",
            components={}
        )

    response = await checker.check_all()

    # If unhealthy, return 503
    if response.status == "unhealthy":
        return response

    return response
