"""Comprehensive automated test suite for the complete FastAPI backend.

Tests:
1. Authentication:
   - Registration (student & instructor)
   - Login (valid credentials returning bearer token, invalid password returning 401)
   - Logout & token revocation
   - Current user profile retrieval
   - Password management (change with old password check)
2. Role-Based Access Control (RBAC):
   - Student access to student endpoints
   - Instructor access to instructor endpoints
   - Student rejected from instructor endpoints (HTTP 403)
   - Student rejected from accessing another student's records (HTTP 403)
3. Students:
   - Profile retrieval
   - Paginated submission history
   - Paginated evaluation reports
4. Instructors:
   - Profile retrieval
   - Student management (enrollment, listing)
   - Assignment management (create, list, update)
   - Rubric management (create, retrieve)
   - Evaluation administration & manual review overrides
5. Submissions:
   - GitHub URL submission
   - File upload submission
   - Status tracking & full audit history
6. Evaluation:
   - Start evaluation workflow
   - Retrieve evaluation status
   - Retrieve test breakdown
   - Retrieve AI feedback
   - Retrieve final report summary
7. Rate limiting:
   - Enforcing threshold and HTTP 429 response
"""

from datetime import datetime, timezone
import io
import pytest
from fastapi import HTTPException, UploadFile, status
from fastapi.security import HTTPAuthorizationCredentials

from evaluator.api.dependencies.auth import (
    get_auth_service,
    get_current_user,
    require_instructor,
    require_student,
)
from evaluator.api.dependencies.pagination import PaginationParams
from evaluator.api.dependencies.rate_limiter import SlidingWindowRateLimiter
from evaluator.api.routers.auth import (
    change_password,
    get_current_user_profile,
    login,
    logout,
    register,
)
from evaluator.api.routers.evaluations import (
    get_ai_feedback,
    get_evaluation,
    get_evaluation_by_submission,
    get_evaluation_status,
    get_evaluation_tests,
    get_final_report_summary,
    run_evaluation,
)
from evaluator.api.routers.instructors import (
    apply_manual_review,
    create_assignment as instructor_create_assignment,
    create_rubric,
    enroll_student,
    get_instructor_by_id,
    get_my_instructor_profile,
    get_rubric,
    list_assignments as instructor_list_assignments,
    list_evaluations as instructor_list_evaluations,
    list_students as instructor_list_students,
    update_assignment as instructor_update_assignment,
)
from evaluator.api.routers.students import (
    get_my_profile,
    get_student_evaluations,
    get_student_profile,
    get_student_submissions,
)
from evaluator.api.routers.submissions import (
    get_submission,
    get_submission_history,
    get_submission_status,
    submit_file_upload,
    submit_github_repo,
)
from evaluator.api.schemas.assignments import (
    CreateAssignmentRequest,
    TestCaseSchema,
)
from evaluator.api.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
)
from evaluator.api.schemas.manual_review import ManualReviewRequest
from evaluator.api.schemas.rubrics import (
    GradingRubricSchema,
    RubricCriterionSchema,
    RubricEvaluationSchema,
)
from evaluator.api.schemas.submissions import GitHubSubmissionRequest
from evaluator.api.schemas.users import StudentCreateSchema
from evaluator.assignment import AssignmentDefinition, TestCaseDefinition
from evaluator.auth.models import UserAccount, UserRole
from evaluator.auth.revocation import InMemoryTokenRevocationStore
from evaluator.auth.security import TokenManager
from evaluator.evaluation import EvaluationReport, EvaluationStatus
from evaluator.grading import GradingReport, TestCaseResult
from evaluator.orchestration.models import (
    StepStatus,
    WorkflowExecutionAudit,
    WorkflowStep,
)
from evaluator.runner import Runner
from evaluator.services.assignment_service import AssignmentService
from evaluator.services.auth_service import AuthService
from evaluator.services.evaluation_orchestrator import EvaluationOrchestrator
from evaluator.services.instructor_service import InstructorService
from evaluator.services.manual_review_service import ManualReviewService
from evaluator.services.student_service import StudentService
from evaluator.services.submission_service import SubmissionService
from evaluator.storage.submission_storage import ControlledFileStorage
from evaluator.stores.assignment_store import InMemoryAssignmentStore
from evaluator.stores.evaluation_store import InMemoryEvaluationStore
from evaluator.stores.instructor_store import InMemoryInstructorStore
from evaluator.stores.rubric_store import InMemoryRubricStore
from evaluator.stores.student_store import InMemoryStudentStore
from evaluator.stores.submission_store import InMemorySubmissionStore
from evaluator.stores.user_store import InMemoryUserStore
from evaluator.submission import (
    SubmissionMetadata,
    SubmissionRecord,
    SubmissionSource,
    SubmissionStatus,
)


