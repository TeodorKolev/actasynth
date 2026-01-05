"""Prometheus metrics for monitoring"""

from functools import wraps
from typing import Any, Callable
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry

# Create a custom registry
metrics_registry = CollectorRegistry()

# Workflow execution metrics
workflow_executions_total = Counter(
    "workflow_executions_total",
    "Total number of workflow executions",
    ["provider", "model", "status"],
    registry=metrics_registry,
)

workflow_duration_seconds = Histogram(
    "workflow_duration_seconds",
    "Workflow execution duration in seconds",
    ["provider", "model"],
    registry=metrics_registry,
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0],
)

workflow_cost_usd = Histogram(
    "workflow_cost_usd",
    "Cost of workflow execution in USD",
    ["provider", "model"],
    registry=metrics_registry,
    buckets=[0.0001, 0.001, 0.01, 0.1, 1.0, 10.0],
)

# Token usage metrics
tokens_consumed_total = Counter(
    "tokens_consumed_total",
    "Total tokens consumed",
    ["provider", "model", "type"],  # type = input/output
    registry=metrics_registry,
)

# Agent step metrics
agent_step_duration_seconds = Histogram(
    "agent_step_duration_seconds",
    "Duration of individual agent steps",
    ["step", "provider"],
    registry=metrics_registry,
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 20.0],
)

agent_step_failures_total = Counter(
    "agent_step_failures_total",
    "Total number of agent step failures",
    ["step", "provider"],
    registry=metrics_registry,
)

# Self-check metrics
hallucination_risk_score = Histogram(
    "hallucination_risk_score",
    "Hallucination risk score from self-check",
    registry=metrics_registry,
    buckets=[0.0, 0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
)

self_check_rejections_total = Counter(
    "self_check_rejections_total",
    "Total number of self-check rejections",
    ["reason"],
    registry=metrics_registry,
)

# Active workflows
active_workflows = Gauge(
    "active_workflows",
    "Number of currently active workflows",
    registry=metrics_registry,
)


def track_workflow_execution(func: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to track workflow execution metrics.

    Usage:
        @track_workflow_execution
        async def execute_workflow(...):
            ...
    """

    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        import time

        active_workflows.inc()
        start_time = time.perf_counter()

        try:
            result = await func(*args, **kwargs)

            # Extract metrics from result
            duration = time.perf_counter() - start_time
            provider = result.provider_used if hasattr(result, "provider_used") else "unknown"
            model = result.model_used if hasattr(result, "model_used") else "unknown"
            status = "success" if result.success else "failure"

            # Record metrics
            workflow_executions_total.labels(provider=provider, model=model, status=status).inc()
            workflow_duration_seconds.labels(provider=provider, model=model).observe(duration)

            if hasattr(result, "total_cost_usd"):
                workflow_cost_usd.labels(provider=provider, model=model).observe(
                    result.total_cost_usd
                )

            return result

        except Exception as e:
            workflow_executions_total.labels(
                provider="unknown", model="unknown", status="error"
            ).inc()
            raise

        finally:
            active_workflows.dec()

    return wrapper
