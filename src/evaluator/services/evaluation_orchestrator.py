"""Central Evaluation Agent orchestration workflow.

Coordinates submission validation, assignment retrieval, source collection,
automated test execution, Gemini code review, structured response validation,
deterministic grading, feedback synthesis, report creation, and database persistence.
"""

import asyncio
from datetime import datetime, timezone
import logging
import time
from typing import Any
import uuid

from evaluator.ai_reviewer import CodeReviewFeedback
from evaluator.assignment import AssignmentDefinition
from evaluator.collector import SourceBundle, SourceCollector
from evaluator.evaluation import EvaluationReport, EvaluationStatus
from evaluator.exceptions import EntityNotFoundError
from evaluator.grading import TestCaseResult, grade_submission
from evaluator.orchestration.exceptions import (
    DuplicateProcessingError,
    InfrastructureExecutionError,
)
from evaluator.orchestration.feedback_generator import FeedbackGenerator
from evaluator.orchestration.models import (
    StepStatus,
    WorkflowExecutionAudit,
    WorkflowStep,
)
from evaluator.runner import Runner
from evaluator.stores.assignment_store import AssignmentStore
from evaluator.stores.evaluation_store import EvaluationStore
from evaluator.stores.submission_store import SubmissionStore
from evaluator.submission import SubmissionRecord, SubmissionSource, SubmissionStatus

logger = logging.getLogger(__name__)


