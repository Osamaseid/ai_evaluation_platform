"""Storage interface and in-memory implementation for submissions."""

from typing import Protocol

from evaluator.exceptions import DuplicateEntityError, EntityNotFoundError
from evaluator.submission import SubmissionRecord


class SubmissionStore(Protocol):
    """Contract that every submission repository must implement."""

    def save(self, submission: SubmissionRecord) -> None:
        """Persist a new submission. Raises DuplicateEntityError if submission_id exists."""
        ...

    def update(self, submission: SubmissionRecord) -> None:
        """Update an existing submission record. Raises EntityNotFoundError if missing."""
        ...

    def get(self, submission_id: str) -> SubmissionRecord | None:
        """Retrieve a submission by its unique ID."""
        ...

    def list_by_student(self, student_id: str) -> list[SubmissionRecord]:
        """List all submissions by a student."""
        ...

    def list_by_task(self, task_id: str) -> list[SubmissionRecord]:
        """List all submissions for an assignment."""
        ...

    def list_all(self) -> list[SubmissionRecord]:
        """Return all submissions."""
        ...


class InMemorySubmissionStore:
    """Thread-safe in-memory store for submission records."""

    def __init__(self) -> None:
        self._submissions: dict[str, SubmissionRecord] = {}

    def save(self, submission: SubmissionRecord) -> None:
        if submission.submission_id in self._submissions:
            raise DuplicateEntityError(
                f"Submission '{submission.submission_id}' already exists."
            )
        self._submissions[submission.submission_id] = submission

    def update(self, submission: SubmissionRecord) -> None:
        if submission.submission_id not in self._submissions:
            raise EntityNotFoundError(
                f"Submission '{submission.submission_id}' does not exist."
            )
        self._submissions[submission.submission_id] = submission

    def get(self, submission_id: str) -> SubmissionRecord | None:
        return self._submissions.get(submission_id)

    def list_by_student(self, student_id: str) -> list[SubmissionRecord]:
        return [
            s for s in self._submissions.values()
            if s.metadata.student_id == student_id
        ]

    def list_by_task(self, task_id: str) -> list[SubmissionRecord]:
        return [
            s for s in self._submissions.values()
            if s.metadata.task_id == task_id
        ]

    def list_all(self) -> list[SubmissionRecord]:
        return list(self._submissions.values())

