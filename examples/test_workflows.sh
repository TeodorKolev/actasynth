#!/bin/bash

# AgentOps Studio - Example API Calls
# This script demonstrates various ways to interact with the API

BASE_URL="${BASE_URL:-http://localhost:8000}"

echo "================================================"
echo "AgentOps Studio - API Examples"
echo "================================================"
echo ""

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test 1: Health Check
echo -e "${BLUE}Test 1: Health Check${NC}"
curl -s "${BASE_URL}/api/v1/health" | jq '.'
echo ""
echo ""

# Test 2: Basic Workflow Execution
echo -e "${BLUE}Test 2: Basic Workflow Execution (OpenAI)${NC}"
curl -s -X POST "${BASE_URL}/api/v1/workflow/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Had a call with Acme Corp today. They are spending 5 hours per day manually entering data from PDF invoices into their ERP system. Their CFO Sarah mentioned they have budget approved for Q1 to automate this. Main pain points: errors in manual entry causing delayed payments, and their current vendor charges per document which is expensive at their volume. They need something that integrates with SAP and maintains audit trails for compliance.",
    "source": "sales_call",
    "customer_id": "acme-corp-001"
  }' | jq '{
    run_id: .run_id,
    success: .success,
    headline: .value_proposition.headline,
    cost_usd: .total_cost_usd,
    latency_ms: .total_latency_ms,
    key_points: .value_proposition.key_talking_points
  }'
echo ""
echo ""

# Test 3: Different Provider (Anthropic)
echo -e "${BLUE}Test 3: Using Anthropic Claude${NC}"
curl -s -X POST "${BASE_URL}/api/v1/workflow/execute?provider=anthropic&model=claude-3-sonnet-20240229" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Customer interview notes: E-commerce company processing 10,000 orders/day. Current system crashes during peak hours, losing sales. CTO mentioned they tried building in-house solution but failed. Budget: $50K. Timeline: ASAP. Key decision maker: VP Engineering Lisa.",
    "source": "discovery_call"
  }' | jq '{
    provider: .provider_used,
    model: .model_used,
    headline: .value_proposition.headline,
    cost: .total_cost_usd,
    latency_ms: .total_latency_ms
  }'
echo ""
echo ""

# Test 4: Temperature Variation
echo -e "${BLUE}Test 4: Creative Output (High Temperature)${NC}"
curl -s -X POST "${BASE_URL}/api/v1/workflow/execute?temperature=0.9" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Startup founder struggling with customer support scaling. Getting 500 tickets/day, response time is 24 hours. Customers complaining on social media. Small team of 3 support agents burning out. Need AI solution.",
    "source": "founder_chat"
  }' | jq '.value_proposition | {
    headline: .headline,
    differentiation: .differentiation
  }'
echo ""
echo ""

# Test 5: Parallel Provider Execution
echo -e "${BLUE}Test 5: Parallel Provider Comparison${NC}"
echo -e "${YELLOW}(This will be slower as it calls multiple providers)${NC}"
curl -s -X POST "${BASE_URL}/api/v1/workflow/execute-parallel" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Enterprise client with 1000 employees. Manual expense reporting taking 2 hours per employee per month. Finance team spending 40 hours/week on reconciliation. Need mobile app, receipt OCR, and policy enforcement.",
    "providers": ["openai", "anthropic"]
  }' | jq 'to_entries | map({
    provider: .key,
    cost_usd: .value.total_cost_usd,
    latency_ms: .value.total_latency_ms,
    headline: .value.value_proposition.headline
  })'
echo ""
echo ""

# Test 6: Metrics Check
echo -e "${BLUE}Test 6: Check Prometheus Metrics${NC}"
echo -e "${YELLOW}Showing workflow execution metrics:${NC}"
curl -s "${BASE_URL}/api/v1/metrics" | grep "workflow_executions_total" | head -5
echo ""
echo ""

# Test 7: Short Input (Should Fail Validation)
echo -e "${BLUE}Test 7: Input Validation (Expected Failure)${NC}"
curl -s -X POST "${BASE_URL}/api/v1/workflow/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Short",
    "source": "test"
  }' | jq '.detail'
echo ""
echo ""

# Test 8: Complex B2B SaaS Scenario
echo -e "${BLUE}Test 8: Complex B2B SaaS Value Proposition${NC}"
curl -s -X POST "${BASE_URL}/api/v1/workflow/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Large healthcare provider with 20 hospitals. Currently using 5 different systems for patient scheduling, causing double-bookings and no-shows. IT Director John mentioned integration with Epic EHR is non-negotiable. Compliance with HIPAA critical. Budget committee meets quarterly. Mentioned competitor quote was $200K but lacked mobile access. Pain point: nurses spending 30 min/day resolving scheduling conflicts.",
    "source": "enterprise_discovery"
  }' | jq '{
    headline: .value_proposition.headline,
    problem: .value_proposition.problem,
    solution: .value_proposition.solution,
    quantified_value: .value_proposition.quantified_value,
    talking_points: .value_proposition.key_talking_points,
    execution_summary: {
      cost: .total_cost_usd,
      latency_ms: .total_latency_ms,
      provider: .provider_used
    }
  }'
echo ""
echo ""

# Test 9: International Use Case
echo -e "${BLUE}Test 9: Multi-language Input Detection${NC}"
curl -s -X POST "${BASE_URL}/api/v1/workflow/execute" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Manufacturing client in Germany. Production line downtime costing €10,000 per hour. Current predictive maintenance system has 40% false positive rate. Need real-time monitoring for 200 machines. CTO Klaus wants pilot program before full rollout.",
    "source": "international_call"
  }' | jq '{
    detected_language: .normalized_input.language,
    headline: .value_proposition.headline,
    quantified_value: .value_proposition.quantified_value
  }'
echo ""
echo ""

echo -e "${GREEN}================================================${NC}"
echo -e "${GREEN}All tests completed!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo -e "Explore more:"
echo -e "  - API Docs: ${BASE_URL}/docs"
echo -e "  - Prometheus: http://localhost:9090"
echo -e "  - Grafana: http://localhost:3000"
echo ""
