# Story 9.4: Health Check Endpoint Enhancement

**Epic:** 9 - Production Readiness
**Story ID:** 9.4
**Sprint:** 8 (Production Readiness)
**Status:** Drafted
**Date Created:** 2025-11-13
**Assignee:** DEV Agent

---

## Story Summary

**As a** operator,
**I want** detailed health checks for all system components,
**So that** I can verify the status of all infrastructure and providers before deciding to handle traffic.

**Story Points:** 8
**Priority:** MUST-HAVE (Operations)
**Complexity:** High

---

## Acceptance Criteria

### AC1: Basic Health Status
**Given** Squad API is running
**When** I call `GET /health`
**Then** the response includes:
- ✅ `status`: "healthy" or "degraded" or "unhealthy"
- ✅ `timestamp`: ISO 8601 format (2025-11-13T10:30:45Z)
- ✅ `uptime_seconds`: seconds since application started
- ✅ HTTP Status Code: 200 (even if degraded) or 503 (if critical failure)

**Example:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-13T10:30:45Z",
  "uptime_seconds": 3600,
  "version": "1.0.0"
}
```

### AC2: Redis Health Check
**Given** Redis is configured
**When** health check runs
**Then** must include:
- ✅ `redis.status`: "healthy" / "degraded" / "unavailable"
- ✅ `redis.latency_ms`: response time in milliseconds
- ✅ `redis.used_memory_mb`: current memory usage
- ✅ `redis.connected_clients`: number of connected clients

**Example:**
```json
{
  "components": {
    "redis": {
      "status": "healthy",
      "latency_ms": 2,
      "used_memory_mb": 45,
      "connected_clients": 3
    }
  }
}
```

### AC3: PostgreSQL Health Check
**Given** PostgreSQL is configured
**When** health check runs
**Then** must include:
- ✅ `postgres.status`: "healthy" / "degraded" / "unavailable"
- ✅ `postgres.latency_ms`: query response time
- ✅ `postgres.pool_size`: current connection pool size
- ✅ `postgres.pool_available`: available connections in pool

**Example:**
```json
{
  "components": {
    "postgres": {
      "status": "healthy",
      "latency_ms": 5,
      "pool_size": 10,
      "pool_available": 8
    }
  }
}
```

### AC4: Provider Health Checks
**Given** multiple LLM providers configured
**When** health check runs
**Then** must include per-provider status:
- ✅ `providers.<name>.status`: "healthy" / "degraded" / "unavailable"
- ✅ `providers.<name>.rpm_limit`: configured RPM limit
- ✅ `providers.<name>.rpm_current`: current RPM usage
- ✅ `providers.<name>.rpm_available`: remaining capacity
- ✅ `providers.<name>.latency_avg_ms`: average response time
- ✅ `providers.<name>.last_429`: timestamp of last 429 error (null if none)

**Example:**
```json
{
  "components": {
    "providers": {
      "groq": {
        "status": "healthy",
        "rpm_limit": 12,
        "rpm_current": 3,
        "rpm_available": 9,
        "latency_avg_ms": 1850,
        "last_429": null
      },
      "cerebras": {
        "status": "healthy",
        "rpm_limit": 60,
        "rpm_current": 15,
        "rpm_available": 45,
        "latency_avg_ms": 2100,
        "last_429": null
      },
      "openrouter": {
        "status": "degraded",
        "rpm_limit": 30,
        "rpm_current": 30,
        "rpm_available": 0,
        "latency_avg_ms": 3500,
        "last_429": "2025-11-13T10:20:00Z"
      }
    }
  }
}
```

### AC5: Overall Status Logic
**When** calculating overall status
**Then** apply these rules:
- ✅ "healthy": All components healthy
- ✅ "degraded":
  - At least one provider has `rpm_available == 0`
  - OR at least one component has latency > threshold
  - OR at least one component "degraded"
- ✅ "unhealthy":
  - Critical components down (Redis/Postgres)
  - OR all providers unavailable
- ✅ HTTP Status: 200 for any status, 503 if unhealthy

**Example Status Transitions:**
```
All healthy              → status: "healthy"   (HTTP 200)
1 provider degraded     → status: "degraded"  (HTTP 200)
Redis down              → status: "unhealthy" (HTTP 503)
All providers 429       → status: "unhealthy" (HTTP 503)
```

### AC6: Performance Thresholds
**When** calculating component status
**Then** use these thresholds:
- ✅ Redis latency: > 10ms = degraded
- ✅ PostgreSQL latency: > 20ms = degraded
- ✅ Provider latency: > 5000ms = degraded
- ✅ Provider RPM: available < 1 = degraded

### AC7: Rate Limiter Status
**When** health check includes rate limiting info
**Then** must show:
- ✅ `rate_limiter.status`: active state
- ✅ `rate_limiter.algorithm`: "token_bucket" / "sliding_window" / "combined"
- ✅ `rate_limiter.throttled_providers`: list of currently throttled providers
- ✅ `rate_limiter.auto_throttle_events`: number of auto-throttle triggers

**Example:**
```json
{
  "components": {
    "rate_limiter": {
      "status": "healthy",
      "algorithm": "combined",
      "throttled_providers": [],
      "auto_throttle_events": 0
    }
  }
}
```

### AC8: Response Format
**When** calling `/health`
**Then** response format:
- ✅ Content-Type: application/json
- ✅ All timestamps: ISO 8601 UTC
- ✅ All latencies: milliseconds (integer)
- ✅ All percentages: 0-100 (integer)

**Full Example Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-13T10:30:45Z",
  "uptime_seconds": 3600,
  "version": "1.0.0",
  "components": {
    "redis": {
      "status": "healthy",
      "latency_ms": 2,
      "used_memory_mb": 45,
      "connected_clients": 3
    },
    "postgres": {
      "status": "healthy",
      "latency_ms": 5,
      "pool_size": 10,
      "pool_available": 8
    },
    "rate_limiter": {
      "status": "healthy",
      "algorithm": "combined",
      "throttled_providers": [],
      "auto_throttle_events": 0
    },
    "providers": {
      "groq": {
        "status": "healthy",
        "rpm_limit": 12,
        "rpm_current": 3,
        "rpm_available": 9,
        "latency_avg_ms": 1850,
        "last_429": null
      },
      "cerebras": {
        "status": "healthy",
        "rpm_limit": 60,
        "rpm_current": 15,
        "rpm_available": 45,
        "latency_avg_ms": 2100,
        "last_429": null
      }
    }
  }
}
```

