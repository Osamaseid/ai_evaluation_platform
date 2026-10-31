"""Unit tests for assignment management API router and schemas."""

import pytest
from fastapi import HTTPException

from evaluator.api.routers.assignments import (
    create_assignment,
    list_assignments,
)
from evaluator.api.schemas.assignments import (
    CreateAssignmentRequest,
    TestCaseSchema,
)
from evaluator.stores.assignment_store import InMemoryAssignmentStore


@pytest.fixture
def store():
    """Provide a fresh in-memory store for each test."""
    return InMemoryAssignmentStore()


@pytest.fixture
def valid_request():
    return CreateAssignmentRequest(
        task_id="python_week1",
        title="Calculator Functions",
        test_cases=[
            TestCaseSchema(test_case_id="add", description="Add two numbers", points=5),
            TestCaseSchema(test_case_id="subtract", description="Subtract two numbers", points=5),
        ],
    )


class TestCreateAssignmentEndpoint:
    def test_successful_creation(self, store, valid_request):
        response = create_assignment(valid_request, store=store)

        assert response.task_id == "python_week1"
        assert response.title == "Calculator Functions"
        assert response.max_score == 10
        assert len(response.test_cases) == 2

    def test_duplicate_task_id_raises_409(self, store, valid_request):
        create_assignment(valid_request, store=store)

        with pytest.raises(HTTPException) as exc_info:
            create_assignment(valid_request, store=store)

        assert exc_info.value.status_code == 409
        assert "already exists" in exc_info.value.detail


class TestListAssignmentsEndpoint:
    def test_empty_list(self, store):
        items = list_assignments(store=store)
        assert items == []

    def test_returns_created_assignments(self, store, valid_request):
        create_assignment(valid_request, store=store)
        items = list_assignments(store=store)

        assert len(items) == 1
        assert items[0].task_id == "python_week1"
        assert items[0].max_score == 10
