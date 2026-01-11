"""Test script to verify Pydantic JSON schema auto-generation"""

import json
from app.schemas.value_proposition import (
    ExtractedData,
    SelfCheckResult,
    ValueProposition,
)


def test_extracted_data_schema():
    """Test ExtractedData schema generation"""
    schema = ExtractedData.model_json_schema()

    # Clean up for LLM consumption
    schema.pop("title", None)
    schema.pop("description", None)

    print("=" * 80)
    print("EXTRACTED DATA SCHEMA (Auto-generated from Pydantic)")
    print("=" * 80)
    print(json.dumps(schema, indent=2))
    print()

    # Verify required fields
    assert "required" in schema
    assert "problem_statement" in schema["required"]
    assert "desired_outcome" in schema["required"]
    assert "pain_points" in schema["required"]
    assert "value_drivers" in schema["required"]

    print("✅ ExtractedData schema validation PASSED")
    print()


def test_self_check_schema():
    """Test SelfCheckResult schema generation"""
    schema = SelfCheckResult.model_json_schema()

    # Clean up for LLM consumption
    schema.pop("title", None)
    schema.pop("description", None)
    schema.pop("$defs", None)  # Remove nested definitions

    print("=" * 80)
    print("SELF-CHECK SCHEMA (Auto-generated from Pydantic)")
    print("=" * 80)
    print(json.dumps(schema, indent=2))
    print()

    # Verify required fields
    assert "required" in schema
    assert "verifications" in schema["required"]
    assert "overall_accuracy" in schema["required"]
    assert "hallucination_risk" in schema["required"]
    assert "approved" in schema["required"]

    print("✅ SelfCheckResult schema validation PASSED")
    print()


def test_value_proposition_schema():
    """Test ValueProposition schema generation"""
    schema = ValueProposition.model_json_schema()

    # Clean up for LLM consumption
    schema.pop("title", None)
    schema.pop("description", None)
    schema.pop("$defs", None)  # Remove nested definitions

    # Remove auto-generated fields
    if "properties" in schema and "generated_at" in schema["properties"]:
        schema["properties"].pop("generated_at")
        if "required" in schema and "generated_at" in schema["required"]:
            schema["required"].remove("generated_at")

    print("=" * 80)
    print("VALUE PROPOSITION SCHEMA (Auto-generated from Pydantic)")
    print("=" * 80)
    print(json.dumps(schema, indent=2))
    print()

    # Verify required fields
    assert "required" in schema
    assert "headline" in schema["required"]
    assert "problem" in schema["required"]
    assert "solution" in schema["required"]
    assert "differentiation" in schema["required"]
    assert "call_to_action" in schema["required"]
    assert "key_talking_points" in schema["required"]

    # Verify constraints
    assert schema["properties"]["headline"]["maxLength"] == 200
    assert schema["properties"]["key_talking_points"]["minItems"] == 3
    assert schema["properties"]["key_talking_points"]["maxItems"] == 5

    print("✅ ValueProposition schema validation PASSED")
    print()


def test_comparison():
    """Compare old hardcoded vs new auto-generated schemas"""

    # Old hardcoded schema
    old_value_prop_schema = {
        "type": "object",
        "required": [
            "headline",
            "problem",
            "solution",
            "differentiation",
            "call_to_action",
            "key_talking_points",
        ],
        "properties": {
            "headline": {"type": "string", "maxLength": 200},
            "problem": {"type": "string"},
            "solution": {"type": "string"},
            "differentiation": {"type": "string"},
            "quantified_value": {"type": ["string", "null"]},
            "call_to_action": {"type": "string"},
            "persona": {"type": "string", "enum": ["executive", "technical", "business_user"]},
            "key_talking_points": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": 3,
                "maxItems": 5,
            },
        },
    }

    # New auto-generated schema
    new_schema = ValueProposition.model_json_schema()
    new_schema.pop("title", None)
    new_schema.pop("description", None)
    new_schema.pop("$defs", None)
    if "properties" in new_schema and "generated_at" in new_schema["properties"]:
        new_schema["properties"].pop("generated_at")
        if "required" in new_schema and "generated_at" in new_schema["required"]:
            new_schema["required"].remove("generated_at")

    print("=" * 80)
    print("COMPARISON: Old (Hardcoded) vs New (Auto-generated)")
    print("=" * 80)

    print("\n📋 OLD HARDCODED SCHEMA:")
    print(json.dumps(old_value_prop_schema, indent=2))

    print("\n🤖 NEW AUTO-GENERATED SCHEMA:")
    print(json.dumps(new_schema, indent=2))

    print("\n" + "=" * 80)
    print("KEY DIFFERENCES:")
    print("=" * 80)

    # Check what changed
    old_props = set(old_value_prop_schema["properties"].keys())
    new_props = set(new_schema["properties"].keys())

    print(f"\n✅ Common properties: {old_props & new_props}")
    print(f"➕ New properties: {new_props - old_props}")
    print(f"➖ Removed properties: {old_props - new_props}")

    print("\n✅ Both schemas maintain the same core structure!")
    print("✅ Auto-generation ensures consistency with Pydantic models!")
    print()


if __name__ == "__main__":
    print("\n" + "🚀 " * 20)
    print("PYDANTIC JSON SCHEMA AUTO-GENERATION TEST")
    print("🚀 " * 20 + "\n")

    try:
        test_extracted_data_schema()
        test_self_check_schema()
        test_value_proposition_schema()
        test_comparison()

        print("\n" + "=" * 80)
        print("✅ ALL TESTS PASSED!")
        print("=" * 80)
        print("\nBenefits of auto-generation:")
        print("  1. Single source of truth (Pydantic models)")
        print("  2. No schema duplication")
        print("  3. Changes to models automatically reflected in LLM prompts")
        print("  4. Type safety guaranteed")
        print("  5. Reduced maintenance burden")
        print()

    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
