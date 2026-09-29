from __future__ import annotations

from datetime import UTC, datetime

import pytest

from models import Question, Topic
from models.enums import AnswerSource
from services.clustering import (
    assign_to_cluster,
    merge_clusters,
    promote_cluster_to_curated,
    rename_cluster,
)
from storage.memory import MemoryStorage

pytestmark = pytest.mark.asyncio


async def test_clustering_assignment_and_seeding(storage: MemoryStorage):
    # Seed topic
    await storage.save_topic(Topic(slug="kasih-allah", name_id="Kasih Allah", name_en="God's Love"))

    # 1. First question seeds a new cluster
    q1 = Question(
        id="q1",
        session_id="s1",
        uid="u1",
        question_text="Bagaimana Allah mengasihi manusia yang berdosa?",
        topic_slug="kasih-allah",
        answer_source=AnswerSource.generated,
        created_at=datetime.now(UTC),
    )
    c1 = await assign_to_cluster(storage, q1)
    assert c1.canonical_text == q1.question_text
    assert c1.question_ids == ["q1"]
    assert c1.topic_slug == "kasih-allah"

    # 2. Near-identical question joins the same cluster
    q2 = Question(
        id="q2",
        session_id="s2",
        uid="u2",
        question_text="Bagaimana Allah mengasihi orang yang berdosa?",
        topic_slug="kasih-allah",
        answer_source=AnswerSource.generated,
        created_at=datetime.now(UTC),
    )
    c2 = await assign_to_cluster(storage, q2, threshold=0.65)
    assert c2.id == c1.id
    assert "q2" in c2.question_ids
    assert len(c2.member_texts) == 2

    # 3. Disjoint question seeds a separate cluster
    q3 = Question(
        id="q3",
        session_id="s3",
        uid="u3",
        question_text="Berapa banyak kitab dalam perjanjian lama?",
        topic_slug="kasih-allah",
        answer_source=AnswerSource.generated,
        created_at=datetime.now(UTC),
    )
    c3 = await assign_to_cluster(storage, q3)
    assert c3.id != c1.id
    assert c3.question_ids == ["q3"]


async def test_clustering_within_topic_boundary(storage: MemoryStorage):
    await storage.save_topic(Topic(slug="topik-a", name_id="Topik A", name_en="Topic A"))
    await storage.save_topic(Topic(slug="topik-b", name_id="Topik B", name_en="Topic B"))

    # Exactly same-worded questions in different topics must NOT merge (PRD §Task 6.3)
    q_a = Question(
        id="qa",
        session_id="sa",
        uid="ua",
        question_text="Apa makna keselamatan sejati?",
        topic_slug="topik-a",
        answer_source=AnswerSource.generated,
        created_at=datetime.now(UTC),
    )
    ca = await assign_to_cluster(storage, q_a)

    q_b = Question(
        id="qb",
        session_id="sb",
        uid="ub",
        question_text="Apa makna keselamatan sejati?",
        topic_slug="topik-b",
        answer_source=AnswerSource.generated,
        created_at=datetime.now(UTC),
    )
    cb = await assign_to_cluster(storage, q_b)

    assert ca.id != cb.id
    assert ca.topic_slug == "topik-a"
    assert cb.topic_slug == "topik-b"


async def test_cluster_merge_rename_and_promote(storage: MemoryStorage):
    await storage.save_topic(Topic(slug="doa", name_id="Doa", name_en="Prayer"))

    q1 = Question(
        id="q1",
        session_id="s1",
        uid="u1",
        question_text="Bagaimana cara berdoa?",
        topic_slug="doa",
        answer_source=AnswerSource.generated,
        created_at=datetime.now(UTC),
    )
    q2 = Question(
        id="q2",
        session_id="s2",
        uid="u2",
        question_text="Waktu yang tepat untuk berdoa",
        topic_slug="doa",
        answer_source=AnswerSource.generated,
        created_at=datetime.now(UTC),
    )
    c1 = await assign_to_cluster(storage, q1)
    c2 = await assign_to_cluster(storage, q2)
    assert c1.id != c2.id

    # 1. Rename
    renamed = await rename_cluster(storage, c1.id, "Tata Cara Berdoa Kristen")
    assert renamed.canonical_text == "Tata Cara Berdoa Kristen"

    # 2. Merge c2 into c1
    merged = await merge_clusters(storage, c1.id, c2.id)
    assert merged.id == c1.id
    assert "q1" in merged.question_ids
    assert "q2" in merged.question_ids
    assert await storage.get_cluster(c2.id) is None

    # 3. Promote to curated draft
    topic = await promote_cluster_to_curated(storage, c1.id, "editor@tanyaiman.id")
    assert topic.curated_answer == "Tata Cara Berdoa Kristen"
    assert topic.curated_status == "draft"
    assert topic.updated_by == "editor@tanyaiman.id"
