"""Validation and sanitization of LLM responses to ensure schema compliance"""

from typing import Any


def validate_extracted_data(data: dict[str, Any]) -> dict[str, Any]:
    """
    Validate and fix ExtractedData to ensure Pydantic schema compliance.

    Ensures all required list fields have at least the minimum number of items.
    """
    # Ensure pain_points has at least 1 item
    if not data.get("pain_points") or len(data["pain_points"]) == 0:
        data["pain_points"] = ["Not specified in input"]

    # Ensure value_drivers has at least 1 item
    if not data.get("value_drivers") or len(data["value_drivers"]) == 0:
        data["value_drivers"] = ["Not specified in input"]

    # Ensure stakeholders is a list (even if empty)
    if data.get("stakeholders") is None:
        data["stakeholders"] = []

    # Ensure confidence_score exists and is valid
    if "confidence_score" not in data or data["confidence_score"] is None:
        data["confidence_score"] = 0.5

    # Ensure required string fields are not empty
    if not data.get("problem_statement"):
        data["problem_statement"] = "Customer problem not clearly specified"

    if not data.get("desired_outcome"):
        data["desired_outcome"] = "Desired outcome not specified"

    return data


def validate_self_check(data: dict[str, Any]) -> dict[str, Any]:
    """
    Validate and fix SelfCheckResult to ensure Pydantic schema compliance.
    """
    # Ensure verifications list exists (can be empty)
    if "verifications" not in data:
        data["verifications"] = []

    # Ensure required fields exist
    if "overall_accuracy" not in data or data["overall_accuracy"] is None:
        data["overall_accuracy"] = 0.5

    if "hallucination_risk" not in data or data["hallucination_risk"] is None:
        data["hallucination_risk"] = 0.5

    if "approved" not in data or data["approved"] is None:
        # Conservative: reject if we're not sure
        data["approved"] = False

    # Ensure rejection_reason has meaningful value when not approved
    if not data.get("approved"):
        if not data.get("rejection_reason") or data["rejection_reason"] is None:
            data["rejection_reason"] = "Self-check did not approve extraction"

    return data


def validate_value_prop(data: dict[str, Any]) -> dict[str, Any]:
    """
    Validate and fix ValueProposition to ensure Pydantic schema compliance.
    """
    # Ensure key_talking_points has 3-5 items
    talking_points = data.get("key_talking_points", [])

    if len(talking_points) < 3:
        # Pad with generic points
        while len(talking_points) < 3:
            talking_points.append(f"Additional value point {len(talking_points) + 1}")
        data["key_talking_points"] = talking_points
    elif len(talking_points) > 5:
        # Trim to 5
        data["key_talking_points"] = talking_points[:5]

    # Ensure all required string fields exist
    required_fields = ["headline", "problem", "solution", "differentiation", "call_to_action"]

    for field in required_fields:
        if not data.get(field) or not data[field].strip():
            data[field] = f"{field.replace('_', ' ').title()} not specified"

    return data
