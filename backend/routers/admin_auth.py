"""Admin authentication router and dependency.

PIP Task 3.5 & PRD §7.4:
- POST /login: Issue access + refresh token
- POST /refresh: Rotate/exchange refresh token
- POST /bootstrap: Seed initial super_admin, blocked in production
- require_admin(role): Dependency enforcing authentication and role checks
"""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, HTTPException, status
from pydantic import BaseModel

from models import (
    AdminBootstrapRequest,
    AdminBootstrapResponse,
    AdminLoginRequest,
    AdminLoginResponse,
    AdminRefreshRequest,
    AdminRefreshResponse,
    AdminUser,
)
from models.enums import AdminRole
from routers.deps import StorageDep
from services.admin_auth import (
    AdminAlreadyExistsError,
    AdminAuthenticationError,
    BootstrapBlockedError,
    InsufficientRoleError,
    InvalidAdminTokenError,
    assert_role_permitted,
    bootstrap_super_admin,
    decode_access_token,
    login_admin,
    refresh_admin_token,
)

router = APIRouter(tags=["admin_auth"])


def require_admin(required_role: AdminRole | None = None):
    """FastAPI dependency factory enforcing admin authentication and role permission."""

    async def _verifier(
        storage: StorageDep,
        authorization: Annotated[str | None, Header()] = None,
    ) -> AdminUser:
        if not authorization or not authorization.lower().startswith("bearer "):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Missing admin bearer token",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = authorization[7:].strip()
        try:
            payload = decode_access_token(token)
        except InvalidAdminTokenError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(exc),
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc

        admin_id = payload["sub"]
        admin = await storage.get_admin_user(admin_id)
        if admin is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin user not found or deactivated",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # Dual-layer check: enforced here in the dependency and re-checked in the service layer
        try:
            assert_role_permitted(admin.role, required_role)
        except InsufficientRoleError as exc:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=str(exc),
            ) from exc

        return admin

    return _verifier


# Type aliases for common route protections
CurrentAdmin = Annotated[AdminUser, Depends(require_admin())]
CurrentReviewer = Annotated[AdminUser, Depends(require_admin(AdminRole.reviewer))]
CurrentSuperAdmin = Annotated[AdminUser, Depends(require_admin(AdminRole.super_admin))]


class AdminProfileResponse(BaseModel):
    id: str
    email: str
    role: AdminRole


@router.post("/login", response_model=AdminLoginResponse)
async def login(payload: AdminLoginRequest, storage: StorageDep) -> AdminLoginResponse:
    try:
        admin, access_token, refresh_token = await login_admin(
            storage, payload.email, payload.password
        )
    except AdminAuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        ) from exc

    return AdminLoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        role=admin.role,
        email=admin.email,
    )


@router.post("/refresh", response_model=AdminRefreshResponse)
async def refresh(payload: AdminRefreshRequest, storage: StorageDep) -> AdminRefreshResponse:
    try:
        _, new_access_token = await refresh_admin_token(storage, payload.refresh_token)
    except AdminAuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        ) from exc

    return AdminRefreshResponse(
        access_token=new_access_token,
        token_type="bearer",
    )


@router.post("/bootstrap", response_model=AdminBootstrapResponse)
async def bootstrap(payload: AdminBootstrapRequest, storage: StorageDep) -> AdminBootstrapResponse:
    try:
        admin = await bootstrap_super_admin(storage, payload.email, payload.password)
    except BootstrapBlockedError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        ) from exc
    except AdminAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc

    return AdminBootstrapResponse(
        status="ok",
        admin_id=admin.id,
    )


@router.get("/me", response_model=AdminProfileResponse)
async def me(admin: CurrentAdmin) -> AdminProfileResponse:
    return AdminProfileResponse(
        id=admin.id,
        email=admin.email,
        role=admin.role,
    )
