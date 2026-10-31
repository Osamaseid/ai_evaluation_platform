"""Pydantic schemas for instructor manual review and grading adjustments."""

from datetime import datetime
from pydantic import BaseModel, Field

from evaluator.api.schemas.rubrics import RubricEvaluationSchema


class ManualReviewRequest(BaseModel):
    """Payload to submit instructor manual review, score override, or rubric scoring."""

    override_score: int | None = Field(default=None, ge=0, description="Optional overridden deterministic score")
    instructor_notes: str | None = Field(default=None, max_length=2000, description="Pedagogical notes from instructor")
    rubric_evaluations: list[RubricEvaluationSchema] = Field(default_factory=list, description="Qualitative rubric assessments")


class ManualReviewResponse(BaseModel):
    """Outcome of applied manual review."""

    evaluation_id: str
    submission_id: str | None = None
    original_score: int | None = None
    final_score: int | None = None
    override_score: int | None = None
    instructor_notes: str | None = None
    rubric_evaluations: list[RubricEvaluationSchema] = []
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None

    model_config = {"from_attributes": True}

