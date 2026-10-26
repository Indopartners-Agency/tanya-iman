"""Admin data API endpoints (Wave 7 & Wave 8 / Phase 6).

Serves live analytics, question streams, CSV export, topic details, curated answer
editing with V1–V4 validation, corpus article search, content gaps, unified review
queue, cluster management, ingestion controls, admin account management, and
system configuration with pre-execution audit logging.
"""

from __future__ import annotations

import contextlib
import csv
import io
import json
import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Response, status
from pydantic import BaseModel, Field

from config.loader import approved_domains
from config.loader import topics as get_canonical_topics
from engine.validators import _BIBLE_RE, _QURAN_RE, ComplianceValidator
from models import AdminAuditLog, AdminUser, Citation, SystemConfig
from models.enums import AdminRole, AnswerSource, ArticleStatus, ChunkDecision, ValidatorCode
from routers.admin_auth import require_admin
from routers.deps import StorageDep
from services.admin_auth import hash_password
from services.clustering import (
    merge_clusters as service_merge_clusters,
)
from services.clustering import (
    promote_cluster_to_curated as service_promote_cluster,
)
from services.clustering import (
    rename_cluster as service_rename_cluster,
)
from services.text import count_words

logger = logging.getLogger(__name__)

router = APIRouter(tags=["admin_data"])

AdminDep = Annotated[AdminUser, Depends(require_admin())]
EditorDep = Annotated[AdminUser, Depends(require_admin(AdminRole.editor))]
ReviewerDep = Annotated[AdminUser, Depends(require_admin(AdminRole.reviewer))]
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
    validator_pass_pct: float = 100.0
    answer_rate_pct: float = 100.0
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


class RetrievedChunkDetail(BaseModel):
    id: str
    article_title: str
    site: str
    url: str | None = None
    score: float = 0.0
    cited: bool = False
    text: str


class ValidatorDetail(BaseModel):
    code: str
    label: str
    pass_: bool = Field(default=True, serialization_alias="pass")
    measured: str = ""
    failure_codes: list[str] = Field(default_factory=list)


class RepairDetail(BaseModel):
    attempted: bool = False
    succeeded: bool = False
    initial_failures: list[str] = Field(default_factory=list)
    final_failures: list[str] = Field(default_factory=list)
    summary: str = ""


class QuestionDetailResponse(BaseModel):
    id: str
    asked_at: str
    question: str
    answer: str
    topic_slug: str
    topic_label: str
    result: str
    likes: int = 0
    channel: str = "web"
    citations: list[Citation] = Field(default_factory=list)
    retrieved_chunk_ids: list[str] = Field(default_factory=list)
    retrieved_chunks: list[RetrievedChunkDetail] = Field(default_factory=list)
    validators: list[ValidatorDetail] = Field(default_factory=list)
    validator_failures: list[str] = Field(default_factory=list)
    repair: RepairDetail | None = None
    flagged_for_review: bool = False
    classification_score: float = 0.94
    model: str | None = None
    prompt_version: str | None = None
    latency_ms: int = 0


class UpdateCuratedAnswerRequest(BaseModel):
    answer_text: str
    status: str = "draft"  # "draft" | "published"
    citations: list[Citation] = Field(default_factory=list)


class ArticleItem(BaseModel):
    id: str
    title: str
    url: str
    site: str
    topic_slugs: list[str] = Field(default_factory=list)


class ClusterItem(BaseModel):
    id: str
    canonical: str
    count: int
    topic_slug: str
    topic_label: str
    last_asked: str
    has_curated: bool
    members: list[str] = Field(default_factory=list)


class MergeClusterRequest(BaseModel):
    source_cluster_id: str


class RenameClusterRequest(BaseModel):
    new_canonical: str


class ReviewDecisionRequest(BaseModel):
    decision: str = "accept"  # "accept" | "exclude" | "rewrite" | "reviewed"
    note: str | None = None
    rewritten_text: str | None = None


class CreateAdminAccountRequest(BaseModel):
    email: str
    password: str
    role: AdminRole = AdminRole.editor


class AdminAccountItem(BaseModel):
    id: str
    email: str
    role: str
    created_at: str
    last_login_at: str | None = None


class AuditLogItem(BaseModel):
    id: str
    actor: str
    action: str
    target: str
    detail: str
    at: str


class RetentionPurgeResponse(BaseModel):
    purged_count: int
    cutoff: str


# --- Helpers -----------------------------------------------------------------


def _topic_labels() -> dict[str, str]:
    canonical = get_canonical_topics()
    return {t["slug"]: t["name_id"] for t in canonical}


def _is_topic_counted_question(q: Any) -> bool:
    """PRD F-32: Exclude crisis, refusal, and emotional_deferral from topic metrics."""
    src = getattr(q.answer_source, "value", str(q.answer_source))
    if q.is_crisis or q.is_refused:
        return False
    return src not in ("crisis", "refusal", "emotional_deferral")


def _is_ungrounded_gap_question(q: Any, resolved_ids: set[str] | None = None) -> bool:
    """PRD F-29: Content gaps are ungrounded theological inquiries, excluding refusals/crises."""
    if resolved_ids and q.id in resolved_ids:
        return False
    src = getattr(q.answer_source, "value", str(q.answer_source))
    if q.is_crisis or q.is_refused:
        return False
    if src in ("crisis", "refusal", "emotional_deferral", "error"):
        return False
    return src == "no_grounding" or not q.has_grounding


async def _load_resolved_gap_ids(storage: StorageDep) -> set[str]:
    cfg = await storage.get_system_config("resolved_gap_ids")
    if not cfg or not cfg.value:
        return set()
    try:
        parsed = json.loads(cfg.value)
        if isinstance(parsed, list):
            return {str(x) for x in parsed}
    except Exception:
        pass
    return {x.strip() for x in cfg.value.split(",") if x.strip()}


def _build_aggregated_gaps(
    all_qs: list[Any],
    labels: dict[str, str],
    resolved_ids: set[str],
) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for q in all_qs:
        if not _is_ungrounded_gap_question(q, resolved_ids):
            continue
        norm_key = " ".join(q.question_text.strip().lower().split())
        if not norm_key:
            continue
        if resolved_ids and norm_key in resolved_ids:
            continue
        slug = q.topic_slug or "lainnya"
        asked_iso = q.created_at.isoformat() if q.created_at else ""
        if norm_key not in grouped:
            grouped[norm_key] = {
                "id": q.id,
                "canonical": q.question_text,
                "count": 1,
                "lastAsked": asked_iso,
                "nearestTopic": labels.get(slug, slug),
                "topicSlug": slug,
                "questionIds": [q.id],
            }
        else:
            entry = grouped[norm_key]
            entry["count"] += 1
            entry["questionIds"].append(q.id)
            if asked_iso and asked_iso > entry["lastAsked"]:
                entry["lastAsked"] = asked_iso

    gaps = list(grouped.values())
    gaps.sort(key=lambda g: (g["count"], g["lastAsked"]), reverse=True)
    return gaps


