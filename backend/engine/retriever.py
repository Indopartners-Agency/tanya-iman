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
import re
from dataclasses import dataclass
from typing import Any

from config.loader import approved_domains
from ingestion.crawler import is_non_article_page
from ingestion.embedder import Embedder, get_embedder
from models import ArticleChunk, Citation
from storage import Storage

logger = logging.getLogger("engine.retriever")

DEFAULT_SIMILARITY_THRESHOLD = 0.72
TOP_K_RETRIEVED = 8
MAX_RETURNED_CHUNKS = 4
MAX_CHUNKS_PER_ARTICLE = 2
MIN_SURVIVING_CHUNKS = 2

_FOLLOWUP_PREFIX_RE = re.compile(
    r"^\s*(?:lalu|terus|kemudian|jadi|lantas|kalau\s+begitu|berarti|nah)\b",
    re.IGNORECASE,
)

_ANAPHORA_RE = re.compile(
    r"\b(?:hal\s+itu|hal\s+tersebut|ajaran\s+itu|ayat\s+itu|jaminannya|maksudnya|buktinya|alasannya|contohnya|beliau|dia|mereka|tadi|tersebut|begitu|demikian)\b",
    re.IGNORECASE,
)

_THEOLOGY_SUBJECT_RE = re.compile(
    r"\b(?:isa|al-masih|allah|(?:ke)?tuhan(?:an)?|yesus|alkitab|injil|taurat|zabur|al-quran|quran|(?:ber)?puasa|ramadan|ramadhan|(?:ber)?doa|(?:ber)?ibadah|sholat|salat|(?:di)?salib(?:kan)?|penyaliban|dosa|surga|neraka|trinitas|tritunggal|keselamatan|pengampunan|muhammad|nabi|rasul|kristen|nasrani|islam|muslim|pernikahan|wanita|kematian|kebangkitan|kiamat|akhirat|(?:meny)?embah)\b",
    re.IGNORECASE,
)


def is_followup_question(question: str) -> bool:
    """Return True if the question is a context-dependent follow-up."""
    q = (question or "").strip()
    if not q:
        return False
    if _FOLLOWUP_PREFIX_RE.search(q):
        return True
    if _ANAPHORA_RE.search(q) and not _THEOLOGY_SUBJECT_RE.search(q):
        return True
    words = q.split()
    return bool(len(words) <= 3 and not _THEOLOGY_SUBJECT_RE.search(q))


def extract_relevant_context_turns(
    question: str,
    context: list[Any] | None,
    topic_slug: str | None = None,
) -> list[str]:
    """Return recent question texts only for follow-ups on the same topic."""
    if not context or not is_followup_question(question):
        return []

    relevant: list[str] = []
    for q in context[-2:]:
        q_text = getattr(q, "question_text", str(q)).strip()
        if not q_text:
            continue
        q_topic = getattr(q, "topic_slug", None)
        if (
            topic_slug
            and topic_slug != "lainnya"
            and q_topic
            and q_topic != "lainnya"
            and q_topic != topic_slug
        ):
            continue
        relevant.append(q_text)
    return relevant


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

    async def _search_and_filter(
        self,
        query_text: str,
        valid_sites: frozenset[str],
        threshold: float,
    ) -> tuple[list[ArticleChunk], list[float]]:
        query_vector = await self.embedder.embed_query(query_text)
        candidates = await self.storage.find_nearest_chunks(
            query_vector=query_vector,
            limit=TOP_K_RETRIEVED + 6,
            site_allowlist=valid_sites,
            min_similarity=threshold,
        )

        surviving_chunks: list[ArticleChunk] = []
        surviving_scores: list[float] = []
        article_counts: dict[str, int] = {}

        for chunk, score in candidates:
            if chunk.site not in valid_sites:
                logger.warning("Rejected off-allowlist chunk in retriever: %s", chunk.site)
                continue

            if is_non_article_page(chunk.url, chunk.title):
                logger.debug("Skipped non-article index/category chunk: %s", chunk.url)
                continue

            current_count = article_counts.get(chunk.article_id, 0)
            if current_count >= MAX_CHUNKS_PER_ARTICLE:
                continue

            article_counts[chunk.article_id] = current_count + 1
            surviving_chunks.append(chunk)
            surviving_scores.append(score)

            if len(surviving_chunks) >= MAX_RETURNED_CHUNKS:
                break

        return surviving_chunks, surviving_scores

    async def retrieve(
        self,
        question: str,
        recent_turns: list[str] | None = None,
        override_threshold: float | None = None,
        context: list[Any] | None = None,
        topic_slug: str | None = None,
    ) -> RetrievalResult:
        """Retrieve and rank top chunks for a question."""
        threshold = (
            override_threshold if override_threshold is not None else await self.get_threshold()
        )
        if context and recent_turns is None:
            recent_turns = extract_relevant_context_turns(
                question, context, topic_slug=topic_slug
            )

        query_text = self.build_query_text(question, recent_turns)

        # 1. Gate 1: Strict query-time allowlist against 5 approved domains
        valid_sites = approved_domains()

        # 2. Retrieve top candidates and apply per-article cap
        surviving_chunks, surviving_scores = await self._search_and_filter(
            query_text, valid_sites, threshold
        )

        # Fallback: if recent_turns diluted the vector query and prevented grounding,
        # retry with the standalone question alone.
        if recent_turns and len(surviving_chunks) < MIN_SURVIVING_CHUNKS:
            standalone_chunks, standalone_scores = await self._search_and_filter(
                question.strip(), valid_sites, threshold
            )
            if len(standalone_chunks) > len(surviving_chunks):
                surviving_chunks = standalone_chunks
                surviving_scores = standalone_scores

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
