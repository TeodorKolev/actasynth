# Pydantic Schema Auto-Generation Refactor

## Summary

Refactored the `WorkflowExecutor` class to use **Pydantic's automatic JSON schema generation** instead of manually duplicating schemas. This eliminates code duplication and ensures a single source of truth.

## What Changed

### Before (Hardcoded JSON Schemas)

```python
def _get_value_prop_schema(self) -> dict[str, Any]:
    """Get JSON schema for value proposition"""
    return {
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
            # ... etc (50+ lines of duplicate schema definition)
        },
    }
```

### After (Auto-Generated from Pydantic)

```python
def _get_value_prop_schema(self) -> dict[str, Any]:
    """Get JSON schema for value proposition - auto-generated from Pydantic model"""
    # Auto-generate from ValueProposition Pydantic model
    schema = ValueProposition.model_json_schema()

    # Clean up for LLM consumption
    schema.pop("title", None)
    schema.pop("description", None)

    # Inline $defs to resolve $ref references (for Persona enum)
    if "$defs" in schema and "persona" in schema.get("properties", {}):
        if "$ref" in schema["properties"]["persona"]:
            persona_schema = schema["$defs"]["Persona"]
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

    schema.pop("$defs", None)

    # Remove auto-generated fields that LLM shouldn't set
    if "properties" in schema and "generated_at" in schema["properties"]:
        schema["properties"].pop("generated_at")
        if "required" in schema and "generated_at" in schema["required"]:
            schema["required"].remove("generated_at")

    return schema
```

## Modified Files

### 1. `app/agents/workflow_executor.py`

**Updated Methods:**

- `_get_extraction_schema()` - Now uses `ExtractedData.model_json_schema()`
- `_get_self_check_schema()` - Now uses `SelfCheckResult.model_json_schema()` with ClaimVerification inlining
- `_get_value_prop_schema()` - Now uses `ValueProposition.model_json_schema()` with Persona enum inlining

**Note:** `_get_ingest_schema()` remains custom because its LLM response format differs from the final `NormalizedInput` structure.

## Benefits

### ✅ Single Source of Truth
- Pydantic models in `app/schemas/value_proposition.py` are now the **only** place schemas are defined
- No more maintaining duplicate JSON schema definitions

### ✅ Automatic Synchronization
- Changes to Pydantic models automatically reflect in LLM prompts
- No risk of schema drift between validation and LLM instructions

### ✅ Type Safety
- Leverages Pydantic's validation automatically
- Constraints (maxLength, minItems, etc.) are preserved

### ✅ Reduced Maintenance
- ~100+ lines of hardcoded JSON removed
- Future schema changes only require updating the Pydantic model

### ✅ Better Developer Experience
- Clear separation: Pydantic models define structure, workflow executor uses them
- Auto-completion and type hints work correctly

## Technical Details

### Schema Cleanup for LLM Consumption

The auto-generated schemas include metadata that LLMs don't need:

1. **Remove `title` and `description`** - Already in field descriptions
2. **Inline `$defs`** - LLMs don't understand JSON Schema `$ref` well
3. **Remove auto-generated fields** - Fields like `generated_at` that have defaults shouldn't be set by the LLM

### Nested Model Inlining

Pydantic generates schemas with `$defs` for nested models and enums:

```json
{
  "properties": {
    "persona": {"$ref": "#/$defs/Persona"}
  },
  "$defs": {
    "Persona": {
      "type": "string",
      "enum": ["executive", "technical", "business_user"]
    }
  }
}
```

We **inline these references** for better LLM comprehension:

```json
{
  "properties": {
    "persona": {
      "type": "string",
      "enum": ["executive", "technical", "business_user"],
      "default": "executive"
    }
  }
}
```

## Testing

Created comprehensive test suite to verify:

- ✅ All schemas auto-generate correctly
- ✅ No `$ref` references remain (fully inlined)
- ✅ No `$defs` sections remain
- ✅ Nested models (ClaimVerification) are inlined
- ✅ Enums (Persona) are inlined
- ✅ Auto-generated fields (generated_at) are removed
- ✅ Pydantic constraints (maxLength, minItems) are preserved

**Test Files:**
- `test_schema_generation.py` - Basic Pydantic schema generation tests
- `test_schemas_isolated.py` - Comprehensive validation with inlining logic

Run tests:
```bash
python test_schemas_isolated.py
```

## Migration Guide

### For Future Schema Changes

**Old Way (DON'T DO THIS):**
1. Update Pydantic model in `app/schemas/value_proposition.py`
2. Update hardcoded JSON schema in `app/agents/workflow_executor.py`
3. Hope they stay in sync

**New Way (DO THIS):**
1. Update Pydantic model in `app/schemas/value_proposition.py`
2. Done! Schema automatically updates everywhere.

### Example: Adding a New Field

**Pydantic Model:**
```python
class ValueProposition(BaseModel):
    headline: str = Field(..., max_length=200)
    # ... existing fields ...
    competitive_advantage: Optional[str] = Field(None, description="Key competitive differentiator")  # NEW
```

**Result:** LLM automatically receives updated schema with the new field. No code changes needed in `workflow_executor.py`.

## Edge Cases

### Why is `_get_ingest_schema()` still custom?

The ingest step returns a different format than `NormalizedInput`:

**LLM Response Format:**
```json
{
  "language": "en",
  "pii_detected": true,
  "redacted_text": "...",
  "word_count": 150
}
```

**NormalizedInput Model:**
```python
class NormalizedInput(BaseModel):
    content: str                      # Original content
    language: Language
    detected_pii: list[PIIDetection]  # Full PII objects
    has_pii: bool
    cleaned_content: str              # Redacted version
    word_count: int
    processed_at: datetime
```

The LLM response is **transformed** in `_parse_ingest_response()` into the final `NormalizedInput` object. Therefore, the schema must match the LLM's response format, not the final parsed structure.

## Future Improvements

1. **Consider using Pydantic's `mode='serialization'`** to generate schemas optimized for LLMs
2. **Create a helper utility** to handle $ref inlining generically
3. **Refactor ingest step** to align LLM response format with NormalizedInput model

## Conclusion

This refactor eliminates ~100+ lines of duplicate code and establishes Pydantic models as the single source of truth for all schemas in the application. Future maintenance is simplified, and the risk of schema drift is eliminated.

---

**Author:** Claude Code
**Date:** 2026-01-11
**Files Modified:** 1
**Lines Removed:** ~100+
**Lines Added:** ~60
**Net Benefit:** Single source of truth, automatic synchronization
