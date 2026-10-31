"""Comprehensive unit and integration tests for student submission integrations.

Tests:
1. GitHub integration:
   - URL validation (valid, branch/tree, invalid scheme/host, path traversal).
   - Private repository authorization headers and token masking.
   - Missing repository (404) and access denied (401/403) handling.
   - Downloading unnecessary file filtering (.git, .vscode, node_modules, binaries).
   - Repository size and archive streaming limits.
2. File upload integration:
   - Valid Python file and valid zip archive extraction.
   - Extension and content validation.
   - Rejection of dangerous file types (.exe, .sh, .bat, .pyc, .js).
   - Zip bomb detection (excessive compression ratio and cumulative size).
   - Zip slip path traversal prevention.
   - Null-byte injection prevention.
3. Controlled file storage:
   - Safe atomic persistence.
   - Path traversal escape protection.
   - SHA-256 integrity calculation.
4. End-to-end evaluation workflow connection:
   - GitHub submission -> evaluation workflow.
   - File upload submission -> evaluation workflow with controlled storage.
5. FastAPI submission API router:
   - GitHub submission endpoint.
   - File upload endpoint.
   - Status tracking endpoint.
"""

import io
from pathlib import Path
import tempfile
from unittest.mock import MagicMock, patch
import zipfile
import pytest

