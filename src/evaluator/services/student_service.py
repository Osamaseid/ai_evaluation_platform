"""Service layer for student management."""

from evaluator.exceptions import EntityNotFoundError
from evaluator.stores.student_store import StudentStore
from evaluator.users import Student


class StudentService:
    """Manages student lifecycle and queries."""

    def __init__(self, store: StudentStore) -> None:
        self._store = store

    def register_student(self, student_id: str, name: str, email: str) -> Student:
        """Register a new student entity."""
        student = Student(student_id=student_id, name=name, email=email)
        self._store.save(student)
        return student

    def get_student(self, student_id: str) -> Student:
        """Retrieve student by student_id or raise EntityNotFoundError."""
        student = self._store.get(student_id)
        if not student:
            raise EntityNotFoundError(f"Student with ID '{student_id}' not found.")
        return student

    def list_students(self) -> list[Student]:
        """Return all registered students."""
        return self._store.list_all()

