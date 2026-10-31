"""Service layer for submission management, GitHub intake, and secure file uploads."""

from datetime import datetime, timezone
import logging
from pathlib import Path
import uuid

from evaluator.collector import SourceCollector, parse_github_url
from evaluator.exceptions import (
    DangerousFileTypeError,
    DeadlineExceededError,
    EntityNotFoundError,
    SecurityValidationError,
)
from evaluator.metadata import SubmissionMetadata
from evaluator.storage.submission_storage import (
    ControlledFileStorage,
    SubmissionStorage,
)
from evaluator.stores.assignment_store import AssignmentStore
from evaluator.stores.student_store import StudentStore
from evaluator.stores.submission_store import SubmissionStore
from evaluator.submission import (
    SubmissionRecord,
    SubmissionSource,
    SubmissionStatus,
)

logger = logging.getLogger(__name__)


class SubmissionService:
    """Coordinates submission creation, validation, storage, and lifecycle state transitions."""

    def __init__(
        self,
        submission_store: SubmissionStore,
        assignment_store: AssignmentStore,
        student_store: StudentStore | None = None,
        storage: SubmissionStorage | None = None,
    ) -> None:
        self._submission_store = submission_store
        self._assignment_store = assignment_store
        self._student_store = student_store
        self._storage = storage or ControlledFileStorage()

    def submit_github(
        self,
        student_id: str,
        task_id: str,
        github_url: str,
        branch: str = "main",
        pre_fetch: bool = False,
        token: str | None = None,
    ) -> SubmissionRecord:
        """Register a GitHub submission after URL validation, student check, and deadline enforcement."""
        # 1. Validate student & assignment & deadline
        self._validate_student_and_assignment(student_id, task_id)

        # 2. Validate URL syntax and domain
        spec = parse_github_url(github_url, default_branch=branch)
        clean_reference = f"https://github.com/{spec.owner}/{spec.repo}"
        if spec.branch != "main":
            clean_reference += f"/tree/{spec.branch}"

        # 3. Optionally pre-fetch repository content
        source_code: str | None = None
        if pre_fetch:
            bundle = SourceCollector.from_github(
                github_url=github_url,
                branch=spec.branch,
                token=token,
            )
            source_code = bundle.get_concatenated_source()

        # 4. Construct and persist submission
        metadata = SubmissionMetadata(student_id=student_id, task_id=task_id)
        record = SubmissionRecord(
            metadata=metadata,
            source_type=SubmissionSource.GITHUB,
            source_reference=clean_reference,
            source_code=source_code,
            status=SubmissionStatus.RECEIVED,
        )
        self._submission_store.save(record)
        logger.info(
            "Registered GitHub submission '%s' for student '%s' on task '%s'.",
            record.submission_id,
            student_id,
            task_id,
        )
        return record

    def submit_file_upload(
        self,
        student_id: str,
        task_id: str,
        filename: str,
        content: bytes,
    ) -> SubmissionRecord:
        """Register a direct file upload submission with security checks and controlled storage."""
        # 1. Validate student & assignment & deadline
        self._validate_student_and_assignment(student_id, task_id)

        clean_filename = Path(filename).name
        ext = Path(clean_filename).suffix.lower()

        # 2. Validate extension & parse source bundle
        if ext == ".py":
            bundle = SourceCollector.from_single_file(content, filename=clean_filename)
        elif ext == ".zip":
            bundle = SourceCollector.from_zip_bytes(content)
        else:
            raise SecurityValidationError(
                f"Unsupported submission file type '{ext}'. Allowed: .py, .zip"
            )

        source_code = bundle.get_concatenated_source()

        # 3. Store payload in controlled storage
        temp_id = f"sub_{uuid.uuid4().hex[:12]}"
        storage_ref = self._storage.store_upload(
            student_id=student_id,
            task_id=task_id,
            submission_id=temp_id,
            filename=clean_filename,
            content=content,
        )

        # 4. Construct and persist submission record
        metadata = SubmissionMetadata(student_id=student_id, task_id=task_id)
        record = SubmissionRecord(
            metadata=metadata,
            source_type=SubmissionSource.FILE_UPLOAD,
            source_reference=storage_ref,
            source_code=source_code,
            submission_id=temp_id,
            status=SubmissionStatus.RECEIVED,
        )
        self._submission_store.save(record)
        logger.info(
            "Registered file upload submission '%s' (%s) for student '%s' on task '%s'.",
            record.submission_id,
            clean_filename,
            student_id,
            task_id,
        )
        return record

    def create_submission(
        self,
        student_id: str,
        task_id: str,
        source_type: SubmissionSource,
        source_reference: str,
        source_code: str | None = None,
    ) -> SubmissionRecord:
        """Create and store a new submission after verifying student, assignment, and deadline."""
        self._validate_student_and_assignment(student_id, task_id)

        metadata = SubmissionMetadata(student_id=student_id, task_id=task_id)
        record = SubmissionRecord(
            metadata=metadata,
            source_type=source_type,
            source_reference=source_reference,
            source_code=source_code,
            status=SubmissionStatus.RECEIVED,
        )

        self._submission_store.save(record)
        return record

    def get_submission(self, submission_id: str) -> SubmissionRecord:
        """Fetch submission by ID or raise EntityNotFoundError."""
        record = self._submission_store.get(submission_id)
        if not record:
            raise EntityNotFoundError(f"Submission with ID '{submission_id}' not found.")
        return record

    def list_by_student(self, student_id: str) -> list[SubmissionRecord]:
        """Fetch all submissions for a given student."""
        return self._submission_store.list_by_student(student_id)

    def list_by_task(self, task_id: str) -> list[SubmissionRecord]:
        """Fetch all submissions for a given assignment task."""
        return self._submission_store.list_by_task(task_id)

    def update_status(
        self,
        submission_id: str,
        new_status: SubmissionStatus,
    ) -> SubmissionRecord:
        """Transition submission status and persist the update."""
        current = self.get_submission(submission_id)
        updated = current.transition_to(new_status)
        self._submission_store.update(updated)
        return updated

    def _validate_student_and_assignment(self, student_id: str, task_id: str) -> None:
        """Verify student existence, assignment existence, and deadline validity."""
        if self._student_store is not None:
            student = self._student_store.get(student_id)
            if not student:
                raise EntityNotFoundError(f"Student with ID '{student_id}' not found.")

        assignment = self._assignment_store.get(task_id)
        if not assignment:
            raise EntityNotFoundError(f"Assignment with ID '{task_id}' not found.")

        now_utc = datetime.now(timezone.utc)
        if assignment.is_past_deadline(now_utc):
            raise DeadlineExceededError(
                f"Submission rejected: deadline for '{task_id}' was {assignment.deadline}."
            )
