"""Instructor management, student administration, assignments, rubrics, and manual review endpoints."""

from typing import Any
from fastapi import APIRouter, Depends, HTTPException, Query, status

from evaluator.api.dependencies.auth import get_current_user, require_instructor
from evaluator.api.dependencies.pagination import PaginationParams, get_pagination
from evaluator.api.schemas.assignments import (
    AssignmentResponse,
    CreateAssignmentRequest,
)
from evaluator.api.schemas.evaluations import (
    EvaluationReportResponse,
    GradingReportSchema,
    TestCaseResultSchema,
)
from evaluator.api.schemas.manual_review import (
    ManualReviewRequest,
    ManualReviewResponse,
)
from evaluator.api.schemas.pagination import PaginatedResponse
from evaluator.api.schemas.rubrics import (
    GradingRubricSchema,
    RubricCriterionSchema,
    RubricEvaluationSchema,
)
from evaluator.api.schemas.users import (
    InstructorResponseSchema,
    StudentCreateSchema,
    StudentResponseSchema,
)
from evaluator.assignment import AssignmentDefinition, TestCaseDefinition
from evaluator.auth.models import UserAccount
from evaluator.evaluation import EvaluationReport
from evaluator.exceptions import DuplicateEntityError, EntityNotFoundError
from evaluator.rubric import GradingRubric, RubricCriterion, RubricEvaluation
from evaluator.services.assignment_service import AssignmentService
from evaluator.services.instructor_service import InstructorService
from evaluator.services.manual_review_service import ManualReviewService
from evaluator.services.student_service import StudentService
from evaluator.stores.assignment_store import (
    AssignmentStore,
    InMemoryAssignmentStore,
)
from evaluator.stores.evaluation_store import (
    EvaluationStore,
    InMemoryEvaluationStore,
)
from evaluator.stores.instructor_store import (
    InMemoryInstructorStore,
    InstructorStore,
)
from evaluator.stores.rubric_store import InMemoryRubricStore, RubricStore
from evaluator.stores.student_store import (
    InMemoryStudentStore,
    StudentStore,
)
from evaluator.users import Instructor, Student

router = APIRouter(prefix="/instructors", tags=["instructors"])

# Shared storage singletons
_instructor_store = InMemoryInstructorStore()
_student_store = InMemoryStudentStore()
_assignment_store = InMemoryAssignmentStore()
_rubric_store = InMemoryRubricStore()
_evaluation_store = InMemoryEvaluationStore()


def get_instructor_service() -> InstructorService:
    return InstructorService(_instructor_store)


def get_student_service() -> StudentService:
    return StudentService(_student_store)


def get_assignment_service() -> AssignmentService:
    return AssignmentService(_assignment_store, _instructor_store)


def get_rubric_store() -> RubricStore:
    return _rubric_store


def get_evaluation_store() -> EvaluationStore:
    return _evaluation_store


def get_manual_review_service() -> ManualReviewService:
    return ManualReviewService(_evaluation_store, _instructor_store)


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


# ---------------------------------------------------------------------------
# Instructor Profile Endpoints
# ---------------------------------------------------------------------------


@router.get(
    "/me",
    response_model=InstructorResponseSchema,
    summary="Get current instructor profile",
)
def get_my_instructor_profile(
    current_user: UserAccount = Depends(require_instructor),
    service: InstructorService = Depends(get_instructor_service),
) -> InstructorResponseSchema:
    """Retrieve the instructor profile for the currently logged in instructor."""
    try:
        instructor = service.get_instructor(current_user.user_id)
        return InstructorResponseSchema(
            instructor_id=instructor.instructor_id,
            name=instructor.name,
            email=instructor.email,
            created_at=instructor.created_at,
        )
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get(
    "/{instructor_id}",
    response_model=InstructorResponseSchema,
    summary="Get instructor profile by ID",
)
def get_instructor_by_id(
    instructor_id: str,
    current_user: UserAccount = Depends(require_instructor),
    service: InstructorService = Depends(get_instructor_service),
) -> InstructorResponseSchema:
    """Retrieve instructor profile details."""
    try:
        instructor = service.get_instructor(instructor_id)
        return InstructorResponseSchema(
            instructor_id=instructor.instructor_id,
            name=instructor.name,
            email=instructor.email,
            created_at=instructor.created_at,
        )
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


# ---------------------------------------------------------------------------
# Student Administration
# ---------------------------------------------------------------------------


