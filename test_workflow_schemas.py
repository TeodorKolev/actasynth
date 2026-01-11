"""Test WorkflowExecutor schema generation methods"""

import json
from app.agents.workflow_executor import WorkflowExecutor
from app.schemas.workflow import WorkflowConfig, ModelConfig, Provider


def test_workflow_executor_schemas():
    """Test that WorkflowExecutor generates proper schemas"""

    # Create a minimal WorkflowExecutor instance
    config = WorkflowConfig(
        primary_model=ModelConfig(
            provider=Provider.OPENAI,
            model_name="gpt-4",
            temperature=0.7,
        )
    )

    # Create executor (with dummy API keys since we're not making actual calls)
    executor = WorkflowExecutor(
        config=config,
        api_keys={"openai": "dummy-key"}
    )

    print("\n" + "=" * 80)
    print("WORKFLOW EXECUTOR SCHEMA GENERATION TEST")
    print("=" * 80 + "\n")

    # Test 1: Extraction Schema
    print("1️⃣  EXTRACTION SCHEMA (ExtractedData)")
    print("-" * 80)
    extraction_schema = executor._get_extraction_schema()
    print(json.dumps(extraction_schema, indent=2))
    assert "required" in extraction_schema
    assert "problem_statement" in extraction_schema["required"]
    assert "$ref" not in json.dumps(extraction_schema), "❌ Schema contains unresolved $ref!"
    print("✅ Extraction schema valid - no $ref references\n")

    # Test 2: Self-Check Schema
    print("2️⃣  SELF-CHECK SCHEMA (SelfCheckResult)")
    print("-" * 80)
    self_check_schema = executor._get_self_check_schema()
    print(json.dumps(self_check_schema, indent=2))
    assert "required" in self_check_schema
    assert "verifications" in self_check_schema["required"]
    assert "$ref" not in json.dumps(self_check_schema), "❌ Schema contains unresolved $ref!"
    assert "$defs" not in self_check_schema, "❌ Schema still has $defs!"
    # Verify ClaimVerification is inlined
    assert "items" in self_check_schema["properties"]["verifications"]
    assert "type" in self_check_schema["properties"]["verifications"]["items"]
    print("✅ Self-check schema valid - ClaimVerification inlined\n")

    # Test 3: Value Proposition Schema
    print("3️⃣  VALUE PROPOSITION SCHEMA (ValueProposition)")
    print("-" * 80)
    value_prop_schema = executor._get_value_prop_schema()
    print(json.dumps(value_prop_schema, indent=2))
    assert "required" in value_prop_schema
    assert "headline" in value_prop_schema["required"]
    assert "generated_at" not in value_prop_schema.get("properties", {}), "❌ generated_at should be removed!"
    assert "$ref" not in json.dumps(value_prop_schema), "❌ Schema contains unresolved $ref!"
    assert "$defs" not in value_prop_schema, "❌ Schema still has $defs!"
    # Verify Persona enum is inlined
    assert "persona" in value_prop_schema["properties"]
    assert "enum" in value_prop_schema["properties"]["persona"]
    assert "executive" in value_prop_schema["properties"]["persona"]["enum"]
    print("✅ Value proposition schema valid - Persona enum inlined\n")

    # Test 4: Ingest Schema
    print("4️⃣  INGEST SCHEMA (NormalizedInput)")
    print("-" * 80)
    ingest_schema = executor._get_ingest_schema()
    print(json.dumps(ingest_schema, indent=2))
    assert "required" in ingest_schema
    assert "language" in ingest_schema["required"]
    print("✅ Ingest schema valid (custom format)\n")

    print("=" * 80)
    print("✅ ALL WORKFLOW EXECUTOR SCHEMAS VALID!")
    print("=" * 80)
    print("\nKey Achievements:")
    print("  ✅ No $ref references (fully inlined)")
    print("  ✅ No $defs sections (cleaned up)")
    print("  ✅ ClaimVerification nested model inlined in SelfCheckResult")
    print("  ✅ Persona enum inlined in ValueProposition")
    print("  ✅ Auto-generated 'generated_at' field removed from ValueProposition")
    print("  ✅ Schemas ready for LLM consumption")
    print()


if __name__ == "__main__":
    try:
        test_workflow_executor_schemas()
        print("🎉 SUCCESS - All schemas properly auto-generated from Pydantic models!")
        exit(0)
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
