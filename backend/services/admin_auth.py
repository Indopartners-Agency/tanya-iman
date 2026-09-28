"""Admin authentication and authorization service.

PIP Task 3.5 & PRD §7.4:
- bcrypt password hashing
- JWT access tokens (1 hour expiration)
- 30-day refresh tokens stored as SHA-256 hashes
- Dual-layer role-based access control (route dependency + service layer re-assertion)
- Initial bootstrap blocked in production
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

from config import Env, get_settings
from models import AdminUser
from models.enums import AdminRole
from storage import Storage

ACCESS_TOKEN_EXPIRE_MINUTES = 60
JWT_ALGORITHM = "HS256"


class AdminAuthError(Exception):
    """Base admin authentication exception."""


class InvalidAdminTokenError(AdminAuthError):
    """Token is invalid, malformed, or expired."""


class InsufficientRoleError(AdminAuthError):
    """Authenticated admin role lacks required permissions."""


class AdminAuthenticationError(AdminAuthError):
    """Invalid credentials or missing account."""


class BootstrapBlockedError(AdminAuthError):
    """Bootstrap endpoint called in forbidden environment."""


class AdminAlreadyExistsError(AdminAuthError):
    """Admin with given email already exists."""


def hash_password(password: str) -> str:
    """Hash password using bcrypt with random salt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify plaintext password against bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except Exception:
        return False


def hash_refresh_token(token: str) -> str:
    """Deterministic SHA-256 hash for secure refresh token storage."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def create_access_token(admin: AdminUser) -> str:
    """Create a signed JWT access token valid for 1 hour."""
    settings = get_settings()
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": admin.id,
        "email": admin.email,
        "role": admin.role.value,
        "type": "access",
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, settings.admin_jwt_secret, algorithm=JWT_ALGORITHM)


def create_refresh_token() -> tuple[str, str]:
    """Create a high-entropy 30-day refresh token. Returns (raw_token, hashed_token)."""
    raw_token = secrets.token_urlsafe(48)
    return raw_token, hash_refresh_token(raw_token)


def decode_access_token(token: str) -> dict[str, Any]:
    """Validate signature and expiration of access token."""
    settings = get_settings()
    try:
        payload = jwt.decode(token, settings.admin_jwt_secret, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError as exc:
        raise InvalidAdminTokenError(f"Invalid or expired token: {exc}") from exc

    if payload.get("type") != "access":
        raise InvalidAdminTokenError("Invalid token type")
    if not payload.get("sub"):
        raise InvalidAdminTokenError("Missing token subject")

    return payload


def assert_role_permitted(role: AdminRole, required_role: AdminRole | None) -> None:
    """Re-checked in the service layer per PRD §7.4 and PIP Task 3.5.

    super_admin satisfies all role requirements.
    """
    if required_role is None:
        return
    if role == AdminRole.super_admin:
        return
    if role != required_role:
        raise InsufficientRoleError(
            f"Admin role '{role}' is not authorized. Required: '{required_role}'"
        )


async def login_admin(storage: Storage, email: str, password: str) -> tuple[AdminUser, str, str]:
    """Authenticate admin with email & password.
    Returns (admin, access_token, raw_refresh_token).
    """
    clean_email = email.strip().lower()
    admin = await storage.get_admin_user_by_email(clean_email)
    if admin is None or not verify_password(password, admin.password_hash):
        raise AdminAuthenticationError("Invalid email or password")

    access_token = create_access_token(admin)
    raw_refresh, hashed_refresh = create_refresh_token()

    # Update session metrics
    now = datetime.now(UTC)
    admin.last_login_at = now
    admin.refresh_token_hash = hashed_refresh
    await storage.save_admin_user(admin)

    return admin, access_token, raw_refresh


async def refresh_admin_token(storage: Storage, refresh_token: str) -> tuple[AdminUser, str]:
    """Exchange a valid refresh token for a fresh access token."""
    hashed_token = hash_refresh_token(refresh_token.strip())
    admin = await storage.get_admin_user_by_refresh_token_hash(hashed_token)
    if admin is None:
        raise AdminAuthenticationError("Invalid or expired refresh token")

    new_access_token = create_access_token(admin)
    return admin, new_access_token


async def bootstrap_super_admin(storage: Storage, email: str, password: str) -> AdminUser:
    """Provision the initial super_admin account.

    Forbidden in ENV=production.
    """
    settings = get_settings()
    if settings.env == Env.production:
        raise BootstrapBlockedError("Bootstrap is forbidden in production environment")

    clean_email = email.strip().lower()
    existing = await storage.get_admin_user_by_email(clean_email)
    if existing is not None:
        raise AdminAlreadyExistsError(f"Admin with email '{clean_email}' already exists")

    now = datetime.now(UTC)
    admin = AdminUser(
        id=f"adm_{uuid.uuid4().hex[:16]}",
        email=clean_email,
        password_hash=hash_password(password),
        role=AdminRole.super_admin,
        created_at=now,
    )
    await storage.save_admin_user(admin)
    return admin
