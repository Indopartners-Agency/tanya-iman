"""CLI tool to create or update an administrator account.

Usage:
    uv run python scripts/create_admin.py \
        --email admin@tanyaiman.id --password secret --role super_admin
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
import uuid
from datetime import UTC, datetime
from pathlib import Path

# Ensure backend root is on sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from models import AdminUser
from models.enums import AdminRole
from services.admin_auth import hash_password
from storage import get_storage

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("create_admin")


async def create_or_update_admin(email: str, password: str, role_name: str) -> None:
    try:
        role = AdminRole(role_name)
    except ValueError as err:
        valid = [r.value for r in AdminRole]
        raise ValueError(f"Invalid role '{role_name}'. Must be one of: {valid}") from err

    storage = get_storage()
    now = datetime.now(UTC)
    pwd_hash = hash_password(password)

    existing = await storage.get_admin_user_by_email(email)
    if existing:
        existing.password_hash = pwd_hash
        existing.role = role
        existing.updated_at = now
        await storage.save_admin_user(existing)
        logger.info("Updated existing admin user: %s (role: %s)", email, role.value)
    else:
        admin_id = f"adm_{uuid.uuid4().hex[:12]}"
        admin = AdminUser(
            id=admin_id,
            email=email.strip().lower(),
            password_hash=pwd_hash,
            role=role,
            is_active=True,
            created_at=now,
            updated_at=now,
        )
        await storage.save_admin_user(admin)
        logger.info("Created new admin user: %s (id: %s, role: %s)", email, admin_id, role.value)


def main() -> None:
    parser = argparse.ArgumentParser(description="Create or update a Tanya Iman admin user.")
    parser.add_argument("--email", required=True, help="Admin user email address")
    parser.add_argument("--password", required=True, help="Plaintext password to hash with bcrypt")
    parser.add_argument(
        "--role",
        default="super_admin",
        choices=["editor", "reviewer", "super_admin"],
        help="Administrative role (default: super_admin)",
    )

    args = parser.parse_args()
    asyncio.run(create_or_update_admin(args.email, args.password, args.role))


if __name__ == "__main__":
    main()