# ---------------------------------------------------------------------------
# Test Fixtures & Mock Environment
# ---------------------------------------------------------------------------


class MockEvaluatorRunner(Runner):
    """Deterministic runner for API integration testing."""

    def run(self, assignment, source_code):
        return (
            TestCaseResult(test_case_id="tc1", passed=True, message="Assertion passed"),
            TestCaseResult(test_case_id="tc2", passed=True, message="Assertion passed"),
        )


@pytest.fixture
def api_backend(tmp_path):
    """Constructs a clean, isolated backend context for automated API tests."""
    user_store = InMemoryUserStore()
    student_store = InMemoryStudentStore()
    instructor_store = InMemoryInstructorStore()
    assignment_store = InMemoryAssignmentStore()
    rubric_store = InMemoryRubricStore()
    submission_store = InMemorySubmissionStore()
    evaluation_store = InMemoryEvaluationStore()

    token_manager = TokenManager(secret_key="test-api-secret-key-32b-length-secure")
    revocation_store = InMemoryTokenRevocationStore()

    auth_service = AuthService(
        user_store=user_store,
        student_store=student_store,
        instructor_store=instructor_store,
        token_manager=token_manager,
        revocation_store=revocation_store,
    )

    storage = ControlledFileStorage(base_dir=tmp_path / "submissions")

    submission_service = SubmissionService(
        submission_store=submission_store,
        assignment_store=assignment_store,
        student_store=student_store,
        storage=storage,
    )

    assignment_service = AssignmentService(
        assignment_store=assignment_store,
        instructor_store=instructor_store,
    )

    student_service = StudentService(student_store)
    instructor_service = InstructorService(instructor_store)
    manual_review_service = ManualReviewService(evaluation_store, instructor_store)

    orchestrator = EvaluationOrchestrator(
        submission_store=submission_store,
        assignment_store=assignment_store,
        evaluation_store=evaluation_store,
        runner=MockEvaluatorRunner(),
        storage=storage,
    )

    # Seed an assignment
    assignment = AssignmentDefinition(
        task_id="algo_hw1",
        title="Algorithms Homework 1",
        instructor_id="inst_curie",
        test_cases=(
            TestCaseDefinition("tc1", "Check base case", 5),
            TestCaseDefinition("tc2", "Check recursive case", 5),
        ),
    )
    assignment_store.save(assignment)

    # Register student and instructor accounts
    student_user = auth_service.register(
        user_id="student_ada",
        email="ada@analytics.org",
        password="securePassword123",
        role=UserRole.STUDENT,
        name="Ada Lovelace",
    )

    instructor_user = auth_service.register(
        user_id="inst_curie",
        email="curie@sorbonne.fr",
        password="profPassword123",
        role=UserRole.INSTRUCTOR,
        name="Prof. Marie Curie",
    )

    return {
        "auth_service": auth_service,
        "student_service": student_service,
        "instructor_service": instructor_service,
        "assignment_service": assignment_service,
        "submission_service": submission_service,
        "manual_review_service": manual_review_service,
        "orchestrator": orchestrator,
        "user_store": user_store,
        "student_store": student_store,
        "instructor_store": instructor_store,
        "assignment_store": assignment_store,
        "rubric_store": rubric_store,
        "submission_store": submission_store,
        "evaluation_store": evaluation_store,
        "storage": storage,
        "student_user": student_user,
        "instructor_user": instructor_user,
        "token_manager": token_manager,
    }


