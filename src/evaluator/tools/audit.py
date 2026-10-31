"""Audit logging and event recording for agent tool execution."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any
import uuid


class ToolExecutionStatus(str, Enum):
    """Outcome status of an agent tool invocation."""

    SUCCESS = "success"
    UNAUTHORIZED = "unauthorized"
    INVALID_ARGUMENTS = "invalid_arguments"
    EXECUTION_FAILED = "execution_failed"


@dataclass(frozen=True)
class ToolExecutionEvent:
    """Immutable audit record of a single tool execution attempt."""

    tool_name: str
    arguments: dict[str, Any]
    status: ToolExecutionStatus
    result: dict[str, Any] | None = None
    error_message: str | None = None
    session_id: str | None = None
    event_id: str = field(default_factory=lambda: f"evt_{uuid.uuid4().hex[:12]}")
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ToolAuditLogger:
    """Thread-safe collector of tool execution audit events."""

    def __init__(self) -> None:
        self._events: list[ToolExecutionEvent] = []

    def record(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        status: ToolExecutionStatus,
        result: dict[str, Any] | None = None,
        error_message: str | None = None,
        session_id: str | None = None,
    ) -> ToolExecutionEvent:
        """Create and store a tool execution audit event."""
        event = ToolExecutionEvent(
            tool_name=tool_name,
            arguments=arguments,
            status=status,
            result=result,
            error_message=error_message,
            session_id=session_id,
        )
        self._events.append(event)
        return event

    def get_events(self) -> list[ToolExecutionEvent]:
        """Return a copy of all recorded audit events."""
        return list(self._events)

