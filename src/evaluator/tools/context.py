"""Security context for agent tool execution."""

from dataclasses import dataclass
import uuid


@dataclass(frozen=True)
class EvaluationSecurityContext:
    """Restricts agent tool permissions to a specific submission and assignment scope."""

    authorized_submission_id: str
    authorized_task_id: str
    authorized_student_id: str
    session_id: str | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.authorized_submission_id, str) or not self.authorized_submission_id.strip():
            raise ValueError("authorized_submission_id cannot be empty.")
        if not isinstance(self.authorized_task_id, str) or not self.authorized_task_id.strip():
            raise ValueError("authorized_task_id cannot be empty.")
        if not isinstance(self.authorized_student_id, str) or not self.authorized_student_id.strip():
            raise ValueError("authorized_student_id cannot be empty.")

        if self.session_id is None:
            object.__setattr__(self, "session_id", f"sess_{uuid.uuid4().hex[:12]}")