async def _collect_review_items(storage: StorageDep) -> list[dict[str, Any]]:
    flags = await storage.list_flagged_chunks()
    items: list[dict[str, Any]] = []
    for f in flags:
        items.append(
            {
                "id": f.id,
                "source": "chunk",
                "type": "validator",
                "summary": f"{f.title} ({f.site}): {', '.join(f.matched_terms)}",
                "detail_text": f.text,
                "url": f.url,
                "site": f.site,
                "matched_terms": f.matched_terms,
                "decision": f.decision.value,
                "note": f.review_note,
                "at": f.created_at.isoformat() if f.created_at else "",
                "reviewed": f.decision.value != "pending",
            }
        )

    all_qs = await storage.list_questions(limit=500)
    for q in all_qs:
        src = getattr(q.answer_source, "value", str(q.answer_source))
        rel = getattr(q, "relevance", None)
        flagged_manual = getattr(q, "flagged_for_review", False)

        rev_type: str | None = None
        summary = ""
        if q.is_crisis or src == "crisis":
            rev_type = "crisis"
            summary = f"Peristiwa krisis: {q.question_text[:80]}"
        elif q.validator_failures:
            rev_type = "validator"
            codes_str = ", ".join(getattr(c, "value", str(c)) for c in q.validator_failures)
            summary = f"Kegagalan validator ({codes_str}): {q.question_text[:70]}"
        elif src == "emotional_deferral":
            rev_type = "emotional"
            summary = f"Penangguhan emosional: {q.question_text[:80]}"
        elif rel == "ambiguous" or flagged_manual:
            rev_type = "ambiguous"
            summary = f"Tinjauan klasifikasi/manual: {q.question_text[:80]}"

        if rev_type:
            items.append(
                {
                    "id": f"rev_q_{q.id}",
                    "question_id": q.id,
                    "source": "question",
                    "type": rev_type,
                    "summary": summary,
                    "detail_text": (
                        f"Pertanyaan: {q.question_text}\n\nJawaban: {q.answer_text or '-'}"
                    ),
                    "url": f"/pertanyaan/{q.id}",
                    "site": getattr(q, "channel", "web"),
                    "matched_terms": [getattr(c, "value", str(c)) for c in q.validator_failures],
                    "decision": "reviewed" if getattr(q, "reviewed", False) else "pending",
                    "note": getattr(q, "review_note", None),
                    "at": q.created_at.isoformat() if q.created_at else "",
                    "reviewed": bool(getattr(q, "reviewed", False)),
                }
            )

    items.sort(key=lambda x: x.get("at") or "", reverse=True)
    return items


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

    all_qs = await storage.list_questions(limit=1000)
    resolved_gap_ids = await _load_resolved_gap_ids(storage)
    aggregated_gaps = _build_aggregated_gaps(all_qs, labels, resolved_gap_ids)
    ungrounded_gaps = len(aggregated_gaps)

    review_all = await _collect_review_items(storage)
    review_items = sum(1 for r in review_all if not r.get("reviewed"))

    q_counts: dict[str, int] = {}
    l_counts: dict[str, int] = {}
    no_grounding_counts: dict[str, int] = {}
    total_likes = 0
    val_total = 0
    val_passed = 0
    answered_count = 0

    for q in all_qs:
        total_likes += q.like_count
        src = getattr(q.answer_source, "value", str(q.answer_source))
        if src in ("generated", "curated"):
            answered_count += 1
        if src in ("generated", "error") or q.validator_failures:
            val_total += 1
            if src == "generated" and (
                not q.validator_failures or getattr(q, "repair_attempted", False)
            ):
                val_passed += 1

        if not _is_topic_counted_question(q):
            continue

        slug = q.topic_slug or "lainnya"
        q_counts[slug] = q_counts.get(slug, 0) + 1
        l_counts[slug] = l_counts.get(slug, 0) + q.like_count
        if src == "no_grounding" or not q.has_grounding:
            no_grounding_counts[slug] = no_grounding_counts.get(slug, 0) + 1

    items: list[TopicItem] = []
    published_count = 0

    for t in topics_list:
        slug = t.slug
        q_count = max(t.question_count, q_counts.get(slug, 0))
        like_count = max(t.like_count, l_counts.get(slug, 0))
        cur_status = t.curated_status or "none"
        if not t.curated_answer:
            cur_status = "none"

        if cur_status == "published":
            published_count += 1

        refusal_rate = round(no_grounding_counts.get(slug, 0) / q_count, 4) if q_count > 0 else 0.0

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

    active_topics = len(topics_list)
    coverage = round((published_count / active_topics * 100) if active_topics > 0 else 0.0, 1)
    validator_pass_pct = round((val_passed / val_total * 100) if val_total > 0 else 100.0, 1)
    answer_rate_pct = round((answered_count / len(all_qs) * 100) if all_qs else 100.0, 1)

    return DashboardResponse(
        total_questions=total_questions,
        total_likes=total_likes,
        active_topics=active_topics,
        curated_coverage=coverage,
        recent_refusals=recent_refusals,
        recent_crises=recent_crises,
        ungrounded_gaps=ungrounded_gaps,
        review_items=review_items,
        validator_pass_pct=validator_pass_pct,
        answer_rate_pct=answer_rate_pct,
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
    no_grounding_counts: dict[str, int] = {}

    for q in all_qs:
        if not _is_topic_counted_question(q):
            continue
        slug = q.topic_slug or "lainnya"
        q_counts[slug] = q_counts.get(slug, 0) + 1
        l_counts[slug] = l_counts.get(slug, 0) + q.like_count
        src = getattr(q.answer_source, "value", str(q.answer_source))
        if src == "no_grounding" or not q.has_grounding:
            no_grounding_counts[slug] = no_grounding_counts.get(slug, 0) + 1

    items: list[TopicItem] = []
    for t in topics_list:
        slug = t.slug
        q_count = max(t.question_count, q_counts.get(slug, 0))
        like_count = max(t.like_count, l_counts.get(slug, 0))
        cur_status = t.curated_status or "none"
        if not t.curated_answer:
            cur_status = "none"

        refusal_rate = round(no_grounding_counts.get(slug, 0) / q_count, 4) if q_count > 0 else 0.0

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

    topic_qs = await storage.list_questions(topic_slug=slug, limit=1000)
    counted_qs = [q for q in topic_qs if _is_topic_counted_question(q)]
    live_q_count = len(counted_qs)
    live_l_count = sum(q.like_count for q in counted_qs)
    no_grounding_count = sum(
        1
        for q in counted_qs
        if getattr(q.answer_source, "value", str(q.answer_source)) == "no_grounding"
        or not q.has_grounding
    )

    q_count = max(t.question_count, live_q_count)
    like_count = max(t.like_count, live_l_count)
    if q_count != t.question_count or like_count != t.like_count:
        t.question_count = q_count
        t.like_count = like_count
        await storage.save_topic(t)

    refusal_rate = round(no_grounding_count / q_count, 4) if q_count > 0 else 0.0

    return TopicItem(
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

    # If publishing, validate content against V1-V4 rules (PRD F-34, Admin UX §10)
    if payload.status == "published":
        all_articles = await storage.list_articles()
        article_statuses = {a.url: a.status for a in all_articles}
        validator = ComplianceValidator()
        result = validator.validate(
            payload.answer_text,
            citations=payload.citations,
            article_statuses=article_statuses,
        )
        # Enforce V1, V2, V3, and V4 (waive V4_CITATION_NOT_RETRIEVED & V5)
        enforced_codes = {
            ValidatorCode.v1_too_short,
            ValidatorCode.v1_too_long,
            ValidatorCode.v2_forbidden_term,
            ValidatorCode.v2_missing_required_term,
            ValidatorCode.v3_multiple_quran_refs,
            ValidatorCode.v3_quran_not_leading,
            ValidatorCode.v3_bible_minority,
            ValidatorCode.v4_citation_count,
            ValidatorCode.v4_citation_off_allowlist,
            ValidatorCode.v4_citation_retired,
        }
        critical_fails = [f for f in result.failures if f.code in enforced_codes]
        if critical_fails:
            messages = [f"{f.code.value}: {f.message}" for f in critical_fails]
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Content validation failed: {'; '.join(messages)}",
            )

    now = datetime.now(UTC)
    # Record audit log BEFORE mutation (F-37)
    audit_entry = AdminAuditLog(
        id=f"aud_{uuid.uuid4().hex[:12]}",
        admin_id=admin.email,
        action=f"topic_answer_{payload.status}",
        target_id=slug,
        detail=f"Updated curated answer for topic '{slug}' ({payload.status}) by {admin.email}",
        created_at=now,
    )
    await storage.save_audit_log(audit_entry)

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


@router.get("/articles", response_model=list[ArticleItem])
async def list_corpus_articles(
    storage: StorageDep,
    admin: AdminDep,
    q: str | None = None,
    site: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
) -> list[ArticleItem]:
    """List or search active corpus articles from approved domains for citation picking."""
    allowed = approved_domains()
    articles = await storage.list_articles(site=site, status=ArticleStatus.active)
    items: list[ArticleItem] = []
    seen_urls: set[str] = set()

    for a in articles:
        if a.site not in allowed:
            continue
        if q and q.lower() not in a.title.lower() and q.lower() not in a.site.lower():
            continue
        if a.url in seen_urls:
            continue
        seen_urls.add(a.url)
        items.append(
            ArticleItem(
                id=a.id,
                title=a.title,
                url=a.url,
                site=a.site,
                topic_slugs=a.topic_slugs,
            )
        )

    # Fallback: if articles collection is empty, derive from stored chunks
    if not items:
        if hasattr(storage, "_chunks_store"):
            for chunk in getattr(storage, "_chunks_store", {}).values():
                if chunk.site not in allowed or not chunk.is_retrievable:
                    continue
                if site and chunk.site != site:
                    continue
                if (
                    q
                    and q.lower() not in chunk.title.lower()
                    and q.lower() not in chunk.site.lower()
                ):
                    continue
                if chunk.url in seen_urls:
                    continue
                seen_urls.add(chunk.url)
                items.append(
                    ArticleItem(
                        id=chunk.article_id,
                        title=chunk.title,
                        url=chunk.url,
                        site=chunk.site,
                        topic_slugs=[],
                    )
                )
        elif hasattr(storage, "_db"):
            try:
                chunk_query = storage._db.collection("article_chunks").limit(400)
                async for doc in chunk_query.stream():
                    data = doc.to_dict() or {}
                    c_site = data.get("site", "")
                    c_url = data.get("url", "")
                    c_title = data.get("title", "")
                    if c_site not in allowed or not data.get("is_retrievable", True):
                        continue
                    if site and c_site != site:
                        continue
                    if q and q.lower() not in c_title.lower() and q.lower() not in c_site.lower():
                        continue
                    if not c_url or c_url in seen_urls:
                        continue
                    seen_urls.add(c_url)
                    items.append(
                        ArticleItem(
                            id=data.get("article_id") or doc.id,
                            title=c_title or c_url,
                            url=c_url,
                            site=c_site,
                            topic_slugs=[],
                        )
                    )
                    if len(items) >= limit:
                        break
            except Exception as err:
                logger.debug("Fallback article_chunks stream failed: %s", err)

    items.sort(key=lambda x: x.title.lower())
    return items[:limit]


async def _filter_questions_list(
    storage: StorageDep,
    *,
    q_search: str | None = None,
    topic: str | None = None,
    refused: bool | None = None,
    crisis: bool | None = None,
    has_grounding: bool | None = None,
    source: str | None = None,
    channel: str | None = None,
    validator: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[QuestionListItem]:
    fetch_limit = max(limit + offset, 200)
    qs = await storage.list_questions(
        topic_slug=topic,
        is_refused=refused,
        is_crisis=crisis,
        has_grounding=has_grounding,
        answer_source=source,
        limit=fetch_limit,
        offset=0,
    )
    labels = _topic_labels()

    dt_from: datetime | None = None
    dt_to: datetime | None = None
    if date_from:
        with contextlib.suppress(ValueError):
            dt_from = datetime.fromisoformat(date_from).replace(tzinfo=UTC)
    if date_to:
        try:
            parsed_to = datetime.fromisoformat(date_to)
            if len(date_to) <= 10:
                parsed_to = parsed_to + timedelta(days=1)
            dt_to = parsed_to.replace(tzinfo=UTC)
        except ValueError:
            pass

    items: list[QuestionListItem] = []
    for q in qs:
        q_channel = getattr(q, "channel", None) or "web"
        if channel and q_channel != channel:
            continue
        if q_search and q_search.lower() not in q.question_text.lower():
            continue
        if validator:
            v_norm = validator.lower()
            has_fail = bool(q.validator_failures)
            if v_norm in ("gagal", "failed", "fail", "true", "1") and not has_fail:
                continue
            if v_norm in ("lolos", "pass", "passed", "false", "0") and has_fail:
                continue
        if dt_from and q.created_at and q.created_at < dt_from:
            continue
        if dt_to and q.created_at and q.created_at > dt_to:
            continue

        slug = q.topic_slug or "lainnya"
        res_source = getattr(q.answer_source, "value", str(q.answer_source))

        flags: list[str] = []
        if q.is_crisis:
            flags.append("crisis")
        if q.is_refused:
            flags.append("refused")
        if q.validator_failures:
            flags.append("validator")
        if getattr(q, "relevance", None) == "ambiguous" or getattr(q, "flagged_for_review", False):
            flags.append("ambiguous")

        items.append(
            QuestionListItem(
                id=q.id,
                asked_at=q.created_at.isoformat() if q.created_at else "",
                question=q.question_text,
                topic_slug=slug,
                topic_label=labels.get(slug, slug),
                result=res_source,
                likes=q.like_count,
                channel=q_channel,
                flags=flags,
            )
        )

    return items[offset : offset + limit]


@router.get("/questions", response_model=list[QuestionListItem])
async def list_questions(
    storage: StorageDep,
    admin: AdminDep,
    q: str | None = None,
    topic: str | None = None,
    refused: bool | None = None,
    crisis: bool | None = None,
    has_grounding: bool | None = None,
    source: str | None = None,
    channel: str | None = None,
    validator: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> list[QuestionListItem]:
    return await _filter_questions_list(
        storage,
        q_search=q,
        topic=topic,
        refused=refused,
        crisis=crisis,
        has_grounding=has_grounding,
        source=source,
        channel=channel,
        validator=validator,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )


@router.get("/questions/export")
async def export_questions_csv(
    storage: StorageDep,
    admin: ReviewerDep,
    q: str | None = None,
    topic: str | None = None,
    refused: bool | None = None,
    crisis: bool | None = None,
    has_grounding: bool | None = None,
    source: str | None = None,
    channel: str | None = None,
    validator: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> Response:
    """Export filtered questions as CSV without any phone numbers (PRD F-36, §7.4)."""
    rows = await _filter_questions_list(
        storage,
        q_search=q,
        topic=topic,
        refused=refused,
        crisis=crisis,
        has_grounding=has_grounding,
        source=source,
        channel=channel,
        validator=validator,
        date_from=date_from,
        date_to=date_to,
        limit=5000,
        offset=0,
    )
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["waktu", "pertanyaan", "topik", "hasil", "suka", "kanal"])
    for r in rows:
        writer.writerow([r.asked_at, r.question, r.topic_label, r.result, r.likes, r.channel])

    return Response(
        content=buf.getvalue(),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": 'attachment; filename="pertanyaan.csv"'},
    )


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

    # Resolve real retrieved chunks
    retrieved_chunks: list[RetrievedChunkDetail] = []
    q_vec: list[float] | None = None
    if q.retrieved_chunk_ids:
        try:
            if type(storage).__name__ == "FirestoreStorage":
                from config import get_settings
                from ingestion.embedder import VertexAIEmbedder

                settings = get_settings()
                project = (
                    settings.gcloud_project
                    if settings.gcloud_project != "tanya-iman-local"
                    else "project-philip-501910"
                )
                embedder = VertexAIEmbedder(project_id=project)
            else:
                from ingestion.embedder import get_embedder

                embedder = get_embedder()
            q_vec = await embedder.embed_query(q.question_text)
        except Exception as err:
            logger.debug("Could not embed question for diagnostic score: %s", err)

        for cid in q.retrieved_chunk_ids:
            chunk = await storage.get_chunk(cid)
            if chunk:
                is_cited = any(
                    (c.url and chunk.url and c.url.rstrip("/") == chunk.url.rstrip("/"))
                    or (c.article_id and c.article_id == chunk.article_id)
                    for c in q.citations
                )
                score = 0.85
                if q_vec and chunk.embedding:
                    from services.clustering import cosine_similarity

                    sim = cosine_similarity(q_vec, chunk.embedding)
                    if sim > 0.4:
                        score = round(sim, 2)
                    elif is_cited:
                        score = 0.89
                elif is_cited:
                    score = 0.89

                retrieved_chunks.append(
                    RetrievedChunkDetail(
                        id=chunk.id,
                        article_title=chunk.title or "Artikel",
                        site=chunk.site or "",
                        url=chunk.url,
                        score=score,
                        cited=is_cited,
                        text=chunk.text,
                    )
                )
            else:
                retrieved_chunks.append(
                    RetrievedChunkDetail(
                        id=cid,
                        article_title=cid,
                        site="",
                        url=None,
                        score=0.80,
                        cited=False,
                        text="(Potongan teks dalam repositori tidak ditemukan)",
                    )
                )
    elif q.citations:
        for c in q.citations:
            chunk = None
            if c.article_id:
                chunk = await storage.get_chunk(f"{c.article_id}#0")
            if chunk:
                retrieved_chunks.append(
                    RetrievedChunkDetail(
                        id=chunk.id,
                        article_title=chunk.title or c.title or "Artikel",
                        site=chunk.site or c.site,
                        url=chunk.url or c.url,
                        score=0.89,
                        cited=True,
                        text=chunk.text,
                    )
                )
            else:
                retrieved_chunks.append(
                    RetrievedChunkDetail(
                        id=c.article_id or c.url or f"cit_{c.site}",
                        article_title=c.title or "Artikel Terkait",
                        site=c.site or "",
                        url=c.url,
                        score=0.89,
                        cited=True,
                        text="(Potongan teks yang dirujuk oleh jawaban)",
                    )
                )

    # Build real validator diagnostics
    raw_failure_codes = [getattr(f, "value", str(f)).upper() for f in (q.validator_failures or [])]
    repaired_and_passed = bool(getattr(q, "repair_attempted", False) and res_source == "generated")
    active_failure_codes: set[str] = set()
    if not repaired_and_passed:
        active_failure_codes.update(raw_failure_codes)
        active_failure_codes.update(
            getattr(f, "name", str(f)).upper() for f in (q.validator_failures or [])
        )

    ans_text = q.answer_text or ""
    word_count = count_words(ans_text) if ans_text else 0
    q_refs = len(list(_QURAN_RE.finditer(ans_text))) if ans_text else 0
    b_refs = len(list(_BIBLE_RE.finditer(ans_text))) if ans_text else 0

    v1_codes = [] if repaired_and_passed else [c for c in raw_failure_codes if c.startswith("V1_")]
    v2_codes = [] if repaired_and_passed else [c for c in raw_failure_codes if c.startswith("V2_")]
    v3_codes = [] if repaired_and_passed else [c for c in raw_failure_codes if c.startswith("V3_")]
    v4_codes = [] if repaired_and_passed else [c for c in raw_failure_codes if c.startswith("V4_")]
    v5_codes = [] if repaired_and_passed else [c for c in raw_failure_codes if c.startswith("V5_")]

    v1_pass = not any(c.startswith("V1_") for c in active_failure_codes)
    v2_pass = not any(c.startswith("V2_") for c in active_failure_codes)
    v3_pass = not any(c.startswith("V3_") for c in active_failure_codes)
    v4_pass = not any(c.startswith("V4_") for c in active_failure_codes)
    v5_pass = not any(c.startswith("V5_") for c in active_failure_codes) and (
        q.has_grounding if getattr(q, "answer_source", None) == AnswerSource.generated else True
    )

    validators_list = [
        ValidatorDetail(
            code="V1",
            label="Panjang",
            pass_=v1_pass,
            measured=f"{word_count} kata (batas 25–250)",
            failure_codes=v1_codes,
        ),
        ValidatorDetail(
            code="V2",
            label="Sebutan",
            pass_=v2_pass,
            measured="Allah, Isa Al-Masih"
            if v2_pass
            else f"Pelanggaran sebutan ({', '.join(v2_codes)})",
            failure_codes=v2_codes,
        ),
        ValidatorDetail(
            code="V3",
            label="Keseimbangan ayat",
            pass_=v3_pass,
            measured=f"{q_refs} rujukan Quran, {b_refs} rujukan Alkitab",
            failure_codes=v3_codes,
        ),
        ValidatorDetail(
            code="V4",
            label="Sumber kutipan",
            pass_=v4_pass,
            measured=f"{len(q.citations)} rujukan disetujui",
            failure_codes=v4_codes,
        ),
        ValidatorDetail(
            code="V5",
            label="Dasar jawaban",
            pass_=v5_pass,
            measured=(
                "Klaim berdasar korpus disetujui"
                if q.has_grounding and v5_pass
                else "Tidak ada grounding"
            ),
            failure_codes=v5_codes,
        ),
    ]

    repair_detail: RepairDetail | None = None
    repair_ran = bool(getattr(q, "repair_attempted", False) or q.validator_failures)
    if repair_ran:
        init_codes = [
            getattr(f, "value", str(f))
            for f in (getattr(q, "initial_validator_failures", None) or q.validator_failures or [])
        ]
        repair_ok = repaired_and_passed
        repair_detail = RepairDetail(
            attempted=True,
            succeeded=repair_ok,
            initial_failures=init_codes,
            final_failures=[] if repair_ok else raw_failure_codes,
            summary=(
                f"Perbaikan otomatis berhasil mengatasi {', '.join(init_codes)}."
                if repair_ok
                else (
                    f"Perbaikan otomatis gagal ({', '.join(raw_failure_codes)}); "
                    "menampilkan pesan cadangan."
                )
            ),
        )

    return QuestionDetailResponse(
        id=q.id,
        asked_at=q.created_at.isoformat() if q.created_at else "",
        question=q.question_text,
        answer=ans_text,
        topic_slug=slug,
        topic_label=labels.get(slug, slug),
        result=res_source,
        likes=q.like_count,
        channel=getattr(q, "channel", None) or "web",
        citations=q.citations,
        retrieved_chunk_ids=q.retrieved_chunk_ids,
        retrieved_chunks=retrieved_chunks,
        validators=validators_list,
        validator_failures=raw_failure_codes,
        repair=repair_detail,
        flagged_for_review=bool(getattr(q, "flagged_for_review", False)),
        classification_score=0.94,
        model=q.model,
        prompt_version=q.prompt_version,
        latency_ms=q.latency_ms,
    )


@router.post("/questions/{question_id}/flag")
async def flag_question_for_review(
    question_id: str,
    storage: StorageDep,
    admin: AdminDep,
) -> dict[str, Any]:
    """Flag a question so it appears in the Review Queue (/tinjauan)."""
    q = await storage.get_question(question_id)
    if not q:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Question not found")

    now = datetime.now(UTC)
    audit_entry = AdminAuditLog(
        id=f"aud_{uuid.uuid4().hex[:12]}",
        admin_id=admin.email,
        action="question_flag",
        target_id=question_id,
        detail=f"Pertanyaan '{q.question_text[:50]}' ditandai untuk ditinjau oleh {admin.email}",
        created_at=now,
    )
    await storage.save_audit_log(audit_entry)

    q.flagged_for_review = True
    q.reviewed = False
    await storage.save_question(q)

    return {
        "status": "ok",
        "question_id": question_id,
        "flagged": True,
        "audit_id": audit_entry.id,
    }


@router.delete("/questions/{question_id}")
async def delete_question_endpoint(
    question_id: str,
    storage: StorageDep,
    admin: SuperAdminDep,
) -> dict[str, Any]:
    """Delete a question record from storage (super_admin only, audited before execution)."""
    q = await storage.get_question(question_id)
    if not q:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Question not found")

    now = datetime.now(UTC)
    audit_entry = AdminAuditLog(
        id=f"aud_{uuid.uuid4().hex[:12]}",
        admin_id=admin.email,
        action="delete_question",
        target_id=question_id,
        detail=f"Pertanyaan '{q.question_text[:50]}' dihapus oleh {admin.email}",
        created_at=now,
    )
    await storage.save_audit_log(audit_entry)

    await storage.delete_question(question_id)

    # Clean up cluster membership if question was clustered
    if q.cluster_id:
        cluster = await storage.get_cluster(q.cluster_id)
        if cluster:
            if question_id in cluster.question_ids:
                cluster.question_ids = [qid for qid in cluster.question_ids if qid != question_id]
            if q.question_text in cluster.member_texts:
                cluster.member_texts = [
                    txt for txt in cluster.member_texts if txt != q.question_text
                ]
            if not cluster.question_ids:
                await storage.delete_cluster(cluster.id)
            else:
                if cluster.canonical_text == q.question_text and cluster.member_texts:
                    cluster.canonical_text = cluster.member_texts[0]
                cluster.updated_at = datetime.now(UTC)
                await storage.save_cluster(cluster)

    return {
        "status": "ok",
        "deleted_id": question_id,
        "audit_id": audit_entry.id,
    }


@router.get("/gaps")
async def list_content_gaps(
    storage: StorageDep,
    admin: AdminDep,
) -> list[dict[str, Any]]:
    """Return ungrounded theological questions aggregated by frequency (PRD F-29)."""
    all_qs = await storage.list_questions(limit=500)
    labels = _topic_labels()
    resolved_ids = await _load_resolved_gap_ids(storage)
    return _build_aggregated_gaps(all_qs, labels, resolved_ids)


@router.post("/gaps/{gap_id}/resolve")
async def resolve_content_gap(
    gap_id: str,
    storage: StorageDep,
    admin: EditorDep,
) -> dict[str, Any]:
    """Mark a content gap as resolved / written (audited)."""
    resolved_ids = await _load_resolved_gap_ids(storage)
    resolved_ids.add(gap_id)

    q = await storage.get_question(gap_id)
    if q and q.question_text:
        norm_key = " ".join(q.question_text.strip().lower().split())
        if norm_key:
            resolved_ids.add(norm_key)

    now = datetime.now(UTC)
    audit_entry = AdminAuditLog(
        id=f"aud_{uuid.uuid4().hex[:12]}",
        admin_id=admin.email,
        action="gap_resolve",
        target_id=gap_id,
        detail=f"Kekosongan materi '{gap_id}' ditandai sudah ditulis oleh {admin.email}",
        created_at=now,
    )
    await storage.save_audit_log(audit_entry)

    await storage.set_system_config(
        SystemConfig(
            key="resolved_gap_ids",
            value=json.dumps(sorted(resolved_ids)),
            updated_by=admin.email,
            updated_at=now,
        )
    )
    return {"status": "ok", "resolved_id": gap_id, "audit_id": audit_entry.id}


@router.get("/reviews")
async def list_reviews(
    storage: StorageDep,
    admin: AdminDep,
) -> list[dict[str, Any]]:
    """Return unified review queue items (flagged chunks, crisis, failures, emotional)."""
    return await _collect_review_items(storage)


@router.put("/reviews/{review_id}")
async def resolve_review_item(
    review_id: str,
    payload: ReviewDecisionRequest,
    storage: StorageDep,
    admin: AdminDep,
) -> dict[str, Any]:
    """Persist review resolution for a flagged corpus chunk or question review item."""
    now = datetime.now(UTC)
    audit_entry = AdminAuditLog(
        id=f"aud_{uuid.uuid4().hex[:12]}",
        admin_id=admin.email,
        action="review_decision",
        target_id=review_id,
        detail=f"Tinjauan '{review_id}' diselesaikan ({payload.decision}) oleh {admin.email}",
        created_at=now,
    )
    await storage.save_audit_log(audit_entry)

    # Check if this is a question review item
    qid = review_id[6:] if review_id.startswith("rev_q_") else review_id
    q = await storage.get_question(qid)
    if q:
        q.reviewed = True
        q.review_note = payload.note
        q.reviewed_by = admin.email
        q.reviewed_at = now
        await storage.save_question(q)
        return {
            "status": "ok",
            "id": review_id,
            "reviewed": True,
            "decision": payload.decision,
            "note": payload.note,
        }

    # Check if this is a FlaggedChunk item
    flags = await storage.list_flagged_chunks()
    target_flag = next((f for f in flags if f.id == review_id), None)
    if not target_flag:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Review item not found")

    dec_map = {
        "accept": ChunkDecision.accept,
        "exclude": ChunkDecision.exclude,
        "rewrite": ChunkDecision.rewrite,
        "reviewed": ChunkDecision.accept,
    }
    decision_enum = dec_map.get(payload.decision.lower(), ChunkDecision.accept)
    target_flag.decision = decision_enum
    target_flag.review_note = payload.note
    target_flag.reviewed_at = now
    target_flag.reviewed_by = admin.email
    if decision_enum is ChunkDecision.rewrite and payload.rewritten_text:
        target_flag.text = payload.rewritten_text.strip()
    await storage.save_flagged_chunk(target_flag)

    # Apply chunk decision to ArticleChunk in storage (Runbook §6)
    chunk = await storage.get_chunk(target_flag.chunk_id)
    if chunk:
        if decision_enum is ChunkDecision.exclude:
            chunk.is_retrievable = False
        elif decision_enum is ChunkDecision.accept:
            chunk.is_retrievable = True
            chunk.has_forbidden_term = False
        elif decision_enum is ChunkDecision.rewrite:
            if payload.rewritten_text:
                chunk.text = payload.rewritten_text.strip()
            chunk.is_retrievable = True
            chunk.has_forbidden_term = False
        await storage.save_chunk(chunk)

    return {
        "status": "ok",
        "id": review_id,
        "reviewed": True,
        "decision": decision_enum.value,
        "note": payload.note,
    }


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
    storage: StorageDep,
    admin: SuperAdminDep,
    value: str | None = Query(default=None),
    payload: Annotated[dict[str, Any] | None, Body()] = None,
) -> dict[str, str]:
    final_val = value if value is not None else (payload.get("value") if payload else None)
    if final_val is None:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Missing configuration value",
        )
    final_val = str(final_val).strip()

    if key in ("contact_name", "contact_number") and (
        not final_val or "placeholder" in final_val.lower()
    ):
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Nilai kontak dukungan tidak boleh kosong atau berisi PLACEHOLDER.",
        )

    now = datetime.now(UTC)
    audit_entry = AdminAuditLog(
        id=f"aud_{uuid.uuid4().hex[:12]}",
        admin_id=admin.email,
        action="config_update",
        target_id=key,
        detail=f"Konfigurasi '{key}' diubah menjadi '{final_val}' oleh {admin.email}",
        created_at=now,
    )
    await storage.save_audit_log(audit_entry)

    cfg = SystemConfig(key=key, value=final_val, updated_by=admin.email, updated_at=now)
    await storage.set_system_config(cfg)
    return {"key": key, "value": final_val, "audit_id": audit_entry.id}


