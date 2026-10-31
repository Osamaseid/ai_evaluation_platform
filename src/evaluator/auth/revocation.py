"""Token revocation store for session invalidation on logout."""

from typing import Protocol


class TokenRevocationStore(Protocol):
    """Protocol for managing revoked tokens."""

    def revoke(self, jti: str) -> None:
        """Mark a token ID as revoked."""
        ...

    def is_revoked(self, jti: str) -> bool:
        """Check if a token ID has been revoked."""
        ...


class InMemoryTokenRevocationStore:
    """Thread-safe in-memory store of revoked token identifiers."""

    def __init__(self) -> None:
        self._revoked_tokens: set[str] = set()

    def revoke(self, jti: str) -> None:
        if jti:
            self._revoked_tokens.add(jti)

    def is_revoked(self, jti: str) -> bool:
        return jti in self._revoked_tokens

