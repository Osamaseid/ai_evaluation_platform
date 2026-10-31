"""Source code collection, validation, security filtering, and bundle organization."""

from dataclasses import dataclass
import io
import logging
import os
from pathlib import Path
import re
import urllib.parse
import zipfile
import requests

from evaluator.exceptions import (
    CollectionError,
    DangerousFileTypeError,
    FileSizeExceededError,
    PathTraversalError,
    RepositoryAccessError,
    RepositoryNotFoundError,
    SecurityValidationError,
    ZipBombError,
)

logger = logging.getLogger(__name__)

# Security & Resource Limits
MAX_FILE_SIZE_BYTES = 512 * 1024  # 512 KB per file
MAX_TOTAL_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB total bundle uncompressed
MAX_ARCHIVE_DOWNLOAD_BYTES = 20 * 1024 * 1024  # 20 MB max zipball download
MAX_FILES_COUNT = 100
MAX_COMPRESSION_RATIO = 100.0  # Max permitted decompression ratio (Zip bomb protection)

# File Type Policies
DANGEROUS_EXTENSIONS = frozenset({
    ".exe", ".dll", ".so", ".dylib", ".bin", ".bat", ".cmd", ".sh",
    ".ps1", ".vbs", ".scr", ".pif", ".com", ".pyc", ".pyo", ".pyd",
    ".class", ".jar", ".html", ".htm", ".js", ".php", ".jsp", ".asp",
    ".aspx", ".svg", ".wasm",
})

IGNORED_DIRECTORIES = frozenset({
    "__pycache__", "venv", ".venv", "env", ".env", "node_modules",
    ".git", ".github", ".vscode", ".idea", "build", "dist",
})

_GITHUB_URL_PATTERN = re.compile(
    r"^https?://(?:www\.)?github\.com/(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+?)(?:\.git)?(?:/tree/(?P<branch>[^/]+))?/?$"
)


