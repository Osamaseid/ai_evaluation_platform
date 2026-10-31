"""Workflow execution tracking and step audit models."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class WorkflowStep(str, Enum):
    """Discrete phases of the evaluation orchestration pipeline."""

    SUBMISSION_VALIDATION = "submission_validation"
    ASSIGNMENT_RETRIEVAL = "assignment_retrieval"
    SOURCE_COLLECTION = "source_collection"
    AUTOMATED_TESTING = "automated_testing"
    DETERMINISTIC_GRADING = "deterministic_grading"
    AI_CODE_REVIEW = "ai_code_review"
    FEEDBACK_GENERATION = "feedback_generation"
    REPORT_PERSISTENCE = "report_persistence"


class StepStatus(str, Enum):
    """Outcome status of an individual pipeline step."""

    SUCCESS = "success"
    DEGRADED = "degraded"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(frozen=True)
class WorkflowStepAudit:
    """Record of execution metrics and status for one pipeline step."""

    step: WorkflowStep
    status: StepStatus
    duration_seconds: float
    details: str | None = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class WorkflowExecutionAudit:
    """Full execution audit trail for an evaluation job."""

    workflow_id: str
    submission_id: str
    task_id: str
    steps: list[WorkflowStepAudit] = field(default_factory=list)
    total_duration_seconds: float = 0.0
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    completed_at: datetime | None = None

    def add_step(
        self,
        step: WorkflowStep,
        status: StepStatus,
        duration_seconds: float,
        details: str | None = None,
    ) -> WorkflowStepAudit:
        """Append an audited step record."""
        record = WorkflowStepAudit(
            step=step,
            status=status,
            duration_seconds=max(0.0, duration_seconds),
            details=details,
        )
        self.steps.append(record)
        return record
