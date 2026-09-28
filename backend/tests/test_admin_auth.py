from __future__ import annotations

from datetime import UTC, datetime

import pytest
from httpx import AsyncClient

from config import Env, get_settings
from models import AdminUser
from models.enums import AdminRole
from services.admin_auth import (
    InsufficientRoleError,
    assert_role_permitted,
    create_access_token,
    hash_password,
)
from storage.memory import MemoryStorage

pytestmark = pytest.mark.asyncio


async def test_admin_bootstrap_and_login(client: AsyncClient, storage: MemoryStorage):
    # 1. Bootstrap initial super_admin
    boot_resp = await client.post(
        "/api/admin/auth/bootstrap",
        json={"email": "Admin@TanyaIman.ID", "password": "SuperSecretPassword123!"},
    )
    assert boot_resp.status_code == 200
    boot_data = boot_resp.json()
    assert boot_data["status"] == "ok"
    assert "adm_" in boot_data["admin_id"]

    # 2. Duplicate bootstrap fails with 409
    dup_resp = await client.post(
        "/api/admin/auth/bootstrap",
        json={"email": "admin@tanyaiman.id", "password": "otherpassword"},
    )
    assert dup_resp.status_code == 409

    # 3. Successful login (case-insensitive email)
    login_resp = await client.post(
        "/api/admin/auth/login",
        json={"email": "ADMIN@tanyaiman.id", "password": "SuperSecretPassword123!"},
    )
    assert login_resp.status_code == 200
    login_data = login_resp.json()
    assert "access_token" in login_data
    assert "refresh_token" in login_data
    assert login_data["role"] == "super_admin"
    assert login_data["email"] == "admin@tanyaiman.id"
    # Ensure password_hash is never returned in response
    assert "password_hash" not in login_data
    assert "password" not in login_data

    # 4. Wrong password returns 401
    bad_pw_resp = await client.post(
        "/api/admin/auth/login",
        json={"email": "admin@tanyaiman.id", "password": "WrongPassword!"},
    )
    assert bad_pw_resp.status_code == 401

    # 5. Non-existent email returns 401
    bad_email_resp = await client.post(
        "/api/admin/auth/login",
        json={"email": "nobody@tanyaiman.id", "password": "SuperSecretPassword123!"},
    )
    assert bad_email_resp.status_code == 401


async def test_admin_refresh_token(client: AsyncClient, storage: MemoryStorage):
    # Setup admin
    admin = AdminUser(
        id="adm_test_refresh",
        email="refresh@test.id",
        password_hash=hash_password("pw123"),
        role=AdminRole.editor,
        created_at=datetime.now(UTC),
    )
    await storage.save_admin_user(admin)

    # Login to get refresh token
    login_resp = await client.post(
        "/api/admin/auth/login",
        json={"email": "refresh@test.id", "password": "pw123"},
    )
    assert login_resp.status_code == 200
    refresh_token = login_resp.json()["refresh_token"]

    # Refresh token exchange
    ref_resp = await client.post(
        "/api/admin/auth/refresh",
        json={"refresh_token": refresh_token},
    )
    assert ref_resp.status_code == 200
    assert "access_token" in ref_resp.json()

    # Invalid refresh token fails with 401
    invalid_resp = await client.post(
        "/api/admin/auth/refresh",
        json={"refresh_token": "bogus-invalid-token"},
    )
    assert invalid_resp.status_code == 401


async def test_admin_token_expiration_and_verification(client: AsyncClient, storage: MemoryStorage):
    admin = AdminUser(
        id="adm_test_jwt",
        email="jwt@test.id",
        password_hash=hash_password("pw123"),
        role=AdminRole.editor,
        created_at=datetime.now(UTC),
    )
    await storage.save_admin_user(admin)

    # Valid token accesses /me
    valid_token = create_access_token(admin)
    me_resp = await client.get(
        "/api/admin/auth/me",
        headers={"Authorization": f"Bearer {valid_token}"},
    )
    assert me_resp.status_code == 200
    assert me_resp.json()["email"] == "jwt@test.id"

    # Missing authorization header fails with 401
    no_auth_resp = await client.get("/api/admin/auth/me")
    assert no_auth_resp.status_code == 401

    # Malformed token fails with 401
    bad_token_resp = await client.get(
        "/api/admin/auth/me",
        headers={"Authorization": "Bearer not-a-jwt"},
    )
    assert bad_token_resp.status_code == 401

    # Dual-mount verification: check /admin/auth/me matches /api/admin/auth/me
    root_me_resp = await client.get(
        "/admin/auth/me",
        headers={"Authorization": f"Bearer {valid_token}"},
    )
    assert root_me_resp.status_code == 200
    assert root_me_resp.json()["id"] == admin.id


async def test_admin_role_enforcement_at_both_layers(storage: MemoryStorage):
    # 1. Service-layer role checks (PIP Task 3.5 & PRD §7.4)
    # super_admin satisfies any required role
    assert_role_permitted(AdminRole.super_admin, None)
    assert_role_permitted(AdminRole.super_admin, AdminRole.editor)
    assert_role_permitted(AdminRole.super_admin, AdminRole.reviewer)
    assert_role_permitted(AdminRole.super_admin, AdminRole.super_admin)

    # editor satisfies editor and None
    assert_role_permitted(AdminRole.editor, None)
    assert_role_permitted(AdminRole.editor, AdminRole.editor)

    # editor fails when reviewer or super_admin required
    with pytest.raises(InsufficientRoleError):
        assert_role_permitted(AdminRole.editor, AdminRole.reviewer)

    with pytest.raises(InsufficientRoleError):
        assert_role_permitted(AdminRole.editor, AdminRole.super_admin)

    # reviewer fails when super_admin required
    with pytest.raises(InsufficientRoleError):
        assert_role_permitted(AdminRole.reviewer, AdminRole.super_admin)


async def test_admin_bootstrap_blocked_in_production(
    client: AsyncClient, storage: MemoryStorage, monkeypatch
):
    settings = get_settings()
    monkeypatch.setattr(settings, "env", Env.production)

    resp = await client.post(
        "/api/admin/auth/bootstrap",
        json={"email": "hacker@evil.com", "password": "password123"},
    )
    assert resp.status_code == 403
    assert "forbidden in production" in resp.json()["detail"].lower()