class EvaluationOrchestrator:
    """Central orchestrator managing the complete 10-step evaluation lifecycle."""

    def __init__(
        self,
        submission_store: SubmissionStore,
        assignment_store: AssignmentStore,
        evaluation_store: EvaluationStore,
        runner: Runner,
        ai_reviewer: Any | None = None,
        max_retries: int = 2,
        retry_delay_seconds: float = 0.5,
    ) -> None:
        self._submission_store = submission_store
        self._assignment_store = assignment_store
        self._evaluation_store = evaluation_store
        self._runner = runner
        self._ai_reviewer = ai_reviewer
        self._max_retries = max(1, max_retries)
        self._retry_delay_seconds = max(0.0, retry_delay_seconds)

    def evaluate_submission(
        self,
        submission_id: str,
        force_reevaluate: bool = False,
    ) -> EvaluationReport:
        """Execute the end-to-end 10-step evaluation workflow for a submission."""
        workflow_id = f"wf_{uuid.uuid4().hex[:12]}"
        t_workflow_start = time.perf_counter()

        # Step 1: Submission Validation
        t0 = time.perf_counter()
        submission = self._submission_store.get(submission_id)
        if not submission:
            raise EntityNotFoundError(f"Submission '{submission_id}' not found.")

        # Concurrency & Re-entrancy Guards
        if submission.status is SubmissionStatus.EVALUATING:
            raise DuplicateProcessingError(
                f"Submission '{submission_id}' is currently being evaluated."
            )

        if submission.status is SubmissionStatus.COMPLETED and not force_reevaluate:
            existing = self._evaluation_store.get_by_submission(submission_id)
            if existing:
                return existing

        audit = WorkflowExecutionAudit(
            workflow_id=workflow_id,
            submission_id=submission_id,
            task_id=submission.metadata.task_id,
            started_at=datetime.now(timezone.utc),
        )

        submission = submission.transition_to(SubmissionStatus.VALIDATED)
        self._submission_store.update(submission)
        audit.add_step(
            WorkflowStep.SUBMISSION_VALIDATION,
            StepStatus.SUCCESS,
            time.perf_counter() - t0,
            details=f"Submission {submission_id} validated successfully.",
        )

        # Step 2: Assignment Retrieval
        t0 = time.perf_counter()
        assignment = self._assignment_store.get(submission.metadata.task_id)
        if not assignment:
            duration = time.perf_counter() - t0
            audit.add_step(
                WorkflowStep.ASSIGNMENT_RETRIEVAL,
                StepStatus.FAILED,
                duration,
                details=f"Assignment '{submission.metadata.task_id}' not found.",
            )
            submission = submission.transition_to(SubmissionStatus.FAILED)
            self._submission_store.update(submission)
            raise EntityNotFoundError(
                f"Assignment '{submission.metadata.task_id}' not found."
            )

        audit.add_step(
            WorkflowStep.ASSIGNMENT_RETRIEVAL,
            StepStatus.SUCCESS,
            time.perf_counter() - t0,
            details=f"Retrieved assignment '{assignment.task_id}'.",
        )

        # Step 3: Source-Code Collection
        t0 = time.perf_counter()
        source_code = submission.source_code
        if not source_code:
            try:
                if submission.source_type is SubmissionSource.GITHUB:
                    bundle = self._collect_github_source_with_retry(
                        submission.source_reference
                    )
                    source_code = bundle.get_concatenated_source()
                    submission = submission.with_source_code(source_code)
                    self._submission_store.update(submission)
                else:
                    raise ValueError(
                        f"No source code available for upload submission '{submission_id}'."
                    )
                audit.add_step(
                    WorkflowStep.SOURCE_COLLECTION,
                    StepStatus.SUCCESS,
                    time.perf_counter() - t0,
                    details=f"Collected {len(source_code)} characters of source code.",
                )
            except Exception as exc:
                duration = time.perf_counter() - t0
                audit.add_step(
                    WorkflowStep.SOURCE_COLLECTION,
                    StepStatus.FAILED,
                    duration,
                    details=f"Source collection failed: {exc}",
                )
                submission = submission.transition_to(SubmissionStatus.FAILED)
                self._submission_store.update(submission)
                return self._record_failure(
                    submission_id=submission_id,
                    error_message=f"Source collection failed: {exc}",
                    audit=audit,
                    t_workflow_start=t_workflow_start,
                )
        else:
            audit.add_step(
                WorkflowStep.SOURCE_COLLECTION,
                StepStatus.SUCCESS,
                time.perf_counter() - t0,
                details="Source code previously populated.",
            )

        # Step 4: Automated Test Execution
        t0 = time.perf_counter()
        submission = submission.transition_to(SubmissionStatus.EVALUATING)
        self._submission_store.update(submission)

        test_results: tuple[TestCaseResult, ...]
        try:
            test_results = self._runner.run(assignment, source_code)
            audit.add_step(
                WorkflowStep.AUTOMATED_TESTING,
                StepStatus.SUCCESS,
                time.perf_counter() - t0,
                details=f"Executed {len(test_results)} test cases.",
            )
        except Exception as exc:
            duration = time.perf_counter() - t0
            # Infrastructure failure must NOT be attributed to student code
            infra_error_msg = f"Worker infrastructure execution failure: {exc}"
            logger.error(
                "Test execution worker crashed for submission '%s': %s",
                submission_id,
                exc,
                exc_info=True,
            )
            audit.add_step(
                WorkflowStep.AUTOMATED_TESTING,
                StepStatus.FAILED,
                duration,
                details=infra_error_msg,
            )
            submission = submission.transition_to(SubmissionStatus.FAILED)
            self._submission_store.update(submission)
            return self._record_failure(
                submission_id=submission_id,
                error_message=infra_error_msg,
                audit=audit,
                t_workflow_start=t_workflow_start,
            )

        # Step 5: Gemini Code Review (Failure-Tolerant)
        t0 = time.perf_counter()
        ai_feedback: str | None = None
        structured_feedback: CodeReviewFeedback | None = None
        ai_degraded = False

        if self._ai_reviewer is not None:
            try:
                if hasattr(self._ai_reviewer, "review_structured"):
                    structured_feedback = self._ai_reviewer.review_structured(
                        source_code=source_code,
                        assignment=assignment,
                        test_results=test_results,
                    )
                    if hasattr(self._ai_reviewer, "_format_feedback_as_markdown"):
                        ai_feedback = self._ai_reviewer._format_feedback_as_markdown(
                            structured_feedback
                        )
                    elif hasattr(structured_feedback, "summary"):
                        ai_feedback = structured_feedback.summary
                elif hasattr(self._ai_reviewer, "review"):
                    ai_feedback = self._ai_reviewer.review(source_code)

                audit.add_step(
                    WorkflowStep.GEMINI_CODE_REVIEW,
                    StepStatus.SUCCESS,
                    time.perf_counter() - t0,
                    details="AI code review completed successfully.",
                )
            except Exception as exc:
                ai_degraded = True
                logger.warning(
                    "AI code review failed for submission '%s': %s",
                    submission_id,
                    exc,
                )
                ai_feedback = f"[AI Review Unavailable: {exc}]"
                structured_feedback = None
                audit.add_step(
                    WorkflowStep.GEMINI_CODE_REVIEW,
                    StepStatus.DEGRADED,
                    time.perf_counter() - t0,
                    details=f"AI review degraded: {exc}",
                )
        else:
            audit.add_step(
                WorkflowStep.GEMINI_CODE_REVIEW,
                StepStatus.SKIPPED,
                time.perf_counter() - t0,
                details="No AI reviewer configured.",
            )

        # Step 6: Structured AI Response Validation
        t0 = time.perf_counter()
        if structured_feedback is not None:
            if isinstance(structured_feedback, CodeReviewFeedback):
                audit.add_step(
                    WorkflowStep.STRUCTURED_AI_VALIDATION,
                    StepStatus.SUCCESS,
                    time.perf_counter() - t0,
                    details="Structured review conforms to CodeReviewFeedback schema.",
                )
            else:
                try:
                    structured_feedback = CodeReviewFeedback.model_validate(
                        structured_feedback
                    )
                    audit.add_step(
                        WorkflowStep.STRUCTURED_AI_VALIDATION,
                        StepStatus.SUCCESS,
                        time.perf_counter() - t0,
                        details="Validated structured review via Pydantic.",
                    )
                except Exception as val_exc:
                    structured_feedback = None
                    audit.add_step(
                        WorkflowStep.STRUCTURED_AI_VALIDATION,
                        StepStatus.DEGRADED,
                        time.perf_counter() - t0,
                        details=f"Structured review validation failed: {val_exc}",
                    )
        elif ai_degraded:
            audit.add_step(
                WorkflowStep.STRUCTURED_AI_VALIDATION,
                StepStatus.DEGRADED,
                time.perf_counter() - t0,
                details="Structured validation skipped due to AI review degradation.",
            )
        else:
            audit.add_step(
                WorkflowStep.STRUCTURED_AI_VALIDATION,
                StepStatus.SKIPPED,
                time.perf_counter() - t0,
                details="No structured feedback to validate.",
            )

        # Step 7: Deterministic Grading
        # Objective marks are calculated strictly from verified test execution
        t0 = time.perf_counter()
        grading_report = grade_submission(assignment, test_results)
        audit.add_step(
            WorkflowStep.DETERMINISTIC_GRADING,
            StepStatus.SUCCESS,
            time.perf_counter() - t0,
            details=f"Calculated score: {grading_report.earned_points}/{grading_report.max_score} ({grading_report.percentage:.1f}%).",
        )

        # Step 8: Feedback Generation
        t0 = time.perf_counter()
        feedback_summary = FeedbackGenerator.generate(
            assignment=assignment,
            test_results=test_results,
            grading_report=grading_report,
            ai_review=ai_feedback,
            structured_feedback=structured_feedback,
        )
        audit.add_step(
            WorkflowStep.FEEDBACK_GENERATION,
            StepStatus.SUCCESS,
            time.perf_counter() - t0,
            details="Synthesized pedagogical feedback summary.",
        )

        # Step 9: Evaluation Report Creation
        t0 = time.perf_counter()
        report = EvaluationReport(
            status=EvaluationStatus.COMPLETED,
            grading_report=grading_report,
            submission_id=submission_id,
            test_results=test_results,
            ai_review=ai_feedback,
            structured_feedback=structured_feedback,
            feedback_summary=feedback_summary,
            workflow_audit=audit,
        )
        audit.add_step(
            WorkflowStep.REPORT_CREATION,
            StepStatus.SUCCESS,
            time.perf_counter() - t0,
            details=f"Created report '{report.evaluation_id}'.",
        )

        # Step 10: Database Persistence
        t0 = time.perf_counter()
        self._evaluation_store.save(report)
        submission = submission.transition_to(SubmissionStatus.COMPLETED)
        self._submission_store.update(submission)

        audit.add_step(
            WorkflowStep.DATABASE_PERSISTENCE,
            StepStatus.SUCCESS,
            time.perf_counter() - t0,
            details=f"Persisted report '{report.evaluation_id}' and updated submission to COMPLETED.",
        )

        # Finalize workflow audit duration
        audit.completed_at = datetime.now(timezone.utc)
        audit.total_duration_seconds = round(
            time.perf_counter() - t_workflow_start, 4
        )

        return report

    async def evaluate_async(
        self,
        submission_id: str,
        force_reevaluate: bool = False,
    ) -> EvaluationReport:
        """Run the evaluation workflow asynchronously without blocking the event loop."""
        return await asyncio.to_thread(
            self.evaluate_submission,
            submission_id,
            force_reevaluate=force_reevaluate,
        )

    def _collect_github_source_with_retry(
        self,
        source_reference: str,
    ) -> SourceBundle:
        """Retrieve GitHub source bundle with transient error retry."""
        last_exc: Exception | None = None
        for attempt in range(1, self._max_retries + 1):
            try:
                return SourceCollector.from_github(source_reference)
            except Exception as exc:
                last_exc = exc
                logger.warning(
                    "GitHub collection attempt %d/%d failed: %s",
                    attempt,
                    self._max_retries,
                    exc,
                )
                if attempt < self._max_retries:
                    time.sleep(self._retry_delay_seconds * attempt)

        raise RuntimeError(
            f"GitHub repository ingestion failed after {self._max_retries} attempts: {last_exc}"
        ) from last_exc

    def _record_failure(
        self,
        submission_id: str,
        error_message: str,
        audit: WorkflowExecutionAudit,
        t_workflow_start: float,
    ) -> EvaluationReport:
        """Assemble and persist a failed evaluation report."""
        audit.completed_at = datetime.now(timezone.utc)
        audit.total_duration_seconds = round(
            time.perf_counter() - t_workflow_start, 4
        )

        report = EvaluationReport(
            status=EvaluationStatus.FAILED,
            error_message=error_message,
            submission_id=submission_id,
            workflow_audit=audit,
        )
        self._evaluation_store.save(report)
        return report
