"""Storage interface.

Only modules in this package may import a database SDK. Everything above the
storage layer talks to this protocol, which is what makes the test suite run
without an emulator and keeps a future backend swap to one directory.
"""

from __future__ import annotations

from datetime import datetime
from typing import Protocol

from models import (
    AdminAuditLog,
    AdminUser,
    Article,
    ArticleChunk,
    FlaggedChunk,
    Question,
    QuestionCluster,
    Session,
    SystemConfig,
    Topic,
    User,
)
from models.enums import ArticleStatus, AuthMethod, ChunkDecision, Platform


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

    async def list_questions(
        self,
        topic_slug: str | None = None,
        is_refused: bool | None = None,
        is_crisis: bool | None = None,
        has_grounding: bool | None = None,
        answer_source: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Question]: ...

    async def count_questions(
        self,
        topic_slug: str | None = None,
        is_refused: bool | None = None,
        is_crisis: bool | None = None,
        has_grounding: bool | None = None,
        answer_source: str | None = None,
    ) -> int: ...

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

    # --- corpus & articles ---------------------------------------------------
    async def get_article(self, article_id: str) -> Article | None: ...

    async def get_article_by_url(self, url: str) -> Article | None: ...

    async def save_article(self, article: Article) -> None: ...

    async def list_articles(
        self, site: str | None = None, status: ArticleStatus | None = None
    ) -> list[Article]: ...

    # --- article chunks & vector search --------------------------------------
    async def get_chunk(self, chunk_id: str) -> ArticleChunk | None: ...

    async def save_chunk(self, chunk: ArticleChunk) -> None: ...

    async def save_chunks_batch(self, chunks: list[ArticleChunk]) -> None: ...

    async def list_chunks_by_article(self, article_id: str) -> list[ArticleChunk]: ...

    async def delete_chunks_by_article(self, article_id: str) -> None: ...

    async def count_article_chunks(self) -> int: ...

    async def find_nearest_chunks(
        self,
        query_vector: list[float],
        limit: int = 8,
        site_allowlist: frozenset[str] | None = None,
        min_similarity: float = 0.0,
    ) -> list[tuple[ArticleChunk, float]]: ...

    # --- flagged chunks (OI-1) -----------------------------------------------
    async def save_flagged_chunk(self, flagged: FlaggedChunk) -> None: ...

    async def list_flagged_chunks(
        self, decision: ChunkDecision | None = None
    ) -> list[FlaggedChunk]: ...

    # --- audit log (F-37) ----------------------------------------------------
    async def save_audit_log(self, entry: AdminAuditLog) -> None: ...

    async def list_audit_logs(self, limit: int = 50) -> list[AdminAuditLog]: ...

    # --- clusters (F-22) -----------------------------------------------------
    async def save_cluster(self, cluster: QuestionCluster) -> None: ...

    async def get_cluster(self, cluster_id: str) -> QuestionCluster | None: ...

    async def list_clusters(self, topic_slug: str | None = None) -> list[QuestionCluster]: ...

    async def delete_cluster(self, cluster_id: str) -> None: ...

    # --- retention purge (F-37) ----------------------------------------------
    async def purge_questions_older_than(self, cutoff: datetime) -> int: ...
