"""Test API endpoints"""

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_root_endpoint(client: AsyncClient):
    """Test root endpoint returns service info"""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "AgentOps Studio"
    assert "version" in data
    assert "docs" in data


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient):
    """Test health check endpoint"""
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "agentops-studio"


@pytest.mark.asyncio
async def test_metrics_endpoint(client: AsyncClient):
    """Test Prometheus metrics endpoint"""
    response = await client.get("/api/v1/metrics")
    assert response.status_code == 200
    # Prometheus format is plain text
    assert "text/plain" in response.headers["content-type"]


@pytest.mark.asyncio
async def test_workflow_execute_validation(client: AsyncClient):
    """Test workflow execute endpoint validates input"""
    # Missing required field 'content'
    response = await client.post(
        "/api/v1/workflow/execute",
        json={"source": "test"},
    )
    assert response.status_code == 422  # Validation error

    # Content too short
    response = await client.post(
        "/api/v1/workflow/execute",
        json={"content": "short", "source": "test"},
    )
    assert response.status_code == 422


# Note: Full integration tests would require real API keys
# These are unit tests for API contract validation
