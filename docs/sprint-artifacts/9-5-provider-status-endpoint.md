# Story 9.5: Provider Status Endpoint

**Epic:** 9 - Production Readiness
**Story:** 9.5 - Provider Status Endpoint
**Priority:** High
**Points:** 5
**Status:** Drafting

---

## Overview

Criar endpoint HTTP que retorna status detalhado de cada LLM provider em tempo real, mostrando rate limiting, últimos erros, latência, histórico de 429s. Essencial para monitoring e debugging em produção.

---

## Acceptance Criteria (AC)

### AC-1: Provider Status Endpoint
- [ ] `GET /providers` - Retorna lista de todos os providers configurados
- [ ] Response model: `ProviderStatusResponse` com array de `ProviderStatus` objects
- [ ] Status HTTP 200 sempre (nunca falha, mesmo se providers indisponíveis)
- [ ] Integração com metrics coletadas pelo Orchestrator

### AC-2: Provider Status Model
- [ ] `ProviderStatus` model com campos:
  - `name` (string): Provider identifier (groq, gemini, openrouter, etc)
  - `model` (string): Model name (llama-3.1-70b, gemini-2.0-flash, etc)
  - `status` (enum): "healthy" | "degraded" | "unavailable"
  - `rpm_limit` (int): Rate limit (requests per minute)
  - `rpm_current` (int): Current RPM usage
  - `rpm_available` (int): RPM remaining
  - `latency_avg_ms` (int): Average response time
  - `latency_p95_ms` (int): 95th percentile latency
  - `total_requests` (int): Total requests since startup
  - `total_failures` (int): Total failed requests
  - `failure_rate` (float): Failure rate (0.0-1.0)
  - `last_error` (Optional[str]): Last error message
  - `last_error_time` (Optional[datetime]): When last error occurred
  - `last_429_time` (Optional[datetime]): Last time rate limited
  - `last_request_time` (Optional[datetime]): Last successful request
  - `enabled` (bool): Whether provider is enabled
  - `uptime_seconds` (int): How long provider has been up

### AC-3: Metrics Collection
- [ ] Metrics collected by Orchestrator and passed to endpoint
- [ ] Per-provider tracking:
  - Total requests processed
  - Failed requests
  - Average latency + P95/P99
  - Last error and timestamp
  - Last 429 rate limit hit
  - RPM consumption (rolling window)
- [ ] Metrics retained for session duration (or configurable retention)

### AC-4: Endpoint Response Format
```json
{
  "timestamp": "2025-11-13T10:30:45Z",
  "providers": [
    {
      "name": "groq",
      "model": "llama-3.1-70b-versatile",
      "status": "healthy",
      "rpm_limit": 30,
      "rpm_current": 12,
      "rpm_available": 18,
      "latency_avg_ms": 450,
      "latency_p95_ms": 890,
      "total_requests": 245,
      "total_failures": 2,
      "failure_rate": 0.0081,
      "last_error": null,
      "last_error_time": null,
      "last_429_time": null,
      "last_request_time": "2025-11-13T10:30:42Z",
      "enabled": true,
      "uptime_seconds": 3600
    },
    {
      "name": "gemini",
      "model": "gemini-2.0-flash",
      "status": "degraded",
      "rpm_limit": 15,
      "rpm_current": 14,
      "rpm_available": 1,
      "latency_avg_ms": 2100,
      "latency_p95_ms": 3500,
      "total_requests": 120,
      "total_failures": 5,
      "failure_rate": 0.0417,
      "last_error": "Rate limit exceeded",
      "last_error_time": "2025-11-13T10:30:30Z",
      "last_429_time": "2025-11-13T10:30:30Z",
      "last_request_time": "2025-11-13T10:30:35Z",
      "enabled": true,
      "uptime_seconds": 3600
    }
  ]
}
```

