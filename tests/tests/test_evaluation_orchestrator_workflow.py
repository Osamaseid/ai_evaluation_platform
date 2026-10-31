"""Comprehensive unit and integration tests for central Evaluation Agent orchestration workflow.

Verifies:
1. Complete 10-step workflow execution with audit logging.
2. Prevention of duplicate / re-entrant processing on active evaluations.
3. Idempotent return of cached report for already-completed evaluations.
4. Independent test results and deterministic grading (AI failures do NOT erase test marks).
5. Clean distinction between worker infrastructure failures and student code failures.
6. Structured AI response validation and graceful degradation on schema mismatches.
7. Asynchronous evaluation support via evaluate_async.
8. Source-code collection from GitHub with retry handling.
9. Comprehensive feedback synthesis combining test cases and pedagogical guidance.
"""

from datetime import datetime, timezone
import inspect
from unittest.mock import patch
import pytest

from evaluator.ai_reviewer import (
    CodeObservation,
    CodeReviewFeedback,
    GeminiReviewError,
    IssueSeverity,
    ReviewCategory,
)
from evaluator.assignment import AssignmentDefinition, TestCaseDefinition
from evaluator.collector import CollectionError, SourceBundle, SourceFile
from evaluator.evaluation import EvaluationReport, EvaluationStatus
from evaluator.exceptions import EntityNotFoundError
from evaluator.grading import TestCaseResult
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


# ---------------------------------------------------------------------------
# Test Fixtures & Fakes
# ---------------------------------------------------------------------------


class FakeStructuredAIReviewer:
    """Mock reviewer returning structured Pydantic CodeReviewFeedback."""

    def __init__(
        self,
        feedback: CodeReviewFeedback | None = None,
        raise_error: Exception | None = None,
    ) -> None:
        self.raise_error = raise_error
        self.feedback = feedback or CodeReviewFeedback(
            summary="Clean and idiomatic calculator functions.",
            strengths=["Well-named parameters", "Correct mathematical operations"],
            observations=[
                CodeObservation(
                    category=ReviewCategory.CODE_QUALITY,
                    severity=IssueSeverity.INFO,
                    title="Docstring formatting",
                    explanation="Consider adding Google-style docstrings with Args and Returns.",
                    code_evidence="def add(a, b): return a + b",
                    line_number=1,
                    suggested_fix="def add(a: float, b: float) -> float:\n    \"\"\"Add two numbers.\"\"\"",
                )
            ],
            pedagogical_guidance="Great start! Next, try adding type annotations and unit test edge cases.",
        )

    def review_structured(
        self,
        source_code: str,
        assignment=None,
        test_results=None,
    ) -> CodeReviewFeedback:
        if self.raise_error:
            raise self.raise_error
        return self.feedback

    def _format_feedback_as_markdown(self, feedback: CodeReviewFeedback) -> str:
        return f"### Summary\n{feedback.summary}"


class MockRunner(Runner):
    """Configurable runner returning fixed test results or raising an infra crash."""

    def __init__(
        self,
        results: tuple[TestCaseResult, ...] | None = None,
        crash_error: Exception | None = None,
    ) -> None:
        self.results = results or ()
        self.crash_error = crash_error

    def run(
        self,
        assignment: AssignmentDefinition,
        source_code: str,
    ) -> tuple[TestCaseResult, ...]:
        if self.crash_error:
            raise self.crash_error
        return self.results


@pytest.fixture
def sample_assignment() -> AssignmentDefinition:
    return AssignmentDefinition(
        task_id="math_arithmetic",
        title="Basic Arithmetic Functions",
        test_cases=(
            TestCaseDefinition(
                test_case_id="tc_add",
                description="Verify 2 + 2 == 4",
                points=5,
                assertion="add(2, 2) == 4",
            ),
            TestCaseDefinition(
                test_case_id="tc_sub",
                description="Verify 10 - 3 == 7",
                points=5,
                assertion="sub(10, 3) == 7",
            ),
        ),
    )


