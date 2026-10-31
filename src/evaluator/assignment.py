"""Assignment definitions, test cases, and rubric configuration."""

from dataclasses import dataclass
from datetime import datetime, timezone

from evaluator.rubric import GradingRubric


@dataclass(frozen=True)
class TestCaseDefinition:
    """Describe one test case configured by an instructor."""

    __test__ = False

    test_case_id: str
    description: str
    points: int
    assertion: str | None = None
    input_data: str | None = None
    expected_output: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.test_case_id, str) or not self.test_case_id.strip():
            raise ValueError("test_case_id cannot be empty.")

        if not isinstance(self.description, str) or not self.description.strip():
            raise ValueError("description cannot be empty.")

        # bool is a subclass of int in Python, so reject it explicitly.
        if isinstance(self.points, bool) or not isinstance(self.points, int):
            raise TypeError("points must be an integer.")

        if self.points <= 0:
            raise ValueError("points must be greater than zero.")

        if self.assertion is not None and not isinstance(self.assertion, str):
            raise TypeError("assertion must be a string or None.")

        if self.input_data is not None and not isinstance(self.input_data, str):
            raise TypeError("input_data must be a string or None.")

        if self.expected_output is not None and not isinstance(self.expected_output, str):
            raise TypeError("expected_output must be a string or None.")


@dataclass(frozen=True)
class AssignmentDefinition:
    """Describe a programming assignment, its grading tests, and optional rubrics."""

    task_id: str
    title: str
    test_cases: tuple[TestCaseDefinition, ...]
    instructor_id: str | None = None
    deadline: datetime | None = None
    rubric: GradingRubric | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.task_id, str) or not self.task_id.strip():
            raise ValueError("task_id cannot be empty.")

        if not isinstance(self.title, str) or not self.title.strip():
            raise ValueError("title cannot be empty.")

        if not isinstance(self.test_cases, tuple) or not self.test_cases:
            raise ValueError("test_cases must be a non-empty tuple.")

        if any(
            not isinstance(case, TestCaseDefinition)
            for case in self.test_cases
        ):
            raise TypeError(
                "Every test case must be a TestCaseDefinition."
            )

        case_ids = [case.test_case_id for case in self.test_cases]
        if len(case_ids) != len(set(case_ids)):
            raise ValueError("Test case IDs must be unique.")

        if self.instructor_id is not None:
            if not isinstance(self.instructor_id, str) or not self.instructor_id.strip():
                raise ValueError("instructor_id cannot be empty if specified.")

        if self.deadline is not None and not isinstance(self.deadline, datetime):
            raise TypeError("deadline must be a datetime instance or None.")

        if self.rubric is not None and not isinstance(self.rubric, GradingRubric):
            raise TypeError("rubric must be a GradingRubric instance or None.")

    @property
    def max_score(self) -> int:
        """Calculate the maximum possible score from deterministic test cases."""
        return sum(case.points for case in self.test_cases)

    def is_past_deadline(self, at_time: datetime | None = None) -> bool:
        """Check if a given timestamp (or current time) is past the submission deadline."""
        if self.deadline is None:
            return False
        current = at_time or datetime.now(timezone.utc)
        return current > self.deadline
