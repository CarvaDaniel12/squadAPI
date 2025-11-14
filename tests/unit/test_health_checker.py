"""Unit tests for health checker."""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

from src.health.checker import HealthChecker
from src.health.probes import RedisProbe, PostgresProbe, ProviderProbe
from src.models.health import ComponentHealth, ProviderHealth, HealthCheckResponse


@pytest.fixture
def health_checker():
    """Create a health checker instance."""
    return HealthChecker(version="1.0.0")


@pytest.fixture
def mock_redis_client():
    """Create a mock Redis client."""
    client = AsyncMock()
    client.ping = AsyncMock()
    client.info = AsyncMock(return_value={
        "used_memory": 10485760,  # 10MB
        "connected_clients": 5
    })
    return client


@pytest.fixture
def mock_db_pool():
    """Create a mock database pool."""
    from contextlib import asynccontextmanager

    pool = AsyncMock()
    pool.get_size = MagicMock(return_value=10)
    pool.get_idle_size = MagicMock(return_value=8)

    # Setup the async context manager properly using asynccontextmanager
    @asynccontextmanager
    async def acquire_context():
        conn = AsyncMock()
        conn.fetchval = AsyncMock(return_value=1)
        yield conn

    pool.acquire = acquire_context

    return pool
class TestRedisProbe:
    """Tests for Redis health probe."""

    @pytest.mark.asyncio
    async def test_redis_healthy(self, mock_redis_client):
        """Test Redis when healthy (latency < 10ms)."""
        probe = RedisProbe()
        health = await probe.check(mock_redis_client)

        assert health.status == "healthy"
        assert health.latency_ms is not None
        assert health.details["connected_clients"] == 5
        assert health.details["used_memory_mb"] == 10

    @pytest.mark.asyncio
    async def test_redis_degraded(self, mock_redis_client):
        """Test Redis when degraded (latency >= 10ms)."""
        probe = RedisProbe()

        # Patch time.time to simulate high latency
        with patch("time.time") as mock_time:
            mock_time.side_effect = [0, 0.015]  # 15ms latency
            health = await probe.check(mock_redis_client)

        assert health.status == "degraded"
        assert health.latency_ms >= 10

    @pytest.mark.asyncio
    async def test_redis_unavailable(self, mock_redis_client):
        """Test Redis when unavailable (connection error)."""
        mock_redis_client.ping.side_effect = ConnectionError("Connection refused")
        probe = RedisProbe()
        health = await probe.check(mock_redis_client)

        assert health.status == "unavailable"
        assert health.latency_ms is None
        assert "error" in health.details


class TestPostgresProbe:
    """Tests for PostgreSQL health probe."""

    @pytest.mark.asyncio
    async def test_postgres_healthy(self, mock_db_pool):
        """Test PostgreSQL when healthy (latency < 20ms)."""
        probe = PostgresProbe()
        health = await probe.check(mock_db_pool)

        assert health.status == "healthy"
        assert health.latency_ms is not None
        assert health.details["pool_size"] == 10
        assert health.details["pool_available"] == 8

    @pytest.mark.asyncio
    async def test_postgres_degraded(self, mock_db_pool):
        """Test PostgreSQL when degraded (latency >= 20ms)."""
        probe = PostgresProbe()

        with patch("time.time") as mock_time:
            mock_time.side_effect = [0, 0.025]  # 25ms latency
            health = await probe.check(mock_db_pool)

        assert health.status == "degraded"
        assert health.latency_ms >= 20

    @pytest.mark.asyncio
    async def test_postgres_unavailable(self):
        """Test PostgreSQL when unavailable (pool error)."""
        pool = AsyncMock()
        pool.acquire = AsyncMock(side_effect=Exception("Pool exhausted"))
        pool.get_size = MagicMock(return_value=10)
        pool.get_idle_size = MagicMock(return_value=8)

        probe = PostgresProbe()
        health = await probe.check(pool)

        assert health.status == "unavailable"
        assert health.latency_ms is None
        assert "error" in health.details


