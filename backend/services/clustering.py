"""Similar-question clustering service (Wave 7 / PIP Task 6.3 / PRD F-22).

Clusters incoming inquiries within their topic classification using semantic
embedding cosine similarity. Provides cluster merging, canonical text renaming,
and cluster promotion to curated answer drafts.
"""

from __future__ import annotations

import math
import uuid
from datetime import UTC, datetime

from ingestion.embedder import DeterministicEmbedder, Embedder
from models import Question, QuestionCluster, Topic
from storage import Storage


def cosine_similarity(v1: list[float], v2: list[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2, strict=True))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


async def assign_to_cluster(
    storage: Storage,
    question: Question,
    embedder: Embedder | None = None,
    threshold: float = 0.85,
) -> QuestionCluster:
    """Assigns an inquiry to an existing within-topic cluster, or seeds a new one."""
    topic_slug = question.topic_slug or "lainnya"
    if embedder is None:
        embedder = DeterministicEmbedder()

    q_vec = await embedder.embed_query(question.question_text)

    # Within-topic clustering: only search clusters matching this question's topic
    existing_clusters = await storage.list_clusters(topic_slug=topic_slug)

    best_sim = -1.0
    best_cluster: QuestionCluster | None = None

    for c in existing_clusters:
        if c.centroid:
            sim = cosine_similarity(q_vec, c.centroid)
            if sim > best_sim:
                best_sim = sim
                best_cluster = c

    now = datetime.now(UTC)

    if best_sim >= threshold and best_cluster is not None:
        if question.id not in best_cluster.question_ids:
            best_cluster.question_ids.append(question.id)
        if question.question_text not in best_cluster.member_texts:
            best_cluster.member_texts.append(question.question_text)

        if question.created_at and (
            not best_cluster.last_asked_at or question.created_at > best_cluster.last_asked_at
        ):
            best_cluster.last_asked_at = question.created_at

        # Update centroid running average and re-normalize
        if best_cluster.centroid:
            n = len(best_cluster.question_ids)
            updated_vec = [
                (c * (n - 1) + q) / n for c, q in zip(best_cluster.centroid, q_vec, strict=True)
            ]
            norm = math.sqrt(sum(x * x for x in updated_vec))
            if norm > 0:
                best_cluster.centroid = [x / norm for x in updated_vec]

        best_cluster.updated_at = now
        await storage.save_cluster(best_cluster)
        return best_cluster

    # Create new cluster seeded by this inquiry
    cluster_id = f"cl_{uuid.uuid4().hex[:12]}"
    new_cluster = QuestionCluster(
        id=cluster_id,
        topic_slug=topic_slug,
        canonical_text=question.question_text,
        question_ids=[question.id],
        member_texts=[question.question_text],
        centroid=q_vec,
        has_curated=False,
        last_asked_at=question.created_at or now,
        created_at=now,
        updated_at=now,
    )
    await storage.save_cluster(new_cluster)
    return new_cluster


async def merge_clusters(
    storage: Storage, target_cluster_id: str, source_cluster_id: str
) -> QuestionCluster:
    """Merges source_cluster into target_cluster, preserving combined members."""
    target = await storage.get_cluster(target_cluster_id)
    if not target:
        raise ValueError(f"Target cluster '{target_cluster_id}' not found")
    source = await storage.get_cluster(source_cluster_id)
    if not source:
        raise ValueError(f"Source cluster '{source_cluster_id}' not found")

    # Combine member IDs and texts uniquely
    target.question_ids = list(dict.fromkeys(target.question_ids + source.question_ids))
    target.member_texts = list(dict.fromkeys(target.member_texts + source.member_texts))

    if source.last_asked_at and (
        not target.last_asked_at or source.last_asked_at > target.last_asked_at
    ):
        target.last_asked_at = source.last_asked_at

    target.has_curated = target.has_curated or source.has_curated
    target.updated_at = datetime.now(UTC)

    await storage.save_cluster(target)
    await storage.delete_cluster(source_cluster_id)
    return target


async def rename_cluster(storage: Storage, cluster_id: str, new_canonical: str) -> QuestionCluster:
    """Renames the canonical phrasing of a cluster."""
    cluster = await storage.get_cluster(cluster_id)
    if not cluster:
        raise ValueError(f"Cluster '{cluster_id}' not found")

    cluster.canonical_text = new_canonical.strip()
    cluster.updated_at = datetime.now(UTC)
    await storage.save_cluster(cluster)
    return cluster


async def promote_cluster_to_curated(storage: Storage, cluster_id: str, admin_email: str) -> Topic:
    """Promotes a cluster's canonical text to a curated answer draft on its topic."""
    cluster = await storage.get_cluster(cluster_id)
    if not cluster:
        raise ValueError(f"Cluster '{cluster_id}' not found")

    topic = await storage.get_topic(cluster.topic_slug)
    if not topic:
        raise ValueError(f"Topic '{cluster.topic_slug}' not found")

    now = datetime.now(UTC)
    topic.curated_answer = cluster.canonical_text
    topic.curated_status = "draft"
    topic.updated_by = admin_email
    topic.updated_at = now

    cluster.has_curated = True
    cluster.updated_at = now

    await storage.save_topic(topic)
    await storage.save_cluster(cluster)
    return topic
