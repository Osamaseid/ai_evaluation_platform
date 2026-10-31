"""Domain models for assignment grading rubrics."""

from dataclasses import dataclass

from evaluator.exceptions import EntityValidationError


@dataclass(frozen=True)
class RubricCriterion:
    """A qualitative evaluation criterion (e.g. Code Style, Time Complexity, Robustness)."""

    criterion_id: str
    name: str
    description: str
    max_points: int
    weight: float = 1.0

    def __post_init__(self) -> None:
        if not isinstance(self.criterion_id, str) or not self.criterion_id.strip():
            raise EntityValidationError("criterion_id cannot be empty.")
        if not isinstance(self.name, str) or not self.name.strip():
            raise EntityValidationError("name cannot be empty.")
        if not isinstance(self.description, str) or not self.description.strip():
            raise EntityValidationError("description cannot be empty.")
        if isinstance(self.max_points, bool) or not isinstance(self.max_points, int):
            raise TypeError("max_points must be an integer.")
        if self.max_points <= 0:
            raise EntityValidationError("max_points must be greater than zero.")
        if self.weight <= 0.0:
            raise EntityValidationError("weight must be greater than zero.")


@dataclass(frozen=True)
class GradingRubric:
    """Collection of criteria configuring qualitative grading guidelines."""

    rubric_id: str
    title: str
    criteria: tuple[RubricCriterion, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.rubric_id, str) or not self.rubric_id.strip():
            raise EntityValidationError("rubric_id cannot be empty.")
        if not isinstance(self.title, str) or not self.title.strip():
            raise EntityValidationError("title cannot be empty.")
        if not isinstance(self.criteria, tuple) or not self.criteria:
            raise EntityValidationError("criteria must be a non-empty tuple.")

        criterion_ids = [c.criterion_id for c in self.criteria]
        if len(criterion_ids) != len(set(criterion_ids)):
            raise EntityValidationError("Rubric criterion IDs must be unique.")

    @property
    def max_score(self) -> int:
        return sum(c.max_points for c in self.criteria)


@dataclass(frozen=True)
class RubricEvaluation:
    """Outcome of evaluating one rubric criterion."""

    criterion_id: str
    score: float
    feedback: str

    def __post_init__(self) -> None:
        if not isinstance(self.criterion_id, str) or not self.criterion_id.strip():
            raise EntityValidationError("criterion_id cannot be empty.")
        if not isinstance(self.score, (int, float)) or self.score < 0:
            raise EntityValidationError("score must be a non-negative number.")
        if not isinstance(self.feedback, str):
            raise TypeError("feedback must be a string.")