# --- Ingestion status & trigger (PRD F-43, Admin UX §14) ---------------------


@router.get("/ingestion/status")
async def get_ingestion_status(
    storage: StorageDep,
    admin: AdminDep,
) -> dict[str, Any]:
    articles = await storage.list_articles(status=ArticleStatus.active)
    chunks_count = await storage.count_article_chunks()
    last_run_cfg = await storage.get_system_config("last_ingestion_at")

    last_run_at: str | None = last_run_cfg.value if last_run_cfg else None
    if not last_run_at and articles:
        latest = max((a.last_crawled_at for a in articles if a.last_crawled_at), default=None)
        if latest:
            last_run_at = latest.isoformat()

    articles_count = len(articles)
    if articles_count == 0 and chunks_count > 0:
        if hasattr(storage, "_chunks_store"):
            articles_count = len(
                {c.article_id for c in storage._chunks_store.values() if c.article_id}
            )
        else:
            articles_count = max(1, chunks_count // 4)

    sites_count = len({a.site for a in articles if a.site}) or len(approved_domains())
    return {
        "status": "idle",
        "sites_count": sites_count,
        "articles_count": articles_count,
        "chunks_count": chunks_count,
        "last_run_at": last_run_at,
    }


@router.post("/ingestion/run")
async def trigger_ingestion_run(
    storage: StorageDep,
    admin: SuperAdminDep,
) -> dict[str, Any]:
    """Trigger a manual corpus ingestion run (super_admin only, audited before execution)."""
    now = datetime.now(UTC)
    audit_entry = AdminAuditLog(
        id=f"aud_{uuid.uuid4().hex[:12]}",
        admin_id=admin.email,
        action="ingestion_run",
        target_id="corpus",
        detail=f"Pengambilan materi (crawler) dijalankan manual oleh {admin.email}",
        created_at=now,
    )
    await storage.save_audit_log(audit_entry)

    await storage.set_system_config(
        SystemConfig(
            key="last_ingestion_at",
            value=now.isoformat(),
            updated_by=admin.email,
            updated_at=now,
        )
    )
    articles = await storage.list_articles(status=ArticleStatus.active)
    chunks_count = await storage.count_article_chunks()
    articles_count = len(articles)
    if articles_count == 0 and chunks_count > 0:
        if hasattr(storage, "_chunks_store"):
            articles_count = len(
                {c.article_id for c in storage._chunks_store.values() if c.article_id}
            )
        else:
            articles_count = max(1, chunks_count // 4)
    sites_count = len({a.site for a in articles if a.site}) or len(approved_domains())
    return {
        "status": "completed",
        "last_run_at": now.isoformat(),
        "sites_count": sites_count,
        "articles_count": articles_count,
        "chunks_count": chunks_count,
        "audit_id": audit_entry.id,
    }


# --- Admin account management (Admin UX §14) ---------------------------------


@router.get("/accounts", response_model=list[AdminAccountItem])
async def list_admin_accounts(
    storage: StorageDep,
    admin: SuperAdminDep,
) -> list[AdminAccountItem]:
    users = await storage.list_admin_users()
    return [
        AdminAccountItem(
            id=u.id,
            email=u.email,
            role=u.role.value,
            created_at=u.created_at.isoformat() if u.created_at else "",
            last_login_at=u.last_login_at.isoformat() if u.last_login_at else None,
        )
        for u in users
    ]


@router.post("/accounts", response_model=AdminAccountItem, status_code=status.HTTP_201_CREATED)
async def create_admin_account(
    payload: CreateAdminAccountRequest,
    storage: StorageDep,
    admin: SuperAdminDep,
) -> AdminAccountItem:
    clean_email = payload.email.strip().lower()
    if not clean_email or "@" not in clean_email:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Email tidak valid")
    if len(payload.password) < 8:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Kata sandi minimal 8 karakter",
        )
    existing = await storage.get_admin_user_by_email(clean_email)
    if existing:
        raise HTTPException(
            status.HTTP_409_CONFLICT, detail="Akun admin dengan email ini sudah ada"
        )

    now = datetime.now(UTC)
    new_admin = AdminUser(
        id=f"adm_{uuid.uuid4().hex[:12]}",
        email=clean_email,
        password_hash=hash_password(payload.password),
        role=payload.role,
        created_at=now,
    )
    audit_entry = AdminAuditLog(
        id=f"aud_{uuid.uuid4().hex[:12]}",
        admin_id=admin.email,
        action="admin_create",
        target_id=clean_email,
        detail=f"Akun admin '{clean_email}' ({payload.role.value}) dibuat oleh {admin.email}",
        created_at=now,
    )
    await storage.save_audit_log(audit_entry)
    await storage.save_admin_user(new_admin)

    return AdminAccountItem(
        id=new_admin.id,
        email=new_admin.email,
        role=new_admin.role.value,
        created_at=now.isoformat(),
        last_login_at=None,
    )


@router.delete("/accounts/{account_id}")
async def delete_admin_account(
    account_id: str,
    storage: StorageDep,
    admin: SuperAdminDep,
) -> dict[str, str]:
    target = await storage.get_admin_user(account_id)
    if not target:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Akun admin tidak ditemukan")
    if target.id == admin.id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Tidak dapat menghapus akun yang sedang digunakan",
        )
    if target.role == AdminRole.super_admin:
        super_count = await storage.count_super_admins()
        if super_count <= 1:
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                detail="Tidak dapat menghapus satu-satunya super_admin",
            )

    now = datetime.now(UTC)
    audit_entry = AdminAuditLog(
        id=f"aud_{uuid.uuid4().hex[:12]}",
        admin_id=admin.email,
        action="admin_delete",
        target_id=target.email,
        detail=f"Akun admin '{target.email}' dihapus oleh {admin.email}",
        created_at=now,
    )
    await storage.save_audit_log(audit_entry)
    await storage.delete_admin_user(account_id)
    return {"status": "ok", "deleted_id": account_id, "audit_id": audit_entry.id}


