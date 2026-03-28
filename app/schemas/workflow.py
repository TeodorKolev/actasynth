"""Workflow orchestration and execution schemas"""

from datetime import datetime
from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


class Provider(str, Enum):
    """Supported LLM providers"""

    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"


class ModelConfig(BaseModel):
    """Model configuration for a provider"""

    provider: Provider
    model_name: str
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2000, gt=0)
    timeout_seconds: int = Field(default=30, gt=0)


class WorkflowConfig(BaseModel):
    """Configuration for a complete workflow run"""

    primary_model: ModelConfig
    enable_caching: bool = True
    enable_tracing: bool = True
    cache_ttl_seconds: int = Field(default=3600, gt=0)
    parallel_execution: bool = False  # For future multi-provider racing


class AgentStep(str, Enum):
    """Steps in the agent workflow"""

    INGEST = "ingest"
    EXTRACT = "extract"
    SELF_CHECK = "self_check"
    REWRITE = "rewrite"


class StepStatus(str, Enum):
    """Execution status of a step"""

    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    RETRYING = "retrying"


class ProviderMetrics(BaseModel):
    """Metrics for a single provider call"""

    provider: Provider
    model: str
    latency_ms: int
    tokens_input: int
    tokens_output: int
    cost_usd: float
    success: bool
    error: Optional[str] = None
    retry_count: int = 0


class AgentStepResult(BaseModel):
    """Result of a single agent step execution"""

    step: AgentStep
    status: StepStatus
    output: Optional[dict[str, Any]] = None
    metrics: Optional[ProviderMetrics] = None
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_ms: Optional[int] = None
    error: Optional[str] = None

    def mark_complete(self, output: dict[str, Any], metrics: ProviderMetrics) -> None:
        """Mark step as successfully completed"""
        self.status = StepStatus.SUCCESS
        self.output = output
        self.metrics = metrics
        self.completed_at = datetime.utcnow()
        self.duration_ms = int((self.completed_at - self.started_at).total_seconds() * 1000)

    def mark_failed(self, error: str) -> None:
        """Mark step as failed"""
        self.status = StepStatus.FAILED
        self.error = error
        self.completed_at = datetime.utcnow()
        self.duration_ms = int((self.completed_at - self.started_at).total_seconds() * 1000)


class WorkflowRun(BaseModel):
    """Complete workflow execution tracking"""

    run_id: str
    config: WorkflowConfig
    status: StepStatus = StepStatus.PENDING
    steps: list[AgentStepResult] = Field(default_factory=list)
    total_cost_usd: float = 0.0
    total_tokens_input: int = 0
    total_tokens_output: int = 0
    total_latency_ms: int = 0
    started_at: datetime = Field(default_factory=datetime.utcnow)
    completed_at: Optional[datetime] = None
    error: Optional[str] = None

    def add_step_result(self, result: AgentStepResult) -> None:
        """Add a step result and update aggregates"""
        self.steps.append(result)
        if result.metrics:
            self.total_cost_usd += result.metrics.cost_usd
            self.total_tokens_input += result.metrics.tokens_input
            self.total_tokens_output += result.metrics.tokens_output
            if result.duration_ms:
                self.total_latency_ms += result.duration_ms

    def mark_complete(self, success: bool = True, error: Optional[str] = None) -> None:
        """Mark workflow as complete"""
        self.status = StepStatus.SUCCESS if success else StepStatus.FAILED
        self.completed_at = datetime.utcnow()
        if error:
            self.error = error
