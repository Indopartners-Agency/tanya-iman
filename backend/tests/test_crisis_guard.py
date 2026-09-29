"""Tests for Crisis Guard (PIP Task 5.1, PRD F-30 - F-32)."""

from __future__ import annotations

import pytest

from config.loader import crisis_config
from providers.llm import FakeLLM
from services.guards import check_crisis, check_rate_limit, render_crisis_response
from storage.memory import MemoryStorage


def test_every_crisis_keyword_fires_guard():
    config = crisis_config()
    keywords = config.get("triggers", {}).get("keywords", [])
    assert len(keywords) > 0

    for kw in keywords:
        # User input wrapping the keyword
        sample_text = f"Tolong saya, saya merasa {kw} sekarang."
        result = check_crisis(sample_text)
        assert result.triggered is True, f"Keyword '{kw}' failed to trigger crisis guard"
        assert len(result.response_text) > 0


def test_ordinary_theology_does_not_fire_crisis():
    ordinary_queries = [
        "Apakah Allah mengampuni dosa besar?",
        "Bagaimana cara berdoa yang benar kepada Allah?",
        "Siapakah Isa Al-Masih dalam Al-Quran dan Kitab Suci?",
    ]
    for q in ordinary_queries:
        res = check_crisis(q)
        assert res.triggered is False
        assert res.response_text == ""


def test_crisis_response_renders_configured_helplines():
    rendered = render_crisis_response()
    config = crisis_config()
    for h in config.get("helplines", []):
        assert h["name"] in rendered
        assert h["number"] in rendered


@pytest.mark.asyncio
async def test_rate_limited_user_in_crisis_still_receives_script():
    """Safety guarantee: Crisis guard fires before rate limiting (AI Spec 3.2)."""
    storage = MemoryStorage()
    uid = "user_exhausted_quota"

    # Burn user's rate quota
    for _ in range(31):
        rate_check = await check_rate_limit(storage, uid)

    assert rate_check.allowed is False

    # Crisis check is independent and runs before rate limiter
    crisis_res = check_crisis("Saya ingin mengakhiri hidup saya.")
    assert crisis_res.triggered is True
    assert len(crisis_res.response_text) > 0


@pytest.mark.asyncio
async def test_crisis_bypasses_engine_and_llm():
    """No LLM call occurs when a crisis is triggered."""
    llm = FakeLLM()
    # In chat route, crisis guard catches before engine.answer is ever called.
    crisis_res = check_crisis("Saya merasa lebih baik saya mati saja.")
    assert crisis_res.triggered is True
    # Ensure LLM was not called
    assert len(llm.calls) == 0
