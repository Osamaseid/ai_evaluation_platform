"""Tool registry and application-controlled execution engine."""

from dataclasses import dataclass
import logging
from typing import Any, Callable

from google.genai import types
from pydantic import BaseModel, ValidationError

from evaluator.stores.assignment_store import AssignmentStore
from evaluator.stores.evaluation_store import EvaluationStore
from evaluator.stores.submission_store import SubmissionStore
from evaluator.tools.audit import ToolAuditLogger, ToolExecutionStatus
from evaluator.tools.context import EvaluationSecurityContext
from evaluator.tools.handlers import (
    ToolAuthorizationError,
    handle_generate_student_feedback,
    handle_get_assignment_details,
    handle_get_grading_report,
    handle_get_submission_source,
    handle_get_test_results,
)
from evaluator.tools.schemas import (
    AssignmentDetailsOutput,
    GenerateStudentFeedbackInput,
    GetAssignmentDetailsInput,
    GetGradingReportInput,
    GetSubmissionSourceInput,
    GetTestResultsInput,
    GradingReportOutput,
    StudentFeedbackOutput,
    SubmissionSourceOutput,
    TestResultsOutput,
)

logger = logging.getLogger(__name__)

_ALLOWED_SCHEMA_FIELDS = set(types.Schema.model_fields.keys())


def _clean_schema_dict(data: Any) -> Any:
    """Recursively filter JSON schema dictionaries to ensure strict compatibility with types.Schema."""
    if isinstance(data, dict):
        cleaned: dict[str, Any] = {}
        for k, v in data.items():
            if k == "examples" and isinstance(v, list) and v:
                cleaned["example"] = str(v[0])
            elif k in _ALLOWED_SCHEMA_FIELDS:
                cleaned[k] = _clean_schema_dict(v)
        return cleaned
    elif isinstance(data, list):
        return [_clean_schema_dict(item) for item in data]
    return data


@dataclass(frozen=True)
class ToolDefinition:
    """Specification of an approved tool."""

    name: str
    description: str
    input_schema: type[BaseModel]
    output_schema: type[BaseModel]
    handler: Callable[..., Any]

    def to_genai_declaration(self) -> types.FunctionDeclaration:
        """Convert tool schema into official Google GenAI FunctionDeclaration."""
        schema_dict = self.input_schema.model_json_schema()
        raw_props = schema_dict.get("properties", {})
        required = schema_dict.get("required", [])

        gemini_parameters: dict[str, Any] = {
            "type": "OBJECT",
            "properties": _clean_schema_dict(raw_props),
            "required": required,
        }

        return types.FunctionDeclaration(
            name=self.name,
            description=self.description,
            parameters=gemini_parameters,
        )


