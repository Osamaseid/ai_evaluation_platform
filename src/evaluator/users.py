"""Student and Instructor domain models."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
import re

from evaluator.exceptions import EntityValidationError

_ID_PATTERN = re.compile(r"^[A-Za-z0-9_-]{1,50}$")
_EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def _validate_user_id(field_name: str, value: str) -> None:
    if not isinstance(value, str) or not _ID_PATTERN.fullmatch(value):
        raise EntityValidationError(
            f"{field_name} must contain 1-50 characters using only letters, numbers, underscores, or hyphens."
        )


def _validate_name(name: str) -> None:
    if not isinstance(name, str) or not name.strip():
        raise EntityValidationError("name cannot be empty.")
    if len(name.strip()) > 100:
        raise EntityValidationError("name cannot exceed 100 characters.")


def _validate_email(email: str) -> None:
    if not isinstance(email, str) or not _EMAIL_PATTERN.fullmatch(email.strip()):
        raise EntityValidationError(f"Invalid email address format: '{email}'.")


@dataclass(frozen=True)
class Student:
    """Represents an enrolled student."""

    student_id: str
    name: str
    email: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        _validate_user_id("student_id", self.student_id)
        _validate_name(self.name)
        _validate_email(self.email)


@dataclass(frozen=True)
class Instructor:
    """Represents a course instructor or teaching assistant."""

    instructor_id: str
    name: str
    email: str
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self) -> None:
        _validate_user_id("instructor_id", self.instructor_id)
        _validate_name(self.name)
        _validate_email(self.email)

