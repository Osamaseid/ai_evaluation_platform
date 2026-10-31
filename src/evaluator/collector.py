"""Source code collection, validation, and bundle organization."""

from dataclasses import dataclass
import io
import os
from pathlib import Path
import re
import urllib.parse
import zipfile
import requests


# Maximum sizes to protect against denial-of-service / memory exhaustion
MAX_FILE_SIZE_BYTES = 512 * 1024  # 512 KB per file
MAX_TOTAL_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB total bundle
MAX_FILES_COUNT = 100

_GITHUB_URL_PATTERN = re.compile(
    r"^https?://github\.com/(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+?)(?:\.git)?/?$"
)


class CollectionError(Exception):
    """Raised when source code collection or validation fails."""


@dataclass(frozen=True)
class GitHubRepoSpec:
    """Parsed GitHub repository coordinates."""

    owner: str
    repo: str
    branch: str = "main"

    @property
    def archive_url(self) -> str:
        """Tarball/zipball download URL on GitHub."""
        return f"https://api.github.com/repos/{self.owner}/{self.repo}/zipball/{self.branch}"


def parse_github_url(url: str, default_branch: str = "main") -> GitHubRepoSpec:
    """Validate and parse a GitHub repository URL."""
    if not isinstance(url, str) or not url.strip():
        raise CollectionError("GitHub URL cannot be empty.")

    cleaned_url = url.strip()
    match = _GITHUB_URL_PATTERN.match(cleaned_url)
    if not match:
        raise CollectionError(
            f"Invalid GitHub repository URL: '{url}'. "
            "Expected format: https://github.com/<owner>/<repo>"
        )

    owner = match.group("owner")
    repo = match.group("repo")

    # Guard against invalid path elements or traversal attempts
    if owner in {".", ".."} or repo in {".", ".."}:
        raise CollectionError(f"Invalid repository coordinates: {owner}/{repo}")

    return GitHubRepoSpec(owner=owner, repo=repo, branch=default_branch)


@dataclass(frozen=True)
class SourceFile:
    """One validated source code file."""

    relative_path: str
    content: str

    def __post_init__(self) -> None:
        normalized = Path(self.relative_path).as_posix()
        if not normalized or normalized.startswith("/") or ".." in normalized.split("/"):
            raise ValueError(f"Insecure or invalid relative path: {self.relative_path}")
        if not normalized.endswith(".py"):
            raise ValueError(f"Only Python source files (.py) are supported: {self.relative_path}")


@dataclass(frozen=True)
class SourceBundle:
    """An immutable bundle of collected Python source files for an assignment."""

    files: tuple[SourceFile, ...]

    def __post_init__(self) -> None:
        if not self.files:
            raise ValueError("SourceBundle cannot be empty.")

        # Ensure paths are unique
        paths = [f.relative_path for f in self.files]
        if len(paths) != len(set(paths)):
            raise ValueError("Duplicate file paths found in source bundle.")

    @property
    def primary_module(self) -> SourceFile:
        """Return the primary source file (e.g. main.py, solution.py, or the first file)."""
        candidates = ("solution.py", "main.py", "app.py", "assignment.py")
        by_name = {Path(f.relative_path).name: f for f in self.files}
        for name in candidates:
            if name in by_name:
                return by_name[name]
        return self.files[0]

    def get_concatenated_source(self) -> str:
        """Format all source files for inspection or AI review context."""
        chunks = []
        for file in self.files:
            chunks.append(f"# --- File: {file.relative_path} ---\n{file.content}\n")
        return "\n".join(chunks)


