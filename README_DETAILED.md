# AgentOps Studio

**Production-grade LLM agent orchestration for value proposition extraction**

A FastAPI service that designs, runs, and observes agentic workflows across OpenAI, Anthropic, and Google with full tracing, cost accounting, retries, and structured outputs.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109+-green.svg)](https://fastapi.tiangolo.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Core Use Case](#core-use-case)
- [Agent Workflow](#agent-workflow)
- [Technical Stack](#technical-stack)
- [Getting Started](#getting-started)
- [API Endpoints](#api-endpoints)
- [Observability](#observability)
- [Design Decisions](#design-decisions)
- [Production Considerations](#production-considerations)
- [Future Enhancements](#future-enhancements)

---

## Overview

AgentOps Studio is a **production-ready system** for orchestrating multi-step LLM agent workflows. It transforms unstructured customer feedback into validated, structured value propositions using a 4-agent pipeline with built-in quality controls.

**Key Features:**

- 🤖 Multi-provider support (OpenAI, Anthropic, Google)
- ⚡ Async-first architecture with FastAPI + Gunicorn
- 📊 Full observability (Prometheus metrics, LangSmith tracing, structured logging)
- 🔄 Automatic retries with exponential backoff
- 💾 Redis caching for cost optimization
- 🗄️ PostgreSQL for workflow persistence
- 🛡️ PII detection and hallucination prevention
- 🐳 Production Docker setup

---

## Architecture

### High-Level Design

```
┌─────────────┐
│   Client    │
└─────┬───────┘
      │
      ▼
┌─────────────────────────────────────────────┐
│          FastAPI Application                │
│  ┌──────────────────────────────────────┐  │
│  │  Async Request Handler               │  │
│  └──────────────┬───────────────────────┘  │
│                 │                           │
│  ┌──────────────▼───────────────────────┐  │
│  │      WorkflowExecutor                │  │
│  │  ┌────────────────────────────────┐  │  │
│  │  │  1. Ingest  (PII Detection)    │  │  │
│  │  │  2. Extract (Structured Data)  │  │  │
│  │  │  3. Self-Check (Verification)  │  │  │
│  │  │  4. Rewrite (Value Prop)       │  │  │
│  │  └────────────────────────────────┘  │  │
│  └──────────────┬───────────────────────┘  │
│                 │                           │
│  ┌──────────────▼───────────────────────┐  │
│  │   Provider Abstraction Layer        │  │
│  │  ┌─────────┬──────────┬──────────┐  │  │
│  │  │ OpenAI  │Anthropic │  Google  │  │  │
│  │  └─────────┴──────────┴──────────┘  │  │
│  └──────────────────────────────────────┘  │
└─────────────────────────────────────────────┘
      │                           │
      ▼                           ▼
┌───────────┐              ┌──────────────┐
│   Redis   │              │  PostgreSQL  │
│  (Cache)  │              │  (Runs)      │
└───────────┘              └──────────────┘
      │
      ▼
┌──────────────────┐
│   LangSmith      │
│   (Tracing)      │
└──────────────────┘
```

### Directory Structure

```
app/
├── api/                    # FastAPI routes and handlers
│   └── routes.py          # REST endpoints
├── agents/                # Agent orchestration
│   └── workflow_executor.py  # 4-step pipeline
├── providers/             # LLM provider abstractions
│   ├── base.py           # Abstract provider interface
│   ├── openai_provider.py
│   ├── anthropic_provider.py
│   ├── google_provider.py
│   └── factory.py        # Provider factory
├── prompts/              # Prompt templates
│   └── templates.py      # System prompts per agent
├── schemas/              # Pydantic models
│   ├── value_proposition.py
│   └── workflow.py
├── workflows/            # Workflow utilities
│   ├── cache.py         # Redis caching
│   └── database.py      # Postgres models
├── observability/        # Logging and metrics
│   ├── logger.py        # Structured logging
│   └── metrics.py       # Prometheus metrics
├── config.py            # Settings management
└── main.py             # FastAPI application
```

---

## Core Use Case

**Problem:** Sales teams have unstructured notes from customer conversations (calls, emails, CRM entries) and need to extract actionable value propositions.

**Solution:** A 4-step AI agent pipeline that:

1. **Normalizes** raw input and detects PII
2. **Extracts** structured business insights
3. **Validates** accuracy and prevents hallucinations
4. **Generates** persona-specific value propositions

**Input Example:**
```
"Had a call with Acme Corp. They're manually entering data from PDFs into
spreadsheets - takes 5 hours/day. Looking for automation. Budget approved
for Q1. CFO Sarah mentioned compliance is critical."
```

**Output Example:**
```json
{
  "headline": "Eliminate 5 hours of daily manual data entry with compliant automation",
  "problem": "Manual PDF-to-spreadsheet data entry consuming 5 hours daily",
  "solution": "Automated data extraction with built-in compliance controls",
  "quantified_value": "Save 25 hours/week per employee",
  "key_talking_points": [
    "Reduce manual data entry from 5 hours to minutes",
    "Built-in compliance for CFO approval",
    "Ready for Q1 deployment"
  ]
}
```

---

## Agent Workflow

### Step 1: Ingest Agent

**Purpose:** Normalize input, detect language and PII

**Outputs:**
- Language detection
- PII identification (emails, phones, names)
- Cleaned content (PII redacted)
- Word count and quality metrics

**Prompt Strategy:** Conservative PII detection - avoid false positives on company names.

### Step 2: Extract Agent

**Purpose:** Extract structured business insights using function calling

**Outputs:**
- Problem statement
- Current solution approach
- Desired outcomes
- Pain points
- Value drivers
- Stakeholders, timeline, budget signals
- Confidence score

**Prompt Strategy:** Only extract what's explicitly stated. Use customer's language. Provide confidence score.

**Provider Notes:**
- OpenAI: Uses function calling with strict schema
- Anthropic: Uses tool calling (Claude 3+)
- Google: Schema embedded in prompt (Gemini limitations)

### Step 3: Self-Check Agent

**Purpose:** Prevent hallucinations through fact-checking

**Outputs:**
- Claim-by-claim verification
- Evidence from original input
- Overall accuracy score (0.0-1.0)
- Hallucination risk score (0.0-1.0)
- Approval decision

**Validation Rules:**
- Approved if: `accuracy > 0.7 AND hallucination_risk < 0.3`
- Rejected extractions stop the workflow

**Prompt Strategy:** Strict verification. Better to reject than pass hallucinated content.

### Step 4: Rewrite Agent

**Purpose:** Generate compelling, persona-specific value proposition

**Outputs:**
- Headline (max 200 chars)
- Problem articulation
- Solution description
- Differentiation
- Quantified value (when possible)
- Call to action
- 3-5 key talking points

**Prompt Strategy:** Match persona (Executive=ROI, Technical=capabilities). Be specific over generic.

---

## Technical Stack

### Core Framework
- **FastAPI** - Async Python web framework
- **Gunicorn** - WSGI HTTP server with Uvicorn workers
- **Pydantic** - Data validation and settings

### LLM Integration
- **LangChain** - Agent orchestration (optional, can be toggled off)
- **LangSmith** - Tracing and monitoring
- **OpenAI SDK** - GPT-4 integration
- **Anthropic SDK** - Claude integration
- **Google Generative AI** - Gemini integration

### Data & Caching
- **PostgreSQL** (asyncpg) - Workflow persistence
- **Redis** (hiredis) - Result caching and rate limiting
- **SQLAlchemy 2.0** - Async ORM

### Observability
- **Prometheus** - Metrics collection
- **Grafana** - Metrics visualization
- **Structlog** - Structured JSON logging
- **Sentry** - Error tracking

### Infrastructure
- **Docker** - Containerization
- **Docker Compose** - Multi-service orchestration
- **MinIO** - S3-compatible object storage

---

## Getting Started

### Prerequisites

- Python 3.11+
- Docker and Docker Compose (for full stack)
- API keys for OpenAI, Anthropic, and/or Google

### Installation

#### Option 1: Local Development

```bash
# Clone repository
git clone https://github.com/yourusername/agentops-studio.git
cd agentops-studio

# Install dependencies
poetry install

# Copy environment template
cp .env.example .env

# Edit .env with your API keys
# Required: OPENAI_API_KEY, ANTHROPIC_API_KEY, GOOGLE_API_KEY

# Run development server
make run

# Or directly
poetry run python -m app.main
```

#### Option 2: Docker (Full Stack)

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys

# Start all services
make docker-up

# View logs
make docker-logs

# Stop services
make docker-down
```

### Quick Test

```bash
curl -X POST "http://localhost:8000/api/v1/workflow/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Customer struggling with 5 hours/day manual data entry from PDFs. Looking for automation. Budget approved.",
    "source": "sales_call"
  }'
```

---

## API Endpoints

### `POST /api/v1/workflow/execute`

Execute the 4-step value proposition workflow.

**Request:**
```json
{
  "content": "Raw customer notes...",
  "source": "sales_call",
  "customer_id": "optional-id"
}
```

**Query Parameters:**
- `provider`: `openai` | `anthropic` | `google` (default: `openai`)
- `model`: Model name (default: `gpt-4-turbo-preview`)
- `temperature`: 0.0-1.0 (default: 0.7)

**Response:**
```json
{
  "run_id": "uuid",
  "value_proposition": {
    "headline": "...",
    "problem": "...",
    "solution": "...",
    "key_talking_points": [...]
  },
  "total_latency_ms": 1234,
  "total_cost_usd": 0.0045,
  "provider_used": "openai",
  "success": true
}
```

### `POST /api/v1/workflow/execute-parallel`

Execute workflow across multiple providers in parallel (race mode).

**Use Case:** Demonstrate async parallel execution and provider comparison.

**Request:**
```json
{
  "content": "Customer notes...",
  "providers": ["openai", "anthropic"]
}
```

**Response:**
```json
{
  "openai": { "run_id": "...", "total_latency_ms": 820, ... },
  "anthropic": { "run_id": "...", "total_latency_ms": 1050, ... }
}
```

### `GET /api/v1/health`

Health check endpoint.

### `GET /api/v1/metrics`

Prometheus metrics endpoint.

**Metrics Include:**
- `workflow_executions_total` - Counter by provider, model, status
- `workflow_duration_seconds` - Histogram
- `workflow_cost_usd` - Histogram
- `tokens_consumed_total` - Counter
- `hallucination_risk_score` - Histogram
- `self_check_rejections_total` - Counter

---

## Observability

### Structured Logging

All logs are JSON-formatted for easy parsing:

```json
{
  "event": "workflow_execution_started",
  "provider": "openai",
  "model": "gpt-4-turbo-preview",
  "timestamp": "2025-01-05T12:00:00Z",
  "level": "info"
}
```

### Metrics (Prometheus)

Access Prometheus at `http://localhost:9090`

**Key Metrics:**
- Execution counts by provider/model/status
- Latency percentiles (p50, p95, p99)
- Cost distribution
- Token usage
- Hallucination risk scores
- Self-check rejection rates

### Tracing (LangSmith)

When `LANGCHAIN_TRACING_V2=true`:
- Every workflow run creates a trace
- View step-by-step execution
- Compare prompts and outputs
- Analyze costs per step

### Dashboards (Grafana)

Access Grafana at `http://localhost:3000` (admin/admin)

Pre-configured dashboards show:
- Request rate and latency
- Error rates by provider
- Cost trends
- Token consumption
- Self-check approval rates

---

## Design Decisions

### Why Async Everywhere?

**Decision:** Use asyncio for all I/O operations.

**Rationale:**
- LLM calls have high latency (0.5-5s)
- Async allows handling multiple requests concurrently
- Better resource utilization on multi-core systems
- Enables parallel provider execution (race mode)

**Trade-off:** Slightly more complex code, but necessary for production scale.

### Why Provider Abstraction?

**Decision:** Abstract providers behind a common interface.

**Rationale:**
- Different providers have different APIs (OpenAI uses functions, Anthropic uses tools, Gemini uses prompt-based schemas)
- Enables easy switching and A/B testing
- Insulates application logic from provider changes
- Allows parallel execution for cost/latency optimization

**Implementation:** Base class with `generate()` method, provider-specific subclasses.

### Why Self-Check Agent?

**Decision:** Dedicate an entire agent to fact-checking.

**Rationale:**
- LLMs hallucinate - especially with extraction tasks
- Can't trust extraction without verification
- Sales decisions based on wrong data are costly
- Better to reject and retry than pass bad data

**Trade-off:** Adds latency and cost, but prevents larger downstream issues.

### Why Structured Output (JSON Schema)?

**Decision:** Enforce strict JSON schemas for agent outputs.

**Rationale:**
- Guarantees parseable, type-safe responses
- Prevents free-form text that's hard to validate
- Enables database storage and downstream processing
- Function/tool calling is more reliable than prompt-only approaches

### Why Redis Caching?

**Decision:** Cache workflow results by content hash.

**Rationale:**
- LLM calls are expensive ($0.001-0.10 per request)
- Identical inputs produce nearly identical outputs
- Development/testing scenarios often reuse inputs
- Configurable TTL (default 1 hour) balances freshness vs cost

### Why Prometheus Over CloudWatch/DataDog?

**Decision:** Use Prometheus for metrics.

**Rationale:**
- Self-hosted, no vendor lock-in
- Excellent Grafana integration
- Pull-based model works well for Docker
- Standard in Kubernetes environments

**Trade-off:** Requires running Prometheus server, but included in docker-compose.

### Why Gunicorn + Uvicorn?

**Decision:** Run FastAPI with Gunicorn as process manager + Uvicorn workers.

**Rationale:**
- Gunicorn handles worker lifecycle, restarts, graceful shutdowns
- Uvicorn provides ASGI interface for async
- Industry standard for production Python deployments
- Better than running Uvicorn directly (no process management)

**Configuration:** `workers = CPU_count * 2 + 1` (Gunicorn recommendation)

---

## Production Considerations

### Security

**Implemented:**
- Non-root Docker user
- Environment-based secrets (no hardcoded keys)
- PII detection and redaction
- Input validation with Pydantic

**TODO (before production):**
- HTTPS/TLS termination (reverse proxy or cert mounting)
- API authentication (JWT tokens, API keys)
- Rate limiting per client (currently global)
- Input sanitization for SQL injection (SQLAlchemy handles this)

### Scaling

**Horizontal Scaling:**
- Stateless API servers (scale with replicas)
- Redis for shared cache
- PostgreSQL connection pooling (asyncpg)

**Vertical Scaling:**
- Increase Gunicorn workers (CPU-bound)
- Increase Redis memory (cache-bound)
- Increase Postgres resources (write-heavy)

**Bottlenecks:**
- LLM API rate limits (provider-specific)
- Database writes (async helps, consider batching)

### Cost Optimization

**Strategies:**
1. **Caching** - Redis cache hits save ~$0.005/request
2. **Model Selection** - Use GPT-3.5 for simple tasks, GPT-4 for complex
3. **Provider Routing** - Route to cheapest provider that meets SLA
4. **Prompt Tuning** - Shorter prompts = fewer input tokens

**Current Costs (per workflow):**
- OpenAI GPT-4 Turbo: ~$0.004-0.008
- Anthropic Claude Sonnet: ~$0.002-0.005
- Google Gemini Pro: ~$0.001-0.003

### Error Handling

**Retry Strategy:**
- Exponential backoff (1s, 2s, 4s)
- Max 3 retries per step
- Provider fallback (optional)

**Error Scenarios:**
1. Rate limit: Retry with delay
2. Timeout: Retry with same provider
3. Invalid response: Retry (may be transient)
4. Persistent failure: Return error to client

### Monitoring Alerts

**Recommended Alerts:**
- Error rate > 5% (5min window)
- p95 latency > 10s
- Self-check rejection rate > 30%
- Cost/hour > threshold
- Redis/Postgres unavailable

---

## Future Enhancements

### Short Term
- [ ] Add authentication (JWT)
- [ ] Implement database query endpoints
- [ ] Add prompt versioning and A/B testing
- [ ] Provider auto-routing based on cost/latency SLA
- [ ] Streaming responses (SSE)

### Medium Term
- [ ] Background job queue (Celery/RQ)
- [ ] Vector store for retrieval-augmented generation
- [ ] Multi-language support (prompts in multiple languages)
- [ ] Workflow customization API (custom agent steps)
- [ ] UI for workflow visualization

### Long Term
- [ ] Auto-scaling based on queue depth
- [ ] Multi-tenant support
- [ ] Model fine-tuning pipeline
- [ ] Real-time collaboration on value propositions

---

## Running Tests

```bash
# Run all tests
make test

# Run with coverage
poetry run pytest --cov=app --cov-report=html

# Run specific test file
poetry run pytest tests/test_providers.py -v
```

---

## Development Workflow

```bash
# Format code
make format

# Lint code
make lint

# Run locally
make run

# Build Docker image
make docker-build

# Start stack
make docker-up

# View logs
make docker-logs

# Clean cache
make clean
```

---

## License

MIT License - see [LICENSE](LICENSE)

---

## Acknowledgments

- Inspired by production patterns from Stripe, Anthropic, and OpenAI
- Prompt engineering patterns from OpenAI Cookbook
- FastAPI best practices from Sebastián Ramírez

---

## Questions?

This is a technical demonstration project showing production-grade engineering for LLM agent orchestration.

**What this demonstrates:**
- ✅ Async Python (FastAPI, asyncio, concurrent LLM calls)
- ✅ Multi-provider LLM integration (OpenAI, Anthropic, Google)
- ✅ Production infrastructure (Docker, Gunicorn, PostgreSQL, Redis)
- ✅ Observability (Prometheus, Grafana, LangSmith, structured logging)
- ✅ Safety (PII detection, hallucination prevention, retries)
- ✅ Cost awareness (token accounting, caching, model selection)

**What this is NOT:**
- ❌ A toy chatbot
- ❌ A single-provider wrapper
- ❌ An unmonitored black box
- ❌ Production-deployed (but production-ready architecture)
