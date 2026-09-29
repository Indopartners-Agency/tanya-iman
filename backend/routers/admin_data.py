"""Admin data API endpoints (Wave 7 / Phase 6).

Serves live analytics, question streams, topic details, curated answer
editing with validation, content gaps, and system configuration.
"""

from __future__ import annotations

import logging
from datetime import UTC, datetime
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from config.loader import topics as get_canonical_topics
from engine.validators import ComplianceValidator
from models import AdminUser, Citation, SystemConfig
from models.enums import AdminRole, ValidatorCode
from routers.admin_auth import require_admin
from routers.deps import StorageDep

logger = logging.getLogger(__name__)

router = APIRouter(tags=["admin_data"])

AdminDep = Annotated[AdminUser, Depends(require_admin())]
EditorDep = Annotated[AdminUser, Depends(require_admin(AdminRole.editor))]
SuperAdminDep = Annotated[AdminUser, Depends(require_admin(AdminRole.super_admin))]


# --- Schemas -----------------------------------------------------------------


class TopicItem(BaseModel):
    slug: str
    label: str
    questions: int = 0
    likes: int = 0
    curated: str = "none"  # "none" | "draft" | "published"
    curated_by: str | None = None
    curated_at: str | None = None
    curated_answer: str | None = None
    curated_citations: list[Citation] = Field(default_factory=list)
    refusal_rate: float = 0.0


class DashboardResponse(BaseModel):
    total_questions: int
    total_likes: int
    active_topics: int
    curated_coverage: float
    recent_refusals: int
    recent_crises: int
    ungrounded_gaps: int
    review_items: int
    top_topics: list[TopicItem]


class QuestionListItem(BaseModel):
    id: str
    asked_at: str
    question: str
    topic_slug: str
    topic_label: str
    result: str
    likes: int = 0
    channel: str = "web"
    flags: list[str] = Field(default_factory=list)


class QuestionDetailResponse(BaseModel):
    id: str
    asked_at: str
    question: str
    answer: str
    topic_slug: str
    topic_label: str
    result: str
    likes: int = 0
    citations: list[Citation] = Field(default_factory=list)
    retrieved_chunk_ids: list[str] = Field(default_factory=list)
    validator_failures: list[str] = Field(default_factory=list)
    model: str | None = None
    prompt_version: str | None = None
    latency_ms: int = 0


class UpdateCuratedAnswerRequest(BaseModel):
    answer_text: str
    status: str = "draft"  # "draft" | "published"
    citations: list[Citation] = Field(default_factory=list)


# --- Helper ------------------------------------------------------------------


def _topic_labels() -> dict[str, str]:
    canonical = get_canonical_topics()
    return {t["slug"]: t["name_id"] for t in canonical}


# --- Endpoints ---------------------------------------------------------------


@router.get("/dashboard", response_model=DashboardResponse)
async def get_dashboard(
    storage: StorageDep,
    admin: AdminDep,
) -> DashboardResponse:
    topics_list = await storage.list_topics()
    labels = _topic_labels()

    total_questions = await storage.count_questions()
    recent_refusals = await storage.count_questions(is_refused=True)
    recent_crises = await storage.count_questions(is_crisis=True)
    ungrounded_gaps = await storage.count_questions(has_grounding=False)
    review_items = len(await storage.list_flagged_chunks())

    # Build topic items
    items: list[TopicItem] = []
    published_count = 0
    total_likes = 0

    # Load questions to count dynamic aggregates
    all_qs = await storage.list_questions(limit=1000)
    q_counts: dict[str, int] = {}
    l_counts: dict[str, int] = {}
    refused_counts: dict[str, int] = {}

    for q in all_qs:
        slug = q.topic_slug or "lainnya"
        q_counts[slug] = q_counts.get(slug, 0) + 1
        l_counts[slug] = l_counts.get(slug, 0) + q.like_count
        total_likes += q.like_count
        if q.is_refused:
            refused_counts[slug] = refused_counts.get(slug, 0) + 1

    for t in topics_list:
        slug = t.slug
        q_count = max(t.question_count, q_counts.get(slug, 0))
        like_count = max(t.like_count, l_counts.get(slug, 0))
        cur_status = t.curated_status or "none"
        if not t.curated_answer:
            cur_status = "none"

        if cur_status == "published":
            published_count += 1

        refusal_rate = round(refused_counts.get(slug, 0) / q_count * 100, 1) if q_count > 0 else 0.0

        items.append(
            TopicItem(
                slug=slug,
                label=labels.get(slug, t.name_id or slug),
                questions=q_count,
                likes=like_count,
                curated=cur_status,
                curated_by=t.updated_by,
                curated_at=t.updated_at.isoformat() if t.updated_at else None,
                curated_answer=t.curated_answer,
                curated_citations=t.curated_citations,
                refusal_rate=refusal_rate,
            )
        )

    # Sort top topics by questions count
    items.sort(key=lambda x: x.questions, reverse=True)

    active_topics = len(topics_list)
    coverage = round((published_count / active_topics * 100) if active_topics > 0 else 0.0, 1)

    return DashboardResponse(
        total_questions=total_questions,
        total_likes=total_likes,
        active_topics=active_topics,
        curated_coverage=coverage,
        recent_refusals=recent_refusals,
        recent_crises=recent_crises,
        ungrounded_gaps=ungrounded_gaps,
        review_items=review_items,
        top_topics=items,
    )