---

## Technical Design

### Module Structure

```
src/
├── health/
│   ├── __init__.py           # Exports
│   ├── checker.py            # HealthChecker class
│   ├── probes.py             # Individual health probes
│
├── models/
│   └── health.py             # Pydantic models for health responses
│
├── api/
│   └── health.py             # Health endpoint (GET /health)
```

### Core Implementation

#### 1. **Health Models** (`src/models/health.py`)

```python
"""Pydantic models for health check responses."""

from typing import Dict, Optional, Any
from datetime import datetime
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
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Check timestamp")
    uptime_seconds: int = Field(..., description="Uptime in seconds")
    version: str = Field("1.0.0", description="API version")
    components: Dict[str, Any] = Field(default_factory=dict, description="Component health statuses")
```

#### 2. **Health Probes** (`src/health/probes.py`)

```python
"""Individual health check probes for each component."""

import time
import asyncio
from typing import Dict, Optional

from src.models.health import ComponentHealth, ProviderHealth


class HealthProbe:
    """Base health probe."""

    async def check(self) -> ComponentHealth:
        """Run health check. Override in subclasses."""
        raise NotImplementedError


class RedisProbe(HealthProbe):
    """Check Redis connectivity and performance."""

    async def check(self, redis_client) -> ComponentHealth:
        """Probe Redis."""
        try:
            start = time.time()
            await redis_client.ping()
            latency_ms = int((time.time() - start) * 1000)

            info = await redis_client.info()

            status = "healthy" if latency_ms < 10 else "degraded"

            return ComponentHealth(
                status=status,
                latency_ms=latency_ms,
                details={
                    "used_memory_mb": info.get("used_memory", 0) // 1024 // 1024,
                    "connected_clients": info.get("connected_clients", 0)
                }
            )
        except Exception as e:
            return ComponentHealth(
                status="unavailable",
                details={"error": str(e)}
            )


class PostgresProbe(HealthProbe):
    """Check PostgreSQL connectivity and pool health."""

    async def check(self, db_pool) -> ComponentHealth:
        """Probe PostgreSQL."""
        try:
            start = time.time()

            async with db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")

            latency_ms = int((time.time() - start) * 1000)

            status = "healthy" if latency_ms < 20 else "degraded"

            return ComponentHealth(
                status=status,
                latency_ms=latency_ms,
                details={
                    "pool_size": db_pool.get_size(),
                    "pool_available": db_pool.get_idle_size()
                }
            )
        except Exception as e:
            return ComponentHealth(
                status="unavailable",
                details={"error": str(e)}
            )


class ProviderProbe:
    """Check provider health using metrics."""

    @staticmethod
    async def check(provider_name: str, metrics) -> ProviderHealth:
        """Check provider health from metrics."""
        provider_metrics = metrics.get_provider_metrics(provider_name)

        rpm_limit = provider_metrics.get("rpm_limit", 0)
        rpm_current = provider_metrics.get("rpm_current", 0)
        rpm_available = max(0, rpm_limit - rpm_current)
        latency_avg = provider_metrics.get("latency_avg_ms", 0)
        last_429 = provider_metrics.get("last_429_time", None)

        # Status logic
        if rpm_available == 0:
            status = "degraded"
        elif latency_avg > 5000:
            status = "degraded"
        else:
            status = "healthy"

        return ProviderHealth(
            status=status,
            rpm_limit=rpm_limit,
            rpm_current=rpm_current,
            rpm_available=rpm_available,
            latency_avg_ms=latency_avg,
            last_429=last_429
        )
```

