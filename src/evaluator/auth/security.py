"""Cryptographic utilities for password hashing and JWT-compatible bearer tokens."""

import base64
from datetime import datetime, timezone
import hashlib
import hmac
import json
import os
import secrets
import time
from typing import Any

from evaluator.auth.exceptions import (
    AuthenticationError,
    InvalidTokenError,
    TokenExpiredError,
)
from evaluator.auth.models import TokenPayload, UserRole


def _b64encode(data: bytes) -> str:
    """Encode bytes to URL-safe base64 string without trailing padding."""
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("utf-8")


def _b64decode(data: str) -> bytes:
    """Decode URL-safe base64 string with restored padding."""
    padded = data + "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode(padded.encode("utf-8"))


class PasswordHasher:
    """Secure password hasher using PBKDF2-HMAC-SHA256 with cryptographically random salts."""

    DEFAULT_ITERATIONS = 100_000

    @classmethod
    def hash_password(cls, plain_password: str, iterations: int = DEFAULT_ITERATIONS) -> str:
        """Derive a salted cryptographic hash for a plain password."""
        if not plain_password or not isinstance(plain_password, str):
            raise ValueError("Password cannot be empty.")

        salt = secrets.token_bytes(16)
        key = hashlib.pbkdf2_hmac(
            "sha256",
            plain_password.encode("utf-8"),
            salt,
            iterations,
        )
        return f"pbkdf2:sha256:{iterations}${salt.hex()}${key.hex()}"

    @classmethod
    def verify_password(cls, plain_password: str, hashed: str) -> bool:
        """Verify plain password against stored hash in constant time."""
        if not plain_password or not hashed:
            return False

        try:
            algorithm_part, salt_hex, key_hex = hashed.split("$")
            _, _, iterations_str = algorithm_part.split(":")
            iterations = int(iterations_str)
            salt = bytes.fromhex(salt_hex)
            expected_key = bytes.fromhex(key_hex)

            derived_key = hashlib.pbkdf2_hmac(
                "sha256",
                plain_password.encode("utf-8"),
                salt,
                iterations,
            )
            return hmac.compare_digest(derived_key, expected_key)
        except Exception:
            return False


class TokenManager:
    """Signs and verifies HMAC-SHA256 bearer tokens conforming to standard JWT structure."""

    DEFAULT_TTL_SECONDS = 3600  # 1 hour

    def __init__(self, secret_key: str | None = None, default_ttl_seconds: int = DEFAULT_TTL_SECONDS) -> None:
        self._secret = (
            secret_key
            or os.environ.get("AUTH_SECRET_KEY")
            or "anti-gravity-evaluation-platform-dev-secret-key-32b"
        ).encode("utf-8")
        self._ttl = max(60, default_ttl_seconds)

    def create_access_token(
        self,
        user_id: str,
        email: str,
        role: UserRole,
        ttl_seconds: int | None = None,
    ) -> str:
        """Mint a signed bearer token for a user."""
        now = int(time.time())
        expires = now + (ttl_seconds or self._ttl)
        jti = secrets.token_hex(16)

        header = {"alg": "HS256", "typ": "JWT"}
        payload = {
            "sub": user_id,
            "email": email,
            "role": role.value if isinstance(role, UserRole) else str(role),
            "iat": now,
            "exp": expires,
            "jti": jti,
        }

        header_b64 = _b64encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
        payload_b64 = _b64encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")

        signature = hmac.new(self._secret, signing_input, hashlib.sha256).digest()
        sig_b64 = _b64encode(signature)

        return f"{header_b64}.{payload_b64}.{sig_b64}"

    def decode_and_verify(self, token: str) -> TokenPayload:
        """Verify signature, expiry, and structure of a bearer token."""
        if not token or not isinstance(token, str):
            raise InvalidTokenError("Bearer token cannot be empty.")

        parts = token.strip().split(".")
        if len(parts) != 3:
            raise InvalidTokenError("Malformed bearer token structure.")

        header_b64, payload_b64, sig_b64 = parts
        signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")

        # Verify signature
        try:
            expected_sig = hmac.new(self._secret, signing_input, hashlib.sha256).digest()
            actual_sig = _b64decode(sig_b64)
            if not hmac.compare_digest(expected_sig, actual_sig):
                raise InvalidTokenError("Token cryptographic signature verification failed.")
        except Exception as exc:
            raise InvalidTokenError(f"Token signature verification failed: {exc}") from exc

        # Decode payload
        try:
            raw_payload = json.loads(_b64decode(payload_b64).decode("utf-8"))
        except Exception as exc:
            raise InvalidTokenError(f"Failed to parse token payload: {exc}") from exc

        # Verify expiration
        exp = raw_payload.get("exp", 0)
        now = int(time.time())
        if now >= exp:
            raise TokenExpiredError(f"Bearer token expired at {datetime.fromtimestamp(exp, tz=timezone.utc)}.")

        try:
            return TokenPayload(
                sub=raw_payload["sub"],
                email=raw_payload["email"],
                role=UserRole(raw_payload["role"]),
                exp=exp,
                iat=raw_payload.get("iat", now),
                jti=raw_payload.get("jti", ""),
            )
        except (KeyError, ValueError) as exc:
            raise InvalidTokenError(f"Invalid claims in token payload: {exc}") from exc