@router.get("/topics", response_model=list[TopicItem])
async def list_topics(
    storage: StorageDep,
    admin: AdminDep,
) -> list[TopicItem]:
    topics_list = await storage.list_topics()
    labels = _topic_labels()

    all_qs = await storage.list_questions(limit=1000)
    q_counts: dict[str, int] = {}
    l_counts: dict[str, int] = {}
    refused_counts: dict[str, int] = {}

    for q in all_qs:
        slug = q.topic_slug or "lainnya"
        q_counts[slug] = q_counts.get(slug, 0) + 1
        l_counts[slug] = l_counts.get(slug, 0) + q.like_count
        if q.is_refused:
            refused_counts[slug] = refused_counts.get(slug, 0) + 1

    items: list[TopicItem] = []
    for t in topics_list:
        slug = t.slug
        q_count = max(t.question_count, q_counts.get(slug, 0))
        like_count = max(t.like_count, l_counts.get(slug, 0))
        cur_status = t.curated_status or "none"
        if not t.curated_answer:
            cur_status = "none"

        refusal_rate = round(refused_counts.get(slug, 0) / q_count * 100, 1) if q_count > 0 else 0.0

        items.append(
            TopicItem(
                slug=slug,
                label=labels.get(slug, t.name_id or slug),
                questions=q_count,
                likes=like_count,
                curated=cur_status,
                curated_by=t.updated_by,
                curated_at=t.updated_at.isoformat() if t.updated_at else None,
                curated_answer=t.curated_answer,
                curated_citations=t.curated_citations,
                refusal_rate=refusal_rate,
            )
        )

    items.sort(key=lambda x: x.questions, reverse=True)
    return items


@router.get("/topics/{slug}", response_model=TopicItem)
async def get_topic_detail(
    slug: str,
    storage: StorageDep,
    admin: AdminDep,
) -> TopicItem:
    t = await storage.get_topic(slug)
    if not t:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Topic '{slug}' not found")
    labels = _topic_labels()
    cur_status = t.curated_status or "none"
    if not t.curated_answer:
        cur_status = "none"

    return TopicItem(
        slug=slug,
        label=labels.get(slug, t.name_id or slug),
        questions=t.question_count,
        likes=t.like_count,
        curated=cur_status,
        curated_by=t.updated_by,
        curated_at=t.updated_at.isoformat() if t.updated_at else None,
        curated_answer=t.curated_answer,
        curated_citations=t.curated_citations,
    )


@router.put("/topics/{slug}/answer", response_model=TopicItem)
async def update_curated_answer(
    slug: str,
    payload: UpdateCuratedAnswerRequest,
    storage: StorageDep,
    admin: EditorDep,
) -> TopicItem:
    topic = await storage.get_topic(slug)
    if not topic:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail=f"Topic '{slug}' not found")

    # If publishing, validate content against V1-V4 rules
    if payload.status == "published":
        validator = ComplianceValidator()
        result = validator.validate(payload.answer_text)
        # Filter failures: ignore V4/V5 grounding since curated answers are editorial
        critical_fails = [
            f
            for f in result.failures
            if f.code
            in (
                ValidatorCode.v1_too_short,
                ValidatorCode.v1_too_long,
                ValidatorCode.v2_forbidden_term,
            )
        ]
        if critical_fails:
            messages = [f"{f.code.value}: {f.message}" for f in critical_fails]
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Content validation failed: {'; '.join(messages)}",
            )

    now = datetime.now(UTC)
    topic.curated_answer = payload.answer_text.strip()
    topic.curated_status = payload.status
    topic.curated_citations = payload.citations
    topic.updated_by = admin.email
    topic.updated_at = now

    await storage.save_topic(topic)
    labels = _topic_labels()

    return TopicItem(
        slug=slug,
        label=labels.get(slug, topic.name_id or slug),
        questions=topic.question_count,
        likes=topic.like_count,
        curated=topic.curated_status,
        curated_by=topic.updated_by,
        curated_at=now.isoformat(),
        curated_answer=topic.curated_answer,
        curated_citations=topic.curated_citations,
    )


