"""Tests for BL-ADMIN-006: Audit log and retention purge endpoints."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from httpx import AsyncClient

from models import AdminUser, Question, QuestionCluster, SystemConfig, Topic
from models.enums import AdminRole, AnswerSource
from services.admin_auth import create_access_token, hash_password
from storage.memory import MemoryStorage

pytestmark = pytest.mark.asyncio


async def _create_admin(storage: MemoryStorage, role: AdminRole = AdminRole.super_admin) -> str:
    user = AdminUser(
        id="adm_audit_test",
        email="superadmin@tanyaiman.id",
        password_hash=hash_password("TestSecret123!"),
        role=role,
        created_at=datetime.now(UTC),
    )
    await storage.save_admin_user(user)
    return create_access_token(user)


async def _create_editor(storage: MemoryStorage) -> str:
    user = AdminUser(
        id="adm_editor_test",
        email="editor@tanyaiman.id",
        password_hash=hash_password("TestSecret123!"),
        role=AdminRole.editor,
        created_at=datetime.now(UTC),
    )
    await storage.save_admin_user(user)
    return create_access_token(user)


# ---------------------------------------------------------------------------
# Audit log written on curated answer update
# ---------------------------------------------------------------------------


async def test_audit_log_written_on_curated_answer_update(
    client: AsyncClient, storage: MemoryStorage
) -> None:
    """Updating a curated answer must write an audit log entry."""
    token = await _create_editor(storage)
    headers = {"Authorization": f"Bearer {token}"}

    # Seed topic
    await storage.save_topic(
        Topic(slug="baptis", name_id="Baptisan", name_en="Baptism", question_count=1, like_count=0)
    )

    payload = {
        "answer_text": "Baptisan adalah tanda perjanjian dengan Allah yang dilaksanakan melalui air.",
        "status": "draft",
        "citations": [],
    }
    resp = await client.put("/api/admin/topics/baptis/answer", json=payload, headers=headers)
    assert resp.status_code == 200, f"PUT failed: {resp.text}"

    # Verify audit log was saved in the shared storage
    logs = await storage.list_audit_logs()
    assert len(logs) >= 1
    last = logs[-1]
    assert last.action == "topic_answer_draft"
    assert last.target_id == "baptis"
    assert "baptis" in (last.detail or "")


# ---------------------------------------------------------------------------
# GET /audit requires super_admin
# ---------------------------------------------------------------------------


async def test_audit_list_requires_super_admin(client: AsyncClient, storage: MemoryStorage) -> None:
    """Editor should NOT be able to list audit logs."""
    editor_token = await _create_editor(storage)
    resp = await client.get(
        "/api/admin/audit", headers={"Authorization": f"Bearer {editor_token}"}
    )
    assert resp.status_code == 403


async def test_audit_list_returns_entries(client: AsyncClient, storage: MemoryStorage) -> None:
    """Super-admin can fetch audit log entries via GET /audit."""
    token = await _create_admin(storage)
    headers = {"Authorization": f"Bearer {token}"}

    # Seed topic and write curated answer as draft (triggers audit log internally)
    await storage.save_topic(
        Topic(slug="doa", name_id="Doa", name_en="Prayer", question_count=2, like_count=0)
    )
    payload = {
        "answer_text": "Doa adalah komunikasi langsung dengan Tuhan.",
        "status": "draft",
        "citations": [],
    }
    put_resp = await client.put(
        "/api/admin/topics/doa/answer",
        json=payload,
        headers=headers,
    )
    assert put_resp.status_code == 200, f"PUT failed: {put_resp.text}"

    resp = await client.get("/api/admin/audit", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) >= 1

    entry = data[0]
    assert "id" in entry
    assert "actor" in entry
    assert "action" in entry
    assert "target" in entry
    assert "at" in entry


# ---------------------------------------------------------------------------
# Retention purge
# ---------------------------------------------------------------------------


async def test_retention_purge_removes_old_questions(
    client: AsyncClient, storage: MemoryStorage
) -> None:
    """POST /purge should delete questions older than the retention window."""
    token = await _create_admin(storage)
    headers = {"Authorization": f"Bearer {token}"}

    # Seed: 2 old questions (14 months ago), 1 recent question
    old_ts = datetime.now(UTC) - timedelta(days=430)
    recent_ts = datetime.now(UTC) - timedelta(days=5)

    for i in range(2):
        await storage.save_question(
            Question(
                id=f"q_old_{i}",
                session_id="sess_old",
                uid="uid_old",
                question_text=f"Pertanyaan lama {i}",
                answer_text="Jawaban lama.",
                topic_slug="baptis",
                answer_source=AnswerSource.generated,
                created_at=old_ts,
            )
        )

    await storage.save_question(
        Question(
            id="q_recent_1",
            session_id="sess_new",
            uid="uid_new",
            question_text="Pertanyaan baru",
            answer_text="Jawaban baru.",
            topic_slug="baptis",
            answer_source=AnswerSource.curated,
            created_at=recent_ts,
        )
    )

    # Set retention to 12 months (so >12 months = purge)
    await storage.set_system_config(
        SystemConfig(
            key="retention_months",
            value="12",
            updated_by="test",
            updated_at=datetime.now(UTC),
        )
    )

    resp = await client.post("/api/admin/purge", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["purged_count"] == 2
    assert "cutoff" in data

    # Recent question still exists
    remaining = await storage.list_questions()
    remaining_ids = [q.id for q in remaining]
    assert "q_recent_1" in remaining_ids
    assert "q_old_0" not in remaining_ids
    assert "q_old_1" not in remaining_ids

    # Audit log for purge was recorded
    logs = await storage.list_audit_logs()
    purge_logs = [lg for lg in logs if lg.action == "retention_purge"]
    assert len(purge_logs) >= 1


async def test_retention_purge_requires_super_admin(
    client: AsyncClient, storage: MemoryStorage
) -> None:
    """Editor should NOT be allowed to trigger a retention purge."""
    editor_token = await _create_editor(storage)
    resp = await client.post(
        "/api/admin/purge", headers={"Authorization": f"Bearer {editor_token}"}
    )
    assert resp.status_code == 403


# ---------------------------------------------------------------------------
# Cluster operations create audit entries
# ---------------------------------------------------------------------------


async def test_cluster_rename_creates_audit_entry(
    client: AsyncClient, storage: MemoryStorage
) -> None:
    """Renaming a cluster via PUT /clusters/{id}/rename must write an audit entry."""
    token = await _create_admin(storage)
    headers = {"Authorization": f"Bearer {token}"}

    # Seed a cluster directly in storage
    now = datetime.now(UTC)
    cluster = QuestionCluster(
        id="clus_test_1",
        topic_slug="baptis",
        canonical_text="Bagaimana cara baptis?",
        question_ids=["q1", "q2"],
        member_texts=["Bagaimana cara baptis?", "Cara dibaptis gimana?"],
        centroid=[0.1] * 768,
        created_at=now,
        updated_at=now,
    )
    await storage.save_cluster(cluster)

    resp = await client.put(
        "/api/admin/clusters/clus_test_1/rename",
        json={"new_canonical": "Bagaimana proses baptisan dilakukan?"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["canonical"] == "Bagaimana proses baptisan dilakukan?"

    logs = await storage.list_audit_logs()
    rename_logs = [lg for lg in logs if lg.action == "cluster_rename"]
    assert len(rename_logs) >= 1
    assert "clus_test_1" in rename_logs[-1].detail


async def test_cluster_promote_creates_audit_entry(
    client: AsyncClient, storage: MemoryStorage
) -> None:
    """Promoting a cluster must write an audit entry and set topic curated_answer to draft."""
    token = await _create_admin(storage)
    headers = {"Authorization": f"Bearer {token}"}

    await storage.save_topic(
        Topic(slug="ibadah", name_id="Ibadah", name_en="Worship", question_count=3, like_count=0)
    )

    now = datetime.now(UTC)
    cluster = QuestionCluster(
        id="clus_ibadah_1",
        topic_slug="ibadah",
        canonical_text="Apa itu ibadah Kristen?",
        question_ids=["qa", "qb"],
        member_texts=["Apa itu ibadah?", "Ibadah itu apa?"],
        centroid=[0.2] * 768,
        created_at=now,
        updated_at=now,
    )
    await storage.save_cluster(cluster)

    resp = await client.post("/api/admin/clusters/clus_ibadah_1/promote", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "draft"
    assert data["topic_slug"] == "ibadah"

    # Topic curated_answer updated
    topic = await storage.get_topic("ibadah")
    assert topic is not None
    assert topic.curated_answer == "Apa itu ibadah Kristen?"
    assert topic.curated_status == "draft"

    # Audit entry created
    logs = await storage.list_audit_logs()
    promote_logs = [lg for lg in logs if lg.action == "cluster_promote"]
    assert len(promote_logs) >= 1
