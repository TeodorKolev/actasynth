#!/bin/bash

# Test scenarios showcasing AgentOps Studio capabilities
# Each scenario demonstrates different aspects of the value prop generation

BASE_URL="http://localhost:8000/api/v1/workflow/execute"
PROVIDER="google"
MODEL="gemini-2.5-flash"

echo "========================================="
echo "AgentOps Studio - Test Scenarios"
echo "========================================="
echo ""

# Scenario 1: Minimal input (already tested)
echo "📝 Scenario 1: Minimal Input - Data Entry Pain"
echo "-----------------------------------------"
curl -X POST "${BASE_URL}?provider=${PROVIDER}&model=${MODEL}" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Customer struggling with manual data entry.",
    "source": "sales_call"
  }' | jq -r '.value_proposition.headline, .value_proposition.quantified_value'

echo -e "\n\n"

# Scenario 2: Rich context with stakeholders and timeline
echo "📝 Scenario 2: Enterprise Sale - Cloud Migration"
echo "-----------------------------------------"
curl -X POST "${BASE_URL}?provider=${PROVIDER}&model=${MODEL}" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "CFO and CTO both concerned about rising infrastructure costs - currently spending $45K/month on legacy data centers. Want to migrate to cloud within 6 months. Main pain points: unpredictable scaling, 3-day deployment cycles, and 24/7 maintenance burden on small DevOps team. Budget allocated: $200K for migration.",
    "source": "discovery_call"
  }' | jq -r '.value_proposition.headline, .value_proposition.problem, .value_proposition.quantified_value, .extracted_data.stakeholders, .extracted_data.budget_signals, .extracted_data.timeline'

echo -e "\n\n"

# Scenario 3: Multiple pain points - Customer support
echo "📝 Scenario 3: SaaS Platform - Customer Support Crisis"
echo "-----------------------------------------"
curl -X POST "${BASE_URL}?provider=${PROVIDER}&model=${MODEL}" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "VP of Customer Success reporting major issues: ticket volume up 300% in last quarter, average response time is 48 hours (should be 4 hours), customer churn increased by 15%, support team is burned out. They need to handle 5000+ tickets/month with only 8 agents. Losing customers to competitors who offer instant chat support.",
    "source": "sales_call"
  }' | jq -r '.value_proposition.headline, .value_proposition.key_talking_points[], .self_check.overall_accuracy'

echo -e "\n\n"

# Scenario 4: Technical buyer - Security focus
echo "📝 Scenario 4: Security-Focused - Compliance Nightmare"
echo "-----------------------------------------"
curl -X POST "${BASE_URL}?provider=${PROVIDER}&model=${MODEL}" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "CISO needs to achieve SOC 2 Type II compliance by Q3. Currently failing audits due to manual access reviews, no centralized logging, and inconsistent security policies across 50+ microservices. Risk of losing enterprise customers who require certification. Last audit found 127 critical gaps.",
    "source": "technical_discovery"
  }' | jq -r '.value_proposition.headline, .value_proposition.differentiation, .extracted_data.pain_points'

echo -e "\n\n"

# Scenario 5: Vague input - tests extraction capabilities
echo "📝 Scenario 5: Vague Input - Sales Rep Notes"
echo "-----------------------------------------"
curl -X POST "${BASE_URL}?provider=${PROVIDER}&model=${MODEL}" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Had coffee with Sarah from marketing. She mentioned they are unhappy with current analytics platform. Something about reports being slow? Team frustrated. Might have budget next quarter.",
    "source": "informal_meeting"
  }' | jq -r '.value_proposition.headline, .extracted_data.confidence_score, .self_check.hallucination_risk'

echo -e "\n\n"

# Scenario 6: Multi-stakeholder complex deal
echo "📝 Scenario 6: Complex Deal - Digital Transformation"
echo "-----------------------------------------"
curl -X POST "${BASE_URL}?provider=${PROVIDER}&model=${MODEL}" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Meeting with CEO, CFO, and CIO of mid-market manufacturer. CEO wants to modernize operations to compete with digital-native competitors. CFO concerned about $2M invested in legacy ERP that is barely used - only 30% adoption rate. CIO frustrated that integration between systems takes months and requires expensive consultants. They have 200 employees still using Excel for inventory management. Production delays cost them $50K per incident, happening 2-3 times per month. Board is pushing for digital transformation roadmap by end of year.",
    "source": "executive_briefing"
  }' | jq

echo -e "\n\n"

# Scenario 7: ROI-focused with metrics
echo "📝 Scenario 7: ROI-Focused - Sales Operations"
echo "-----------------------------------------"
curl -X POST "${BASE_URL}?provider=${PROVIDER}&model=${MODEL}" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "VP of Sales Operations shared metrics: sales cycle is 120 days (industry average is 60), reps spend only 35% of time actually selling (rest is admin), deal win rate is 18% (should be 30%+), and they are missing quota by 40% this year. Sales team of 25 reps, each costing $150K fully loaded. Lost 3 top performers last quarter due to frustration with tools.",
    "source": "sales_call"
  }' | jq -r '.value_proposition.headline, .value_proposition.quantified_value, .value_proposition.call_to_action'

echo -e "\n\n"

# Scenario 8: PII detection test
echo "📝 Scenario 8: PII Detection - Email with Sensitive Data"
echo "-----------------------------------------"
curl -X POST "${BASE_URL}?provider=${PROVIDER}&model=${MODEL}" \
  -H "Content-Type: application/json" \
  -d '{
    "content": "Follow-up from John Smith (john.smith@acmecorp.com, 555-123-4567). His SSN is 123-45-6789 for the contract. Credit card 4532-1234-5678-9010. Mentioned they need better customer data protection - current system exposed 10,000 customer records last month. Compliance team is panicking.",
    "source": "email"
  }' | jq -r '.normalized_input.has_pii, .normalized_input.detected_pii, .normalized_input.cleaned_content, .value_proposition.headline'

echo -e "\n\n"

echo "========================================="
echo "✅ All scenarios completed!"
echo "========================================="
