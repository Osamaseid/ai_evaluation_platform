"""Coordinate test execution, deterministic grading, and evaluation reporting."""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
import uuid

from evaluator.assignment import AssignmentDefinition
from evaluator.grading import GradingReport, TestCaseResult, grade_submission
from evaluator.rubric import RubricEvaluation
from evaluator.runner import Runner


class EvaluationStatus(str, Enum):
    """Possible outcomes of an evaluation request."""

    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class EvaluationReport:
    """Represent the outcome of one evaluation."""

    status: EvaluationStatus
    grading_report: GradingReport | None = None
    error_message: str | None = None
    evaluation_id: str | None = None
    submission_id: str | None = None
    test_results: tuple[TestCaseResult, ...] = ()
    rubric_evaluations: tuple[RubricEvaluation, ...] = ()
    ai_review: str | None = None
    evaluated_at: datetime | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.status, EvaluationStatus):
            raise TypeError("status must be an EvaluationStatus value.")

        if self.status is EvaluationStatus.COMPLETED:
            if not isinstance(self.grading_report, GradingReport):
                raise ValueError(
                    "A completed evaluation must contain a grading report."
                )
            if self.error_message is not None:
                raise ValueError(
                    "A completed evaluation cannot contain an error message."
                )

        if self.status is EvaluationStatus.FAILED:
            if self.grading_report is not None:
                raise ValueError(
                    "A failed evaluation cannot contain a grading report."
                )
            if not self.error_message:
                raise ValueError(
                    "A failed evaluation must contain an error message."
                )

        if self.evaluation_id is None:
            object.__setattr__(self, "evaluation_id", f"eval_{uuid.uuid4().hex[:12]}")

        if self.evaluated_at is None:
            object.__setattr__(self, "evaluated_at", datetime.now(timezone.utc))


class EvaluationService:
    """Coordinate a runner and the grading engine."""

    def __init__(self, runner: Runner) -> None:
        self._runner = runner

    def evaluate(
        self,
        assignment: AssignmentDefinition,
        source_code: str,
        submission_id: str | None = None,
    ) -> EvaluationReport:
        """Run tests and calculate a score, or report a failure."""
        try:
            results = self._runner.run(assignment, source_code)
            grading_report = grade_submission(assignment, results)

            return EvaluationReport(
                status=EvaluationStatus.COMPLETED,
                grading_report=grading_report,
                submission_id=submission_id,
                test_results=results,
            )

        except Exception as exc:
            return EvaluationReport(
                status=EvaluationStatus.FAILED,
                error_message=f"{type(exc).__name__}: {exc}",
                submission_id=submission_id,
            )
