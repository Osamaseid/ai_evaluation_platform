import pytest

from evaluator.assignment import (
    AssignmentDefinition,
    TestCaseDefinition,
)
from evaluator.grading import TestCaseResult, grade_submission
from evaluator.runner import MockTestRunner


@pytest.fixture
def assignment():
    return AssignmentDefinition(
        task_id="python_week1",
        title="Calculator Functions",
        test_cases=(
            TestCaseDefinition("add", "Add two numbers", 5),
            TestCaseDefinition("subtract", "Subtract two numbers", 5),
        ),
    )


@pytest.fixture
def results():
    return (
        TestCaseResult("add", True),
        TestCaseResult("subtract", False),
    )


def test_mock_runner_returns_configured_results(assignment, results):
    runner = MockTestRunner(results)

    actual = runner.run(assignment, "def add(a, b): return a + b")

    assert actual == results


def test_mock_runner_does_not_execute_source_code(assignment, results):
    runner = MockTestRunner(results)
    malicious_or_broken_code = "raise RuntimeError('This must not execute')"

    actual = runner.run(assignment, malicious_or_broken_code)

    assert actual == results


def test_mock_runner_rejects_non_tuple_results():
    with pytest.raises(TypeError, match="tuple"):
        MockTestRunner([])


def test_mock_runner_rejects_invalid_result_objects():
    with pytest.raises(TypeError, match="TestCaseResult"):
        MockTestRunner(("passed",))


def test_mock_results_can_be_used_by_grading_engine(assignment, results):
    runner = MockTestRunner(results)
    test_results = runner.run(assignment, "placeholder source")

    report = grade_submission(assignment, test_results)

    assert report.earned_points == 5
    assert report.max_score == 10
    assert report.percentage == 50.0
