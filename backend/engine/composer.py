"""Answer composer and repair loop (F-11 through F-15, F-28).

Generates empathetic Indonesian theological answers based exclusively on
retrieved article passages. Passages are supplied indexed and strictly
without URLs so the model can never emit or hallucinate links.

Specification: AI Spec section 7, section 9.2, section 9.3.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

from config import get_settings
from config.loader import prompt
from engine.validators import ValidatorFailure, format_failures_for_repair
from models.schemas import ArticleChunk, Question
from providers.llm import LLMProvider, get_llm

logger = logging.getLogger(__name__)


@dataclass
class ComposerResult:
    answer: str
    used_passages: list[int]
    quran_reference: str | None = None
    bible_references: list[str] = field(default_factory=list)
    confidence: str = "medium"
    model: str = ""
    prompt_version: str = ""


class AnswerComposer:
    """Composes theological answers from retrieved passages."""

    def __init__(
        self,
        primary_llm: LLMProvider | None = None,
        fallback_llm: LLMProvider | None = None,
        timeout: float = 7.0,
    ) -> None:
        self.primary_llm = primary_llm
        self.fallback_llm = fallback_llm
        self.timeout = timeout

    def _render_passages(self, chunks: list[ArticleChunk]) -> str:
        """Render passages indexed without raw URLs (AI Spec 7.1)."""
        rendered = []
        for i, c in enumerate(chunks, start=1):
            rendered.append(f"[{i}] {c.title}\n{c.text.strip()}")
        return "\n\n".join(rendered)

    def _render_recent_turns(self, context: list[Question] | None) -> str:
        if not context:
            return "(Tidak ada percakapan sebelumnya)"
        turns = []
        for q in context[-2:]:
            turns.append(f"User: {q.question_text}")
            if q.answer_text:
                turns.append(f"Tanya Iman: {q.answer_text[:150]}...")
        return "\n".join(turns)

    def _render_composer_system(
        self, chunks: list[ArticleChunk], question: str, context: list[Question] | None
    ) -> str:
        base = prompt("composer")
        passages_text = self._render_passages(chunks)
        turns_text = self._render_recent_turns(context)
        return (
            base.replace("{passages}", passages_text)
            .replace("{question}", question.strip())
            .replace("{recent_turns}", turns_text)
        )

    async def _call_llm(self, system: str, user: str) -> tuple[dict[str, Any], str]:
        primary = self.primary_llm or get_llm()

        try:
            raw = await asyncio.wait_for(
                primary.complete_json(system, user, max_tokens=700, temperature=0.4),
                timeout=self.timeout,
            )
            return raw, primary.name
        except Exception as err:
            logger.warning(
                "Primary LLM (%s) failed or timed out (%s), trying fallback",
                primary.name,
                err,
            )
            fallback = self.fallback_llm or get_llm(fallback=True)
            raw = await asyncio.wait_for(
                fallback.complete_json(system, user, max_tokens=700, temperature=0.4),
                timeout=self.timeout,
            )
            return raw, fallback.name

    async def compose(
        self,
        question: str,
        chunks: list[ArticleChunk],
        context: list[Question] | None = None,
    ) -> ComposerResult:
        settings = get_settings()
        system = self._render_composer_system(chunks, question, context)
        user = (
            f"Silakan jawab pertanyaan berikut berdasarkan kutipan yang diberikan: "
            f"'{question.strip()}'"
        )

        raw, model_name = await self._call_llm(system, user)
        return self._parse_result(raw, model_name, settings.prompt_version)

    async def repair(
        self,
        previous_answer: str,
        failures: list[ValidatorFailure],
        chunks: list[ArticleChunk],
        question: str,
    ) -> ComposerResult:
        """Run single repair attempt on answer draft (AI Spec 8.6, 9.3)."""
        settings = get_settings()
        failure_list_str = format_failures_for_repair(failures)

        repair_tmpl = prompt("repair")
        repair_system = repair_tmpl.replace("{failure_list}", failure_list_str).replace(
            "{previous_answer}", previous_answer
        )

        user_prompt = (
            f"Kutipan bahan yang tersedia:\n{self._render_passages(chunks)}\n\n"
            f"Pertanyaan pengguna: '{question.strip()}'\n\n"
            "Perbaiki jawaban sebelumnya agar lulus semua validator."
        )

        raw, model_name = await self._call_llm(repair_system, user_prompt)
        return self._parse_result(raw, model_name, settings.prompt_version)

    def _parse_result(
        self, raw: dict[str, Any], model_name: str, prompt_version: str
    ) -> ComposerResult:
        answer = str(raw.get("answer", "")).strip()
        used_raw = raw.get("used_passages", [])
        used_passages = [int(x) for x in used_raw if isinstance(x, (int, str)) and str(x).isdigit()]
        quran_ref = raw.get("quran_reference")
        bible_refs = raw.get("bible_references") or []
        if isinstance(bible_refs, str):
            bible_refs = [bible_refs]

        return ComposerResult(
            answer=answer,
            used_passages=used_passages,
            quran_reference=str(quran_ref) if quran_ref else None,
            bible_references=[str(b) for b in bible_refs],
            confidence=str(raw.get("confidence", "medium")),
            model=model_name,
            prompt_version=prompt_version,
        )
