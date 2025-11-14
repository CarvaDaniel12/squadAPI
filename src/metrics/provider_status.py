"""Provider status models and tracking."""

from datetime import datetime, timezone
from typing import Optional, Dict, List
from enum import Enum
from pydantic import BaseModel, Field
from dataclasses import dataclass, field
from collections import deque


class ProviderStatusEnum(str, Enum):
    """Provider status enumeration."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNAVAILABLE = "unavailable"


class ProviderStatus(BaseModel):
    """Status of a single LLM provider."""

    name: str = Field(..., description="Provider identifier (groq, gemini, etc)")
    model: str = Field(..., description="Model name")
    status: ProviderStatusEnum = Field(..., description="Current status")

    # Rate limiting
    rpm_limit: int = Field(..., description="Rate limit (requests per minute)")
    rpm_current: int = Field(..., description="Current RPM usage")
    rpm_available: int = Field(..., description="RPM remaining")

    # Performance
    latency_avg_ms: int = Field(default=0, description="Average response time (ms)")
    latency_p95_ms: int = Field(default=0, description="95th percentile latency (ms)")

    # Request stats
    total_requests: int = Field(default=0, description="Total requests since startup")
    total_failures: int = Field(default=0, description="Total failed requests")
    failure_rate: float = Field(default=0.0, description="Failure rate 0.0-1.0")

    # Errors
    last_error: Optional[str] = Field(default=None, description="Last error message")
    last_error_time: Optional[datetime] = Field(default=None, description="Last error timestamp")
    last_429_time: Optional[datetime] = Field(default=None, description="Last rate limit hit")

    # Availability
    last_request_time: Optional[datetime] = Field(default=None, description="Last successful request")
    enabled: bool = Field(default=True, description="Whether provider is enabled")
    uptime_seconds: int = Field(default=0, description="Uptime in seconds")


class ProviderStatusResponse(BaseModel):
    """Response with all provider statuses."""

    timestamp: datetime = Field(..., description="Response timestamp")
    providers: List[ProviderStatus] = Field(..., description="List of provider statuses")


@dataclass
class ProviderMetrics:
    """Track metrics for a single provider."""

    total_requests: int = 0
    total_failures: int = 0
    latencies: deque = field(default_factory=lambda: deque(maxlen=1000))
    last_error: Optional[str] = None
    last_error_time: Optional[datetime] = None
    last_429_time: Optional[datetime] = None
    last_request_time: Optional[datetime] = None
    rpm_current: int = 0

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate."""
        if self.total_requests == 0:
            return 0.0
        return self.total_failures / self.total_requests

    @property
    def avg_latency_ms(self) -> int:
        """Calculate average latency."""
        if not self.latencies:
            return 0
        return int(sum(self.latencies) / len(self.latencies))

    @property
    def p95_latency_ms(self) -> int:
        """Calculate 95th percentile latency."""
        if not self.latencies:
            return 0
        sorted_latencies = sorted(self.latencies)
        idx = int(len(sorted_latencies) * 0.95)
        return sorted_latencies[idx] if idx < len(sorted_latencies) else sorted_latencies[-1]


class ProviderStatusTracker:
    """Track status of all providers."""

    def __init__(self):
        """Initialize tracker."""
        self.providers: Dict[str, ProviderMetrics] = {}
        self.start_time = datetime.now(timezone.utc)

    def record_request(
        self,
        provider_name: str,
        latency_ms: int,
        success: bool = True,
        error: Optional[str] = None
    ):
        """Record a request metric."""
        if provider_name not in self.providers:
            self.providers[provider_name] = ProviderMetrics()

        metrics = self.providers[provider_name]
        metrics.total_requests += 1
        metrics.latencies.append(latency_ms)
        metrics.last_request_time = datetime.now(timezone.utc)

        if not success:
            metrics.total_failures += 1
            if error:
                metrics.last_error = error
            metrics.last_error_time = datetime.now(timezone.utc)

    def record_rate_limit(self, provider_name: str):
        """Record a rate limit hit."""
        if provider_name not in self.providers:
            self.providers[provider_name] = ProviderMetrics()

        self.providers[provider_name].last_429_time = datetime.now(timezone.utc)

    def set_rpm_current(self, provider_name: str, rpm_current: int):
        """Set current RPM usage."""
        if provider_name not in self.providers:
            self.providers[provider_name] = ProviderMetrics()

        self.providers[provider_name].rpm_current = rpm_current

    def get_status(
        self,
        provider_name: str,
        config: dict
    ) -> Optional[ProviderStatus]:
        """Get status of a provider."""
        if not config:
            return None

        metrics = self.providers.get(provider_name, ProviderMetrics())

        rpm_limit = config.get("rpm_limit", 0)
        rpm_current = metrics.rpm_current
        rpm_available = max(0, rpm_limit - rpm_current)

        # Determine status
        status = self._calculate_status(metrics, rpm_available, config)

        uptime = int((datetime.now(timezone.utc) - self.start_time).total_seconds())

        return ProviderStatus(
            name=provider_name,
            model=config.get("model", "unknown"),
            status=status,
            rpm_limit=rpm_limit,
            rpm_current=rpm_current,
            rpm_available=rpm_available,
            latency_avg_ms=metrics.avg_latency_ms,
            latency_p95_ms=metrics.p95_latency_ms,
            total_requests=metrics.total_requests,
            total_failures=metrics.total_failures,
            failure_rate=metrics.failure_rate,
            last_error=metrics.last_error,
            last_error_time=metrics.last_error_time,
            last_429_time=metrics.last_429_time,
            last_request_time=metrics.last_request_time,
            enabled=config.get("enabled", True),
            uptime_seconds=uptime
        )

    def get_all_statuses(
        self,
        providers_config: Optional[Dict] = None
    ) -> List[ProviderStatus]:
        """Get status of all providers."""
        if not providers_config:
            providers_config = {}

        statuses = []
        for provider_name, config in providers_config.items():
            status = self.get_status(provider_name, config)
            if status:
                statuses.append(status)

        return statuses

    @staticmethod
    def _calculate_status(
        metrics: ProviderMetrics,
        rpm_available: int,
        config: dict
    ) -> ProviderStatusEnum:
        """Calculate provider status."""
        if not config.get("enabled", True):
            return ProviderStatusEnum.UNAVAILABLE

        # Unavailable
        if rpm_available == 0:
            return ProviderStatusEnum.UNAVAILABLE

        if metrics.last_error_time:
            time_since_error = (datetime.now(timezone.utc) - metrics.last_error_time).total_seconds()
            if time_since_error < 30:
                return ProviderStatusEnum.UNAVAILABLE

        # Degraded
        if rpm_available < 5:
            return ProviderStatusEnum.DEGRADED
        if metrics.avg_latency_ms >= 2000:
            return ProviderStatusEnum.DEGRADED
        if metrics.failure_rate >= 0.01:
            return ProviderStatusEnum.DEGRADED

        # Healthy
        return ProviderStatusEnum.HEALTHY
