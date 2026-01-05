"""Pytest configuration and fixtures"""

import pytest
from typing import AsyncGenerator
from httpx import AsyncClient
from app.main import app


@pytest.fixture
def mock_api_keys() -> dict[str, str]:
    """Mock API keys for testing"""
    return {
        "openai": "sk-test-openai-key",
        "anthropic": "sk-test-anthropic-key",
        "google": "test-google-key",
    }


@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client for testing FastAPI endpoints"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac
