"""Individual health check probes for each component."""

import time
from typing import Optional

from src.models.health import ComponentHealth, ProviderHealth


class HealthProbe:
    """Base health probe."""

    async def check(self) -> ComponentHealth:
        """Run health check. Override in subclasses."""
        raise NotImplementedError


class RedisProbe(HealthProbe):
    """Check Redis connectivity and performance."""

    LATENCY_THRESHOLD_MS = 10

    async def check(self, redis_client) -> ComponentHealth:
        """Probe Redis."""
        try:
            start = time.time()
            await redis_client.ping()
            latency_ms = int((time.time() - start) * 1000)

            info = await redis_client.info()

            status = "healthy" if latency_ms < self.LATENCY_THRESHOLD_MS else "degraded"

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
                latency_ms=None,
                details={"error": str(e)}
            )


class PostgresProbe(HealthProbe):
    """Check PostgreSQL connectivity and pool health."""

    LATENCY_THRESHOLD_MS = 20

    async def check(self, db_pool) -> ComponentHealth:
        """Probe PostgreSQL."""
        try:
            start = time.time()

            async with db_pool.acquire() as conn:
                await conn.fetchval("SELECT 1")

            latency_ms = int((time.time() - start) * 1000)

            status = "healthy" if latency_ms < self.LATENCY_THRESHOLD_MS else "degraded"

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
                latency_ms=None,
                details={"error": str(e)}
            )


class ProviderProbe:
    """Check provider health using metrics."""

    LATENCY_THRESHOLD_MS = 5000

    @staticmethod
    async def check(
        provider_name: str,
        rpm_limit: int = 0,
        rpm_current: int = 0,
        latency_avg_ms: int = 0,
        last_429_time: Optional[str] = None
    ) -> ProviderHealth:
        """Check provider health from metrics."""
        rpm_available = max(0, rpm_limit - rpm_current)

        # Status logic
        if rpm_available == 0:
            status = "degraded"
        elif latency_avg_ms > ProviderProbe.LATENCY_THRESHOLD_MS:
            status = "degraded"
        else:
            status = "healthy"

        return ProviderHealth(
            status=status,
            rpm_limit=rpm_limit,
            rpm_current=rpm_current,
            rpm_available=rpm_available,
            latency_avg_ms=latency_avg_ms,
            last_429=last_429_time
        )
