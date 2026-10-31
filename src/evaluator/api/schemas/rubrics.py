"""Pydantic schemas for grading rubrics and criteria."""

from pydantic import BaseModel, Field


class RubricCriterionSchema(BaseModel):
    """Specification for one qualitative rubric criterion."""

    criterion_id: str = Field(..., min_length=1, max_length=50, examples=["code_style"])
    name: str = Field(..., min_length=1, max_length=100, examples=["Code Style & PEP8"])
    description: str = Field(..., min_length=1, max_length=500, examples=["Follows PEP8 conventions"])
    max_points: int = Field(..., gt=0, examples=[10])
    weight: float = Field(default=1.0, gt=0.0, examples=[1.0])


class GradingRubricSchema(BaseModel):
    """Grading rubric containing multiple assessment criteria."""

    rubric_id: str = Field(..., min_length=1, max_length=50, examples=["rubric_week1"])
    title: str = Field(..., min_length=1, max_length=200, examples=["Week 1 Code Quality Rubric"])
    criteria: list[RubricCriterionSchema] = Field(..., min_length=1)

    model_config = {"from_attributes": True}


class RubricEvaluationSchema(BaseModel):
    """Assessment score and explanation for one rubric criterion."""

    criterion_id: str
    score: float
    feedback: str

    model_config = {"from_attributes": True}

