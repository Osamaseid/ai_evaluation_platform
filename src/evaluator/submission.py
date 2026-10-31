"""Core domain model and lifecycle management for programming submissions."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import uuid

from evaluator.exceptions import InvalidStateTransitionError
from evaluator.metadata import SubmissionMetadata


class SubmissionSource(str, Enum):
    """The channel through which a submission was received."""

    GITHUB = "github"
    FILE_UPLOAD = "file_upload"


class SubmissionStatus(str, Enum):
    """The lifecycle state of a submission."""

    RECEIVED = "received"
    VALIDATED = "validated"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"


_VALID_TRANSITIONS: dict[SubmissionStatus, set[SubmissionStatus]] = {
    SubmissionStatus.RECEIVED: {SubmissionStatus.VALIDATED, SubmissionStatus.FAILED},
    SubmissionStatus.VALIDATED: {SubmissionStatus.EVALUATING, SubmissionStatus.FAILED},
    SubmissionStatus.EVALUATING: {SubmissionStatus.COMPLETED, SubmissionStatus.FAILED},
    SubmissionStatus.COMPLETED: set(),
    SubmissionStatus.FAILED: set(),
}


@dataclass(frozen=True)
class SubmissionRecord:
    """Represent one programming assignment submission with lifecycle audit tracking."""

    metadata: SubmissionMetadata
    source_type: SubmissionSource
    source_reference: str
    status: SubmissionStatus = SubmissionStatus.RECEIVED
    submission_id: str | None = None
    submitted_at: datetime | None = None
    source_code: str | None = None
    status_history: tuple[tuple[SubmissionStatus, datetime], ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.metadata, SubmissionMetadata):
            raise TypeError("metadata must be a SubmissionMetadata instance.")

        if not isinstance(self.source_type, SubmissionSource):
            raise TypeError("source_type must be a SubmissionSource value.")

        if not isinstance(self.status, SubmissionStatus):
            raise TypeError("status must be a SubmissionStatus value.")

        if not isinstance(self.source_reference, str):
            raise TypeError("source_reference must be a string.")

        if not self.source_reference.strip():
            raise ValueError("source_reference cannot be empty.")

        if len(self.source_reference) > 2048:
            raise ValueError("source_reference cannot exceed 2048 characters.")

        if self.submission_id is None:
            generated_id = f"sub_{uuid.uuid4().hex[:12]}"
            object.__setattr__(self, "submission_id", generated_id)
        elif not isinstance(self.submission_id, str) or not self.submission_id.strip():
            raise ValueError("submission_id must be a non-empty string.")

        if self.submitted_at is None:
            now_ts = datetime.now(timezone.utc)
            object.__setattr__(self, "submitted_at", now_ts)
        elif not isinstance(self.submitted_at, datetime):
            raise TypeError("submitted_at must be a datetime instance.")

        if not self.status_history:
            object.__setattr__(
                self,
                "status_history",
                ((self.status, self.submitted_at),),
            )

    def transition_to(self, new_status: SubmissionStatus) -> "SubmissionRecord":
        """Produce an updated submission record adhering to legal lifecycle transitions."""
        if not isinstance(new_status, SubmissionStatus):
            raise TypeError("new_status must be a SubmissionStatus value.")

        allowed = _VALID_TRANSITIONS.get(self.status, set())
        if new_status not in allowed:
            raise InvalidStateTransitionError(
                f"Cannot transition submission from '{self.status.value}' to '{new_status.value}'."
            )

        now_ts = datetime.now(timezone.utc)
        updated_history = self.status_history + ((new_status, now_ts),)

        return SubmissionRecord(
            metadata=self.metadata,
            source_type=self.source_type,
            source_reference=self.source_reference,
            status=new_status,
            submission_id=self.submission_id,
            submitted_at=self.submitted_at,
            source_code=self.source_code,
            status_history=updated_history,
        )

    def with_source_code(self, code: str) -> "SubmissionRecord":
        """Attach collected source code to the submission."""
        if not isinstance(code, str) or not code.strip():
            raise ValueError("Source code cannot be empty.")

        return SubmissionRecord(
            metadata=self.metadata,
            source_type=self.source_type,
            source_reference=self.source_reference,
            status=self.status,
            submission_id=self.submission_id,
            submitted_at=self.submitted_at,
            source_code=code,
            status_history=self.status_history,
        )
