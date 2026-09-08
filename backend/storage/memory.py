"""In-memory storage.

Used by the test suite and by first-run local development, so that neither
requires a Firestore emulator. It implements the same protocol as the Firestore
backend, which means a test that passes here exercises the real code path above
the storage layer.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta

from models import Question, Session, User
from models.enums import AuthMethod, Platform


class MemoryStorage:
    def __init__(self) -> None:
        self._users: dict[str, User] = {}
        self._sessions: dict[str, Session] = {}
        self._questions: dict[str, Question] = {}
        self._likes: set[str] = set()
        self._rate: dict[str, int] = {}
        self._chunks: int = 0
        self._lock = asyncio.Lock()

    # --- users ---------------------------------------------------------------

    async def get_user(self, uid: str) -> User | None:
        return self._users.get(uid)

    async def create_user(self, uid: str, auth_method: AuthMethod) -> User:
        now = datetime.now()
        user = User(
            uid=uid,
            auth_method=auth_method,
            created_at=now,
            last_active_at=now,
        )
        self._users[uid] = user
        return user

    async def touch_user(self, uid: str, at: datetime) -> None:
        user = self._users.get(uid)
        if user is not None:
            user.last_active_at = at
            user.question_count += 1

    # --- sessions ------------------------------------------------------------

    async def create_session(
        self,
        uid: str,
        platform: Platform,
        embed_origin: str | None,
        now: datetime,
        ttl_hours: int,
    ) -> Session:
        session = Session(
            id=f"s_{uuid.uuid4().hex[:16]}",
            uid=uid,
            platform=platform,
            embed_origin=embed_origin,
            started_at=now,
            last_message_at=now,
            expires_at=now + timedelta(hours=ttl_hours),
        )
        self._sessions[session.id] = session
        return session

    async def get_session(self, session_id: str) -> Session | None:
        return self._sessions.get(session_id)

    async def record_turn(self, session_id: str, now: datetime, ttl_hours: int) -> None:
        session = self._sessions.get(session_id)
        if session is None:
            return
        session.last_message_at = now
        session.expires_at = now + timedelta(hours=ttl_hours)
        session.message_count += 1

    # --- questions -----------------------------------------------------------

    async def save_question(self, question: Question) -> None:
        self._questions[question.id] = question

    async def get_question(self, question_id: str) -> Question | None:
        return self._questions.get(question_id)

    async def recent_questions(self, session_id: str, limit: int) -> list[Question]:
        rows = [q for q in self._questions.values() if q.session_id == session_id]
        rows.sort(key=lambda q: q.created_at)
        return rows[-limit:]

    # --- likes ---------------------------------------------------------------

    async def set_like(self, uid: str, question_id: str, liked: bool) -> int:
        key = f"{uid}_{question_id}"
        if liked:
            self._likes.add(key)
        else:
            self._likes.discard(key)

        question = self._questions.get(question_id)
        if question is None:
            return 0
        question.like_count = sum(1 for k in self._likes if k.endswith(f"_{question_id}"))
        return question.like_count

    async def is_liked(self, uid: str, question_id: str) -> bool:
        return f"{uid}_{question_id}" in self._likes

    # --- rate limiting -------------------------------------------------------

    async def increment_rate_window(self, uid: str, bucket: str) -> int:
        # The lock stands in for the Firestore transaction. Without it, two
        # concurrent requests at the limit boundary could both pass.
        async with self._lock:
            key = f"{uid}:{bucket}"
            self._rate[key] = self._rate.get(key, 0) + 1
            return self._rate[key]

    # --- corpus --------------------------------------------------------------

    async def count_article_chunks(self) -> int:
        return self._chunks

    # --- test helpers --------------------------------------------------------

    def seed_chunk_count(self, count: int) -> None:
        self._chunks = count