class ToolRegistry:
    """Manages approved tools, validates arguments, and executes authorized calls."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, tool_def: ToolDefinition) -> None:
        """Register an application-approved tool."""
        if tool_def.name in self._tools:
            raise ValueError(f"Tool '{tool_def.name}' is already registered.")
        self._tools[tool_def.name] = tool_def

    def get_tool(self, name: str) -> ToolDefinition | None:
        return self._tools.get(name)

    def get_declarations(self) -> list[types.FunctionDeclaration]:
        """Generate list of FunctionDeclarations for the Gemini API."""
        return [tool.to_genai_declaration() for tool in self._tools.values()]

    def execute_tool(
        self,
        tool_name: str,
        raw_args: dict[str, Any],
        context: EvaluationSecurityContext,
        audit_logger: ToolAuditLogger | None = None,
    ) -> dict[str, Any]:
        """Validate input arguments, check permissions, and execute the tool handler."""
        # 1. Permission check: tool must be in approved registry
        tool_def = self.get_tool(tool_name)
        if not tool_def:
            err_msg = f"Forbidden: Tool '{tool_name}' is not an approved application tool."
            logger.warning(err_msg)
            if audit_logger:
                audit_logger.record(
                    tool_name=tool_name,
                    arguments=raw_args,
                    status=ToolExecutionStatus.UNAUTHORIZED,
                    error_message=err_msg,
                    session_id=context.session_id,
                )
            return {"error": err_msg}

        # 2. Schema validation
        try:
            validated_input = tool_def.input_schema.model_validate(raw_args)
        except ValidationError as val_err:
            err_msg = f"Invalid arguments for tool '{tool_name}': {val_err.errors()}"
            logger.warning(err_msg)
            if audit_logger:
                audit_logger.record(
                    tool_name=tool_name,
                    arguments=raw_args,
                    status=ToolExecutionStatus.INVALID_ARGUMENTS,
                    error_message=err_msg,
                    session_id=context.session_id,
                )
            return {"error": err_msg}

        # 3. Execution with authorization handling
        try:
            result_obj = tool_def.handler(validated_input, context)
            if isinstance(result_obj, BaseModel):
                result_dict = result_obj.model_dump()
            elif isinstance(result_obj, dict):
                result_dict = result_obj
            else:
                result_dict = {"result": result_obj}

            if audit_logger:
                audit_logger.record(
                    tool_name=tool_name,
                    arguments=raw_args,
                    status=ToolExecutionStatus.SUCCESS,
                    result=result_dict,
                    session_id=context.session_id,
                )
            return result_dict

        except ToolAuthorizationError as auth_err:
            err_msg = f"Authorization failed: {auth_err}"
            logger.warning(err_msg)
            if audit_logger:
                audit_logger.record(
                    tool_name=tool_name,
                    arguments=raw_args,
                    status=ToolExecutionStatus.UNAUTHORIZED,
                    error_message=err_msg,
                    session_id=context.session_id,
                )
            return {"error": err_msg}

        except Exception as exc:
            err_msg = f"Execution error in tool '{tool_name}': {type(exc).__name__}: {exc}"
            logger.error(err_msg, exc_info=True)
            if audit_logger:
                audit_logger.record(
                    tool_name=tool_name,
                    arguments=raw_args,
                    status=ToolExecutionStatus.EXECUTION_FAILED,
                    error_message=err_msg,
                    session_id=context.session_id,
                )
            return {"error": err_msg}


def create_default_tool_registry(
    assignment_store: AssignmentStore,
    submission_store: SubmissionStore,
    evaluation_store: EvaluationStore,
) -> ToolRegistry:
    """Instantiate and populate registry with the 5 application-approved tools."""
    registry = ToolRegistry()

    # Tool 1: get_assignment_details
    registry.register(
        ToolDefinition(
            name="get_assignment_details",
            description="Retrieve assignment title, requirements, test case specifications, and point values.",
            input_schema=GetAssignmentDetailsInput,
            output_schema=AssignmentDetailsOutput,
            handler=lambda inp, ctx: handle_get_assignment_details(inp, ctx, assignment_store),
        )
    )

    # Tool 2: get_submission_source
    registry.register(
        ToolDefinition(
            name="get_submission_source",
            description="Retrieve the student's submitted Python source code for inspection.",
            input_schema=GetSubmissionSourceInput,
            output_schema=SubmissionSourceOutput,
            handler=lambda inp, ctx: handle_get_submission_source(inp, ctx, submission_store),
        )
    )

    # Tool 3: get_test_results
    registry.register(
        ToolDefinition(
            name="get_test_results",
            description="Retrieve verified automated test execution results (pass/fail status and messages).",
            input_schema=GetTestResultsInput,
            output_schema=TestResultsOutput,
            handler=lambda inp, ctx: handle_get_test_results(inp, ctx, evaluation_store),
        )
    )

    # Tool 4: get_grading_report
    registry.register(
        ToolDefinition(
            name="get_grading_report",
            description="Retrieve the deterministic score breakdown (earned points, total score, percentage).",
            input_schema=GetGradingReportInput,
            output_schema=GradingReportOutput,
            handler=lambda inp, ctx: handle_get_grading_report(inp, ctx, evaluation_store),
        )
    )

    # Tool 5: generate_student_feedback
    registry.register(
        ToolDefinition(
            name="generate_student_feedback",
            description="Generate and finalize structured student-facing pedagogical feedback.",
            input_schema=GenerateStudentFeedbackInput,
            output_schema=StudentFeedbackOutput,
            handler=lambda inp, ctx: handle_generate_student_feedback(inp, ctx),
        )
    )

    return registry
