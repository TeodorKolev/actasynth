# AgentOps Studio - Quick Start Guide

Get up and running in under 5 minutes.

## Prerequisites

- Python 3.11+ OR Docker
- API keys for at least one provider (OpenAI, Anthropic, or Google)

## Option 1: Docker (Recommended)

The fastest way to see the system in action:

```bash
# 1. Clone the repository
git clone <your-repo-url>
cd agentops-studio

# 2. Create environment file
cp .env.example .env

# 3. Add your API keys to .env
# Edit .env and add:
#   OPENAI_API_KEY=sk-your-key-here
#   ANTHROPIC_API_KEY=sk-ant-your-key-here
#   GOOGLE_API_KEY=your-key-here

# 4. Start the stack
docker-compose up -d

# 5. Wait for services to be ready (~30 seconds)
docker-compose logs -f api

# 6. Test the API
curl http://localhost:8000/api/v1/health
```

Services now running:
- **API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **MinIO**: http://localhost:9001 (minioadmin/minioadmin)

## Option 2: Local Development

For active development:

```bash
# 1. Install dependencies
poetry install

# 2. Create .env file
cp .env.example .env

# 3. Add API keys to .env

# 4. Run the server
poetry run python -m app.main

# Or use the Makefile
make run
```

Server running at: http://localhost:8000

## Your First Request

### Basic Workflow Execution

```bash
curl -X POST "http://localhost:8000/api/v1/workflow/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Had a call with Acme Corp today. They are spending 5 hours per day manually entering data from PDF invoices into their ERP system. Their CFO Sarah mentioned they have budget approved for Q1 to automate this. Main pain points: errors in manual entry causing delayed payments, and their current vendor charges per document which is expensive at their volume. They need something that integrates with SAP and maintains audit trails for compliance.",
    "source": "sales_call",
    "customer_id": "acme-corp"
  }'
```

### Expected Response

```json
{
  "run_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "value_proposition": {
    "headline": "Eliminate 5 hours of daily manual invoice entry with compliant automation",
    "problem": "Manual PDF invoice data entry consuming 5 hours daily with error-prone processes causing payment delays",
    "solution": "AI-powered invoice extraction with SAP integration and built-in audit trails",
    "differentiation": "Unlike per-document pricing, flat-rate model saves costs at high volumes with guaranteed compliance",
    "quantified_value": "Save 25 hours per week per employee, reduce payment delays by 40%",
    "call_to_action": "Schedule Q1 implementation planning meeting with Sarah",
    "persona": "executive",
    "key_talking_points": [
      "Eliminate 5 hours of manual work per day",
      "Native SAP integration with audit compliance",
      "Flat-rate pricing beats per-document costs at scale",
      "Ready for Q1 deployment timeline",
      "Reduce payment delays and manual errors"
    ]
  },
  "total_latency_ms": 2847,
  "total_cost_usd": 0.0056,
  "provider_used": "openai",
  "model_used": "gpt-4-turbo-preview",
  "success": true
}
```

### Try Different Providers

```bash
# Use Anthropic Claude
curl -X POST "http://localhost:8000/api/v1/workflow/execute?provider=anthropic&model=claude-3-sonnet-20240229" \
  -H "Content-Type: application/json" \
  -d '{ ... }'

# Use Google Gemini
curl -X POST "http://localhost:8000/api/v1/workflow/execute?provider=google&model=gemini-pro" \
  -H "Content-Type: application/json" \
  -d '{ ... }'
```

### Parallel Provider Execution

Race multiple providers to compare latency and cost:

```bash
curl -X POST "http://localhost:8000/api/v1/workflow/execute-parallel" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Your sales notes here...",
    "providers": ["openai", "anthropic", "google"]
  }'
```

## Explore the System

### 1. API Documentation

Visit http://localhost:8000/docs for interactive Swagger UI:
- Try all endpoints
- See request/response schemas
- Test with your own data

### 2. Prometheus Metrics

Visit http://localhost:9090:
- Query: `workflow_executions_total`
- Query: `rate(workflow_duration_seconds_sum[5m])`
- Query: `workflow_cost_usd`

### 3. Grafana Dashboards

Visit http://localhost:3000 (admin/admin):
1. Add Prometheus data source: http://prometheus:9090
2. Import dashboard or create custom views
3. Monitor real-time metrics

### 4. LangSmith Tracing (Optional)

If you have LangSmith API key:

```bash
# Add to .env
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=your-langsmith-key
LANGCHAIN_PROJECT=agentops-studio

# Restart services
docker-compose restart api
```

Visit https://smith.langchain.com to see detailed traces.

## Common Tasks

### View Logs

```bash
# All services
docker-compose logs -f

# Just API
docker-compose logs -f api

# With timestamps
docker-compose logs -f --timestamps api
```

### Check Service Health

```bash
# API health
curl http://localhost:8000/api/v1/health

# Redis
docker-compose exec redis redis-cli ping

# Postgres
docker-compose exec postgres pg_isready -U agentops
```

### Access Database

```bash
# PostgreSQL shell
docker-compose exec postgres psql -U agentops

# Inside psql:
\dt                          # List tables
SELECT * FROM workflow_runs; # View runs
```

### Access Redis

```bash
# Redis CLI
docker-compose exec redis redis-cli

# Inside redis-cli:
KEYS *                       # List all keys
GET workflow:result:abc123   # Get cached result
```

## Development Workflow

```bash
# Format code
make format

# Run linters
make lint

# Run tests
make test

# Clean cache
make clean
```

## Troubleshooting

### "Connection refused" errors

Services take ~30 seconds to start. Wait and retry.

```bash
# Check all services are running
docker-compose ps

# Restart if needed
docker-compose restart
```

### "API key not found" errors

Ensure .env file has valid API keys:

```bash
# Check .env file exists
cat .env | grep API_KEY

# Restart to pick up changes
docker-compose restart api
```

### Tests failing

Install dev dependencies:

```bash
poetry install  # Includes dev dependencies
make test
```

### Port conflicts

If ports 8000, 5432, 6379, 9000 are in use:

Edit docker-compose.yml:
```yaml
ports:
  - "8001:8000"  # Use 8001 instead of 8000
```

## Next Steps

1. **Read the detailed README**: See [README_DETAILED.md](README_DETAILED.md) for architecture deep-dive
2. **Customize prompts**: Edit [app/prompts/templates.py](app/prompts/templates.py)
3. **Add your own agents**: Extend [app/agents/workflow_executor.py](app/agents/workflow_executor.py)
4. **Experiment with models**: Try different model configurations
5. **Monitor metrics**: Set up Grafana dashboards
6. **Run experiments**: Compare prompts and providers

## Production Checklist

Before deploying to production:

- [ ] Add authentication (JWT tokens)
- [ ] Configure HTTPS/TLS
- [ ] Set up rate limiting per client
- [ ] Configure Sentry error tracking
- [ ] Set up database backups
- [ ] Configure log aggregation
- [ ] Set up monitoring alerts
- [ ] Review security settings
- [ ] Configure autoscaling
- [ ] Set cost budgets and alerts

## Getting Help

- **API Issues**: Check logs with `docker-compose logs -f api`
- **Provider Issues**: Verify API keys and quotas
- **Performance**: Check Prometheus metrics
- **Bugs**: Open an issue on GitHub

---

**You're ready to go!** The system is running and processing workflows. Try different inputs, experiment with providers, and explore the observability tools.
