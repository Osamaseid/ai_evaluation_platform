"""FastAPI authentication and role-based access control dependencies."""

from collections.abc import Callable
from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from evaluator.auth.exceptions import (
    AuthenticationError,
    AuthorizationError,
    InvalidTokenError,
    TokenExpiredError,
    UserInactiveError,
)
from evaluator.auth.models import UserAccount, UserRole
from evaluator.services.auth_service import AuthService
from evaluator.stores.instructor_store import InMemoryInstructorStore
from evaluator.stores.student_store import InMemoryStudentStore
from evaluator.stores.user_store import InMemoryUserStore

_security = HTTPBearer(auto_error=False)

# Shared singleton dependencies for application lifecycle
_user_store = InMemoryUserStore()
_student_store = InMemoryStudentStore()
_instructor_store = InMemoryInstructorStore()
_auth_service = AuthService(
    user_store=_user_store,
    student_store=_student_store,
    instructor_store=_instructor_store,
)


def get_user_store():
    return _user_store


def get_auth_service() -> AuthService:
    """Provide authentication service instance."""
    return _auth_service


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Security(_security),
    auth_service: AuthService = Depends(get_auth_service),
) -> UserAccount:
    """Validate bearer token from Authorization header and return authenticated UserAccount."""
    if not credentials or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    try:
        return auth_service.get_current_user(token)
    except TokenExpiredError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token expired: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except (InvalidTokenError, AuthenticationError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid authentication token: {exc}",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except UserInactiveError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )


def require_role(*allowed_roles: UserRole) -> Callable[[UserAccount], UserAccount]:
    """Dependency factory checking that current user belongs to an approved role."""

    def role_checker(current_user: UserAccount = Depends(get_current_user)) -> UserAccount:
        if current_user.role is UserRole.ADMIN:
            return current_user

        if current_user.role not in allowed_roles:
            role_names = [r.value for r in allowed_roles]
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Access forbidden: role '{current_user.role.value}' is not authorized. Allowed roles: {role_names}.",
            )
        return current_user

    return role_checker


# Role shortcut dependencies
require_student = require_role(UserRole.STUDENT)
require_instructor = require_role(UserRole.INSTRUCTOR)
require_admin = require_role(UserRole.ADMIN)
require_any_authenticated = get_current_user