@pytest.fixture
def sample_submission(sample_assignment: AssignmentDefinition) -> SubmissionRecord:
    return SubmissionRecord(
        metadata=SubmissionMetadata(
            student_id="student_123",
            task_id=sample_assignment.task_id,
        ),
        source_type=SubmissionSource.FILE_UPLOAD,
        source_reference="upload:solution.py",
        source_code="def add(a, b): return a + b\ndef sub(a, b): return a - b\n",
        status=SubmissionStatus.RECEIVED,
    )


# ---------------------------------------------------------------------------
# Workflow Execution & 10-Step Pipeline Tests
# ---------------------------------------------------------------------------


class TestComplete10StepPipeline:
    def test_full_10_step_workflow_success(
        self,
        sample_assignment: AssignmentDefinition,
        sample_submission: SubmissionRecord,
    ):
        """Verify the complete 10-step pipeline runs successfully with structured audit records."""
        assignment_store = InMemoryAssignmentStore()
        assignment_store.save(sample_assignment)

        submission_store = InMemorySubmissionStore()
        submission_store.save(sample_submission)

        evaluation_store = InMemoryEvaluationStore()

        runner = MockRunner(
            results=(
                TestCaseResult("tc_add", passed=True, message="Passed"),
                TestCaseResult("tc_sub", passed=True, message="Passed"),
            )
        )
        ai_reviewer = FakeStructuredAIReviewer()

        orchestrator = EvaluationOrchestrator(
            submission_store=submission_store,
            assignment_store=assignment_store,
            evaluation_store=evaluation_store,
            runner=runner,
            ai_reviewer=ai_reviewer,
        )

        report = orchestrator.evaluate_submission(sample_submission.submission_id)

        # 1. Report outcome assertions
        assert report.status is EvaluationStatus.COMPLETED
        assert report.grading_report is not None
        assert report.grading_report.earned_points == 10
        assert report.grading_report.percentage == 100.0
        assert report.grading_report.passed_tests == 2
        assert report.grading_report.total_tests == 2
        assert report.structured_feedback is not None
        assert report.structured_feedback.summary == "Clean and idiomatic calculator functions."
        assert "Evaluation Feedback: Basic Arithmetic Functions" in report.feedback_summary

        # 2. Persistence assertions
        stored_submission = submission_store.get(sample_submission.submission_id)
        assert stored_submission is not None
        assert stored_submission.status is SubmissionStatus.COMPLETED

        stored_report = evaluation_store.get_by_submission(sample_submission.submission_id)
        assert stored_report is not None
        assert stored_report.evaluation_id == report.evaluation_id

        # 3. Audit trail assertions: All 10 discrete workflow steps must be audited
        audit = report.workflow_audit
        assert isinstance(audit, WorkflowExecutionAudit)
        assert audit.submission_id == sample_submission.submission_id
        assert audit.task_id == sample_assignment.task_id
        assert audit.completed_at is not None
        assert audit.total_duration_seconds >= 0.0

        step_map = {step.step: step for step in audit.steps}
        assert WorkflowStep.SUBMISSION_VALIDATION in step_map
        assert step_map[WorkflowStep.SUBMISSION_VALIDATION].status is StepStatus.SUCCESS

        assert WorkflowStep.ASSIGNMENT_RETRIEVAL in step_map
        assert step_map[WorkflowStep.ASSIGNMENT_RETRIEVAL].status is StepStatus.SUCCESS

        assert WorkflowStep.SOURCE_COLLECTION in step_map
        assert step_map[WorkflowStep.SOURCE_COLLECTION].status is StepStatus.SUCCESS

        assert WorkflowStep.AUTOMATED_TESTING in step_map
        assert step_map[WorkflowStep.AUTOMATED_TESTING].status is StepStatus.SUCCESS

        assert WorkflowStep.GEMINI_CODE_REVIEW in step_map
        assert step_map[WorkflowStep.GEMINI_CODE_REVIEW].status is StepStatus.SUCCESS

        assert WorkflowStep.STRUCTURED_AI_VALIDATION in step_map
        assert step_map[WorkflowStep.STRUCTURED_AI_VALIDATION].status is StepStatus.SUCCESS

        assert WorkflowStep.DETERMINISTIC_GRADING in step_map
        assert step_map[WorkflowStep.DETERMINISTIC_GRADING].status is StepStatus.SUCCESS

        assert WorkflowStep.FEEDBACK_GENERATION in step_map
        assert step_map[WorkflowStep.FEEDBACK_GENERATION].status is StepStatus.SUCCESS

        assert WorkflowStep.REPORT_CREATION in step_map
        assert step_map[WorkflowStep.REPORT_CREATION].status is StepStatus.SUCCESS

        assert WorkflowStep.DATABASE_PERSISTENCE in step_map
        assert step_map[WorkflowStep.DATABASE_PERSISTENCE].status is StepStatus.SUCCESS


