"""Tests for the assignment management API endpoints."""

import pytest
from fastapi.testclient import TestClient

from evaluator.api.app import create_app
from evaluator.api.routers.assignments import get_assignment_store
from evaluator.stores.assignment_store import InMemoryAssignmentStore


@pytest.fixture
def store():
    """Provide a fresh in-memory store for each test."""
    return InMemoryAssignmentStore()


@pytest.fixture
def client(store):
    """Create a test client with an isolated store."""
    app = create_app()
    app.dependency_overrides[get_assignment_store] = lambda: store
    return TestClient(app)


VALID_ASSIGNMENT = {
    "task_id": "python_week1",
    "title": "Calculator Functions",
    "test_cases": [
        {"test_case_id": "add", "description": "Add two numbers", "points": 5},
        {"test_case_id": "subtract", "description": "Subtract two numbers", "points": 5},
    ],
}


# ---------------------------------------------------------------------------
# POST /assignments
# ---------------------------------------------------------------------------


class TestCreateAssignment:
    """Tests for assignment creation."""

    def test_successful_creation(self, client):
        response = client.post("/assignments", json=VALID_ASSIGNMENT)

        assert response.status_code == 201

        data = response.json()
        assert data["task_id"] == "python_week1"
        assert data["title"] == "Calculator Functions"
        assert data["max_score"] == 10
        assert len(data["test_cases"]) == 2

    def test_duplicate_task_id_returns_409(self, client):
        client.post("/assignments", json=VALID_ASSIGNMENT)
        response = client.post("/assignments", json=VALID_ASSIGNMENT)

        assert response.status_code == 409
        assert "already exists" in response.json()["detail"]

    def test_empty_task_id_returns_422(self, client):
        payload = {**VALID_ASSIGNMENT, "task_id": ""}
        response = client.post("/assignments", json=payload)

        assert response.status_code == 422

    def test_invalid_task_id_characters_returns_422(self, client):
        payload = {**VALID_ASSIGNMENT, "task_id": "../hack"}
        response = client.post("/assignments", json=payload)

        assert response.status_code == 422

    def test_missing_test_cases_returns_422(self, client):
        payload = {"task_id": "test1", "title": "Test"}
        response = client.post("/assignments", json=payload)

        assert response.status_code == 422

    def test_zero_points_returns_422(self, client):
        payload = {
            **VALID_ASSIGNMENT,
            "test_cases": [
                {"test_case_id": "t1", "description": "Test", "points": 0},
            ],
        }
        response = client.post("/assignments", json=payload)

        assert response.status_code == 422


# ---------------------------------------------------------------------------
# GET /assignments
# ---------------------------------------------------------------------------


class TestListAssignments:
    """Tests for listing assignments."""

    def test_empty_list(self, client):
        response = client.get("/assignments")

        assert response.status_code == 200
        assert response.json() == []

    def test_returns_created_assignments(self, client):
        client.post("/assignments", json=VALID_ASSIGNMENT)
        response = client.get("/assignments")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["task_id"] == "python_week1"
        assert data[0]["max_score"] == 10

