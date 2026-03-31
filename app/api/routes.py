"""API route handlers"""

from typing import Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

from app.schemas.value_proposition import RawInput, WorkflowResult
from app.schemas.workflow import WorkflowConfig, ModelConfig, Provider
from app.agents.workflow_executor import WorkflowExecutor
from app.api.auth import rate_limited_user, verify_cognito_token
from app.config import settings
from app.observability.logger import get_logger
from app.observability.metrics import track_workflow_execution, metrics_registry
from app.workflows.cache import workflow_cache

logger = get_logger(__name__)
router = APIRouter()


@router.get("/health")
async def health_check() -> Dict[str, str]:
    """
    Health check endpoint.

    Returns:
        Status message
    """
    return {"status": "healthy", "service": "agentops-studio"}


@router.get("/config/check")
async def config_check() -> Dict[str, Any]:
    """
    Check configuration status (for debugging).

    Returns:
        Configuration status
    """
    api_keys = settings.get_api_keys()
    return {
        "openai_key_configured": bool(api_keys.get("openai") and len(api_keys["openai"]) > 10),
        "anthropic_key_configured": bool(api_keys.get("anthropic") and len(api_keys["anthropic"]) > 10),
        "google_key_configured": bool(api_keys.get("google") and len(api_keys["google"]) > 10),
        "environment": settings.environment,
        "langsmith_enabled": settings.langchain_tracing_v2,
    }


@router.get("/metrics", dependencies=[Depends(verify_cognito_token)])
async def metrics() -> Response:
    """
    Prometheus metrics endpoint.

    Returns:
        Prometheus-formatted metrics
    """
    return Response(generate_latest(metrics_registry), media_type=CONTENT_TYPE_LATEST)


@router.post("/workflow/execute", response_model=WorkflowResult)
@track_workflow_execution
async def execute_workflow(
    raw_input: RawInput,
    provider: Provider = Provider.GOOGLE,
    model: str = "gemini-2.5-flash-lite",
    temperature: float = 0.7,
    _user: dict = Depends(rate_limited_user),
) -> WorkflowResult:
    """
    Execute the complete 4-step value proposition workflow.

    This endpoint:
    1. Normalizes input and detects PII
    2. Extracts structured insights
    3. Validates accuracy (self-check)
    4. Generates final value proposition

    Args:
        raw_input: Raw customer notes/feedback
        provider: LLM provider to use (openai, anthropic, google)
        model: Specific model name
        temperature: Model temperature (0.0-1.0)

    Returns:
        Complete workflow result with value proposition and metrics

    Example:
        ```bash
        curl -X POST "http://localhost:8000/workflow/execute" \\
          -H "Content-Type: application/json" \\
          -d '{
            "content": "Customer is struggling with manual data entry...",
            "source": "sales_call"
          }'
        ```
    """
    logger.info(
        "workflow_execution_started",
        provider=provider.value,
        model=model,
        source=raw_input.source,
    )

    try:
        # Build workflow configuration
        model_config = ModelConfig(
            provider=provider, model_name=model, temperature=temperature, max_tokens=2000
        )

        config = WorkflowConfig(primary_model=model_config)

        # Check cache first
        if config.enable_caching:
            cached = await workflow_cache.get(raw_input.content, provider.value, model)
            if cached:
                logger.info("workflow_cache_hit", provider=provider.value, model=model)
                return cached

        # Execute workflow
        executor = WorkflowExecutor(config=config, api_keys=settings.get_api_keys())
        result = await executor.execute(raw_input)

        # Store successful result in cache
        if config.enable_caching and result.success:
            await workflow_cache.set(raw_input.content, provider.value, model, result)

        logger.info(
            "workflow_execution_completed",
            run_id=result.run_id,
            success=result.success,
            total_cost_usd=result.total_cost_usd,
            total_latency_ms=result.total_latency_ms,
        )

        return result

    except Exception as e:
        logger.error("workflow_execution_failed", error=str(e), exc_info=True)
        raise HTTPException(status_code=500, detail="Workflow execution failed. Check server logs for details.")



