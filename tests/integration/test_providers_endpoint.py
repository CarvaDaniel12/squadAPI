"""Integration tests for provider status endpoint."""

import pytest
from httpx import AsyncClient
from fastapi.testclient import TestClient
from datetime import datetime, timezone
from unittest.mock import patch, MagicMock, AsyncMock
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../'))

from src.main import app
from src.metrics.provider_status import ProviderStatusTracker, ProviderStatusEnum


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_tracker():
    """Create a mock provider status tracker."""
    tracker = ProviderStatusTracker()

    # Record some sample data for groq
    tracker.record_request("groq", latency_ms=500, success=True)
    tracker.record_request("groq", latency_ms=550, success=True)
    tracker.record_request("groq", latency_ms=450, success=True)
    tracker.set_rpm_current("groq", 10)

    # Record some data for gemini with a failure
    tracker.record_request("gemini", latency_ms=300, success=True)
    tracker.record_request("gemini", latency_ms=350, success=False, error="Rate limit")
    tracker.record_rate_limit("gemini")
    tracker.set_rpm_current("gemini", 25)

    return tracker


class TestProvidersEndpoint:
    """Tests for provider endpoints."""

    def test_get_all_providers_endpoint_response_structure(self, client):
        """Test that GET /providers returns correct structure."""
        response = client.get("/providers")

        assert response.status_code == 200
        data = response.json()

        # Should have timestamp and providers list
        assert "timestamp" in data
        assert "providers" in data
        assert isinstance(data["providers"], list)

    def test_get_all_providers_endpoint_provider_structure(self, client):
        """Test that each provider has correct structure."""
        response = client.get("/providers")

        assert response.status_code == 200
        data = response.json()

        if data["providers"]:  # If there are providers configured
            provider = data["providers"][0]

            # Check required fields
            assert "name" in provider
            assert "model" in provider
            assert "status" in provider
            assert "rpm_limit" in provider
            assert "rpm_current" in provider
            assert "rpm_available" in provider
            assert "latency_avg_ms" in provider
            assert "latency_p95_ms" in provider
            assert "total_requests" in provider
            assert "total_failures" in provider
            assert "failure_rate" in provider
            assert "enabled" in provider

    def test_get_all_providers_endpoint_timestamp_format(self, client):
        """Test that timestamp is ISO 8601 format."""
        response = client.get("/providers")

        assert response.status_code == 200
        data = response.json()

        timestamp = data["timestamp"]
        # Should be parseable as ISO 8601
        assert isinstance(timestamp, str)
        try:
            datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
        except ValueError:
            pytest.fail(f"Invalid timestamp format: {timestamp}")

    def test_get_all_providers_status_values(self, client):
        """Test that provider status values are valid."""
        response = client.get("/providers")

        assert response.status_code == 200
        data = response.json()

        valid_statuses = {"healthy", "degraded", "unavailable"}

        for provider in data["providers"]:
            assert provider["status"] in valid_statuses

    def test_get_single_provider_endpoint_valid_provider(self, client):
        """Test GET /providers/{provider} for valid provider - if any are configured."""
        # First get all providers to see what's available
        response_all = client.get("/providers")

        assert response_all.status_code == 200
        data_all = response_all.json()

        # Only test if there's at least one provider configured
        if data_all["providers"]:
            provider_name = data_all["providers"][0]["name"]
            response = client.get(f"/providers/{provider_name}")

            assert response.status_code == 200
            provider = response.json()
            assert provider["name"] == provider_name
            assert "model" in provider
            assert "status" in provider

    def test_get_single_provider_endpoint_invalid_provider(self, client):
        """Test GET /providers/{provider} for invalid provider."""
        response = client.get("/providers/nonexistent-provider")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data or "error" in data

    def test_get_single_provider_endpoint_structure(self, client):
        """Test that GET /providers/{provider} returns correct structure - if any are configured."""
        # First get all providers
        response_all = client.get("/providers")

        if response_all.status_code == 200:
            data_all = response_all.json()

            if data_all["providers"]:
                provider_name = data_all["providers"][0]["name"]
                response = client.get(f"/providers/{provider_name}")

                if response.status_code == 200:
                    provider = response.json()

                    # Check for all required fields
                    assert "name" in provider
                    assert "model" in provider
                    assert "status" in provider
                    assert "rpm_limit" in provider
                    assert "rpm_current" in provider
                    assert "rpm_available" in provider
                    assert "latency_avg_ms" in provider
                    assert "latency_p95_ms" in provider
                    assert "total_requests" in provider
                    assert "total_failures" in provider
                    assert "failure_rate" in provider

    def test_get_all_providers_metrics_consistency(self, client):
        """Test that metrics are consistent."""
        response = client.get("/providers")

        assert response.status_code == 200
        data = response.json()

        for provider in data["providers"]:
            # RPM available should be rpm_limit - rpm_current
            expected_available = max(0, provider["rpm_limit"] - provider["rpm_current"])
            assert provider["rpm_available"] == expected_available

            # Failure rate should be consistent
            if provider["total_requests"] > 0:
                expected_rate = provider["total_failures"] / provider["total_requests"]
                assert abs(provider["failure_rate"] - expected_rate) < 0.01
            else:
                assert provider["failure_rate"] == 0.0

    def test_get_all_providers_error_handling(self, client):
        """Test error handling in provider endpoints."""
        # Test with invalid provider name
        response = client.get("/providers/invalid-provider-name")

        assert response.status_code == 404

    def test_providers_endpoint_content_type(self, client):
        """Test that responses have correct content type."""
        response = client.get("/providers")

        assert response.headers.get("content-type") == "application/json"

    def test_single_provider_content_type(self, client):
        """Test that single provider response has correct content type."""
        response = client.get("/providers/groq")

        if response.status_code == 200:
            assert response.headers.get("content-type") == "application/json"
