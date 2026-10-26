from __future__ import annotations

from datetime import UTC, datetime

import pytest
from httpx import AsyncClient

from models import AdminUser, Question, QuestionCluster, Topic
from models.enums import AdminRole, AnswerSource, ValidatorCode
from services.admin_auth import create_access_token, hash_password
from storage.memory import MemoryStorage

pytestmark = pytest.mark.asyncio


async def _create_admin(
    storage: MemoryStorage,
    role: AdminRole = AdminRole.super_admin,
    user_id: str = "adm_test",
) -> str:
    user = AdminUser(
        id=user_id,
        email=f"{user_id}@tanyaiman.id",
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

    # 4. Test Update Curated Answer (publishing with 0 citations fails V4; valid citation succeeds)
    no_cit_resp = await client.put(
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
    assert no_cit_resp.status_code == 422
    assert "V4_CITATION_COUNT" in no_cit_resp.json()["detail"]

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
            "citations": [
                {
                    "title": "Baptisan dalam Injil",
                    "url": "https://isadanislam.org/baptisan",
                    "site": "isadanislam.org",
                }
            ],
        },
    )
    assert update_resp.status_code == 200
    updated_topic = update_resp.json()
    assert updated_topic["curated"] == "published"
    assert "Baptisan adalah" in updated_topic["curated_answer"]
    assert len(updated_topic["curated_citations"]) == 1


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

    # 2. Question detail with diagnostics
    detail_resp = await client.get("/api/admin/questions/q_101", headers=headers)
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert detail_data["question"] == "Apa itu keselamatan?"
    assert "retrieved_chunks" in detail_data
    assert "validators" in detail_data
    assert len(detail_data["validators"]) == 5
    assert any(v["code"] == "V1" and v["pass"] is True for v in detail_data["validators"])

    # 3. Gaps
    gap_resp = await client.get("/api/admin/gaps", headers=headers)
    assert gap_resp.status_code == 200
    gaps_data = gap_resp.json()
    assert any(item["id"] == "q_101" for item in gaps_data)


async def test_admin_delete_question(client: AsyncClient, storage: MemoryStorage):
    token = await _create_admin(storage, AdminRole.super_admin)
    headers = {"Authorization": f"Bearer {token}"}

    q = Question(
        id="q_delete_target",
        session_id="sess_del",
        uid="uid_del",
        question_text="Pertanyaan untuk dihapus",
        answer_text="Jawaban",
        topic_slug="keselamatan",
        answer_source=AnswerSource.generated,
        created_at=datetime.now(UTC),
    )
    await storage.save_question(q)

    # 1. Non super_admin is rejected
    editor_token = await _create_admin(storage, AdminRole.editor, user_id="adm_editor")
    forbidden_resp = await client.delete(
        "/api/admin/questions/q_delete_target",
        headers={"Authorization": f"Bearer {editor_token}"},
    )
    assert forbidden_resp.status_code == 403

    # 2. Super_admin deletes successfully
    del_resp = await client.delete("/api/admin/questions/q_delete_target", headers=headers)
    assert del_resp.status_code == 200
    assert del_resp.json()["deleted_id"] == "q_delete_target"
    assert "audit_id" in del_resp.json()

    # Verify deleted from storage
    assert await storage.get_question("q_delete_target") is None

    # Verify audit log recorded
    logs = await storage.list_audit_logs()
    assert any(
        log.action == "delete_question" and log.target_id == "q_delete_target" for log in logs
    )


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


