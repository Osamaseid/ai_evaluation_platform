"""Contracts and safe development doubles for test execution."""

from typing import Protocol

from evaluator.assignment import AssignmentDefinition
from evaluator.grading import TestCaseResult


class Runner(Protocol):
    """Contract that every test runner must implement."""

    def run(
        self,
        assignment: AssignmentDefinition,
        source_code: str,
    ) -> tuple[TestCaseResult, ...]:
        """Return one result for each configured test case."""
        ...


class MockTestRunner:
    """Return predefined results without executing student code."""

    def __init__(
        self,
        results: tuple[TestCaseResult, ...],
    ) -> None:
        if not isinstance(results, tuple):
            raise TypeError("results must be a tuple.")

        if any(not isinstance(result, TestCaseResult) for result in results):
            raise TypeError("Every result must be a TestCaseResult.")

        self._results = results

    def run(
        self,
        assignment: AssignmentDefinition,
        source_code: str,
    ) -> tuple[TestCaseResult, ...]:
        """Return configured results; this does not execute source_code."""
        if not isinstance(assignment, AssignmentDefinition):
            raise TypeError("assignment must be an AssignmentDefinition.")

        if not isinstance(source_code, str):
            raise TypeError("source_code must be a string.")

        return self._results
