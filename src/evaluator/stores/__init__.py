"""Storage interfaces and repository implementations."""

from evaluator.stores.assignment_store import (
    AssignmentStore,
    InMemoryAssignmentStore,
)
from evaluator.stores.student_store import (
    InMemoryStudentStore,
    StudentStore,
)
from evaluator.stores.instructor_store import (
    InMemoryInstructorStore,
    InstructorStore,
)
from evaluator.stores.submission_store import (
    InMemorySubmissionStore,
    SubmissionStore,
)
from evaluator.stores.evaluation_store import (
    EvaluationStore,
    InMemoryEvaluationStore,
)

__all__ = [
    "AssignmentStore",
    "InMemoryAssignmentStore",
    "StudentStore",
    "InMemoryStudentStore",
    "InstructorStore",
    "InMemoryInstructorStore",
    "SubmissionStore",
    "InMemorySubmissionStore",
    "EvaluationStore",
    "InMemoryEvaluationStore",
]
