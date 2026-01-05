# AgentOps Studio - Architecture Deep Dive

## System Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           Client Layer                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐               │
│  │   cURL   │  │ Postman  │  │   SDK    │  │  Custom  │               │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘               │
└───────┼─────────────┼─────────────┼─────────────┼────────────────────────┘
        │             │             │             │
        └─────────────┴─────────────┴─────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      API Gateway / Load Balancer                         │
│                      (nginx, AWS ALB, etc.)                              │
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         FastAPI Application                              │
│  ┌───────────────────────────────────────────────────────────────────┐  │
│  │                    Gunicorn (Process Manager)                     │  │
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐         │  │
│  │  │ Worker 1 │  │ Worker 2 │  │ Worker 3 │  │ Worker 4 │         │  │
│  │  │ Uvicorn  │  │ Uvicorn  │  │ Uvicorn  │  │ Uvicorn  │         │  │
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘         │  │
│  └───────┼─────────────┼─────────────┼─────────────┼────────────────┘  │
│          └─────────────┴─────────────┴─────────────┘                    │
│                            │                                             │
│  ┌─────────────────────────▼─────────────────────────────────────────┐  │
│  │                   Request Handler Layer                           │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐           │  │
│  │  │ Input Valid. │→ │ Cache Check  │→ │ Workflow Exec│           │  │
│  │  └──────────────┘  └──────────────┘  └──────┬───────┘           │  │
│  └─────────────────────────────────────────────┼────────────────────┘  │
└─────────────────────────────────────────────────┼────────────────────────┘
                                                  │
                    ┌─────────────────────────────┼─────────────────────┐
                    │                             ▼                     │
                    │         ┌───────────────────────────────────┐    │
                    │         │    WorkflowExecutor (Orchestrator)│    │
                    │         └───────────────┬───────────────────┘    │
                    │                         │                        │
                    │         ┌───────────────┴───────────────┐        │
                    │         │      4-Step Agent Pipeline    │        │
                    │         │                                │        │
                    │         │  ┌──────────────────────────┐ │        │
                    │         │  │ 1. Ingest Agent          │ │        │
                    │         │  │    - Language Detection  │ │        │
                    │         │  │    - PII Detection       │ │        │
                    │         │  │    - Normalization       │ │        │
                    │         │  └──────────┬───────────────┘ │        │
                    │         │             │                  │        │
                    │         │  ┌──────────▼───────────────┐ │        │
                    │         │  │ 2. Extract Agent         │ │        │
                    │         │  │    - Structured Extraction│ │       │
                    │         │  │    - Function/Tool Calling│ │       │
                    │         │  │    - Confidence Scoring  │ │        │
                    │         │  └──────────┬───────────────┘ │        │
                    │         │             │                  │        │
                    │         │  ┌──────────▼───────────────┐ │        │
                    │         │  │ 3. Self-Check Agent      │ │        │
                    │         │  │    - Fact Verification   │ │        │
                    │         │  │    - Hallucination Check │ │        │
                    │         │  │    - Approval/Rejection  │ │        │
                    │         │  └──────────┬───────────────┘ │        │
                    │         │             │                  │        │
                    │         │  ┌──────────▼───────────────┐ │        │
                    │         │  │ 4. Rewrite Agent         │ │        │
                    │         │  │    - Value Prop Creation │ │        │
                    │         │  │    - Persona Optimization│ │        │
                    │         │  │    - Final Output        │ │        │
                    │         │  └──────────────────────────┘ │        │
                    │         └────────────┬──────────────────┘        │
                    │                      │                           │
                    │         ┌────────────▼──────────────┐            │
                    │         │   Provider Abstraction    │            │
                    │         │   ┌──────────────────┐    │            │
                    │         │   │  Provider Router │    │            │
                    │         │   └────────┬─────────┘    │            │
                    │         │            │              │            │
                    │         │   ┌────────▼──────────┐   │            │
                    │         │   │ Retry + Fallback  │   │            │
                    │         │   └────────┬──────────┘   │            │
                    │         └────────────┼──────────────┘            │
                    └──────────────────────┼───────────────────────────┘
                                           │
          ┌────────────────────────────────┼────────────────────────────────┐
          │                                │                                │
          ▼                                ▼                                ▼
