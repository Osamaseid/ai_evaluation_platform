"""Storage interface and in-memory implementation for evaluation reports."""

from typing import Protocol

from evaluator.evaluation import EvaluationReport
from evaluator.exceptions import DuplicateEntityError


class EvaluationStore(Protocol):
    """Contract that every evaluation repository must implement."""

    def save(self, report: EvaluationReport) -> None:
        """Persist an evaluation report. Raises DuplicateEntityError if already exists."""
        ...

    def update(self, report: EvaluationReport) -> None:
        """Update an existing evaluation report. Raises EntityNotFoundError if missing."""
        ...

    def get(self, evaluation_id: str) -> EvaluationReport | None:
        """Retrieve an evaluation report by ID."""
        ...

    def get_by_submission(self, submission_id: str) -> EvaluationReport | None:
        """Retrieve evaluation report by associated submission ID."""
        ...

    def list_all(self) -> list[EvaluationReport]:
        """Return all evaluation reports."""
        ...


class InMemoryEvaluationStore:
    """Thread-safe in-memory store for evaluation reports."""

    def __init__(self) -> None:
        self._reports: dict[str, EvaluationReport] = {}

    def save(self, report: EvaluationReport) -> None:
        if report.evaluation_id in self._reports:
            raise DuplicateEntityError(
                f"EvaluationReport '{report.evaluation_id}' already exists."
            )
        self._reports[report.evaluation_id] = report

    def update(self, report: EvaluationReport) -> None:
        from evaluator.exceptions import EntityNotFoundError

        if report.evaluation_id not in self._reports:
            raise EntityNotFoundError(
                f"EvaluationReport '{report.evaluation_id}' not found."
            )
        self._reports[report.evaluation_id] = report

    def get(self, evaluation_id: str) -> EvaluationReport | None:
        return self._reports.get(evaluation_id)

    def get_by_submission(self, submission_id: str) -> EvaluationReport | None:
        for r in self._reports.values():
            if r.submission_id == submission_id:
                return r
        return None

    def list_all(self) -> list[EvaluationReport]:
        return list(self._reports.values())