class TestDuplicateProcessingAndIdempotency:
    def test_evaluating_submission_raises_duplicate_processing_error(
        self,
        sample_assignment: AssignmentDefinition,
        sample_submission: SubmissionRecord,
    ):
        """Re-entry prevention: cannot evaluate a submission that is actively EVALUATING."""
        assignment_store = InMemoryAssignmentStore()
        assignment_store.save(sample_assignment)

        submission_store = InMemorySubmissionStore()
        # Put submission in EVALUATING state
        evaluating_sub = sample_submission.transition_to(
            SubmissionStatus.VALIDATED
        ).transition_to(SubmissionStatus.EVALUATING)
        submission_store.save(evaluating_sub)

        evaluation_store = InMemoryEvaluationStore()
        orchestrator = EvaluationOrchestrator(
            submission_store=submission_store,
            assignment_store=assignment_store,
            evaluation_store=evaluation_store,
            runner=MockRunner(),
        )

        with pytest.raises(DuplicateProcessingError) as exc_info:
            orchestrator.evaluate_submission(evaluating_sub.submission_id)

        assert "is currently being evaluated" in str(exc_info.value)

    def test_completed_submission_returns_cached_report_idempotently(
        self,
        sample_assignment: AssignmentDefinition,
        sample_submission: SubmissionRecord,
    ):
        """Idempotency: evaluating an already COMPLETED submission returns cached report without re-executing."""
        assignment_store = InMemoryAssignmentStore()
        assignment_store.save(sample_assignment)

        submission_store = InMemorySubmissionStore()
        submission_store.save(sample_submission)

        evaluation_store = InMemoryEvaluationStore()
        runner = MockRunner(
            results=(
                TestCaseResult("tc_add", passed=True),
                TestCaseResult("tc_sub", passed=True),
            )
        )

        orchestrator = EvaluationOrchestrator(
            submission_store=submission_store,
            assignment_store=assignment_store,
            evaluation_store=evaluation_store,
            runner=runner,
        )

        # First run creates the report
        first_report = orchestrator.evaluate_submission(sample_submission.submission_id)
        assert first_report.status is EvaluationStatus.COMPLETED

        # Mutate runner to raise an error to prove it is NOT called again
        runner.crash_error = RuntimeError("Should not be invoked on cached submission")

        # Second run should return existing report idempotently
        second_report = orchestrator.evaluate_submission(sample_submission.submission_id)
        assert second_report.evaluation_id == first_report.evaluation_id
        assert second_report.status is EvaluationStatus.COMPLETED


# ---------------------------------------------------------------------------
# Independent Results & Partial Failure Tests
# ---------------------------------------------------------------------------


