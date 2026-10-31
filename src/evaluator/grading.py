"""Deterministic grading based on trusted test results."""

from dataclasses import dataclass

from evaluator.assignment import AssignmentDefinition


@dataclass(frozen=True)
class TestCaseResult:
    """Represent the outcome of one executed test case."""

    __test__ = False

    test_case_id: str
    passed: bool
    message: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.test_case_id, str) or not self.test_case_id.strip():
            raise ValueError("test_case_id cannot be empty.")

        if not isinstance(self.passed, bool):
            raise TypeError("passed must be a boolean.")

        if self.message is not None and not isinstance(self.message, str):
            raise TypeError("message must be a string or None.")


@dataclass(frozen=True)
class GradingReport:
    """Summarize a submission's deterministic test score."""

    earned_points: int
    max_score: int
    passed_tests: int
    total_tests: int

    @property
    def percentage(self) -> float:
        """Return the score as a percentage."""
        return self.earned_points / self.max_score * 100


def grade_submission(
    assignment: AssignmentDefinition,
    results: tuple[TestCaseResult, ...],
) -> GradingReport:
    """Calculate a score from one result for every configured test."""

    if not isinstance(assignment, AssignmentDefinition):
        raise TypeError("assignment must be an AssignmentDefinition.")

    if not isinstance(results, tuple):
        raise TypeError("results must be a tuple.")

    if any(not isinstance(result, TestCaseResult) for result in results):
        raise TypeError("Every result must be a TestCaseResult.")

    expected_ids = {case.test_case_id for case in assignment.test_cases}
    result_ids = [result.test_case_id for result in results]

    if len(result_ids) != len(set(result_ids)):
        raise ValueError("Duplicate test results are not allowed.")

    actual_ids = set(result_ids)

    if actual_ids != expected_ids:
        missing = expected_ids - actual_ids
        unexpected = actual_ids - expected_ids
        raise ValueError(
            f"Test results do not match the assignment. "
            f"Missing: {sorted(missing)}; "
            f"Unexpected: {sorted(unexpected)}."
        )

    points_by_id = {
        case.test_case_id: case.points
        for case in assignment.test_cases
    }

    earned_points = sum(
        points_by_id[result.test_case_id]
        for result in results
        if result.passed
    )

    passed_tests = sum(result.passed for result in results)

    return GradingReport(
        earned_points=earned_points,
        max_score=assignment.max_score,
        passed_tests=passed_tests,
        total_tests=len(assignment.test_cases),
    )
