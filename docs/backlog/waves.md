# Backlog Resolution Waves

Tactical **order of work** for open and scheduled items in [backlog.md](backlog.md). Strategic phases stay in [Project Implementation Plan](../project-implementation-plan.md) (PIP).

**Last updated:** 2026-10-26 — Waves 1, 2, 3, 5, 6, 7 & 8 shipped; Wave 4 (Phone & OTP Auth) deferred to backlog on hold.

---

## What's Next *(2026-10-26)*

| # | Wave | Status | Scope |
|---|------|--------|-------|
| — | **Wave 1** | ✅ shipped | Foundation & Nuxt Shell — Pydantic schemas, storage layer parity, topics/config seeder, automated unit tests (**BL-FOUND-001**, **BL-AUTH-000**) |
| — | **Wave 2** | ✅ shipped | Dev Cloud Infrastructure — Cloud Run backend, Firebase hosting (seeker + admin), `deploy.sh` (**BL-OPS-001**) |
| — | **Wave 3** | ✅ shipped | Admin Authentication & Security Hardening — JWT login, refresh token, bcrypt, dual-layer RBAC, super_admin bootstrap, portal session store (**BL-SEC-001**, **BL-SEC-002**) |
| — | **Wave 5** | ✅ shipped | Corpus Ingestion & RAG Pipeline — 5-site crawler, token chunker, Vertex AI multilingual embeddings, Firestore vector retriever (**BL-CORP-001**, **BL-CORP-002**, **BL-CORP-003**, **BL-CORP-004**) |
| — | **Wave 6** | ✅ shipped | Production Answer Engine — Classifier, curated override, composer, compliance validators (V1–V5), and pipeline integration (**BL-ENG-001**, **BL-ENG-002**, **BL-ENG-003**, **BL-ENG-004**) |
| — | **Wave 7** | ✅ shipped | Editorial Surface & Admin Portal — Question review, live chunk diagnostics, topic metrics, curated editor, live clustering pipeline & backfill, gaps, question delete, CORS fix, and audit logs (**BL-ADMIN-001** – **BL-ADMIN-006**) |
| — | **Wave 8** | ✅ shipped | PRD & UX Compliance Audit Remediation — Admin route protection, real corpus citations & V1–V4 validation, gap/topic/cluster refinements, unified review queue & question diagnostics, question filters & CSV export, interactive settings & ingestion controls, seeker chat persistence & answer states, RAG validator fallback (**BL-SEC-003**, **BL-ENG-005**, **BL-ADMIN-007** – **BL-ADMIN-011**, **BL-UI-001**) |
| **4** | **Wave 4** | ⏸️ on_hold | Live Phone Auth (SMS & WhatsApp OTP) & Guest Conversion — (**BL-AUTH-001**, **BL-AUTH-002**, **BL-AUTH-003**, **BL-AUTH-004**) |

---

## Wave Details

### Wave 1 — Foundation & Nuxt Shell ✅ *(closed 2026-09-25)*

**Status:** completed