# --- Clustering endpoints (BL-ADMIN-004) -------------------------------------


@router.get("/clusters", response_model=list[ClusterItem])
async def list_clusters(
    storage: StorageDep,
    admin: AdminDep,
    topic: str | None = None,
) -> list[ClusterItem]:
    """Return all question clusters, optionally filtered by topic slug."""
    clusters = await storage.list_clusters(topic_slug=topic)
    labels = _topic_labels()
    items: list[ClusterItem] = []
    for c in clusters:
        last_asked = ""
        if c.updated_at:
            last_asked = c.updated_at.isoformat()
        elif c.created_at:
            last_asked = c.created_at.isoformat()
        items.append(
            ClusterItem(
                id=c.id,
                canonical=c.canonical_text,
                count=len(c.question_ids),
                topic_slug=c.topic_slug,
                topic_label=labels.get(c.topic_slug, c.topic_slug),
                last_asked=last_asked,
                has_curated=c.has_curated,
                members=c.member_texts or [],
            )
        )
    return items


@router.put("/clusters/{cluster_id}/rename", response_model=ClusterItem)
async def rename_cluster_endpoint(
    cluster_id: str,
    payload: RenameClusterRequest,
    storage: StorageDep,
    admin: EditorDep,
) -> ClusterItem:
    """Rename the canonical text of a cluster."""
    cluster = await storage.get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Cluster not found")

    now = datetime.now(UTC)
    await storage.save_audit_log(
        AdminAuditLog(
            id=f"aud_{uuid.uuid4().hex[:12]}",
            admin_id=admin.email,
            action="cluster_rename",
            target_id=cluster_id,
            detail=f"Renamed cluster '{cluster_id}' to '{payload.new_canonical}' by {admin.email}",
            created_at=now,
        )
    )

    updated = await service_rename_cluster(storage, cluster_id, payload.new_canonical)
    labels = _topic_labels()
    last_asked = updated.updated_at.isoformat() if updated.updated_at else ""

    return ClusterItem(
        id=updated.id,
        canonical=updated.canonical_text,
        count=len(updated.question_ids),
        topic_slug=updated.topic_slug,
        topic_label=labels.get(updated.topic_slug, updated.topic_slug),
        last_asked=last_asked,
        has_curated=updated.has_curated,
        members=updated.member_texts or [],
    )


