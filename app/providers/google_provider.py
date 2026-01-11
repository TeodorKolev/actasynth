"""Google Gemini provider implementation"""

import json
import time
from typing import Any, Optional
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, SystemMessage
from app.providers.base import BaseProvider, ProviderResponse


# Pricing per 1M tokens (as of Jan 2025)
GOOGLE_PRICING = {
    "gemini-pro": {"input": 0.5, "output": 1.5},
    "gemini-1.5-pro": {"input": 3.5, "output": 10.5},
    "gemini-1.5-flash": {"input": 0.075, "output": 0.3},
    "gemini-2.0-flash": {"input": 0.0, "output": 0.0},  # Free tier
    "gemini-2.0-flash-exp": {"input": 0.0, "output": 0.0},  # Free experimental
    "gemini-2.5-flash": {"input": 0.075, "output": 0.3},  # Same as 1.5 Flash
    "gemini-2.5-flash-lite": {"input": 0.0375, "output": 0.15},  # Half of Flash pricing
    "gemini-2.5-pro": {"input": 1.25, "output": 5.0},
}


class GoogleProvider(BaseProvider):
    """Google Gemini provider implementation"""

    def __init__(self, api_key: str, model: str, temperature: float = 0.7, max_tokens: int = 2000):
        super().__init__(api_key, model, temperature, max_tokens)
        self.client = ChatGoogleGenerativeAI(
            model=model,
            temperature=temperature,
            max_output_tokens=max_tokens,
            google_api_key=api_key,
            convert_system_message_to_human=True,  # Gemini doesn't support system messages natively
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_schema: Optional[dict[str, Any]] = None,
    ) -> ProviderResponse:
        """Generate response using Google Gemini API via LangChain (with LangSmith tracing)"""
        start_time = time.perf_counter()

        # Build messages
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))

        # Add JSON schema instruction if provided
        user_prompt = prompt
        if json_schema:
            schema_str = json.dumps(json_schema, indent=2)
            user_prompt += f"\n\nRespond with valid JSON matching this schema:\n{schema_str}"

        messages.append(HumanMessage(content=user_prompt))

        # Invoke the model
        response = await self.client.ainvoke(messages)

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        # Safely extract content
        content = ""
        if hasattr(response, "content"):
            content = response.content or ""
        elif isinstance(response, str):
            content = response

        # Extract token usage from response metadata with safe access
        tokens_input = 0
        tokens_output = 0
        finish_reason = "stop"
        raw_response = None

        if hasattr(response, "response_metadata"):
            metadata = response.response_metadata
            raw_response = metadata

            # Try to get usage metadata
            usage = metadata.get("usage_metadata", {})
            tokens_input = usage.get("prompt_token_count", 0)
            tokens_output = usage.get("candidates_token_count", 0)
            finish_reason = metadata.get("finish_reason", "stop")

        # Fallback to estimation if not available
        if tokens_input == 0:
            tokens_input = int(len(user_prompt.split()) * 1.3)
        if tokens_output == 0:
            tokens_output = int(len(content.split()) * 1.3)

        return ProviderResponse(
            content=content,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            latency_ms=latency_ms,
            cost_usd=self.calculate_cost(tokens_input, tokens_output),
            model=self.model,
            finish_reason=finish_reason,
            raw_response=raw_response,
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
