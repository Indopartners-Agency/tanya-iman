"""Retriever for grounded answer composition.

PIP Task 4.4 & AI Spec §7-§8:
- Query-time vector search over article_chunks.
- Redundant query-time site filter against approved_domains().
- top_k=8 retrieved, similarity threshold applied (default: 0.72 from system_config).
- Max 2 chunks per article.
- Top 4 surviving chunks passed to composer.
- Fewer than 2 surviving chunks emits has_grounding=False (triggers no-grounding path F-29).
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from config.loader import approved_domains
from ingestion.embedder import Embedder, get_embedder
from models import ArticleChunk, Citation
from storage import Storage

logger = logging.getLogger("engine.retriever")

DEFAULT_SIMILARITY_THRESHOLD = 0.72
TOP_K_RETRIEVED = 8
MAX_RETURNED_CHUNKS = 4
MAX_CHUNKS_PER_ARTICLE = 2
MIN_SURVIVING_CHUNKS = 2


@dataclass(frozen=True)
class RetrievalResult:
    chunks: list[ArticleChunk]
    citations: list[Citation]
    has_grounding: bool
    similarity_scores: list[float]


class VectorRetriever:
    """Retrieves grounded theological passages from approved ministry corpus."""

    def __init__(
        self,
        storage: Storage,
        embedder: Embedder | None = None,
        default_threshold: float = DEFAULT_SIMILARITY_THRESHOLD,
    ) -> None:
        self.storage = storage
        self.embedder = embedder or get_embedder()
        self.default_threshold = default_threshold

    async def get_threshold(self) -> float:
        """Fetch current similarity threshold from system_config with fallback."""
        try:
            cfg = await self.storage.get_system_config("similarity_threshold")
            if cfg and cfg.value:
                return float(cfg.value)
        except Exception as err:
            logger.debug("Failed reading similarity_threshold config: %s", err)
        return self.default_threshold

    def build_query_text(self, question: str, recent_turns: list[str] | None = None) -> str:
        """Compose query text using current question and last 2 conversation turns."""
        parts: list[str] = []
        if recent_turns:
            # At most 2 recent turns
            for turn in recent_turns[-2:]:
                parts.append(turn.strip())
        parts.append(question.strip())
        return " ".join(parts).strip()

    async def retrieve(
        self,
        question: str,
        recent_turns: list[str] | None = None,
        override_threshold: float | None = None,
    ) -> RetrievalResult:
        """Retrieve and rank top chunks for a question."""
        threshold = (
            override_threshold if override_threshold is not None else await self.get_threshold()
        )
        query_text = self.build_query_text(question, recent_turns)
        query_vector = await self.embedder.embed_query(query_text)

        # 1. Gate 1: Strict query-time allowlist against 5 approved domains
        valid_sites = approved_domains()

        # 2. Retrieve top_k=8 nearest candidates from storage
        candidates = await self.storage.find_nearest_chunks(
            query_vector=query_vector,
            limit=TOP_K_RETRIEVED,
            site_allowlist=valid_sites,
            min_similarity=threshold,
        )

        # 3. Apply per-article cap (max 2 chunks per article)
        surviving_chunks: list[ArticleChunk] = []
        surviving_scores: list[float] = []
        article_counts: dict[str, int] = {}

        for chunk, score in candidates:
            # Redundant check: ensure site is on allowlist
            if chunk.site not in valid_sites:
                logger.warning("Rejected off-allowlist chunk in retriever: %s", chunk.site)
                continue

            current_count = article_counts.get(chunk.article_id, 0)
            if current_count >= MAX_CHUNKS_PER_ARTICLE:
                continue

            article_counts[chunk.article_id] = current_count + 1
            surviving_chunks.append(chunk)
            surviving_scores.append(score)

            if len(surviving_chunks) >= MAX_RETURNED_CHUNKS:
                break

        # 4. Evaluate minimum grounding signal
        has_grounding = len(surviving_chunks) >= MIN_SURVIVING_CHUNKS

        # 5. Extract distinct citations from surviving chunks
        citations: list[Citation] = []
        seen_urls: set[str] = set()
        for chunk in surviving_chunks:
            if chunk.url not in seen_urls:
                seen_urls.add(chunk.url)
                citations.append(
                    Citation(
                        title=chunk.title,
                        url=chunk.url,
                        site=chunk.site,
                        article_id=chunk.article_id,
                    )
                )

        logger.info(
            "Retrieved %d chunks (threshold=%.2f, has_grounding=%s) for question: %s",
            len(surviving_chunks),
            threshold,
            has_grounding,
            question[:60],
        )

        return RetrievalResult(
            chunks=surviving_chunks,
            citations=citations,
            has_grounding=has_grounding,
            similarity_scores=surviving_scores,
        )
