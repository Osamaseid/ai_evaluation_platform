"""Tests for controlled tool calling, authorization, audit logging, and agent workflow."""

from datetime import datetime, timezone
import pytest

from evaluator.assignment import AssignmentDefinition, TestCaseDefinition
from evaluator.evaluation import EvaluationReport, EvaluationStatus
from evaluator.grading import GradingReport, TestCaseResult
from evaluator.stores.assignment_store import InMemoryAssignmentStore
from evaluator.stores.evaluation_store import InMemoryEvaluationStore
from evaluator.stores.submission_store import InMemorySubmissionStore
from evaluator.submission import (
    SubmissionMetadata,
    SubmissionRecord,
    SubmissionSource,
    SubmissionStatus,
)
from evaluator.tools.audit import ToolAuditLogger, ToolExecutionStatus
from evaluator.tools.context import EvaluationSecurityContext
from evaluator.tools.registry import (
    ToolDefinition,
    ToolRegistry,
    create_default_tool_registry,
)
from evaluator.tools.agent import ProgrammingEvaluationAgent
from google.genai import types


# ---------------------------------------------------------------------------
# Test Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def stores():
    assignment_store = InMemoryAssignmentStore()
    submission_store = InMemorySubmissionStore()
    evaluation_store = InMemoryEvaluationStore()

    # Seed an assignment
    assignment = AssignmentDefinition(
        task_id="sort_algo",
        title="Merge Sort Implementation",
        test_cases=(
            TestCaseDefinition("t1", "Sort empty list", 5),
            TestCaseDefinition("t2", "Sort randomized integers", 5),
        ),
    )
    assignment_store.save(assignment)

    # Seed a submission
    submission = SubmissionRecord(
        metadata=SubmissionMetadata(student_id="student_42", task_id="sort_algo"),
        source_type=SubmissionSource.GITHUB,
        source_reference="https://github.com/student/merge-sort",
        source_code="def merge_sort(arr): return sorted(arr)\n",
        status=SubmissionStatus.EVALUATING,
        submission_id="sub_valid_123",
    )
    submission_store.save(submission)

    # Seed an evaluation report
    report = EvaluationReport(
        status=EvaluationStatus.COMPLETED,
        grading_report=GradingReport(
            earned_points=10,
            max_score=10,
            passed_tests=2,
            total_tests=2,
        ),
        submission_id="sub_valid_123",
        test_results=(
            TestCaseResult("t1", True),
            TestCaseResult("t2", True),
        ),
    )
    evaluation_store.save(report)

    return assignment_store, submission_store, evaluation_store


@pytest.fixture
def sec_context():
    return EvaluationSecurityContext(
        authorized_submission_id="sub_valid_123",
        authorized_task_id="sort_algo",
        authorized_student_id="student_42",
    )


@pytest.fixture
def registry(stores):
    assignment_store, submission_store, evaluation_store = stores
    return create_default_tool_registry(
        assignment_store=assignment_store,
        submission_store=submission_store,
        evaluation_store=evaluation_store,
    )


# ---------------------------------------------------------------------------
# Unit Tests for Individual Tools & Authorization
# ---------------------------------------------------------------------------


class TestIndividualTools:
    def test_get_assignment_details_authorized(self, registry, sec_context):
        audit = ToolAuditLogger()
        res = registry.execute_tool(
            "get_assignment_details",
            {"task_id": "sort_algo"},
            sec_context,
            audit,
        )

        assert "error" not in res
        assert res["task_id"] == "sort_algo"
        assert res["max_score"] == 10
        assert len(res["test_cases"]) == 2

        events = audit.get_events()
        assert len(events) == 1
        assert events[0].status is ToolExecutionStatus.SUCCESS

    def test_get_assignment_details_unauthorized_task_rejected(self, registry, sec_context):
        audit = ToolAuditLogger()
        res = registry.execute_tool(
            "get_assignment_details",
            {"task_id": "other_secret_task"},
            sec_context,
            audit,
        )

        assert "error" in res
        assert "Authorization failed" in res["error"]
        assert audit.get_events()[0].status is ToolExecutionStatus.UNAUTHORIZED

    def test_get_submission_source_authorized(self, registry, sec_context):
        audit = ToolAuditLogger()
        res = registry.execute_tool(
            "get_submission_source",
            {"submission_id": "sub_valid_123"},
            sec_context,
            audit,
        )

        assert "error" not in res
        assert "def merge_sort" in res["source_code"]
        assert res["student_id"] == "student_42"

    def test_get_submission_source_unauthorized_submission_rejected(self, registry, sec_context):
        audit = ToolAuditLogger()
        res = registry.execute_tool(
            "get_submission_source",
            {"submission_id": "sub_other_student"},
            sec_context,
            audit,
        )

        assert "error" in res
        assert "Authorization failed" in res["error"]

    def test_get_test_results_authorized(self, registry, sec_context):
        audit = ToolAuditLogger()
        res = registry.execute_tool(
            "get_test_results",
            {"submission_id": "sub_valid_123"},
            sec_context,
            audit,
        )

        assert "error" not in res
        assert res["total_tests"] == 2
        assert res["passed_count"] == 2
        assert res["failed_count"] == 0

    def test_get_grading_report_authorized(self, registry, sec_context):
        audit = ToolAuditLogger()
        res = registry.execute_tool(
            "get_grading_report",
            {"submission_id": "sub_valid_123"},
            sec_context,
            audit,
        )

        assert "error" not in res
        assert res["earned_points"] == 10
        assert res["percentage"] == 100.0

    def test_generate_student_feedback_authorized(self, registry, sec_context):
        audit = ToolAuditLogger()
        args = {
            "submission_id": "sub_valid_123",
            "summary": "Great implementation using idiomatic Python.",
            "strengths": ["Clean function signature"],
            "observations": [
                {
                    "title": "Use of built-in sort",
                    "category": "code_quality",
                    "severity": "info",
                    "explanation": "You used sorted() instead of manual merge.",
                    "code_evidence": "return sorted(arr)",
                    "suggested_fix": "Implement divide and conquer manually.",
                }
            ],
            "pedagogical_guidance": "Try implementing the recursive merge helper next.",
        }

        res = registry.execute_tool("generate_student_feedback", args, sec_context, audit)
        assert res["status"] == "success"
        assert "Assessment Feedback" in res["formatted_feedback"]
        assert "Use of built-in sort" in res["formatted_feedback"]


