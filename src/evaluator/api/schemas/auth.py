"""Pydantic schemas for authentication and user account management."""

from datetime import datetime
from pydantic import BaseModel, Field

from evaluator.auth.models import UserRole


class RegisterRequest(BaseModel):
    """User registration payload."""

    user_id: str = Field(..., min_length=1, max_length=50, pattern=r"^[A-Za-z0-9_-]+$")
    email: str = Field(..., pattern=r"^[^@]+@[^@]+\.[^@]+$")
    password: str = Field(..., min_length=6, max_length=128)
    role: UserRole = Field(default=UserRole.STUDENT)
    name: str = Field(..., min_length=1, max_length=100)


class LoginRequest(BaseModel):
    """User login credential payload."""

    email_or_user_id: str = Field(..., min_length=1, max_length=100)
    password: str = Field(..., min_length=1, max_length=128)


class TokenResponse(BaseModel):
    """Successful authentication response containing signed bearer token."""

    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    role: str
    name: str


class ChangePasswordRequest(BaseModel):
    """Password update payload."""

    old_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=6, max_length=128)


class UserProfileResponse(BaseModel):
    """Current user profile."""

    user_id: str
    email: str
    role: str
    name: str
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None = None

    model_config = {"from_attributes": True}