┌────────────────────┐        ┌────────────────────┐        ┌────────────────────┐
│   OpenAI API       │        │  Anthropic API     │        │   Google AI API    │
│                    │        │                    │        │                    │
│  - GPT-4 Turbo     │        │  - Claude 3 Opus   │        │  - Gemini Pro      │
│  - GPT-4           │        │  - Claude 3 Sonnet │        │  - Gemini 1.5 Pro  │
│  - GPT-3.5 Turbo   │        │  - Claude 3 Haiku  │        │                    │
│                    │        │                    │        │                    │
│  Function Calling  │        │  Tool Calling      │        │  Prompt-based JSON │
│  Native JSON Mode  │        │  Custom Tools      │        │  Function Calling  │
└────────┬───────────┘        └────────┬───────────┘        └────────┬───────────┘
         │                             │                             │
         └─────────────────────────────┴─────────────────────────────┘
                                       │
                                       ▼
         ┌─────────────────────────────────────────────────────────────┐
         │                  Observability Layer                         │
         │                                                              │
         │  ┌────────────────┐  ┌────────────────┐  ┌───────────────┐ │
         │  │  Metrics       │  │   Logging      │  │    Tracing    │ │
         │  │                │  │                │  │               │ │
         │  │  - Prometheus  │  │  - Structlog   │  │  - LangSmith  │ │
         │  │  - Grafana     │  │  - JSON format │  │  - OpenTelemetry│
         │  │                │  │  - Sentry      │  │               │ │
         │  └────────────────┘  └────────────────┘  └───────────────┘ │
         └─────────────────────────────────────────────────────────────┘

         ┌─────────────────────────────────────────────────────────────┐
         │                    Data Layer                                │
         │                                                              │
         │  ┌────────────────┐  ┌────────────────┐  ┌───────────────┐ │
         │  │  PostgreSQL    │  │     Redis      │  │    MinIO      │ │
         │  │                │  │                │  │   (S3-compat) │ │
         │  │  - Runs        │  │  - Cache       │  │               │ │
         │  │  - Experiments │  │  - Rate Limit  │  │  - Artifacts  │ │
         │  │  - Analytics   │  │  - Sessions    │  │  - Exports    │ │
         │  └────────────────┘  └────────────────┘  └───────────────┘ │
         └─────────────────────────────────────────────────────────────┘
```

## Request Flow

### 1. Workflow Execution Request

```
Client Request
    │
    ▼
[NGINX/ALB] → Load balancing
    │
    ▼
[Gunicorn] → Worker selection
    │
    ▼
[Uvicorn Worker] → Async request handling
    │
    ▼
[FastAPI Route Handler]
    │
    ├─→ [Pydantic Validation] → Validate RawInput schema
    │       ├─ content: min 10 chars
    │       ├─ source: string
    │       └─ metadata: dict
    │
    ├─→ [Redis Cache Check]
    │       ├─ Generate cache key: SHA256(content + provider + model)
    │       ├─ Query Redis: GET workflow:result:{hash}
    │       └─ If HIT → Return cached result (skip LLM calls)
    │
    ▼
