# Tanya Iman Backlog

Ad-hoc tasks and tactical work. Phased roadmap stays in [Project Implementation Plan](../project-implementation-plan.md) (PIP).

**Resolution order:** [waves.md](waves.md) (waves by cross-cutting impact). **Design / implementation plans:** [plans/](plans/).

**Last updated:** 2026-09-30 — Waves 1, 2, 3, 5, 6 & 7 shipped; SMS & WhatsApp OTP (Wave 4) deferred on hold.

---

## Status & What's Next *(2026-09-29)*

**Active:** **1** on hold wave · **4** on hold BL items · **6 waves shipped**.

| Priority | Wave / Item | Status | What |
|----------|-------------|--------|------|
| **Shipped** | **Wave 1** | completed | Foundation & Nuxt Shell: Pydantic schemas, storage layer parity, topics/config seeder, automated test suites (Phase 1) |
| **Shipped** | **Wave 2** | completed | Dev Cloud Deployment: Cloud Run backend, Firebase hosting (seeker + admin), `deploy.sh` script, named Firestore (`tanya-iman`) |
| **Shipped** | **Wave 3** | completed | Admin Authentication & Hardening: JWT login, refresh, bcrypt, dual-layer RBAC, initial super_admin bootstrap, portal session store — **BL-SEC-001**, **BL-SEC-002** |
| **Shipped** | **Wave 5** | completed | Corpus Ingestion & RAG Pipeline: 5-site crawler, token-bounded chunker, Vertex AI multilingual embeddings, Firestore vector retriever — **BL-CORP-001**, **BL-CORP-002**, **BL-CORP-003**, **BL-CORP-004** |
| **Shipped** | **Wave 6** | completed | Production Answer Engine & RAG Integration: Classifier, curated override, composer, compliance validators (V1-V5), and pipeline integration — **BL-ENG-001**, **BL-ENG-002**, **BL-ENG-003**, **BL-ENG-004** |
| **Shipped** | **Wave 7** | completed | Editorial Surface & Admin Portal: Question review, topic metrics, curated editor with V1–V4 checks, clustering, gaps, and audit logs — **BL-ADMIN-001** – **BL-ADMIN-006** |
| **On Hold** | **Wave 4** | on_hold | Live Phone Auth (SMS & WhatsApp OTP) & Guest Conversion — **BL-AUTH-001**, **BL-AUTH-002**, **BL-AUTH-003**, **BL-AUTH-004** |

---

## Current Wave Backlog

### Archive — Wave 7 (shipped 2026-09-29)

| Wave | ID | Status | Title |
|------|-----|--------|-------|
| **7** | BL-ADMIN-001 | ~~completed~~ | Question list API with cursor pagination, filters, and CSV export |
| **7** | BL-ADMIN-002 | ~~completed~~ | Topic analytics and content gaps APIs |
| **7** | BL-ADMIN-003 | ~~completed~~ | Curated answer editing API with V1–V4 validation and audit trail |
| **7** | BL-ADMIN-004 | ~~completed~~ | Similar-question clustering within topics |
| **7** | BL-ADMIN-005 | ~~completed~~ | Editorial Web Admin Portal UI in Nuxt 3 SPA |
| **7** | BL-ADMIN-006 | ~~completed~~ | Audit log tracking and retention policy purge |

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

##### BL-ADMIN-001 — Question list API with cursor pagination, filters, and CSV export
- **Status:** completed
- **Created:** 2026-09-29
- **Updated:** 2026-09-29
- **Notes:** **Wave 7.** PIP Task 6.1 & PRD F-20, F-35, F-36. `GET /api/admin/questions` with cursor pagination (default 50), filtered by date range, topic, refusal, crisis, grounding, validator failure, and ambiguous flag. Always masks phone numbers (`+62 812-****-**90`). Includes `GET /api/admin/questions/export` streaming CSV of the filtered results, omitting phone numbers entirely.

##### BL-ADMIN-002 — Topic analytics and content gaps APIs
- **Status:** planned
- **Created:** 2026-09-29
- **Updated:** 2026-09-29
- **Notes:** **Wave 7.** PIP Tasks 6.2, 6.4 & PRD F-21, F-29, US-8. `GET /api/admin/topics` returns metrics for all 13 canonical topics plus `lainnya` (question count, like count, curated status, last updated). Strictly excludes crisis questions from topic metrics (F-32). `GET /api/admin/gaps` aggregates no-grounding questions clustered and ordered by frequency to serve as the editorial content queue.

##### BL-ADMIN-003 — Curated answer editing API with V1–V4 validation and audit trail
- **Status:** completed
- **Created:** 2026-09-29
- **Updated:** 2026-09-29
- **Notes:** **Wave 7.** PIP Task 6.5 & PRD F-23, F-34. `PUT /api/admin/topics/{slug}/answer` enables editors and reviewers to manage canonical curated responses. Executes V1–V4 compliance validation before saving. Supports `draft` and `published` states (only `published` is served to seekers). Records `updated_by`, `updated_at`, and writes an immutable audit entry before saving.

##### BL-ADMIN-004 — Similar-question clustering within topics
- **Status:** planned
- **Created:** 2026-09-29
- **Updated:** 2026-09-29
- **Notes:** **Wave 7.** PIP Task 6.3 & PRD F-22. `backend/services/clustering.py` + `GET /api/admin/clusters`. Asynchronously assigns inquiries to within-topic clusters using cosine similarity threshold (0.85). Provides actions to rename canonical cluster text, merge clusters, or promote a cluster to a curated answer.

##### BL-ADMIN-005 — Editorial Web Admin Portal UI in Nuxt 3 SPA
- **Status:** completed
- **Created:** 2026-09-29
- **Updated:** 2026-09-29
- **Notes:** **Wave 7.** PIP Task 6.6 & Admin UX Specification. Desktop-first Nuxt 3 SPA in `web/admin/`. Features question review list with filtering/sorting, question detail view with citation/validator metadata, topic analytics dashboard, content gaps queue, and curated answer editor with live Indonesian word counter adhering to shared counting rules.

##### BL-ADMIN-006 — Audit log tracking and retention policy purge
- **Status:** planned
- **Created:** 2026-09-29
- **Updated:** 2026-09-29
- **Notes:** **Wave 7.** PIP Task 6.7 & PRD F-37. Implements `audit_log` collection capturing destructive actions, curated answer changes, configuration updates, and manual crawler runs prior to execution. Includes automated retention purge utility adhering to `retention_months` policy.

---

### Operations & Deployments

Cloud Run, Firebase Hosting, environments, CI/CD.

#### Archive

##### BL-OPS-001 — Dev project Cloud Run backend & Firebase multi-site deployment
- **Status:** completed
- **Created:** 2026-09-15
- **Completed:** 2026-09-25
- **Updated:** 2026-09-25
- **Notes:** **Wave 2.** Configured GCP project `project-philip-501910` in `asia-southeast2`: Cloud Run backend (`tanya-iman-backend`), Firebase multi-site hosting (`tanya-iman-app-dev` for seeker app and `tanya-iman-admin-dev` for admin portal), and named Firestore database `tanya-iman`. Shipped automated `./deploy.sh` script.

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