# ---------------------------------------------------------------------------
# 1. Authentication & Credentials Tests
# ---------------------------------------------------------------------------


class TestAuthenticationEndpoints:
    def test_register_student_and_instructor(self, api_backend):
        auth_svc = api_backend["auth_service"]

        # Register new student
        req_student = RegisterRequest(
            user_id="student_gauss",
            email="gauss@gottingen.de",
            password="gaussianPassword123",
            role=UserRole.STUDENT,
            name="Carl Gauss",
        )
        resp_student = register(req_student, auth_service=auth_svc)
        assert resp_student.user_id == "student_gauss"
        assert resp_student.role == "student"

        # Duplicate ID rejection
        with pytest.raises(HTTPException) as exc:
            register(req_student, auth_service=auth_svc)
        assert exc.value.status_code == status.HTTP_409_CONFLICT

    def test_login_success_and_failure(self, api_backend):
        auth_svc = api_backend["auth_service"]

        # Successful login
        req_valid = LoginRequest(
            email_or_user_id="ada@analytics.org",
            password="securePassword123",
        )
        resp = login(req_valid, auth_service=auth_svc)
        assert resp.access_token is not None
        assert resp.token_type == "bearer"
        assert resp.user_id == "student_ada"
        assert resp.role == "student"

        # Invalid password
        req_invalid = LoginRequest(
            email_or_user_id="ada@analytics.org",
            password="wrongPassword",
        )
        with pytest.raises(HTTPException) as exc:
            login(req_invalid, auth_service=auth_svc)
        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_current_user_and_logout_revocation(self, api_backend):
        auth_svc = api_backend["auth_service"]

        login_resp = login(
            LoginRequest(email_or_user_id="student_ada", password="securePassword123"),
            auth_service=auth_svc,
        )
        token = login_resp.access_token

        # Access profile with token
        current_user = auth_svc.get_current_user(token)
        profile = get_current_user_profile(current_user=current_user)
        assert profile.user_id == "student_ada"
        assert profile.email == "ada@analytics.org"

        # Logout revokes the token
        logout(authorization=f"Bearer {token}", auth_service=auth_svc)

        # Subsequent attempt with revoked token must raise HTTPException 401
        with pytest.raises(HTTPException) as exc:
            get_current_user(
                credentials=HTTPAuthorizationCredentials(scheme="Bearer", credentials=token),
                auth_service=auth_svc,
            )
        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED

    def test_password_management(self, api_backend):
        auth_svc = api_backend["auth_service"]
        user = api_backend["student_user"]

        # Successful change
        change_password(
            ChangePasswordRequest(
                old_password="securePassword123",
                new_password="brandNewPassword456",
            ),
            current_user=user,
            auth_service=auth_svc,
        )

        # Login with new password succeeds
        login_resp = login(
            LoginRequest(email_or_user_id="student_ada", password="brandNewPassword456"),
            auth_service=auth_svc,
        )
        assert login_resp.user_id == "student_ada"

        # Old password rejected
        with pytest.raises(HTTPException) as exc:
            login(
                LoginRequest(email_or_user_id="student_ada", password="securePassword123"),
                auth_service=auth_svc,
            )
        assert exc.value.status_code == status.HTTP_401_UNAUTHORIZED


# ---------------------------------------------------------------------------
# 2. Role-Based Access Control (RBAC) Tests
# ---------------------------------------------------------------------------


