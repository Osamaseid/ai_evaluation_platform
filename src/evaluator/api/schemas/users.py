"""Pydantic schemas for student and instructor entities."""

from datetime import datetime
from pydantic import BaseModel, Field


class StudentCreateSchema(BaseModel):
    """Payload to register a new student."""

    student_id: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=r"^[A-Za-z0-9_-]+$",
        examples=["student001"],
    )
    name: str = Field(..., min_length=1, max_length=100, examples=["Ada Lovelace"])
    email: str = Field(..., examples=["ada@example.com"])


class StudentResponseSchema(BaseModel):
    """Response payload representing an enrolled student."""

    student_id: str
    name: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}


class InstructorCreateSchema(BaseModel):
    """Payload to register a new instructor."""

    instructor_id: str = Field(
        ...,
        min_length=1,
        max_length=50,
        pattern=r"^[A-Za-z0-9_-]+$",
        examples=["inst_prof_smith"],
    )
    name: str = Field(..., min_length=1, max_length=100, examples=["Prof. Smith"])
    email: str = Field(..., examples=["smith@university.edu"])


class InstructorResponseSchema(BaseModel):
    """Response payload representing an instructor."""

    instructor_id: str
    name: str
    email: str
    created_at: datetime

    model_config = {"from_attributes": True}

