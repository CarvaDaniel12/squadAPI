"""Integration tests for health API endpoint."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from src.health.checker import HealthChecker
from src.models.health import ComponentHealth, ProviderHealth


@pytest.fixture
async def setup_health_app():
    """Setup a minimal FastAPI app with health endpoint."""
    from fastapi import FastAPI
    from src.api.health import router, set_health_checker

    app = FastAPI()
    app.include_router(router)

    # Create and set health checker
    checker = HealthChecker(version="1.0.0")
    set_health_checker(checker)

    return app, checker


@pytest.fixture
def health_client(setup_health_app):
    """Create test client for health app."""
    app, _ = setup_health_app
    return TestClient(app)


@pytest.fixture
def mock_healthy_checker():
    """Create a mock health checker returning healthy status."""
    checker = AsyncMock(spec=HealthChecker)
    checker.check_all = AsyncMock(return_value={
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc),
        "uptime_seconds": 3600,
        "version": "1.0.0",
        "components": {
            "redis": {"status": "healthy", "latency_ms": 5},
            "postgres": {"status": "healthy", "latency_ms": 10}
        }
    })
    return checker


@pytest.fixture
def mock_unhealthy_checker():
    """Create a mock health checker returning unhealthy status."""
    checker = AsyncMock(spec=HealthChecker)
    checker.check_all = AsyncMock(return_value={
        "status": "unhealthy",
        "timestamp": datetime.now(timezone.utc),
        "uptime_seconds": 300,
        "version": "1.0.0",
        "components": {
            "redis": {
                "status": "unavailable",
                "latency_ms": None,
                "details": {"error": "Connection refused"}
            },
            "postgres": {"status": "healthy", "latency_ms": 10}
        }
    })
    return checker


@pytest.mark.asyncio
async def test_health_endpoint_returns_200_when_healthy(setup_health_app):
    """Test /health returns 200 when system is healthy."""
    from fastapi import FastAPI
    from src.api.health import router, set_health_checker
    from src.models.health import HealthCheckResponse, ComponentHealth

    app = FastAPI()
    app.include_router(router)

    # Mock healthy response with proper HealthCheckResponse object
    mock_checker = AsyncMock(spec=HealthChecker)
    response_obj = HealthCheckResponse(
        status="healthy",
        timestamp=datetime.now(timezone.utc),
        uptime_seconds=3600,
        version="1.0.0",
        components={
            "redis": ComponentHealth(status="healthy", latency_ms=5),
            "postgres": ComponentHealth(status="healthy", latency_ms=10)
        }
    )
    mock_checker.check_all = AsyncMock(return_value=response_obj)

    from src.api import health as health_module
    health_module._health_checker = mock_checker

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.asyncio
async def test_health_endpoint_returns_degraded_with_200():
    """Test /health returns 200 with degraded status."""
    from fastapi import FastAPI
    from src.api.health import router, set_health_checker
    from src.models.health import HealthCheckResponse, ComponentHealth

    app = FastAPI()
    app.include_router(router)

    mock_checker = AsyncMock(spec=HealthChecker)
    response_obj = HealthCheckResponse(
        status="degraded",
        timestamp=datetime.now(timezone.utc),
        uptime_seconds=3600,
        version="1.0.0",
        components={
            "redis": ComponentHealth(status="healthy", latency_ms=5),
            "postgres": ComponentHealth(status="degraded", latency_ms=25)
        }
    )
    mock_checker.check_all = AsyncMock(return_value=response_obj)

    from src.api import health as health_module
    health_module._health_checker = mock_checker

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "degraded"


@pytest.mark.asyncio
async def test_health_endpoint_no_checker():
    """Test /health when no checker is configured."""
    from fastapi import FastAPI
    from src.api.health import router
    from datetime import datetime, timezone

    app = FastAPI()
    app.include_router(router)

    from src.api import health as health_module
    health_module._health_checker = None

    client = TestClient(app)
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "unknown"


@pytest.mark.asyncio
async def test_orchestrator_integration_health_check():
    """Test that health checker integrates with orchestrator scenario."""
    from src.health.checker import HealthChecker

    checker = HealthChecker(version="1.0.0")

    # Simulate checking with mock clients
    mock_redis = AsyncMock()
    mock_redis.ping = AsyncMock()
    mock_redis.info = AsyncMock(return_value={
        "used_memory": 10485760,
        "connected_clients": 5
    })

    mock_pool = MagicMock()
    mock_pool.acquire = AsyncMock()
    mock_pool.get_size = MagicMock(return_value=10)
    mock_pool.get_idle_size = MagicMock(return_value=8)

    conn = AsyncMock()
    conn.fetchval = AsyncMock(return_value=1)
    mock_pool.acquire.return_value.__aenter__ = AsyncMock(return_value=conn)
    mock_pool.acquire.return_value.__aexit__ = AsyncMock(return_value=None)

    providers_health = {
        "groq": {
            "rpm_limit": 100,
            "rpm_current": 20,
            "latency_avg_ms": 500,
            "last_429_time": None
        },
        "gemini": {
            "rpm_limit": 200,
            "rpm_current": 150,
            "latency_avg_ms": 300,
            "last_429_time": "2025-01-15T10:30:00Z"
        }
    }

    response = await checker.check_all(
        redis_client=mock_redis,
        db_pool=mock_pool,
        providers_health=providers_health
    )

    # Verify response structure
    assert response.status in ["healthy", "degraded", "unhealthy"]
    assert response.version == "1.0.0"
    assert response.uptime_seconds >= 0
    assert "redis" in response.components
    assert "postgres" in response.components
    assert "groq" in response.components
    assert "gemini" in response.components

    # Verify providers have correct structure
    groq_health = response.components["groq"]
    assert groq_health.rpm_limit == 100
    assert groq_health.rpm_available == 80
