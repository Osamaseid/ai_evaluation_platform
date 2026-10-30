import pytest

from evaluator.assignment import (
    AssignmentDefinition,
    TestCaseDefinition,
)
from evaluator.evaluation import (
    EvaluationReport,
    EvaluationService,
    EvaluationStatus,
)
from evaluator.grading import TestCaseResult, GradingReport
from evaluator.runner import MockTestRunner


@pytest.fixture
def assignment():
    return AssignmentDefinition(
        task_id="python_week1",
        title="Calculator Functions",
        test_cases=(
            TestCaseDefinition("add", "Add numbers", 5),
            TestCaseDefinition("subtract", "Subtract numbers", 5),
        ),
    )


def test_successful_evaluation(assignment):
    runner = MockTestRunner(
        (
            TestCaseResult("add", True),
            TestCaseResult("subtract", True),
        )
    )

    service = EvaluationService(runner)
    report = service.evaluate(assignment, "student source code")

    assert report.status is EvaluationStatus.COMPLETED
    assert report.grading_report.earned_points == 10
    assert report.grading_report.percentage == 100.0
    assert report.error_message is None


def test_partial_score_evaluation(assignment):
    runner = MockTestRunner(
        (
            TestCaseResult("add", True),
            TestCaseResult("subtract", False),
        )
    )

    service = EvaluationService(runner)
    report = service.evaluate(assignment, "student source code")

    assert report.status is EvaluationStatus.COMPLETED
    assert report.grading_report.earned_points == 5
    assert report.grading_report.percentage == 50.0


def test_runner_failure_returns_failed_report(assignment):
    class BrokenRunner:
        def run(self, assignment, source_code):
            raise RuntimeError("Runner crashed")

    service = EvaluationService(BrokenRunner())
    report = service.evaluate(assignment, "student source code")

    assert report.status is EvaluationStatus.FAILED
    assert report.grading_report is None
    assert "Runner crashed" in report.error_message


def test_invalid_runner_results_return_failed_report(assignment):
    runner = MockTestRunner(
        (
            TestCaseResult("add", True),
            # The second expected test result is missing.
        )
    )

    service = EvaluationService(runner)
    report = service.evaluate(assignment, "student source code")

    assert report.status is EvaluationStatus.FAILED
    assert report.grading_report is None
    assert "Missing" in report.error_message


def test_completed_report_requires_grading_report():
    with pytest.raises(ValueError):
        EvaluationReport(status=EvaluationStatus.COMPLETED)


def test_failed_report_requires_error_message():
    with pytest.raises(ValueError):
        EvaluationReport(status=EvaluationStatus.FAILED)


def test_failed_report_cannot_contain_grading_report():
    grading = GradingReport(
        earned_points=10,
        max_score=10,
        passed_tests=2,
        total_tests=2,
    )

    with pytest.raises(ValueError):
        EvaluationReport(
            status=EvaluationStatus.FAILED,
            grading_report=grading,
            error_message="Runner failed",
        )