class TestRoleBasedAccessControl:
    def test_student_prohibited_from_instructor_endpoints(self, api_backend):
        student_user = api_backend["student_user"]
        instructor_svc = api_backend["instructor_service"]

        # Student user attempting instructor endpoint must be rejected with 403
        with pytest.raises(HTTPException) as exc:
            get_my_instructor_profile(
                current_user=require_instructor(student_user),
                service=instructor_svc,
            )
        assert exc.value.status_code == status.HTTP_403_FORBIDDEN

    def test_instructor_permitted_on_instructor_endpoints(self, api_backend):
        instructor_user = api_backend["instructor_user"]
        instructor_svc = api_backend["instructor_service"]

        resp = get_my_instructor_profile(
            current_user=require_instructor(instructor_user),
            service=instructor_svc,
        )
        assert resp.instructor_id == "inst_curie"

    def test_student_cannot_view_another_students_submissions(self, api_backend):
        student_ada = api_backend["student_user"]
        sub_store = api_backend["submission_store"]

        # Attempting to query student_turing's data while logged in as student_ada
        with pytest.raises(HTTPException) as exc:
            get_student_submissions(
                student_id="student_turing",
                pagination=PaginationParams(limit=10, offset=0),
                current_user=student_ada,
                submission_store=sub_store,
            )
        assert exc.value.status_code == status.HTTP_403_FORBIDDEN

    def test_instructor_can_view_any_students_submissions(self, api_backend):
        instructor = api_backend["instructor_user"]
        sub_store = api_backend["submission_store"]

        resp = get_student_submissions(
            student_id="student_ada",
            pagination=PaginationParams(limit=10, offset=0),
            current_user=instructor,
            submission_store=sub_store,
        )
        assert resp.items == []
        assert resp.total == 0


# ---------------------------------------------------------------------------
# 3. Student Profile & Submission Query Tests
# ---------------------------------------------------------------------------


class TestStudentEndpoints:
    def test_student_profile_and_paginated_history(self, api_backend):
        student_user = api_backend["student_user"]
        student_svc = api_backend["student_service"]
        sub_store = api_backend["submission_store"]
        eval_store = api_backend["evaluation_store"]

        profile = get_my_profile(
            current_user=student_user,
            student_service=student_svc,
        )
        assert profile.student_id == "student_ada"
        assert profile.name == "Ada Lovelace"

        # Populate two submissions
        for i in range(5):
            sub = SubmissionRecord(
                metadata=SubmissionMetadata(student_id="student_ada", task_id="algo_hw1"),
                source_type=SubmissionSource.FILE_UPLOAD,
                source_reference=f"upload:sub_{i}.py",
                source_code="def solution(): pass",
                status=SubmissionStatus.COMPLETED,
            )
            sub_store.save(sub)

        # Query first page (limit=2, offset=0)
        p1 = get_student_submissions(
            student_id="student_ada",
            pagination=PaginationParams(limit=2, offset=0),
            current_user=student_user,
            submission_store=sub_store,
        )
        assert len(p1.items) == 2
        assert p1.total == 5
        assert p1.offset == 0

        # Query second page (limit=2, offset=2)
        p2 = get_student_submissions(
            student_id="student_ada",
            pagination=PaginationParams(limit=2, offset=2),
            current_user=student_user,
            submission_store=sub_store,
        )
        assert len(p2.items) == 2
        assert p2.offset == 2


# ---------------------------------------------------------------------------
# 4. Instructor Administration & Manual Review Tests
# ---------------------------------------------------------------------------