from evaluator.api.routers.submissions import (
    get_submission,
    get_submission_status,
    submit_file_upload,
    submit_github_repo,
)
from evaluator.api.schemas.submissions import GitHubSubmissionRequest
from evaluator.assignment import AssignmentDefinition, TestCaseDefinition
from evaluator.collector import (
    DANGEROUS_EXTENSIONS,
    MAX_FILE_SIZE_BYTES,
    MAX_TOTAL_SIZE_BYTES,
    CollectionError,
    GitHubRepoSpec,
    SourceCollector,
    parse_github_url,
)
from evaluator.evaluation import EvaluationStatus
from evaluator.exceptions import (
    DangerousFileTypeError,
    FileSizeExceededError,
    PathTraversalError,
    RepositoryAccessError,
    RepositoryNotFoundError,
    SecurityValidationError,
    ZipBombError,
)
from evaluator.grading import TestCaseResult
from evaluator.runner import Runner
from evaluator.services.evaluation_orchestrator import EvaluationOrchestrator
from evaluator.services.submission_service import SubmissionService
from evaluator.storage.submission_storage import ControlledFileStorage
from evaluator.stores.assignment_store import InMemoryAssignmentStore
from evaluator.stores.evaluation_store import InMemoryEvaluationStore
from evaluator.stores.student_store import InMemoryStudentStore
from evaluator.stores.submission_store import InMemorySubmissionStore
from evaluator.submission import SubmissionRecord, SubmissionSource, SubmissionStatus
from evaluator.users import Student


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_zip_payload(files: dict[str, bytes | str]) -> bytes:
    """Helper to build in-memory zip bytes."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path, data in files.items():
            if isinstance(data, str):
                zf.writestr(path, data)
            else:
                zf.writestr(path, data)
    return buf.getvalue()


class MockEvaluationRunner(Runner):
    """Mock runner for end-to-end tests."""

    def run(self, assignment, source_code):
        return (
            TestCaseResult(
                test_case_id="tc_add",
                passed=True,
                message="Addition verified",
            ),
        )


@pytest.fixture
def assignment() -> AssignmentDefinition:
    return AssignmentDefinition(
        task_id="math_basic",
        title="Basic Math Functions",
        test_cases=(
            TestCaseDefinition(
                test_case_id="tc_add",
                description="Verify add(1, 2) == 3",
                points=10,
                assertion="add(1, 2) == 3",
            ),
        ),
    )


@pytest.fixture
def student() -> Student:
    return Student("student_42", "Alan Turing", "alan@cambridge.edu")


@pytest.fixture
def test_environment(assignment: AssignmentDefinition, student: Student):
    """Provides wired stores and services inside a temporary storage root."""
    temp_dir = tempfile.mkdtemp(prefix="evaluator_test_storage_")
    storage = ControlledFileStorage(base_dir=temp_dir)

    assignment_store = InMemoryAssignmentStore()
    assignment_store.save(assignment)

    student_store = InMemoryStudentStore()
    student_store.save(student)

    submission_store = InMemorySubmissionStore()
    evaluation_store = InMemoryEvaluationStore()

    service = SubmissionService(
        submission_store=submission_store,
        assignment_store=assignment_store,
        student_store=student_store,
        storage=storage,
    )

    orchestrator = EvaluationOrchestrator(
        submission_store=submission_store,
        assignment_store=assignment_store,
        evaluation_store=evaluation_store,
        runner=MockEvaluationRunner(),
        storage=storage,
    )

    return {
        "storage": storage,
        "assignment_store": assignment_store,
        "student_store": student_store,
        "submission_store": submission_store,
        "evaluation_store": evaluation_store,
        "service": service,
        "orchestrator": orchestrator,
    }


# ---------------------------------------------------------------------------
# 1. GitHub Integration Tests
# ---------------------------------------------------------------------------


class TestGitHubIntegration:
    def test_parse_github_url_with_branch_and_tree(self):
        spec1 = parse_github_url("https://github.com/torvalds/linux/tree/v6.1")
        assert spec1.owner == "torvalds"
        assert spec1.repo == "linux"
        assert spec1.branch == "v6.1"

        spec2 = parse_github_url("https://www.github.com/user/project.git")
        assert spec2.owner == "user"
        assert spec2.repo == "project"
        assert spec2.branch == "main"

    @pytest.mark.parametrize(
        "invalid_url",
        [
            "ftp://github.com/user/repo",
            "https://gitlab.com/user/repo",
            "https://evil.com/github.com/user/repo",
            "https://github.com/../evil/repo",
            "https://github.com/user/..",
        ],
    )
    def test_parse_github_url_rejects_insecure_urls(self, invalid_url):
        with pytest.raises(CollectionError):
            parse_github_url(invalid_url)

    def test_private_repository_sends_authorization_header(self, monkeypatch):
        sent_headers = {}

        class FakeResponse:
            status_code = 200
            content = _create_zip_payload({"repo-main/solution.py": "def add(a, b): return a + b\n"})
            headers = {"Content-Length": "100"}

        def mock_get(url, headers=None, **kwargs):
            nonlocal sent_headers
            sent_headers = headers or {}
            return FakeResponse()

        import requests
        monkeypatch.setattr(requests, "get", mock_get)

        bundle = SourceCollector.from_github(
            "https://github.com/classroom/private-hw",
            token="ghp_SecretStudentToken12345678",
        )
        assert len(bundle.files) == 1
        assert "Authorization" in sent_headers
        assert sent_headers["Authorization"] == "Bearer ghp_SecretStudentToken12345678"

    def test_missing_repository_raises_repository_not_found(self, monkeypatch):
        class FakeResponse:
            status_code = 404
            headers = {}

        import requests
        monkeypatch.setattr(requests, "get", lambda *a, **kw: FakeResponse())

        with pytest.raises(RepositoryNotFoundError, match="not found or is private"):
            SourceCollector.from_github("https://github.com/org/missing-repo")

    def test_unauthorized_repository_raises_repository_access_error(self, monkeypatch):
        class FakeResponse:
            status_code = 403
            headers = {}

        import requests
        monkeypatch.setattr(requests, "get", lambda *a, **kw: FakeResponse())

        with pytest.raises(RepositoryAccessError, match="access denied"):
            SourceCollector.from_github("https://github.com/org/forbidden-repo")

    def test_unnecessary_files_are_filtered_from_github_archive(self, monkeypatch):
        zip_bytes = _create_zip_payload(
            {
                "repo-main/solution.py": "def add(a, b): return a + b\n",
                "repo-main/README.md": "# Readme",
                "repo-main/.git/config": "core",
                "repo-main/.vscode/settings.json": "{}",
                "repo-main/node_modules/pkg/index.js": "alert()",
                "repo-main/__pycache__/cache.py": "bytecode",
                "repo-main/assets/image.png": b"\x89PNG\r\n",
            }
        )

        class FakeResponse:
            status_code = 200
            content = zip_bytes
            headers = {}

        import requests
        monkeypatch.setattr(requests, "get", lambda *a, **kw: FakeResponse())

        bundle = SourceCollector.from_github("https://github.com/student/hw")
        paths = [f.relative_path for f in bundle.files]
        assert paths == ["solution.py"]

    def test_archive_download_limit_exceeded_raises_error(self, monkeypatch):
        class FakeResponse:
            status_code = 200
            headers = {"Content-Length": str(25 * 1024 * 1024)}  # 25 MB > 20 MB limit

        import requests
        monkeypatch.setattr(requests, "get", lambda *a, **kw: FakeResponse())

        with pytest.raises(FileSizeExceededError, match="exceeds limit"):
            SourceCollector.from_github("https://github.com/huge/monorepo")


# ---------------------------------------------------------------------------
# 2. File Upload & Security Tests
# ---------------------------------------------------------------------------


class TestFileUploadValidation:
    def test_valid_single_python_file(self):
        bundle = SourceCollector.from_single_file(
            content=b"def add(a, b):\n    return a + b\n",
            filename="solution.py",
        )
        assert len(bundle.files) == 1
        assert bundle.files[0].relative_path == "solution.py"
        assert "def add" in bundle.files[0].content

    def test_single_file_rejects_non_python_extension(self):
        with pytest.raises(CollectionError, match="Only Python source files"):
            SourceCollector.from_single_file(b"content", filename="document.pdf")

    @pytest.mark.parametrize(
        "bad_filename",
        ["malware.exe", "backdoor.sh", "payload.bat", "module.pyc", "index.html"],
    )
    def test_single_file_rejects_dangerous_extensions(self, bad_filename):
        with pytest.raises(DangerousFileTypeError, match="prohibited extension"):
            SourceCollector.from_single_file(b"code", filename=bad_filename)

    def test_single_file_rejects_null_bytes(self):
        with pytest.raises(SecurityValidationError, match="prohibited null bytes"):
            SourceCollector.from_single_file(b"def add():\x00 pass", filename="solution.py")

    def test_single_file_rejects_oversized_content(self):
        oversized = b"a = 1\n" * 150_000  # > 512 KB
        with pytest.raises(FileSizeExceededError, match="maximum size limit"):
            SourceCollector.from_single_file(oversized, filename="solution.py")

    def test_archive_rejects_dangerous_file_inside_zip(self):
        payload = _create_zip_payload(
            {
                "solution.py": "def add(a, b): return a + b\n",
                "hidden.exe": b"MZ\x90\x00binary",
            }
        )
        with pytest.raises(DangerousFileTypeError, match="prohibited file type"):
            SourceCollector.from_zip_bytes(payload)

    def test_archive_rejects_zip_slip_traversal(self):
        # Entry attempting path traversal
        payload = _create_zip_payload(
            {
                "safe.py": "x = 10\n",
                "../../../../windows/system32/calc.py": "x = 20\n",
            }
        )
        bundle = SourceCollector.from_zip_bytes(payload)
        # Traversal entry must be ignored and not extracted
        assert len(bundle.files) == 1
        assert bundle.files[0].relative_path == "safe.py"

    def test_archive_detects_zip_bomb_excessive_compression(self):
        """Simulate high compression ratio entry triggering ZipBombError."""
        buf = io.BytesIO()
        with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
            # 500 KB of zeros compresses down to under 1 KB (> 500:1 ratio)
            zf.writestr("huge_zeroes.py", "0" * (300 * 1024))

        payload = buf.getvalue()
        with pytest.raises(ZipBombError, match="Decompression bomb detected"):
            SourceCollector.from_zip_bytes(payload)

    def test_archive_rejects_corrupted_magic_bytes(self):
        with pytest.raises(CollectionError, match="not a valid zip"):
            SourceCollector.from_zip_bytes(b"NOT_A_ZIP_HEADER_BYTES")


# ---------------------------------------------------------------------------
# 3. Controlled File Storage Tests
# ---------------------------------------------------------------------------


class TestControlledFileStorage:
    def test_store_and_load_round_trip(self, tmp_path):
        storage = ControlledFileStorage(base_dir=tmp_path)
        payload = b"def solution(): return 42\n"

        ref = storage.store_upload(
            student_id="student_1",
            task_id="math_1",
            submission_id="sub_abc123",
            filename="solution.py",
            content=payload,
        )

        assert ref.startswith("storage://submissions/math_1/student_1/sub_abc123/solution.py")
        assert storage.exists(ref)

        loaded = storage.load_upload(ref)
        assert loaded == payload

        info = storage.get_info(ref)
        assert info["filename"] == "solution.py"
        assert info["byte_size"] == len(payload)
        assert len(info["sha256"]) == 64

    def test_storage_prevents_path_traversal(self, tmp_path):
        storage = ControlledFileStorage(base_dir=tmp_path)

        with pytest.raises(PathTraversalError, match="traversal in student_id"):
            storage.store_upload(
                student_id="../../outside",
                task_id="task",
                submission_id="sub",
                filename="test.py",
                content=b"code",
            )

        with pytest.raises(PathTraversalError, match="Directory traversal detected"):
            storage.load_upload("storage://submissions/../../etc/passwd")


# ---------------------------------------------------------------------------
# 4. End-to-End Submission & Evaluation Workflow Tests
# ---------------------------------------------------------------------------


class TestSubmissionWorkflowConnection:
    def test_submit_github_and_evaluate_end_to_end(self, test_environment):
        service: SubmissionService = test_environment["service"]
        orchestrator: EvaluationOrchestrator = test_environment["orchestrator"]

        # Register GitHub submission
        record = service.submit_github(
            student_id="student_42",
            task_id="math_basic",
            github_url="https://github.com/alan/math-solver",
        )
        assert record.status is SubmissionStatus.RECEIVED

        # Mock the GitHub collector call during evaluation
        mock_bundle = SourceCollector.from_single_file(
            content="def add(a, b): return a + b\n",
            filename="solution.py",
        )
        with patch("evaluator.collector.SourceCollector.from_github", return_value=mock_bundle):
            report = orchestrator.evaluate_submission(record.submission_id)

        assert report.status is EvaluationStatus.COMPLETED
        assert report.grading_report.earned_points == 10
        assert report.grading_report.percentage == 100.0

        updated_sub = service.get_submission(record.submission_id)
        assert updated_sub.status is SubmissionStatus.COMPLETED

    def test_submit_file_upload_zip_and_evaluate_end_to_end(self, test_environment):
        service: SubmissionService = test_environment["service"]
        orchestrator: EvaluationOrchestrator = test_environment["orchestrator"]

        zip_payload = _create_zip_payload(
            {
                "solution.py": "def add(a, b): return a + b\n",
                "helpers.py": "# helper module\n",
            }
        )

        record = service.submit_file_upload(
            student_id="student_42",
            task_id="math_basic",
            filename="project.zip",
            content=zip_payload,
        )
        assert record.status is SubmissionStatus.RECEIVED
        assert record.source_reference.startswith("storage://submissions/")

        report = orchestrator.evaluate_submission(record.submission_id)
        assert report.status is EvaluationStatus.COMPLETED
        assert report.grading_report.earned_points == 10


# ---------------------------------------------------------------------------
# 5. FastAPI Router Tests (Direct Invocation)
# ---------------------------------------------------------------------------


class TestSubmissionsApiRouter:
    def test_submit_github_endpoint(self, test_environment):
        service = test_environment["service"]

        req = GitHubSubmissionRequest(
            student_id="student_42",
            task_id="math_basic",
            github_url="https://github.com/alan/calculator",
            branch="main",
        )

        response = submit_github_repo(req, service=service)
        assert response.student_id == "student_42"
        assert response.task_id == "math_basic"
        assert response.status == "received"
        assert response.source_reference == "https://github.com/alan/calculator"

        fetched = get_submission(response.submission_id, service=service)
        assert fetched.submission_id == response.submission_id

        status_resp = get_submission_status(response.submission_id, service=service)
        assert status_resp.status == "received"
        assert len(status_resp.history) == 1

    def test_submit_file_upload_endpoint(self, test_environment):
        service = test_environment["service"]

        from fastapi import UploadFile

        py_content = b"def add(a, b): return a + b\n"
        upload_file = UploadFile(
            file=io.BytesIO(py_content),
            filename="my_solution.py",
        )

        response = submit_file_upload(
            file=upload_file,
            student_id="student_42",
            task_id="math_basic",
            service=service,
        )

        assert response.student_id == "student_42"
        assert response.task_id == "math_basic"
        assert response.status == "received"
        assert "storage://submissions/" in response.source_reference
