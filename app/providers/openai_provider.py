"""OpenAI provider implementation"""

import json
import time
from typing import Any, Optional
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.output_parsers import JsonOutputParser
from app.providers.base import BaseProvider, ProviderResponse


# Pricing per 1M tokens (as of Jan 2025)
OPENAI_PRICING = {
    "gpt-4-turbo": {"input": 10.0, "output": 30.0},
    "gpt-4-turbo-preview": {"input": 10.0, "output": 30.0},
    "gpt-4-1106-preview": {"input": 10.0, "output": 30.0},
    "gpt-4o": {"input": 2.5, "output": 10.0},
    "gpt-4o-mini": {"input": 0.15, "output": 0.6},
    "gpt-4": {"input": 30.0, "output": 60.0},
    "gpt-3.5-turbo": {"input": 0.5, "output": 1.5},
    "gpt-3.5-turbo-1106": {"input": 1.0, "output": 2.0},
}


class OpenAIProvider(BaseProvider):
    """OpenAI provider with function calling and JSON mode support"""

    def __init__(self, api_key: str, model: str, temperature: float = 0.7, max_tokens: int = 2000):
        super().__init__(api_key, model, temperature, max_tokens)
        self.client = ChatOpenAI(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            openai_api_key=api_key,
        )

    async def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        json_schema: Optional[dict[str, Any]] = None,
    ) -> ProviderResponse:
        """Generate response using OpenAI API via LangChain (with LangSmith tracing)"""
        start_time = time.perf_counter()

        # Build messages
        messages = []
        if system_prompt:
            messages.append(SystemMessage(content=system_prompt))
        messages.append(HumanMessage(content=prompt))

        # Configure structured output if schema provided
        if json_schema:
            # Use bind_functions for structured output (compatible with LangChain 0.1.0)
            structured_llm = self.client.bind_functions(
                functions=[
                    {
                        "name": "extract_data",
                        "description": "Extract structured data from the input",
                        "parameters": json_schema,
                    }
                ],
                function_call={"name": "extract_data"},
            )
            response = await structured_llm.ainvoke(messages)
        else:
            response = await self.client.ainvoke(messages)

        latency_ms = int((time.perf_counter() - start_time) * 1000)

        # Extract content from response with safe access
        content = ""
        if json_schema:
            # Check for function_call in additional_kwargs (LangChain 0.1.0 format)
            if hasattr(response, "additional_kwargs") and "function_call" in response.additional_kwargs:
                func_call = response.additional_kwargs["function_call"]
                content = func_call.get("arguments", "{}")
            # Check for tool_calls (newer format)
            elif hasattr(response, "tool_calls") and response.tool_calls:
                content = json.dumps(response.tool_calls[0]["args"])
            else:
                # Fallback to regular content
                if hasattr(response, "content"):
                    content = response.content or ""
        else:
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

            token_usage = metadata.get("token_usage", {})
            tokens_input = token_usage.get("prompt_tokens", 0)
            tokens_output = token_usage.get("completion_tokens", 0)
            finish_reason = metadata.get("finish_reason", "stop")

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