class TestIndependentResultsAndDegradation:
    def test_gemini_api_failure_does_not_erase_successful_test_results(
        self,
        sample_assignment: AssignmentDefinition,
        sample_submission: SubmissionRecord,
    ):
        """CRITICAL: An AI reviewer crash/rate-limit must never erase verified deterministic test marks."""
        assignment_store = InMemoryAssignmentStore()
        assignment_store.save(sample_assignment)

        submission_store = InMemorySubmissionStore()
        submission_store.save(sample_submission)

        evaluation_store = InMemoryEvaluationStore()
        runner = MockRunner(
            results=(
                TestCaseResult("tc_add", passed=True),
                TestCaseResult("tc_sub", passed=True),
            )
        )
        failing_ai = FakeStructuredAIReviewer(
            raise_error=GeminiReviewError("Gemini API HTTP 503: Service Unavailable")
        )

        orchestrator = EvaluationOrchestrator(
            submission_store=submission_store,
            assignment_store=assignment_store,
            evaluation_store=evaluation_store,
            runner=runner,
            ai_reviewer=failing_ai,
        )

        report = orchestrator.evaluate_submission(sample_submission.submission_id)

        # Grade is 100% despite AI failure
        assert report.status is EvaluationStatus.COMPLETED
        assert report.grading_report.earned_points == 10
        assert report.grading_report.percentage == 100.0
        assert "[AI Review Unavailable" in report.ai_review
        assert report.structured_feedback is None

        # Verify audit records the degradation
        gemini_step = report.workflow_audit.get_step(WorkflowStep.GEMINI_CODE_REVIEW)
        assert gemini_step is not None
        assert gemini_step.status is StepStatus.DEGRADED
        assert "Service Unavailable" in gemini_step.details

        # Submission still transitions to COMPLETED
        updated_sub = submission_store.get(sample_submission.submission_id)
        assert updated_sub.status is SubmissionStatus.COMPLETED

    def test_malformed_ai_response_degrades_gracefully(
        self,
        sample_assignment: AssignmentDefinition,
        sample_submission: SubmissionRecord,
    ):
        """If AI review returns invalid schema, structured validation degrades gracefully."""
        assignment_store = InMemoryAssignmentStore()
        assignment_store.save(sample_assignment)

        submission_store = InMemorySubmissionStore()
        submission_store.save(sample_submission)

        evaluation_store = InMemoryEvaluationStore()
        runner = MockRunner(
            results=(
                TestCaseResult("tc_add", passed=True),
                TestCaseResult("tc_sub", passed=True),
            )
        )

        class MalformedAIReviewer:
            def review_structured(self, *args, **kwargs):
                return {"invalid_key": "not a valid CodeReviewFeedback object"}

        orchestrator = EvaluationOrchestrator(
            submission_store=submission_store,
            assignment_store=assignment_store,
            evaluation_store=evaluation_store,
            runner=runner,
            ai_reviewer=MalformedAIReviewer(),
        )

        report = orchestrator.evaluate_submission(sample_submission.submission_id)

        assert report.status is EvaluationStatus.COMPLETED
        assert report.grading_report.earned_points == 10
        assert report.structured_feedback is None

        val_step = report.workflow_audit.get_step(WorkflowStep.STRUCTURED_AI_VALIDATION)
        assert val_step is not None
        assert val_step.status is StepStatus.DEGRADED


# ---------------------------------------------------------------------------
# Infrastructure vs Student Code Failure Distinction
# ---------------------------------------------------------------------------


class TestInfrastructureVsStudentCodeFailure:
    def test_student_code_failure_produces_completed_evaluation_with_zero_marks(
        self,
        sample_assignment: AssignmentDefinition,
        sample_submission: SubmissionRecord,
    ):
        """Student code failing tests is a valid pedagogical evaluation, not an infrastructure error."""
        assignment_store = InMemoryAssignmentStore()
        assignment_store.save(sample_assignment)

        submission_store = InMemorySubmissionStore()
        submission_store.save(sample_submission)

        evaluation_store = InMemoryEvaluationStore()
        # Student code failed all assertions
        runner = MockRunner(
            results=(
                TestCaseResult("tc_add", passed=False, message="AssertionError: 5 != 4"),
                TestCaseResult("tc_sub", passed=False, message="ZeroDivisionError: division by zero"),
            )
        )
        ai_reviewer = FakeStructuredAIReviewer()

        orchestrator = EvaluationOrchestrator(
            submission_store=submission_store,
            assignment_store=assignment_store,
            evaluation_store=evaluation_store,
            runner=runner,
            ai_reviewer=ai_reviewer,
        )

        report = orchestrator.evaluate_submission(sample_submission.submission_id)

        # Evaluation is COMPLETED, not FAILED
        assert report.status is EvaluationStatus.COMPLETED
        assert report.grading_report.earned_points == 0
        assert report.grading_report.passed_tests == 0
        assert report.grading_report.percentage == 0.0

        testing_step = report.workflow_audit.get_step(WorkflowStep.AUTOMATED_TESTING)
        assert testing_step.status is StepStatus.SUCCESS

    def test_worker_infrastructure_crash_is_distinct_and_marks_evaluation_failed(
        self,
        sample_assignment: AssignmentDefinition,
        sample_submission: SubmissionRecord,
    ):
        """A container/worker crash must be presented as infrastructure error, never blamed on student code."""
        assignment_store = InMemoryAssignmentStore()
        assignment_store.save(sample_assignment)

        submission_store = InMemorySubmissionStore()
        submission_store.save(sample_submission)

        evaluation_store = InMemoryEvaluationStore()
        runner = MockRunner(
            crash_error=RuntimeError("Docker daemon socket connection refused on host /var/run/docker.sock")
        )

        orchestrator = EvaluationOrchestrator(
            submission_store=submission_store,
            assignment_store=assignment_store,
            evaluation_store=evaluation_store,
            runner=runner,
        )

        report = orchestrator.evaluate_submission(sample_submission.submission_id)

        # Evaluation itself is marked FAILED due to system error
        assert report.status is EvaluationStatus.FAILED
        assert report.grading_report is None
        assert "Worker infrastructure execution failure" in report.error_message
        assert "Docker daemon socket connection refused" in report.error_message

        # Submission marked FAILED
        updated_sub = submission_store.get(sample_submission.submission_id)
        assert updated_sub.status is SubmissionStatus.FAILED

        # Audit captures runner crash
        testing_step = report.workflow_audit.get_step(WorkflowStep.AUTOMATED_TESTING)
        assert testing_step.status is StepStatus.FAILED
        assert "Worker infrastructure execution failure" in testing_step.details


