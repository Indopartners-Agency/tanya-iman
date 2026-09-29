"""User records.

The seeker-facing product never asks for a name or an email. A user record is a
Firebase uid, how they authenticated, and counters. Phone numbers, when present,
are stored encrypted and are never returned by any API (TDD section 8).
"""

from __future__ import annotations

from datetime import UTC, datetime

from models import User
from models.enums import AuthMethod
from storage.base import Storage


async def ensure_user(storage: Storage, uid: str, auth_method: AuthMethod) -> User:
    """Get-or-create. Called on every authenticated request, so it must be cheap."""
    user = await storage.get_user(uid)
    if user is None:
        user = await storage.create_user(uid, auth_method)
    return user


async def record_activity(storage: Storage, uid: str) -> None:
    await storage.touch_user(uid, at=datetime.now(UTC))
