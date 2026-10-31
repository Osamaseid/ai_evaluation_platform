"""Storage interface and in-memory implementation for grading rubrics."""

from typing import Protocol

from evaluator.exceptions import DuplicateEntityError, EntityNotFoundError
from evaluator.rubric import GradingRubric


class RubricStore(Protocol):
    """Storage contract for grading rubrics."""

    def save(self, rubric: GradingRubric) -> None:
        """Persist a grading rubric. Raises DuplicateEntityError if already exists."""
        ...

    def update(self, rubric: GradingRubric) -> None:
        """Update an existing grading rubric. Raises EntityNotFoundError if missing."""
        ...

    def get(self, rubric_id: str) -> GradingRubric | None:
        """Retrieve a rubric by its unique ID."""
        ...

    def list_all(self) -> list[GradingRubric]:
        """Return all stored grading rubrics."""
        ...


class InMemoryRubricStore:
    """Thread-safe in-memory store for grading rubrics."""

    def __init__(self) -> None:
        self._rubrics: dict[str, GradingRubric] = {}

    def save(self, rubric: GradingRubric) -> None:
        if rubric.rubric_id in self._rubrics:
            raise DuplicateEntityError(f"GradingRubric '{rubric.rubric_id}' already exists.")
        self._rubrics[rubric.rubric_id] = rubric

    def update(self, rubric: GradingRubric) -> None:
        if rubric.rubric_id not in self._rubrics:
            raise EntityNotFoundError(f"GradingRubric '{rubric.rubric_id}' not found.")
        self._rubrics[rubric.rubric_id] = rubric

    def get(self, rubric_id: str) -> GradingRubric | None:
        return self._rubrics.get(rubric_id)

    def list_all(self) -> list[GradingRubric]:
        return list(self._rubrics.values())

