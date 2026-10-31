"""Storage interface and in-memory implementation for students."""

from typing import Protocol

from evaluator.exceptions import DuplicateEntityError
from evaluator.users import Student


class StudentStore(Protocol):
    """Contract that every student repository must implement."""

    def save(self, student: Student) -> None:
        """Persist a student. Raises DuplicateEntityError if student_id exists."""
        ...

    def get(self, student_id: str) -> Student | None:
        """Retrieve a student by student_id, or None if not found."""
        ...

    def get_by_email(self, email: str) -> Student | None:
        """Retrieve a student by email address, or None if not found."""
        ...

    def list_all(self) -> list[Student]:
        """Return all registered students."""
        ...


class InMemoryStudentStore:
    """Thread-safe in-memory store for student records."""

    def __init__(self) -> None:
        self._students: dict[str, Student] = {}

    def save(self, student: Student) -> None:
        if student.student_id in self._students:
            raise DuplicateEntityError(
                f"Student '{student.student_id}' already exists."
            )
        # Check duplicate email
        if any(s.email.lower() == student.email.lower() for s in self._students.values()):
            raise DuplicateEntityError(
                f"Student with email '{student.email}' already exists."
            )
        self._students[student.student_id] = student

    def get(self, student_id: str) -> Student | None:
        return self._students.get(student_id)

    def get_by_email(self, email: str) -> Student | None:
        clean = email.strip().lower()
        for student in self._students.values():
            if student.email.lower() == clean:
                return student
        return None

    def list_all(self) -> list[Student]:
        return list(self._students.values())

