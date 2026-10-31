"""Storage interface and in-memory implementation for instructors."""

from typing import Protocol

from evaluator.exceptions import DuplicateEntityError
from evaluator.users import Instructor


class InstructorStore(Protocol):
    """Contract that every instructor repository must implement."""

    def save(self, instructor: Instructor) -> None:
        """Persist an instructor. Raises DuplicateEntityError if instructor_id exists."""
        ...

    def get(self, instructor_id: str) -> Instructor | None:
        """Retrieve an instructor by instructor_id, or None if not found."""
        ...

    def get_by_email(self, email: str) -> Instructor | None:
        """Retrieve an instructor by email address, or None if not found."""
        ...

    def list_all(self) -> list[Instructor]:
        """Return all registered instructors."""
        ...


class InMemoryInstructorStore:
    """Thread-safe in-memory store for instructor records."""

    def __init__(self) -> None:
        self._instructors: dict[str, Instructor] = {}

    def save(self, instructor: Instructor) -> None:
        if instructor.instructor_id in self._instructors:
            raise DuplicateEntityError(
                f"Instructor '{instructor.instructor_id}' already exists."
            )
        if any(i.email.lower() == instructor.email.lower() for i in self._instructors.values()):
            raise DuplicateEntityError(
                f"Instructor with email '{instructor.email}' already exists."
            )
        self._instructors[instructor.instructor_id] = instructor

    def get(self, instructor_id: str) -> Instructor | None:
        return self._instructors.get(instructor_id)

    def get_by_email(self, email: str) -> Instructor | None:
        clean = email.strip().lower()
        for instructor in self._instructors.values():
            if instructor.email.lower() == clean:
                return instructor
        return None

    def list_all(self) -> list[Instructor]:
        return list(self._instructors.values())