async def test_admin_question_detail_validator_failures(
    client: AsyncClient, storage: MemoryStorage
):
    token = await _create_admin(storage, AdminRole.super_admin)
    headers = {"Authorization": f"Bearer {token}"}

    q = Question(
        id="q_fail_diag",
        session_id="sess_fail",
        uid="uid_fail",
        question_text="Siapakah Isa Al-Masih?",
        answer_text="Jawaban singkat Yesus",
        topic_slug="keselamatan",
        answer_source=AnswerSource.generated,
        validator_failures=[
            ValidatorCode.v1_too_short,
            ValidatorCode.v2_forbidden_term,
        ],
        has_grounding=True,
        created_at=datetime.now(UTC),
    )
    await storage.save_question(q)

    resp = await client.get("/api/admin/questions/q_fail_diag", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    validators = {v["code"]: v["pass"] for v in data["validators"]}
    assert validators["V1"] is False  # v1_too_short failed
    assert validators["V2"] is False  # v2_forbidden_term failed
    assert validators["V3"] is True
    assert validators["V4"] is True
    assert data["repair"]["attempted"] is True
    assert data["repair"]["succeeded"] is False

    # Repaired question shows V1-V5 pass=True and repair.succeeded=True
    q_repaired = Question(
        id="q_repaired_ok",
        session_id="sess_rep",
        uid="uid_rep",
        question_text="Siapakah Isa Al-Masih?",
        answer_text=(
            "Isa Al-Masih adalah Kalimat Allah dan Roh daripada-Nya yang membawa kasih karunia, "
            "pengampunan dosa, serta keselamatan yang kekal bagi setiap orang yang percaya "
            "kepada Allah dengan segenap hati."
        ),
        topic_slug="keselamatan",
        answer_source=AnswerSource.generated,
        validator_failures=[ValidatorCode.v1_too_short],
        initial_validator_failures=[ValidatorCode.v1_too_short],
        repair_attempted=True,
        has_grounding=True,
        created_at=datetime.now(UTC),
    )
    await storage.save_question(q_repaired)
    rep_resp = await client.get("/api/admin/questions/q_repaired_ok", headers=headers)
    assert rep_resp.status_code == 200
    rep_data = rep_resp.json()
    rep_validators = {v["code"]: v["pass"] for v in rep_data["validators"]}
    assert all(rep_validators.values())
    assert rep_data["repair"]["attempted"] is True
    assert rep_data["repair"]["succeeded"] is True
    assert rep_data["repair"]["initial_failures"] == ["V1_TOO_SHORT"]
    assert rep_data["repair"]["final_failures"] == []


async def test_admin_delete_question_cluster_cleanup(client: AsyncClient, storage: MemoryStorage):
    token = await _create_admin(storage, AdminRole.super_admin)
    headers = {"Authorization": f"Bearer {token}"}

    now = datetime.now(UTC)
    cluster = QuestionCluster(
        id="cl_cleanup_test",
        topic_slug="keselamatan",
        canonical_text="Pertanyaan Satu",
        question_ids=["q_c1", "q_c2"],
        member_texts=["Pertanyaan Satu", "Pertanyaan Dua"],
        created_at=now,
        updated_at=now,
    )
    await storage.save_cluster(cluster)

    q1 = Question(
        id="q_c1",
        session_id="s1",
        uid="u1",
        question_text="Pertanyaan Satu",
        topic_slug="keselamatan",
        cluster_id="cl_cleanup_test",
        answer_source=AnswerSource.generated,
        created_at=now,
    )
    q2 = Question(
        id="q_c2",
        session_id="s2",
        uid="u2",
        question_text="Pertanyaan Dua",
        topic_slug="keselamatan",
        cluster_id="cl_cleanup_test",
        answer_source=AnswerSource.generated,
        created_at=now,
    )
    await storage.save_question(q1)
    await storage.save_question(q2)

    # 1. Delete canonical question q_c1
    del_resp1 = await client.delete("/api/admin/questions/q_c1", headers=headers)
    assert del_resp1.status_code == 200

    # Cluster should now have canonical updated to q_c2 and count = 1
    c_updated = await storage.get_cluster("cl_cleanup_test")
    assert c_updated is not None
    assert c_updated.question_ids == ["q_c2"]
    assert c_updated.member_texts == ["Pertanyaan Dua"]
    assert c_updated.canonical_text == "Pertanyaan Dua"

    # 2. Delete remaining question q_c2
    del_resp2 = await client.delete("/api/admin/questions/q_c2", headers=headers)
    assert del_resp2.status_code == 200

    # Cluster should be deleted completely since it has no remaining members
    assert await storage.get_cluster("cl_cleanup_test") is None


async def test_admin_cluster_merge_and_self_merge_guard(
    client: AsyncClient, storage: MemoryStorage
):
    token = await _create_admin(storage, AdminRole.editor)
    headers = {"Authorization": f"Bearer {token}"}

    now = datetime.now(UTC)
    c1 = QuestionCluster(
        id="cl_target",
        topic_slug="keselamatan",
        canonical_text="Target Kanonikal",
        question_ids=["q_t1"],
        member_texts=["Target Kanonikal"],
        centroid=[0.5] * 768,
        created_at=now,
        updated_at=now,
    )
    c2 = QuestionCluster(
        id="cl_source",
        topic_slug="keselamatan",
        canonical_text="Source Kanonikal",
        question_ids=["q_s1"],
        member_texts=["Source Kanonikal"],
        centroid=[0.8] * 768,
        created_at=now,
        updated_at=now,
    )
    await storage.save_cluster(c1)
    await storage.save_cluster(c2)

    q_s1 = Question(
        id="q_s1",
        session_id="s_src",
        uid="u_src",
        question_text="Source Kanonikal",
        topic_slug="keselamatan",
        cluster_id="cl_source",
        answer_source=AnswerSource.generated,
        created_at=now,
    )
    await storage.save_question(q_s1)

    # 1. Attempt self-merge should fail with 400
    self_merge_resp = await client.post(
        "/api/admin/clusters/cl_target/merge",
        headers=headers,
        json={"source_cluster_id": "cl_target"},
    )
    assert self_merge_resp.status_code == 400

    # 2. Valid merge cl_source into cl_target
    merge_resp = await client.post(
        "/api/admin/clusters/cl_target/merge",
        headers=headers,
        json={"source_cluster_id": "cl_source"},
    )
    assert merge_resp.status_code == 200
    merged_data = merge_resp.json()
    assert merged_data["count"] == 2
    assert "Source Kanonikal" in merged_data["members"]

    # Verify source question pointer updated to target cluster
    q_s1_after = await storage.get_question("q_s1")
    assert q_s1_after is not None
    assert q_s1_after.cluster_id == "cl_target"

    # Verify source cluster deleted
    assert await storage.get_cluster("cl_source") is None


async def test_admin_delete_cluster_unlinks_questions(client: AsyncClient, storage: MemoryStorage):
    token = await _create_admin(storage, AdminRole.super_admin)
    headers = {"Authorization": f"Bearer {token}"}

    now = datetime.now(UTC)
    c = QuestionCluster(
        id="cl_to_del",
        topic_slug="keselamatan",
        canonical_text="Cluster to delete",
        question_ids=["q_linked"],
        member_texts=["Cluster to delete"],
        created_at=now,
        updated_at=now,
    )
    await storage.save_cluster(c)

    q = Question(
        id="q_linked",
        session_id="s_link",
        uid="u_link",
        question_text="Cluster to delete",
        topic_slug="keselamatan",
        cluster_id="cl_to_del",
        answer_source=AnswerSource.generated,
        created_at=now,
    )
    await storage.save_question(q)

    # Delete cluster
    del_resp = await client.delete("/api/admin/clusters/cl_to_del", headers=headers)
    assert del_resp.status_code == 204

    # Verify question's cluster_id is cleared
    q_after = await storage.get_question("q_linked")
    assert q_after is not None
    assert q_after.cluster_id is None


async def test_admin_wave8_curated_validation_and_articles(
    client: AsyncClient, storage: MemoryStorage
):
    from models.schemas import Article

    token = await _create_admin(storage, AdminRole.editor)
    headers = {"Authorization": f"Bearer {token}"}
    now = datetime.now(UTC)

    await storage.save_topic(Topic(slug="doa", name_id="Doa", name_en="Prayer"))
    await storage.save_article(
        Article(
            id="art_doa_1",
            site="isadanislam.org",
            url="https://isadanislam.org/doa-dalam-injil",
            title="Doa dalam Injil",
            content_hash="h1",
            first_seen_at=now,
            last_crawled_at=now,
        )
    )

    # 1. GET /api/admin/articles returns approved articles
    art_resp = await client.get("/api/admin/articles?q=Doa", headers=headers)
    assert art_resp.status_code == 200
    articles = art_resp.json()
    assert len(articles) == 1
    assert articles[0]["site"] == "isadanislam.org"

    # 2. Publishing curated answer with forbidden term "Yesus" or too short fails with 422
    bad_resp = await client.put(
        "/api/admin/topics/doa/answer",
        headers=headers,
        json={
            "answer_text": "Jawaban singkat tentang Yesus.",
            "status": "published",
            "citations": [
                {
                    "title": "Doa dalam Injil",
                    "url": "https://isadanislam.org/doa-dalam-injil",
                    "site": "isadanislam.org",
                }
            ],
        },
    )
    assert bad_resp.status_code == 422

    # 3. Publishing valid 25-250 word answer with Allah/Isa Al-Masih and valid citation succeeds
    valid_text = (
        "Doa adalah sarana komunikasi yang tulus antara umat manusia dengan Allah yang Maha "
        "Pengasih. Melalui ajaran Isa Al-Masih di dalam Kitab Suci, setiap orang diajak untuk "
        "berdoa dengan kerendahan hati, memohon pengampunan, serta mencari petunjuk hidup yang "
        "benar di hadapan Allah setiap hari."
    )
    ok_resp = await client.put(
        "/api/admin/topics/doa/answer",
        headers=headers,
        json={
            "answer_text": valid_text,
            "status": "published",
            "citations": [
                {
                    "title": "Doa dalam Injil",
                    "url": "https://isadanislam.org/doa-dalam-injil",
                    "site": "isadanislam.org",
                }
            ],
        },
    )
    assert ok_resp.status_code == 200
    assert ok_resp.json()["curated"] == "published"


async def test_admin_wave8_gaps_reviews_export_and_settings(
    client: AsyncClient, storage: MemoryStorage
):
    from models.enums import ChunkDecision, Platform, Relevance
    from models.schemas import ArticleChunk, FlaggedChunk

    token = await _create_admin(storage, AdminRole.super_admin)
    headers = {"Authorization": f"Bearer {token}"}
    now = datetime.now(UTC)

    # 1. Seed ungrounded theology questions (duplicate text to verify aggregation) + refusal/crisis
    await storage.save_question(
        Question(
            id="q_gap_a",
            session_id="s1",
            uid="u1",
            question_text="Apa pandangan Kitab Suci tentang mimpi?",
            topic_slug="lainnya",
            answer_source=AnswerSource.no_grounding,
            has_grounding=False,
            channel=Platform.widget,
            created_at=now,
        )
    )
    await storage.save_question(
        Question(
            id="q_gap_b",
            session_id="s2",
            uid="u2",
            question_text="Apa pandangan Kitab Suci tentang mimpi?",
            topic_slug="lainnya",
            answer_source=AnswerSource.no_grounding,
            has_grounding=False,
            channel=Platform.android,
            created_at=now,
        )
    )
    await storage.save_question(
        Question(
            id="q_refusal_not_gap",
            session_id="s3",
            uid="u3",
            question_text="Siapa presiden sekarang?",
            topic_slug="lainnya",
            answer_source=AnswerSource.refusal,
            has_grounding=False,
            is_refused=True,
            created_at=now,
        )
    )

    gaps_resp = await client.get("/api/admin/gaps", headers=headers)
    assert gaps_resp.status_code == 200
    gaps = gaps_resp.json()
    # Refusal excluded; duplicate ungrounded questions aggregated with count == 2
    assert not any(g["id"] == "q_refusal_not_gap" for g in gaps)
    dream_gap = next(g for g in gaps if "mimpi" in g["canonical"])
    assert dream_gap["count"] == 2

    # Resolve gap
    res_gap = await client.post(f"/api/admin/gaps/{dream_gap['id']}/resolve", headers=headers)
    assert res_gap.status_code == 200
    gaps_after = (await client.get("/api/admin/gaps", headers=headers)).json()
    assert not any("mimpi" in g["canonical"] for g in gaps_after)

    # 2. Reviews queue: chunk review + ambiguous question review
    await storage.save_chunk(
        ArticleChunk(
            id="chk_flag_1",
            article_id="art_1",
            site="isadanislam.org",
            url="https://isadanislam.org/kasih",
            title="Kasih Allah",
            chunk_index=0,
            text="Potongan teks dengan istilah yang perlu ditinjau.",
            is_retrievable=False,
            created_at=now,
        )
    )
    await storage.save_flagged_chunk(
        FlaggedChunk(
            id="flg_1",
            chunk_id="chk_flag_1",
            article_id="art_1",
            site="isadanislam.org",
            url="https://isadanislam.org/kasih",
            title="Kasih Allah",
            text="Potongan teks dengan istilah Tuhan yang perlu ditinjau.",
            matched_terms=["Tuhan"],
            created_at=now,
        )
    )
    await storage.save_question(
        Question(
            id="q_ambig_1",
            session_id="s4",
            uid="u4",
            question_text="Saya bingung soal iman dan perasaan",
            answer_text="Jawaban",
            topic_slug="lainnya",
            answer_source=AnswerSource.generated,
            relevance=Relevance.ambiguous,
            created_at=now,
        )
    )

    rev_resp = await client.get("/api/admin/reviews", headers=headers)
    assert rev_resp.status_code == 200
    reviews = rev_resp.json()
    assert any(r["id"] == "flg_1" for r in reviews)
    assert any(r["id"] == "rev_q_q_ambig_1" for r in reviews)

    # Resolve flagged chunk with rewrite decision
    resolve_chunk_resp = await client.put(
        "/api/admin/reviews/flg_1",
        headers=headers,
        json={
            "decision": ChunkDecision.rewrite.value,
            "rewritten_text": "Potongan teks dengan sebutan Allah yang sudah diperbaiki.",
            "note": "Sudah diganti menjadi Allah",
        },
    )
    assert resolve_chunk_resp.status_code == 200
    updated_chunk = await storage.get_chunk("chk_flag_1")
    assert updated_chunk is not None
    assert updated_chunk.is_retrievable is True
    assert "Allah" in updated_chunk.text

    # 3. Export CSV (no PII)
    csv_resp = await client.get("/api/admin/questions/export?channel=widget", headers=headers)
    assert csv_resp.status_code == 200
    assert "waktu,pertanyaan,topik,hasil,suka,kanal" in csv_resp.text
    assert "widget" in csv_resp.text

    # 4. Config placeholder guard
    bad_cfg = await client.put(
        "/api/admin/config/contact_number",
        headers=headers,
        json={"value": "PLACEHOLDER"},
    )
    assert bad_cfg.status_code == 422

    # 5. Ingestion status & run
    ing_status = await client.get("/api/admin/ingestion/status", headers=headers)
    assert ing_status.status_code == 200
    ing_run = await client.post("/api/admin/ingestion/run", headers=headers)
    assert ing_run.status_code == 200
    assert ing_run.json()["status"] == "completed"

    # 6. Admin accounts CRUD
    create_acc = await client.post(
        "/api/admin/accounts",
        headers=headers,
        json={"email": "reviewer2@tanyaiman.id", "password": "secretpassword", "role": "reviewer"},
    )
    assert create_acc.status_code == 201
    acc_id = create_acc.json()["id"]

    list_acc = await client.get("/api/admin/accounts", headers=headers)
    assert list_acc.status_code == 200
    assert any(a["id"] == acc_id for a in list_acc.json())

    del_acc = await client.delete(f"/api/admin/accounts/{acc_id}", headers=headers)
    assert del_acc.status_code == 200
