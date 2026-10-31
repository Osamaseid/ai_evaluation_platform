"""Authentication service coordinating registration, credentials, tokens, and password lifecycle."""

from datetime import datetime, timezone
import logging

from evaluator.auth.exceptions import (
    AuthenticationError,
    InvalidTokenError,
    UserInactiveError,
)
from evaluator.auth.models import TokenPayload, UserAccount, UserRole
from evaluator.auth.revocation import (
    InMemoryTokenRevocationStore,
    TokenRevocationStore,
)
from evaluator.auth.security import PasswordHasher, TokenManager
from evaluator.exceptions import DuplicateEntityError, EntityNotFoundError
from evaluator.stores.instructor_store import InstructorStore
from evaluator.stores.student_store import StudentStore
from evaluator.stores.user_store import InMemoryUserStore, UserStore
from evaluator.users import Instructor, Student

logger = logging.getLogger(__name__)


class AuthService:
    """Service layer for authentication, session lifecycle, and credential security."""

    def __init__(
        self,
        user_store: UserStore,
        student_store: StudentStore | None = None,
        instructor_store: InstructorStore | None = None,
        token_manager: TokenManager | None = None,
        revocation_store: TokenRevocationStore | None = None,
    ) -> None:
        self._user_store = user_store
        self._student_store = student_store
        self._instructor_store = instructor_store
        self._token_manager = token_manager or TokenManager()
        self._revocation_store = revocation_store or InMemoryTokenRevocationStore()

    def register(
        self,
        user_id: str,
        email: str,
        password: str,
        role: UserRole,
        name: str,
    ) -> UserAccount:
        """Register a new user account with salted password hashing and role assignment."""
        clean_user_id = user_id.strip()
        clean_email = email.strip().lower()
        clean_name = name.strip()

        if len(password) < 6:
            raise ValueError("Password must be at least 6 characters.")

        # Check existing user
        if self._user_store.get(clean_user_id):
            raise DuplicateEntityError(f"User ID '{clean_user_id}' is already registered.")
        if self._user_store.get_by_email(clean_email):
            raise DuplicateEntityError(f"Email '{clean_email}' is already registered.")

        hashed_password = PasswordHasher.hash_password(password)

        account = UserAccount(
            user_id=clean_user_id,
            email=clean_email,
            hashed_password=hashed_password,
            role=role,
            name=clean_name,
        )
        self._user_store.save(account)

        # Synchronize corresponding student/instructor domain profiles
        if role is UserRole.STUDENT and self._student_store is not None:
            if not self._student_store.get(clean_user_id):
                self._student_store.save(Student(clean_user_id, clean_name, clean_email))
        elif role is UserRole.INSTRUCTOR and self._instructor_store is not None:
            if not self._instructor_store.get(clean_user_id):
                self._instructor_store.save(Instructor(clean_user_id, clean_name, clean_email))

        logger.info("Registered user '%s' (%s, role=%s)", clean_user_id, clean_email, role.value)
        return account

    def login(self, email_or_user_id: str, password: str) -> tuple[str, UserAccount]:
        """Authenticate user credentials and issue a signed bearer token."""
        identifier = email_or_user_id.strip()

        user = self._user_store.get(identifier) or self._user_store.get_by_email(identifier.lower())
        if not user:
            raise AuthenticationError("Invalid email or password.")

        if not user.is_active:
            raise UserInactiveError(f"User account '{user.user_id}' is deactivated.")

        if not PasswordHasher.verify_password(password, user.hashed_password):
            raise AuthenticationError("Invalid email or password.")

        # Update last login timestamp
        now = datetime.now(timezone.utc)
        user = user.with_last_login(now)
        self._user_store.update(user)

        token = self._token_manager.create_access_token(
            user_id=user.user_id,
            email=user.email,
            role=user.role,
        )
        logger.info("User '%s' logged in successfully.", user.user_id)
        return token, user

    def logout(self, token: str) -> None:
        """Revoke a bearer token to immediately invalidate the active session."""
        try:
            payload = self._token_manager.decode_and_verify(token)
            if payload.jti:
                self._revocation_store.revoke(payload.jti)
                logger.info("Revoked session token jti='%s' for user '%s'", payload.jti, payload.sub)
        except Exception as exc:
            # Token might be expired or malformed, but attempt best-effort revocation
            logger.debug("Logout token revocation notice: %s", exc)

    def get_current_user(self, token: str) -> UserAccount:
        """Validate bearer token and retrieve the associated active UserAccount."""
        payload = self._token_manager.decode_and_verify(token)

        if payload.jti and self._revocation_store.is_revoked(payload.jti):
            raise InvalidTokenError("Authentication token has been revoked.")

        user = self._user_store.get(payload.sub)
        if not user:
            raise AuthenticationError(f"User '{payload.sub}' does not exist.")

        if not user.is_active:
            raise UserInactiveError(f"User '{user.user_id}' is deactivated.")

        return user

    def change_password(
        self,
        user_id: str,
        old_password: str,
        new_password: str,
    ) -> None:
        """Change user password after verifying the existing password."""
        user = self._user_store.get(user_id)
        if not user:
            raise EntityNotFoundError(f"User '{user_id}' not found.")

        if not PasswordHasher.verify_password(old_password, user.hashed_password):
            raise AuthenticationError("Current password does not match.")

        if len(new_password) < 6:
            raise ValueError("New password must be at least 6 characters.")

        new_hash = PasswordHasher.hash_password(new_password)
        updated_user = user.with_password(new_hash)
        self._user_store.update(updated_user)
        logger.info("Password updated successfully for user '%s'.", user_id)