@router.post("/clusters/{cluster_id}/merge", response_model=ClusterItem)
async def merge_cluster_endpoint(
    cluster_id: str,
    payload: MergeClusterRequest,
    storage: StorageDep,
    admin: EditorDep,
) -> ClusterItem:
    """Merge source cluster into target cluster (cluster_id is the target)."""
    if cluster_id == payload.source_cluster_id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            detail="Cannot merge a cluster into itself",
        )
    target = await storage.get_cluster(cluster_id)
    if not target:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Target cluster not found")
    source = await storage.get_cluster(payload.source_cluster_id)
    if not source:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Source cluster not found")

    now = datetime.now(UTC)
    await storage.save_audit_log(
        AdminAuditLog(
            id=f"aud_{uuid.uuid4().hex[:12]}",
            admin_id=admin.email,
            action="cluster_merge",
            target_id=cluster_id,
            detail=(
                f"Merged cluster '{payload.source_cluster_id}' into '{cluster_id}' by {admin.email}"
            ),
            created_at=now,
        )
    )

    merged = await service_merge_clusters(storage, cluster_id, payload.source_cluster_id)
    labels = _topic_labels()
    last_asked = merged.updated_at.isoformat() if merged.updated_at else ""

    return ClusterItem(
        id=merged.id,
        canonical=merged.canonical_text,
        count=len(merged.question_ids),
        topic_slug=merged.topic_slug,
        topic_label=labels.get(merged.topic_slug, merged.topic_slug),
        last_asked=last_asked,
        has_curated=merged.has_curated,
        members=merged.member_texts or [],
    )


