"""Centralized HTTP exception handling and consistent error responses."""

import logging
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse

from evaluator.auth.exceptions import (
    AuthenticationError,
    AuthorizationError,
    InvalidTokenError,
    TokenExpiredError,
    UserInactiveError,
)
from evaluator.exceptions import (
    DangerousFileTypeError,
    DeadlineExceededError,
    DomainError,
    DuplicateEntityError,
    EntityNotFoundError,
    FileSizeExceededError,
    InvalidStateTransitionError,
    PathTraversalError,
    RepositoryAccessError,
    RepositoryNotFoundError,
    SecurityValidationError,
    ZipBombError,
)
from evaluator.orchestration.exceptions import DuplicateProcessingError

logger = logging.getLogger(__name__)


def _error_response(status_code: int, code: str, message: str) -> JSONResponse:
    """Format consistent error response payload."""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "status_code": status_code,
            }
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register custom domain exception handlers on the FastAPI application."""

    @app.exception_handler(EntityNotFoundError)
    def handle_not_found(request: Request, exc: EntityNotFoundError):
        return _error_response(status.HTTP_404_NOT_FOUND, "NOT_FOUND", str(exc))

    @app.exception_handler(RepositoryNotFoundError)
    def handle_repo_not_found(request: Request, exc: RepositoryNotFoundError):
        return _error_response(status.HTTP_404_NOT_FOUND, "REPOSITORY_NOT_FOUND", str(exc))

    @app.exception_handler(DuplicateEntityError)
    def handle_duplicate(request: Request, exc: DuplicateEntityError):
        return _error_response(status.HTTP_409_CONFLICT, "ALREADY_EXISTS", str(exc))

    @app.exception_handler(DuplicateProcessingError)
    def handle_duplicate_eval(request: Request, exc: DuplicateProcessingError):
        return _error_response(status.HTTP_409_CONFLICT, "DUPLICATE_PROCESSING", str(exc))

    @app.exception_handler(InvalidStateTransitionError)
    def handle_invalid_transition(request: Request, exc: InvalidStateTransitionError):
        return _error_response(status.HTTP_409_CONFLICT, "INVALID_STATE_TRANSITION", str(exc))

    @app.exception_handler(AuthenticationError)
    def handle_auth_error(request: Request, exc: AuthenticationError):
        return _error_response(status.HTTP_401_UNAUTHORIZED, "AUTHENTICATION_FAILED", str(exc))

    @app.exception_handler(TokenExpiredError)
    def handle_token_expired(request: Request, exc: TokenExpiredError):
        return _error_response(status.HTTP_401_UNAUTHORIZED, "TOKEN_EXPIRED", str(exc))

    @app.exception_handler(AuthorizationError)
    def handle_forbidden(request: Request, exc: AuthorizationError):
        return _error_response(status.HTTP_403_FORBIDDEN, "FORBIDDEN", str(exc))

    @app.exception_handler(RepositoryAccessError)
    def handle_repo_forbidden(request: Request, exc: RepositoryAccessError):
        return _error_response(status.HTTP_403_FORBIDDEN, "REPOSITORY_ACCESS_DENIED", str(exc))

    @app.exception_handler(UserInactiveError)
    def handle_user_inactive(request: Request, exc: UserInactiveError):
        return _error_response(status.HTTP_403_FORBIDDEN, "USER_INACTIVE", str(exc))

    @app.exception_handler(FileSizeExceededError)
    def handle_payload_too_large(request: Request, exc: FileSizeExceededError):
        return _error_response(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "FILE_TOO_LARGE", str(exc))

    @app.exception_handler(DeadlineExceededError)
    def handle_deadline(request: Request, exc: DeadlineExceededError):
        return _error_response(status.HTTP_422_UNPROCESSABLE_ENTITY, "DEADLINE_EXCEEDED", str(exc))

    @app.exception_handler(SecurityValidationError)
    def handle_security_violation(request: Request, exc: SecurityValidationError):
        return _error_response(status.HTTP_400_BAD_REQUEST, "SECURITY_VIOLATION", str(exc))

    @app.exception_handler(DangerousFileTypeError)
    def handle_dangerous_file(request: Request, exc: DangerousFileTypeError):
        return _error_response(status.HTTP_400_BAD_REQUEST, "DANGEROUS_FILE_TYPE", str(exc))

    @app.exception_handler(ZipBombError)
    def handle_zip_bomb(request: Request, exc: ZipBombError):
        return _error_response(status.HTTP_400_BAD_REQUEST, "ZIP_BOMB_DETECTED", str(exc))

    @app.exception_handler(PathTraversalError)
    def handle_path_traversal(request: Request, exc: PathTraversalError):
        return _error_response(status.HTTP_400_BAD_REQUEST, "PATH_TRAVERSAL_DETECTED", str(exc))

