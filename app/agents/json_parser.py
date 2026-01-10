"""Robust JSON parsing utilities for LLM responses"""

import json
import re
from typing import Any


def find_json_objects_helper(text: str) -> list[str]:
    """Find all potential JSON objects in text by tracking brace depth"""
    objects = []
    depth = 0
    start = -1

    for i, char in enumerate(text):
        if char == '{':
            if depth == 0:
                start = i
            depth += 1
        elif char == '}':
            depth -= 1
            if depth == 0 and start != -1:
                objects.append(text[start:i+1])
                start = -1

    return objects


def extract_json_from_response(content: str) -> dict[str, Any]:
    """
    Extract and parse JSON from LLM response, handling various formats.

    Tries multiple strategies:
    1. Direct JSON parsing
    2. Extract from markdown code blocks
    3. Find JSON object in text
    4. Clean and retry

    Args:
        content: Raw LLM response

    Returns:
        Parsed JSON dictionary

    Raises:
        ValueError: If no valid JSON can be extracted
    """
    # Strategy 1: Try direct parsing
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        pass

    # Strategy 2: Extract from markdown code blocks
    # Use non-greedy match and handle multiline properly
    code_block_pattern = r'```(?:json)?\s*(\{[\s\S]*?\})\s*```'
    match = re.search(code_block_pattern, content, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Also try without closing backticks (sometimes incomplete)
    code_block_start_pattern = r'```(?:json)?\s*(\{[\s\S]*)'
    match = re.search(code_block_start_pattern, content)
    if match:
        json_candidate = match.group(1).strip()
        # Find the end of the JSON object
        for i, obj in enumerate(find_json_objects_helper(json_candidate)):
            try:
                return json.loads(obj)
            except json.JSONDecodeError:
                continue

    # Strategy 3: Find largest JSON object (most likely to be complete)
    potential_jsons = find_json_objects_helper(content)
    # Try from longest to shortest (longest is likely the complete response)
    for json_str in sorted(potential_jsons, key=len, reverse=True):
        try:
            parsed = json.loads(json_str)
            # Prefer objects with more keys (more complete)
            if isinstance(parsed, dict) and len(parsed) > 2:
                return parsed
        except json.JSONDecodeError:
            continue

    # If nothing good found, try the first valid one
    for json_str in potential_jsons:
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            continue

    # Strategy 4: Try to clean common issues
    # Remove markdown formatting
    cleaned = re.sub(r'```(?:json)?', '', content)
    cleaned = cleaned.strip()

    # Try to find anything that looks like JSON
    if cleaned.startswith('{') and cleaned.endswith('}'):
        try:
            # Replace common issues
            cleaned = cleaned.replace('\n', ' ')
            cleaned = re.sub(r',(\s*[}\]])', r'\1', cleaned)  # Remove trailing commas
            return json.loads(cleaned)
        except json.JSONDecodeError:
            pass

    # Strategy 5: Extract largest {...} block
    all_json_like = re.findall(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', content, re.DOTALL)
    if all_json_like:
        # Try the longest match
        longest = max(all_json_like, key=len)
        try:
            return json.loads(longest)
        except json.JSONDecodeError:
            pass

    # Give up
    raise ValueError(
        f"Could not parse JSON from response. "
        f"First 500 chars: {content[:500]}"
    )
