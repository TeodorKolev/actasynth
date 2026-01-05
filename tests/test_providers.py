"""Test provider abstractions"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.providers.base import ProviderResponse
from app.providers.openai_provider import OpenAIProvider
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.factory import get_provider
from app.schemas.workflow import ModelConfig, Provider


class TestOpenAIProvider:
    """Test OpenAI provider implementation"""

    def test_calculate_cost(self):
        """Test cost calculation for OpenAI"""
        provider = OpenAIProvider(
            api_key="test-key",
            model="gpt-4-turbo-preview",
            temperature=0.7,
        )

        # Test with known token counts
        cost = provider.calculate_cost(tokens_input=1000, tokens_output=500)

        # gpt-4-turbo: $10/1M input, $30/1M output
        # (1000/1M * $10) + (500/1M * $30) = $0.01 + $0.015 = $0.025
        assert cost == pytest.approx(0.025, rel=1e-6)

    def test_supports_function_calling(self):
        """Test that OpenAI supports function calling"""
        provider = OpenAIProvider(api_key="test-key", model="gpt-4")
        assert provider.supports_function_calling is True

    def test_supports_json_mode(self):
        """Test that OpenAI supports JSON mode"""
        provider = OpenAIProvider(api_key="test-key", model="gpt-4")
        assert provider.supports_json_mode is True

    @pytest.mark.asyncio
    async def test_generate_basic(self):
        """Test basic generate call (mocked)"""
        provider = OpenAIProvider(api_key="test-key", model="gpt-4")

        # Mock the OpenAI client
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(
                message=MagicMock(content="Test response", function_call=None),
                finish_reason="stop",
            )
        ]
        mock_response.usage = MagicMock(prompt_tokens=100, completion_tokens=50)

        with patch.object(
            provider.client.chat.completions,
            "create",
            new=AsyncMock(return_value=mock_response),
        ):
            response = await provider.generate(
                prompt="Test prompt", system_prompt="Test system"
            )

            assert isinstance(response, ProviderResponse)
            assert response.content == "Test response"
            assert response.tokens_input == 100
            assert response.tokens_output == 50
            assert response.latency_ms > 0
            assert response.cost_usd > 0


class TestAnthropicProvider:
    """Test Anthropic provider implementation"""

    def test_calculate_cost(self):
        """Test cost calculation for Anthropic"""
        provider = AnthropicProvider(
            api_key="test-key",
            model="claude-3-sonnet-20240229",
            temperature=0.7,
        )

        # Test with known token counts
        cost = provider.calculate_cost(tokens_input=1000, tokens_output=500)

        # claude-3-sonnet: $3/1M input, $15/1M output
        # (1000/1M * $3) + (500/1M * $15) = $0.003 + $0.0075 = $0.0105
        assert cost == pytest.approx(0.0105, rel=1e-6)

    def test_supports_function_calling(self):
        """Test that Claude 3 supports tool calling"""
        provider = AnthropicProvider(api_key="test-key", model="claude-3-sonnet-20240229")
        assert provider.supports_function_calling is True

    def test_does_not_support_json_mode(self):
        """Test that Anthropic doesn't support native JSON mode"""
        provider = AnthropicProvider(api_key="test-key", model="claude-3-sonnet-20240229")
        assert provider.supports_json_mode is False


class TestProviderFactory:
    """Test provider factory"""

    def test_get_openai_provider(self, mock_api_keys):
        """Test creating OpenAI provider"""
        config = ModelConfig(
            provider=Provider.OPENAI,
            model_name="gpt-4",
            temperature=0.5,
        )

        provider = get_provider(config, mock_api_keys)

        assert isinstance(provider, OpenAIProvider)
        assert provider.model == "gpt-4"
        assert provider.temperature == 0.5

    def test_get_anthropic_provider(self, mock_api_keys):
        """Test creating Anthropic provider"""
        config = ModelConfig(
            provider=Provider.ANTHROPIC,
            model_name="claude-3-sonnet-20240229",
            temperature=0.7,
        )

        provider = get_provider(config, mock_api_keys)

        assert isinstance(provider, AnthropicProvider)
        assert provider.model == "claude-3-sonnet-20240229"

    def test_missing_api_key_raises_error(self):
        """Test that missing API key raises ValueError"""
        config = ModelConfig(
            provider=Provider.OPENAI,
            model_name="gpt-4",
        )

        with pytest.raises(ValueError, match="API key not found"):
            get_provider(config, {})
