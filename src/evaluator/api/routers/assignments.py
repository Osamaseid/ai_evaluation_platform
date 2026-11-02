"""Assignment management endpoints."""

from fastapi import APIRouter, Depends, HTTPException, status

from evaluator.api.dependencies.stores import shared_assignment_store
from evaluator.api.schemas.assignments import (
    AssignmentResponse,
    CreateAssignmentRequest,
)
from evaluator.assignment import AssignmentDefinition, TestCaseDefinition
from evaluator.stores.assignment_store import AssignmentStore

router = APIRouter(prefix="/assignments", tags=["assignments"])


def get_assignment_store() -> AssignmentStore:
    """Return the application's assignment store."""
    return shared_assignment_store


# ---------------------------------------------------------------------------
# Helper: convert between API schemas and domain models.
# This is the thin translation layer between HTTP and the domain.
# ---------------------------------------------------------------------------


def _to_domain(request: CreateAssignmentRequest) -> AssignmentDefinition:
    """Convert an API request into a domain object."""
    return AssignmentDefinition(
        task_id=request.task_id,
        title=request.title,
        test_cases=tuple(
            TestCaseDefinition(
                test_case_id=tc.test_case_id,
                description=tc.description,
                points=tc.points,
            )
            for tc in request.test_cases
        ),
    )


def _to_response(assignment: AssignmentDefinition) -> AssignmentResponse:
    """Convert a domain object into an API response."""
    return AssignmentResponse(
        task_id=assignment.task_id,
        title=assignment.title,
        test_cases=[
            {"test_case_id": tc.test_case_id,
             "description": tc.description,
             "points": tc.points}
            for tc in assignment.test_cases
        ],
        max_score=assignment.max_score,
    )


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@router.post(
    "",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new assignment",
)
def create_assignment(
    request: CreateAssignmentRequest,
    store: AssignmentStore = Depends(get_assignment_store),
) -> AssignmentResponse:
    """Create a programming assignment with its test cases."""
    assignment = _to_domain(request)

    try:
        store.save(assignment)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        )

    return _to_response(assignment)


@router.get(
    "",
    response_model=list[AssignmentResponse],
    summary="List all assignments",
)
def list_assignments(
    store: AssignmentStore = Depends(get_assignment_store),
) -> list[AssignmentResponse]:
    """Return every assignment currently in the system."""
    return [_to_response(a) for a in store.list_all()]