@router.get(
    "/students",
    response_model=PaginatedResponse[StudentResponseSchema],
    summary="List enrolled students (paginated)",
)
def list_students(
    pagination: PaginationParams = Depends(get_pagination),
    current_user: UserAccount = Depends(require_instructor),
    student_service: StudentService = Depends(get_student_service),
) -> PaginatedResponse[StudentResponseSchema]:
    """List all students registered in the course."""
    all_students = student_service.list_students()
    total = len(all_students)

    sliced = all_students[pagination.offset : pagination.offset + pagination.limit]
    items = [
        StudentResponseSchema(
            student_id=s.student_id,
            name=s.name,
            email=s.email,
            created_at=s.created_at,
        )
        for s in sliced
    ]

    return PaginatedResponse(
        items=items,
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.post(
    "/students",
    response_model=StudentResponseSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Enroll a new student",
)
def enroll_student(
    request: StudentCreateSchema,
    current_user: UserAccount = Depends(require_instructor),
    student_service: StudentService = Depends(get_student_service),
) -> StudentResponseSchema:
    """Register/enroll a student into the platform."""
    try:
        student = student_service.register_student(
            student_id=request.student_id,
            name=request.name,
            email=request.email,
        )
        return StudentResponseSchema(
            student_id=student.student_id,
            name=student.name,
            email=student.email,
            created_at=student.created_at,
        )
    except DuplicateEntityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


# ---------------------------------------------------------------------------
# Assignment Management
# ---------------------------------------------------------------------------


@router.get(
    "/assignments",
    response_model=list[AssignmentResponse],
    summary="List all course assignments",
)
def list_assignments(
    current_user: UserAccount = Depends(require_instructor),
    assignment_service: AssignmentService = Depends(get_assignment_service),
) -> list[AssignmentResponse]:
    """Retrieve all assignment definitions."""
    assignments = assignment_service.list_assignments()
    return [
        AssignmentResponse(
            task_id=a.task_id,
            title=a.title,
            test_cases=[
                {"test_case_id": tc.test_case_id, "description": tc.description, "points": tc.points}
                for tc in a.test_cases
            ],
            max_score=a.max_score,
        )
        for a in assignments
    ]


@router.post(
    "/assignments",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new assignment",
)
def create_assignment(
    request: CreateAssignmentRequest,
    current_user: UserAccount = Depends(require_instructor),
    assignment_service: AssignmentService = Depends(get_assignment_service),
) -> AssignmentResponse:
    """Create a new programming assignment with test cases."""
    assignment = AssignmentDefinition(
        task_id=request.task_id,
        title=request.title,
        instructor_id=current_user.user_id,
        test_cases=tuple(
            TestCaseDefinition(
                test_case_id=tc.test_case_id,
                description=tc.description,
                points=tc.points,
            )
            for tc in request.test_cases
        ),
    )

    try:
        saved = assignment_service.create_assignment(assignment)
        return AssignmentResponse(
            task_id=saved.task_id,
            title=saved.title,
            test_cases=[
                {"test_case_id": tc.test_case_id, "description": tc.description, "points": tc.points}
                for tc in saved.test_cases
            ],
            max_score=saved.max_score,
        )
    except (ValueError, DuplicateEntityError) as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.put(
    "/assignments/{task_id}",
    response_model=AssignmentResponse,
    summary="Update an existing assignment",
)
def update_assignment(
    task_id: str,
    request: CreateAssignmentRequest,
    current_user: UserAccount = Depends(require_instructor),
    assignment_service: AssignmentService = Depends(get_assignment_service),
) -> AssignmentResponse:
    """Update title and test cases for an assignment."""
    updated = AssignmentDefinition(
        task_id=task_id,
        title=request.title,
        instructor_id=current_user.user_id,
        test_cases=tuple(
            TestCaseDefinition(
                test_case_id=tc.test_case_id,
                description=tc.description,
                points=tc.points,
            )
            for tc in request.test_cases
        ),
    )
    try:
        saved = assignment_service.update_assignment(updated)
        return AssignmentResponse(
            task_id=saved.task_id,
            title=saved.title,
            test_cases=[
                {"test_case_id": tc.test_case_id, "description": tc.description, "points": tc.points}
                for tc in saved.test_cases
            ],
            max_score=saved.max_score,
        )
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


# ---------------------------------------------------------------------------
# Grading Rubric Management
# ---------------------------------------------------------------------------


@router.post(
    "/rubrics",
    response_model=GradingRubricSchema,
    status_code=status.HTTP_201_CREATED,
    summary="Create or register a grading rubric",
)
def create_rubric(
    request: GradingRubricSchema,
    current_user: UserAccount = Depends(require_instructor),
    rubric_store: RubricStore = Depends(get_rubric_store),
) -> GradingRubricSchema:
    """Create a qualitative grading rubric with criteria."""
    rubric = GradingRubric(
        rubric_id=request.rubric_id,
        title=request.title,
        criteria=tuple(
            RubricCriterion(
                criterion_id=c.criterion_id,
                name=c.name,
                description=c.description,
                max_points=c.max_points,
                weight=c.weight,
            )
            for c in request.criteria
        ),
    )
    try:
        rubric_store.save(rubric)
        return request
    except DuplicateEntityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))


