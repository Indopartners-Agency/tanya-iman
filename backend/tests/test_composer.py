"""Tests for AnswerComposer and repair loop (PIP Task 5.4)."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from engine.composer import AnswerComposer
from engine.validators import ValidatorCode, ValidatorFailure
from models.schemas import ArticleChunk
from providers.llm import FakeLLM


def _make_chunk(chunk_id: str, title: str, text: str, url: str) -> ArticleChunk:
    return ArticleChunk(
        id=chunk_id,
        article_id="art_comp",
        site="isadanislam.org",
        url=url,
        title=title,
        chunk_index=0,
        text=text,
        created_at=datetime.now(UTC),
    )


@pytest.mark.asyncio
async def test_passages_rendered_without_urls():
    primary_llm = FakeLLM()
    composer = AnswerComposer(primary_llm=primary_llm)

    chunk = _make_chunk(
        "c1",
        "Kasih Sejati",
        "Isa Al-Masih mengajarkan kasih sejati yang memberikan pengampunan.",
        "https://isadanislam.org/kasih-sejati",
    )

    await composer.compose("Apa arti kasih?", [chunk])

    assert len(primary_llm.calls) == 1
    system_prompt, user_prompt = primary_llm.calls[0]

    # Crucial check: Passages in system prompt must not contain raw URLs (AI Spec 7.1)
    assert "https://" not in system_prompt
    assert "http://" not in system_prompt
    assert "[1] Kasih Sejati" in system_prompt


@pytest.mark.asyncio
async def test_composer_structured_output_parsed():
    primary_llm = FakeLLM()
    primary_llm.next_response = {
        "answer": (
            "Terima kasih atas pertanyaan Anda. Allah mengasihi setiap insan, dan Isa Al-Masih "
            "mengajarkan jalan kedamaian bagi siapa saja yang mencari pertolongan-Nya."
        ),
        "used_passages": [1],
        "quran_reference": None,
        "bible_references": ["Yohanes 3:16"],
        "confidence": "high",
    }
    composer = AnswerComposer(primary_llm=primary_llm)

    chunk = _make_chunk("c1", "Judul", "Teks kutipan", "https://isadanislam.org/judul")
    res = await composer.compose("Tentang kasih", [chunk])

    assert "Isa Al-Masih" in res.answer
    assert res.used_passages == [1]
    assert res.bible_references == ["Yohanes 3:16"]
    assert res.confidence == "high"


@pytest.mark.asyncio
async def test_composer_fallback_on_primary_failure():
    primary_llm = FakeLLM()

    # Define primary that raises an exception
    async def _failing_call(*args, **kwargs):
        raise RuntimeError("Primary model timeout")

    primary_llm.complete_json = _failing_call  # type: ignore

    fallback_llm = FakeLLM()
    fallback_llm.name = "fake:gemini-fallback"
    fallback_llm.next_response = {
        "answer": "Jawaban dari fallback model mengenai kasih Allah dan Isa Al-Masih.",
        "used_passages": [1],
        "confidence": "medium",
    }

    composer = AnswerComposer(primary_llm=primary_llm, fallback_llm=fallback_llm)
    chunk = _make_chunk("c1", "Judul", "Teks kutipan", "https://isadanislam.org/judul")

    res = await composer.compose("Tentang kasih", [chunk])
    assert res.model == "fake:gemini-fallback"
    assert "fallback model" in res.answer


@pytest.mark.asyncio
async def test_composer_repair_renders_prompt():
    primary_llm = FakeLLM()
    primary_llm.next_response = {
        "answer": "Jawaban yang sudah diperbaiki memenuhi semua syarat iman.",
        "used_passages": [1],
        "confidence": "high",
    }
    composer = AnswerComposer(primary_llm=primary_llm)

    chunk = _make_chunk("c1", "Judul", "Teks kutipan", "https://isadanislam.org/judul")
    failures = [
        ValidatorFailure(
            ValidatorCode.v1_too_short, "Panjang jawaban 20 kata; batas minimum adalah 25 kata."
        )
    ]

    res = await composer.repair("Jawaban pendek", failures, [chunk], "Pertanyaan")
    assert len(primary_llm.calls) == 1
    system_text, user_text = primary_llm.calls[0]

    assert "Panjang jawaban 20 kata" in system_text
    assert "Jawaban pendek" in system_text
    assert res.answer == "Jawaban yang sudah diperbaiki memenuhi semua syarat iman."
