import pytest

from evaluator.ai_reviewer import (
    GeminiCodeReviewer,
    GeminiReviewError,
)


class FakeResponse:
    def __init__(self, text):
        self.text = text


class FakeModels:
    def __init__(self, response=None, error=None):
        self.response = response
        self.error = error
        self.last_request = None

    def generate_content(self, **kwargs):
        self.last_request = kwargs

        if self.error:
            raise self.error

        return self.response


class FakeClient:
    def __init__(self, response=None, error=None):
        self.models = FakeModels(response=response, error=error)


def test_reviewer_returns_gemini_feedback():
    client = FakeClient(
        response=FakeResponse("Your function is readable.")
    )

    reviewer = GeminiCodeReviewer(
        model="test-model",
        client=client,
    )

    result = reviewer.review("def add(a, b):\n    return a + b")

    assert result == "Your function is readable."
    assert client.models.last_request["model"] == "test-model"


def test_reviewer_removes_extra_whitespace():
    client = FakeClient(
        response=FakeResponse("  Good code review.  ")
    )

    reviewer = GeminiCodeReviewer(client=client)

    result = reviewer.review("print('hello')")

    assert result == "Good code review."


def test_empty_source_code_is_rejected():
    reviewer = GeminiCodeReviewer(client=FakeClient())

    with pytest.raises(ValueError, match="empty"):
        reviewer.review("   ")


def test_non_string_source_code_is_rejected():
    reviewer = GeminiCodeReviewer(client=FakeClient())

    with pytest.raises(TypeError, match="string"):
        reviewer.review(None)


def test_oversized_source_code_is_rejected():
    reviewer = GeminiCodeReviewer(client=FakeClient())

    with pytest.raises(ValueError, match="20,000"):
        reviewer.review("x" * 20_001)


def test_api_error_is_wrapped():
    client = FakeClient(error=RuntimeError("Simulated API failure"))
    reviewer = GeminiCodeReviewer(client=client)

    with pytest.raises(
        GeminiReviewError,
        match="request failed",
    ):
        reviewer.review("print('hello')")


def test_empty_gemini_response_is_rejected():
    client = FakeClient(response=FakeResponse(""))
    reviewer = GeminiCodeReviewer(client=client)

    with pytest.raises(GeminiReviewError, match="empty review"):
        reviewer.review("print('hello')")
