"""Curated answer override (F-23).

When a topic has a published curated answer authored by the editorial team,
it is returned verbatim with its configured citations. Draft curated answers
are never served.

Specification: AI Spec section 11.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from models.schemas import Citation
from storage.base import Storage


@dataclass(frozen=True)
class CuratedResult:
    matched: bool
    answer_text: str = ""
    citations: list[Citation] = field(default_factory=list)
    topic_slug: str | None = None


class CuratedResolver:
    """Checks whether a canonical published answer exists for a topic."""

    def __init__(self, storage: Storage) -> None:
        self.storage = storage

    async def resolve(self, topic_slug: str | None) -> CuratedResult:
        if not topic_slug or topic_slug == "lainnya":
            return CuratedResult(matched=False)

        topic = await self.storage.get_topic(topic_slug)
        if topic is None:
            return CuratedResult(matched=False)

        # Only published curated answers are served
        if topic.curated_status == "published" and topic.curated_answer:
            return CuratedResult(
                matched=True,
                answer_text=topic.curated_answer,
                citations=list(topic.curated_citations),
                topic_slug=topic.slug,
            )

        return CuratedResult(matched=False)
