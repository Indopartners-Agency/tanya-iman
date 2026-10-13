"""Backfill similar-question clusters for existing Firestore questions.

Uses Vertex AI Multilingual Embedder (text-multilingual-embedding-002) and
assign_to_cluster() to group existing seeker inquiries into semantic clusters.
"""

from __future__ import annotations

import asyncio
import logging
from collections import Counter
from datetime import UTC, datetime

from google.oauth2.credentials import Credentials

from ingestion.embedder import VertexAIEmbedder, _get_gcloud_token
from models import Question
from services.clustering import assign_to_cluster
from storage.firestore import FirestoreStorage

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("backfill_clusters")


async def main() -> None:
    project_id = "project-philip-501910"
    db_name = "tanya-iman"

    token = _get_gcloud_token()
    creds = Credentials(token)

    logger.info("Connecting to Firestore project=%s database=%s...", project_id, db_name)
    storage = FirestoreStorage(project=project_id, database=db_name, credentials=creds)
    embedder = VertexAIEmbedder(project_id=project_id)

    # 1. Fetch all questions from Firestore
    questions_coll = storage._db.collection("questions")
    docs = [d async for d in questions_coll.stream()]
    logger.info("Found %d total question documents in Firestore", len(docs))

    questions: list[Question] = []
    for d in docs:
        data = d.to_dict()
        try:
            q = Question(**data)
            # Exclude crisis and empty questions from clusters
            if not q.is_crisis and q.question_text and q.question_text.strip():
                questions.append(q)
        except Exception as err:
            logger.warning("Failed parsing question %s: %s", d.id, err)

    logger.info("Clustering %d eligible inquiries...", len(questions))

    # Sort chronologically so older questions establish canonical topics
    epoch = datetime(1970, 1, 1, tzinfo=UTC)
    questions.sort(key=lambda q: q.created_at or epoch)

    # 2. Assign each question to a cluster
    cluster_counts: Counter[str] = Counter()
    for idx, q in enumerate(questions, start=1):
        try:
            logger.info(
                "[%d/%d] Clustering question '%s' (topic=%s)...",
                idx,
                len(questions),
                q.question_text[:40],
                q.topic_slug,
            )
            c = await assign_to_cluster(storage, q, embedder=embedder, threshold=0.80)
            cluster_counts[c.id] += 1
        except Exception as err:
            logger.error("Error clustering question %s: %s", q.id, err)

    # 3. Report cluster statistics
    all_clusters = await storage.list_clusters()
    logger.info("=== BACKFILL SUMMARY ===")
    logger.info("Total questions processed: %d", len(questions))
    logger.info("Total clusters in Firestore: %d", len(all_clusters))

    logger.info("\nTop 10 Clusters by Member Count:")
    for c in all_clusters[:10]:
        logger.info(
            "- [%s] (%d members, topic=%s): %s",
            c.id,
            len(c.question_ids),
            c.topic_slug,
            c.canonical_text,
        )


if __name__ == "__main__":
    asyncio.run(main())
