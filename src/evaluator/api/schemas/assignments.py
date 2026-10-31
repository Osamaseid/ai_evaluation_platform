"""Pydantic models for assignment API requests and responses."""

from pydantic import BaseModel, Field


class TestCaseSchema(BaseModel):
    """One test case in an assignment — used in both requests and responses."""

    __test__ = False

    test_case_id: str = Field(
        ...,
        min_length=1,
        max_length=100,
        examples=["test_add"],
    )
    description: str = Field(
        ...,
        min_length=1,
        max_length=500,
        examples=["Test basic addition"],
    )
    points: int = Field(..., gt=0, examples=[5])


class CreateAssignmentRequest(BaseModel):
    """Payload for creating a new assignment."""

    task_id: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=r"^[A-Za-z0-9_-]+$",
        examples=["python_week1"],
    )
    title: str = Field(
        ...,
        min_length=1,
        max_length=200,
        examples=["Calculator Functions"],
    )
    test_cases: list[TestCaseSchema] = Field(
        ...,
        min_length=1,
    )


class AssignmentResponse(BaseModel):
    """Assignment data returned to the client."""

    task_id: str
    title: str
    test_cases: list[TestCaseSchema]
    max_score: int

    model_config = {"from_attributes": True}