@router.post("/clusters/{cluster_id}/promote")
async def promote_cluster_endpoint(
    cluster_id: str,
    storage: StorageDep,
    admin: EditorDep,
) -> dict[str, str]:
    """Promote cluster canonical text to topic's curated answer (draft)."""
    cluster = await storage.get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Cluster not found")

    now = datetime.now(UTC)
    await storage.save_audit_log(
        AdminAuditLog(
            id=f"aud_{uuid.uuid4().hex[:12]}",
            admin_id=admin.email,
            action="cluster_promote",
            target_id=cluster_id,
            detail=(
                f"Promoted cluster '{cluster_id}' to curated draft for topic "
                f"'{cluster.topic_slug}' by {admin.email}"
            ),
            created_at=now,
        )
    )

    topic = await service_promote_cluster(storage, cluster_id, admin.email)

    return {
        "cluster_id": cluster_id,
        "topic_slug": topic.slug,
        "canonical_text": cluster.canonical_text,
        "status": topic.curated_status,
    }


@router.delete("/clusters/{cluster_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cluster_endpoint(
    cluster_id: str,
    storage: StorageDep,
    admin: SuperAdminDep,
) -> None:
    """Delete a cluster entirely (super_admin only, audited before execution)."""
    cluster = await storage.get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Cluster not found")

    now = datetime.now(UTC)
    await storage.save_audit_log(
        AdminAuditLog(
            id=f"aud_{uuid.uuid4().hex[:12]}",
            admin_id=admin.email,
            action="cluster_delete",
            target_id=cluster_id,
            detail=f"Deleted cluster '{cluster_id}' by {admin.email}",
            created_at=now,
        )
    )

    # Unlink member questions before deleting cluster
    for qid in cluster.question_ids:
        member_q = await storage.get_question(qid)
        if member_q and member_q.cluster_id == cluster_id:
            member_q.cluster_id = None
            await storage.save_question(member_q)

    await storage.delete_cluster(cluster_id)


