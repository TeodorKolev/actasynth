"""API route handlers"""

from typing import Dict, Any
from fastapi import APIRouter, HTTPException, BackgroundTasks
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response

from app.schemas.value_proposition import RawInput, WorkflowResult
from app.schemas.workflow import WorkflowConfig, ModelConfig, Provider
from app.agents.workflow_executor import WorkflowExecutor
from app.config import settings
from app.observability.logger import get_logger
from app.observability.metrics import track_workflow_execution, metrics_registry

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


@router.get("/metrics")
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

        config = WorkflowConfig(primary_model=model_config, enable_tracing=True)

        # Execute workflow
        executor = WorkflowExecutor(config=config, api_keys=settings.get_api_keys())
        result = await executor.execute(raw_input)

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
        raise HTTPException(status_code=500, detail=f"Workflow execution failed: {str(e)}")


@router.post("/workflow/execute-parallel")
async def execute_workflow_parallel(
    raw_input: RawInput,
    providers: list[Provider] = [Provider.OPENAI, Provider.ANTHROPIC],
) -> Dict[str, WorkflowResult]:
    """
    Execute workflow across multiple providers in parallel and return fastest result.

    This demonstrates async parallel execution - a key production pattern.
    Fires requests to multiple providers simultaneously and returns the first
    successful result (or all results for comparison).

    Args:
        raw_input: Raw customer notes/feedback
        providers: List of providers to race

    Returns:
        Dictionary mapping provider name to workflow result
    """
    import asyncio

    logger.info("parallel_workflow_started", providers=[p.value for p in providers])

    # Default models for each provider
    provider_models = {
        Provider.OPENAI: "gpt-5-mini",
        Provider.ANTHROPIC: "claude-sonnet-4-5",
        Provider.GOOGLE: "gemini-2.5-flash-lite",
    }

    async def run_provider(provider: Provider) -> tuple[str, WorkflowResult]:
        """Run workflow for a single provider"""
        try:
            model_config = ModelConfig(
                provider=provider,
                model_name=provider_models[provider],
                temperature=0.7,
                max_tokens=2000,
            )
            config = WorkflowConfig(primary_model=model_config)
            executor = WorkflowExecutor(config=config, api_keys=settings.get_api_keys())
            result = await executor.execute(raw_input)
            return (provider.value, result)
        except Exception as e:
            logger.error("provider_execution_failed", provider=provider.value, error=str(e))
            raise

    # Execute all providers in parallel
    tasks = [run_provider(p) for p in providers]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Build response
    response = {}
    for result in results:
        if isinstance(result, Exception):
            continue
        provider_name, workflow_result = result
        response[provider_name] = workflow_result

    logger.info(
        "parallel_workflow_completed",
        providers_succeeded=len(response),
        providers_total=len(providers),
    )

    if not response:
        raise HTTPException(status_code=500, detail="All providers failed")

    return response


@router.get("/workflow/run/{run_id}")
async def get_workflow_run(run_id: str) -> Dict[str, str]:
    """
    Retrieve a specific workflow run by ID.

    In production, this would query the database.
    For now, returns a placeholder.

    Args:
        run_id: Workflow run ID

    Returns:
        Workflow run details
    """
    # TODO: Implement database query
    return {"run_id": run_id, "status": "not_implemented"}
