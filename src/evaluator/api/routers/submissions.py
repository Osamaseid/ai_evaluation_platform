"""Submission management and evaluation intake endpoints."""

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from evaluator.api.schemas.submissions import (
    GitHubSubmissionRequest,
    SubmissionResponse,
    SubmissionStatusResponse,
)
from evaluator.exceptions import (
    DangerousFileTypeError,
    DeadlineExceededError,
    EntityNotFoundError,
    FileSizeExceededError,
    PathTraversalError,
    RepositoryAccessError,
    RepositoryNotFoundError,
    SecurityValidationError,
    ZipBombError,
)
from evaluator.services.evaluation_orchestrator import EvaluationOrchestrator
from evaluator.services.submission_service import SubmissionService
from evaluator.storage.submission_storage import ControlledFileStorage
from evaluator.stores.assignment_store import InMemoryAssignmentStore
from evaluator.stores.evaluation_store import InMemoryEvaluationStore
from evaluator.stores.student_store import InMemoryStudentStore
from evaluator.stores.submission_store import InMemorySubmissionStore
from evaluator.submission import SubmissionRecord

router = APIRouter(prefix="/submissions", tags=["submissions"])

# ---------------------------------------------------------------------------
# Shared application dependencies
# ---------------------------------------------------------------------------
_submission_store = InMemorySubmissionStore()
_assignment_store = InMemoryAssignmentStore()
_student_store = InMemoryStudentStore()
_evaluation_store = InMemoryEvaluationStore()
_file_storage = ControlledFileStorage()


def get_submission_service() -> SubmissionService:
    """Provide submission service with configured storage."""
    return SubmissionService(
        submission_store=_submission_store,
        assignment_store=_assignment_store,
        student_store=_student_store,
        storage=_file_storage,
    )


def get_evaluation_orchestrator() -> EvaluationOrchestrator:
    """Provide central evaluation orchestrator."""
    from evaluator.runners.process_runner import IsolatedProcessRunner

    return EvaluationOrchestrator(
        submission_store=_submission_store,
        assignment_store=_assignment_store,
        evaluation_store=_evaluation_store,
        runner=IsolatedProcessRunner(),
        storage=_file_storage,
    )


def _to_submission_response(record: SubmissionRecord) -> SubmissionResponse:
    """Translate domain SubmissionRecord to Pydantic SubmissionResponse schema."""
    return SubmissionResponse(
        submission_id=record.submission_id,
        student_id=record.metadata.student_id,
        task_id=record.metadata.task_id,
        source_type=record.source_type.value,
        source_reference=record.source_reference,
        status=record.status.value,
        submitted_at=record.submitted_at,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "/github",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit GitHub repository URL",
)
def submit_github_repo(
    request: GitHubSubmissionRequest,
    service: SubmissionService = Depends(get_submission_service),
) -> SubmissionResponse:
    """Register a GitHub repository URL submission."""
    try:
        record = service.submit_github(
            student_id=request.student_id,
            task_id=request.task_id,
            github_url=request.github_url,
            branch=request.branch,
        )
        return _to_submission_response(record)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except DeadlineExceededError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except (RepositoryNotFoundError, RepositoryAccessError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post(
    "/upload",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit source code file or archive upload",
)
def submit_file_upload(
    file: UploadFile = File(..., description="Single .py script or .zip archive"),
    student_id: str = Form(..., min_length=1, max_length=50),
    task_id: str = Form(..., min_length=1, max_length=50),
    service: SubmissionService = Depends(get_submission_service),
) -> SubmissionResponse:
    """Register a direct source file or project zip archive upload."""
    content = file.file.read()
    filename = file.filename or "solution.py"

    try:
        record = service.submit_file_upload(
            student_id=student_id,
            task_id=task_id,
            filename=filename,
            content=content,
        )
        return _to_submission_response(record)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except DeadlineExceededError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except FileSizeExceededError as exc:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc))
    except (DangerousFileTypeError, ZipBombError, PathTraversalError, SecurityValidationError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get(
    "/{submission_id}",
    response_model=SubmissionResponse,
    summary="Get submission details",
)
def get_submission(
    submission_id: str,
    service: SubmissionService = Depends(get_submission_service),
) -> SubmissionResponse:
    """Retrieve details for a submission."""
    try:
        record = service.get_submission(submission_id)
        return _to_submission_response(record)
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get(
    "/{submission_id}/status",
    response_model=SubmissionStatusResponse,
    summary="Get submission status and transition audit history",
)
def get_submission_status(
    submission_id: str,
    service: SubmissionService = Depends(get_submission_service),
) -> SubmissionStatusResponse:
    """Retrieve submission status and audit trail."""
    try:
        record = service.get_submission(submission_id)
        return SubmissionStatusResponse(
            submission_id=record.submission_id,
            status=record.status.value,
            history=[(status.value, ts) for status, ts in record.status_history],
        )
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/{submission_id}/evaluate",
    summary="Trigger evaluation workflow for a submission",
)
def evaluate_submission(
    submission_id: str,
    orchestrator: EvaluationOrchestrator = Depends(get_evaluation_orchestrator),
) -> dict:
    """Trigger the central 10-step evaluation workflow for a submission."""
    try:
        report = orchestrator.evaluate_submission(submission_id)
        return {
            "evaluation_id": report.evaluation_id,
            "submission_id": report.submission_id,
            "status": report.status.value,
            "score": report.grading_report.earned_points if report.grading_report else None,
            "max_score": report.grading_report.max_score if report.grading_report else None,
            "percentage": report.grading_report.percentage if report.grading_report else None,
            "feedback": report.feedback_summary,
        }
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