@router.get(
    "/rubrics/{rubric_id}",
    response_model=GradingRubricSchema,
    summary="Get grading rubric by ID",
)
def get_rubric(
    rubric_id: str,
    current_user: UserAccount = Depends(require_instructor),
    rubric_store: RubricStore = Depends(get_rubric_store),
) -> GradingRubricSchema:
    """Retrieve rubric definition and criteria."""
    rubric = rubric_store.get(rubric_id)
    if not rubric:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"GradingRubric '{rubric_id}' not found.",
        )

    return GradingRubricSchema(
        rubric_id=rubric.rubric_id,
        title=rubric.title,
        criteria=[
            RubricCriterionSchema(
                criterion_id=c.criterion_id,
                name=c.name,
                description=c.description,
                max_points=c.max_points,
                weight=c.weight,
            )
            for c in rubric.criteria
        ],
    )


# ---------------------------------------------------------------------------
# Evaluation Management & Manual Review
# ---------------------------------------------------------------------------


@router.get(
    "/evaluations",
    response_model=PaginatedResponse[EvaluationReportResponse],
    summary="List all evaluation reports across the course",
)
def list_evaluations(
    task_id: str | None = Query(default=None, description="Optional task ID filter"),
    pagination: PaginationParams = Depends(get_pagination),
    current_user: UserAccount = Depends(require_instructor),
    evaluation_store: EvaluationStore = Depends(get_evaluation_store),
) -> PaginatedResponse[EvaluationReportResponse]:
    """Retrieve all student evaluations with optional task filter."""
    all_reports = evaluation_store.list_all()
    if task_id:
        all_reports = [r for r in all_reports if r.workflow_audit and r.workflow_audit.task_id == task_id]

    total = len(all_reports)
    sliced = all_reports[pagination.offset : pagination.offset + pagination.limit]
    items = [_to_evaluation_schema(r) for r in sliced]

    return PaginatedResponse(
        items=items,
        total=total,
        limit=pagination.limit,
        offset=pagination.offset,
    )


@router.post(
    "/evaluations/{evaluation_id}/manual-review",
    response_model=ManualReviewResponse,
    summary="Apply instructor manual review, score override, and qualitative assessment",
)
def apply_manual_review(
    evaluation_id: str,
    request: ManualReviewRequest,
    current_user: UserAccount = Depends(require_instructor),
    review_service: ManualReviewService = Depends(get_manual_review_service),
) -> ManualReviewResponse:
    """Apply manual instructor grade adjustment and qualitative feedback."""
    rubric_evals = tuple(
        RubricEvaluation(
            criterion_id=r.criterion_id,
            score=r.score,
            feedback=r.feedback,
        )
        for r in request.rubric_evaluations
    )

    try:
        updated = review_service.add_manual_review(
            evaluation_id=evaluation_id,
            instructor_id=current_user.user_id,
            override_score=request.override_score,
            instructor_notes=request.instructor_notes,
            rubric_evaluations=rubric_evals,
        )

        original = updated.grading_report.earned_points if updated.grading_report else None
        final_score = updated.manual_override_score if updated.manual_override_score is not None else original

        return ManualReviewResponse(
            evaluation_id=updated.evaluation_id,
            submission_id=updated.submission_id,
            original_score=original,
            final_score=final_score,
            override_score=updated.manual_override_score,
            instructor_notes=updated.instructor_notes,
            rubric_evaluations=[
                RubricEvaluationSchema(
                    criterion_id=re.criterion_id,
                    score=re.score,
                    feedback=re.feedback,
                )
                for re in updated.rubric_evaluations
            ],
            reviewed_by=updated.reviewed_by,
            reviewed_at=updated.reviewed_at,
        )
    except EntityNotFoundError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))