[WorkflowExecutor]
    │
    ├─→ [Initialize]
    │       ├─ Load API keys from settings
    │       ├─ Create provider instance (factory pattern)
    │       ├─ Initialize workflow run tracking
    │       └─ Generate run UUID
    │
    ├─→ [Step 1: Ingest Agent]
    │       ├─ Load system prompt (INGEST_SYSTEM_PROMPT)
    │       ├─ Build user prompt with input content
    │       ├─ Call provider.generate() with retry wrapper
    │       │   └─ [Retry Logic]
    │       │       ├─ Attempt 1 (immediate)
    │       │       ├─ Attempt 2 (wait 1s on failure)
    │       │       └─ Attempt 3 (wait 2s on failure)
    │       ├─ Parse response → NormalizedInput
    │       │   ├─ language: Language enum
    │       │   ├─ detected_pii: List[PIIDetection]
    │       │   ├─ cleaned_content: PII redacted
    │       │   └─ word_count: int
    │       ├─ Record metrics (tokens, cost, latency)
    │       └─ Update workflow run state
    │
    ├─→ [Step 2: Extract Agent]
    │       ├─ Load system prompt (EXTRACT_SYSTEM_PROMPT)
    │       ├─ Build prompt with cleaned content
    │       ├─ Generate JSON schema from ExtractedData model
    │       ├─ Call provider.generate() with schema
    │       │   └─ [Provider-Specific Handling]
    │       │       ├─ OpenAI: Use function calling
    │       │       ├─ Anthropic: Use tool calling
    │       │       └─ Google: Embed schema in prompt
    │       ├─ Parse JSON response → ExtractedData
    │       │   ├─ problem_statement: str
    │       │   ├─ pain_points: List[str]
    │       │   ├─ value_drivers: List[str]
    │       │   └─ confidence_score: float
    │       ├─ Record metrics
    │       └─ Update workflow run state
    │
    ├─→ [Step 3: Self-Check Agent]
    │       ├─ Load system prompt (SELF_CHECK_SYSTEM_PROMPT)
    │       ├─ Build prompt with original + extracted data
    │       ├─ Call provider.generate() with verification schema
    │       ├─ Parse response → SelfCheckResult
    │       │   ├─ verifications: List[ClaimVerification]
    │       │   ├─ overall_accuracy: float (0.0-1.0)
    │       │   ├─ hallucination_risk: float (0.0-1.0)
    │       │   └─ approved: bool
    │       ├─ Record metrics (including hallucination_risk)
    │       ├─ [Decision Gate]
    │       │   ├─ If approved: Continue to Step 4
    │       │   └─ If rejected: Fail workflow with reason
    │       └─ Update workflow run state
    │
    ├─→ [Step 4: Rewrite Agent] (only if self-check passed)
    │       ├─ Load system prompt (REWRITE_SYSTEM_PROMPT)
    │       ├─ Build prompt with verified extracted data
    │       ├─ Call provider.generate() with value prop schema
    │       ├─ Parse response → ValueProposition
    │       │   ├─ headline: str (max 200 chars)
    │       │   ├─ problem: str
    │       │   ├─ solution: str
    │       │   ├─ key_talking_points: List[str] (3-5 items)
    │       │   └─ persona: Persona enum
    │       ├─ Record metrics
    │       └─ Update workflow run state
    │
    ├─→ [Finalize]
    │       ├─ Aggregate metrics across all steps
    │       │   ├─ total_cost_usd: sum of all step costs
    │       │   ├─ total_latency_ms: sum of all step latencies
    │       │   ├─ total_tokens_input: sum across steps
    │       │   └─ total_tokens_output: sum across steps
    │       ├─ Build WorkflowResult
    │       ├─ Cache result in Redis (TTL 1 hour)
    │       ├─ Record Prometheus metrics
    │       │   ├─ workflow_executions_total{provider, model, status}
    │       │   ├─ workflow_duration_seconds{provider, model}
    │       │   ├─ workflow_cost_usd{provider, model}
    │       │   └─ hallucination_risk_score
    │       └─ Log to structlog (JSON)
    │
    ▼
[Response]
    └─ Return WorkflowResult to client
```

## Data Flow Patterns

### Async Execution Pattern

```python
# All I/O is async for concurrency
async def execute_workflow():
    # Steps run sequentially (each depends on previous)
    step1 = await execute_ingest()
    step2 = await execute_extract(step1)
    step3 = await execute_self_check(step1, step2)
    step4 = await execute_rewrite(step2)
    return result

# But multiple requests are handled concurrently
# Uvicorn worker can handle N concurrent workflows
```

### Parallel Provider Execution

```python
# Race multiple providers to find fastest/cheapest
async def execute_parallel():
    tasks = [
        execute_with_provider(Provider.OPENAI),
        execute_with_provider(Provider.ANTHROPIC),
        execute_with_provider(Provider.GOOGLE),
    ]
    # All run concurrently
    results = await asyncio.gather(*tasks)
    return results
```

## Scaling Considerations

### Horizontal Scaling

```
┌─────────────────┐
│  Load Balancer  │
└────────┬────────┘
         │
    ┌────┴────┬─────────┬─────────┐
    │         │         │         │
┌───▼───┐ ┌──▼───┐ ┌──▼───┐ ┌───▼───┐
│ Pod 1 │ │ Pod 2│ │ Pod 3│ │ Pod N │
│ 4 wrk │ │ 4 wrk│ │ 4 wrk│ │ 4 wrk │
└───┬───┘ └──┬───┘ └──┬───┘ └───┬───┘
    │        │        │         │
    └────────┴────────┴─────────┘
             │
    ┌────────┴─────────┐
    │                  │
