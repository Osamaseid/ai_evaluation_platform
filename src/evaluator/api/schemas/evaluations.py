"""Pydantic schemas for test execution outcomes and evaluation reports."""

from datetime import datetime
from pydantic import BaseModel

from evaluator.api.schemas.rubrics import RubricEvaluationSchema


class TestCaseResultSchema(BaseModel):
    """Execution outcome of a single test case."""

    __test__ = False

    test_case_id: str
    passed: bool
    message: str | None = None

    model_config = {"from_attributes": True}


class GradingReportSchema(BaseModel):
    """Deterministic score breakdown."""

    earned_points: int
    max_score: int
    passed_tests: int
    total_tests: int
    percentage: float

    model_config = {"from_attributes": True}


class EvaluationReportResponse(BaseModel):
    """Comprehensive evaluation report for student and instructor."""

    evaluation_id: str
    submission_id: str | None = None
    status: str
    grading_report: GradingReportSchema | None = None
    test_results: list[TestCaseResultSchema] = []
    rubric_evaluations: list[RubricEvaluationSchema] = []
    ai_review: str | None = None
    error_message: str | None = None
    evaluated_at: datetime

    model_config = {"from_attributes": True}

