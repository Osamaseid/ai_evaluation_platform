"""Service layer for assignment management."""

from evaluator.assignment import AssignmentDefinition
from evaluator.exceptions import EntityNotFoundError
from evaluator.stores.assignment_store import AssignmentStore
from evaluator.stores.instructor_store import InstructorStore


class AssignmentService:
    """Manages assignment creation and queries."""

    def __init__(
        self,
        assignment_store: AssignmentStore,
        instructor_store: InstructorStore | None = None,
    ) -> None:
        self._store = assignment_store
        self._instructor_store = instructor_store

    def create_assignment(self, assignment: AssignmentDefinition) -> AssignmentDefinition:
        """Create and persist an assignment definition."""
        if assignment.instructor_id and self._instructor_store:
            instructor = self._instructor_store.get(assignment.instructor_id)
            if not instructor:
                raise EntityNotFoundError(
                    f"Instructor with ID '{assignment.instructor_id}' not found."
                )

        self._store.save(assignment)
        return assignment

    def get_assignment(self, task_id: str) -> AssignmentDefinition:
        """Retrieve assignment by task_id or raise EntityNotFoundError."""
        assignment = self._store.get(task_id)
        if not assignment:
            raise EntityNotFoundError(f"Assignment with ID '{task_id}' not found.")
        return assignment

    def list_assignments(self) -> list[AssignmentDefinition]:
        """Return all stored assignments."""
        return self._store.list_all()

    def update_assignment(self, assignment: AssignmentDefinition) -> AssignmentDefinition:
        """Update an existing assignment definition."""
        self.get_assignment(assignment.task_id)
        self._store.update(assignment)
        return assignment