┌───▼────────┐   ┌────▼──────┐
│   Redis    │   │ Postgres  │
│  (Shared)  │   │ (Shared)  │
└────────────┘   └───────────┘
```

**Scaling Metrics:**
- Workers per pod: `CPU_count * 2 + 1`
- Pods: Scale on CPU > 70% or Queue depth
- Redis: Single instance sufficient for cache (not critical path)
- Postgres: Connection pooling, read replicas

### Performance Characteristics

| Component | Latency | Bottleneck | Optimization |
|-----------|---------|------------|--------------|
| API Handler | <10ms | CPU | Increase workers |
| Cache Lookup | <5ms | Network | Redis cluster |
| LLM Call | 500-5000ms | Provider API | Parallel execution |
| DB Write | <50ms | I/O | Async writes, batching |
| Total Workflow | 2-10s | LLM calls | Caching, cheaper models |

## Security Architecture

### Layers

1. **Network**: TLS termination at load balancer
2. **Authentication**: JWT tokens (to be implemented)
3. **Validation**: Pydantic schemas on all inputs
4. **Secrets**: Environment variables, never in code
5. **PII Protection**: Detection + redaction in Ingest agent
6. **Data Storage**: Encrypted at rest (DB/S3)

### Threat Model

| Threat | Mitigation |
|--------|-----------|
| API abuse | Rate limiting per client |
| Prompt injection | Input sanitization, sandboxed execution |
| PII leakage | Detection + redaction, audit logs |
| Cost overflow | Budget limits, circuit breakers |
| Data exfiltration | Audit logs, access controls |

## Monitoring Strategy

### Metrics (Prometheus)

**Golden Signals:**
- **Latency**: p50, p95, p99 of workflow duration
- **Traffic**: Requests per second by endpoint
- **Errors**: Error rate by provider and step
- **Saturation**: Worker CPU/memory, queue depth

**Business Metrics:**
- Cost per workflow by provider
- Self-check rejection rate
- Token consumption trends
- Cache hit rate

### Logging (Structlog)

**Log Levels:**
- `DEBUG`: Individual step outputs
- `INFO`: Workflow start/complete, metrics
- `WARNING`: Self-check rejections, retries
- `ERROR`: Step failures, provider errors

**Log Enrichment:**
- `run_id`: Trace requests across services
- `provider`, `model`: Context
- `customer_id`: Business context

### Tracing (LangSmith)

- Full LLM call traces
- Prompt/response capture
- Step-by-step execution
- Cost attribution

## Cost Management

### Per-Request Costs

| Provider | Model | ~Cost per Workflow |
|----------|-------|--------------------|
| OpenAI | GPT-4 Turbo | $0.004 - $0.008 |
| OpenAI | GPT-3.5 Turbo | $0.0005 - $0.001 |
| Anthropic | Claude Sonnet | $0.002 - $0.005 |
| Google | Gemini Pro | $0.001 - $0.003 |

### Optimization Strategies

1. **Caching**: 1 hour TTL saves ~70% of dev/test costs
2. **Model Selection**: Use GPT-3.5 for simple extractions
3. **Prompt Tuning**: Shorter prompts = fewer input tokens
4. **Batch Processing**: Process multiple inputs per request

### Budget Alerts

Set alerts at:
- $10/day (development)
- $100/day (staging)
- $1000/day (production)

## Deployment Architecture

### Development
```
docker-compose.yml
├── API (1 worker, auto-reload)
├── Postgres (local)
├── Redis (local)
└── MinIO (local)
```

### Production (Kubernetes)
```
┌────────────────────────────────────────┐
│              Ingress (TLS)             │
└──────────────┬─────────────────────────┘
               │
        ┌──────┴──────┐
        │   Service   │
        └──────┬──────┘
               │
     ┌─────────┴─────────┐
     │                   │
┌────▼──────┐      ┌────▼──────┐
│ API Pod 1 │      │ API Pod N │
│ 4 workers │      │ 4 workers │
└───────────┘      └───────────┘
     │                   │
     └─────────┬─────────┘
               │
     ┌─────────┴─────────────────┐
     │                           │
┌────▼──────┐              ┌────▼──────┐
│  Redis    │              │ Postgres  │
│ (Managed) │              │ (RDS)     │
└───────────┘              └───────────┘
```

**Key Components:**
- HPA: Horizontal Pod Autoscaler (target CPU 70%)
- PDB: Pod Disruption Budget (min 2 pods)
- ConfigMap: Environment configuration
- Secret: API keys, credentials
- PVC: Persistent volume claims

---

This architecture demonstrates production-ready patterns for LLM agent orchestration at scale.
