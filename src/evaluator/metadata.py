"""Validation for programming submission metadata."""

import re
from dataclasses import dataclass


_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,50}$")


@dataclass(frozen=True)
class SubmissionMetadata:
    """Identify the student and assignment for a submission."""

    student_id: str
    task_id: str

    def __post_init__(self) -> None:
        self._validate_id("student_id", self.student_id)
        self._validate_id("task_id", self.task_id)

    @staticmethod
    def _validate_id(field_name: str, value: str) -> None:
        if not isinstance(value, str) or not _ID_PATTERN.fullmatch(value):
            raise ValueError(
                f"{field_name} must contain 1-50 characters "
                "using only letters, numbers, underscores, or hyphens."
            )
