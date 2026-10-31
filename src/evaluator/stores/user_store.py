"""Storage interface and in-memory implementation for user accounts."""

from typing import Protocol

from evaluator.auth.models import UserAccount
from evaluator.exceptions import DuplicateEntityError, EntityNotFoundError


class UserStore(Protocol):
    """Storage contract for user account persistence."""

    def save(self, user: UserAccount) -> None:
        """Persist a new user account. Raises DuplicateEntityError if user_id or email exists."""
        ...

    def update(self, user: UserAccount) -> None:
        """Update an existing user account. Raises EntityNotFoundError if missing."""
        ...

    def get(self, user_id: str) -> UserAccount | None:
        """Retrieve a user account by unique user ID."""
        ...

    def get_by_email(self, email: str) -> UserAccount | None:
        """Retrieve a user account by email address."""
        ...

    def list_all() -> list[UserAccount]:
        """Return all stored user accounts."""
        ...

    def delete(self, user_id: str) -> None:
        """Remove a user account."""
        ...


class InMemoryUserStore:
    """Thread-safe in-memory repository for user accounts."""

    def __init__(self) -> None:
        self._users_by_id: dict[str, UserAccount] = {}
        self._users_by_email: dict[str, str] = {}  # email -> user_id

    def save(self, user: UserAccount) -> None:
        if user.user_id in self._users_by_id:
            raise DuplicateEntityError(f"User with ID '{user.user_id}' already exists.")

        email_norm = user.email.strip().lower()
        if email_norm in self._users_by_email:
            raise DuplicateEntityError(f"User with email '{user.email}' already exists.")

        self._users_by_id[user.user_id] = user
        self._users_by_email[email_norm] = user.user_id

    def update(self, user: UserAccount) -> None:
        if user.user_id not in self._users_by_id:
            raise EntityNotFoundError(f"User with ID '{user.user_id}' not found.")

        old_user = self._users_by_id[user.user_id]
        old_email_norm = old_user.email.strip().lower()
        new_email_norm = user.email.strip().lower()

        if old_email_norm != new_email_norm and new_email_norm in self._users_by_email:
            raise DuplicateEntityError(f"User with email '{user.email}' already exists.")

        if old_email_norm != new_email_norm:
            del self._users_by_email[old_email_norm]

        self._users_by_id[user.user_id] = user
        self._users_by_email[new_email_norm] = user.user_id

    def get(self, user_id: str) -> UserAccount | None:
        return self._users_by_id.get(user_id)

    def get_by_email(self, email: str) -> UserAccount | None:
        email_norm = email.strip().lower()
        user_id = self._users_by_email.get(email_norm)
        if user_id:
            return self._users_by_id.get(user_id)
        return None

    def list_all(self) -> list[UserAccount]:
        return list(self._users_by_id.values())

    def delete(self, user_id: str) -> None:
        user = self._users_by_id.pop(user_id, None)
        if user:
            self._users_by_email.pop(user.email.strip().lower(), None)

