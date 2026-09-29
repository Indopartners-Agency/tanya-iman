"""Storage interface.

Only modules in this package may import a database SDK. Everything above the
storage layer talks to this protocol, which is what makes the test suite run
without an emulator and keeps a future backend swap to one directory.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from models import AdminUser, Question, Session, SystemConfig, Topic, User
from models.enums import AuthMethod, Platform


class Storage(Protocol):
    # --- users ---------------------------------------------------------------
    async def get_user(self, uid: str) -> User | None: ...

    async def create_user(self, uid: str, auth_method: AuthMethod) -> User: ...

    async def touch_user(self, uid: str, at: datetime) -> None: ...

    # --- sessions ------------------------------------------------------------
    async def create_session(
        self,
        uid: str,
        platform: Platform,
        embed_origin: str | None,
        now: datetime,
        ttl_hours: int,
    ) -> Session: ...

    async def get_session(self, session_id: str) -> Session | None: ...

    async def record_turn(self, session_id: str, now: datetime, ttl_hours: int) -> None: ...

    # --- questions -----------------------------------------------------------
    async def save_question(self, question: Question) -> None: ...

    async def get_question(self, question_id: str) -> Question | None: ...

    async def recent_questions(self, session_id: str, limit: int) -> list[Question]: ...

    # --- likes ---------------------------------------------------------------
    async def set_like(self, uid: str, question_id: str, liked: bool) -> int:
        """Idempotent by construction — the like key is ``{uid}_{question_id}``.

        Returns the resulting like count for the question.
        """
        ...

    async def is_liked(self, uid: str, question_id: str) -> bool: ...

    # --- rate limiting -------------------------------------------------------
    async def increment_rate_window(self, uid: str, bucket: str) -> int:
        """Atomically increment and return the count for this uid/hour bucket."""
        ...

    # --- topics --------------------------------------------------------------
    async def save_topic(self, topic: Topic) -> None: ...

    async def get_topic(self, slug: str) -> Topic | None: ...

    async def list_topics(self) -> list[Topic]: ...

    # --- system config -------------------------------------------------------
    async def get_system_config(self, key: str) -> SystemConfig | None: ...

    async def set_system_config(self, config: SystemConfig) -> None: ...

    # --- admin users ---------------------------------------------------------
    async def get_admin_user(self, admin_id: str) -> AdminUser | None: ...

    async def get_admin_user_by_email(self, email: str) -> AdminUser | None: ...

    async def get_admin_user_by_refresh_token_hash(self, token_hash: str) -> AdminUser | None: ...

    async def save_admin_user(self, admin: AdminUser) -> None: ...

    async def count_super_admins(self) -> int: ...

    # --- corpus --------------------------------------------------------------
    async def count_article_chunks(self) -> int: ...