#### 3. **Health Checker** (`src/health/checker.py`)

```python
"""Main health check orchestrator."""

import time
from datetime import datetime, timezone
from typing import Dict, Any

from src.health.probes import RedisProbe, PostgresProbe, ProviderProbe
from src.models.health import HealthCheckResponse


class HealthChecker:
    """Orchestrate health checks for all components."""

    # Thresholds
    THRESHOLD_REDIS_LATENCY = 10  # ms
    THRESHOLD_POSTGRES_LATENCY = 20  # ms
    THRESHOLD_PROVIDER_LATENCY = 5000  # ms

    def __init__(self, redis_client=None, db_pool=None, metrics=None, providers=None):
        """Initialize health checker with dependencies."""
        self.redis_client = redis_client
        self.db_pool = db_pool
        self.metrics = metrics
        self.providers = providers or {}

        self.start_time = time.time()
        self.redis_probe = RedisProbe()
        self.postgres_probe = PostgresProbe()

    async def check(self) -> HealthCheckResponse:
        """Run complete health check."""
        components: Dict[str, Any] = {}

        # Check Redis
        if self.redis_client:
            redis_health = await self.redis_probe.check(self.redis_client)
            components["redis"] = redis_health.model_dump()

        # Check PostgreSQL
        if self.db_pool:
            postgres_health = await self.postgres_probe.check(self.db_pool)
            components["postgres"] = postgres_health.model_dump()

        # Check providers
        if self.providers:
            provider_health = {}
            for provider_name in self.providers.keys():
                health = await ProviderProbe.check(provider_name, self.metrics)
                provider_health[provider_name] = health.model_dump()
            components["providers"] = provider_health

        # Calculate overall status
        overall_status = self._calculate_overall_status(components)

        # Build response
        uptime_seconds = int(time.time() - self.start_time)

        return HealthCheckResponse(
            status=overall_status,
            timestamp=datetime.now(timezone.utc),
            uptime_seconds=uptime_seconds,
            components=components
        )

    def _calculate_overall_status(self, components: Dict[str, Any]) -> str:
        """Calculate overall status based on component statuses."""
        has_critical_down = False
        has_degraded = False

        # Check critical components
        if "redis" in components and components["redis"]["status"] == "unavailable":
            has_critical_down = True
        if "postgres" in components and components["postgres"]["status"] == "unavailable":
            has_critical_down = True

        # Check providers
        if "providers" in components:
            all_providers_down = all(
                p.get("status") == "unavailable"
                for p in components["providers"].values()
            )
            if all_providers_down:
                has_critical_down = True

            if any(p.get("status") == "degraded" for p in components["providers"].values()):
                has_degraded = True

        # Determine status
        if has_critical_down:
            return "unhealthy"
        elif has_degraded or any(c.get("status") == "degraded" for c in components.values()):
            return "degraded"
        else:
            return "healthy"
```

