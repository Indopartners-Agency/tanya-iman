"""Firestore storage.

The only module in the codebase permitted to import the Firestore SDK.

Phase 1, Task 1.2. The collection shape is specified in
docs/tdd.md section 3.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta

from google.cloud import firestore  # type: ignore[attr-defined]

from models import Citation, Question, Session, User
from models.enums import AuthMethod, Platform

USERS = "users"
SESSIONS = "sessions"
QUESTIONS = "questions"
LIKES = "likes"
RATE_WINDOWS = "rate_windows"
ARTICLE_CHUNKS = "article_chunks"


class FirestoreStorage:
    def __init__(self, project: str) -> None:
        self._db = firestore.AsyncClient(project=project)

    # --- users ---------------------------------------------------------------

    async def get_user(self, uid: str) -> User | None:
        snap = await self._db.collection(USERS).document(uid).get()
        return User(**snap.to_dict()) if snap.exists else None

    async def create_user(self, uid: str, auth_method: AuthMethod) -> User:
        now = datetime.now()
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

    # --- likes ---------------------------------------------------------------

    async def set_like(self, uid: str, question_id: str, liked: bool) -> int:
        # F-33: the document ID makes the like idempotent by construction.
        like_ref = self._db.collection(LIKES).document(f"{uid}_{question_id}")
        question_ref = self._db.collection(QUESTIONS).document(question_id)

        existing = await like_ref.get()
        if liked and not existing.exists:
            await like_ref.set(
                {"uid": uid, "question_id": question_id, "created_at": datetime.now()}
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

    # --- corpus --------------------------------------------------------------

    async def count_article_chunks(self) -> int:
        agg = self._db.collection(ARTICLE_CHUNKS).count()
        result = await agg.get()
        return int(result[0][0].value)
