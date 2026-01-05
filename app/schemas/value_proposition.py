"""Domain schemas for Value Proposition extraction workflow"""

from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class Language(str, Enum):
    """Detected language codes"""

    ENGLISH = "en"
    SPANISH = "es"
    FRENCH = "fr"
    GERMAN = "de"
    OTHER = "other"


class PIIType(str, Enum):
    """Types of detected PII"""

    EMAIL = "email"
    PHONE = "phone"
    SSN = "ssn"
    CREDIT_CARD = "credit_card"
    NAME = "name"
    ADDRESS = "address"


class RawInput(BaseModel):
    """Input to the value proposition extraction workflow"""

    content: str = Field(..., min_length=10, description="Raw sales notes or customer feedback")
    source: str = Field(default="manual", description="Source of the input (crm, email, call, etc)")
    customer_id: Optional[str] = Field(None, description="Optional customer identifier")
    metadata: dict[str, str] = Field(default_factory=dict, description="Additional metadata")

    @field_validator("content")
    @classmethod
    def content_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("Content cannot be empty or whitespace only")
        return v.strip()


class PIIDetection(BaseModel):
    """Detected PII in input"""

    pii_type: PIIType
    value: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    location: tuple[int, int]  # start, end indices


class NormalizedInput(BaseModel):
    """Output of the Ingest Agent"""

    content: str
    language: Language
    detected_pii: list[PIIDetection] = Field(default_factory=list)
    has_pii: bool = False
    cleaned_content: str  # PII redacted version
    word_count: int
    processed_at: datetime = Field(default_factory=datetime.utcnow)


class ExtractedData(BaseModel):
    """Structured extraction from the Extract Agent"""

    problem_statement: str = Field(..., description="Core problem the customer is facing")
    current_solution: Optional[str] = Field(None, description="How they currently solve it")
    desired_outcome: str = Field(..., description="What success looks like")
    pain_points: list[str] = Field(..., min_length=1, description="Specific pain points mentioned")
    value_drivers: list[str] = Field(
        ..., min_length=1, description="What they value most (cost, time, quality, etc)"
    )
    stakeholders: list[str] = Field(default_factory=list, description="Mentioned decision makers")
    timeline: Optional[str] = Field(None, description="Mentioned timeframes or urgency")
    budget_signals: Optional[str] = Field(None, description="Any budget or cost mentions")
    confidence_score: float = Field(
        ..., ge=0.0, le=1.0, description="Model's confidence in extraction"
    )

    @field_validator("pain_points", "value_drivers")
    @classmethod
    def no_empty_items(cls, v: list[str]) -> list[str]:
        if not all(item.strip() for item in v):
            raise ValueError("List items cannot be empty")
        return [item.strip() for item in v]


class ClaimVerification(BaseModel):
    """Individual claim verification from Self-check Agent"""

    claim: str
    supported_by_input: bool
    evidence: Optional[str] = None
    confidence: float = Field(..., ge=0.0, le=1.0)


class SelfCheckResult(BaseModel):
    """Output of Self-check Agent"""

    verifications: list[ClaimVerification]
    overall_accuracy: float = Field(..., ge=0.0, le=1.0)
    hallucination_risk: float = Field(..., ge=0.0, le=1.0)
    approved: bool
    rejection_reason: Optional[str] = None


class Persona(str, Enum):
    """Target persona for value proposition"""

    EXECUTIVE = "executive"
    TECHNICAL = "technical"
    BUSINESS_USER = "business_user"
    PROCUREMENT = "procurement"


class ValueProposition(BaseModel):
    """Final value proposition output from Rewrite Agent"""

    headline: str = Field(..., max_length=200, description="Compelling one-liner")
    problem: str = Field(..., description="Clear problem articulation")
    solution: str = Field(..., description="How we solve it")
    differentiation: str = Field(..., description="Why us vs alternatives")
    quantified_value: Optional[str] = Field(
        None, description="Specific metrics or outcomes (e.g., '30% cost reduction')"
    )
    call_to_action: str = Field(..., description="Next step for the customer")
    persona: Persona = Field(default=Persona.EXECUTIVE, description="Optimized for this persona")
    key_talking_points: list[str] = Field(
        ..., min_length=3, max_length=5, description="Core points for sales conversation"
    )
    generated_at: datetime = Field(default_factory=datetime.utcnow)


class WorkflowResult(BaseModel):
    """Complete workflow output"""

    run_id: str
    value_proposition: ValueProposition
    normalized_input: NormalizedInput
    extracted_data: ExtractedData
    self_check: SelfCheckResult
    total_latency_ms: int
    total_cost_usd: float
    provider_used: str
    model_used: str
    success: bool
    error: Optional[str] = None
