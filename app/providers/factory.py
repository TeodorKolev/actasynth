"""Provider factory for creating provider instances"""

from app.schemas.workflow import Provider, ModelConfig
from app.providers.base import BaseProvider
from app.providers.openai_provider import OpenAIProvider
from app.providers.anthropic_provider import AnthropicProvider
from app.providers.google_provider import GoogleProvider


def get_provider(config: ModelConfig, api_keys: dict[str, str]) -> BaseProvider:
    """
    Factory function to create a provider instance based on config.

    Args:
        config: Model configuration
        api_keys: Dictionary of API keys for each provider

    Returns:
        Provider instance

    Raises:
        ValueError: If provider is not supported or API key is missing
    """
    provider_map = {
        Provider.OPENAI: OpenAIProvider,
        Provider.ANTHROPIC: AnthropicProvider,
        Provider.GOOGLE: GoogleProvider,
    }

    if config.provider not in provider_map:
        raise ValueError(f"Unsupported provider: {config.provider}")

    api_key = api_keys.get(config.provider.value)
    if not api_key:
        raise ValueError(f"API key not found for provider: {config.provider}")

    provider_class = provider_map[config.provider]
    return provider_class(
        api_key=api_key,
        model=config.model_name,
        temperature=config.temperature,
        max_tokens=config.max_tokens,
    )
