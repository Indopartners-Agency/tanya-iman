from __future__ import annotations

from datetime import UTC, datetime

import pytest
from httpx import AsyncClient

from models import AdminUser, Question, Topic
from models.enums import AdminRole, AnswerSource
from services.admin_auth import create_access_token, hash_password
from storage.memory import MemoryStorage

pytestmark = pytest.mark.asyncio


async def _create_admin(storage: MemoryStorage, role: AdminRole = AdminRole.super_admin) -> str:
    user = AdminUser(
        id="adm_test",
        email="testadmin@tanyaiman.id",
        password_hash=hash_password("TestSecret123!"),
        role=role,
        created_at=datetime.now(UTC),
    )
    await storage.save_admin_user(user)
    return create_access_token(user)


async def test_admin_data_unauthorized(client: AsyncClient):
    resp = await client.get("/api/admin/dashboard")
    assert resp.status_code == 401

    resp = await client.get("/api/admin/topics")
    assert resp.status_code == 401

    resp = await client.get("/api/admin/questions")
    assert resp.status_code == 401


async def test_admin_dashboard_and_topics(client: AsyncClient, storage: MemoryStorage):
    token = await _create_admin(storage, AdminRole.super_admin)
    headers = {"Authorization": f"Bearer {token}"}

    # Seed topics and questions
    await storage.save_topic(
        Topic(slug="baptis", name_id="Baptisan", name_en="Baptism", question_count=5, like_count=2)
    )
    await storage.save_question(
        Question(
            id="q_test_1",
            session_id="sess_1",
            uid="uid_1",
            question_text="Bagaimana cara dibaptis?",
            answer_text="Melalui baptisan air.",
            topic_slug="baptis",
            answer_source=AnswerSource.curated,
            like_count=2,
            has_grounding=True,
            created_at=datetime.now(UTC),
        )
    )

    # 1. Test Dashboard
    dash_resp = await client.get("/api/admin/dashboard", headers=headers)
    assert dash_resp.status_code == 200
    dash_data = dash_resp.json()
    assert dash_data["total_questions"] >= 1
    assert dash_data["active_topics"] >= 1
    assert len(dash_data["top_topics"]) >= 1

    # 2. Test Topics List
    topics_resp = await client.get("/api/admin/topics", headers=headers)
    assert topics_resp.status_code == 200
    topics_data = topics_resp.json()
    assert any(t["slug"] == "baptis" for t in topics_data)

    # 3. Test Topic Detail
    detail_resp = await client.get("/api/admin/topics/baptis", headers=headers)
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert detail_data["slug"] == "baptis"
    assert detail_data["label"] == "Baptisan"

    # 4. Test Update Curated Answer
    update_resp = await client.put(
        "/api/admin/topics/baptis/answer",
        headers=headers,
        json={
            "answer_text": (
                "Baptisan adalah sakramen inisiasi yang kudus di mana orang percaya "
                "mengaku imannya kepada Allah dan menerima anugerah hidup yang baru "
                "menurut ajaran para rasul yang sejati dan damai."
            ),
            "status": "published",
            "citations": [],
        },
    )
    assert update_resp.status_code == 200
    updated_topic = update_resp.json()
    assert updated_topic["curated"] == "published"
    assert "Baptisan adalah" in updated_topic["curated_answer"]


async def test_admin_questions_and_gaps(client: AsyncClient, storage: MemoryStorage):
    token = await _create_admin(storage, AdminRole.super_admin)
    headers = {"Authorization": f"Bearer {token}"}

    q1 = Question(
        id="q_101",
        session_id="sess_101",
        uid="uid_101",
        question_text="Apa itu keselamatan?",
        answer_text="Keselamatan melalui kasih karunia.",
        topic_slug="keselamatan",
        answer_source=AnswerSource.generated,
        has_grounding=False,
        created_at=datetime.now(UTC),
    )
    await storage.save_question(q1)

    # 1. List questions
    q_resp = await client.get("/api/admin/questions", headers=headers)
    assert q_resp.status_code == 200
    q_data = q_resp.json()
    assert any(item["id"] == "q_101" for item in q_data)

    # 2. Question detail
    detail_resp = await client.get("/api/admin/questions/q_101", headers=headers)
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert detail_data["question"] == "Apa itu keselamatan?"

    # 3. Gaps
    gap_resp = await client.get("/api/admin/gaps", headers=headers)
    assert gap_resp.status_code == 200
    gaps_data = gap_resp.json()
    assert any(item["id"] == "q_101" for item in gaps_data)


async def test_admin_config(client: AsyncClient, storage: MemoryStorage):
    token = await _create_admin(storage, AdminRole.super_admin)
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Update config
    put_resp = await client.put(
        "/api/admin/config/contact_name",
        headers=headers,
        params={"value": "Konselor Iman"},
    )
    assert put_resp.status_code == 200

    # 2. Get configs
    get_resp = await client.get("/api/admin/config", headers=headers)
    assert get_resp.status_code == 200
    cfg_data = get_resp.json()
    assert cfg_data.get("contact_name") == "Konselor Iman"
