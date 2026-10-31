"""API dependencies package."""

from evaluator.api.dependencies.auth import (
    get_auth_service,
    get_current_user,
    require_admin,
    require_any_authenticated,
    require_instructor,
    require_role,
    require_student,
)
from evaluator.api.dependencies.pagination import PaginationParams, get_pagination
from evaluator.api.dependencies.rate_limiter import rate_limit

__all__ = [
    "get_auth_service",
    "get_current_user",
    "require_role",
    "require_student",
    "require_instructor",
    "require_admin",
    "require_any_authenticated",
    "PaginationParams",
    "get_pagination",
    "rate_limit",
]

