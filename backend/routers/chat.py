"""The one endpoint seekers actually use.

The order of operations below is specified in the AI Answer Engine Spec section 3.2
and locked by tests/test_pipeline_order.py. Read that test before reordering
anything here.
"""

from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime

from fastapi import APIRouter, HTTPException, status

from engine import EngineRequest, get_engine
from models import AskRequest, AskResponse, Citation, LikeResponse, Question
from models.enums import AnswerSource, ValidatorCode
from routers.deps import CurrentUser, StorageDep
from services import guards
from services.sessions import (
    SessionExpiredError,
    SessionNotFoundError,
    conversation_context,
    load_active_session,
    record_turn,
)
from services.users import record_activity
from storage import Storage

router = APIRouter(tags=["chat"])


@router.post("/ask", response_model=AskResponse)
async def ask(payload: AskRequest, user: CurrentUser, storage: StorageDep) -> AskResponse:
    started = time.perf_counter()

    try:
        text = guards.check_input_bounds(payload.text)
    except (guards.InputEmptyError, guards.InputTooLongError) as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    try:
        session = await load_active_session(storage, payload.session_id, user.uid)
    except SessionNotFoundError as exc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="session not found") from exc
    except SessionExpiredError as exc:
        raise HTTPException(status.HTTP_410_GONE, detail="session expired") from exc

    # Crisis first, before the rate limiter. Someone who has burned through
    # their hourly quota and then types something alarming still gets the
    # helpline. See F-30 and the note in services/guards.py.
    crisis = guards.check_crisis(text)
    if crisis.triggered:
        return await _persist_and_respond(
            storage,
            session_id=session.id,
            uid=user.uid,
            question_text=text,
            answer_text=crisis.response_text,
            answer_source=AnswerSource.crisis,
            started=started,
        )

    rate = await guards.check_rate_limit(storage, user.uid)
    if not rate.allowed:
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            detail=guards.rate_limit_message(rate),
            headers={"Retry-After": str(rate.retry_after_seconds)},
        )

    context = await conversation_context(storage, session.id)
    result = await get_engine().answer(
        EngineRequest(
            question_text=text,
            uid=user.uid,
            session_id=session.id,
            context=context,
        )
    )

    return await _persist_and_respond(
        storage,
        session_id=session.id,
        uid=user.uid,
        question_text=text,
        answer_text=result.answer_text,
        answer_source=result.answer_source,
        started=started,
        topic_slug=result.topic_slug,
        citations=list(result.citations),
        retrieved_chunk_ids=result.retrieved_chunk_ids,
        validator_failures=result.validator_failures,
        model=result.model,
        prompt_version=result.prompt_version,
    )


async def _persist_and_respond(
    storage: Storage,
    *,
    session_id: str,
    uid: str,
    question_text: str,
    answer_text: str,
    answer_source: AnswerSource,
    started: float,
    topic_slug: str | None = None,
    citations: list[Citation] | None = None,
    retrieved_chunk_ids: list[str] | None = None,
    validator_failures: list[ValidatorCode] | None = None,
    model: str | None = None,
    prompt_version: str | None = None,
) -> AskResponse:
    latency_ms = int((time.perf_counter() - started) * 1000)
    question = Question(
        id=f"q_{uuid.uuid4().hex[:16]}",
        session_id=session_id,
        uid=uid,
        question_text=question_text,
        answer_text=answer_text,
        answer_source=answer_source,
        topic_slug=topic_slug,
        citations=citations or [],
        retrieved_chunk_ids=retrieved_chunk_ids or [],
        validator_failures=validator_failures or [],
        is_refused=answer_source is AnswerSource.refusal,
        is_crisis=answer_source is AnswerSource.crisis,
        has_grounding=bool(citations),
        model=model,
        prompt_version=prompt_version,
        latency_ms=latency_ms,
        created_at=datetime.now(UTC),
    )

    await storage.save_question(question)
    await record_turn(storage, session_id)
    await record_activity(storage, uid)

    return AskResponse(
        question_id=question.id,
        answer_source=answer_source,
        answer_text=answer_text,
        citations=question.citations,
        topic_slug=topic_slug,
        likeable=answer_source.likeable,
        latency_ms=latency_ms,
    )


@router.post("/questions/{question_id}/like", response_model=LikeResponse)
async def like(
    question_id: str, user: CurrentUser, storage: StorageDep, liked: bool = True
) -> LikeResponse:
    question = await storage.get_question(question_id)
    if question is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="question not found")

    # F-33: refusals, crisis responses, and errors are not likeable. A thumbs-up
    # on a crisis message would corrupt the editorial signal the admin panel
    # reads from like counts.
    if not question.answer_source.likeable:
        raise HTTPException(status.HTTP_409_CONFLICT, detail="this answer type cannot be liked")

    count = await storage.set_like(user.uid, question_id, liked)
    return LikeResponse(question_id=question_id, liked=liked, like_count=count)