### AC-5: Status Determination Logic
- [ ] "healthy": RPM available > 0, latency < 2000ms, failure_rate < 1%
- [ ] "degraded": RPM available low (< 5) OR latency >= 2000ms OR failure_rate >= 1%
- [ ] "unavailable": RPM available = 0 OR last_error_time recent (< 30 seconds) OR not enabled

### AC-6: Provider-Specific Endpoint
- [ ] `GET /providers/{provider_name}` - Get status of single provider
- [ ] Returns single `ProviderStatus` object
- [ ] Response 404 if provider not found or not enabled

### AC-7: Filtering & Sorting
- [ ] Query parameters:
  - `?status=healthy` - Filter by status
  - `?enabled=true` - Filter by enabled/disabled
  - `?sort=rpm_available` - Sort by field (asc/desc)
- [ ] Default sort: by status (healthy first) then by failure_rate (ascending)

### AC-8: Integration with Orchestrator
- [ ] Orchestrator updates provider metrics after each request
- [ ] Metrics accessible via `metrics.providers` dict or similar
- [ ] No performance impact on request handling (metrics collected async if needed)

---

## Technical Design

### 1. Provider Status Model

```python
# src/models/provider_status.py

from datetime import datetime
from typing import Optional
from enum import Enum
from pydantic import BaseModel, Field

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
    providers: list[ProviderStatus] = Field(..., description="List of provider statuses")
```

### 2. Provider Status Tracker

```python
# src/metrics/provider_status.py

from datetime import datetime, timezone
from typing import Dict, Optional
from dataclasses import dataclass, field
from collections import deque
from src.models.provider_status import ProviderStatus, ProviderStatusEnum


@dataclass
class ProviderMetrics:
    """Track metrics for a single provider."""

    total_requests: int = 0
    total_failures: int = 0
    latencies: deque = field(default_factory=lambda: deque(maxlen=1000))  # Keep last 1000
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
        self.providers: Dict[str, ProviderMetrics] = {}

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

        if success:
            pass  # Request succeeded
        else:
            metrics.total_failures += 1
            metrics.last_error = error
            metrics.last_error_time = datetime.now(timezone.utc)

    def record_rate_limit(self, provider_name: str):
        """Record a rate limit hit."""
        if provider_name not in self.providers:
            self.providers[provider_name] = ProviderMetrics()

        self.providers[provider_name].last_429_time = datetime.now(timezone.utc)

    def get_status(
        self,
        provider_name: str,
        config: dict,
        rate_limit_data: dict
    ) -> ProviderStatus:
        """Get status of a provider."""
        metrics = self.providers.get(provider_name, ProviderMetrics())

        rpm_limit = config.get("rpm_limit", 0)
        rpm_current = rate_limit_data.get("rpm_current", 0)
        rpm_available = max(0, rpm_limit - rpm_current)

        # Determine status
        status = self._calculate_status(metrics, rpm_available)

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
            uptime_seconds=int((datetime.now(timezone.utc) - self.start_time).total_seconds())
        )

    @staticmethod
    def _calculate_status(metrics: ProviderMetrics, rpm_available: int) -> ProviderStatusEnum:
        """Calculate provider status."""
        # Unavailable
        if rpm_available == 0:
            return ProviderStatusEnum.UNAVAILABLE
        if metrics.last_error_time and (
            datetime.now(timezone.utc) - metrics.last_error_time
        ).total_seconds() < 30:
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
```

### 3. API Endpoint

