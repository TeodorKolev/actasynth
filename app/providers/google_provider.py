"""Google Gemini provider implementation"""

import time
from typing import Any, Optional
import google.generativeai as genai
from app.providers.base import BaseProvider, ProviderResponse


# Pricing per 1M tokens (as of Jan 2025)
GOOGLE_PRICING = {
    "gemini-pro": {"input": 0.5, "output": 1.5},
    "gemini-pro-vision": {"input": 0.5, "output": 1.5},
    "gemini-1.5-pro": {"input": 3.5, "output": 10.5},
}


class GoogleProvider(BaseProvider):
    """Google Gemini provider implementation"""

    def __init__(self, api_key: str, model: str, temperature: float = 0.7, max_tokens: int = 2000):
        super().__init__(api_key, model, temperature, max_tokens)
        genai.configure(api_key=api_key)
        self.model_instance = genai.GenerativeModel(model)

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_schema: Optional[dict[str, Any]] = None,
    ) -> ProviderResponse:
        """Generate response using Google Gemini API"""
        start_time = time.perf_counter()

        # Gemini combines system and user prompts
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"

        # Add JSON schema instruction if provided
        if json_schema:
            import json

            schema_str = json.dumps(json_schema, indent=2)
            full_prompt += f"\n\nRespond with valid JSON matching this schema:\n{schema_str}"

        generation_config = genai.GenerationConfig(
            temperature=self.temperature,
            max_output_tokens=self.max_tokens,
        )

        # Gemini async API
        response = await self.model_instance.generate_content_async(
            full_prompt, generation_config=generation_config
        )

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        content = response.text

        # Gemini doesn't provide exact token counts, estimate
        # This is a known limitation - in production you'd use tiktoken or similar
        tokens_input = len(full_prompt.split()) * 1.3  # Rough estimate
        tokens_output = len(content.split()) * 1.3

        return ProviderResponse(
            content=content,
            tokens_input=int(tokens_input),
            tokens_output=int(tokens_output),
            latency_ms=latency_ms,
            cost_usd=self.calculate_cost(int(tokens_input), int(tokens_output)),
            model=self.model,
            finish_reason="stop",
            raw_response={
                "candidates": len(response.candidates) if hasattr(response, "candidates") else 0
            },
        )

    def calculate_cost(self, tokens_input: int, tokens_output: int) -> float:
        """Calculate cost based on Google pricing"""
        pricing = GOOGLE_PRICING.get(self.model, {"input": 0.5, "output": 1.5})
        input_cost = (tokens_input / 1_000_000) * pricing["input"]
        output_cost = (tokens_output / 1_000_000) * pricing["output"]
        return round(input_cost + output_cost, 6)

    @property
    def supports_json_mode(self) -> bool:
        return False  # Gemini requires schema in prompt

    @property
    def supports_function_calling(self) -> bool:
        return True  # Gemini 1.5 supports function calling
