# Tanya Iman Backlog

Ad-hoc tasks and tactical work. Phased roadmap stays in [Project Implementation Plan](../project-implementation-plan.md) (PIP).

**Resolution order:** [waves.md](waves.md) (waves by cross-cutting impact). **Design / implementation plans:** [plans/](plans/).

**Last updated:** 2026-10-26 — Waves 1, 2, 3, 5, 6, 7 & 8 shipped; SMS & WhatsApp OTP (Wave 4) deferred on hold.

---

## Status & What's Next *(2026-10-26)*

**Active:** **0** active waves · **1** on hold wave (Wave 4) · **7 waves shipped**.

| Priority | Wave / Item | Status | What |
|----------|-------------|--------|------|
| **Shipped** | **Wave 8** | completed | PRD & UX Audit Remediation: Admin route guard, live corpus citations & V1–V4 editor validation, gap/topic/cluster refinements, unified review queue & question diagnostics, question filters & CSV export, interactive settings & ingestion controls, seeker chat persistence & answer states, RAG validator fallback — **BL-SEC-003**, **BL-ENG-005**, **BL-ADMIN-007** – **BL-ADMIN-011**, **BL-UI-001** |
| **Shipped** | **Wave 1** | completed | Foundation & Nuxt Shell: Pydantic schemas, storage layer parity, topics/config seeder, automated test suites (Phase 1) |
| **Shipped** | **Wave 2** | completed | Dev Cloud Deployment: Cloud Run backend, Firebase hosting (seeker + admin), `deploy.sh` script, named Firestore (`tanya-iman`) |
| **Shipped** | **Wave 3** | completed | Admin Authentication & Hardening: JWT login, refresh, bcrypt, dual-layer RBAC, initial super_admin bootstrap, portal session store — **BL-SEC-001**, **BL-SEC-002** |
| **Shipped** | **Wave 5** | completed | Corpus Ingestion & RAG Pipeline: 5-site crawler, token-bounded chunker, Vertex AI multilingual embeddings, Firestore vector retriever — **BL-CORP-001**, **BL-CORP-002**, **BL-CORP-003**, **BL-CORP-004** |
| **Shipped** | **Wave 6** | completed | Production Answer Engine & RAG Integration: Classifier, curated override, composer, compliance validators (V1-V5), and pipeline integration — **BL-ENG-001**, **BL-ENG-002**, **BL-ENG-003**, **BL-ENG-004** |
| **Shipped** | **Wave 7** | completed | Editorial Surface & Admin Portal: Question review, live chunk diagnostics, topic metrics, curated editor, live clustering pipeline & backfill, gaps, question delete, CORS fix, and audit logs — **BL-ADMIN-001** – **BL-ADMIN-006** |
| **On Hold** | **Wave 4** | on_hold | Live Phone Auth (SMS & WhatsApp OTP) & Guest Conversion — **BL-AUTH-001**, **BL-AUTH-002**, **BL-AUTH-003**, **BL-AUTH-004** |

---

## Current Wave Backlog

### Archive — Wave 8 (shipped 2026-10-26)

