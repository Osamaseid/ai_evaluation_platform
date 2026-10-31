"""Service layer for instructor manual review and grading adjustments."""

from datetime import datetime, timezone
import logging

from evaluator.evaluation import EvaluationReport
from evaluator.exceptions import EntityNotFoundError
from evaluator.rubric import RubricEvaluation
from evaluator.stores.evaluation_store import EvaluationStore
from evaluator.stores.instructor_store import InstructorStore

logger = logging.getLogger(__name__)


class ManualReviewService:
    """Coordinates instructor post-evaluation review, score overrides, and rubric evaluations."""

    def __init__(
        self,
        evaluation_store: EvaluationStore,
        instructor_store: InstructorStore | None = None,
    ) -> None:
        self._evaluation_store = evaluation_store
        self._instructor_store = instructor_store

    def add_manual_review(
        self,
        evaluation_id: str,
        instructor_id: str,
        override_score: int | None = None,
        instructor_notes: str | None = None,
        rubric_evaluations: tuple[RubricEvaluation, ...] = (),
    ) -> EvaluationReport:
        """Apply instructor review observations, score override, and qualitative rubric assessments."""
        if self._instructor_store is not None:
            instructor = self._instructor_store.get(instructor_id)
            if not instructor:
                raise EntityNotFoundError(f"Instructor '{instructor_id}' not found.")

        report = self._evaluation_store.get(evaluation_id)
        if not report:
            raise EntityNotFoundError(f"Evaluation report '{evaluation_id}' not found.")

        now_ts = datetime.now(timezone.utc)

        # Build updated evaluation report preserving all prior attributes
        updated_report = EvaluationReport(
            status=report.status,
            grading_report=report.grading_report,
            error_message=report.error_message,
            evaluation_id=report.evaluation_id,
            submission_id=report.submission_id,
            test_results=report.test_results,
            rubric_evaluations=rubric_evaluations or report.rubric_evaluations,
            ai_review=report.ai_review,
            evaluated_at=report.evaluated_at,
            structured_feedback=report.structured_feedback,
            workflow_audit=report.workflow_audit,
            feedback_summary=report.feedback_summary,
            instructor_notes=instructor_notes or report.instructor_notes,
            manual_override_score=override_score if override_score is not None else report.manual_override_score,
            reviewed_by=instructor_id,
            reviewed_at=now_ts,
        )

        self._evaluation_store.update(updated_report)
        logger.info(
            "Instructor '%s' applied manual review to evaluation '%s' (override_score=%s)",
            instructor_id,
            evaluation_id,
            override_score,
        )
        return updated_report

