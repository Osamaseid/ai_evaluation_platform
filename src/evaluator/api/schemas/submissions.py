"""Pydantic schemas for submission requests and lifecycle responses."""

from datetime import datetime
from pydantic import BaseModel, Field

from evaluator.submission import SubmissionSource, SubmissionStatus


class CreateSubmissionRequest(BaseModel):
    """Payload to submit student work for evaluation."""

    student_id: str = Field(..., min_length=1, max_length=50, pattern=r"^[A-Za-z0-9_-]+$")
    task_id: str = Field(..., min_length=1, max_length=50, pattern=r"^[A-Za-z0-9_-]+$")
    source_type: SubmissionSource = Field(..., examples=[SubmissionSource.GITHUB])
    source_reference: str = Field(
        ...,
        min_length=1,
        max_length=2048,
        examples=["https://github.com/student/homework1"],
    )
    source_code: str | None = Field(default=None, max_length=500_000)


class SubmissionResponse(BaseModel):
    """Details of a registered submission."""

    submission_id: str
    student_id: str
    task_id: str
    source_type: str
    source_reference: str
    status: str
    submitted_at: datetime

    model_config = {"from_attributes": True}


class SubmissionStatusResponse(BaseModel):
    """Status query payload including state transition audit history."""

    submission_id: str
    status: str
    history: list[tuple[str, datetime]]

    model_config = {"from_attributes": True}

