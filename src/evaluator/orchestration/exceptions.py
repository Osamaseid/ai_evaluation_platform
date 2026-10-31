"""Exceptions specific to evaluation orchestration."""

from evaluator.exceptions import DomainError


class DuplicateProcessingError(DomainError):
    """Raised when an evaluation job is triggered for a submission already in progress."""


class InfrastructureExecutionError(DomainError):
    """Raised when a test runner or container worker fails to execute due to host/environment errors."""
