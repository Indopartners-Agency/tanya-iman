"""Guard ordering.

AI Answer Engine Specification section 3.2 fixes the order as:

    input bounds -> session -> crisis -> rate limit -> engine

Each assertion below fails for a different reordering, which is the point: the
order is a safety property, not an implementation detail, and a future refactor
that "tidies up" the router must fail here rather than in production.
"""

import pytest

from config import get_settings
from engine import reset_engine
from models import EngineResult
from models.enums import AnswerSource

pytestmark = pytest.mark.asyncio


class RecordingEngine:
    name = "recording"

    def __init__(self) -> None:
        self.called = 0

    async def answer(self, request) -> EngineResult:
        self.called += 1
        return EngineResult(
            answer_source=AnswerSource.generated,
            answer_text="jawaban uji coba",
        )


@pytest.fixture
def engine() -> RecordingEngine:
    recorder = RecordingEngine()
    reset_engine(recorder)
    yield recorder
    reset_engine(None)


async def test_crisis_never_reaches_the_engine(client, auth_headers, session_id, engine):
    """Sending a crisis message to an LLM is both a cost and a safety problem:
    the reply would be unscripted at the moment scripting matters most."""
    await client.post(
        "/ask",
        json={"session_id": session_id, "text": "saya ingin mati"},
        headers=auth_headers,
    )
    assert engine.called == 0


async def test_rate_limited_request_never_reaches_the_engine(
    client, auth_headers, session_id, engine
):
    limit = get_settings().rate_limit_per_hour
    for _ in range(limit):
        await client.post(
            "/ask",
            json={"session_id": session_id, "text": "halo"},
            headers=auth_headers,
        )
    calls_at_limit = engine.called

    await client.post("/ask", json={"session_id": session_id, "text": "halo"}, headers=auth_headers)
    assert engine.called == calls_at_limit


async def test_oversized_input_never_reaches_the_engine(client, auth_headers, session_id, engine):
    """Length is checked before anything bills by the token."""
    await client.post(
        "/ask",
        json={
            "session_id": session_id,
            "text": "a" * (get_settings().max_question_chars + 1),
        },
        headers=auth_headers,
    )
    assert engine.called == 0


async def test_invalid_session_never_reaches_the_engine(client, auth_headers, engine):
    await client.post(
        "/ask",
        json={"session_id": "s_does_not_exist", "text": "halo"},
        headers=auth_headers,
    )
    assert engine.called == 0


async def test_a_rate_limited_request_still_consumes_quota(client, auth_headers, session_id):
    """Blocked requests count. Otherwise a client that ignores 429 gets free
    retries forever and the limit means nothing."""
    from services import guards
    from storage import get_storage

    storage = get_storage()
    limit = get_settings().rate_limit_per_hour
    for _ in range(limit + 3):
        await guards.check_rate_limit(storage, "u_quota")

    result = await guards.check_rate_limit(storage, "u_quota")
    assert result.count == limit + 4
