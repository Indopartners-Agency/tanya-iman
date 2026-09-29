from __future__ import annotations

from datetime import UTC, datetime

import pytest

from models import Citation, Question, SystemConfig, Topic
from models.enums import AnswerSource, AuthMethod, Platform
from scripts.seed import seed_database
from storage.memory import MemoryStorage

pytestmark = pytest.mark.asyncio


async def test_user_lifecycle(storage: MemoryStorage):
    uid = "u_lifecycle_test"
    user = await storage.create_user(uid, AuthMethod.sms)
    assert user.uid == uid
    assert user.auth_method == AuthMethod.sms
    assert user.question_count == 0

    fetched = await storage.get_user(uid)
    assert fetched is not None
    assert fetched.uid == uid

    now = datetime.now(UTC)
    await storage.touch_user(uid, now)
    updated = await storage.get_user(uid)
    assert updated is not None
    assert updated.question_count == 1
    assert updated.last_active_at == now


async def test_session_lifecycle(storage: MemoryStorage):
    uid = "u_session_test"
    now = datetime.now(UTC)
    session = await storage.create_session(
        uid=uid,
        platform=Platform.web,
        embed_origin="https://isadanislam.org",
        now=now,
        ttl_hours=24,
    )
    assert session.uid == uid
    assert session.platform == Platform.web
    assert session.embed_origin == "https://isadanislam.org"
    assert session.message_count == 0

    fetched = await storage.get_session(session.id)
    assert fetched is not None
    assert fetched.id == session.id

    turn_time = datetime.now(UTC)
    await storage.record_turn(session.id, turn_time, ttl_hours=24)
    updated = await storage.get_session(session.id)
    assert updated is not None
    assert updated.message_count == 1
    assert updated.last_message_at == turn_time


async def test_question_and_citations(storage: MemoryStorage):
    qid = "q_storage_test"
    now = datetime.now(UTC)
    citations = [
        Citation(
            title="Kasih Allah",
            url="https://isadanislam.org/kasih",
            site="isadanislam.org",
            article_id="art_1",
        )
    ]
    question = Question(
        id=qid,
        session_id="s_test",
        uid="u_test",
        question_text="Bagaimana kasih Allah?",
        answer_text="Kasih Allah kekal.",
        answer_source=AnswerSource.generated,
        topic_slug="kasih-allah",
        citations=citations,
        created_at=now,
    )
    await storage.save_question(question)

    fetched = await storage.get_question(qid)
    assert fetched is not None
    assert fetched.id == qid
    assert fetched.citations[0].url == "https://isadanislam.org/kasih"

    # Test recent_questions
    recent = await storage.recent_questions("s_test", limit=5)
    assert len(recent) == 1
    assert recent[0].id == qid


async def test_like_idempotency(storage: MemoryStorage):
    uid = "u_liker"
    qid = "q_likeable"

    question = Question(
        id=qid,
        session_id="s_test",
        uid="u_author",
        question_text="Test question",
        answer_source=AnswerSource.generated,
        created_at=datetime.now(UTC),
    )
    await storage.save_question(question)

    assert await storage.is_liked(uid, qid) is False

    # First like
    count1 = await storage.set_like(uid, qid, True)
    assert count1 == 1
    assert await storage.is_liked(uid, qid) is True

    # Duplicate like (idempotent)
    count2 = await storage.set_like(uid, qid, True)
    assert count2 == 1

    # Unlike
    count3 = await storage.set_like(uid, qid, False)
    assert count3 == 0
    assert await storage.is_liked(uid, qid) is False


async def test_rate_window_increment(storage: MemoryStorage):
    uid = "u_rate_test"
    bucket = "2026-09-25T16"

    c1 = await storage.increment_rate_window(uid, bucket)
    c2 = await storage.increment_rate_window(uid, bucket)
    c3 = await storage.increment_rate_window(uid, bucket)
    assert c1 == 1
    assert c2 == 2
    assert c3 == 3

    # Different bucket is isolated
    other_bucket_count = await storage.increment_rate_window(uid, "2026-09-25T17")
    assert other_bucket_count == 1


async def test_topics_storage(storage: MemoryStorage):
    topic = Topic(
        slug="kasih-allah",
        name_id="Kasih Allah",
        name_en="Love of Allah",
        curated_answer="Kasih Allah dinyatakan bagi semua orang.",
        curated_status="published",
    )
    await storage.save_topic(topic)

    fetched = await storage.get_topic("kasih-allah")
    assert fetched is not None
    assert fetched.slug == "kasih-allah"
    assert fetched.curated_status == "published"
    assert fetched.curated_answer == "Kasih Allah dinyatakan bagi semua orang."

    topics_list = await storage.list_topics()
    assert len(topics_list) >= 1
    assert any(t.slug == "kasih-allah" for t in topics_list)


async def test_system_config_storage(storage: MemoryStorage):
    cfg = SystemConfig(key="rate_limit_per_hour", value="30")
    await storage.set_system_config(cfg)

    fetched = await storage.get_system_config("rate_limit_per_hour")
    assert fetched is not None
    assert fetched.key == "rate_limit_per_hour"
    assert fetched.value == "30"


async def test_seed_database_idempotency(storage: MemoryStorage):
    # First seed
    await seed_database(storage)
    topics = await storage.list_topics()
    assert len(topics) == 14  # 13 canonical + lainnya
    assert any(t.slug == "kasih-allah" for t in topics)
    assert any(t.slug == "lainnya" for t in topics)

    cfg = await storage.get_system_config("rate_limit_per_hour")
    assert cfg is not None
    assert cfg.value == "30"

    # Simulate editor setting a curated answer
    target_topic = await storage.get_topic("kasih-allah")
    assert target_topic is not None
    target_topic.curated_answer = "Editorial answer test"
    target_topic.curated_status = "published"
    await storage.save_topic(target_topic)

    # Second seed run (must NOT overwrite curated answer)
    await seed_database(storage)
    refetched = await storage.get_topic("kasih-allah")
    assert refetched is not None
    assert refetched.curated_answer == "Editorial answer test"
    assert refetched.curated_status == "published"
