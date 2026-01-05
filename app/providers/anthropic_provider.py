"""Anthropic Claude provider implementation"""

import time
from typing import Any, Optional
from anthropic import AsyncAnthropic
from app.providers.base import BaseProvider, ProviderResponse


# Pricing per 1M tokens (as of Jan 2025)
ANTHROPIC_PRICING = {
    "claude-3-opus-20240229": {"input": 15.0, "output": 75.0},
    "claude-3-sonnet-20240229": {"input": 3.0, "output": 15.0},
    "claude-3-haiku-20240307": {"input": 0.25, "output": 1.25},
    "claude-2.1": {"input": 8.0, "output": 24.0},
}


class AnthropicProvider(BaseProvider):
    """Anthropic Claude provider with tool calling support"""

    def __init__(self, api_key: str, model: str, temperature: float = 0.7, max_tokens: int = 2000):
        super().__init__(api_key, model, temperature, max_tokens)
        self.client = AsyncAnthropic(api_key=api_key)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_schema: Optional[dict[str, Any]] = None,
    ) -> ProviderResponse:
        """Generate response using Anthropic API"""
        start_time = time.perf_counter()

        kwargs: dict[str, Any] = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "messages": [{"role": "user", "content": prompt}],
        }

        if system_prompt:
            kwargs["system"] = system_prompt

        # Anthropic uses tools for structured output
        if json_schema:
            kwargs["tools"] = [
                {
                    "name": "extract_structured_data",
                    "description": "Extract data according to the specified schema",
                    "input_schema": json_schema,
                }
            ]
            kwargs["tool_choice"] = {"type": "tool", "name": "extract_structured_data"}

        response = await self.client.messages.create(**kwargs)

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        # Extract content from response
        # Anthropic returns tool use in content blocks
        content = ""
        for block in response.content:
            if block.type == "text":
                content += block.text
            elif block.type == "tool_use" and json_schema:
                # Tool use returns structured data
                import json

                content = json.dumps(block.input)

        tokens_input = response.usage.input_tokens
        tokens_output = response.usage.output_tokens

        return ProviderResponse(
            content=content,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            latency_ms=latency_ms,
            cost_usd=self.calculate_cost(tokens_input, tokens_output),
            model=self.model,
            finish_reason=response.stop_reason or "end_turn",
            raw_response={"id": response.id, "stop_reason": response.stop_reason},
        )

    def calculate_cost(self, tokens_input: int, tokens_output: int) -> float:
        """Calculate cost based on Anthropic pricing"""
        pricing = ANTHROPIC_PRICING.get(
            self.model, {"input": 3.0, "output": 15.0}  # Default to Sonnet pricing
        )
        input_cost = (tokens_input / 1_000_000) * pricing["input"]
        output_cost = (tokens_output / 1_000_000) * pricing["output"]
        return round(input_cost + output_cost, 6)

    @property
    def supports_json_mode(self) -> bool:
        return False  # Anthropic doesn't have native JSON mode

    @property
    def supports_function_calling(self) -> bool:
        return "claude-3" in self.model  # Claude 3 has tool calling
