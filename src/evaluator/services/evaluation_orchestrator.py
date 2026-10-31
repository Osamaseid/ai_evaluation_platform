"""Orchestration service coordinating code collection, test execution, deterministic grading, and AI review."""

import logging
from typing import Any

from evaluator.collector import SourceCollector
from evaluator.evaluation import EvaluationReport, EvaluationStatus
from evaluator.exceptions import EntityNotFoundError
from evaluator.grading import grade_submission
from evaluator.runner import Runner
from evaluator.stores.assignment_store import AssignmentStore
from evaluator.stores.evaluation_store import EvaluationStore
from evaluator.stores.submission_store import SubmissionStore
from evaluator.submission import SubmissionSource, SubmissionStatus

logger = logging.getLogger(__name__)


class EvaluationOrchestrator:
    """Coordinates the multi-stage evaluation pipeline."""

    def __init__(
        self,
        submission_store: SubmissionStore,
        assignment_store: AssignmentStore,
        evaluation_store: EvaluationStore,
        runner: Runner,
        ai_reviewer: Any | None = None,
    ) -> None:
        self._submission_store = submission_store
        self._assignment_store = assignment_store
        self._evaluation_store = evaluation_store
        self._runner = runner
        self._ai_reviewer = ai_reviewer

    def evaluate_submission(self, submission_id: str) -> EvaluationReport:
        """Run the end-to-end evaluation pipeline for a submission."""
        submission = self._submission_store.get(submission_id)
        if not submission:
            raise EntityNotFoundError(f"Submission '{submission_id}' not found.")

        assignment = self._assignment_store.get(submission.metadata.task_id)
        if not assignment:
            raise EntityNotFoundError(
                f"Assignment '{submission.metadata.task_id}' not found."
            )

        # Stage 1: Transition to VALIDATED
        submission = submission.transition_to(SubmissionStatus.VALIDATED)
        self._submission_store.update(submission)

        # Stage 2: Ensure source code is collected
        source_code = submission.source_code
        if not source_code:
            try:
                if submission.source_type == SubmissionSource.GITHUB:
                    bundle = SourceCollector.from_github(submission.source_reference)
                    source_code = bundle.get_concatenated_source()
                    submission = submission.with_source_code(source_code)
                    self._submission_store.update(submission)
                else:
                    raise ValueError(
                        f"No source code available for upload submission '{submission_id}'."
                    )
            except Exception as exc:
                submission = submission.transition_to(SubmissionStatus.FAILED)
                self._submission_store.update(submission)
                report = EvaluationReport(
                    status=EvaluationStatus.FAILED,
                    error_message=f"Source collection failed: {exc}",
                    submission_id=submission_id,
                )
                self._evaluation_store.save(report)
                return report

        # Stage 3: Transition to EVALUATING
        submission = submission.transition_to(SubmissionStatus.EVALUATING)
        self._submission_store.update(submission)

        # Stage 4: Execute tests via isolated runner
        try:
            test_results = self._runner.run(assignment, source_code)
            grading_report = grade_submission(assignment, test_results)
        except Exception as exc:
            submission = submission.transition_to(SubmissionStatus.FAILED)
            self._submission_store.update(submission)
            report = EvaluationReport(
                status=EvaluationStatus.FAILED,
                error_message=f"Test execution or grading failed: {exc}",
                submission_id=submission_id,
            )
            self._evaluation_store.save(report)
            return report

        # Stage 5: Qualitative AI Review (Failure-tolerant)
        ai_feedback: str | None = None
        if self._ai_reviewer:
            try:
                ai_feedback = self._ai_reviewer.review(source_code)
            except Exception as exc:
                logger.warning(
                    f"AI code review failed for submission '{submission_id}': {exc}"
                )
                ai_feedback = f"[AI Review Unavailable: {exc}]"

        # Stage 6: Complete submission & build final report
        submission = submission.transition_to(SubmissionStatus.COMPLETED)
        self._submission_store.update(submission)

        report = EvaluationReport(
            status=EvaluationStatus.COMPLETED,
            grading_report=grading_report,
            submission_id=submission_id,
            test_results=test_results,
            ai_review=ai_feedback,
        )
        self._evaluation_store.save(report)
        return report

