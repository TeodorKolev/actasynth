"""Test Pydantic schemas for validation"""

import pytest
from datetime import datetime
from pydantic import ValidationError

from app.schemas.value_proposition import (
    RawInput,
    ExtractedData,
    SelfCheckResult,
    ValueProposition,
    ClaimVerification,
    Persona,
)
from app.schemas.workflow import (
    ModelConfig,
    Provider,
    WorkflowConfig,
    AgentStepResult,
    AgentStep,
    StepStatus,
    ProviderMetrics,
)


class TestRawInput:
    """Test RawInput schema validation"""

    def test_valid_raw_input(self):
        """Test creating valid raw input"""
        raw_input = RawInput(
            content="Customer needs automation for data entry",
            source="sales_call",
            customer_id="customer-123",
        )
        assert raw_input.content == "Customer needs automation for data entry"
        assert raw_input.source == "sales_call"
        assert raw_input.customer_id == "customer-123"

    def test_content_too_short(self):
        """Test that content must be at least 10 characters"""
        with pytest.raises(ValidationError):
            RawInput(content="Short", source="test")

    def test_content_whitespace_stripped(self):
        """Test that whitespace is stripped from content"""
        raw_input = RawInput(content="  Test content  ", source="test")
        assert raw_input.content == "Test content"

    def test_empty_content_fails(self):
        """Test that empty content raises validation error"""
        with pytest.raises(ValidationError):
            RawInput(content="   ", source="test")


class TestExtractedData:
    """Test ExtractedData schema validation"""

    def test_valid_extraction(self):
        """Test creating valid extracted data"""
        extracted = ExtractedData(
            problem_statement="Manual data entry taking 5 hours daily",
            desired_outcome="Automate data entry process",
            pain_points=["Time consuming", "Error prone"],
            value_drivers=["Cost savings", "Efficiency"],
            confidence_score=0.85,
        )
        assert extracted.problem_statement == "Manual data entry taking 5 hours daily"
        assert len(extracted.pain_points) == 2
        assert extracted.confidence_score == 0.85

    def test_empty_pain_points_fails(self):
        """Test that pain_points must have at least one item"""
        with pytest.raises(ValidationError):
            ExtractedData(
                problem_statement="Test",
                desired_outcome="Test",
                pain_points=[],
                value_drivers=["Test"],
                confidence_score=0.5,
            )

    def test_confidence_score_bounds(self):
        """Test confidence score must be between 0 and 1"""
        with pytest.raises(ValidationError):
            ExtractedData(
                problem_statement="Test",
                desired_outcome="Test",
                pain_points=["Test"],
                value_drivers=["Test"],
                confidence_score=1.5,
            )


class TestValueProposition:
    """Test ValueProposition schema validation"""

    def test_valid_value_proposition(self):
        """Test creating valid value proposition"""
        vp = ValueProposition(
            headline="Eliminate 5 hours of manual work daily",
            problem="Manual data entry consuming significant time",
            solution="Automated extraction with AI",
            differentiation="99% accuracy with compliance built-in",
            call_to_action="Schedule a demo this week",
            key_talking_points=[
                "Save 25 hours per week",
                "Built-in compliance",
                "Ready in Q1",
            ],
        )
        assert vp.headline == "Eliminate 5 hours of manual work daily"
        assert len(vp.key_talking_points) == 3
        assert vp.persona == Persona.EXECUTIVE  # default

    def test_headline_max_length(self):
        """Test headline cannot exceed 200 characters"""
        with pytest.raises(ValidationError):
            ValueProposition(
                headline="x" * 201,
                problem="Test",
                solution="Test",
                differentiation="Test",
                call_to_action="Test",
                key_talking_points=["1", "2", "3"],
            )

    def test_key_talking_points_bounds(self):
        """Test key_talking_points must have 3-5 items"""
        with pytest.raises(ValidationError):
            ValueProposition(
                headline="Test",
                problem="Test",
                solution="Test",
                differentiation="Test",
                call_to_action="Test",
                key_talking_points=["1", "2"],  # Too few
            )


class TestWorkflowConfig:
    """Test WorkflowConfig schema"""

    def test_valid_workflow_config(self):
        """Test creating valid workflow configuration"""
        model_config = ModelConfig(
            provider=Provider.OPENAI,
            model_name="gpt-4-turbo-preview",
            temperature=0.7,
            max_tokens=2000,
        )
        config = WorkflowConfig(primary_model=model_config)
        assert config.primary_model.provider == Provider.OPENAI
        assert config.enable_caching is True  # default

    def test_temperature_bounds(self):
        """Test temperature must be between 0 and 2"""
        with pytest.raises(ValidationError):
            ModelConfig(
                provider=Provider.OPENAI,
                model_name="gpt-4",
                temperature=2.5,
            )


class TestAgentStepResult:
    """Test AgentStepResult schema"""

    def test_mark_complete(self):
        """Test marking step as complete updates all fields"""
        step = AgentStepResult(
            step=AgentStep.INGEST,
            status=StepStatus.RUNNING,
            started_at=datetime.utcnow(),
        )

        output = {"test": "data"}
        metrics = ProviderMetrics(
            provider=Provider.OPENAI,
            model="gpt-4",
            latency_ms=500,
            tokens_input=100,
            tokens_output=50,
            cost_usd=0.005,
            success=True,
        )

        step.mark_complete(output, metrics)

        assert step.status == StepStatus.SUCCESS
        assert step.output == output
        assert step.metrics == metrics
        assert step.completed_at is not None
        assert step.duration_ms is not None
        assert step.duration_ms > 0

    def test_mark_failed(self):
        """Test marking step as failed"""
        step = AgentStepResult(
            step=AgentStep.EXTRACT,
            status=StepStatus.RUNNING,
            started_at=datetime.utcnow(),
        )

        step.mark_failed("Provider timeout")

        assert step.status == StepStatus.FAILED
        assert step.error == "Provider timeout"
        assert step.completed_at is not None