def _mask_token(token: str | None) -> str:
    """Mask credentials for safe audit logging."""
    if not token:
        return "<none>"
    cleaned = token.strip()
    if len(cleaned) <= 8:
        return "***"
    return f"{cleaned[:4]}...{cleaned[-4:]}"


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
    parsed = urllib.parse.urlparse(cleaned_url)

    if parsed.scheme not in ("http", "https"):
        raise CollectionError(f"Unsupported URL scheme '{parsed.scheme}'. Only HTTPS/HTTP is allowed.")

    if parsed.netloc.lower() not in ("github.com", "www.github.com"):
        raise CollectionError(f"Host '{parsed.netloc}' is not GitHub. Expected 'github.com'.")

    match = _GITHUB_URL_PATTERN.match(cleaned_url)
    if not match:
        raise CollectionError(
            f"Invalid GitHub repository URL: '{url}'. "
            "Expected format: https://github.com/<owner>/<repo> or https://github.com/<owner>/<repo>/tree/<branch>"
        )

    owner = match.group("owner")
    repo = match.group("repo")
    branch = match.group("branch") or default_branch

    # Guard against invalid path elements or traversal attempts
    if owner in {".", ".."} or repo in {".", ".."}:
        raise CollectionError(f"Invalid repository coordinates: {owner}/{repo}")

    return GitHubRepoSpec(owner=owner, repo=repo, branch=branch)


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
    def from_single_file(content: str | bytes, filename: str = "solution.py") -> SourceBundle:
        """Validate and construct a SourceBundle from a single Python file upload."""
        clean_filename = Path(filename).name

        ext = Path(clean_filename).suffix.lower()
        if ext in DANGEROUS_EXTENSIONS:
            raise DangerousFileTypeError(
                f"File '{clean_filename}' has prohibited extension '{ext}'."
            )
        if ext != ".py":
            raise CollectionError(f"Only Python source files (.py) are supported: '{clean_filename}'.")

        # Decode if bytes provided
        if isinstance(content, bytes):
            if len(content) > MAX_FILE_SIZE_BYTES:
                raise FileSizeExceededError(
                    f"Source file exceeds maximum size limit of {MAX_FILE_SIZE_BYTES} bytes."
                )
            if b"\x00" in content:
                raise SecurityValidationError(f"File '{clean_filename}' contains prohibited null bytes.")
            try:
                text_content = content.decode("utf-8")
            except UnicodeDecodeError as exc:
                raise CollectionError(f"File '{clean_filename}' is not valid UTF-8 text.") from exc
        elif isinstance(content, str):
            text_content = content
            source_bytes = len(text_content.encode("utf-8"))
            if source_bytes > MAX_FILE_SIZE_BYTES:
                raise FileSizeExceededError(
                    f"Source file exceeds maximum size limit of {MAX_FILE_SIZE_BYTES} bytes."
                )
            if "\x00" in text_content:
                raise SecurityValidationError(f"File '{clean_filename}' contains prohibited null bytes.")
        else:
            raise TypeError("content must be str or bytes.")

        if not text_content.strip():
            raise CollectionError("Source code content cannot be empty.")

        return SourceBundle(files=(SourceFile(relative_path=clean_filename, content=text_content),))

    @staticmethod
    def from_zip_bytes(archive_bytes: bytes) -> SourceBundle:
        """Safely extract Python source files from an in-memory zip archive with security defenses."""
        if not archive_bytes:
            raise CollectionError("Zip archive bytes cannot be empty.")

        if len(archive_bytes) > MAX_TOTAL_SIZE_BYTES:
            raise FileSizeExceededError(
                f"Archive size ({len(archive_bytes)} bytes) exceeds maximum limit of {MAX_TOTAL_SIZE_BYTES} bytes."
            )

        # Magic bytes check for ZIP (PK\x03\x04 or PK\x05\x06)
        if not (archive_bytes.startswith(b"PK\x03\x04") or archive_bytes.startswith(b"PK\x05\x06") or archive_bytes.startswith(b"PK\x07\x08")):
            raise CollectionError("Uploaded payload is not a valid zip archive.")

        try:
            zip_buffer = io.BytesIO(archive_bytes)
            with zipfile.ZipFile(zip_buffer, "r") as archive:
                infolist = archive.infolist()

                collected_files: list[SourceFile] = []
                total_uncompressed_bytes = 0

                for info in infolist:
                    # Ignore directories
                    if info.is_dir() or info.filename.endswith("/"):
                        continue

                    raw_name = info.filename

                    # 1. Zip Slip / Path Traversal Defense
                    norm_raw = raw_name.replace("\\", "/")
                    if "\x00" in norm_raw:
                        raise PathTraversalError(f"Null bytes detected in archive entry name: '{norm_raw}'.")

                    parts = [p for p in norm_raw.split("/") if p]
                    if any(p == ".." or p.startswith(":") for p in parts) or norm_raw.startswith("/"):
                        # Skip or drop path traversal attempts
                        logger.warning("Skipping suspicious path traversal archive entry: '%s'", raw_name)
                        continue

                    # GitHub zipballs wrap contents in an outer root directory: '<repo>-<branch>/...'
                    # Strip top-level directory if it represents the container folder
                    if len(parts) > 1 and not parts[0].endswith(".py"):
                        clean_rel_parts = parts[1:]
                    else:
                        clean_rel_parts = parts

                    clean_rel_path = "/".join(clean_rel_parts)
                    norm_path = Path(clean_rel_path).as_posix()

                    # 2. Filter out non-code directories, virtualenvs, hidden files, caches
                    if any(part.startswith(".") or part in IGNORED_DIRECTORIES for part in clean_rel_parts):
                        continue

                    # 3. Check for dangerous extensions in user project files
                    file_ext = Path(clean_rel_path).suffix.lower()
                    if file_ext in DANGEROUS_EXTENSIONS:
                        raise DangerousFileTypeError(
                            f"Archive contains prohibited file type: '{clean_rel_path}'."
                        )

                    # Filter strictly to Python files for evaluation
                    if not norm_path.endswith(".py"):
                        continue

                    # 4. Zip Bomb Defense (Decompression Ratio & Cumulative Limits)
                    if info.compress_size > 0:
                        ratio = info.file_size / info.compress_size
                        if ratio > MAX_COMPRESSION_RATIO and info.file_size > 100 * 1024:
                            raise ZipBombError(
                                f"Decompression bomb detected in entry '{clean_rel_path}' (ratio {ratio:.1f}:1)."
                            )

                    if info.file_size > MAX_FILE_SIZE_BYTES:
                        raise FileSizeExceededError(
                            f"File '{clean_rel_path}' exceeds limit of {MAX_FILE_SIZE_BYTES} bytes."
                        )

                    total_uncompressed_bytes += info.file_size
                    if total_uncompressed_bytes > MAX_TOTAL_SIZE_BYTES:
                        raise FileSizeExceededError(
                            f"Total extracted files exceed maximum limit of {MAX_TOTAL_SIZE_BYTES} bytes."
                        )

                    if len(collected_files) >= MAX_FILES_COUNT:
                        raise CollectionError(
                            f"Archive contains too many Python files (max {MAX_FILES_COUNT})."
                        )

                    with archive.open(info) as f:
                        file_bytes = f.read(MAX_FILE_SIZE_BYTES + 1)
                        if len(file_bytes) > MAX_FILE_SIZE_BYTES:
                            raise FileSizeExceededError(
                                f"Decompressed file '{clean_rel_path}' exceeds size limit."
                            )

                        if b"\x00" in file_bytes:
                            raise SecurityValidationError(
                                f"Binary/null bytes detected in Python source file '{clean_rel_path}'."
                            )

                        try:
                            file_text = file_bytes.decode("utf-8")
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
        """Fetch a GitHub repository zipball and build a SourceBundle with security controls."""
        auth_token = token or os.environ.get("GITHUB_TOKEN")
        spec = parse_github_url(github_url, default_branch=branch)

        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "ProgrammingEvaluator/1.0",
        }
        if auth_token:
            headers["Authorization"] = f"Bearer {auth_token}"

        logger.info(
            "Fetching GitHub archive for %s/%s (branch=%s, auth=%s)",
            spec.owner,
            spec.repo,
            spec.branch,
            _mask_token(auth_token),
        )

        try:
            response = requests.get(
                spec.archive_url,
                headers=headers,
                allow_redirects=True,
                stream=True,
                timeout=timeout_seconds,
            )
        except requests.RequestException as exc:
            raise CollectionError(
                f"Failed to connect to GitHub for {spec.owner}/{spec.repo}: {exc}"
            ) from exc

        if response.status_code == 404:
            raise RepositoryNotFoundError(
                f"GitHub repository '{spec.owner}/{spec.repo}' (branch '{spec.branch}') not found or is private/inaccessible."
            )
        if response.status_code in (401, 403):
            raise RepositoryAccessError(
                f"GitHub access denied (HTTP {response.status_code}) for '{spec.owner}/{spec.repo}'. "
                "Ensure a valid GITHUB_TOKEN is configured with repository read permissions."
            )
        if response.status_code != 200:
            raise CollectionError(
                f"GitHub API returned unexpected status {response.status_code} while fetching {spec.owner}/{spec.repo}."
            )

        # Enforce stream download size limit
        headers_dict = getattr(response, "headers", {}) or {}
        content_length_header = headers_dict.get("Content-Length")
        if content_length_header and str(content_length_header).isdigit():
            if int(content_length_header) > MAX_ARCHIVE_DOWNLOAD_BYTES:
                raise FileSizeExceededError(
                    f"Remote repository archive ({content_length_header} bytes) exceeds limit of {MAX_ARCHIVE_DOWNLOAD_BYTES} bytes."
                )

        if hasattr(response, "iter_content"):
            chunks = []
            downloaded = 0
            for chunk in response.iter_content(chunk_size=64 * 1024):
                if chunk:
                    downloaded += len(chunk)
                    if downloaded > MAX_ARCHIVE_DOWNLOAD_BYTES:
                        raise FileSizeExceededError(
                            f"Remote repository archive exceeded download limit of {MAX_ARCHIVE_DOWNLOAD_BYTES} bytes."
                        )
                    chunks.append(chunk)
            archive_bytes = b"".join(chunks)
        else:
            archive_bytes = getattr(response, "content", b"")
            if len(archive_bytes) > MAX_ARCHIVE_DOWNLOAD_BYTES:
                raise FileSizeExceededError(
                    f"Remote repository archive exceeded download limit of {MAX_ARCHIVE_DOWNLOAD_BYTES} bytes."
                )
        return cls.from_zip_bytes(archive_bytes)
