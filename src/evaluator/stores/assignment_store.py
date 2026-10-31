"""Storage interface and in-memory implementation for assignments."""

from typing import Protocol

from evaluator.assignment import AssignmentDefinition


class AssignmentStore(Protocol):
    """Contract that every assignment storage backend must implement."""

    def save(self, assignment: AssignmentDefinition) -> None:
        """Persist an assignment. Raises ValueError if task_id already exists."""
        ...

    def update(self, assignment: AssignmentDefinition) -> None:
        """Update an existing assignment. Raises EntityNotFoundError if missing."""
        ...

    def get(self, task_id: str) -> AssignmentDefinition | None:
        """Retrieve an assignment by task_id, or None if not found."""
        ...

    def list_all(self) -> list[AssignmentDefinition]:
        """Return all stored assignments."""
        ...


class InMemoryAssignmentStore:
    """Dictionary-backed assignment store for development and testing."""

    def __init__(self) -> None:
        self._assignments: dict[str, AssignmentDefinition] = {}

    def save(self, assignment: AssignmentDefinition) -> None:
        if assignment.task_id in self._assignments:
            raise ValueError(
                f"Assignment '{assignment.task_id}' already exists."
            )
        self._assignments[assignment.task_id] = assignment

    def update(self, assignment: AssignmentDefinition) -> None:
        from evaluator.exceptions import EntityNotFoundError

        if assignment.task_id not in self._assignments:
            raise EntityNotFoundError(
                f"Assignment '{assignment.task_id}' not found."
            )
        self._assignments[assignment.task_id] = assignment

    def get(self, task_id: str) -> AssignmentDefinition | None:
        return self._assignments.get(task_id)

    def list_all(self) -> list[AssignmentDefinition]:
        return list(self._assignments.values())

