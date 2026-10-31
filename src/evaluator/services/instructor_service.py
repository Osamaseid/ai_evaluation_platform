"""Service layer for instructor management."""

from evaluator.exceptions import EntityNotFoundError
from evaluator.stores.instructor_store import InstructorStore
from evaluator.users import Instructor


class InstructorService:
    """Manages instructor lifecycle and queries."""

    def __init__(self, store: InstructorStore) -> None:
        self._store = store

    def register_instructor(self, instructor_id: str, name: str, email: str) -> Instructor:
        """Register a new instructor entity."""
        instructor = Instructor(instructor_id=instructor_id, name=name, email=email)
        self._store.save(instructor)
        return instructor

    def get_instructor(self, instructor_id: str) -> Instructor:
        """Retrieve instructor by instructor_id or raise EntityNotFoundError."""
        instructor = self._store.get(instructor_id)
        if not instructor:
            raise EntityNotFoundError(f"Instructor with ID '{instructor_id}' not found.")
        return instructor

    def list_instructors(self) -> list[Instructor]:
        """Return all registered instructors."""
        return self._store.list_all()

