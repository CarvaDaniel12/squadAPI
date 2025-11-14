"""Pydantic models for health check responses."""

from typing import Dict, Optional, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field


class ComponentHealth(BaseModel):
    """Health status of a single component."""
    status: str = Field(..., description="healthy|degraded|unavailable")
    latency_ms: Optional[int] = Field(None, description="Response latency in ms")
    details: Dict[str, Any] = Field(default_factory=dict, description="Component-specific details")


class ProviderHealth(BaseModel):
    """Health status of an LLM provider."""
    status: str = Field(..., description="healthy|degraded|unavailable")
    rpm_limit: int = Field(..., description="RPM limit")
    rpm_current: int = Field(default=0, description="Current RPM usage")
    rpm_available: int = Field(..., description="Remaining RPM capacity")
    latency_avg_ms: int = Field(..., description="Average response latency")
    last_429: Optional[datetime] = Field(None, description="Last 429 error timestamp")


class HealthCheckResponse(BaseModel):
    """Complete health check response."""
    status: str = Field(..., description="healthy|degraded|unhealthy")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Check timestamp")
    uptime_seconds: int = Field(..., description="Uptime in seconds")
    version: str = Field("1.0.0", description="API version")
    components: Dict[str, Any] = Field(default_factory=dict, description="Component health statuses")
