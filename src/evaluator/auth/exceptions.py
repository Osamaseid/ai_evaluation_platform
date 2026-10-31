"""Authentication and authorization domain exceptions."""

from evaluator.exceptions import DomainError


class AuthenticationError(DomainError):
    """Raised when user credentials or token verification fails."""


class AuthorizationError(DomainError):
    """Raised when an authenticated user attempts an action outside their role permissions."""


class InvalidTokenError(AuthenticationError):
    """Raised when a bearer token is structurally invalid or signature check fails."""


class TokenExpiredError(AuthenticationError):
    """Raised when an authentication token has passed its expiration time."""


class UserInactiveError(AuthenticationError):
    """Raised when attempting to authenticate an inactive or suspended account."""

