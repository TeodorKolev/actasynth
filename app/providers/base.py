"""Base provider abstraction for LLM providers"""

from abc import ABC, abstractmethod
from typing import Any, Optional
from pydantic import BaseModel


class ProviderResponse(BaseModel):
    """Standardized response from any provider"""

    content: str
    tokens_input: int
    tokens_output: int
    latency_ms: int
    cost_usd: float
    model: str
    finish_reason: str = "stop"
    raw_response: Optional[dict[str, Any]] = None


class BaseProvider(ABC):
    """Abstract base class for LLM providers"""

    def __init__(self, api_key: str, model: str, temperature: float = 0.7, max_tokens: int = 2000, timeout_seconds: int = 30):
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.timeout_seconds = timeout_seconds

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_schema: Optional[dict[str, Any]] = None,
    ) -> ProviderResponse:
        """
        Generate a response from the LLM.

        Args:
            prompt: User message/prompt
            system_prompt: Optional system instructions
            json_schema: Optional JSON schema for structured output

        Returns:
            ProviderResponse with content and metrics
        """
        pass

    @abstractmethod
    def calculate_cost(self, tokens_input: int, tokens_output: int) -> float:
        """
        Calculate cost in USD for token usage.

        Args:
            tokens_input: Number of input tokens
            tokens_output: Number of output tokens

        Returns:
            Cost in USD
        """
        pass

    @property
    @abstractmethod
    def supports_json_mode(self) -> bool:
        """Whether this provider supports native JSON mode"""
        pass

    @property
    @abstractmethod
    def supports_function_calling(self) -> bool:
        """Whether this provider supports function/tool calling"""
        pass