**Impact:** [Foundation & Architecture](backlog.md#foundation--architecture) + [Seeker Authentication & Identity](backlog.md#seeker-authentication--identity) — PIP Phase 1 & Task 2.1.

**Shipped:** 
- `Topic` and `SystemConfig` Pydantic models.
- Full storage protocol parity across `MemoryStorage` and `FirestoreStorage`.
- Idempotent database seeder (`backend/scripts/seed.py`) for 14 canonical topics and initial system configuration.
- Anonymous Guest Authentication flow.
- 48 passing backend tests (`backend/tests/test_storage.py`, `test_api_chat.py`, etc.) and 42 passing frontend tests (`web/app/tests/welcome.spec.ts`).

| ID | Title | Status |
|----|-------|--------|
| ~~**BL-FOUND-001**~~ | ~~Data models, storage parity, seeder, and test suites~~ | completed |
| ~~**BL-AUTH-000**~~ | ~~First-class Guest Access (Anonymous Auth)~~ | completed |

---

### Wave 2 — Dev Cloud Deployment & Multisite ✅ *(closed 2026-09-25)*

**Status:** completed

**Impact:** [Operations & Deployments](backlog.md#operations--deployments).

**Shipped:**
- GCP project `project-philip-501910` configured in `asia-southeast2`.
- Cloud Run backend deployed with Docker container and Secret Manager secret mounts.
- Firebase multi-site hosting configured: Seeker Web App (`tanya-iman-app-dev.web.app`) and Admin Portal (`tanya-iman-admin-dev.web.app`).
- Firestore named database `tanya-iman` provisioned.
- Production-grade deployment automation script (`./deploy.sh`).

| ID | Title | Status |
|----|-------|--------|
| ~~**BL-OPS-001**~~ | ~~Dev project Cloud Run backend & Firebase multi-site deployment~~ | completed |

---

### Wave 3 — Admin Authentication & Security Hardening ✅ *(closed 2026-09-28)*

**Status:** completed

**Impact:** [Security & Admin Auth](backlog.md#security--admin-auth) — PIP Task 3.5 & PRD F-19.

**Shipped:**
- `backend/routers/admin_auth.py` mounted at `/api/admin/auth/` and `/admin/auth/`.
- `POST /api/admin/auth/login`: verifies bcrypt-hashed passwords; issues 1h access JWT and 30d refresh token (stored hashed).
- `POST /api/admin/auth/refresh`: safely exchanges refresh token for new access token.
- `POST /api/admin/auth/bootstrap`: creates initial `super_admin`; strictly blocked (HTTP 403) when `ENV=production`.
- `GET /api/admin/auth/me`: inspects authenticated admin claims.
- `require_admin(role)` dependency with dual-layer checks (HTTP dependency + service layer re-assertion per PRD §7.4).
- `backend/scripts/create_admin.py` CLI utility for direct admin provisioning.
- `web/admin/stores/session.ts` and `web/admin/pages/masuk.vue` connected with JWT login, refresh, and storage persistence.
- Full test suite: 53 passing backend tests (`backend/tests/test_admin_auth.py`).

| ID | Title | Status |
|----|-------|--------|
| ~~**BL-SEC-001**~~ | ~~Admin JWT authentication and refresh lifecycle~~ | completed |
| ~~**BL-SEC-002**~~ | ~~Admin role-based access control and bootstrap~~ | completed |

---

### Wave 4 — Seeker Phone & WhatsApp Authentication ⏸️ *(on hold / deferred)*

**Status:** on_hold

**Impact:** [Seeker Authentication & Identity](backlog.md#seeker-authentication--identity) — PIP Tasks 3.1, 3.2, 3.3.

**Reason for hold:** Deferred per user instruction to prioritize core theological answer engine, corpus ingestion, and editorial tooling while maintaining first-class Guest Auth for seekers.

| ID | Title | Depends on |
|----|-------|------------|
| **BL-AUTH-001** | Firebase Phone Auth (SMS) flow | — |
| **BL-AUTH-002** | WhatsApp OTP provider and custom token minting | — |
| **BL-AUTH-003** | Phone number AES encryption, HMAC indexing, and OTP throttle | **BL-AUTH-001** |
| **BL-AUTH-004** | Guest-to-Phone account conversion | **BL-AUTH-001**, **BL-AUTH-002** |

---

### Wave 5 — Corpus Ingestion & Vector RAG Pipeline ✅ *(closed 2026-09-28)*

**Status:** completed

**Impact:** [Corpus & Knowledge Base](backlog.md#corpus--knowledge-base) — PIP Phase 4 & PRD F-41.

**Shipped:**
- 5-site web crawler with robots.txt, sitemaps, semantic content extraction, and SHA-256 change detection (`crawler.py`).
- Token-bounded article chunker (~400 token windows, 80 token overlap) with V2 forbidden-term screening (`chunker.py`).
- Batched 768-dim vector embedder with `embedding_model` stamping, upsert, and chunk retirement (`embedder.py`).
- Vector retriever with query-time domain allowlist gate, threshold evaluation, and per-article cap (`retriever.py`).
- CLI orchestration runner (`run.py`).
- 20 unit tests across 4 test suites with 100% test pass rate (`test_crawler.py`, `test_chunker.py`, `test_embedder.py`, `test_retriever.py`).

| ID | Title | Status |
|----|-------|--------|
| ~~**BL-CORP-001**~~ | ~~Five-site crawler with change detection and allowlist~~ | completed |
| ~~**BL-CORP-002**~~ | ~~Article chunker with token bounds and forbidden-term screening~~ | completed |
| ~~**BL-CORP-003**~~ | ~~Multilingual embeddings and Firestore vector upsert~~ | completed |
| ~~**BL-CORP-004**~~ | ~~Vector retriever with query-time site allowlist~~ | completed |

---

### Wave 6 — Production Answer Engine & RAG Integration ✅ *(closed 2026-09-29)*

**Status:** completed

**Impact:** [AI Answer Engine & Evaluation](backlog.md#ai-answer-engine--evaluation) — PIP Phase 5 & PRD F-9 – F-15, F-28, F-30 – F-32.

**Shipped:**
- Gemini LLM provider supporting structured JSON output and `thinkingBudget: 0` (`providers/llm.py`).
- Crisis guard asserting 100% recall before rate limiting (`services/guards.py`).
- Relevance classifier & topic resolver with prompt injection rejection and canonical topic fallback (`engine/classifier.py`).
- Curated answer override routing before retrieval (`engine/curated.py`).
- Answer composer with versioned prompt, URL hallucination defense, and fallback model on error/timeout (`engine/composer.py`).
- Five compliance validators V1–V5 (word count bounds, terminology screening, scripture balance, citation allowlist & provenance, grounding overlap) with targeted repair loop (`engine/validators.py`).
- Production RAG pipeline orchestrator wiring all stages and retiring the stub engine (`engine/rag.py`).
- 120-question Indonesian evaluation benchmark and test runner (`tests/benchmark/questions.yml`, `tests/benchmark/test_benchmark.py`).
- Complete automated test suite of 107 tests passing with 100% green status and 0 lint errors (`uv run pytest`, `uv run ruff check .`).

| ID | Title | Status |
|----|-------|--------|
| ~~**BL-ENG-001**~~ | ~~Relevance classifier, topic resolver, and curated answer override~~ | completed |
| ~~**BL-ENG-002**~~ | ~~Answer composer with structured output and prompt stamping~~ | completed |
| ~~**BL-ENG-003**~~ | ~~Compliance validators V1–V5 and repair loop~~ | completed |
| ~~**BL-ENG-004**~~ | ~~Pipeline wiring, stub retirement, and benchmark harness~~ | completed |

---

### Wave 7 — Editorial Surface & Admin Portal ✅ *(closed 2026-09-29, enhanced 2026-10-26 in `2d75a1f`)*

**Status:** completed

**Impact:** [Editorial Surface & Moderation](backlog.md#editorial-surface--moderation) — PIP Phase 6 & PRD F-20 – F-23, F-29, F-34 – F-37.

**Shipped:**
- Question list, detail diagnostics (`retrieved_chunks` & `cited_urls`), and audited deletion API (`GET /api/admin/questions`, `GET /api/admin/questions/{id}`, `DELETE /api/admin/questions/{id}`).
- Topic analytics API: `GET /api/admin/topics`, `GET /api/admin/topics/{slug}` with question counts, like counts, curated status.
- Content gaps API: `GET /api/admin/gaps` listing ungrounded topics.
- Curated answer editor API: `PUT /api/admin/topics/{slug}/answer` with live V1–V4 compliance validation.
- Similar-question clustering service (`services/clustering.py`): live background clustering in `POST /api/chat/messages`, Firestore backfill (`POST /api/admin/clusters/backfill`), cosine similarity assignment (`cluster_similarity_threshold`), within-topic isolation, running centroid update.
- Cluster management API & UI modals (`/serupa`): `GET /api/admin/clusters`, `PUT /clusters/{id}/rename`, `POST /clusters/{id}/merge`, `POST /clusters/{id}/promote`, `DELETE /clusters/{id}`, topic filter, and member question drawer.
- Audit log (`GET /api/admin/audit`) & Retention purge (`POST /api/admin/purge`) wired to live `/pengaturan` page.
- Explicit CORS preflight configuration (`allow_methods`, `allow_headers`) on backend (`main.py`).
- 133 passing backend tests (`test_clustering.py`, `test_admin_audit.py`, `test_api_admin.py`).

| ID | Title | Status |
|----|-------|--------|
| ~~**BL-ADMIN-001**~~ | ~~Question list API with cursor pagination, filters, and CSV export~~ | completed |
| ~~**BL-ADMIN-002**~~ | ~~Topic analytics and content gaps APIs~~ | completed |
| ~~**BL-ADMIN-003**~~ | ~~Curated answer editing API with V1–V4 validation and audit trail~~ | completed |
| ~~**BL-ADMIN-004**~~ | ~~Similar-question clustering within topics~~ | completed |
| ~~**BL-ADMIN-005**~~ | ~~Editorial Web Admin Portal UI in Nuxt 3 SPA~~ | completed |
| ~~**BL-ADMIN-006**~~ | ~~Audit log tracking and retention policy purge~~ | completed |

---

### Wave 8 — PRD & UX Compliance Audit Remediation ✅ *(closed 2026-10-26)*

**Status:** completed

**Impact:** [Security & Admin Auth](backlog.md#security--admin-auth) + [AI Answer Engine & Evaluation](backlog.md#ai-answer-engine--evaluation) + [Editorial Surface & Moderation](backlog.md#editorial-surface--moderation) + [Seeker Web App & Channels](backlog.md#seeker-web-app--channels) — PRD F-3, F-4, F-8, F-14, F-17, F-19, F-23, F-25, F-28–F-30, F-32, F-34–F-37, F-43–F-45 & Admin/Chat UX Specifications.

**Shipped:**
- Admin portal global route middleware (`middleware/auth.global.ts`), session `canEdit`/`canAdminister` authentication guard, 401 redirect without silent fixture fallback, and live sidebar badge counts (`liveGapCount`, `liveReviewCount`).
- Real corpus article search (`GET /api/admin/articles`), curated citation persistence, and full V1–V4 validation in `/editor/[slug]` and `PUT /api/admin/topics/{slug}/answer`.
- Content gap filtering to ungrounded theology questions, frequency aggregation, and `POST /api/admin/gaps/{id}/resolve`; topic metrics exclusion (`is_crisis`, `is_refused`, `emotional_deferral`) and `no_grounding` `refusal_rate`; safe cluster promotion preserving published curated answers.
- Unified review queue (`GET /api/admin/reviews`, `PUT /api/admin/reviews/{id}`) across flagged chunks, crisis, validator failures, emotional deferral, and ambiguous questions with `ChunkDecision` persistence (`accept`, `rewrite`, `exclude`); question detail (`GET /api/admin/questions/{id}`, `POST /api/admin/questions/{id}/flag`) with expandable chunk snippets, per-validator `measured` strings & failure codes, and `RepairDetail` diagnostics.
- Question list filters (`q`, `topic`, `source`, `channel`, `validator=gagal`, `date_from`, `date_to`), session platform channel tracking, and `GET /api/admin/questions/export` CSV endpoint.
- Interactive system & support contact configuration with placeholder rejection, corpus ingestion status & trigger (`GET/POST /api/admin/ingestion/*`), admin account management (`GET/POST/DELETE /api/admin/accounts`), and audit log filters (`actor`, `action`, `date_from`, `date_to`).
- Seeker chat session & auth persistence across `/privasi` navigation, guest-to-phone upgrade, and page reloads; dedicated `emotional_deferral` state and tappable `tel:` helpline links (`AnswerStates.vue`, `utils/phoneLinks.ts`).
- RAG validator double-failure fallback returning `AnswerSource.error` (`likeable = False`) and preserving combined initial + repair validator failure codes.

| ID | Title | Status |
|----|-------|--------|
| ~~**BL-SEC-003**~~ | ~~Admin portal global route protection, session `canEdit` hardening, 401 redirect & live sidebar badges~~ | completed |
| ~~**BL-ADMIN-007**~~ | ~~Curated answer editor real corpus article search (`GET /api/admin/articles`), citation persistence & full V1–V4 validation~~ | completed |
| ~~**BL-ADMIN-008**~~ | ~~Content gaps `no_grounding` aggregation & resolution, topic metrics exclusion & `refusal_rate`, and safe cluster promotion~~ | completed |
| ~~**BL-ADMIN-009**~~ | ~~Unified review queue sources & persistent decisions (`/tinjauan`) and question detail actions & repair diagnostics (`/pertanyaan/[id]`)~~ | completed |
| ~~**BL-ADMIN-010**~~ | ~~Question list date/validator/channel/`emotional_deferral` filters, session channel tracking & `GET /api/admin/questions/export`~~ | completed |
| ~~**BL-ADMIN-011**~~ | ~~Interactive settings (`contact_*` & system config), ingestion status/trigger API, admin account management & audit log filters~~ | completed |
| ~~**BL-UI-001**~~ | ~~Seeker chat session persistence across `/privasi` & reload, `emotional_deferral` card, and tappable `tel:` crisis links~~ | completed |
| ~~**BL-ENG-005**~~ | ~~RAG validator post-repair fallback source (`AnswerSource.error`, non-likeable) and full failure code preservation~~ | completed |
