"""Evaluation execution and report retrieval endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status

from evaluator.api.dependencies.auth import get_current_user
from evaluator.api.schemas.evaluations import (
    EvaluationReportResponse,
    GradingReportSchema,
    TestCaseResultSchema,
)
from evaluator.api.schemas.rubrics import RubricEvaluationSchema
from evaluator.auth.models import UserAccount, UserRole
from evaluator.evaluation import EvaluationReport
from evaluator.exceptions import EntityNotFoundError
from evaluator.orchestration.exceptions import DuplicateProcessingError
from evaluator.runners.process_runner import IsolatedProcessRunner
from evaluator.services.evaluation_orchestrator import EvaluationOrchestrator
from evaluator.storage.submission_storage import ControlledFileStorage
from evaluator.stores.assignment_store import (
    AssignmentStore,
    InMemoryAssignmentStore,
)
from evaluator.stores.evaluation_store import (
    EvaluationStore,
    InMemoryEvaluationStore,
)
from evaluator.stores.submission_store import (
    InMemorySubmissionStore,
    SubmissionStore,
)

from evaluator.api.dependencies.stores import (
    shared_assignment_store,
    shared_evaluation_store,
    shared_file_storage,
    shared_submission_store,
)

router = APIRouter(prefix="/evaluations", tags=["evaluation"])


def get_evaluation_store() -> EvaluationStore:
    return shared_evaluation_store


def get_orchestrator() -> EvaluationOrchestrator:
    return EvaluationOrchestrator(
        submission_store=shared_submission_store,
        assignment_store=shared_assignment_store,
        evaluation_store=shared_evaluation_store,
        runner=IsolatedProcessRunner(),
        storage=shared_file_storage,
    )


def _to_response_schema(report: EvaluationReport) -> EvaluationReportResponse:
    submission = shared_submission_store.get(report.submission_id) if report.submission_id else None
    student_id = submission.metadata.student_id if submission else None
    task_id = submission.metadata.task_id if submission else None

    test_schemas = [
        TestCaseResultSchema(
            test_case_id=tr.test_case_id,
            passed=tr.passed,
            message=tr.message,
            execution_time_ms=getattr(tr, "execution_time_ms", 12),
            stdout=getattr(tr, "stdout", None),
            stderr=getattr(tr, "stderr", None),
        )
        for tr in report.test_results
    ]

    grading_schema = None
    if report.grading_report:
        grading_schema = GradingReportSchema(
            earned_points=report.grading_report.earned_points,
            max_score=report.grading_report.max_score,
            passed_tests=report.grading_report.passed_tests,
            total_tests=report.grading_report.total_tests,
            percentage=report.grading_report.percentage,
            score_percentage=report.grading_report.percentage,
            test_case_results=test_schemas,
        )

    rubric_schemas = [
        RubricEvaluationSchema(
            criterion_id=re.criterion_id,
            score=re.score,
            feedback=re.feedback,
        )
        for re in report.rubric_evaluations
    ]

    ai_payload = report.structured_feedback or report.ai_review
    if hasattr(ai_payload, "model_dump"):
        ai_payload = ai_payload.model_dump()
    elif hasattr(ai_payload, "dict"):
        ai_payload = ai_payload.dict()
    elif isinstance(ai_payload, str):
        ai_payload = {"summary": ai_payload, "strengths": [], "weaknesses": [], "observations": []}

    return EvaluationReportResponse(
        evaluation_id=report.evaluation_id,
        submission_id=report.submission_id,
        student_id=student_id,
        task_id=task_id,
        status=report.status.value,
        deterministic_score=report.grading_report.earned_points if report.grading_report else 0,
        max_score=report.grading_report.max_score if report.grading_report else 100,
        grading_report=grading_schema,
        test_results=test_schemas,
        rubric_evaluations=rubric_schemas,
        ai_review=ai_payload,
        error_message=report.error_message,
        evaluated_at=report.evaluated_at,
        manual_override_score=report.manual_override_score,
        instructor_notes=report.instructor_notes,
        reviewed_by=report.reviewed_by,
        reviewed_at=report.reviewed_at,
        started_at=report.evaluated_at,
        completed_at=report.evaluated_at,
    )


@router.post(
    "/run/{submission_id}",
    response_model=EvaluationReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Start central evaluation workflow for a submission",
)
def run_evaluation(
    submission_id: str,
    orchestrator: EvaluationOrchestrator = Depends(get_orchestrator),
) -> EvaluationReportResponse:
    """Execute the complete 10-step evaluation pipeline for a submission."""
    try:
        report = orchestrator.evaluate_submission(submission_id)
        return _to_response_schema(report)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except DuplicateProcessingError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.get(
    "/{evaluation_id}",
    response_model=EvaluationReportResponse,
    summary="Retrieve evaluation report by ID",
)
def get_evaluation(
    evaluation_id: str,
    store: EvaluationStore = Depends(get_evaluation_store),
) -> EvaluationReportResponse:
    """Retrieve full evaluation report including grading and test results."""
    report = store.get(evaluation_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"EvaluationReport '{evaluation_id}' not found.",
        )
    return _to_response_schema(report)


@router.get(
    "/by-submission/{submission_id}",
    response_model=EvaluationReportResponse,
    summary="Retrieve evaluation report by submission ID",
)
def get_evaluation_by_submission(
    submission_id: str,
    store: EvaluationStore = Depends(get_evaluation_store),
) -> EvaluationReportResponse:
    """Retrieve evaluation report associated with a given submission."""
    report = store.get_by_submission(submission_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No evaluation report found for submission '{submission_id}'.",
        )
    return _to_response_schema(report)


@router.get(
    "/{evaluation_id}/status",
    summary="Retrieve evaluation status and timing",
)
def get_evaluation_status(
    evaluation_id: str,
    store: EvaluationStore = Depends(get_evaluation_store),
) -> dict:
    """Retrieve high-level status and execution timing for an evaluation."""
    report = store.get(evaluation_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"EvaluationReport '{evaluation_id}' not found.",
        )

    duration = 0.0
    if report.workflow_audit:
        duration = report.workflow_audit.total_duration_seconds

    return {
        "evaluation_id": report.evaluation_id,
        "submission_id": report.submission_id,
        "status": report.status.value,
        "duration_seconds": duration,
        "evaluated_at": report.evaluated_at,
    }


@router.get(
    "/{evaluation_id}/tests",
    response_model=list[TestCaseResultSchema],
    summary="Retrieve test results breakdown",
)
def get_evaluation_tests(
    evaluation_id: str,
    store: EvaluationStore = Depends(get_evaluation_store),
) -> list[TestCaseResultSchema]:
    """Retrieve verified individual test case outcomes."""
    report = store.get(evaluation_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"EvaluationReport '{evaluation_id}' not found.",
        )

    return [
        TestCaseResultSchema(
            test_case_id=tr.test_case_id,
            passed=tr.passed,
            message=tr.message,
        )
        for tr in report.test_results
    ]


@router.get(
    "/{evaluation_id}/ai-feedback",
    summary="Retrieve AI code review and pedagogical advice",
)
def get_ai_feedback(
    evaluation_id: str,
    store: EvaluationStore = Depends(get_evaluation_store),
) -> dict:
    """Retrieve AI qualitative analysis, strengths, observations, and advice."""
    report = store.get(evaluation_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"EvaluationReport '{evaluation_id}' not found.",
        )

    structured_dict = None
    if report.structured_feedback:
        if hasattr(report.structured_feedback, "model_dump"):
            structured_dict = report.structured_feedback.model_dump()
        else:
            structured_dict = report.structured_feedback

    return {
        "evaluation_id": report.evaluation_id,
        "ai_review": report.ai_review,
        "structured_feedback": structured_dict,
    }


@router.get(
    "/{evaluation_id}/report",
    summary="Retrieve final synthesized report and feedback summary",
)
def get_final_report_summary(
    evaluation_id: str,
    store: EvaluationStore = Depends(get_evaluation_store),
) -> dict:
    """Retrieve comprehensive pedagogical markdown summary report."""
    report = store.get(evaluation_id)
    if not report:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"EvaluationReport '{evaluation_id}' not found.",
        )

    return {
        "evaluation_id": report.evaluation_id,
        "submission_id": report.submission_id,
        "status": report.status.value,
        "earned_points": report.grading_report.earned_points if report.grading_report else None,
        "max_score": report.grading_report.max_score if report.grading_report else None,
        "percentage": report.grading_report.percentage if report.grading_report else None,
        "feedback_summary": report.feedback_summary or report.ai_review,
        "evaluated_at": report.evaluated_at,
    }

