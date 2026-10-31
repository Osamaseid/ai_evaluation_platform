"""Tests for structured Gemini code reviewer, retry handling, and prompt construction."""

import json
from typing import Any
import pytest

from evaluator.ai_reviewer import (
    CodeObservation,
    CodeReviewFeedback,
    GeminiCodeReviewer,
    GeminiConfigurationError,
    GeminiReviewError,
    IssueSeverity,
    ReviewCategory,
    _is_transient_error,
    _mask_secret,
)
from evaluator.assignment import AssignmentDefinition, TestCaseDefinition
from evaluator.grading import TestCaseResult


class MockApiResponse:
    def __init__(self, text: str, parsed: Any = None):
        self.text = text
        self.parsed = parsed


class MockModelsService:
    def __init__(self, responses=None, errors=None):
        self.responses = list(responses or [])
        self.errors = list(errors or [])
        self.call_count = 0
        self.last_call_kwargs = None

    def generate_content(self, **kwargs):
        self.last_call_kwargs = kwargs
        self.call_count += 1

        if self.errors:
            err = self.errors.pop(0)
            raise err

        if self.responses:
            return self.responses.pop(0)

        return MockApiResponse(text="{}")


class MockGenAIClient:
    def __init__(self, responses=None, errors=None):
        self.models = MockModelsService(responses=responses, errors=errors)


SAMPLE_FEEDBACK_DICT = {
    "summary": "The solution is clean and demonstrates good understanding of recursion.",
    "strengths": ["Well-named functions", "Correct base case"],
    "observations": [
        {
            "category": "edge_case",
            "severity": "warning",
            "title": "Unchecked Negative Inputs",
            "explanation": "Recursion does not guard against negative integers causing infinite recursion.",
            "code_evidence": "def factorial(n):",
            "line_number": 1,
            "suggested_fix": "Add `if n < 0: raise ValueError(...)`.",
        },
        {
            "category": "readability",
            "severity": "info",
            "title": "Missing Docstring",
            "explanation": "Function should include a docstring explaining arguments and return value.",
            "code_evidence": None,
            "line_number": 1,
            "suggested_fix": "Add PEP 257 docstring.",
        },
    ],
    "pedagogical_guidance": "Great start! Adding input validation will make your function production-grade.",
    "untrusted_code_detected_notes": None,
}


class TestSecretMasking:
    def test_mask_empty_and_short(self):
        assert _mask_secret(None) == "<none>"
        assert _mask_secret("") == "<none>"
        assert _mask_secret("12345") == "***"

    def test_mask_standard_api_key(self):
        key = "AIzaSyD-1234567890abcdefghijklmnopqrstuv"
        masked = _mask_secret(key)
        assert masked.startswith("AIza")
        assert masked.endswith("stuv")
        assert "1234567890" not in masked


class TestTransientErrorDetection:
    def test_identifies_transient_failures(self):
        assert _is_transient_error(RuntimeError("503 Server Unavailable")) is True
        assert _is_transient_error(RuntimeError("Resource_Exhausted: 429 quota")) is True
        assert _is_transient_error(RuntimeError("ConnectError: connection reset")) is True

    def test_identifies_permanent_failures(self):
        assert _is_transient_error(ValueError("400 Bad Request: Invalid JSON")) is False
        assert _is_transient_error(PermissionError("401 Unauthorized: Invalid API key")) is False


class TestStructuredCodeReview:
    @pytest.fixture
    def sample_assignment(self):
        return AssignmentDefinition(
            task_id="factorial_task",
            title="Recursive Factorial",
            test_cases=(
                TestCaseDefinition("test_zero", "0! is 1", 5, assertion="factorial(0) == 1"),
                TestCaseDefinition("test_positive", "5! is 120", 5, assertion="factorial(5) == 120"),
            ),
        )

    @pytest.fixture
    def sample_results(self):
        return (
            TestCaseResult("test_zero", True),
            TestCaseResult("test_positive", False, message="Returned 24 instead of 120"),
        )

    def test_review_structured_returns_pydantic_model(self):
        raw_json = json.dumps(SAMPLE_FEEDBACK_DICT)
        client = MockGenAIClient(responses=[MockApiResponse(text=raw_json)])
        reviewer = GeminiCodeReviewer(client=client)

        feedback = reviewer.review_structured("def factorial(n): return 1 if n <= 1 else n * factorial(n - 1)")

        assert isinstance(feedback, CodeReviewFeedback)
        assert feedback.summary.startswith("The solution is clean")
        assert len(feedback.observations) == 2
        assert feedback.observations[0].category is ReviewCategory.EDGE_CASE
        assert feedback.observations[0].severity is IssueSeverity.WARNING
        assert feedback.observations[0].line_number == 1
        assert "negative integers" in feedback.observations[0].explanation

    def test_assignment_and_verified_tests_injected_in_prompt(self, sample_assignment, sample_results):
        raw_json = json.dumps(SAMPLE_FEEDBACK_DICT)
        client = MockGenAIClient(responses=[MockApiResponse(text=raw_json)])
        reviewer = GeminiCodeReviewer(client=client)

        reviewer.review_structured(
            source_code="def factorial(n): return 1",
            assignment=sample_assignment,
            test_results=sample_results,
        )

        sent_prompt = client.models.last_call_kwargs["contents"]
        assert "<assignment_context>" in sent_prompt
        assert "factorial_task" in sent_prompt
        assert "test_zero: 0! is 1" in sent_prompt
        assert "<verified_test_results>" in sent_prompt
        assert "Test 'test_positive': FAILED" in sent_prompt
        assert "Returned 24 instead of 120" in sent_prompt
        assert "<student_source_code>" in sent_prompt

    def test_markdown_fallback_formatting(self):
        raw_json = json.dumps(SAMPLE_FEEDBACK_DICT)
        client = MockGenAIClient(responses=[MockApiResponse(text=raw_json)])
        reviewer = GeminiCodeReviewer(client=client)

        md = reviewer.review("def factorial(n): pass")

        assert "### Code Review Summary" in md
        assert "#### Observations & Improvement Opportunities" in md
        assert "[WARNING] Unchecked Negative Inputs" in md
        assert "#### Guidance for Next Steps" in md


class TestRetryAndErrorHandling:
    def test_retry_on_transient_error_succeeds_eventually(self):
        transient_503 = RuntimeError("503 UNAVAILABLE: Model overloaded")
        raw_json = json.dumps(SAMPLE_FEEDBACK_DICT)

        client = MockGenAIClient(
            errors=[transient_503, transient_503],
            responses=[MockApiResponse(text=raw_json)],
        )

        reviewer = GeminiCodeReviewer(
            client=client,
            max_retries=3,
            retry_delay=0.01,
        )

        feedback = reviewer.review_structured("def add(a, b): return a + b")

        assert client.models.call_count == 3
        assert feedback.summary.startswith("The solution is clean")

    def test_permanent_error_fails_immediately(self):
        perm_error = PermissionError("401 Unauthorized: Invalid API key")
        client = MockGenAIClient(errors=[perm_error])

        reviewer = GeminiCodeReviewer(
            client=client,
            max_retries=3,
            retry_delay=0.01,
        )

        with pytest.raises(GeminiReviewError, match="401 Unauthorized"):
            reviewer.review_structured("def add(a, b): return a + b")

        # Must not retry permanent failures
        assert client.models.call_count == 1

    def test_missing_api_key_raises_configuration_error(self, monkeypatch):
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        with pytest.raises(GeminiConfigurationError, match="GEMINI_API_KEY"):
            GeminiCodeReviewer(api_key=None, client=None)
