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


# ---------------------------------------------------------------------------
# Source Collection & Security Exceptions
# ---------------------------------------------------------------------------


class CollectionError(DomainError):
    """Raised when source code collection or extraction fails."""


class RepositoryNotFoundError(CollectionError):
    """Raised when a GitHub repository is not found or is private/inaccessible."""


class RepositoryAccessError(CollectionError):
    """Raised when GitHub authorization fails or API rate limit is exceeded."""


class SecurityValidationError(DomainError):
    """Base exception for security policy violations in submissions."""


class DangerousFileTypeError(SecurityValidationError):
    """Raised when a submission contains a disallowed or dangerous file type."""


class PathTraversalError(SecurityValidationError):
    """Raised when an archive entry or storage path attempts directory traversal."""


class ZipBombError(SecurityValidationError):
    """Raised when a zip archive shows characteristics of a decompression bomb."""


class FileSizeExceededError(SecurityValidationError):
    """Raised when a file or extracted archive exceeds configured size limits."""