| Wave | ID | Status | Title |
|------|-----|--------|-------|
| **8** | [BL-SEC-003](#bl-sec-003--admin-portal-global-route-protection-session-hardening-and-live-sidebar-badges) | ~~completed~~ | Admin portal global route protection, session `canEdit` hardening, 401 redirect & live sidebar badges |
| **8** | [BL-ADMIN-007](#bl-admin-007--curated-answer-editor-real-corpus-citations-and-full-v1v4-validation) | ~~completed~~ | Curated answer editor real corpus article search (`GET /api/admin/articles`), citation persistence & full V1–V4 validation |
| **8** | [BL-ADMIN-008](#bl-admin-008--content-gaps-aggregation-topic-analytics-accuracy-and-safe-cluster-promotion) | ~~completed~~ | Content gaps `no_grounding` aggregation & resolution, topic metrics exclusion & `refusal_rate`, and safe cluster promotion |
| **8** | [BL-ADMIN-009](#bl-admin-009--unified-review-queue-persistence-and-question-detail-diagnostics) | ~~completed~~ | Unified review queue sources & persistent decisions (`/tinjauan`) and question detail actions & repair diagnostics (`/pertanyaan/[id]`) |
| **8** | [BL-ADMIN-010](#bl-admin-010--question-list-advanced-filters-session-channel-tracking-and-csv-export-api) | ~~completed~~ | Question list date/validator/channel/`emotional_deferral` filters, session channel tracking & `GET /api/admin/questions/export` |
| **8** | [BL-ADMIN-011](#bl-admin-011--interactive-settings-ingestion-controls-admin-management-and-audit-log-filters) | ~~completed~~ | Interactive settings (`contact_*` & system config), ingestion status/trigger API, admin account management & audit log filters |
| **8** | [BL-UI-001](#bl-ui-001--seeker-chat-session-persistence-emotional-deferral-ui-and-tappable-crisis-links) | ~~completed~~ | Seeker chat session persistence across `/privasi` & reload, `emotional_deferral` card, and tappable `tel:` crisis links |
| **8** | [BL-ENG-005](#bl-eng-005--rag-validator-post-repair-fallback-source-and-failure-code-preservation) | ~~completed~~ | RAG validator post-repair fallback source (`AnswerSource.error`, non-likeable) and full failure code preservation |

### Archive — Wave 7 (shipped 2026-09-29, enhanced 2026-10-26 in `2d75a1f`)

| Wave | ID | Status | Title |
|------|-----|--------|-------|
| **7** | BL-ADMIN-001 | ~~completed~~ | Question list API with cursor pagination, filters, and CSV export |
| **7** | BL-ADMIN-002 | ~~completed~~ | Topic analytics and content gaps APIs |
| **7** | BL-ADMIN-003 | ~~completed~~ | Curated answer editing API with V1–V4 validation and audit trail |
| **7** | BL-ADMIN-004 | ~~completed~~ | Similar-question clustering within topics (with live chat pipeline & Firestore backfill) |
| **7** | BL-ADMIN-005 | ~~completed~~ | Editorial Web Admin Portal UI in Nuxt 3 SPA |
| **7** | BL-ADMIN-006 | ~~completed~~ | Audit log tracking, question deletion (`DELETE /api/admin/questions/{id}`), and retention policy purge |

### On Hold (Wave 4 — Phone & OTP Auth)
*Deferred per user direction to prioritize core answer engine, corpus, and editorial workflows while keeping Guest access active.*

| Wave | ID | Status | Title |
|------|-----|--------|-------|
| **4** | [BL-AUTH-001](#bl-auth-001--firebase-phone-auth-sms-flow) | on_hold | Firebase Phone Auth (SMS) client & verification |
| **4** | [BL-AUTH-002](#bl-auth-002--whatsapp-otp-provider-and-custom-token-minting) | on_hold | WhatsApp Twilio Verify OTP provider & custom token minting |
| **4** | [BL-AUTH-003](#bl-auth-003--phone-number-aes-encryption-hmac-indexing-and-otp-throttle) | on_hold | Phone number AES-256-GCM encryption, HMAC indexing & OTP throttle accounting |
| **4** | [BL-AUTH-004](#bl-auth-004--guest-to-phone-account-conversion) | on_hold | Guest-to-Phone account conversion (`POST /api/auth/convert`) |

---

## Feature Sections

### Seeker Authentication & Identity

Seeker identity, guest access, SMS & WhatsApp OTP, account conversion.

#### On Hold

##### BL-AUTH-001 — Firebase Phone Auth (SMS) flow
- **Status:** on_hold
- **Created:** 2026-09-28
- **Updated:** 2026-09-28
- **Notes:** **Wave 4.** PIP Task 3.1 & PRD F-2. Connect seeker web app (`web/app/pages/masuk.vue`) to Firebase Phone Auth for native SMS verification with reCAPTCHA. Resolves Firebase ID token on backend and records user with `auth_method: sms`. **Deferred:** Seeker app currently operates via first-class Guest Auth (Firebase Anonymous Auth / local guest tokens), which collects zero personal data and allows immediate conversation access.

##### BL-AUTH-002 — WhatsApp OTP provider and custom token minting
- **Status:** on_hold
- **Created:** 2026-09-28
- **Updated:** 2026-09-28
- **Notes:** **Wave 4.** PIP Task 3.2, PRD F-2, and PRD OD-1. Backend bridge for WhatsApp OTP since Firebase does not natively support WhatsApp. Dispatches OTP via Twilio Verify (`POST /api/auth/otp/request`), validates 6-digit code with a 5-attempt ceiling (`POST /api/auth/otp/verify`), and mints a Firebase custom token via Admin SDK. Includes `FakeOTP` provider (`000000`) for zero-cost offline development and testing. **Deferred:** Awaiting production Twilio Verify account provisioning and live cost ceiling agreement.

##### BL-AUTH-003 — Phone number AES encryption, HMAC indexing, and OTP throttle
- **Status:** on_hold
- **Created:** 2026-09-28
- **Updated:** 2026-09-28
- **Notes:** **Wave 4.** PIP Task 3.1 & PRD §7.4. Phone numbers are stored encrypted at rest using AES-256-GCM (`phone_e164_enc`), never plaintext. Fast O(1) user lookup uses HMAC-SHA256 (`phone_hash`) without decryption. OTP request accounting enforces a strict rate limit of 3 code requests per number per hour (F-24). Masked in logs and admin exports (`+62 812-****-**90`).

##### BL-AUTH-004 — Guest-to-Phone account conversion
- **Status:** on_hold
- **Created:** 2026-09-28
- **Updated:** 2026-09-28
- **Notes:** **Wave 4.** PIP Task 3.3 & PRD F-25. `POST /api/auth/convert` allows a seeker who started as a guest to authenticate with phone without losing their active chat transcript. Atomically re-points the anonymous UID's `sessions`, `questions`, and `likes` at the phone UID and marks the anonymous record `superseded_by`. Deduplicates likes if both identities liked the same question.

#### Archive

##### BL-AUTH-000 — First-class Guest Access (Anonymous Auth)
- **Status:** completed
- **Created:** 2026-09-08
- **Completed:** 2026-09-11
- **Updated:** 2026-09-25
- **Notes:** **Wave 1.** PIP Task 2.1 & PRD F-3. Enables instant, low-friction access for Muslim seekers without entering phone or email. Uses persistent anonymous UID, records `auth_method: guest`, and stores zero personally identifiable information (ZDR).

---

### Security & Admin Auth

Admin access, JWT tokens, RBAC, password security.

#### Archive

##### BL-SEC-003 — Admin portal global route protection, session hardening, and live sidebar badges
- **Status:** completed
- **Created:** 2026-10-26
- **Completed:** 2026-10-26
- **Updated:** 2026-10-26
- **Notes:** **Wave 8.** PRD F-19 & §7.4. Global route middleware (`web/admin/middleware/auth.global.ts`) redirects unauthenticated users to `/masuk`. Hardened `web/admin/stores/session.ts` so `isAuthenticated` requires both `email` and `accessToken`, and `canEdit`/`canAdminister` require `isAuthenticated`. In `web/admin/composables/useAdminApi.ts`, when `!demo`, redirects to `/masuk` on 401 and removes silent `fixtures.*` fallbacks. Connected sidebar badges (`gapCount` and `reviewCount` in `web/admin/layouts/default.vue`) to live reactive API counts.

##### BL-SEC-001 — Admin JWT authentication and refresh lifecycle
- **Status:** completed
- **Created:** 2026-09-28
- **Completed:** 2026-09-28
- **Updated:** 2026-09-28
- **Notes:** **Wave 3.** PIP Task 3.5 & PRD F-19. Secure editorial access to the admin portal (`web/admin/`). `POST /api/admin/auth/login` verifies bcrypt-hashed credentials and issues an access token (1h TTL, JWT signed with `ADMIN_JWT_SECRET`) and a refresh token (30d TTL, stored as SHA-256 hash in `admin_users.refresh_token_hash`). `POST /api/admin/auth/refresh` safely exchanges a valid refresh token. Integrated with `web/admin/stores/session.ts` and `web/admin/pages/masuk.vue`.

##### BL-SEC-002 — Admin role-based access control and bootstrap
- **Status:** completed
- **Created:** 2026-09-28
- **Completed:** 2026-09-28
- **Updated:** 2026-09-28
- **Notes:** **Wave 3.** PIP Task 3.5 & PRD §7.4. Enforces three administrative roles: `editor`, `reviewer`, `super_admin`. Implements `require_admin(role)` dependency with dual-layer checks: validated at the HTTP route and redundantly re-asserted in the service layer so routing mistakes cannot cause privilege escalation. `POST /api/admin/auth/bootstrap` provisions the initial `super_admin` in development and staging, but returns HTTP 403 Forbidden in `ENV=production`. Includes `backend/scripts/create_admin.py` CLI utility. Tested via `backend/tests/test_admin_auth.py`.

---

### AI Answer Engine & Evaluation

Classification, curated answers, generation, compliance validators, and evaluation benchmark.

#### Archive

##### BL-ENG-005 — RAG validator post-repair fallback source and failure code preservation
- **Status:** completed
- **Created:** 2026-10-26
- **Completed:** 2026-10-26
- **Updated:** 2026-10-26
- **Notes:** **Wave 8.** PRD F-17 & F-28. Fixed `RAGEngine` validator double-failure fallback (`backend/engine/rag.py`) so that when both initial and repair passes fail V1–V5 validation, the returned fallback uses `AnswerSource.error` (`likeable = False`) instead of `AnswerSource.generated`, and preserves combined validator failure codes plus `initial_validator_failures` and `repair_attempted = True`.

##### BL-ENG-001 — Relevance classifier, topic resolver, and curated answer override
- **Status:** completed
- **Created:** 2026-09-28
- **Completed:** 2026-09-29
- **Updated:** 2026-09-29
- **Notes:** **Wave 6.** PIP Tasks 5.2, 5.3 & PRD F-9, F-10, F-23. Single structured LLM call classifying inquiry (`theology`, `emotional_only`, `ambiguous`, `irrelevant`) and mapping to one of 14 canonical topics. Rejects prompt injection attempts with standard refusal. Intercepts published curated answers before vector retrieval to serve byte-identical canonical responses.

##### BL-ENG-002 — Answer composer with structured output and prompt stamping
- **Status:** completed
- **Created:** 2026-09-28
- **Completed:** 2026-09-29
- **Updated:** 2026-09-29
- **Notes:** **Wave 6.** PIP Task 5.4 & PRD F-11–F-15. Composes theological answers using versioned Indonesian prompt template and structured output. Passages injected without raw URLs to prevent link hallucination. Records `prompt_version` and model metadata with timeout fallback.

##### BL-ENG-003 — Compliance validators V1–V5 and repair loop
- **Status:** completed
- **Created:** 2026-09-28
- **Completed:** 2026-09-29
- **Updated:** 2026-09-29
- **Notes:** **Wave 6.** PIP Task 5.5 & PRD F-28. Implements V1 word count bounds (25–250 words), V2 forbidden terminology check ('Tuhan'/'Yesus' prohibited, 'Allah'/'Isa Al-Masih' required), V3 scripture balance rule (max 1 Quran citation leading in first 25%, Bible ≥ 2 if Quran present), V4 citation allowlist and provenance, and V5 grounding content overlap. Runs exactly one automated repair attempt before fallback.

##### BL-ENG-004 — Pipeline wiring, stub retirement, and benchmark harness
- **Status:** completed
- **Created:** 2026-09-28
- **Completed:** 2026-09-29
- **Updated:** 2026-09-29
- **Notes:** **Wave 6.** PIP Tasks 5.6, 5.7 & PRD F-30–F-32. Connects crisis guard (running before rate limiter), classifier, curated override, vector retriever, composer, and validators into unified production RAG pipeline. Retires stub chat engine. Executes 120-question automated benchmark suite (`questions.yml`).

---

### Corpus & Knowledge Base

Crawler, chunker, embeddings, vector retriever.

#### Archive

##### BL-CORP-001 — Five-site crawler with change detection and allowlist
- **Status:** completed
- **Created:** 2026-09-28
- **Completed:** 2026-09-28
- **Updated:** 2026-09-28
- **Notes:** **Wave 5.** PIP Task 4.1 & PRD F-41. Crawls the 5 approved ministry sites (`isadanislam.org`, `isadanalquran.com`, `isadanalfatihah.com`, `isaislamdankaumwanita.com`, `takutneraka.com`). Sitemap-first traversal, polite delay, main-content extraction, and SHA-256 `content_hash` change detection to eliminate redundant writes.

##### BL-CORP-002 — Article chunker with token bounds and forbidden-term screening
- **Status:** completed
- **Created:** 2026-09-28
- **Completed:** 2026-09-28
- **Updated:** 2026-09-28
- **Notes:** **Wave 5.** PIP Task 4.2 & AI Spec §8.2 (OI-1). Chunks extracted articles into ~400 token windows with 80-token overlap, never spanning article boundaries. Flags chunks containing forbidden terms ("Yesus", "Tuhan") into a review collection before indexing.

##### BL-CORP-003 — Multilingual embeddings and Firestore vector upsert
- **Status:** completed
- **Created:** 2026-09-28
- **Completed:** 2026-09-28
- **Updated:** 2026-09-28
- **Notes:** **Wave 5.** PIP Task 4.3. Batched embeddings using Vertex AI `text-multilingual-embedding-002` (with DeterministicEmbedder for offline test parity). Stamps `embedding_model` on stored chunks to enable graceful re-indexing. Upserts into Firestore `article_chunks` and retires obsolete chunks.

##### BL-CORP-004 — Vector retriever with query-time site allowlist
- **Status:** completed
- **Created:** 2026-09-28
- **Completed:** 2026-09-28
- **Updated:** 2026-09-28
- **Notes:** **Wave 5.** PIP Task 4.4. Firestore `find_nearest` over `article_chunks`. Filters strictly by the 5 approved domains at query time (defense-in-depth). Returns top 4 passages (max 2 per article), evaluates similarity threshold from `system_config`, and emits no-grounding signal if < 2 passages survive.

---

### Editorial Surface & Moderation

Admin portal UI, question moderation, topic analytics, curated answers, clustering, content gaps, audit logs.

#### Archive

##### BL-ADMIN-007 — Curated answer editor real corpus citations and full V1–V4 validation
- **Status:** completed
- **Created:** 2026-10-26
- **Completed:** 2026-10-26
- **Updated:** 2026-10-26
- **Notes:** **Wave 8.** PRD F-14, F-23, F-34 & Admin UX §10. Added `GET /api/admin/articles` to search/list real corpus articles from storage (filtered to approved sites) and connected `web/admin/pages/editor/[slug].vue`. Loads `data.curatedCitations` on mount and persists selected `Citation[]` on `saveDraft()` and `publish()`. Completed live & backend V1–V4 validation in `editor/[slug].vue` and `PUT /api/admin/topics/{slug}/answer` (bans `Jesus`/`Tuhan`/`Yesus`, requires `Allah` or `Isa Al-Masih`, highlights forbidden terms, validates scripture balance across 66 Bible book names, requires 1–2 approved citations on publish, and renders `error` in the template).

##### BL-ADMIN-008 — Content gaps aggregation, topic analytics accuracy, and safe cluster promotion
- **Status:** completed
- **Created:** 2026-10-26
- **Completed:** 2026-10-26
- **Updated:** 2026-10-26
- **Notes:** **Wave 8.** PRD F-29, F-32 & Admin UX §9, §11, §12. Filtered `GET /api/admin/gaps` and dashboard `ungrounded_gaps` strictly to ungrounded theology questions (excluding `refusal`, `crisis`, `emotional_deferral`, `error`), grouped repeated gap questions by normalized text frequency (`count`), and wired `POST /api/admin/gaps/{id}/resolve` to the *"Sudah ditulis"* action button. Excluded `is_crisis`, `is_refused`, and `emotional_deferral` from topic question counts and background clustering (`_bg_assign_cluster` in `backend/routers/chat.py`). Fixed `promote_cluster_to_curated` (`backend/services/clustering.py` and `/serupa.vue`) so promoting or clicking *"Jadikan jawaban kurasi"* passes cluster context to the editor without overwriting an existing published curated answer. Computed topic `refusal_rate` (*Tingkat penolakan*, Admin UX §9) as the share of `no_grounding` questions in that topic, and updated `topic.question_count` / `topic.like_count` in storage.

##### BL-ADMIN-009 — Unified review queue, persistence, and question detail diagnostics
- **Status:** completed
- **Created:** 2026-10-26
- **Completed:** 2026-10-26
- **Updated:** 2026-10-26
- **Notes:** **Wave 8.** Admin UX §8, §13 & Runbook §6. Unified `/tinjauan` and `GET /api/admin/reviews` across `flagged_chunks`, `is_crisis`, `validator_failures`, `emotional_deferral`, and `ambiguous`/`flagged_for_review` items, with expandable flagged text & article URL, and persistent review resolution (`PUT /api/admin/reviews/{id}` with optional note and `ChunkDecision` `accept`/`exclude`/`rewrite` updating `ArticleChunk.is_retrievable`/`text`). In `/pertanyaan/[id].vue`, wired *"Salin tautan"* and *"Tandai untuk ditinjau"* (`POST /api/admin/questions/{id}/flag`), expandable retrieved chunk snippets, `measured` values & failure codes per validator V1–V5, and the *Perbaikan (Repair)* diagnostic block.

##### BL-ADMIN-010 — Question list advanced filters, session channel tracking, and CSV export API
- **Status:** completed
- **Created:** 2026-10-26
- **Completed:** 2026-10-26
- **Updated:** 2026-10-26
- **Notes:** **Wave 8.** PRD F-35, F-36 & Admin UX §7. Added date range, validator failure (`?validator=gagal`), channel, and `emotional_deferral` filters in `/pertanyaan` and `GET /api/admin/questions`, plus `GET /api/admin/questions/export` (`reviewer` and `super_admin`). Recorded `channel` on `Question` from the session platform (`web`, `widget`, `android`).

##### BL-ADMIN-011 — Interactive settings, ingestion controls, admin management, and audit log filters
- **Status:** completed
- **Created:** 2026-10-26
- **Completed:** 2026-10-26
- **Updated:** 2026-10-26
- **Notes:** **Wave 8.** PRD F-37, F-43, F-45 & Admin UX §14. Enabled editing and saving `contact_name`, `contact_number` (with confirmation and server/client placeholder rejection), and system config parameters (`retention_months`, `rate_limit_per_hour`, `similarity_threshold`) with pre-execution audit logging in `PUT /api/admin/config/{key}`. Standardized `AdminAuditLog.admin_id` to `admin.email` and added actor/action/date filtering to `GET /api/admin/audit` and `/pengaturan`. Implemented `GET /api/admin/ingestion/status`, `POST /api/admin/ingestion/run` (audited), and `GET/POST/DELETE /api/admin/accounts` (audited) wired to `/pengaturan`.

##### BL-ADMIN-001 — Question list API with cursor pagination, filters, and CSV export
- **Status:** completed
- **Created:** 2026-09-29
- **Completed:** 2026-09-29
- **Updated:** 2026-10-26
- **Notes:** **Wave 7.** PIP Task 6.1 & PRD F-20, F-35, F-36. `GET /api/admin/questions` and `GET /api/admin/questions/{id}` with live `retrieved_chunks` and `cited_urls` diagnostics persisted on `Question` (`2d75a1f`). Always masks phone numbers (`+62 812-****-**90`).

##### BL-ADMIN-002 — Topic analytics and content gaps APIs
- **Status:** completed
- **Created:** 2026-09-29
- **Completed:** 2026-09-29
- **Updated:** 2026-10-26
- **Notes:** **Wave 7.** PIP Tasks 6.2, 6.4 & PRD F-21, F-29, US-8. `GET /api/admin/topics` returns metrics for all 13 canonical topics plus `lainnya` (question count, like count, curated status, last updated). `GET /api/admin/gaps` returns ungrounded questions for editorial review.

##### BL-ADMIN-003 — Curated answer editing API with V1–V4 validation and audit trail
- **Status:** completed
- **Created:** 2026-09-29
- **Completed:** 2026-09-29
- **Updated:** 2026-09-29
- **Notes:** **Wave 7.** PIP Task 6.5 & PRD F-23, F-34. `PUT /api/admin/topics/{slug}/answer` enables editors and super_admins to manage canonical curated responses. Executes V1–V4 compliance validation before saving. Supports `draft` and `published` states (only `published` is served to seekers). Records `updated_by`, `updated_at`, and writes an immutable audit entry.

##### BL-ADMIN-004 — Similar-question clustering within topics
- **Status:** completed
- **Created:** 2026-09-29
- **Completed:** 2026-10-26
- **Updated:** 2026-10-26
- **Notes:** **Wave 7.** PIP Task 6.3 & PRD F-22. `backend/services/clustering.py` + `GET /api/admin/clusters` + `POST /api/admin/clusters/backfill`. Asynchronously assigns live chat inquiries in `POST /api/chat/messages` (`_bg_assign_cluster`) to within-topic clusters using cosine similarity threshold (`cluster_similarity_threshold`, default 0.85) (`2d75a1f`). Provides actions and modals in `/serupa` to filter by topic, view member questions, rename canonical cluster text, merge clusters, promote a cluster, or delete a cluster (`super_admin`).

##### BL-ADMIN-005 — Editorial Web Admin Portal UI in Nuxt 3 SPA
- **Status:** completed
- **Created:** 2026-09-29
- **Completed:** 2026-09-29
- **Updated:** 2026-10-26
- **Notes:** **Wave 7.** PIP Task 6.6 & Admin UX Specification. Desktop-first Nuxt 3 SPA in `web/admin/`. Features question review list, question detail view with live retrieved chunk snippets and `Dikutip`/`Diambil` badges (`2d75a1f`), topic analytics dashboard, content gaps queue, cluster management modals, and curated answer editor with live Indonesian word counter.

##### BL-ADMIN-006 — Audit log tracking and retention policy purge
- **Status:** completed
- **Created:** 2026-09-29
- **Completed:** 2026-10-26
- **Updated:** 2026-10-26
- **Notes:** **Wave 7.** PIP Task 6.7 & PRD F-37. Implements `audit_log` collection capturing destructive actions (including `DELETE /api/admin/questions/{id}`, cluster delete/merge, and `POST /api/admin/purge`), curated answer changes, and configuration updates, wired to the live *Jejak Audit* table in `/pengaturan` (`2d75a1f`).

---

### Seeker Web App & Channels

Seeker chat interface, privacy navigation, answer states, embedded widget, Android shell.

#### Archive

##### BL-UI-001 — Seeker chat session persistence, emotional deferral UI, and tappable crisis links
- **Status:** completed
- **Created:** 2026-10-26
- **Completed:** 2026-10-26
- **Updated:** 2026-10-26
- **Notes:** **Wave 8.** PRD F-3, F-4, F-8, F-25, F-30, F-44. Updated `web/app/stores/chat.ts`, `stores/auth.ts`, `pages/privasi.vue`, `pages/masuk.vue`, and `components/AppShell.vue` so navigating to `/privasi` and clicking `← Kembali`, upgrading from guest to phone, or reloading `/chat` preserves the active chat session and transcript. Updated `AnswerStates.vue` (`utils/phoneLinks.ts`) to render a dedicated `emotional_deferral` state with a tappable `tel:` contact link, render crisis helpline numbers (`119`, `(021) 500-454`) as tappable `tel:` links (min 44px), and show `crisis_demo_note` only in demo mode.

---

### Operations & Deployments

Cloud Run, Firebase Hosting, environments, CI/CD.

#### Archive

##### BL-OPS-001 — Dev project Cloud Run backend & Firebase multi-site deployment
- **Status:** completed
- **Created:** 2026-09-15
- **Completed:** 2026-09-25
- **Updated:** 2026-10-26
- **Notes:** **Wave 2.** Configured GCP project `project-philip-501910` in `asia-southeast2`: Cloud Run backend (`tanya-iman-backend`) with explicit CORS preflight method/header configuration (`2d75a1f`), Firebase multi-site hosting (`tanya-iman-app-dev` for seeker app and `tanya-iman-admin-dev` for admin portal), and named Firestore database `tanya-iman`. Shipped automated `./deploy.sh` script.

---

### Foundation & Architecture

Core scaffolding, data models, storage protocols.

#### Archive

##### BL-FOUND-001 — Data models, storage parity, seeder, and test suites
- **Status:** completed
- **Created:** 2026-09-08
- **Completed:** 2026-09-25
- **Updated:** 2026-09-25
- **Notes:** **Wave 1.** PIP Phase 1 (Tasks 1.1–1.5). Delivered Topic and SystemConfig schemas, Storage protocol with 100% parity between `MemoryStorage` and `FirestoreStorage`, idempotent database seeder (`scripts/seed.py`), 48 backend pytest unit tests, and 42 frontend vitest tests.
