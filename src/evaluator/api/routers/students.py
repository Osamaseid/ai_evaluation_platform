"""Student profile, submission history, and evaluation reporting endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status

from evaluator.api.dependencies.auth import get_current_user, require_student
from evaluator.api.dependencies.pagination import PaginationParams, get_pagination
from evaluator.api.schemas.evaluations import (
    EvaluationReportResponse,
    GradingReportSchema,
    TestCaseResultSchema,
)
from evaluator.api.schemas.pagination import PaginatedResponse
from evaluator.api.schemas.rubrics import RubricEvaluationSchema
from evaluator.api.schemas.submissions import SubmissionResponse
from evaluator.api.schemas.users import StudentResponseSchema
from evaluator.auth.models import UserAccount, UserRole
from evaluator.evaluation import EvaluationReport
from evaluator.exceptions import EntityNotFoundError
from evaluator.services.student_service import StudentService
from evaluator.stores.evaluation_store import (
    EvaluationStore,
    InMemoryEvaluationStore,
)
from evaluator.stores.student_store import (
    InMemoryStudentStore,
    StudentStore,
)
from evaluator.stores.submission_store import (
    InMemorySubmissionStore,
    SubmissionStore,
)
from evaluator.submission import SubmissionRecord

router = APIRouter(prefix="/students", tags=["students"])

_student_store = InMemoryStudentStore()
_submission_store = InMemorySubmissionStore()
_evaluation_store = InMemoryEvaluationStore()


def get_student_service() -> StudentService:
    return StudentService(_student_store)


def get_submission_store() -> SubmissionStore:
    return _submission_store


def get_evaluation_store() -> EvaluationStore:
    return _evaluation_store


def _check_access_permission(current_user: UserAccount, target_student_id: str) -> None:
    """Ensure the user is authorized to view this student's records."""
    if current_user.role in (UserRole.INSTRUCTOR, UserRole.ADMIN):
        return
    if current_user.user_id != target_student_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access denied: cannot access student data for '{target_student_id}'.",
        )


def _to_submission_schema(s: SubmissionRecord) -> SubmissionResponse:
    return SubmissionResponse(
        submission_id=s.submission_id,
        student_id=s.metadata.student_id,
        task_id=s.metadata.task_id,
        source_type=s.source_type.value,
        source_reference=s.source_reference,
        status=s.status.value,
        submitted_at=s.submitted_at,
    )


def _to_evaluation_schema(report: EvaluationReport) -> EvaluationReportResponse:
    grading_schema = None
    if report.grading_report:
        grading_schema = GradingReportSchema(
            earned_points=report.grading_report.earned_points,
            max_score=report.grading_report.max_score,
            passed_tests=report.grading_report.passed_tests,
            total_tests=report.grading_report.total_tests,
            percentage=report.grading_report.percentage,
        )

    test_schemas = [
        TestCaseResultSchema(
            test_case_id=tr.test_case_id,
            passed=tr.passed,
            message=tr.message,
        )
        for tr in report.test_results
    ]

    rubric_schemas = [
        RubricEvaluationSchema(
            criterion_id=re.criterion_id,
            score=re.score,
            feedback=re.feedback,
        )
        for re in report.rubric_evaluations
    ]

    return EvaluationReportResponse(
        evaluation_id=report.evaluation_id,
        submission_id=report.submission_id,
        status=report.status.value,
        grading_report=grading_schema,
        test_results=test_schemas,
        rubric_evaluations=rubric_schemas,
        ai_review=report.ai_review,
        error_message=report.error_message,
        evaluated_at=report.evaluated_at,
    )


@router.get(
    "/me",
    response_model=StudentResponseSchema,
    summary="Get current student profile",
)
def get_my_profile(
    current_user: UserAccount = Depends(require_student),
    student_service: StudentService = Depends(get_student_service),
) -> StudentResponseSchema:
    """Retrieve the enrolled profile of the logged-in student."""
    try:
        student = student_service.get_student(current_user.user_id)
        return StudentResponseSchema(
            student_id=student.student_id,
            name=student.name,
            email=student.email,
            created_at=student.created_at,
        )
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get(
    "/{student_id}",
    response_model=StudentResponseSchema,
    summary="Get student profile by ID",
)
def get_student_profile(
    student_id: str,
    current_user: UserAccount = Depends(get_current_user),
    student_service: StudentService = Depends(get_student_service),
) -> StudentResponseSchema:
    """Retrieve student profile (requires ownership or instructor/admin role)."""
    _check_access_permission(current_user, student_id)
    try:
        student = student_service.get_student(student_id)
        return StudentResponseSchema(
            student_id=student.student_id,
            name=student.name,
            email=student.email,
            created_at=student.created_at,
        )
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get(
    "/{student_id}/submissions",
    response_model=PaginatedResponse[SubmissionResponse],
    summary="List student submissions (paginated)",
)
def get_student_submissions(
    student_id: str,
    pagination: PaginationParams = Depends(get_pagination),
    current_user: UserAccount = Depends(get_current_user),
    submission_store: SubmissionStore = Depends(get_submission_store),
) -> PaginatedResponse[SubmissionResponse]:
    """Retrieve paginated submissions for a student."""
    _check_access_permission(current_user, student_id)
    all_submissions = submission_store.list_by_student(student_id)
    total = len(all_submissions)

    sliced = all_submissions[pagination.offset : pagination.offset + pagination.limit]
    items = [_to_submission_schema(s) for s in sliced]

    return PaginatedResponse(
        items=items,
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.get(
    "/{student_id}/evaluations",
    response_model=PaginatedResponse[EvaluationReportResponse],
    summary="List student evaluation reports (paginated)",
)
def get_student_evaluations(
    student_id: str,
    pagination: PaginationParams = Depends(get_pagination),
    current_user: UserAccount = Depends(get_current_user),
    submission_store: SubmissionStore = Depends(get_submission_store),
    evaluation_store: EvaluationStore = Depends(get_evaluation_store),
) -> PaginatedResponse[EvaluationReportResponse]:
    """Retrieve paginated evaluation reports for a student."""
    _check_access_permission(current_user, student_id)
    student_subs = {s.submission_id for s in submission_store.list_by_student(student_id)}

    all_reports = [r for r in evaluation_store.list_all() if r.submission_id in student_subs]
    total = len(all_reports)

    sliced = all_reports[pagination.offset : pagination.offset + pagination.limit]
    items = [_to_evaluation_schema(r) for r in sliced]

    return PaginatedResponse(
        items=items,
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )

