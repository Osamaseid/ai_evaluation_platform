import pytest

from evaluator.assignment import (
    AssignmentDefinition,
    TestCaseDefinition,
)
from evaluator.grading import TestCaseResult, grade_submission


@pytest.fixture
def assignment():
    return AssignmentDefinition(
        task_id="python_week1",
        title="Calculator Functions",
        test_cases=(
            TestCaseDefinition("add", "Add two numbers", 3),
            TestCaseDefinition("subtract", "Subtract two numbers", 3),
            TestCaseDefinition("negative", "Handle negative numbers", 4),
        ),
    )


def test_max_score_is_calculated_from_test_cases(assignment):
    assert assignment.max_score == 10


def test_all_tests_pass(assignment):
    report = grade_submission(
        assignment,
        (
            TestCaseResult("add", True),
            TestCaseResult("subtract", True),
            TestCaseResult("negative", True),
        ),
    )

    assert report.earned_points == 10
    assert report.max_score == 10
    assert report.passed_tests == 3
    assert report.total_tests == 3
    assert report.percentage == 100.0


def test_partial_score(assignment):
    report = grade_submission(
        assignment,
        (
            TestCaseResult("add", True),
            TestCaseResult("subtract", False),
            TestCaseResult("negative", True),
        ),
    )

    assert report.earned_points == 7
    assert report.percentage == 70.0
    assert report.passed_tests == 2


def test_no_tests_pass(assignment):
    report = grade_submission(
        assignment,
        (
            TestCaseResult("add", False),
            TestCaseResult("subtract", False),
            TestCaseResult("negative", False),
        ),
    )

    assert report.earned_points == 0
    assert report.percentage == 0.0
    assert report.passed_tests == 0


def test_missing_result_is_rejected(assignment):
    with pytest.raises(ValueError, match="Missing"):
        grade_submission(
            assignment,
            (
                TestCaseResult("add", True),
                TestCaseResult("subtract", True),
            ),
        )


def test_duplicate_result_is_rejected(assignment):
    with pytest.raises(ValueError, match="Duplicate"):
        grade_submission(
            assignment,
            (
                TestCaseResult("add", True),
                TestCaseResult("add", False),
                TestCaseResult("subtract", True),
                TestCaseResult("negative", True),
            ),
        )


def test_unknown_test_result_is_rejected(assignment):
    with pytest.raises(ValueError, match="Unexpected"):
        grade_submission(
            assignment,
            (
                TestCaseResult("add", True),
                TestCaseResult("subtract", True),
                TestCaseResult("unknown", True),
            ),
        )


def test_invalid_test_outcome_is_rejected():
    with pytest.raises(TypeError, match="passed"):
        TestCaseResult("add", "yes")


def test_zero_or_negative_points_are_rejected():
    with pytest.raises(ValueError, match="greater than zero"):
        TestCaseDefinition("add", "Add numbers", 0)


def test_duplicate_assignment_test_ids_are_rejected():
    with pytest.raises(ValueError, match="unique"):
        AssignmentDefinition(
            task_id="python_week1",
            title="Calculator",
            test_cases=(
                TestCaseDefinition("add", "First test", 3),
                TestCaseDefinition("add", "Duplicate test", 4),
            ),
        )
