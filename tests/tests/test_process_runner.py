"""Tests for IsolatedProcessRunner execution engine."""

import pytest

from evaluator.assignment import AssignmentDefinition, TestCaseDefinition
from evaluator.collector import SourceCollector
from evaluator.grading import grade_submission
from evaluator.runners.process_runner import IsolatedProcessRunner


@pytest.fixture
def calculator_assignment():
    return AssignmentDefinition(
        task_id="math_ops",
        title="Basic Math Operations",
        test_cases=(
            TestCaseDefinition(
                test_case_id="test_add",
                description="Test addition",
                points=5,
                assertion="add(2, 3) == 5",
            ),
            TestCaseDefinition(
                test_case_id="test_sub",
                description="Test subtraction",
                points=5,
                assertion="subtract(10, 4) == 6",
            ),
        ),
    )


class TestIsolatedProcessRunner:
    def test_successful_execution(self, calculator_assignment):
        student_code = """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
"""
        runner = IsolatedProcessRunner(timeout_seconds=3.0)
        results = runner.run(calculator_assignment, student_code)

        assert len(results) == 2
        assert all(r.passed for r in results)

        report = grade_submission(calculator_assignment, results)
        assert report.earned_points == 10
        assert report.percentage == 100.0

    def test_partial_failure(self, calculator_assignment):
        student_code = """
def add(a, b):
    return a + b

def subtract(a, b):
    return a + b  # Buggy implementation
"""
        runner = IsolatedProcessRunner(timeout_seconds=3.0)
        results = runner.run(calculator_assignment, student_code)

        res_map = {r.test_case_id: r for r in results}
        assert res_map["test_add"].passed is True
        assert res_map["test_sub"].passed is False
        assert "Assertion failed" in res_map["test_sub"].message

        report = grade_submission(calculator_assignment, results)
        assert report.earned_points == 5
        assert report.percentage == 50.0

    def test_syntax_error_handled_gracefully(self, calculator_assignment):
        student_code = "def invalid_syntax(:::"
        runner = IsolatedProcessRunner(timeout_seconds=3.0)
        results = runner.run(calculator_assignment, student_code)

        assert all(not r.passed for r in results)
        assert "Import error" in results[0].message or "SyntaxError" in results[0].message

    def test_infinite_loop_times_out(self, calculator_assignment):
        student_code = """
def add(a, b):
    while True:
        pass
"""
        runner = IsolatedProcessRunner(timeout_seconds=1.0)
        results = runner.run(calculator_assignment, student_code)

        assert all(not r.passed for r in results)
        assert any("timed out" in (r.message or "") for r in results)

    def test_source_bundle_execution(self, calculator_assignment):
        student_code = """
def add(a, b):
    return a + b

def subtract(a, b):
    return a - b
"""
        bundle = SourceCollector.from_single_file(student_code, "solution.py")
        runner = IsolatedProcessRunner(timeout_seconds=3.0)
        results = runner.run(calculator_assignment, bundle)

        assert all(r.passed for r in results)