# ---------------------------------------------------------------------------
# Argument Validation & Unapproved Tool Defense
# ---------------------------------------------------------------------------


class TestSecurityDefenses:
    def test_unapproved_tool_is_rejected(self, registry, sec_context):
        audit = ToolAuditLogger()
        res = registry.execute_tool(
            "run_bash_command",
            {"command": "rm -rf /"},
            sec_context,
            audit,
        )

        assert "error" in res
        assert "Forbidden" in res["error"]
        assert audit.get_events()[0].status is ToolExecutionStatus.UNAUTHORIZED

    def test_invalid_schema_arguments_rejected(self, registry, sec_context):
        audit = ToolAuditLogger()
        # Invalid arguments: missing required task_id
        res = registry.execute_tool(
            "get_assignment_details",
            {},
            sec_context,
            audit,
        )

        assert "error" in res
        assert "Invalid arguments" in res["error"]
        assert audit.get_events()[0].status is ToolExecutionStatus.INVALID_ARGUMENTS


# ---------------------------------------------------------------------------
# Multi-turn Agent Flow Integration Tests
# ---------------------------------------------------------------------------


class FakeFunctionCall:
    def __init__(self, name: str, args: dict):
        self.name = name
        self.args = args


class FakeCandidatePart:
    def __init__(self, text: str = None, function_call: FakeFunctionCall = None):
        self.text = text
        self.function_call = function_call


class FakeCandidateContent:
    def __init__(self, parts: list):
        self.parts = parts


class FakeCandidate:
    def __init__(self, content: FakeCandidateContent):
        self.content = content


class FakeAgentApiResponse:
    def __init__(self, candidates: list, text: str = ""):
        self.candidates = candidates
        self.text = text


class MockMultiTurnClient:
    def __init__(self, scripted_turns: list):
        self.scripted_turns = list(scripted_turns)
        self.call_history = []

    @property
    def models(self):
        return self

    def generate_content(self, **kwargs):
        self.call_history.append(kwargs)
        if self.scripted_turns:
            return self.scripted_turns.pop(0)
        return FakeAgentApiResponse(candidates=[])


class TestAgentToolWorkflow:
    def test_complete_agent_tool_calling_flow(self, registry, sec_context):
        # Script 2 turns of model tool calling followed by final synthesis
        turn1_response = FakeAgentApiResponse(
            candidates=[
                FakeCandidate(
                    content=FakeCandidateContent(
                        parts=[
                            FakeCandidatePart(
                                function_call=FakeFunctionCall(
                                    name="get_assignment_details",
                                    args={"task_id": "sort_algo"},
                                )
                            ),
                            FakeCandidatePart(
                                function_call=FakeFunctionCall(
                                    name="get_submission_source",
                                    args={"submission_id": "sub_valid_123"},
                                )
                            ),
                        ]
                    )
                )
            ]
        )

        turn2_response = FakeAgentApiResponse(
            candidates=[
                FakeCandidate(
                    content=FakeCandidateContent(
                        parts=[
                            FakeCandidatePart(
                                function_call=FakeFunctionCall(
                                    name="generate_student_feedback",
                                    args={
                                        "submission_id": "sub_valid_123",
                                        "summary": "Completed successfully.",
                                        "strengths": ["Working sort"],
                                        "observations": [],
                                        "pedagogical_guidance": "Well done.",
                                    },
                                )
                            )
                        ]
                    )
                )
            ]
        )

        turn3_final = FakeAgentApiResponse(
            candidates=[
                FakeCandidate(
                    content=FakeCandidateContent(
                        parts=[
                            FakeCandidatePart(
                                text="I have inspected the code, verified the test specs, and generated the student feedback."
                            )
                        ]
                    )
                )
            ],
            text="I have inspected the code, verified the test specs, and generated the student feedback.",
        )

        mock_client = MockMultiTurnClient([turn1_response, turn2_response, turn3_final])

        agent = ProgrammingEvaluationAgent(
            registry=registry,
            client=mock_client,
        )

        result = agent.run_evaluation(sec_context)

        assert result.session_id == sec_context.session_id
        assert result.tool_calls_count == 3
        assert len(result.audit_events) == 3
        assert all(e.status is ToolExecutionStatus.SUCCESS for e in result.audit_events)

        tool_names_called = [e.tool_name for e in result.audit_events]
        assert "get_assignment_details" in tool_names_called
        assert "get_submission_source" in tool_names_called
        assert "generate_student_feedback" in tool_names_called
        assert "inspected the code" in result.output_text