# ---------------------------------------------------------------------------
# Asynchronous Execution & Source Collection Tests
# ---------------------------------------------------------------------------


class TestAsyncAndSourceCollection:
    def test_evaluate_async_definition_and_execution(
        self,
        sample_assignment: AssignmentDefinition,
        sample_submission: SubmissionRecord,
    ):
        """Asynchronous evaluate_async executes non-blockingly via asyncio.to_thread delegation."""
        assignment_store = InMemoryAssignmentStore()
        assignment_store.save(sample_assignment)

        submission_store = InMemorySubmissionStore()
        submission_store.save(sample_submission)

        evaluation_store = InMemoryEvaluationStore()
        runner = MockRunner(
            results=(
                TestCaseResult("tc_add", passed=True),
                TestCaseResult("tc_sub", passed=True),
            )
        )

        orchestrator = EvaluationOrchestrator(
            submission_store=submission_store,
            assignment_store=assignment_store,
            evaluation_store=evaluation_store,
            runner=runner,
        )

        # Verify coroutine interface
        assert inspect.iscoroutinefunction(orchestrator.evaluate_async)

        async def fake_to_thread(fn, *args, **kwargs):
            return fn(*args, **kwargs)

        with patch("asyncio.to_thread", side_effect=fake_to_thread):
            coro = orchestrator.evaluate_async(sample_submission.submission_id)
            try:
                coro.send(None)
            except StopIteration as exc:
                report = exc.value
                assert report.status is EvaluationStatus.COMPLETED
                assert report.grading_report.earned_points == 10

    def test_github_source_collection_failure_fails_gracefully(
        self,
        sample_assignment: AssignmentDefinition,
    ):
        """When GitHub source collection fails after retries, workflow records FAILED report."""
        assignment_store = InMemoryAssignmentStore()
        assignment_store.save(sample_assignment)

        submission_store = InMemorySubmissionStore()
        github_sub = SubmissionRecord(
            metadata=SubmissionMetadata(
                student_id="student_git",
                task_id=sample_assignment.task_id,
            ),
            source_type=SubmissionSource.GITHUB,
            source_reference="https://github.com/mock_org/mock_repo",
            source_code=None,  # triggers ingestion
            status=SubmissionStatus.RECEIVED,
        )
        submission_store.save(github_sub)

        evaluation_store = InMemoryEvaluationStore()
        orchestrator = EvaluationOrchestrator(
            submission_store=submission_store,
            assignment_store=assignment_store,
            evaluation_store=evaluation_store,
            runner=MockRunner(),
            max_retries=2,
            retry_delay_seconds=0.001,
        )

        with patch.object(
            orchestrator,
            "_collect_github_source_with_retry",
            side_effect=CollectionError("Simulated connection timeout fetching git repository"),
        ):
            report = orchestrator.evaluate_submission(github_sub.submission_id)

        assert report.status is EvaluationStatus.FAILED
        assert "Source collection failed" in report.error_message

        updated_sub = submission_store.get(github_sub.submission_id)
        assert updated_sub.status is SubmissionStatus.FAILED

        step = report.workflow_audit.get_step(WorkflowStep.SOURCE_COLLECTION)
        assert step is not None
        assert step.status is StepStatus.FAILED

    def test_github_source_collection_success_triggers_runner_and_grading(
        self,
        sample_assignment: AssignmentDefinition,
    ):
        """Successful GitHub source ingestion updates submission source code and evaluates."""
        assignment_store = InMemoryAssignmentStore()
        assignment_store.save(sample_assignment)

        submission_store = InMemorySubmissionStore()
        github_sub = SubmissionRecord(
            metadata=SubmissionMetadata(
                student_id="student_git_ok",
                task_id=sample_assignment.task_id,
            ),
            source_type=SubmissionSource.GITHUB,
            source_reference="https://github.com/example/calculator",
            source_code=None,
            status=SubmissionStatus.RECEIVED,
        )
        submission_store.save(github_sub)

        evaluation_store = InMemoryEvaluationStore()
        runner = MockRunner(
            results=(
                TestCaseResult("tc_add", passed=True),
                TestCaseResult("tc_sub", passed=True),
            )
        )
        orchestrator = EvaluationOrchestrator(
            submission_store=submission_store,
            assignment_store=assignment_store,
            evaluation_store=evaluation_store,
            runner=runner,
        )

        mock_bundle = SourceBundle(
            files=(
                SourceFile(relative_path="calc.py", content="def add(a, b): return a + b\ndef sub(a, b): return a - b"),
            )
        )

        with patch("evaluator.collector.SourceCollector.from_github", return_value=mock_bundle):
            report = orchestrator.evaluate_submission(github_sub.submission_id)

        assert report.status is EvaluationStatus.COMPLETED
        assert report.grading_report.earned_points == 10

        # Check that submission was updated with source code
        updated_sub = submission_store.get(github_sub.submission_id)
        assert updated_sub.source_code is not None
        assert "def add(a, b):" in updated_sub.source_code
        assert updated_sub.status is SubmissionStatus.COMPLETED

        step = report.workflow_audit.get_step(WorkflowStep.SOURCE_COLLECTION)
        assert step is not None
        assert step.status is StepStatus.SUCCESS


