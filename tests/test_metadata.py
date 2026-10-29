import pytest

from evaluator.metadata import SubmissionMetadata


def test_valid_metadata_is_created():
    metadata = SubmissionMetadata(
        student_id="student001",
        task_id="python_week1",
    )

    assert metadata.student_id == "student001"
    assert metadata.task_id == "python_week1"


@pytest.mark.parametrize(
    "invalid_id",
    [
        "",
        "../student",
        "student/001",
        "student 001",
        "a" * 51,
    ],
)
def test_invalid_student_id_is_rejected(invalid_id):
    with pytest.raises(ValueError):
        SubmissionMetadata(
            student_id=invalid_id,
            task_id="python_week1",
        )


def test_invalid_task_id_is_rejected():
    with pytest.raises(ValueError):
        SubmissionMetadata(
            student_id="student001",
            task_id="../task",
        )


def test_metadata_is_immutable():
    metadata = SubmissionMetadata(
        student_id="student001",
        task_id="python_week1",
    )

    with pytest.raises(AttributeError):
        metadata.student_id = "student002"
