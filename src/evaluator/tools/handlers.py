"""Concrete tool handlers with authorization checks and store access."""

import uuid

from evaluator.exceptions import EntityNotFoundError
from evaluator.stores.assignment_store import AssignmentStore
from evaluator.stores.evaluation_store import EvaluationStore
from evaluator.stores.submission_store import SubmissionStore
from evaluator.tools.context import EvaluationSecurityContext
from evaluator.tools.schemas import (
    AssignmentDetailsOutput,
    GenerateStudentFeedbackInput,
    GetAssignmentDetailsInput,
    GetGradingReportInput,
    GetSubmissionSourceInput,
    GetTestResultsInput,
    GradingReportOutput,
    StudentFeedbackOutput,
    SubmissionSourceOutput,
    TestCaseOutcome,
    TestCaseSummary,
    TestResultsOutput,
)


class ToolAuthorizationError(PermissionError):
    """Raised when an agent attempts to access resources outside its security context."""


# ---------------------------------------------------------------------------
# Handler 1: get_assignment_details
# ---------------------------------------------------------------------------


def handle_get_assignment_details(
    input_data: GetAssignmentDetailsInput,
    context: EvaluationSecurityContext,
    assignment_store: AssignmentStore,
) -> AssignmentDetailsOutput:
    """Retrieve assignment details if authorized by security context."""
    if input_data.task_id != context.authorized_task_id:
        raise ToolAuthorizationError(
            f"Unauthorized: Agent is authorized only for task '{context.authorized_task_id}', "
            f"not '{input_data.task_id}'."
        )

    assignment = assignment_store.get(input_data.task_id)
    if not assignment:
        raise EntityNotFoundError(f"Assignment '{input_data.task_id}' not found.")

    test_summaries = [
        TestCaseSummary(
            test_case_id=tc.test_case_id,
            description=tc.description,
            points=tc.points,
        )
        for tc in assignment.test_cases
    ]

    return AssignmentDetailsOutput(
        task_id=assignment.task_id,
        title=assignment.title,
        max_score=assignment.max_score,
        test_cases=test_summaries,
    )


# ---------------------------------------------------------------------------
# Handler 2: get_submission_source
# ---------------------------------------------------------------------------


def handle_get_submission_source(
    input_data: GetSubmissionSourceInput,
    context: EvaluationSecurityContext,
    submission_store: SubmissionStore,
) -> SubmissionSourceOutput:
    """Retrieve student source code if authorized by security context."""
    if input_data.submission_id != context.authorized_submission_id:
        raise ToolAuthorizationError(
            f"Unauthorized: Agent is authorized only for submission '{context.authorized_submission_id}', "
            f"not '{input_data.submission_id}'."
        )

    submission = submission_store.get(input_data.submission_id)
    if not submission:
        raise EntityNotFoundError(f"Submission '{input_data.submission_id}' not found.")

    if not submission.source_code:
        raise ValueError(f"No source code available for submission '{input_data.submission_id}'.")

    return SubmissionSourceOutput(
        submission_id=submission.submission_id,
        task_id=submission.metadata.task_id,
        student_id=submission.metadata.student_id,
        source_type=submission.source_type.value,
        source_code=submission.source_code,
    )


# ---------------------------------------------------------------------------
# Handler 3: get_test_results
# ---------------------------------------------------------------------------


def handle_get_test_results(
    input_data: GetTestResultsInput,
    context: EvaluationSecurityContext,
    evaluation_store: EvaluationStore,
) -> TestResultsOutput:
    """Retrieve executed test outcomes for authorized submission."""
    if input_data.submission_id != context.authorized_submission_id:
        raise ToolAuthorizationError(
            f"Unauthorized: Agent is authorized only for submission '{context.authorized_submission_id}'."
        )

    report = evaluation_store.get_by_submission(input_data.submission_id)
    if not report:
        raise EntityNotFoundError(
            f"No evaluation report exists yet for submission '{input_data.submission_id}'."
        )

    outcomes = [
        TestCaseOutcome(
            test_case_id=tr.test_case_id,
            passed=tr.passed,
            message=tr.message,
        )
        for tr in report.test_results
    ]

    passed_count = sum(1 for o in outcomes if o.passed)
    failed_count = len(outcomes) - passed_count

    return TestResultsOutput(
        submission_id=input_data.submission_id,
        total_tests=len(outcomes),
        passed_count=passed_count,
        failed_count=failed_count,
        results=outcomes,
    )


# ---------------------------------------------------------------------------
# Handler 4: get_grading_report
# ---------------------------------------------------------------------------


def handle_get_grading_report(
    input_data: GetGradingReportInput,
    context: EvaluationSecurityContext,
    evaluation_store: EvaluationStore,
) -> GradingReportOutput:
    """Retrieve deterministic score report for authorized submission."""
    if input_data.submission_id != context.authorized_submission_id:
        raise ToolAuthorizationError(
            f"Unauthorized: Agent is authorized only for submission '{context.authorized_submission_id}'."
        )

    report = evaluation_store.get_by_submission(input_data.submission_id)
    if not report or not report.grading_report:
        raise EntityNotFoundError(
            f"Grading report not found for submission '{input_data.submission_id}'."
        )

    gr = report.grading_report
    return GradingReportOutput(
        submission_id=input_data.submission_id,
        earned_points=gr.earned_points,
        max_score=gr.max_score,
        passed_tests=gr.passed_tests,
        total_tests=gr.total_tests,
        percentage=gr.percentage,
    )


# ---------------------------------------------------------------------------
# Handler 5: generate_student_feedback
# ---------------------------------------------------------------------------


def handle_generate_student_feedback(
    input_data: GenerateStudentFeedbackInput,
    context: EvaluationSecurityContext,
) -> StudentFeedbackOutput:
    """Format and record student-facing pedagogical feedback."""
    if input_data.submission_id != context.authorized_submission_id:
        raise ToolAuthorizationError(
            f"Unauthorized: Agent is authorized only for submission '{context.authorized_submission_id}'."
        )

    feedback_id = f"fb_{uuid.uuid4().hex[:12]}"

    # Format feedback markdown
    lines = [
        f"## Assessment Feedback for Submission {input_data.submission_id}\n",
        f"**Summary:** {input_data.summary}\n",
    ]

    if input_data.strengths:
        lines.append("### Strengths")
        for s in input_data.strengths:
            lines.append(f"- {s}")
        lines.append("")

    if input_data.observations:
        lines.append("### Observations & Recommendations")
        for obs in input_data.observations:
            lines.append(f"#### [{obs.severity.upper()}] {obs.title} ({obs.category})")
            lines.append(f"{obs.explanation}")
            if obs.code_evidence:
                lines.append(f"\n```python\n{obs.code_evidence}\n```")
            if obs.suggested_fix:
                lines.append(f"\n*Recommendation:* {obs.suggested_fix}\n")

    lines.append(f"### Next Steps\n{input_data.pedagogical_guidance}")
    formatted_text = "\n".join(lines)

    return StudentFeedbackOutput(
        status="success",
        feedback_id=feedback_id,
        submission_id=input_data.submission_id,
        formatted_feedback=formatted_text,
    )

