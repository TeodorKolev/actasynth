"""Anthropic Claude provider implementation"""

import json
import time
from typing import Any, Optional
from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
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
        self.client = ChatAnthropic(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            anthropic_api_key=api_key,
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_schema: Optional[dict[str, Any]] = None,
    ) -> ProviderResponse:
        """Generate response using Anthropic API via LangChain (with LangSmith tracing)"""
        start_time = time.perf_counter()

        # Build messages - Anthropic in LangChain handles system prompts differently
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        # Configure structured output if schema provided
        # For LangChain 0.1.0, we'll add schema to prompt instead of using bind_tools
        if json_schema:
            # Add schema instruction to the user message
            schema_instruction = f"\n\nRespond with valid JSON matching this schema:\n{json.dumps(json_schema, indent=2)}"
            if messages:
                # Append to the last human message
                last_msg = messages[-1]
                if isinstance(last_msg, HumanMessage):
                    messages[-1] = HumanMessage(content=last_msg.content + schema_instruction)
            response = await self.client.ainvoke(messages)
        else:
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
        finish_reason = "end_turn"
        raw_response = None

        if hasattr(response, "response_metadata"):
            metadata = response.response_metadata
            raw_response = metadata

            usage = metadata.get("usage", {})
            tokens_input = usage.get("input_tokens", 0)
            tokens_output = usage.get("output_tokens", 0)
            finish_reason = metadata.get("stop_reason", "end_turn")

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
