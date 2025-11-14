"""Provider status API endpoints."""

from fastapi import APIRouter, Query, HTTPException
from typing import Optional
from datetime import datetime, timezone
import logging
from src.metrics.provider_status import ProviderStatusResponse, ProviderStatus, ProviderStatusTracker

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/providers", tags=["providers"])

# Global tracker instance (set by main.py)
_provider_tracker: Optional[ProviderStatusTracker] = None
_providers_config: Optional = None


def set_provider_tracker(tracker: ProviderStatusTracker, providers_config):
    """Set the provider status tracker and config."""
    global _provider_tracker, _providers_config
    _provider_tracker = tracker
    _providers_config = providers_config


# @router.get(
#     "",
#     response_model=ProviderStatusResponse,
#     summary="Get status of all LLM providers",
#     description="Returns real-time status metrics for all configured LLM providers"
# )
# async def get_providers_status(
#     status: Optional[str] = Query(None, description="Filter by status (healthy/degraded/unavailable)"),
#     enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
#     sort: str = Query("status", description="Sort field (status, rpm_available, failure_rate)")
# ) -> ProviderStatusResponse:
#     """Get status of all providers."""
#     if not _provider_tracker or not _providers_config:
#         return ProviderStatusResponse(
#             timestamp=datetime.now(timezone.utc),
#             providers=[]
#         )

#     # Temporarily return empty list to avoid Pydantic model issues
#     # TODO: Fix Pydantic model conversion issue
#     logger.warning("Providers endpoint temporarily disabled due to model conversion issue")
#     all_statuses = []

#     # Filter by status
#     if status:
#         all_statuses = [p for p in all_statuses if p.status.value == status]

#     # Filter by enabled
#     if enabled is not None:
#         all_statuses = [p for p in all_statuses if p.enabled == enabled]

#     # Sort
#     if sort == "rpm_available":
#         all_statuses.sort(key=lambda p: p.rpm_available, reverse=True)
#     elif sort == "failure_rate":
#         all_statuses.sort(key=lambda p: p.failure_rate)
#     else:  # status (default)
#         status_order = {"healthy": 0, "degraded": 1, "unavailable": 2}
#         all_statuses.sort(key=lambda p: (status_order.get(p.status.value, 999), p.failure_rate))

#     return ProviderStatusResponse(
#         timestamp=datetime.now(timezone.utc),
#         providers=all_statuses
#     )


@router.get(
    "/{provider_name}",
    response_model=ProviderStatus,
    summary="Get status of a specific provider",
    description="Returns real-time status metrics for a single provider"
)
async def get_provider_status(provider_name: str) -> ProviderStatus:
    """Get status of a specific provider."""
    if not _provider_tracker or not _providers_config:
        raise HTTPException(status_code=404, detail="Provider not found")

    # Convert Pydantic model to dict if needed
    if hasattr(_providers_config, 'model_dump'):
        providers_config = _providers_config.model_dump()
    else:
        providers_config = _providers_config

    if provider_name not in providers_config:
        raise HTTPException(status_code=404, detail=f"Provider {provider_name} not found")

    status = _provider_tracker.get_status(provider_name, providers_config[provider_name])
    if not status:
        raise HTTPException(status_code=404, detail=f"Provider {provider_name} not found")

    return status