class TestProviderProbe:
    """Tests for provider health probe."""

    @pytest.mark.asyncio
    async def test_provider_healthy(self):
        """Test provider when healthy (available RPM and low latency)."""
        health = await ProviderProbe.check(
            provider_name="groq",
            rpm_limit=100,
            rpm_current=20,
            latency_avg_ms=500
        )

        assert health.status == "healthy"
        assert health.rpm_available == 80
        assert health.rpm_current == 20

    @pytest.mark.asyncio
    async def test_provider_rate_limited(self):
        """Test provider when rate limited (no available RPM)."""
        health = await ProviderProbe.check(
            provider_name="groq",
            rpm_limit=100,
            rpm_current=100,
            latency_avg_ms=500
        )

        assert health.status == "degraded"
        assert health.rpm_available == 0

    @pytest.mark.asyncio
    async def test_provider_high_latency(self):
        """Test provider when high latency (> 5000ms)."""
        health = await ProviderProbe.check(
            provider_name="gemini",
            rpm_limit=100,
            rpm_current=10,
            latency_avg_ms=6000
        )

        assert health.status == "degraded"
        assert health.rpm_available == 90

    @pytest.mark.asyncio
    async def test_provider_with_429_time(self):
        """Test provider captures last 429 time."""
        from datetime import datetime, timezone
        last_429 = datetime(2025, 1, 15, 10, 30, 0, tzinfo=timezone.utc)
        health = await ProviderProbe.check(
            provider_name="openrouter",
            rpm_limit=50,
            rpm_current=0,
            latency_avg_ms=400,
            last_429_time=last_429
        )

        assert health.status == "healthy"
        assert health.last_429 == last_429


class TestHealthCheckerStatus:
    """Tests for overall health status calculation."""

    @pytest.mark.asyncio
    async def test_all_healthy(self, health_checker):
        """Test when all components are healthy."""
        components = {
            "redis": ComponentHealth(status="healthy", latency_ms=5),
            "postgres": ComponentHealth(status="healthy", latency_ms=10),
            "groq": ProviderHealth(
                status="healthy",
                rpm_limit=100,
                rpm_current=20,
                rpm_available=80,
                latency_avg_ms=500
            )
        }

        overall = health_checker._calculate_overall_status(components)
        assert overall == "healthy"

    @pytest.mark.asyncio
    async def test_any_degraded_returns_degraded(self, health_checker):
        """Test when any component is degraded."""
        components = {
            "redis": ComponentHealth(status="healthy", latency_ms=5),
            "postgres": ComponentHealth(status="degraded", latency_ms=25),
            "groq": ProviderHealth(
                status="healthy",
                rpm_limit=100,
                rpm_current=20,
                rpm_available=80,
                latency_avg_ms=500
            )
        }

        overall = health_checker._calculate_overall_status(components)
        assert overall == "degraded"

    @pytest.mark.asyncio
    async def test_any_unavailable_returns_unhealthy(self, health_checker):
        """Test when any component is unavailable."""
        components = {
            "redis": ComponentHealth(
                status="unavailable",
                latency_ms=None,
                details={"error": "Connection refused"}
            ),
            "postgres": ComponentHealth(status="healthy", latency_ms=10),
            "groq": ProviderHealth(
                status="healthy",
                rpm_limit=100,
                rpm_current=20,
                rpm_available=80,
                latency_avg_ms=500
            )
        }

        overall = health_checker._calculate_overall_status(components)
        assert overall == "unhealthy"

    @pytest.mark.asyncio
    async def test_empty_components_returns_healthy(self, health_checker):
        """Test when no components checked (returns healthy)."""
        overall = health_checker._calculate_overall_status({})
        assert overall == "healthy"


class TestHealthCheckerIntegration:
    """Integration tests for full health check flow."""

    @pytest.mark.asyncio
    async def test_check_all_with_all_components(self, health_checker, mock_redis_client, mock_db_pool):
        """Test checking all components together."""
        providers_health = {
            "groq": {
                "rpm_limit": 100,
                "rpm_current": 20,
                "latency_avg_ms": 500,
                "last_429_time": None
            }
        }

        response = await health_checker.check_all(
            redis_client=mock_redis_client,
            db_pool=mock_db_pool,
            providers_health=providers_health
        )

        assert isinstance(response, HealthCheckResponse)
        assert response.status in ["healthy", "degraded", "unhealthy"]
        assert response.version == "1.0.0"
        assert response.uptime_seconds >= 0
        assert "redis" in response.components
        assert "postgres" in response.components
        assert "groq" in response.components

    @pytest.mark.asyncio
    async def test_check_all_with_no_components(self, health_checker):
        """Test checking with no components provided."""
        response = await health_checker.check_all()

        assert response.status == "healthy"  # No unhealthy components = healthy
        assert len(response.components) == 0
        assert response.version == "1.0.0"