```python
# src/api/providers.py

from fastapi import APIRouter, Query
from typing import Optional
from datetime import datetime, timezone
from src.models.provider_status import ProviderStatusResponse, ProviderStatus

router = APIRouter(prefix="/providers", tags=["providers"])

# Global tracker instance (set by main.py)
_provider_tracker = None


def set_provider_tracker(tracker):
    """Set the provider status tracker."""
    global _provider_tracker
    _provider_tracker = tracker


@router.get(
    "",
    response_model=ProviderStatusResponse,
    summary="Get status of all LLM providers",
    description="Returns real-time status metrics for all configured LLM providers"
)
async def get_providers_status(
    status: Optional[str] = Query(None, description="Filter by status (healthy/degraded/unavailable)"),
    enabled: Optional[bool] = Query(None, description="Filter by enabled status"),
    sort: str = Query("status", description="Sort field (status, rpm_available, failure_rate)")
) -> ProviderStatusResponse:
    """Get status of all providers."""
    if not _provider_tracker:
        return ProviderStatusResponse(
            timestamp=datetime.now(timezone.utc),
            providers=[]
        )

    # Get all provider statuses
    all_statuses = _provider_tracker.get_all_statuses()

    # Filter by status
    if status:
        all_statuses = [p for p in all_statuses if p.status.value == status]

    # Filter by enabled
    if enabled is not None:
        all_statuses = [p for p in all_statuses if p.enabled == enabled]

    # Sort
    if sort == "rpm_available":
        all_statuses.sort(key=lambda p: p.rpm_available, reverse=True)
    elif sort == "failure_rate":
        all_statuses.sort(key=lambda p: p.failure_rate)
    else:  # status (default)
        status_order = {"healthy": 0, "degraded": 1, "unavailable": 2}
        all_statuses.sort(key=lambda p: (status_order.get(p.status.value, 999), p.failure_rate))

    return ProviderStatusResponse(
        timestamp=datetime.now(timezone.utc),
        providers=all_statuses
    )


@router.get(
    "/{provider_name}",
    response_model=ProviderStatus,
    summary="Get status of a specific provider",
    description="Returns real-time status metrics for a single provider"
)
async def get_provider_status(provider_name: str) -> ProviderStatus:
    """Get status of a specific provider."""
    if not _provider_tracker:
        raise HTTPException(status_code=404, detail="Provider not found")

    status = _provider_tracker.get_status(provider_name)
    if not status:
        raise HTTPException(status_code=404, detail=f"Provider {provider_name} not found")

    return status
```

---

## Testing Strategy

### Unit Tests (8 tests)
1. `test_provider_metrics_calculation` - Latency percentiles, failure rate
2. `test_status_determination_healthy` - Status logic (healthy condition)
3. `test_status_determination_degraded` - Status logic (degraded condition)
4. `test_status_determination_unavailable` - Status logic (unavailable condition)
5. `test_record_request_success` - Metrics tracking on success
6. `test_record_request_failure` - Metrics tracking on failure
7. `test_record_rate_limit` - 429 tracking
8. `test_provider_status_model_serialization` - Pydantic model validation

### Integration Tests (2 tests)
1. `test_get_providers_status_endpoint_all` - GET /providers returns all
2. `test_get_provider_status_endpoint_single` - GET /providers/{name} returns one
3. `test_provider_status_filtering_sorting` - Query params work

---

## Dependencies

- Existing: FastAPI, Pydantic, datetime, collections
- No new external dependencies

---

## Implementation Tasks

1. Create `src/models/provider_status.py` with Pydantic models
2. Create `src/metrics/provider_status.py` with ProviderStatusTracker
3. Create `src/api/providers.py` with FastAPI endpoints
4. Create `tests/unit/test_provider_status.py` with unit tests
5. Create `tests/integration/test_provider_status_endpoint.py` with integration tests
6. Update `src/api/__init__.py` to export new endpoint
7. Update `main.py` to initialize tracker and set in endpoint
8. Integration with Orchestrator: Call tracker methods after each request

---

## Definition of Done

- ✅ All 8 unit tests passing
- ✅ All 2 integration tests passing
- ✅ Endpoint responses match AC-4 format exactly
- ✅ Status determination logic matches AC-5
- ✅ Filtering and sorting working (AC-7)
- ✅ Integration with Orchestrator complete
- ✅ Sprint status updated: 9-5-provider-status-endpoint -> ready-for-dev

---

## Notes

- Metrics are kept in-memory for session duration
- For persistence, would need to integrate with PostgreSQL (future story)
- Rate limit tracking uses metrics from rate limiter modules
- No blocking operations - tracker methods are sync and fast
