"""Pydantic schemas for test execution outcomes and evaluation reports."""

from datetime import datetime
from typing import Any
from pydantic import BaseModel

from evaluator.api.schemas.rubrics import RubricEvaluationSchema


class TestCaseResultSchema(BaseModel):
    """Execution outcome of a single test case."""

    __test__ = False

    test_case_id: str
    passed: bool
    message: str | None = None
    execution_time_ms: int | None = None
    stdout: str | None = None
    stderr: str | None = None

    model_config = {"from_attributes": True}


class GradingReportSchema(BaseModel):
    """Deterministic score breakdown."""

    earned_points: int
    max_score: int
    passed_tests: int
    total_tests: int
    percentage: float
    score_percentage: float | None = None
    test_case_results: list[TestCaseResultSchema] = []

    model_config = {"from_attributes": True}


class EvaluationReportResponse(BaseModel):
    """Comprehensive evaluation report for student and instructor."""

    evaluation_id: str
    submission_id: str | None = None
    student_id: str | None = None
    task_id: str | None = None
    status: str
    deterministic_score: int | None = None
    max_score: int | None = None
    grading_report: GradingReportSchema | None = None
    test_results: list[TestCaseResultSchema] = []
    rubric_evaluations: Any | None = []
    ai_review: Any | None = None
    error_message: str | None = None
    evaluated_at: datetime
    manual_override_score: int | None = None
    instructor_notes: str | None = None
    reviewed_by: str | None = None
    reviewed_at: datetime | None = None
    started_at: datetime | None = None
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}
