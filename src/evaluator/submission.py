"""Core domain model for programming submissions."""

from dataclasses import dataclass
from enum import Enum

from evaluator.metadata import SubmissionMetadata


class SubmissionSource(str, Enum):
    """The channel through which a submission was received."""

    GITHUB = "github"
    FILE_UPLOAD = "file_upload"


class SubmissionStatus(str, Enum):
    """The current state of a submission."""

    RECEIVED = "received"
    VALIDATED = "validated"
    EVALUATING = "evaluating"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass(frozen=True)
class SubmissionRecord:
    """Represent one programming assignment submission."""

    metadata: SubmissionMetadata
    source_type: SubmissionSource
    source_reference: str
    status: SubmissionStatus = SubmissionStatus.RECEIVED

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
