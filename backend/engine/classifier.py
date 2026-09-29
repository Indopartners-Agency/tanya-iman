"""Relevance classifier and topic resolver (F-9, F-10, F-21).

Performs a single structured LLM call that determines:
1. Relevance: 'theology', 'emotional_only', 'irrelevant', or 'ambiguous'
2. Topic: One of the canonical topics (or 'lainnya')
3. Prompt injection attempt detection

Specification: AI Spec section 4, section 5, section 9.1.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from config.loader import prompt, topics
from models.enums import Relevance
from models.schemas import Question
from providers.llm import LLMProvider, get_llm

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ClassificationResult:
    relevance: Relevance
    topic_slug: str | None = None
    is_injection_attempt: bool = False
    confidence: str = "high"


class RelevanceClassifier:
    """Classifies user inquiry relevance and resolves canonical topic."""

    def __init__(self, llm: LLMProvider | None = None) -> None:
        self.llm = llm

    def _render_system_prompt(self) -> str:
        topic_lines = [f"- {t['slug']}: {t['name_id']}" for t in topics()]
        topic_list_str = "\n".join(topic_lines)
        base_prompt = prompt("classifier")
        return base_prompt.replace("{topic_list}", topic_list_str)

    def _render_user_prompt(self, question_text: str, context: list[Question] | None) -> str:
        turns = []
        if context:
            for q in context[-2:]:
                turns.append(f"User: {q.question_text}")
                if q.answer_text:
                    turns.append(f"Tanya Iman: {q.answer_text[:150]}...")
        context_str = "\n".join(turns) if turns else "(Tidak ada percakapan sebelumnya)"

        return f"PERTANYAAN:\n{question_text.strip()}\n\nKONTEKS PERCAKAPAN:\n{context_str}"

    async def classify(
        self, question_text: str, context: list[Question] | None = None
    ) -> ClassificationResult:
        llm = self.llm or get_llm()
        system_text = self._render_system_prompt()
        user_text = self._render_user_prompt(question_text, context)

        try:
            raw: dict[str, Any] = await llm.complete_json(
                system_text, user_text, max_tokens=200, temperature=0.0
            )
        except Exception as err:
            logger.warning("Classifier LLM error, falling back to ambiguous: %s", err)
            return ClassificationResult(
                relevance=Relevance.ambiguous,
                topic_slug="lainnya",
                confidence="low",
            )

        # Parse relevance
        rel_str = str(raw.get("relevance", "")).strip().lower()
        if rel_str == "theology" or rel_str == "relevant":
            relevance = Relevance.theology
        elif rel_str == "emotional_only":
            relevance = Relevance.emotional_only
        elif rel_str == "irrelevant":
            relevance = Relevance.irrelevant
        elif rel_str == "ambiguous":
            relevance = Relevance.ambiguous
        else:
            logger.warning("Unknown relevance value '%s', falling back to ambiguous", rel_str)
            relevance = Relevance.ambiguous

        # Parse injection attempt
        injection = bool(raw.get("injection_attempt", False))
        if injection:
            # AI Spec 4.3: injection attempts are classified irrelevant
            relevance = Relevance.irrelevant

        # Parse topic slug
        valid_slugs = {t["slug"] for t in topics()}
        raw_slug = raw.get("topic_slug")
        slug = str(raw_slug).strip().lower() if raw_slug else None
        if (slug and slug not in valid_slugs and slug != "lainnya") or (
            not slug and relevance in (Relevance.theology, Relevance.ambiguous)
        ):
            slug = "lainnya"

        return ClassificationResult(
            relevance=relevance,
            topic_slug=slug,
            is_injection_attempt=injection,
            confidence=str(raw.get("confidence", "high")),
        )
