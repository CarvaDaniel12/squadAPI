"""Main health check orchestrator."""

from datetime import datetime, timezone
from typing import Optional, Dict, Any

from src.models.health import HealthCheckResponse, ComponentHealth, ProviderHealth
from src.health.probes import RedisProbe, PostgresProbe, ProviderProbe


class HealthChecker:
    """Orchestrate all health checks and aggregate status."""

    def __init__(self, version: str = "1.0.0"):
        """Initialize health checker."""
        self.version = version
        self.start_time = datetime.now(timezone.utc)

    async def check_all(
        self,
        redis_client: Optional[Any] = None,
        db_pool: Optional[Any] = None,
        providers_health: Optional[Dict[str, Dict[str, Any]]] = None
    ) -> HealthCheckResponse:
        """Run all health checks."""
        components = {}

        # Check Redis
        if redis_client:
            redis_probe = RedisProbe()
            components["redis"] = await redis_probe.check(redis_client)

        # Check PostgreSQL
        if db_pool:
            postgres_probe = PostgresProbe()
            components["postgres"] = await postgres_probe.check(db_pool)

        # Check providers
        if providers_health:
            for provider_name, metrics in providers_health.items():
                components[provider_name] = await ProviderProbe.check(
                    provider_name=provider_name,
                    rpm_limit=metrics.get("rpm_limit", 0),
                    rpm_current=metrics.get("rpm_current", 0),
                    latency_avg_ms=metrics.get("latency_avg_ms", 0),
                    last_429_time=metrics.get("last_429_time")
                )

        # Calculate overall status and uptime
        overall_status = self._calculate_overall_status(components)
        uptime_seconds = int((datetime.now(timezone.utc) - self.start_time).total_seconds())

        return HealthCheckResponse(
            status=overall_status,
            timestamp=datetime.now(timezone.utc),
            uptime_seconds=uptime_seconds,
            version=self.version,
            components=components
        )

    @staticmethod
    def _calculate_overall_status(components: Dict[str, Any]) -> str:
        """Calculate overall status from component statuses."""
        if not components:
            return "healthy"

        statuses = [
            comp.status if isinstance(comp, (ComponentHealth, ProviderHealth))
            else comp.get("status", "unknown")
            for comp in components.values()
        ]

        # Logic: all healthy = healthy, any unavailable = unhealthy, otherwise degraded
        if "unavailable" in statuses:
            return "unhealthy"
        elif "degraded" in statuses:
            return "degraded"
        else:
            return "healthy"