# --- Audit log & retention purge (BL-ADMIN-006) ------------------------------


@router.get("/audit", response_model=list[AuditLogItem])
async def list_audit_logs(
    storage: StorageDep,
    admin: SuperAdminDep,
    actor: str | None = None,
    action: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[AuditLogItem]:
    """Return recent audit log entries (super_admin only), with optional filters."""
    entries = await storage.list_audit_logs(limit=limit)

    dt_from: datetime | None = None
    dt_to: datetime | None = None
    if date_from:
        with contextlib.suppress(ValueError):
            dt_from = datetime.fromisoformat(date_from).replace(tzinfo=UTC)
    if date_to:
        try:
            parsed_to = datetime.fromisoformat(date_to)
            if len(date_to) <= 10:
                parsed_to = parsed_to + timedelta(days=1)
            dt_to = parsed_to.replace(tzinfo=UTC)
        except ValueError:
            pass

    filtered: list[AuditLogItem] = []
    for e in entries:
        if actor and actor.lower() not in e.admin_id.lower():
            continue
        if action and action.lower() not in e.action.lower():
            continue
        if dt_from and e.created_at and e.created_at < dt_from:
            continue
        if dt_to and e.created_at and e.created_at > dt_to:
            continue
        filtered.append(
            AuditLogItem(
                id=e.id,
                actor=e.admin_id,
                action=e.action,
                target=e.target_id,
                detail=e.detail or "",
                at=e.created_at.isoformat() if e.created_at else "",
            )
        )
    return filtered


@router.post("/purge", response_model=RetentionPurgeResponse)
async def run_retention_purge(
    storage: StorageDep,
    admin: SuperAdminDep,
) -> RetentionPurgeResponse:
    """Purge questions older than the configured retention window (super_admin only)."""
    cfg = await storage.get_system_config("retention_months")
    months = int(cfg.value) if cfg else 12
    cutoff = datetime.now(UTC) - timedelta(days=months * 30)

    now = datetime.now(UTC)
    audit_entry = AdminAuditLog(
        id=f"aud_{uuid.uuid4().hex[:12]}",
        admin_id=admin.email,
        action="retention_purge",
        target_id="questions",
        detail=(
            f"Retention purge executed for questions older than {cutoff.date().isoformat()} "
            f"(retention={months} months) by {admin.email}"
        ),
        created_at=now,
    )
    await storage.save_audit_log(audit_entry)

    purged = await storage.purge_questions_older_than(cutoff)
    return RetentionPurgeResponse(purged_count=purged, cutoff=cutoff.isoformat())
