"""Main workflow executor that orchestrates the 4-step agent pipeline"""

import asyncio
import json
import uuid
from datetime import datetime
from typing import Any

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.agents.json_parser import extract_json_from_response
from app.agents.response_validator import (
    validate_extracted_data,
    validate_self_check,
    validate_value_prop,
)
from app.schemas.value_proposition import (
    RawInput,
    NormalizedInput,
    ExtractedData,
    SelfCheckResult,
    ValueProposition,
    WorkflowResult,
    Language,
    PIIDetection,
    PIIType,
    ClaimVerification,
    Persona,
)
from app.schemas.workflow import (
    WorkflowConfig,
    WorkflowRun,
    AgentStep,
    AgentStepResult,
    StepStatus,
    ProviderMetrics,
)
from app.providers.base import BaseProvider
from app.providers.factory import get_provider
from app.prompts.templates import (
    INGEST_SYSTEM_PROMPT,
    EXTRACT_SYSTEM_PROMPT,
    SELF_CHECK_SYSTEM_PROMPT,
    REWRITE_SYSTEM_PROMPT,
)


class WorkflowExecutor:
    """Orchestrates the 4-step value proposition extraction workflow"""

    def __init__(self, config: WorkflowConfig, api_keys: dict[str, str]):
        self.config = config
        self.api_keys = api_keys
        self.provider = get_provider(config.primary_model, api_keys)

    async def execute(self, raw_input: RawInput) -> WorkflowResult:
        """
        Execute the complete 4-step workflow.

        Steps:
        1. Ingest - Normalize input, detect language and PII
        2. Extract - Extract structured insights
        3. Self-check - Verify accuracy, prevent hallucinations
        4. Rewrite - Generate final value proposition

        Returns:
            WorkflowResult with complete execution data
        """
        run_id = str(uuid.uuid4())
        workflow_run = WorkflowRun(run_id=run_id, config=self.config)

        try:
            # Step 1: Ingest
            normalized = await self._execute_ingest(raw_input, workflow_run)

            # Step 2: Extract
            extracted = await self._execute_extract(normalized, workflow_run)

            # Step 3: Self-check
            self_check = await self._execute_self_check(normalized, extracted, workflow_run)

            # If self-check fails, reject the workflow
            if not self_check.approved:
                workflow_run.mark_complete(
                    success=False, error=f"Self-check failed: {self_check.rejection_reason}"
                )
                return self._build_error_result(
                    run_id, workflow_run, f"Self-check failed: {self_check.rejection_reason}"
                )

            # Step 4: Rewrite
            value_prop = await self._execute_rewrite(extracted, workflow_run)

            # Mark workflow as complete
            workflow_run.mark_complete(success=True)

            return WorkflowResult(
                run_id=run_id,
                value_proposition=value_prop,
                normalized_input=normalized,
                extracted_data=extracted,
                self_check=self_check,
                total_latency_ms=workflow_run.total_latency_ms,
                total_cost_usd=workflow_run.total_cost_usd,
                provider_used=self.config.primary_model.provider.value,
                model_used=self.config.primary_model.model_name,
                success=True,
            )

        except Exception as e:
            workflow_run.mark_complete(success=False, error=str(e))
            return self._build_error_result(run_id, workflow_run, str(e))

    async def _execute_ingest(
        self, raw_input: RawInput, workflow_run: WorkflowRun
    ) -> NormalizedInput:
        """Step 1: Normalize input and detect PII"""
        step_result = AgentStepResult(
            step=AgentStep.INGEST, status=StepStatus.RUNNING, started_at=datetime.utcnow()
        )

        prompt = f"""Analyze this input and normalize it:

Input: {raw_input.content}
Source: {raw_input.source}

Detect language, identify PII, and provide a cleaned version."""

        schema = self._get_ingest_schema()
        response = await self._call_with_retry(prompt, INGEST_SYSTEM_PROMPT, json_schema=schema)

        # Parse response using JSON parser
        normalized = self._parse_ingest_response(raw_input.content, response.content)

        metrics = ProviderMetrics(
            provider=self.config.primary_model.provider,
            model=self.config.primary_model.model_name,
            latency_ms=response.latency_ms,
            tokens_input=response.tokens_input,
            tokens_output=response.tokens_output,
            cost_usd=response.cost_usd,
            success=True,
        )

        step_result.mark_complete(output=normalized.model_dump(), metrics=metrics)
        workflow_run.add_step_result(step_result)

        return normalized

    async def _execute_extract(
        self, normalized: NormalizedInput, workflow_run: WorkflowRun
    ) -> ExtractedData:
        """Step 2: Extract structured insights"""
        step_result = AgentStepResult(
            step=AgentStep.EXTRACT, status=StepStatus.RUNNING, started_at=datetime.utcnow()
        )

        prompt = f"""Extract structured insights from this normalized input:

{normalized.cleaned_content}

Extract problem, solution, pain points, value drivers, stakeholders, timeline, and budget signals."""

        # Generate JSON schema for structured output
        schema = self._get_extraction_schema()
        response = await self._call_with_retry(prompt, EXTRACT_SYSTEM_PROMPT, json_schema=schema)

        # Parse JSON response using robust parser
        extracted_dict = extract_json_from_response(response.content)
        # Validate and sanitize to ensure schema compliance
        extracted_dict = validate_extracted_data(extracted_dict)
        extracted = ExtractedData(**extracted_dict)

        metrics = ProviderMetrics(
            provider=self.config.primary_model.provider,
            model=self.config.primary_model.model_name,
            latency_ms=response.latency_ms,
            tokens_input=response.tokens_input,
            tokens_output=response.tokens_output,
            cost_usd=response.cost_usd,
            success=True,
        )

        step_result.mark_complete(output=extracted.model_dump(), metrics=metrics)
        workflow_run.add_step_result(step_result)

        return extracted

    async def _execute_self_check(
        self, normalized: NormalizedInput, extracted: ExtractedData, workflow_run: WorkflowRun
    ) -> SelfCheckResult:
        """Step 3: Verify accuracy and prevent hallucinations"""
        step_result = AgentStepResult(
            step=AgentStep.SELF_CHECK, status=StepStatus.RUNNING, started_at=datetime.utcnow()
        )

        prompt = f"""Verify this extraction against the original input:

ORIGINAL INPUT:
{normalized.cleaned_content}

EXTRACTED DATA:
{json.dumps(extracted.model_dump(), indent=2)}

Check each claim for accuracy and identify any potential hallucinations."""

        schema = self._get_self_check_schema()
        response = await self._call_with_retry(prompt, SELF_CHECK_SYSTEM_PROMPT, json_schema=schema)

        # Parse response using robust parser
        self_check_dict = extract_json_from_response(response.content)
        # Validate and sanitize to ensure schema compliance
        self_check_dict = validate_self_check(self_check_dict)
        self_check = SelfCheckResult(**self_check_dict)

        metrics = ProviderMetrics(
            provider=self.config.primary_model.provider,
            model=self.config.primary_model.model_name,
            latency_ms=response.latency_ms,
            tokens_input=response.tokens_input,
            tokens_output=response.tokens_output,
            cost_usd=response.cost_usd,
            success=True,
        )

        step_result.mark_complete(output=self_check.model_dump(), metrics=metrics)
        workflow_run.add_step_result(step_result)

        return self_check

    async def _execute_rewrite(
        self, extracted: ExtractedData, workflow_run: WorkflowRun
    ) -> ValueProposition:
        """Step 4: Generate final value proposition"""
        step_result = AgentStepResult(
            step=AgentStep.REWRITE, status=StepStatus.RUNNING, started_at=datetime.utcnow()
        )

        prompt = f"""Create a compelling value proposition from these verified insights:

{json.dumps(extracted.model_dump(), indent=2)}

Target persona: Executive (focus on ROI and business impact)"""

        schema = self._get_value_prop_schema()
        response = await self._call_with_retry(prompt, REWRITE_SYSTEM_PROMPT, json_schema=schema)

        # Parse response using robust parser
        value_prop_dict = extract_json_from_response(response.content)
        # Validate and sanitize to ensure schema compliance
        value_prop_dict = validate_value_prop(value_prop_dict)
        value_prop = ValueProposition(**value_prop_dict)

        metrics = ProviderMetrics(
            provider=self.config.primary_model.provider,
            model=self.config.primary_model.model_name,
            latency_ms=response.latency_ms,
            tokens_input=response.tokens_input,
            tokens_output=response.tokens_output,
            cost_usd=response.cost_usd,
            success=True,
        )

        step_result.mark_complete(output=value_prop.model_dump(), metrics=metrics)
        workflow_run.add_step_result(step_result)

        return value_prop

    @retry(
        stop=stop_after_attempt(2),
        wait=wait_exponential(multiplier=2, min=4, max=30),
        retry=retry_if_exception_type(Exception),
    )
    async def _call_with_retry(
        self, prompt: str, system_prompt: str, json_schema: dict[str, Any] | None = None
    ):
        """Call provider with retry logic"""
        return await self.provider.generate(prompt, system_prompt, json_schema)

    def _parse_ingest_response(self, original: str, response: str) -> NormalizedInput:
        """Parse ingest response from JSON"""
        try:
            # Parse JSON response
            data = extract_json_from_response(response)

            # Map response fields to NormalizedInput
            return NormalizedInput(
                content=original,
                language=Language(data.get("language", "en")),
                detected_pii=[],  # TODO: Parse PII from response
                has_pii=data.get("pii_detected", False),
                cleaned_content=data.get("redacted_text", original),
                word_count=data.get("word_count", len(original.split())),
            )
        except Exception as e:
            # Fallback to basic normalized version if parsing fails
            return NormalizedInput(
                content=original,
                language=Language.ENGLISH,
                detected_pii=[],
                has_pii=False,
                cleaned_content=original,
                word_count=len(original.split()),
            )

    def _get_ingest_schema(self) -> dict[str, Any]:
        """Get JSON schema for ingest"""
        return {
            "type": "object",
            "required": ["language", "pii_detected", "redacted_text", "word_count"],
            "properties": {
                "language": {"type": "string", "enum": ["en", "es", "fr", "de", "zh", "ja", "other"]},
                "pii_detected": {"type": "boolean"},
                "redacted_text": {"type": "string"},
                "word_count": {"type": "integer"},
                "input_quality": {"type": "string", "enum": ["good", "fair", "poor"]},
            },
        }

    def _get_extraction_schema(self) -> dict[str, Any]:
        """Get JSON schema for extraction"""
        return {
            "type": "object",
            "required": ["problem_statement", "desired_outcome", "pain_points", "value_drivers"],
            "properties": {
                "problem_statement": {"type": "string"},
                "current_solution": {"type": ["string", "null"]},
                "desired_outcome": {"type": "string"},
                "pain_points": {"type": "array", "items": {"type": "string"}},
                "value_drivers": {"type": "array", "items": {"type": "string"}},
                "stakeholders": {"type": "array", "items": {"type": "string"}},
                "timeline": {"type": ["string", "null"]},
                "budget_signals": {"type": ["string", "null"]},
                "confidence_score": {"type": "number", "minimum": 0, "maximum": 1},
            },
        }

    def _get_self_check_schema(self) -> dict[str, Any]:
        """Get JSON schema for self-check"""
        return {
            "type": "object",
            "required": ["verifications", "overall_accuracy", "hallucination_risk", "approved"],
            "properties": {
                "verifications": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "claim": {"type": "string"},
                            "supported_by_input": {"type": "boolean"},
                            "evidence": {"type": ["string", "null"]},
                            "confidence": {"type": "number"},
                        },
                    },
                },
                "overall_accuracy": {"type": "number"},
                "hallucination_risk": {"type": "number"},
                "approved": {"type": "boolean"},
                "rejection_reason": {"type": ["string", "null"]},
            },
        }

    def _get_value_prop_schema(self) -> dict[str, Any]:
        """Get JSON schema for value proposition"""
        return {
            "type": "object",
            "required": [
                "headline",
                "problem",
                "solution",
                "differentiation",
                "call_to_action",
                "key_talking_points",
            ],
            "properties": {
                "headline": {"type": "string", "maxLength": 200},
                "problem": {"type": "string"},
                "solution": {"type": "string"},
                "differentiation": {"type": "string"},
                "quantified_value": {"type": ["string", "null"]},
                "call_to_action": {"type": "string"},
                "persona": {"type": "string", "enum": ["executive", "technical", "business_user"]},
                "key_talking_points": {
                    "type": "array",
                    "items": {"type": "string"},
                    "minItems": 3,
                    "maxItems": 5,
                },
            },
        }

    def _build_error_result(
        self, run_id: str, workflow_run: WorkflowRun, error: str
    ) -> WorkflowResult:
        """Build error result when workflow fails"""
        return WorkflowResult(
            run_id=run_id,
            value_proposition=ValueProposition(
                headline="Workflow execution failed",
                problem="An error occurred during workflow execution",
                solution="Please check logs and try again",
                differentiation="N/A",
                call_to_action="Review error message and retry",
                key_talking_points=[
                    "Workflow execution encountered an error",
                    "Check API keys and configuration",
                    "Review logs for detailed error information",
                ],
            ),
            normalized_input=NormalizedInput(
                content="", language=Language.ENGLISH, cleaned_content="", word_count=0
            ),
            extracted_data=ExtractedData(
                problem_statement="",
                desired_outcome="",
                pain_points=["Error"],
                value_drivers=["Error"],
                confidence_score=0.0,
            ),
            self_check=SelfCheckResult(
                verifications=[], overall_accuracy=0.0, hallucination_risk=1.0, approved=False
            ),
            total_latency_ms=workflow_run.total_latency_ms,
            total_cost_usd=workflow_run.total_cost_usd,
            provider_used=self.config.primary_model.provider.value,
            model_used=self.config.primary_model.model_name,
            success=False,
            error=error,
        )
