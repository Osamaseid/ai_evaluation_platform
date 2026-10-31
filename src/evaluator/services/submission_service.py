"""Service layer for submission management and lifecycle tracking."""

from datetime import datetime, timezone

from evaluator.exceptions import (
    DeadlineExceededError,
    EntityNotFoundError,
)
from evaluator.metadata import SubmissionMetadata
from evaluator.stores.assignment_store import AssignmentStore
from evaluator.stores.student_store import StudentStore
from evaluator.stores.submission_store import SubmissionStore
from evaluator.submission import (
    SubmissionRecord,
    SubmissionSource,
    SubmissionStatus,
)


class SubmissionService:
    """Coordinates submission creation, validation, and lifecycle state transitions."""

    def __init__(
        self,
        submission_store: SubmissionStore,
        assignment_store: AssignmentStore,
        student_store: StudentStore | None = None,
    ) -> None:
        self._submission_store = submission_store
        self._assignment_store = assignment_store
        self._student_store = student_store

    def create_submission(
        self,
        student_id: str,
        task_id: str,
        source_type: SubmissionSource,
        source_reference: str,
        source_code: str | None = None,
    ) -> SubmissionRecord:
        """Create and store a new submission after verifying student, assignment, and deadline."""
        if self._student_store is not None:
            student = self._student_store.get(student_id)
            if not student:
                raise EntityNotFoundError(f"Student with ID '{student_id}' not found.")

        assignment = self._assignment_store.get(task_id)
        if not assignment:
            raise EntityNotFoundError(f"Assignment with ID '{task_id}' not found.")

        now_utc = datetime.now(timezone.utc)
        if assignment.is_past_deadline(now_utc):
            raise DeadlineExceededError(
                f"Submission rejected: deadline for '{task_id}' was {assignment.deadline}."
            )

        metadata = SubmissionMetadata(student_id=student_id, task_id=task_id)
        record = SubmissionRecord(
            metadata=metadata,
            source_type=source_type,
            source_reference=source_reference,
            source_code=source_code,
            status=SubmissionStatus.RECEIVED,
        )

        self._submission_store.save(record)
        return record

    def get_submission(self, submission_id: str) -> SubmissionRecord:
        """Fetch submission by ID or raise EntityNotFoundError."""
        record = self._submission_store.get(submission_id)
        if not record:
            raise EntityNotFoundError(f"Submission with ID '{submission_id}' not found.")
        return record

    def list_by_student(self, student_id: str) -> list[SubmissionRecord]:
        """Fetch all submissions for a given student."""
        return self._submission_store.list_by_student(student_id)

    def list_by_task(self, task_id: str) -> list[SubmissionRecord]:
        """Fetch all submissions for a given assignment task."""
        return self._submission_store.list_by_task(task_id)

    def update_status(
        self,
        submission_id: str,
        new_status: SubmissionStatus,
    ) -> SubmissionRecord:
        """Transition submission status and persist the update."""
        current = self.get_submission(submission_id)
        updated = current.transition_to(new_status)
        self._submission_store.update(updated)
        return updated