# ---------------------------------------------------------------------------
# Feedback Synthesis Tests
# ---------------------------------------------------------------------------


class TestFeedbackSynthesis:
    def test_feedback_generator_produces_rich_markdown(
        self,
        sample_assignment: AssignmentDefinition,
    ):
        """Verify FeedbackGenerator combines test results and structured observations into markdown."""
        test_results = (
            TestCaseResult("tc_add", passed=True),
            TestCaseResult("tc_sub", passed=False, message="Expected 7 but received -7"),
        )
        from evaluator.grading import grade_submission

        grading_report = grade_submission(sample_assignment, test_results)
        structured_feedback = CodeReviewFeedback(
            summary="Good structural attempt.",
            strengths=["Consistent spacing"],
            observations=[
                CodeObservation(
                    category=ReviewCategory.POTENTIAL_BUG,
                    severity=IssueSeverity.WARNING,
                    title="Operand order reversed",
                    explanation="In sub(a, b), returning b - a reverses subtraction operands.",
                    code_evidence="return b - a",
                    line_number=2,
                    suggested_fix="return a - b",
                )
            ],
            pedagogical_guidance="Check operand ordering in noncommutative operations.",
        )

        markdown = FeedbackGenerator.generate(
            assignment=sample_assignment,
            test_results=test_results,
            grading_report=grading_report,
            structured_feedback=structured_feedback,
        )

        assert "# Evaluation Feedback: Basic Arithmetic Functions" in markdown
        assert "**Score**: 5 / 10 (50.0%)" in markdown
        assert "[PASS] **`tc_add`**" in markdown
        assert "[FAIL] **`tc_sub`**" in markdown
        assert "Expected 7 but received -7" in markdown
        assert "Good structural attempt." in markdown
        assert "[WARNING] Operand order reversed" in markdown
        assert "return a - b" in markdown
