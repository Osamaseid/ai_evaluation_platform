"""Tests for source code collection and GitHub ingestion."""

import io
import zipfile
import pytest
import requests

from evaluator.collector import (
    CollectionError,
    GitHubRepoSpec,
    SourceBundle,
    SourceCollector,
    SourceFile,
    parse_github_url,
)


def _create_test_zip(files: dict[str, str]) -> bytes:
    """Helper to create an in-memory zip bytes buffer."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for path, content in files.items():
            zf.writestr(path, content)
    return buf.getvalue()


class TestGitHubUrlParser:
    def test_valid_urls(self):
        spec1 = parse_github_url("https://github.com/octocat/Hello-World")
        assert spec1.owner == "octocat"
        assert spec1.repo == "Hello-World"
        assert spec1.branch == "main"

        spec2 = parse_github_url("https://github.com/student_99/cs101-task.git/")
        assert spec2.owner == "student_99"
        assert spec2.repo == "cs101-task"

    def test_custom_branch(self):
        spec = parse_github_url("https://github.com/user/repo", default_branch="develop")
        assert spec.branch == "develop"
        assert spec.archive_url == "https://api.github.com/repos/user/repo/zipball/develop"

    @pytest.mark.parametrize(
        "invalid_url",
        [
            "",
            "   ",
            "not_a_url",
            "https://gitlab.com/user/repo",
            "https://github.com/onlyuser",
            "https://github.com/user/repo/extra/parts",
        ],
    )
    def test_invalid_urls_raise_collection_error(self, invalid_url):
        with pytest.raises(CollectionError):
            parse_github_url(invalid_url)


class TestSourceBundle:
    def test_single_file_creation(self):
        bundle = SourceCollector.from_single_file("def add(a, b): return a + b\n", "solution.py")
        assert len(bundle.files) == 1
        assert bundle.primary_module.relative_path == "solution.py"
        assert "def add" in bundle.primary_module.content
        assert "File: solution.py" in bundle.get_concatenated_source()

    def test_empty_content_rejected(self):
        with pytest.raises(CollectionError, match="empty"):
            SourceCollector.from_single_file("   ")

    def test_primary_module_selection(self):
        bundle = SourceBundle(
            files=(
                SourceFile(relative_path="utils.py", content="# utils"),
                SourceFile(relative_path="solution.py", content="# solution"),
            )
        )
        assert bundle.primary_module.relative_path == "solution.py"

    def test_duplicate_file_paths_rejected(self):
        with pytest.raises(ValueError, match="Duplicate"):
            SourceBundle(
                files=(
                    SourceFile(relative_path="main.py", content="x = 1"),
                    SourceFile(relative_path="main.py", content="x = 2"),
                )
            )


class TestZipExtraction:
    def test_valid_zip_extraction(self):
        zip_bytes = _create_test_zip(
            {
                "root_dir/main.py": "print('hello')",
                "root_dir/helper.py": "def help(): pass",
                "root_dir/README.md": "# Readme",
                "root_dir/.env": "SECRET=123",
                "root_dir/__pycache__/compiled.py": "binary",
            }
        )

        bundle = SourceCollector.from_zip_bytes(zip_bytes)
        paths = [f.relative_path for f in bundle.files]

        assert "main.py" in paths
        assert "helper.py" in paths
        assert len(bundle.files) == 2  # README, .env, and __pycache__ are filtered out

    def test_zip_with_path_traversal_skipped(self):
        zip_bytes = _create_test_zip(
            {
                "root_dir/safe.py": "safe = True",
                "root_dir/../../etc/passwd.py": "danger = True",
            }
        )

        bundle = SourceCollector.from_zip_bytes(zip_bytes)
        assert len(bundle.files) == 1
        assert bundle.files[0].relative_path == "safe.py"

    def test_empty_or_non_py_zip_raises_error(self):
        zip_bytes = _create_test_zip({"docs.txt": "some documentation"})
        with pytest.raises(CollectionError, match="No valid Python source"):
            SourceCollector.from_zip_bytes(zip_bytes)

    def test_corrupt_zip_bytes_raises_error(self):
        with pytest.raises(CollectionError, match="not a valid zip"):
            SourceCollector.from_zip_bytes(b"corrupt non-zip bytes")


class TestGitHubIngestion:
    def test_successful_github_fetch(self, monkeypatch):
        fake_zip = _create_test_zip({"user-repo-abc1234/solution.py": "answer = 42"})

        class FakeResponse:
            status_code = 200
            content = fake_zip

        def fake_get(*args, **kwargs):
            return FakeResponse()

        monkeypatch.setattr(requests, "get", fake_get)

        bundle = SourceCollector.from_github("https://github.com/student/assignment1")
        assert len(bundle.files) == 1
        assert bundle.files[0].relative_path == "solution.py"
        assert "answer = 42" in bundle.files[0].content

    def test_github_404_raises_error(self, monkeypatch):
        class FakeResponse:
            status_code = 404
            content = b"Not Found"

        monkeypatch.setattr(requests, "get", lambda *a, **kw: FakeResponse())

        with pytest.raises(CollectionError, match="not found or is private"):
            SourceCollector.from_github("https://github.com/student/private-repo")

    def test_github_network_error_raises_error(self, monkeypatch):
        def fake_get(*args, **kwargs):
            raise requests.ConnectionError("Network connection refused")

        monkeypatch.setattr(requests, "get", fake_get)

        with pytest.raises(CollectionError, match="Failed to connect to GitHub"):
            SourceCollector.from_github("https://github.com/student/assignment1")

