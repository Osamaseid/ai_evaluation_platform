"""Controlled submission storage interface and filesystem implementation."""

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import re
import tempfile
from typing import Any, Protocol

from evaluator.exceptions import EntityNotFoundError, PathTraversalError


class SubmissionStorage(Protocol):
    """Storage contract for untrusted student submission uploads."""

    def store_upload(
        self,
        student_id: str,
        task_id: str,
        submission_id: str,
        filename: str,
        content: bytes,
    ) -> str:
        """Persist an uploaded artifact safely and return a canonical storage reference."""
        ...

    def load_upload(self, storage_ref: str) -> bytes:
        """Retrieve raw bytes for a stored submission artifact."""
        ...

    def delete_upload(self, storage_ref: str) -> None:
        """Delete stored submission artifact."""
        ...

    def exists(self, storage_ref: str) -> bool:
        """Check if an artifact exists in controlled storage."""
        ...

    def get_info(self, storage_ref: str) -> dict[str, Any]:
        """Return metadata (size, sha256 checksum, timestamps) for a stored artifact."""
        ...


@dataclass(frozen=True)
class StoredArtifactMetadata:
    """Audit metadata for a stored submission payload."""

    storage_ref: str
    sha256: str
    byte_size: int
    filename: str
    stored_at: datetime


class ControlledFileStorage:
    """Filesystem storage with strict path-traversal isolation and integrity hashing."""

    _SAFE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_.-]+$")

    def __init__(self, base_dir: str | Path | None = None) -> None:
        if base_dir is None:
            # Default to a dedicated local directory
            self._base_dir = Path(".data/submissions").resolve()
        else:
            self._base_dir = Path(base_dir).resolve()

        self._base_dir.mkdir(parents=True, exist_ok=True)

    @property
    def base_dir(self) -> Path:
        """Return the resolved storage root path."""
        return self._base_dir

    def _sanitize_component(self, name: str, field_name: str) -> str:
        """Verify path component has no traversal tokens."""
        if not name or not isinstance(name, str):
            raise PathTraversalError(f"{field_name} must be a non-empty string.")

        clean = name.strip()
        if not self._SAFE_ID_PATTERN.match(clean) or clean in (".", ".."):
            raise PathTraversalError(
                f"Disallowed characters or traversal in {field_name}: '{name}'."
            )
        return clean

    def _resolve_safe_path(self, storage_ref: str) -> Path:
        """Resolve a storage reference into an absolute Path and verify boundary confinement."""
        if not storage_ref or not isinstance(storage_ref, str):
            raise PathTraversalError("Invalid storage reference.")

        prefix = "storage://submissions/"
        if storage_ref.startswith(prefix):
            rel_part = storage_ref[len(prefix):]
        else:
            rel_part = storage_ref

        # Check for traversal attempts
        parts = Path(rel_part).as_posix().split("/")
        if any(p in (".", "..") for p in parts) or rel_part.startswith("/") or "\\" in rel_part:
            raise PathTraversalError(f"Directory traversal detected in storage ref: '{storage_ref}'.")

        target_path = (self._base_dir / rel_part).resolve()

        # Enforce boundary: target must be inside base_dir
        try:
            target_path.relative_to(self._base_dir)
        except ValueError as exc:
            raise PathTraversalError(
                f"Path traversal escape detected: '{storage_ref}' points outside storage root."
            ) from exc

        return target_path

    def store_upload(
        self,
        student_id: str,
        task_id: str,
        submission_id: str,
        filename: str,
        content: bytes,
    ) -> str:
        """Store an upload payload atomically inside task/student/submission directory."""
        if not isinstance(content, (bytes, bytearray)):
            raise TypeError("content must be bytes.")

        clean_task = self._sanitize_component(task_id, "task_id")
        clean_student = self._sanitize_component(student_id, "student_id")
        clean_sub = self._sanitize_component(submission_id, "submission_id")
        clean_file = self._sanitize_component(Path(filename).name, "filename")

        target_dir = self._base_dir / clean_task / clean_student / clean_sub
        target_dir.mkdir(parents=True, exist_ok=True)

        target_file = target_dir / clean_file

        # Atomic write: write to temp file then rename
        temp_fd, temp_path = tempfile.mkstemp(dir=target_dir, prefix=".tmp_")
        try:
            with os.fdopen(temp_fd, "wb") as f:
                f.write(content)
                f.flush()
                os.fsync(f.fileno())

            # Atomic replace
            os.replace(temp_path, target_file)
        except Exception:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

        rel_path = f"{clean_task}/{clean_student}/{clean_sub}/{clean_file}"
        return f"storage://submissions/{rel_path}"

    def load_upload(self, storage_ref: str) -> bytes:
        """Load artifact content bytes."""
        path = self._resolve_safe_path(storage_ref)
        if not path.is_file():
            raise EntityNotFoundError(f"Stored submission artifact not found: '{storage_ref}'.")

        with open(path, "rb") as f:
            return f.read()

    def delete_upload(self, storage_ref: str) -> None:
        """Remove artifact from storage."""
        path = self._resolve_safe_path(storage_ref)
        if path.is_file():
            path.unlink()

    def exists(self, storage_ref: str) -> bool:
        """Check existence of stored artifact."""
        try:
            path = self._resolve_safe_path(storage_ref)
            return path.is_file()
        except PathTraversalError:
            return False

    def get_info(self, storage_ref: str) -> dict[str, Any]:
        """Compute checksum, size, and timestamps for stored artifact."""
        content = self.load_upload(storage_ref)
        sha256 = hashlib.sha256(content).hexdigest()
        path = self._resolve_safe_path(storage_ref)
        stat = path.stat()

        return {
            "storage_ref": storage_ref,
            "filename": path.name,
            "byte_size": len(content),
            "sha256": sha256,
            "modified_at": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
        }

