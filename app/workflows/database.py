"""Database models and operations"""

from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Integer, Float, Boolean, DateTime, JSON, Text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base

from app.config import settings

Base = declarative_base()


class WorkflowRunDB(Base):
    """Database model for workflow runs"""

    __tablename__ = "workflow_runs"

    id = Column(String, primary_key=True)  # UUID
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Input
    input_content = Column(Text, nullable=False)
    input_source = Column(String, nullable=False)
    customer_id = Column(String, nullable=True)

    # Configuration
    provider = Column(String, nullable=False)
    model = Column(String, nullable=False)
    temperature = Column(Float, nullable=False)

    # Execution
    status = Column(String, nullable=False)  # pending, running, success, failed
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_ms = Column(Integer, nullable=True)

    # Results
    value_proposition = Column(JSON, nullable=True)
    normalized_input = Column(JSON, nullable=True)
    extracted_data = Column(JSON, nullable=True)
    self_check_result = Column(JSON, nullable=True)

    # Metrics
    total_tokens_input = Column(Integer, default=0)
    total_tokens_output = Column(Integer, default=0)
    total_cost_usd = Column(Float, default=0.0)
    total_latency_ms = Column(Integer, default=0)

    # Error tracking
    error_message = Column(Text, nullable=True)
    retry_count = Column(Integer, default=0)

    # Self-check metrics
    hallucination_risk = Column(Float, nullable=True)
    overall_accuracy = Column(Float, nullable=True)
    self_check_approved = Column(Boolean, nullable=True)


class ExperimentDB(Base):
    """Database model for prompt/model experiments"""

    __tablename__ = "experiments"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Experiment configuration
    baseline_config = Column(JSON, nullable=False)
    variant_config = Column(JSON, nullable=False)

    # Results
    baseline_runs = Column(Integer, default=0)
    variant_runs = Column(Integer, default=0)

    baseline_avg_cost = Column(Float, default=0.0)
    variant_avg_cost = Column(Float, default=0.0)

    baseline_avg_latency = Column(Float, default=0.0)
    variant_avg_latency = Column(Float, default=0.0)

    baseline_success_rate = Column(Float, default=0.0)
    variant_success_rate = Column(Float, default=0.0)


# Database engine and session
engine = create_async_engine(settings.database_url, echo=False, future=True)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db_session() -> AsyncSession:
    """Get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database tables"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