@router.get("/questions", response_model=list[QuestionListItem])
async def list_questions(
    storage: StorageDep,
    admin: AdminDep,
    topic: str | None = None,
    refused: bool | None = None,
    crisis: bool | None = None,
    has_grounding: bool | None = None,
    source: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[QuestionListItem]:
    qs = await storage.list_questions(
        topic_slug=topic,
        is_refused=refused,
        is_crisis=crisis,
        has_grounding=has_grounding,
        answer_source=source,
        limit=limit,
        offset=offset,
    )
    labels = _topic_labels()

    items: list[QuestionListItem] = []
    for q in qs:
        slug = q.topic_slug or "lainnya"
        res_source = getattr(q.answer_source, "value", str(q.answer_source))

        flags: list[str] = []
        if q.is_crisis:
            flags.append("crisis")
        if q.is_refused:
            flags.append("refused")
        if q.validator_failures:
            flags.append("validator")

        items.append(
            QuestionListItem(
                id=q.id,
                asked_at=q.created_at.isoformat() if q.created_at else "",
                question=q.question_text,
                topic_slug=slug,
                topic_label=labels.get(slug, slug),
                result=res_source,
                likes=q.like_count,
                channel="web",
                flags=flags,
            )
        )

    return items


@router.get("/questions/{question_id}", response_model=QuestionDetailResponse)
async def get_question_detail(
    question_id: str,
    storage: StorageDep,
    admin: AdminDep,
) -> QuestionDetailResponse:
    q = await storage.get_question(question_id)
    if not q:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Question not found")
    labels = _topic_labels()
    slug = q.topic_slug or "lainnya"
    res_source = getattr(q.answer_source, "value", str(q.answer_source))

    return QuestionDetailResponse(
        id=q.id,
        asked_at=q.created_at.isoformat() if q.created_at else "",
        question=q.question_text,
        answer=q.answer_text,
        topic_slug=slug,
        topic_label=labels.get(slug, slug),
        result=res_source,
        likes=q.like_count,
        citations=q.citations,
        retrieved_chunk_ids=q.retrieved_chunk_ids,
        validator_failures=q.validator_failures,
        model=q.model,
        prompt_version=q.prompt_version,
        latency_ms=q.latency_ms,
    )


@router.get("/gaps")
async def list_content_gaps(
    storage: StorageDep,
    admin: AdminDep,
) -> list[dict[str, Any]]:
    """Return ungrounded questions grouped by content gaps."""
    qs = await storage.list_questions(has_grounding=False, limit=100)
    labels = _topic_labels()

    gaps: list[dict[str, Any]] = []
    for q in qs:
        slug = q.topic_slug or "lainnya"
        gaps.append(
            {
                "id": q.id,
                "canonical": q.question_text,
                "count": 1,
                "lastAsked": q.created_at.isoformat() if q.created_at else "",
                "nearestTopic": labels.get(slug, slug),
            }
        )
    return gaps


@router.get("/reviews")
async def list_reviews(
    storage: StorageDep,
    admin: AdminDep,
) -> list[dict[str, Any]]:
    """Return flagged chunks or review items."""
    flags = await storage.list_flagged_chunks()
    items: list[dict[str, Any]] = []
    for f in flags:
        items.append(
            {
                "id": f.id,
                "type": "validator",
                "summary": f"{f.title} ({f.site}): {', '.join(f.matched_terms)}",
                "at": f.created_at.isoformat() if f.created_at else "",
                "reviewed": f.decision.value != "pending",
            }
        )
    return items


@router.get("/config")
async def get_system_configurations(
    storage: StorageDep,
    admin: AdminDep,
) -> dict[str, str]:
    keys = [
        "contact_name",
        "contact_number",
        "similarity_threshold",
        "rate_limit_per_hour",
        "session_ttl_hours",
        "retention_months",
    ]
    res: dict[str, str] = {}
    for k in keys:
        cfg = await storage.get_system_config(k)
        if cfg:
            res[k] = cfg.value
    return res


@router.put("/config/{key}")
async def update_system_configuration(
    key: str,
    value: str,
    storage: StorageDep,
    admin: SuperAdminDep,
) -> dict[str, str]:
    now = datetime.now(UTC)
    cfg = SystemConfig(key=key, value=value, updated_by=admin.email, updated_at=now)
    await storage.set_system_config(cfg)
    return {"key": key, "value": value}
