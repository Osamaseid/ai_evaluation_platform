import pytest

from evaluator.metadata import SubmissionMetadata
from evaluator.submission import (
    SubmissionRecord,
    SubmissionSource,
    SubmissionStatus,
)


@pytest.fixture
def metadata():
    return SubmissionMetadata(
        student_id="student001",
        task_id="python_week1",
    )


def test_github_submission_starts_as_received(metadata):
    record = SubmissionRecord(
        metadata=metadata,
        source_type=SubmissionSource.GITHUB,
        source_reference="https://github.com/example/student-task",
    )

    assert record.metadata == metadata
    assert record.source_type is SubmissionSource.GITHUB
    assert record.status is SubmissionStatus.RECEIVED


def test_file_upload_submission(metadata):
    record = SubmissionRecord(
        metadata=metadata,
        source_type=SubmissionSource.FILE_UPLOAD,
        source_reference="upload:abc123",
    )

    assert record.source_type is SubmissionSource.FILE_UPLOAD


def test_custom_status_is_preserved(metadata):
    record = SubmissionRecord(
        metadata=metadata,
        source_type=SubmissionSource.GITHUB,
        source_reference="https://github.com/example/student-task",
        status=SubmissionStatus.COMPLETED,
    )

    assert record.status is SubmissionStatus.COMPLETED


def test_empty_source_reference_is_rejected(metadata):
    with pytest.raises(ValueError):
        SubmissionRecord(
            metadata=metadata,
            source_type=SubmissionSource.FILE_UPLOAD,
            source_reference="   ",
        )


def test_invalid_source_type_is_rejected(metadata):
    with pytest.raises(TypeError):
        SubmissionRecord(
            metadata=metadata,
            source_type="github",
            source_reference="https://github.com/example/student-task",
        )


def test_invalid_status_is_rejected(metadata):
    with pytest.raises(TypeError):
        SubmissionRecord(
            metadata=metadata,
            source_type=SubmissionSource.GITHUB,
            source_reference="https://github.com/example/student-task",
            status="completed",
        )


def test_source_reference_must_be_string(metadata):
    with pytest.raises(TypeError):
        SubmissionRecord(
            metadata=metadata,
            source_type=SubmissionSource.FILE_UPLOAD,
            source_reference=None,
        )


def test_submission_record_is_immutable(metadata):
    record = SubmissionRecord(
        metadata=metadata,
        source_type=SubmissionSource.FILE_UPLOAD,
        source_reference="upload:abc123",
    )

    with pytest.raises(AttributeError):
        record.status = SubmissionStatus.COMPLETED
