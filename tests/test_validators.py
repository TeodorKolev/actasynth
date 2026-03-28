"""Tests for response_validator — ensures padding is applied and logged correctly"""

import pytest
from unittest.mock import patch
from app.agents.response_validator import (
    validate_extracted_data,
    validate_self_check,
    validate_value_prop,
)


class TestValidateExtractedData:
    def test_passes_through_valid_data(self):
        data = {
            "problem_statement": "Manual process",
            "desired_outcome": "Automation",
            "pain_points": ["slow", "error-prone"],
            "value_drivers": ["efficiency"],
            "confidence_score": 0.9,
        }
        result = validate_extracted_data(data.copy())
        assert result["pain_points"] == ["slow", "error-prone"]
        assert result["problem_statement"] == "Manual process"

    def test_pads_missing_pain_points(self):
        data = {"problem_statement": "p", "desired_outcome": "d", "pain_points": [], "value_drivers": ["v"], "confidence_score": 0.5}
        with patch("app.agents.response_validator.logger") as mock_logger:
            result = validate_extracted_data(data)
            mock_logger.warning.assert_any_call("extraction_missing_field", field="pain_points")
        assert result["pain_points"] == ["Not specified in input"]

    def test_pads_missing_value_drivers(self):
        data = {"problem_statement": "p", "desired_outcome": "d", "pain_points": ["x"], "value_drivers": [], "confidence_score": 0.5}
        with patch("app.agents.response_validator.logger") as mock_logger:
            result = validate_extracted_data(data)
            mock_logger.warning.assert_any_call("extraction_missing_field", field="value_drivers")
        assert result["value_drivers"] == ["Not specified in input"]

    def test_pads_missing_problem_statement(self):
        data = {"problem_statement": "", "desired_outcome": "d", "pain_points": ["x"], "value_drivers": ["v"], "confidence_score": 0.5}
        with patch("app.agents.response_validator.logger") as mock_logger:
            result = validate_extracted_data(data)
            mock_logger.warning.assert_any_call("extraction_missing_field", field="problem_statement")
        assert result["problem_statement"] == "Customer problem not clearly specified"

    def test_defaults_confidence_score(self):
        data = {"problem_statement": "p", "desired_outcome": "d", "pain_points": ["x"], "value_drivers": ["v"]}
        result = validate_extracted_data(data)
        assert result["confidence_score"] == 0.5


class TestValidateSelfCheck:
    def test_passes_through_valid_data(self):
        data = {"verifications": [], "overall_accuracy": 0.9, "hallucination_risk": 0.1, "approved": True}
        result = validate_self_check(data.copy())
        assert result["approved"] is True
        assert result["overall_accuracy"] == 0.9

    def test_rejects_when_approved_missing(self):
        data = {"verifications": [], "overall_accuracy": 0.5, "hallucination_risk": 0.5}
        result = validate_self_check(data)
        assert result["approved"] is False

    def test_adds_rejection_reason_when_not_approved(self):
        data = {"verifications": [], "overall_accuracy": 0.3, "hallucination_risk": 0.7, "approved": False}
        result = validate_self_check(data)
        assert result["rejection_reason"] is not None


class TestValidateValueProp:
    def test_passes_through_valid_data(self):
        data = {
            "headline": "Save time",
            "problem": "Manual work",
            "solution": "Automate",
            "differentiation": "AI-powered",
            "call_to_action": "Book demo",
            "key_talking_points": ["p1", "p2", "p3"],
        }
        result = validate_value_prop(data.copy())
        assert result["key_talking_points"] == ["p1", "p2", "p3"]

    def test_pads_talking_points_below_minimum(self):
        data = {
            "headline": "h", "problem": "p", "solution": "s",
            "differentiation": "d", "call_to_action": "c",
            "key_talking_points": ["only one"],
        }
        with patch("app.agents.response_validator.logger") as mock_logger:
            result = validate_value_prop(data)
            mock_logger.warning.assert_called_once_with(
                "value_prop_padding_talking_points", count=1
            )
        assert len(result["key_talking_points"]) == 3

    def test_trims_talking_points_above_maximum(self):
        data = {
            "headline": "h", "problem": "p", "solution": "s",
            "differentiation": "d", "call_to_action": "c",
            "key_talking_points": ["1", "2", "3", "4", "5", "6"],
        }
        result = validate_value_prop(data)
        assert len(result["key_talking_points"]) == 5

    def test_pads_missing_required_field(self):
        data = {
            "headline": "", "problem": "p", "solution": "s",
            "differentiation": "d", "call_to_action": "c",
            "key_talking_points": ["1", "2", "3"],
        }
        with patch("app.agents.response_validator.logger") as mock_logger:
            result = validate_value_prop(data)
            mock_logger.warning.assert_any_call("value_prop_missing_field", field="headline")
        assert result["headline"] == "Headline not specified"
