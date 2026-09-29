"""Session lifecycle.

A session is a conversation window, not a login. It carries the platform the
user arrived on (F-24 web / widget / android) and the last few turns that the
engine gets as context (F-6).
"""

from __future__ import annotations

from datetime import UTC, datetime

from config import get_settings
from models import Question, Session
from models.enums import Platform
from storage.base import Storage


def _now() -> datetime:
    return datetime.now(UTC)


def _is_expired(expires_at: datetime) -> bool:
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=UTC)
    return expires_at <= _now()


class SessionExpiredError(Exception):
    pass


class SessionNotFoundError(Exception):
    pass


async def start_session(
    storage: Storage,
    uid: str,
    platform: Platform,
    embed_origin: str | None = None,
) -> Session:
    settings = get_settings()
    return await storage.create_session(
        uid=uid,
        platform=platform,
        embed_origin=embed_origin,
        now=_now(),
        ttl_hours=settings.session_ttl_hours,
    )


async def load_active_session(storage: Storage, session_id: str, uid: str) -> Session:
    """Fetch a session, verifying ownership and expiry.

    Ownership is checked here rather than at the router, because every caller
    needs it and one that forgets is an IDOR.
    """
    session = await storage.get_session(session_id)
    if session is None or session.uid != uid:
        raise SessionNotFoundError(session_id)
    if _is_expired(session.expires_at):
        raise SessionExpiredError(session_id)
    return session


async def record_turn(storage: Storage, session_id: str) -> None:
    settings = get_settings()
    await storage.record_turn(session_id, now=_now(), ttl_hours=settings.session_ttl_hours)


async def conversation_context(storage: Storage, session_id: str) -> list[Question]:
    """The last N turns handed to the engine as context (F-6).

    Bounded on purpose: an unbounded history is both a cost problem and a
    prompt-injection surface that grows with the length of the conversation.
    """
    settings = get_settings()
    if settings.context_turns == 0:
        return []
    return await storage.recent_questions(session_id, limit=settings.context_turns)