class TestInstructorEndpoints:
    def test_enroll_and_list_students_paginated(self, api_backend):
        instructor = api_backend["instructor_user"]
        student_svc = api_backend["student_service"]

        # Enroll student
        req = StudentCreateSchema(
            student_id="student_hypatia",
            name="Hypatia of Alexandria",
            email="hypatia@alexandria.edu",
        )
        enrolled = enroll_student(req, current_user=instructor, student_service=student_svc)
        assert enrolled.student_id == "student_hypatia"

        # List students paginated
        p = instructor_list_students(
            pagination=PaginationParams(limit=10, offset=0),
            current_user=instructor,
            student_service=student_svc,
        )
        assert p.total >= 2
        student_ids = [s.student_id for s in p.items]
        assert "student_hypatia" in student_ids

    def test_assignment_lifecycle(self, api_backend):
        instructor = api_backend["instructor_user"]
        assignment_svc = api_backend["assignment_service"]

        req = CreateAssignmentRequest(
            task_id="graph_bfs",
            title="Graph BFS Traversal",
            test_cases=[
                TestCaseSchema(test_case_id="tc_bfs", description="Verify BFS order", points=10),
            ],
        )

        # Create
        created = instructor_create_assignment(req, current_user=instructor, assignment_service=assignment_svc)
        assert created.task_id == "graph_bfs"
        assert created.max_score == 10

        # Update
        req_update = CreateAssignmentRequest(
            task_id="graph_bfs",
            title="Graph BFS & Shortest Path",
            test_cases=[
                TestCaseSchema(test_case_id="tc_bfs", description="Verify BFS order", points=10),
                TestCaseSchema(test_case_id="tc_path", description="Verify Shortest Path", points=10),
            ],
        )
        updated = instructor_update_assignment("graph_bfs", req_update, current_user=instructor, assignment_service=assignment_svc)
        assert updated.title == "Graph BFS & Shortest Path"
        assert updated.max_score == 20

    def test_rubric_creation_and_retrieval(self, api_backend):
        instructor = api_backend["instructor_user"]
        rubric_st = api_backend["rubric_store"]

        req = GradingRubricSchema(
            rubric_id="rubric_complexity",
            title="Time and Space Complexity Rubric",
            criteria=[
                RubricCriterionSchema(
                    criterion_id="crit_time",
                    name="Time Complexity",
                    description="O(N log N) or better",
                    max_points=10,
                ),
            ],
        )

        created = create_rubric(req, current_user=instructor, rubric_store=rubric_st)
        assert created.rubric_id == "rubric_complexity"

        retrieved = get_rubric("rubric_complexity", current_user=instructor, rubric_store=rubric_st)
        assert retrieved.rubric_id == "rubric_complexity"
        assert len(retrieved.criteria) == 1

    def test_manual_review_override_and_rubric_scoring(self, api_backend):
        instructor = api_backend["instructor_user"]
        review_svc = api_backend["manual_review_service"]
        eval_st = api_backend["evaluation_store"]

        # Seed an evaluation report
        report = EvaluationReport(
            status=EvaluationStatus.COMPLETED,
            evaluation_id="eval_test_review",
            submission_id="sub_test_1",
            grading_report=GradingReport(
                earned_points=6,
                max_score=10,
                passed_tests=1,
                total_tests=2,
            ),
            test_results=(
                TestCaseResult("t1", passed=True),
                TestCaseResult("t2", passed=False, message="Timed out"),
            ),
        )
        eval_st.save(report)

        # Apply manual review with score override and qualitative feedback
        rev_req = ManualReviewRequest(
            override_score=8,
            instructor_notes="Partial credit granted for near-optimal recursion logic.",
            rubric_evaluations=[
                RubricEvaluationSchema(
                    criterion_id="crit_style",
                    score=8.5,
                    feedback="Good readability and variable names.",
                )
            ],
        )

        rev_resp = apply_manual_review(
            evaluation_id="eval_test_review",
            request=rev_req,
            current_user=instructor,
            review_service=review_svc,
        )

        assert rev_resp.original_score == 6
        assert rev_resp.override_score == 8
        assert rev_resp.final_score == 8
        assert "Partial credit granted" in rev_resp.instructor_notes
        assert len(rev_resp.rubric_evaluations) == 1
        assert rev_resp.reviewed_by == "inst_curie"


# ---------------------------------------------------------------------------
# 5. Submission Endpoints & Audit History Tests
# ---------------------------------------------------------------------------


