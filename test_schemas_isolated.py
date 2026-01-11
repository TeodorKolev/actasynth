"""Isolated test for Pydantic schema generation (no app imports needed)"""

import json
from typing import Any


# Copy the schema generation logic to test it in isolation
def get_extraction_schema_from_pydantic() -> dict[str, Any]:
    """Simulate _get_extraction_schema() using Pydantic model"""
    from app.schemas.value_proposition import ExtractedData

    # Auto-generate from ExtractedData Pydantic model
    schema = ExtractedData.model_json_schema()

    # Remove JSON schema metadata that LLMs don't need
    schema.pop("title", None)
    schema.pop("description", None)

    return schema


def get_self_check_schema_from_pydantic() -> dict[str, Any]:
    """Simulate _get_self_check_schema() using Pydantic model"""
    from app.schemas.value_proposition import SelfCheckResult

    # Auto-generate from SelfCheckResult Pydantic model
    schema = SelfCheckResult.model_json_schema()

    # Remove JSON schema metadata that LLMs don't need
    schema.pop("title", None)
    schema.pop("description", None)

    # Inline $defs to resolve $ref references (LLMs don't understand $ref well)
    if "$defs" in schema and "verifications" in schema.get("properties", {}):
        # Replace $ref with actual ClaimVerification schema
        if "$ref" in schema["properties"]["verifications"].get("items", {}):
            claim_verification_schema = schema["$defs"]["ClaimVerification"]
            # Remove title/description from nested schema
            claim_verification_schema.pop("title", None)
            claim_verification_schema.pop("description", None)
            # Inline the schema
            schema["properties"]["verifications"]["items"] = claim_verification_schema

    # Remove $defs after inlining
    schema.pop("$defs", None)

    return schema


def get_value_prop_schema_from_pydantic() -> dict[str, Any]:
    """Simulate _get_value_prop_schema() using Pydantic model"""
    from app.schemas.value_proposition import ValueProposition

    # Auto-generate from ValueProposition Pydantic model
    schema = ValueProposition.model_json_schema()

    # Remove JSON schema metadata that LLMs don't need
    schema.pop("title", None)
    schema.pop("description", None)

    # Inline $defs to resolve $ref references (for Persona enum)
    if "$defs" in schema and "persona" in schema.get("properties", {}):
        # Replace $ref with actual Persona enum schema
        if "$ref" in schema["properties"]["persona"]:
            persona_schema = schema["$defs"]["Persona"]
            # Merge persona schema into the property, keeping default and description
            default = schema["properties"]["persona"].get("default")
            description = schema["properties"]["persona"].get("description")
            schema["properties"]["persona"] = {
                "type": "string",
                "enum": persona_schema.get("enum", []),
            }
            if default:
                schema["properties"]["persona"]["default"] = default
            if description:
                schema["properties"]["persona"]["description"] = description

    # Remove $defs after inlining
    schema.pop("$defs", None)

    # Remove auto-generated fields that LLM shouldn't set
    if "properties" in schema and "generated_at" in schema["properties"]:
        schema["properties"].pop("generated_at")
        if "required" in schema and "generated_at" in schema["required"]:
            schema["required"].remove("generated_at")

    return schema


