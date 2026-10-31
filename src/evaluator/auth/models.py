"""Domain models and value objects for authentication and role-based access control."""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum


class UserRole(str, Enum):
    """User authorization roles."""

    STUDENT = "student"
    INSTRUCTOR = "instructor"
    ADMIN = "admin"


@dataclass(frozen=True)
class UserAccount:
    """Represents an authenticated user account."""

    user_id: str
    email: str
    hashed_password: str
    role: UserRole
    name: str
    is_active: bool = True
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    last_login_at: datetime | None = None

    def with_password(self, new_hashed_password: str) -> "UserAccount":
        """Return a copy with an updated password hash."""
        return UserAccount(
            user_id=self.user_id,
            email=self.email,
            hashed_password=new_hashed_password,
            role=self.role,
            name=self.name,
            is_active=self.is_active,
            created_at=self.created_at,
            last_login_at=self.last_login_at,
        )

    def with_last_login(self, timestamp: datetime) -> "UserAccount":
        """Return a copy with an updated last login timestamp."""
        return UserAccount(
            user_id=self.user_id,
            email=self.email,
            hashed_password=self.hashed_password,
            role=self.role,
            name=self.name,
            is_active=self.is_active,
            created_at=self.created_at,
            last_login_at=timestamp,
        )


@dataclass(frozen=True)
class TokenPayload:
    """Decoded claims payload from an authentication token."""

    sub: str  # user_id
    email: str
    role: UserRole
    exp: int  # UNIX timestamp
    iat: int  # UNIX timestamp
    jti: str  # Unique token identifier