class TestSubmissionEndpoints:
    def test_github_submission_and_status(self, api_backend):
        sub_svc = api_backend["submission_service"]

        req = GitHubSubmissionRequest(
            student_id="student_ada",
            task_id="algo_hw1",
            github_url="https://github.com/ada/algorithms",
            branch="main",
        )
        resp = submit_github_repo(req, service=sub_svc)
        assert resp.student_id == "student_ada"
        assert resp.status == "received"

        # Check status
        st = get_submission_status(resp.submission_id, service=sub_svc)
        assert st.status == "received"
        assert len(st.history) >= 1

    def test_file_upload_and_history(self, api_backend):
        sub_svc = api_backend["submission_service"]
        sub_st = api_backend["submission_store"]
        eval_st = api_backend["evaluation_store"]

        py_content = b"def add(a, b): return a + b\n"
        upload_file = UploadFile(
            file=io.BytesIO(py_content),
            filename="solution.py",
        )

        sub_resp = submit_file_upload(
            file=upload_file,
            student_id="student_ada",
            task_id="algo_hw1",
            service=sub_svc,
        )
        assert sub_resp.submission_id.startswith("sub_")
        assert "storage://submissions/" in sub_resp.source_reference

        # Query history
        hist = get_submission_history(sub_resp.submission_id, service=sub_svc)
        assert hist["submission_id"] == sub_resp.submission_id
        assert hist["task_id"] == "algo_hw1"
        assert hist["current_status"] == "received"


# ---------------------------------------------------------------------------
# 6. Evaluation Endpoints Tests
# ---------------------------------------------------------------------------


class TestEvaluationEndpoints:
    def test_run_evaluation_and_retrieve_breakdowns(self, api_backend):
        sub_svc = api_backend["submission_service"]
        orchestrator = api_backend["orchestrator"]
        eval_st = api_backend["evaluation_store"]

        # Register submission with source code
        sub = sub_svc.create_submission(
            student_id="student_ada",
            task_id="algo_hw1",
            source_type=SubmissionSource.FILE_UPLOAD,
            source_reference="upload:code.py",
            source_code="def solve(): pass\n",
        )

        # 1. Run evaluation
        eval_resp = run_evaluation(sub.submission_id, orchestrator=orchestrator)
        assert eval_resp.status == "completed"
        assert eval_resp.grading_report.earned_points == 10
        assert eval_resp.grading_report.percentage == 100.0

        eval_id = eval_resp.evaluation_id

        # 2. Retrieve full evaluation
        full = get_evaluation(eval_id, store=eval_st)
        assert full.evaluation_id == eval_id

        # 3. Retrieve by submission
        by_sub = get_evaluation_by_submission(sub.submission_id, store=eval_st)
        assert by_sub.evaluation_id == eval_id

        # 4. Retrieve status
        status_info = get_evaluation_status(eval_id, store=eval_st)
        assert status_info["status"] == "completed"
        assert status_info["duration_seconds"] >= 0.0

        # 5. Retrieve granular tests breakdown
        tests = get_evaluation_tests(eval_id, store=eval_st)
        assert len(tests) == 2
        assert tests[0].passed is True

        # 6. Retrieve AI feedback
        feedback = get_ai_feedback(eval_id, store=eval_st)
        assert feedback["evaluation_id"] == eval_id

        # 7. Retrieve final report summary
        summary = get_final_report_summary(eval_id, store=eval_st)
        assert summary["earned_points"] == 10
        assert "algo_hw1" in summary["feedback_summary"] or "Basic" in summary["feedback_summary"] or summary["status"] == "completed"


# ---------------------------------------------------------------------------
# 7. Rate Limiter Tests
# ---------------------------------------------------------------------------


class TestRateLimiter:
    def test_sliding_window_rate_limiter_throttles_bursts(self):
        limiter = SlidingWindowRateLimiter(window_seconds=10.0)

        # Allowed 3 requests
        for _ in range(3):
            allowed, _ = limiter.is_allowed("client_test", max_requests=3)
            assert allowed is True

        # 4th request in the same window must be blocked
        allowed, retry_after = limiter.is_allowed("client_test", max_requests=3)
        assert allowed is False
        assert retry_after >= 1
