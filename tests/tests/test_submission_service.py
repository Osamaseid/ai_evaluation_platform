"""Tests for SubmissionService and lifecycle status tracking."""

from datetime import datetime, timedelta, timezone
import pytest

from evaluator.assignment import AssignmentDefinition, TestCaseDefinition
from evaluator.exceptions import (
    DeadlineExceededError,
    EntityNotFoundError,
    InvalidStateTransitionError,
)
from evaluator.services.submission_service import SubmissionService
from evaluator.stores.assignment_store import InMemoryAssignmentStore
from evaluator.stores.student_store import InMemoryStudentStore
from evaluator.stores.submission_store import InMemorySubmissionStore
from evaluator.submission import SubmissionSource, SubmissionStatus
from evaluator.users import Student


@pytest.fixture
def student_store():
    store = InMemoryStudentStore()
    store.save(Student("student101", "John Von Neumann", "john@ias.edu"))
    return store


@pytest.fixture
def assignment_store():
    store = InMemoryAssignmentStore()
    store.save(
        AssignmentDefinition(
            task_id="sort_algo",
            title="Sorting Algorithms",
            test_cases=(
                TestCaseDefinition("test_sort", "Sort integers", 10),
            ),
        )
    )
    return store


@pytest.fixture
def submission_service(student_store, assignment_store):
    return SubmissionService(
        submission_store=InMemorySubmissionStore(),
        assignment_store=assignment_store,
        student_store=student_store,
    )


class TestSubmissionService:
    def test_successful_submission(self, submission_service):
        record = submission_service.create_submission(
            student_id="student101",
            task_id="sort_algo",
            source_type=SubmissionSource.GITHUB,
            source_reference="https://github.com/john/sorting-homework",
        )

        assert record.submission_id.startswith("sub_")
        assert record.status is SubmissionStatus.RECEIVED
        assert len(record.status_history) == 1
        assert record.status_history[0][0] is SubmissionStatus.RECEIVED

        fetched = submission_service.get_submission(record.submission_id)
        assert fetched.submission_id == record.submission_id

    def test_submission_rejects_nonexistent_student(self, submission_service):
        with pytest.raises(EntityNotFoundError, match="Student with ID 'ghost' not found"):
            submission_service.create_submission(
                student_id="ghost",
                task_id="sort_algo",
                source_type=SubmissionSource.GITHUB,
                source_reference="https://github.com/ghost/repo",
            )

    def test_submission_rejects_nonexistent_assignment(self, submission_service):
        with pytest.raises(EntityNotFoundError, match="Assignment with ID 'invalid_task' not found"):
            submission_service.create_submission(
                student_id="student101",
                task_id="invalid_task",
                source_type=SubmissionSource.FILE_UPLOAD,
                source_reference="upload:123",
            )

    def test_submission_rejects_past_deadline(self, assignment_store, student_store):
        past_deadline = datetime.now(timezone.utc) - timedelta(days=1)
        assignment_store.save(
            AssignmentDefinition(
                task_id="late_task",
                title="Late Assignment",
                test_cases=(TestCaseDefinition("t1", "desc", 5),),
                deadline=past_deadline,
            )
        )
        service = SubmissionService(
            submission_store=InMemorySubmissionStore(),
            assignment_store=assignment_store,
            student_store=student_store,
        )

        with pytest.raises(DeadlineExceededError, match="deadline"):
            service.create_submission(
                student_id="student101",
                task_id="late_task",
                source_type=SubmissionSource.FILE_UPLOAD,
                source_reference="upload:file",
            )

    def test_status_transitions_and_history(self, submission_service):
        record = submission_service.create_submission(
            student_id="student101",
            task_id="sort_algo",
            source_type=SubmissionSource.FILE_UPLOAD,
            source_reference="upload:abc",
        )

        # Transition: RECEIVED -> VALIDATED
        validated = submission_service.update_status(record.submission_id, SubmissionStatus.VALIDATED)
        assert validated.status is SubmissionStatus.VALIDATED
        assert len(validated.status_history) == 2

        # Transition: VALIDATED -> EVALUATING
        evaluating = submission_service.update_status(record.submission_id, SubmissionStatus.EVALUATING)
        assert evaluating.status is SubmissionStatus.EVALUATING
        assert len(evaluating.status_history) == 3

        # Transition: EVALUATING -> COMPLETED
        completed = submission_service.update_status(record.submission_id, SubmissionStatus.COMPLETED)
        assert completed.status is SubmissionStatus.COMPLETED
        assert len(completed.status_history) == 4

    def test_illegal_status_transition_rejected(self, submission_service):
        record = submission_service.create_submission(
            student_id="student101",
            task_id="sort_algo",
            source_type=SubmissionSource.FILE_UPLOAD,
            source_reference="upload:abc",
        )

        # Direct transition from RECEIVED to COMPLETED is prohibited
        with pytest.raises(InvalidStateTransitionError):
            submission_service.update_status(record.submission_id, SubmissionStatus.COMPLETED)

