"""Tests for EvaluationOrchestrator multi-stage evaluation pipeline."""

import pytest

from evaluator.assignment import AssignmentDefinition, TestCaseDefinition
from evaluator.evaluation import EvaluationStatus
from evaluator.grading import TestCaseResult
from evaluator.runner import MockTestRunner
from evaluator.runners.process_runner import IsolatedProcessRunner
from evaluator.services.evaluation_orchestrator import EvaluationOrchestrator
from evaluator.stores.assignment_store import InMemoryAssignmentStore
from evaluator.stores.evaluation_store import InMemoryEvaluationStore
from evaluator.stores.submission_store import InMemorySubmissionStore
from evaluator.submission import (
    SubmissionMetadata,
    SubmissionRecord,
    SubmissionSource,
    SubmissionStatus,
)


class FakeAIReviewer:
    def __init__(self, feedback="Well-structured code.", should_fail=False):
        self.feedback = feedback
        self.should_fail = should_fail

    def review(self, source_code: str) -> str:
        if self.should_fail:
            raise RuntimeError("Gemini API rate limit exceeded")
        return self.feedback


@pytest.fixture
def assignment():
    return AssignmentDefinition(
        task_id="math_add",
        title="Addition Task",
        test_cases=(
            TestCaseDefinition(
                test_case_id="add_case",
                description="Check addition",
                points=10,
                assertion="add(4, 6) == 10",
            ),
        ),
    )


@pytest.fixture
def submission(assignment):
    return SubmissionRecord(
        metadata=SubmissionMetadata(student_id="student_99", task_id=assignment.task_id),
        source_type=SubmissionSource.FILE_UPLOAD,
        source_reference="upload:test",
        source_code="def add(a, b): return a + b\n",
        status=SubmissionStatus.RECEIVED,
    )


class TestEvaluationOrchestrator:
    def test_full_evaluation_pipeline_success(self, assignment, submission):
        assignment_store = InMemoryAssignmentStore()
        assignment_store.save(assignment)

        submission_store = InMemorySubmissionStore()
        submission_store.save(submission)

        evaluation_store = InMemoryEvaluationStore()
        runner = IsolatedProcessRunner(timeout_seconds=3.0)
        ai_reviewer = FakeAIReviewer("Clean function implementation.")

        orchestrator = EvaluationOrchestrator(
            submission_store=submission_store,
            assignment_store=assignment_store,
            evaluation_store=evaluation_store,
            runner=runner,
            ai_reviewer=ai_reviewer,
        )

        report = orchestrator.evaluate_submission(submission.submission_id)

        assert report.status is EvaluationStatus.COMPLETED
        assert report.grading_report.earned_points == 10
        assert report.grading_report.percentage == 100.0
        assert report.ai_review == "Clean function implementation."
        assert len(report.test_results) == 1
        assert report.test_results[0].passed is True

        # Verify submission status was updated to COMPLETED
        updated_sub = submission_store.get(submission.submission_id)
        assert updated_sub.status is SubmissionStatus.COMPLETED

        # Verify report stored in persistence
        stored_report = evaluation_store.get_by_submission(submission.submission_id)
        assert stored_report.evaluation_id == report.evaluation_id

    def test_evaluation_survives_ai_review_failure(self, assignment, submission):
        assignment_store = InMemoryAssignmentStore()
        assignment_store.save(assignment)

        submission_store = InMemorySubmissionStore()
        submission_store.save(submission)

        evaluation_store = InMemoryEvaluationStore()
        runner = IsolatedProcessRunner(timeout_seconds=3.0)
        failing_ai = FakeAIReviewer(should_fail=True)

        orchestrator = EvaluationOrchestrator(
            submission_store=submission_store,
            assignment_store=assignment_store,
            evaluation_store=evaluation_store,
            runner=runner,
            ai_reviewer=failing_ai,
        )

        report = orchestrator.evaluate_submission(submission.submission_id)

        # Objective evaluation must complete even when AI review fails
        assert report.status is EvaluationStatus.COMPLETED
        assert report.grading_report.earned_points == 10
        assert "[AI Review Unavailable" in report.ai_review

    def test_evaluation_fails_when_test_runner_crashes(self, assignment, submission):
        assignment_store = InMemoryAssignmentStore()
        assignment_store.save(assignment)

        submission_store = InMemorySubmissionStore()
        submission_store.save(submission)

        evaluation_store = InMemoryEvaluationStore()

        class ExplodingRunner:
            def run(self, assignment, code):
                raise RuntimeError("Runner container died")

        orchestrator = EvaluationOrchestrator(
            submission_store=submission_store,
            assignment_store=assignment_store,
            evaluation_store=evaluation_store,
            runner=ExplodingRunner(),
        )

        report = orchestrator.evaluate_submission(submission.submission_id)

        assert report.status is EvaluationStatus.FAILED
        assert "Runner container died" in report.error_message

        # Submission should be marked FAILED
        updated_sub = submission_store.get(submission.submission_id)
        assert updated_sub.status is SubmissionStatus.FAILED

