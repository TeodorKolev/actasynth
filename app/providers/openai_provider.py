"""OpenAI provider implementation"""

import time
from typing import Any, Optional
from openai import AsyncOpenAI
from app.providers.base import BaseProvider, ProviderResponse


# Pricing per 1M tokens (as of Jan 2025)
OPENAI_PRICING = {
    "gpt-4-turbo-preview": {"input": 10.0, "output": 30.0},
    "gpt-4-1106-preview": {"input": 10.0, "output": 30.0},
    "gpt-4": {"input": 30.0, "output": 60.0},
    "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
    "gpt-3.5-turbo-1106": {"input": 1.0, "output": 2.0},
}


class OpenAIProvider(BaseProvider):
    """OpenAI provider with function calling and JSON mode support"""

    def __init__(self, api_key: str, model: str, temperature: float = 0.7, max_tokens: int = 2000):
        super().__init__(api_key, model, temperature, max_tokens)
        self.client = AsyncOpenAI(api_key=api_key)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_schema: Optional[dict[str, Any]] = None,
    ) -> ProviderResponse:
        """Generate response using OpenAI API"""
        start_time = time.perf_counter()

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
        }

        # Use function calling for structured output if schema provided
        if json_schema:
            # OpenAI function calling approach
            kwargs["functions"] = [
                {
                    "name": "extract_data",
                    "description": "Extract structured data from the input",
                    "parameters": json_schema,
                }
            ]
            kwargs["function_call"] = {"name": "extract_data"}

        response = await self.client.chat.completions.create(**kwargs)

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        # Extract content from response
        choice = response.choices[0]
        if json_schema and choice.message.function_call:
            content = choice.message.function_call.arguments
        else:
            content = choice.message.content or ""

        tokens_input = response.usage.prompt_tokens if response.usage else 0
        tokens_output = response.usage.completion_tokens if response.usage else 0

        return ProviderResponse(
            content=content,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            latency_ms=latency_ms,
            cost_usd=self.calculate_cost(tokens_input, tokens_output),
            model=self.model,
            finish_reason=choice.finish_reason or "stop",
            raw_response=response.model_dump() if hasattr(response, "model_dump") else None,
        )

    def calculate_cost(self, tokens_input: int, tokens_output: int) -> float:
        """Calculate cost based on OpenAI pricing"""
        pricing = OPENAI_PRICING.get(self.model, {"input": 10.0, "output": 30.0})
        input_cost = (tokens_input / 1_000_000) * pricing["input"]
        output_cost = (tokens_output / 1_000_000) * pricing["output"]
        return round(input_cost + output_cost, 6)

    @property
    def supports_json_mode(self) -> bool:
        return "gpt-4" in self.model or "gpt-3.5" in self.model

    @property
    def supports_function_calling(self) -> bool:
        return True
