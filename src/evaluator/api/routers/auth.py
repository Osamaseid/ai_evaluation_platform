"""Authentication and password management endpoints."""

from fastapi import APIRouter, Depends, Header, HTTPException, status

from evaluator.api.dependencies.auth import get_auth_service, get_current_user
from evaluator.api.dependencies.rate_limiter import rate_limit
from evaluator.api.schemas.auth import (
    ChangePasswordRequest,
    LoginRequest,
    RegisterRequest,
    TokenResponse,
    UserProfileResponse,
)
from evaluator.auth.exceptions import AuthenticationError, UserInactiveError
from evaluator.auth.models import UserAccount, UserRole
from evaluator.exceptions import DuplicateEntityError, EntityNotFoundError
from evaluator.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post(
    "/register",
    response_model=UserProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new student or instructor user account",
    dependencies=[Depends(rate_limit(max_requests_per_minute=20))],
)
def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> UserProfileResponse:
    """Register a new user account with secure password hashing."""
    try:
        user = auth_service.register(
            user_id=request.user_id,
            email=request.email,
            password=request.password,
            role=request.role,
            name=request.name,
        )
        return UserProfileResponse(
            user_id=user.user_id,
            email=user.email,
            role=user.role.value,
            name=user.name,
            is_active=user.is_active,
            created_at=user.created_at,
            last_login_at=user.last_login_at,
        )
    except DuplicateEntityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate credentials and obtain signed bearer access token",
    dependencies=[Depends(rate_limit(max_requests_per_minute=30))],
)
def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> TokenResponse:
    """Authenticate with user_id/email and password."""
    try:
        token, user = auth_service.login(
            email_or_user_id=request.email_or_user_id,
            password=request.password,
        )
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    except UserInactiveError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc))
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user_id=user.user_id,
        email=user.email,
        role=user.role.value,
        name=user.name,
    )


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Revoke active bearer token and invalidate session",
)
def logout(
    authorization: str | None = Header(default=None),
    auth_service: AuthService = Depends(get_auth_service),
) -> None:
    """Revoke active bearer token."""
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization[7:].strip()
        auth_service.logout(token)


@router.get(
    "/me",
    response_model=UserProfileResponse,
    summary="Get current authenticated user profile",
)
def get_current_user_profile(
    current_user: UserAccount = Depends(get_current_user),
) -> UserProfileResponse:
    """Return the profile of the current authenticated user."""
    return UserProfileResponse(
        user_id=current_user.user_id,
        email=current_user.email,
        role=current_user.role.value,
        name=current_user.name,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login_at=current_user.last_login_at,
    )


@router.post(
    "/password",
    status_code=status.HTTP_200_OK,
    summary="Change password for current user",
)
def change_password(
    request: ChangePasswordRequest,
    current_user: UserAccount = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    """Update password with verification of current password."""
    try:
        auth_service.change_password(
            user_id=current_user.user_id,
            old_password=request.old_password,
            new_password=request.new_password,
        )
        return {"message": "Password changed successfully."}
    except AuthenticationError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