class SourceCollector:
    """Safely collects, filters, and bundles Python source code from multiple channels."""

    @staticmethod
    def from_single_file(content: str, filename: str = "solution.py") -> SourceBundle:
        """Create a SourceBundle from a single raw Python script."""
        if not isinstance(content, str) or not content.strip():
            raise CollectionError("Source code content cannot be empty.")

        if not filename.endswith(".py"):
            filename = f"{filename}.py"

        source_bytes = len(content.encode("utf-8"))
        if source_bytes > MAX_FILE_SIZE_BYTES:
            raise CollectionError(
                f"Source file exceeds maximum size limit of {MAX_FILE_SIZE_BYTES} bytes."
            )

        return SourceBundle(files=(SourceFile(relative_path=filename, content=content),))

    @staticmethod
    def from_zip_bytes(archive_bytes: bytes) -> SourceBundle:
        """Extract Python source files from an in-memory zip archive (e.g., file upload or GitHub zipball)."""
        if not archive_bytes:
            raise CollectionError("Zip archive bytes cannot be empty.")

        if len(archive_bytes) > MAX_TOTAL_SIZE_BYTES:
            raise CollectionError(
                f"Archive size exceeds maximum allowed limit of {MAX_TOTAL_SIZE_BYTES} bytes."
            )

        try:
            zip_buffer = io.BytesIO(archive_bytes)
            with zipfile.ZipFile(zip_buffer, "r") as archive:
                namelist = archive.namelist()

                collected_files: list[SourceFile] = []
                total_bytes = 0

                for raw_name in namelist:
                    # Ignore directories
                    if raw_name.endswith("/"):
                        continue

                    # Filter strictly to Python files
                    if not raw_name.endswith(".py"):
                        continue

                    # GitHub zipballs wrap contents in an outer root directory: '<repo>-<branch>/...'
                    # Strip top-level directory if present
                    parts = raw_name.split("/")
                    if len(parts) > 1 and not parts[0].endswith(".py"):
                        clean_rel_path = "/".join(parts[1:])
                    else:
                        clean_rel_path = raw_name

                    # Security checks: prevent path traversal attacks
                    norm_path = Path(clean_rel_path).as_posix()
                    if norm_path.startswith("/") or ".." in norm_path.split("/"):
                        continue

                    # Ignore hidden files, virtualenvs, and pycache
                    if any(part.startswith(".") or part in ("__pycache__", "venv", ".venv") for part in norm_path.split("/")):
                        continue

                    info = archive.getinfo(raw_name)
                    if info.file_size > MAX_FILE_SIZE_BYTES:
                        raise CollectionError(
                            f"File '{clean_rel_path}' exceeds limit of {MAX_FILE_SIZE_BYTES} bytes."
                        )

                    total_bytes += info.file_size
                    if total_bytes > MAX_TOTAL_SIZE_BYTES:
                        raise CollectionError(
                            f"Total extracted files exceed maximum limit of {MAX_TOTAL_SIZE_BYTES} bytes."
                        )

                    if len(collected_files) >= MAX_FILES_COUNT:
                        raise CollectionError(
                            f"Archive contains too many Python files (max {MAX_FILES_COUNT})."
                        )

                    with archive.open(raw_name) as f:
                        try:
                            file_text = f.read().decode("utf-8")
                        except UnicodeDecodeError as exc:
                            raise CollectionError(
                                f"File '{clean_rel_path}' is not valid UTF-8 text."
                            ) from exc

                        collected_files.append(
                            SourceFile(relative_path=norm_path, content=file_text)
                        )

                if not collected_files:
                    raise CollectionError("No valid Python source files (.py) found in archive.")

                return SourceBundle(files=tuple(collected_files))

        except zipfile.BadZipFile as exc:
            raise CollectionError("Uploaded payload is not a valid zip archive.") from exc

    @classmethod
    def from_github(
        cls,
        github_url: str,
        branch: str = "main",
        token: str | None = None,
        timeout_seconds: int = 15,
    ) -> SourceBundle:
        """Fetch a GitHub repository zipball and build a SourceBundle."""
        spec = parse_github_url(github_url, default_branch=branch)

        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "ProgrammingEvaluator/1.0",
        }
        if token:
            headers["Authorization"] = f"Bearer {token}"

        try:
            response = requests.get(
                spec.archive_url,
                headers=headers,
                allow_redirects=True,
                timeout=timeout_seconds,
            )
        except requests.RequestException as exc:
            raise CollectionError(
                f"Failed to connect to GitHub for {spec.owner}/{spec.repo}: {exc}"
            ) from exc

        if response.status_code == 404:
            raise CollectionError(
                f"GitHub repository '{spec.owner}/{spec.repo}' (branch '{spec.branch}') not found or is private."
            )
        if response.status_code != 200:
            raise CollectionError(
                f"GitHub API returned unexpected status {response.status_code} while fetching {spec.owner}/{spec.repo}."
            )

        return cls.from_zip_bytes(response.content)

