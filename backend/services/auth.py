"""Token verification.

Seeker identity always comes from a Firebase ID token, including for guests —
anonymous auth gives a guest a real uid, which is what makes the guest-to-phone
upgrade in F-4 possible without losing their history.

In development, `AUTH_ALLOW_INSECURE_DEV_TOKENS` accepts `dev:<uid>:<method>` so
the app runs with no Firebase project. The setting is refused outside
development, because a bearer token anyone can forge is a total auth bypass.
"""

from __future__ import annotations

from dataclasses import dataclass

from config import get_settings
from models.enums import AuthMethod


class InvalidTokenError(Exception):
    pass


@dataclass(frozen=True)
class Principal:
    uid: str
    auth_method: AuthMethod


def _parse_dev_token(token: str) -> Principal:
    try:
        _, uid, method = token.split(":", 2)
    except ValueError as exc:
        raise InvalidTokenError("malformed dev token") from exc
    if not uid:
        raise InvalidTokenError("dev token has no uid")
    try:
        return Principal(uid=uid, auth_method=AuthMethod(method))
    except ValueError as exc:
        raise InvalidTokenError(f"unknown auth method '{method}'") from exc


async def verify_token(token: str) -> Principal:
    settings = get_settings()

    if token.startswith("dev:"):
        if not (settings.is_development and settings.auth_allow_insecure_dev_tokens):
            raise InvalidTokenError("dev tokens are rejected outside development")
        return _parse_dev_token(token)

    return await _verify_firebase_token(token)


async def _verify_firebase_token(token: str) -> Principal:  # pragma: no cover - Phase 3
    raise NotImplementedError("Firebase ID token verification lands in Phase 3 (PIP Task 3.1).")
