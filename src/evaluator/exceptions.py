"""Domain exceptions for the programming evaluation platform."""


class DomainError(Exception):
    """Base exception for all domain logic failures."""


class EntityNotFoundError(DomainError):
    """Raised when a requested entity does not exist."""


class DuplicateEntityError(DomainError):
    """Raised when an entity with the given identity already exists."""


class EntityValidationError(DomainError):
    """Raised when domain entity validation invariants fail."""


class InvalidStateTransitionError(DomainError):
    """Raised when a submission attempts an illegal status transition."""


class DeadlineExceededError(DomainError):
    """Raised when a submission is received after the assignment deadline."""

