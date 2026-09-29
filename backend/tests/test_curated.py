"""Tests for CuratedResolver (PIP Task 5.3)."""

from __future__ import annotations

import pytest

from engine.curated import CuratedResolver
from models.schemas import Citation, Topic
from storage.memory import MemoryStorage


@pytest.mark.asyncio
async def test_published_curated_answer_returned():
    storage = MemoryStorage()
    resolver = CuratedResolver(storage=storage)

    citation = Citation(
        title="Jalan Menuju Keselamatan",
        url="https://isadanislam.org/jalan-keselamatan",
        site="isadanislam.org",
    )

    topic = Topic(
        slug="keselamatan-dan-rahmat",
        name_id="Keselamatan dan Rahmat",
        name_en="Salvation and Grace",
        curated_answer="Keselamatan adalah anugerah Allah yang cuma-cuma melalui kasih-Nya.",
        curated_citations=[citation],
        curated_status="published",
    )
    await storage.save_topic(topic)

    res = await resolver.resolve("keselamatan-dan-rahmat")
    assert res.matched is True
    assert res.answer_text == topic.curated_answer
    assert len(res.citations) == 1
    assert res.citations[0].url == citation.url
    assert res.topic_slug == "keselamatan-dan-rahmat"


@pytest.mark.asyncio
async def test_draft_curated_answer_ignored():
    storage = MemoryStorage()
    resolver = CuratedResolver(storage=storage)

    topic = Topic(
        slug="doa-dan-ibadah",
        name_id="Doa dan Ibadah",
        name_en="Prayer and Worship",
        curated_answer="Ini masih draf jawaban kurasi yang belum disetujui.",
        curated_citations=[],
        curated_status="draft",
    )
    await storage.save_topic(topic)

    res = await resolver.resolve("doa-dan-ibadah")
    assert res.matched is False
    assert res.answer_text == ""


@pytest.mark.asyncio
async def test_unknown_or_empty_topic_returns_unmatched():
    storage = MemoryStorage()
    resolver = CuratedResolver(storage=storage)

    res1 = await resolver.resolve("topik-tidak-ada")
    assert res1.matched is False

    res2 = await resolver.resolve(None)
    assert res2.matched is False

    res3 = await resolver.resolve("lainnya")
    assert res3.matched is False