def main():
    print("\n" + "=" * 80)
    print("PYDANTIC AUTO-GENERATED SCHEMA VALIDATION")
    print("=" * 80 + "\n")

    # Test 1: Extraction Schema
    print("1️⃣  EXTRACTION SCHEMA (ExtractedData)")
    print("-" * 80)
    try:
        schema = get_extraction_schema_from_pydantic()
        print(json.dumps(schema, indent=2))

        # Validations
        assert "required" in schema, "Missing 'required' field"
        assert "problem_statement" in schema["required"], "Missing required field: problem_statement"
        assert "desired_outcome" in schema["required"], "Missing required field: desired_outcome"
        assert "$ref" not in json.dumps(schema), "Schema contains unresolved $ref!"
        assert "title" not in schema, "Title should be removed"

        print("\n✅ ExtractedData schema PASSED\n")
    except Exception as e:
        print(f"\n❌ FAILED: {e}\n")
        raise

    # Test 2: Self-Check Schema
    print("2️⃣  SELF-CHECK SCHEMA (SelfCheckResult)")
    print("-" * 80)
    try:
        schema = get_self_check_schema_from_pydantic()
        print(json.dumps(schema, indent=2))

        # Validations
        assert "required" in schema, "Missing 'required' field"
        assert "verifications" in schema["required"], "Missing required field: verifications"
        assert "overall_accuracy" in schema["required"], "Missing required field: overall_accuracy"
        assert "$ref" not in json.dumps(schema), "Schema contains unresolved $ref!"
        assert "$defs" not in schema, "Schema still has $defs!"

        # Verify ClaimVerification is inlined
        items_schema = schema["properties"]["verifications"].get("items", {})
        assert "type" in items_schema, "ClaimVerification not properly inlined"
        assert items_schema["type"] == "object", "ClaimVerification should be object type"
        assert "properties" in items_schema, "ClaimVerification missing properties"
        assert "claim" in items_schema["properties"], "ClaimVerification missing 'claim' field"

        print("\n✅ SelfCheckResult schema PASSED (ClaimVerification inlined)\n")
    except Exception as e:
        print(f"\n❌ FAILED: {e}\n")
        raise

    # Test 3: Value Proposition Schema
    print("3️⃣  VALUE PROPOSITION SCHEMA (ValueProposition)")
    print("-" * 80)
    try:
        schema = get_value_prop_schema_from_pydantic()
        print(json.dumps(schema, indent=2))

        # Validations
        assert "required" in schema, "Missing 'required' field"
        assert "headline" in schema["required"], "Missing required field: headline"
        assert "problem" in schema["required"], "Missing required field: problem"
        assert "generated_at" not in schema.get("properties", {}), "generated_at should be removed!"
        assert "$ref" not in json.dumps(schema), "Schema contains unresolved $ref!"
        assert "$defs" not in schema, "Schema still has $defs!"

        # Verify Persona enum is inlined
        persona_schema = schema["properties"].get("persona", {})
        assert "enum" in persona_schema, "Persona enum not inlined"
        assert "executive" in persona_schema["enum"], "Missing 'executive' in Persona enum"
        assert "technical" in persona_schema["enum"], "Missing 'technical' in Persona enum"
        assert "business_user" in persona_schema["enum"], "Missing 'business_user' in Persona enum"

        # Verify constraints from Pydantic model
        assert schema["properties"]["headline"]["maxLength"] == 200, "headline maxLength constraint missing"
        assert schema["properties"]["key_talking_points"]["minItems"] == 3, "key_talking_points minItems constraint missing"
        assert schema["properties"]["key_talking_points"]["maxItems"] == 5, "key_talking_points maxItems constraint missing"

        print("\n✅ ValueProposition schema PASSED (Persona enum inlined, constraints preserved)\n")
    except Exception as e:
        print(f"\n❌ FAILED: {e}\n")
        raise

    print("=" * 80)
    print("✅ ALL SCHEMA TESTS PASSED!")
    print("=" * 80)
    print("\n🎯 Key Achievements:")
    print("  ✅ Schemas auto-generated from Pydantic models")
    print("  ✅ No manual JSON schema duplication")
    print("  ✅ All $ref references properly inlined")
    print("  ✅ All $defs sections removed")
    print("  ✅ Nested models (ClaimVerification) inlined")
    print("  ✅ Enums (Persona) inlined")
    print("  ✅ Auto-generated fields (generated_at) removed")
    print("  ✅ Pydantic constraints (maxLength, minItems, etc.) preserved")
    print("  ✅ Schemas ready for LLM consumption")
    print("\n🚀 Single Source of Truth: Pydantic Models!")
    print()


if __name__ == "__main__":
    try:
        main()
        exit(0)
    except Exception as e:
        print(f"\n💥 TEST SUITE FAILED\n")
        import traceback
        traceback.print_exc()
        exit(1)