#### 4. **Health Endpoint** (`src/api/health.py`)

```python
"""Health check endpoint."""

from fastapi import APIRouter, Response
from src.health.checker import HealthChecker

router = APIRouter()


@router.get("/health")
async def health_check(
    redis_client = None,  # Injected
    db_pool = None,       # Injected
    metrics = None,       # Injected
    providers = None      # Injected
) -> Response:
    """
    GET /health - Complete health check endpoint.

    Returns 200 for healthy/degraded, 503 for unhealthy.
    """
    checker = HealthChecker(
        redis_client=redis_client,
        db_pool=db_pool,
        metrics=metrics,
        providers=providers
    )

    response = await checker.check()

    status_code = 503 if response.status == "unhealthy" else 200

    return Response(
        content=response.model_dump_json(),
        status_code=status_code,
        media_type="application/json"
    )
```

---

## Testing Strategy

### Unit Tests (8 tests)

1. **test_redis_health_check_success**
   - Mock: Redis ping succeeds
   - Assert: status="healthy", latency < 10ms

2. **test_redis_health_check_slow**
   - Mock: Redis responds in 15ms
   - Assert: status="degraded"

3. **test_redis_health_check_failed**
   - Mock: Redis connection fails
   - Assert: status="unavailable"

4. **test_postgres_health_check_success**
   - Mock: Query succeeds in 5ms
   - Assert: status="healthy", pool_available > 0

5. **test_provider_health_degraded**
   - Mock: Provider at RPM limit (available=0)
   - Assert: status="degraded"

6. **test_overall_status_healthy**
   - All components healthy
   - Assert: status="healthy"

7. **test_overall_status_degraded**
   - One provider degraded
   - Assert: status="degraded"

8. **test_overall_status_unhealthy**
   - Critical component (Redis) down
   - Assert: status="unhealthy"

### Integration Tests (2 tests)

1. **test_health_endpoint_200_healthy**
   - Call: GET /health (all healthy)
   - Assert: HTTP 200, status="healthy"

2. **test_health_endpoint_503_unhealthy**
   - Call: GET /health (critical down)
   - Assert: HTTP 503, status="unhealthy"

---

## Success Metrics

- ✅ All 10 tests passing (8 unit + 2 integration)
- ✅ Health endpoint responsive < 500ms
- ✅ Comprehensive component coverage
- ✅ Clear status transitions
- ✅ Proper HTTP status codes
- ✅ Ready for monitoring/alerting integration

---

## Definition of Done

- [ ] `src/health/checker.py` created with HealthChecker class
- [ ] `src/health/probes.py` created with component probes
- [ ] `src/models/health.py` created with Pydantic models
- [ ] `src/api/health.py` created with endpoint
- [ ] 8 unit tests written and passing
- [ ] 2 integration tests written and passing
- [ ] Endpoint integrated into FastAPI app
- [ ] HTTP status codes correct (200/503)
- [ ] Documentation complete
- [ ] Code review passed
- [ ] Ready for production deployment

---

## References

- **Epic 9:** `docs/epics.md` (line 3358+)
- **Related Stories:** 0.7 (health foundation), 9.5 (provider status)
- **Deployment:** Story 8.3 (deployment runbook)

