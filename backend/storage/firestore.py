"""Firestore storage.

The only module in the codebase permitted to import the Firestore SDK.

Phase 1, Task 1.2. The collection shape is specified in
docs/tdd.md section 3.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from google.cloud import firestore  # type: ignore[attr-defined]
from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
from google.cloud.firestore_v1.vector import Vector

from models import (
    AdminUser,
    Article,
    ArticleChunk,
    Citation,
    FlaggedChunk,
    Question,
    Session,
    SystemConfig,
    Topic,
    User,
)
from models.enums import AdminRole, ArticleStatus, AuthMethod, ChunkDecision, Platform

USERS = "users"
SESSIONS = "sessions"
QUESTIONS = "questions"
LIKES = "likes"
RATE_WINDOWS = "rate_windows"
ARTICLES = "articles"
ARTICLE_CHUNKS = "article_chunks"
FLAGGED_CHUNKS = "flagged_chunks"
TOPICS = "topics"
SYSTEM_CONFIG = "system_config"
ADMIN_USERS = "admin_users"


class FirestoreStorage:
    def __init__(
        self,
        project: str,
        database: str = "(default)",
        credentials: Any | None = None,
    ) -> None:
        self._db = firestore.AsyncClient(
            project=project, database=database, credentials=credentials
        )

    # --- users ---------------------------------------------------------------

    async def get_user(self, uid: str) -> User | None:
        snap = await self._db.collection(USERS).document(uid).get()
        return User(**snap.to_dict()) if snap.exists else None

    async def create_user(self, uid: str, auth_method: AuthMethod) -> User:
        now = datetime.now(UTC)
        user = User(uid=uid, auth_method=auth_method, created_at=now, last_active_at=now)
        await self._db.collection(USERS).document(uid).set(user.model_dump())
        return user

    async def touch_user(self, uid: str, at: datetime) -> None:
        await (
            self._db.collection(USERS)
            .document(uid)
            .update({"last_active_at": at, "question_count": firestore.Increment(1)})
        )

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
        await self._db.collection(SESSIONS).document(session.id).set(session.model_dump())
        return session

    async def get_session(self, session_id: str) -> Session | None:
        snap = await self._db.collection(SESSIONS).document(session_id).get()
        return Session(**snap.to_dict()) if snap.exists else None

    async def record_turn(self, session_id: str, now: datetime, ttl_hours: int) -> None:
        await (
            self._db.collection(SESSIONS)
            .document(session_id)
            .update(
                {
                    "last_message_at": now,
                    "expires_at": now + timedelta(hours=ttl_hours),
                    "message_count": firestore.Increment(1),
                }
            )
        )

    # --- questions -----------------------------------------------------------

    async def save_question(self, question: Question) -> None:
        await self._db.collection(QUESTIONS).document(question.id).set(question.model_dump())

    async def get_question(self, question_id: str) -> Question | None:
        snap = await self._db.collection(QUESTIONS).document(question_id).get()
        if not snap.exists:
            return None
        data = snap.to_dict()
        data["citations"] = [Citation(**c) for c in data.get("citations", [])]
        return Question(**data)

    async def recent_questions(self, session_id: str, limit: int) -> list[Question]:
        query = (
            self._db.collection(QUESTIONS)
            .where(filter=firestore.FieldFilter("session_id", "==", session_id))
            .order_by("created_at", direction=firestore.Query.DESCENDING)
            .limit(limit)
        )
        rows = [Question(**doc.to_dict()) async for doc in query.stream()]
        return list(reversed(rows))

    async def list_questions(
        self,
        topic_slug: str | None = None,
        is_refused: bool | None = None,
        is_crisis: bool | None = None,
        has_grounding: bool | None = None,
        answer_source: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Question]:
        query = self._db.collection(QUESTIONS)
        if topic_slug:
            query = query.where(filter=firestore.FieldFilter("topic_slug", "==", topic_slug))
        if is_refused is not None:
            query = query.where(filter=firestore.FieldFilter("is_refused", "==", is_refused))
        if is_crisis is not None:
            query = query.where(filter=firestore.FieldFilter("is_crisis", "==", is_crisis))
        if has_grounding is not None:
            query = query.where(filter=firestore.FieldFilter("has_grounding", "==", has_grounding))
        if answer_source:
            query = query.where(filter=firestore.FieldFilter("answer_source", "==", answer_source))

        query = query.order_by("created_at", direction=firestore.Query.DESCENDING).limit(limit)
        if offset > 0:
            query = query.offset(offset)

        rows: list[Question] = []
        async for doc in query.stream():
            data = doc.to_dict()
            data["citations"] = [Citation(**c) for c in data.get("citations", [])]
            rows.append(Question(**data))
        return rows

    async def count_questions(
        self,
        topic_slug: str | None = None,
        is_refused: bool | None = None,
        is_crisis: bool | None = None,
        has_grounding: bool | None = None,
        answer_source: str | None = None,
    ) -> int:
        query = self._db.collection(QUESTIONS)
        if topic_slug:
            query = query.where(filter=firestore.FieldFilter("topic_slug", "==", topic_slug))
        if is_refused is not None:
            query = query.where(filter=firestore.FieldFilter("is_refused", "==", is_refused))
        if is_crisis is not None:
            query = query.where(filter=firestore.FieldFilter("is_crisis", "==", is_crisis))
        if has_grounding is not None:
            query = query.where(filter=firestore.FieldFilter("has_grounding", "==", has_grounding))
        if answer_source:
            query = query.where(filter=firestore.FieldFilter("answer_source", "==", answer_source))

        agg = query.count()
        result = await agg.get()
        return int(result[0][0].value)

    # --- likes ---------------------------------------------------------------

    async def set_like(self, uid: str, question_id: str, liked: bool) -> int:
        # F-33: the document ID makes the like idempotent by construction.
        like_ref = self._db.collection(LIKES).document(f"{uid}_{question_id}")
        question_ref = self._db.collection(QUESTIONS).document(question_id)

        existing = await like_ref.get()
        if liked and not existing.exists:
            await like_ref.set(
                {"uid": uid, "question_id": question_id, "created_at": datetime.now(UTC)}
            )
            await question_ref.update({"like_count": firestore.Increment(1)})
        elif not liked and existing.exists:
            await like_ref.delete()
            await question_ref.update({"like_count": firestore.Increment(-1)})

        snap = await question_ref.get()
        return int(snap.to_dict().get("like_count", 0)) if snap.exists else 0

    async def is_liked(self, uid: str, question_id: str) -> bool:
        snap = await self._db.collection(LIKES).document(f"{uid}_{question_id}").get()
        return snap.exists

    # --- rate limiting -------------------------------------------------------

    async def increment_rate_window(self, uid: str, bucket: str) -> int:
        ref = self._db.collection(RATE_WINDOWS).document(f"{uid}:{bucket}")

        @firestore.async_transactional
        async def _bump(transaction: firestore.AsyncTransaction) -> int:
            snap = await ref.get(transaction=transaction)
            count = int(snap.to_dict().get("count", 0)) if snap.exists else 0
            count += 1
            transaction.set(ref, {"uid": uid, "bucket": bucket, "count": count})
            return count

        return await _bump(self._db.transaction())

    # --- topics --------------------------------------------------------------

    async def save_topic(self, topic: Topic) -> None:
        await self._db.collection(TOPICS).document(topic.slug).set(topic.model_dump())

    async def get_topic(self, slug: str) -> Topic | None:
        snap = await self._db.collection(TOPICS).document(slug).get()
        if not snap.exists:
            return None
        data = snap.to_dict()
        data["curated_citations"] = [Citation(**c) for c in data.get("curated_citations", [])]
        return Topic(**data)

    async def list_topics(self) -> list[Topic]:
        query = self._db.collection(TOPICS)
        rows: list[Topic] = []
        async for doc in query.stream():
            data = doc.to_dict()
            data["curated_citations"] = [Citation(**c) for c in data.get("curated_citations", [])]
            rows.append(Topic(**data))
        return rows

    # --- system config -------------------------------------------------------

    async def get_system_config(self, key: str) -> SystemConfig | None:
        snap = await self._db.collection(SYSTEM_CONFIG).document(key).get()
        return SystemConfig(**snap.to_dict()) if snap.exists else None

    async def set_system_config(self, config: SystemConfig) -> None:
        await self._db.collection(SYSTEM_CONFIG).document(config.key).set(config.model_dump())

    # --- admin users ---------------------------------------------------------

    async def get_admin_user(self, admin_id: str) -> AdminUser | None:
        snap = await self._db.collection(ADMIN_USERS).document(admin_id).get()
        return AdminUser(**snap.to_dict()) if snap.exists else None

    async def get_admin_user_by_email(self, email: str) -> AdminUser | None:
        email_clean = email.strip().lower()
        query = (
            self._db.collection(ADMIN_USERS)
            .where(filter=firestore.FieldFilter("email", "==", email_clean))
            .limit(1)
        )
        async for doc in query.stream():
            return AdminUser(**doc.to_dict())
        return None

    async def get_admin_user_by_refresh_token_hash(self, token_hash: str) -> AdminUser | None:
        query = (
            self._db.collection(ADMIN_USERS)
            .where(filter=firestore.FieldFilter("refresh_token_hash", "==", token_hash))
            .limit(1)
        )
        async for doc in query.stream():
            return AdminUser(**doc.to_dict())
        return None

    async def save_admin_user(self, admin: AdminUser) -> None:
        await self._db.collection(ADMIN_USERS).document(admin.id).set(admin.model_dump())

    async def count_super_admins(self) -> int:
        query = self._db.collection(ADMIN_USERS).where(
            filter=firestore.FieldFilter("role", "==", AdminRole.super_admin.value)
        )
        agg = query.count()
        result = await agg.get()
        return int(result[0][0].value)

    # --- corpus & articles ---------------------------------------------------

    async def get_article(self, article_id: str) -> Article | None:
        snap = await self._db.collection(ARTICLES).document(article_id).get()
        return Article(**snap.to_dict()) if snap.exists else None

    async def get_article_by_url(self, url: str) -> Article | None:
        query = (
            self._db.collection(ARTICLES)
            .where(filter=firestore.FieldFilter("url", "==", url))
            .limit(1)
        )
        async for doc in query.stream():
            return Article(**doc.to_dict())
        return None

    async def save_article(self, article: Article) -> None:
        await self._db.collection(ARTICLES).document(article.id).set(article.model_dump())

    async def list_articles(
        self, site: str | None = None, status: ArticleStatus | None = None
    ) -> list[Article]:
        query = self._db.collection(ARTICLES)
        if site is not None:
            query = query.where(filter=firestore.FieldFilter("site", "==", site))
        if status is not None:
            query = query.where(filter=firestore.FieldFilter("status", "==", status.value))

        articles: list[Article] = []
        async for doc in query.stream():
            articles.append(Article(**doc.to_dict()))
        return articles

    # --- article chunks & vector search --------------------------------------

    async def get_chunk(self, chunk_id: str) -> ArticleChunk | None:
        snap = await self._db.collection(ARTICLE_CHUNKS).document(chunk_id).get()
        return ArticleChunk(**snap.to_dict()) if snap.exists else None

    async def save_chunk(self, chunk: ArticleChunk) -> None:
        data = chunk.model_dump()
        if chunk.embedding is not None:
            data["embedding"] = Vector(chunk.embedding)
        await self._db.collection(ARTICLE_CHUNKS).document(chunk.id).set(data)

    async def save_chunks_batch(self, chunks: list[ArticleChunk]) -> None:
        # Firestore batch maximum is 500 writes
        for i in range(0, len(chunks), 400):
            batch = self._db.batch()
            for chunk in chunks[i : i + 400]:
                data = chunk.model_dump()
                if chunk.embedding is not None:
                    data["embedding"] = Vector(chunk.embedding)
                doc_ref = self._db.collection(ARTICLE_CHUNKS).document(chunk.id)
                batch.set(doc_ref, data)
            await batch.commit()

    async def list_chunks_by_article(self, article_id: str) -> list[ArticleChunk]:
        query = self._db.collection(ARTICLE_CHUNKS).where(
            filter=firestore.FieldFilter("article_id", "==", article_id)
        )
        chunks: list[ArticleChunk] = []
        async for doc in query.stream():
            chunks.append(ArticleChunk(**doc.to_dict()))
        return chunks

    async def delete_chunks_by_article(self, article_id: str) -> None:
        query = self._db.collection(ARTICLE_CHUNKS).where(
            filter=firestore.FieldFilter("article_id", "==", article_id)
        )
        doc_ids: list[str] = []
        async for doc in query.stream():
            doc_ids.append(doc.id)

        for i in range(0, len(doc_ids), 400):
            batch = self._db.batch()
            for doc_id in doc_ids[i : i + 400]:
                batch.delete(self._db.collection(ARTICLE_CHUNKS).document(doc_id))
            await batch.commit()

    async def count_article_chunks(self) -> int:
        agg = self._db.collection(ARTICLE_CHUNKS).count()
        result = await agg.get()
        return int(result[0][0].value)

    async def find_nearest_chunks(
        self,
        query_vector: list[float],
        limit: int = 8,
        site_allowlist: frozenset[str] | None = None,
        min_similarity: float = 0.0,
    ) -> list[tuple[ArticleChunk, float]]:
        coll = self._db.collection(ARTICLE_CHUNKS)
        results: list[tuple[ArticleChunk, float]] = []

        if site_allowlist:
            for site in site_allowlist:
                try:
                    site_query = coll.where(filter=firestore.FieldFilter("site", "==", site))
                    vector_query = site_query.find_nearest(
                        vector_field="embedding",
                        query_vector=Vector(query_vector),
                        distance_measure=DistanceMeasure.COSINE,
                        limit=limit,
                        distance_result_field="vector_distance",
                    )
                    async for doc in vector_query.stream():
                        data = doc.to_dict()
                        if not data.get("is_retrievable", True):
                            continue
                        dist = data.pop("vector_distance", 1.0)
                        similarity = 1.0 - float(dist)
                        if similarity >= min_similarity:
                            results.append((ArticleChunk(**data), similarity))
                except Exception:
                    pass
        else:
            try:
                vector_query = coll.find_nearest(
                    vector_field="embedding",
                    query_vector=Vector(query_vector),
                    distance_measure=DistanceMeasure.COSINE,
                    limit=limit,
                    distance_result_field="vector_distance",
                )
                async for doc in vector_query.stream():
                    data = doc.to_dict()
                    if not data.get("is_retrievable", True):
                        continue
                    dist = data.pop("vector_distance", 1.0)
                    similarity = 1.0 - float(dist)
                    if similarity >= min_similarity:
                        results.append((ArticleChunk(**data), similarity))
            except Exception:
                pass

        if not results:
            # Fallback for emulator or non-indexed environments
            import math

            query = coll
            if site_allowlist:
                query = query.where(
                    filter=firestore.FieldFilter("site", "in", list(site_allowlist))
                )

            all_chunks: list[ArticleChunk] = []
            async for doc in query.stream():
                data = doc.to_dict()
                if not data.get("is_retrievable", True):
                    continue
                all_chunks.append(ArticleChunk(**data))

            for chunk in all_chunks:
                if not chunk.embedding:
                    continue
                dot = sum(a * b for a, b in zip(query_vector, chunk.embedding, strict=False))
                norm1 = math.sqrt(sum(a * a for a in query_vector))
                norm2 = math.sqrt(sum(b * b for b in chunk.embedding))
                if norm1 > 0 and norm2 > 0:
                    sim = dot / (norm1 * norm2)
                    if sim >= min_similarity:
                        results.append((chunk, sim))

        results.sort(key=lambda item: item[1], reverse=True)
        return results[:limit]

    # --- flagged chunks (OI-1) -----------------------------------------------

    async def save_flagged_chunk(self, flagged: FlaggedChunk) -> None:
        await self._db.collection(FLAGGED_CHUNKS).document(flagged.id).set(flagged.model_dump())

    async def list_flagged_chunks(
        self, decision: ChunkDecision | None = None
    ) -> list[FlaggedChunk]:
        query = self._db.collection(FLAGGED_CHUNKS)
        if decision is not None:
            query = query.where(filter=firestore.FieldFilter("decision", "==", decision.value))

        flagged: list[FlaggedChunk] = []
        async for doc in query.stream():
            flagged.append(FlaggedChunk(**doc.to_dict()))
        return flagged
