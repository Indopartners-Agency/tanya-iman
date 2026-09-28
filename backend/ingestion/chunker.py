"""Article chunker with token bounds and forbidden-term screening.

PIP Task 4.2 & AI Spec §8.2 (OI-1):
- ~400 token windows with ~80 token overlap.
- Splits on heading and paragraph boundaries; never spans two articles.
- Denormalises article_id, site, url, and title onto every chunk.
- Scans for V2 forbidden terms ("Tuhan", "TUHAN", "Yesus", "Jesus") and
  flags matching chunks into a review collection (FlaggedChunk).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import UTC, datetime

from models import Article, ArticleChunk, FlaggedChunk
from models.enums import ChunkDecision

# Forbidden terms per AI Spec §8.2 / V2 compliance rule
FORBIDDEN_TERMS = ("Tuhan", "TUHAN", "Yesus", "Jesus")
FORBIDDEN_REGEX = re.compile(r"\b(" + "|".join(FORBIDDEN_TERMS) + r")\b")

# Token bounds (estimated at ~1.33 tokens per word, or 4 chars per token)
TARGET_TOKENS = 400
OVERLAP_TOKENS = 80
MIN_CHUNK_TOKENS = 50


def estimate_tokens(text: str) -> int:
    """Estimate token count from text using word & character heuristics."""
    words = text.split()
    if not words:
        return 0
    # Average 1.3 tokens per word in Indonesian text
    return max(1, int(len(words) * 1.3))


def find_forbidden_terms(text: str) -> list[str]:
    """Return all distinct forbidden terms matched in text."""
    matches = FORBIDDEN_REGEX.findall(text)
    return sorted(set(matches))


@dataclass(frozen=True)
class ChunkingResult:
    chunks: list[ArticleChunk]
    flagged: list[FlaggedChunk]


class ArticleChunker:
    """Splits article content into overlapping token-bounded chunks and screens for V2 terms."""

    def __init__(
        self,
        target_tokens: int = TARGET_TOKENS,
        overlap_tokens: int = OVERLAP_TOKENS,
        min_tokens: int = MIN_CHUNK_TOKENS,
    ) -> None:
        self.target_tokens = target_tokens
        self.overlap_tokens = overlap_tokens
        self.min_tokens = min_tokens

    def chunk_article(
        self, article: Article, text: str, now: datetime | None = None
    ) -> ChunkingResult:
        """Chunk a single article. A chunk never spans across two articles."""
        current_time = now or datetime.now(UTC)
        paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

        if not paragraphs:
            return ChunkingResult(chunks=[], flagged=[])

        # Step 1: Group paragraphs into target-bounded sections
        raw_sections: list[str] = []
        current_section: list[str] = []
        current_token_count = 0

        for para in paragraphs:
            para_tokens = estimate_tokens(para)
            if current_token_count + para_tokens > self.target_tokens and current_section:
                raw_sections.append("\n\n".join(current_section))
                # Build overlap from recent paragraphs
                overlap_paras: list[str] = []
                overlap_count = 0
                for p in reversed(current_section):
                    pt = estimate_tokens(p)
                    if overlap_count + pt <= self.overlap_tokens:
                        overlap_paras.insert(0, p)
                        overlap_count += pt
                    else:
                        break
                current_section = overlap_paras
                current_token_count = overlap_count

            current_section.append(para)
            current_token_count += para_tokens

        if current_section:
            raw_sections.append("\n\n".join(current_section))

        chunks: list[ArticleChunk] = []
        flagged: list[FlaggedChunk] = []

        for idx, sec_text in enumerate(raw_sections):
            tok_count = estimate_tokens(sec_text)
            matched = find_forbidden_terms(sec_text)
            has_forbidden = len(matched) > 0

            chunk_id = f"{article.id}#{idx}"
            chunk = ArticleChunk(
                id=chunk_id,
                article_id=article.id,
                site=article.site,
                url=article.url,
                title=article.title,
                chunk_index=idx,
                text=sec_text,
                token_count=tok_count,
                has_forbidden_term=has_forbidden,
                is_retrievable=True,
                created_at=current_time,
            )
            chunks.append(chunk)

            if has_forbidden:
                flag = FlaggedChunk(
                    id=f"flg_{article.id}_{idx}",
                    chunk_id=chunk_id,
                    article_id=article.id,
                    site=article.site,
                    url=article.url,
                    title=article.title,
                    matched_terms=matched,
                    text=sec_text,
                    decision=ChunkDecision.pending,
                    created_at=current_time,
                )
                flagged.append(flag)

        return ChunkingResult(chunks=chunks, flagged=flagged)
