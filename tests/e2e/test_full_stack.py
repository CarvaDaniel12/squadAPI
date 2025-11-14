"""
End-to-End Integration Tests
Story 8.7: Full Stack Integration Test
Epic 8: Deployment & Documentation

Simplified E2E tests focusing on critical API functionality with documentation validation.
These tests verify OpenAPI documentation completeness and API contract compliance.
"""

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def client():
    """Create test client (without orchestrator initialization for doc tests)"""
    return TestClient(app)


class TestOpenAPIDocumentation:
    """Test OpenAPI/Swagger documentation completeness"""

    def test_openapi_json_accessible(self, client):
        """Verify OpenAPI JSON schema is accessible"""
        response = client.get("/openapi.json")
        assert response.status_code == 200

    def test_swagger_ui_accessible(self, client):
        """Verify Swagger UI documentation is accessible"""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_ui_accessible(self, client):
        """Verify ReDoc documentation is accessible"""
        response = client.get("/redoc")
        assert response.status_code == 200

    def test_openapi_schema_structure(self, client):
        """Verify OpenAPI schema has required components"""
        response = client.get("/openapi.json")
        schema = response.json()

        # Verify main structure
        assert "openapi" in schema
        assert "info" in schema
        assert "paths" in schema
        assert "components" in schema

        # Verify info metadata
        info = schema["info"]
        assert info["title"] == "Squad API"
        assert info["version"] == "1.0.0"
        assert "description" in info
        assert len(info["description"]) > 100  # Rich description
        assert "contact" in info
        assert "license" in info

    def test_openapi_endpoints_documented(self, client):
        """Verify all main endpoints are documented"""
        response = client.get("/openapi.json")
        schema = response.json()
        paths = schema["paths"]

        # Verify critical endpoints exist
        assert "/health" in paths
        assert "/v1/agents/{agent_name}" in paths
        assert "/v1/agents" in paths
        # Note: /metrics is mounted separately via Prometheus, not in OpenAPI    def test_openapi_request_response_schemas(self, client):
        """Verify request/response models are defined"""
        response = client.get("/openapi.json")
        schema = response.json()
        components = schema.get("components", {})
        schemas = components.get("schemas", {})

        # Verify Pydantic models are in schemas
        assert "AgentExecutionRequest" in schemas
        assert "AgentExecutionResponse" in schemas
        assert "ExecutionMetadata" in schemas

        # Verify AgentExecutionRequest has documented fields
        request_schema = schemas["AgentExecutionRequest"]
        assert "properties" in request_schema
        props = request_schema["properties"]
        assert "prompt" in props
        assert "conversation_id" in props
        assert "metadata" in props
        assert "max_tokens" in props
        assert "temperature" in props

        # Verify field descriptions exist
        assert "description" in props["prompt"]
        assert len(props["prompt"]["description"]) > 20

    def test_openapi_tags_defined(self, client):
        """Verify OpenAPI tags are defined"""
        response = client.get("/openapi.json")
        schema = response.json()

        assert "tags" in schema
        tags = {tag["name"] for tag in schema["tags"]}
        assert "agents" in tags
        assert "health" in tags
        assert "metrics" in tags


class TestHealthEndpoint:
    """Test health check endpoint"""

    def test_health_check_returns_200(self, client):
        """Verify health endpoint is accessible"""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_check_structure(self, client):
        """Verify health response has correct structure"""
        response = client.get("/health")
        data = response.json()

        assert "status" in data
        assert "version" in data
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"


class TestMetricsCollection:
    """Test Prometheus metrics endpoint"""

    def test_metrics_endpoint_accessible(self, client):
        """Verify /metrics endpoint is accessible"""
        response = client.get("/metrics")
        assert response.status_code == 200

    def test_metrics_content_type(self, client):
        """Verify metrics use Prometheus format"""
        response = client.get("/metrics")
        assert "text/plain" in response.headers.get("content-type", "")

    def test_metrics_has_content(self, client):
        """Verify metrics endpoint returns data"""
        response = client.get("/metrics")
        metrics_text = response.text
        assert len(metrics_text) > 0


# Test Summary
"""
E2E Test Coverage:

 OpenAPI Documentation (6 tests)
   - OpenAPI JSON accessible
   - Swagger UI accessible
   - ReDoc UI accessible
   - Schema structure validation
   - Endpoints documented
   - Request/Response schemas defined
   - Tags defined

 Health endpoint (2 tests)
   - 200 status code
   - Correct response structure

 Metrics collection (3 tests)
   - Metrics endpoint accessible
   - Prometheus format
   - Returns data

Total: 11 tests covering documentation and infrastructure endpoints

Note: Request validation tests moved to unit tests (tests/unit/test_request_validation.py)
Note: Full integration tests with orchestrator will be added in Epic 9
"""

