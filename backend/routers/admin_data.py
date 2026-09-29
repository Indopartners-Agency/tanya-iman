"""Admin data API endpoints (Wave 7 / Phase 6).

Serves live analytics, question streams, topic details, curated answer
editing with validation, content gaps, and system configuration.
"""

from __future__ import annotations

import logging
import uuid
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from config.loader import topics as get_canonical_topics
from engine.validators import ComplianceValidator
from models import AdminAuditLog, AdminUser, Citation, SystemConfig
from models.enums import AdminRole, ValidatorCode
from routers.admin_auth import require_admin
from routers.deps import StorageDep
from services.clustering import (
    merge_clusters as service_merge_clusters,
)
from services.clustering import (
    promote_cluster_to_curated as service_promote_cluster,
)
from services.clustering import (
    rename_cluster as service_rename_cluster,
)

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

    # Record audit log (F-37)
    audit_entry = AdminAuditLog(
        id=f"aud_{uuid.uuid4().hex[:12]}",
        admin_id=admin.id,
        action=f"topic_answer_{payload.status}",
        target_id=slug,
        detail=f"Updated curated answer for topic '{slug}' ({payload.status}) by {admin.email}",
        created_at=now,
    )
    await storage.save_audit_log(audit_entry)

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

    updated = await service_rename_cluster(storage, cluster_id, payload.new_canonical)
    labels = _topic_labels()
    last_asked = updated.updated_at.isoformat() if updated.updated_at else ""

    # Audit
    now = datetime.now(UTC)
    await storage.save_audit_log(
        AdminAuditLog(
            id=f"aud_{uuid.uuid4().hex[:12]}",
            admin_id=admin.id,
            action="cluster_rename",
            target_id=cluster_id,
            detail=f"Renamed cluster '{cluster_id}' to '{payload.new_canonical}' by {admin.email}",
            created_at=now,
        )
    )

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
    target = await storage.get_cluster(cluster_id)
    if not target:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Target cluster not found")
    source = await storage.get_cluster(payload.source_cluster_id)
    if not source:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Source cluster not found")

    merged = await service_merge_clusters(storage, cluster_id, payload.source_cluster_id)
    labels = _topic_labels()
    last_asked = merged.updated_at.isoformat() if merged.updated_at else ""

    now = datetime.now(UTC)
    await storage.save_audit_log(
        AdminAuditLog(
            id=f"aud_{uuid.uuid4().hex[:12]}",
            admin_id=admin.id,
            action="cluster_merge",
            target_id=cluster_id,
            detail=(
                f"Merged cluster '{payload.source_cluster_id}' into '{cluster_id}' by {admin.email}"
            ),
            created_at=now,
        )
    )

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

    topic = await service_promote_cluster(storage, cluster_id, admin.email)

    now = datetime.now(UTC)
    await storage.save_audit_log(
        AdminAuditLog(
            id=f"aud_{uuid.uuid4().hex[:12]}",
            admin_id=admin.id,
            action="cluster_promote",
            target_id=cluster_id,
            detail=(
                f"Promoted cluster '{cluster_id}' to curated draft for topic "
                f"'{cluster.topic_slug}' by {admin.email}"
            ),
            created_at=now,
        )
    )

    return {"cluster_id": cluster_id, "topic_slug": topic.slug, "status": "draft"}


@router.delete("/clusters/{cluster_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_cluster_endpoint(
    cluster_id: str,
    storage: StorageDep,
    admin: SuperAdminDep,
) -> None:
    """Delete a cluster entirely (super_admin only)."""
    cluster = await storage.get_cluster(cluster_id)
    if not cluster:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Cluster not found")
    await storage.delete_cluster(cluster_id)

    now = datetime.now(UTC)
    await storage.save_audit_log(
        AdminAuditLog(
            id=f"aud_{uuid.uuid4().hex[:12]}",
            admin_id=admin.id,
            action="cluster_delete",
            target_id=cluster_id,
            detail=f"Deleted cluster '{cluster_id}' by {admin.email}",
            created_at=now,
        )
    )


# --- Audit log & retention purge (BL-ADMIN-006) ------------------------------


@router.get("/audit", response_model=list[AuditLogItem])
async def list_audit_logs(
    storage: StorageDep,
    admin: SuperAdminDep,
    limit: int = Query(default=100, ge=1, le=500),
) -> list[AuditLogItem]:
    """Return recent audit log entries (super_admin only)."""
    entries = await storage.list_audit_logs(limit=limit)
    return [
        AuditLogItem(
            id=e.id,
            actor=e.admin_id,
            action=e.action,
            target=e.target_id,
            detail=e.detail or "",
            at=e.created_at.isoformat() if e.created_at else "",
        )
        for e in entries
    ]


@router.post("/purge", response_model=RetentionPurgeResponse)
async def run_retention_purge(
    storage: StorageDep,
    admin: SuperAdminDep,
) -> RetentionPurgeResponse:
    """Purge questions older than the configured retention window (super_admin only)."""
    # Read retention months from config (default: 12)
    cfg = await storage.get_system_config("retention_months")
    months = int(cfg.value) if cfg else 12
    cutoff = datetime.now(UTC) - timedelta(days=months * 30)

    purged = await storage.purge_questions_older_than(cutoff)

    now = datetime.now(UTC)
    await storage.save_audit_log(
        AdminAuditLog(
            id=f"aud_{uuid.uuid4().hex[:12]}",
            admin_id=admin.id,
            action="retention_purge",
            target_id="questions",
            detail=(
                f"Purged {purged} questions older than {cutoff.date().isoformat()} "
                f"(retention={months} months) by {admin.email}"
            ),
            created_at=now,
        )
    )

    return RetentionPurgeResponse(purged_count=purged, cutoff=cutoff.isoformat())
