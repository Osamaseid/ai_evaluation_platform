"""Tests for Student and Instructor models, stores, and services."""

import pytest

from evaluator.exceptions import (
    DuplicateEntityError,
    EntityNotFoundError,
    EntityValidationError,
)
from evaluator.services.instructor_service import InstructorService
from evaluator.services.student_service import StudentService
from evaluator.stores.instructor_store import InMemoryInstructorStore
from evaluator.stores.student_store import InMemoryStudentStore
from evaluator.users import Instructor, Student


class TestUserModelValidation:
    def test_valid_student(self):
        student = Student(student_id="student_1", name="Grace Hopper", email="grace@navy.mil")
        assert student.student_id == "student_1"
        assert student.name == "Grace Hopper"
        assert student.email == "grace@navy.mil"

    def test_valid_instructor(self):
        instructor = Instructor(instructor_id="prof_01", name="Alan Turing", email="alan@manchester.ac.uk")
        assert instructor.instructor_id == "prof_01"
        assert instructor.name == "Alan Turing"

    @pytest.mark.parametrize("invalid_id", ["", "   ", "user/hack", "../traversal", "a" * 51])
    def test_invalid_student_id_rejected(self, invalid_id):
        with pytest.raises(EntityValidationError):
            Student(student_id=invalid_id, name="Test", email="test@example.com")

    @pytest.mark.parametrize("invalid_email", ["", "no-at-sign", "user@", "@domain.com", "user@domain"])
    def test_invalid_email_rejected(self, invalid_email):
        with pytest.raises(EntityValidationError):
            Student(student_id="student1", name="Test", email=invalid_email)

    def test_empty_name_rejected(self):
        with pytest.raises(EntityValidationError):
            Student(student_id="student1", name="   ", email="test@example.com")


class TestStudentService:
    @pytest.fixture
    def service(self):
        return StudentService(InMemoryStudentStore())

    def test_register_and_get_student(self, service):
        registered = service.register_student("std_001", "Barbara Liskov", "barbara@mit.edu")
        assert registered.student_id == "std_001"

        retrieved = service.get_student("std_001")
        assert retrieved == registered

    def test_duplicate_student_id_rejected(self, service):
        service.register_student("std_001", "Barbara", "barbara@mit.edu")
        with pytest.raises(DuplicateEntityError):
            service.register_student("std_001", "Another Name", "other@mit.edu")

    def test_duplicate_student_email_rejected(self, service):
        service.register_student("std_001", "Barbara", "barbara@mit.edu")
        with pytest.raises(DuplicateEntityError):
            service.register_student("std_002", "Other", "barbara@mit.edu")

    def test_get_nonexistent_student_raises_error(self, service):
        with pytest.raises(EntityNotFoundError):
            service.get_student("unknown_std")


class TestInstructorService:
    @pytest.fixture
    def service(self):
        return InstructorService(InMemoryInstructorStore())

    def test_register_and_get_instructor(self, service):
        registered = service.register_instructor("inst_01", "Edsger Dijkstra", "dijkstra@cs.utexas.edu")
        assert registered.instructor_id == "inst_01"

        retrieved = service.get_instructor("inst_01")
        assert retrieved == registered

    def test_duplicate_instructor_rejected(self, service):
        service.register_instructor("inst_01", "Edsger", "dijkstra@cs.utexas.edu")
        with pytest.raises(DuplicateEntityError):
            service.register_instructor("inst_01", "Edsger", "other@cs.utexas.edu")

    def test_get_nonexistent_instructor_raises_error(self, service):
        with pytest.raises(EntityNotFoundError):
            service.get_instructor("unknown_inst")

