# **Project Implementation Plan (PIP)**

**Project:** Tanya Iman \- Indonesian Theology Q&A for Muslim Seekers

**Version:** 1.0

**Date:** August 2026

---

## **1\. Document Purpose**

This document is the engineering build plan: what gets built, in what order, with what tests, and what must be true before each phase can start. It expands the product-level sequence in PRD §14 into deliverable tasks.

It is not a schedule. There are no dates and no effort estimates here, because both depend on team size and on the resolution of the blocking dependencies in §6 — several of which are editorial rather than technical. Sequencing and gates are what this document guarantees.

**Phase mapping to the PRD release plan (nine phases, 1:1):**

| PRD phase | PIP phases |
|---|---|
| P1 Prototype *(complete)* | — (historical) |
| P2 Production foundation | Phase 1, Phase 2 |
| P3 Identity | Phase 3 |
| P4 Corpus | Phase 4 |
| P5 Production answer engine | Phase 5 |
| P6 Editorial surface | Phase 6 |
| P7 Distribution | Phase 7 |
| P8 Pilot | Phase 8 |
| P9 Launch | Phase 9 |

Allowlist growth (F-42) is **post-v1.0**, after Phase 9.

---

## **2\. Development Infrastructure & Environments**

* **Version control:** Git, GitHub. Integration branch `dev`; releases from `main`. Branch rules in [Branching and Deployment Workflow](branching-and-deployment-workflow.md).
* **Backend:** Python 3.12 + **FastAPI** + Uvicorn. Dependencies managed with **`uv`** (`pyproject.toml` in `backend/`). Never `pip`, never bare `python`.
* **Frontend:** **Nuxt 3 (Vue 3) + Tailwind CSS in SPA mode (`ssr: false`)**, built to static output with `nuxt generate`. Two apps — `web/app/` (seeker) and `web/admin/` (editorial) — plus `web/shared/`. Tailwind is wired through Nuxt's built-in PostCSS support, **not** `@nuxtjs/tailwindcss`. Rationale and constraints: [Frontend Framework Decision — Nuxt](frontend-framework-decision-nuxt.md).
* **Android:** Capacitor wrapping `web/app/`'s static build, in `android/`.
* **Database:** Google Cloud Firestore, including vector search over `article_chunks`. Local development and automated tests use the **Firestore emulator** on separate ports and separate project IDs.
* **Hosting:** Backend on Cloud Run. Both frontends on Firebase Hosting as separate sites. Scheduled ingestion via Cloud Scheduler → Cloud Run job.
* **Secrets:** GCP Secret Manager for staging and production; `.env` files for development only.

### **2.1 Environments**

| `ENV` | Firestore | LLM | OTP | Purpose |
|---|---|---|---|---|
| `development` | Emulator (`127.0.0.1:8080`, project `tanya-iman-local`) | Live or `LLM_PROVIDER=fake` | Stubbed, fixed code | Local work |
| *tests* | Emulator (`127.0.0.1:8081`, project `tanya-iman-local-test`) | Always `fake` | Stubbed | Automated suite |
| `staging` | Real Firestore, staging project | Live | Live, test numbers only | QA, pilot |
| `production` | Real Firestore, production project | Live | Live | Launch |

> **Emulator isolation rule.** Automated tests must never point at the development emulator project. Test fixtures wipe all documents between tests; pointing them at the dev project destroys local work with no warning.

### **2.2 Core commands**

```bash
# Backend
cd backend && uv sync
cd backend && uv run uvicorn main:app --reload
cd backend && uv run pytest -v
cd backend && uv add <package>

# Firestore emulators
firebase emulators:start --only firestore --config firebase.json        # dev,  UI :4000
firebase emulators:start --only firestore --config firebase.test.json   # test, UI :4001

# Frontends
cd web/app   && npm install && npm run dev        # http://localhost:3000
cd web/admin && npm install && npm run dev        # http://localhost:3001
cd web/app   && npm run generate                  # → .output/public

# Android
cd web/app && npm run generate && npx cap sync android
cd android && ./gradlew bundleRelease
```

Copy `backend/.env.example` → `backend/.env` before the first run.

### **2.3 Configuration files that gate deployment**

| File | Contents | Gate |
|---|---|---|
| `backend/config/prompts/*.txt` | Classifier, composer, repair, judge prompts | Composer prompt requires editorial sign-off before P5 ships |
| `backend/config/responses.id.yml` | Refusal, no-grounding, rate-limit, error copy | Editorial sign-off before P5 |
| `backend/config/crisis_scripts.id.yml` | Crisis response and helpline numbers | **Blocking.** Editorial sign-off; numbers verified. No placeholder may reach staging |
| `backend/config/approved_sites.yml` | The five allowed domains | Changing it changes the product's core promise; requires a PRD update |
| `backend/tests/benchmark/questions.yml` | The 120-question benchmark | Must exist before Phase 5 can be evaluated |

---

## **3\. Phased Development Steps**

### **Phase 1: Foundation & Nuxt Shell**

**Goal:** A running Nuxt seeker app and a running FastAPI backend that talk to each other against the Firestore emulator, with the repository structure, tooling, and CI that every later phase assumes.

---

**Task 1.1 — Repository structure and tooling**

```
backend/          FastAPI service (uv, pyproject.toml)
web/app/          Nuxt 3 seeker app (ssr: false)
web/admin/        Nuxt 3 admin portal (ssr: false)
web/shared/       Shared API client + UI primitives (workspace package)
android/          Capacitor project (created in Phase 7)
docs/             This documentation set
```

- `backend/` initialised with `uv`, FastAPI, pytest, ruff
- Both Nuxt apps scaffolded with `ssr: false` and Tailwind via built-in PostCSS
- `firebase.json` and `firebase.test.json` for the two emulator configurations
- `.env.example` listing every variable in TDD §5.3
- CI on GitHub Actions: `uv run pytest`, `ruff check`, `npm run build` for both apps

---

**Task 1.2 — Firestore schema and storage layer**

Create `backend/storage/firestore.py` — the **only** module permitted to import the Firestore SDK.

- Collection accessors for `users`, `sessions`, `questions`, `likes`, `topics`, `articles`, `article_chunks`, `question_clusters`, `admin_users`, `admin_audit_log`, `system_config`, per TDD §3
- Composite indexes declared in `firestore.indexes.json`: `(created_at desc)`, `(topic_slug, created_at desc)`, `(is_refused, created_at desc)`, `(has_grounding, created_at desc)`
- Vector index on `article_chunks.embedding`
- Seed script for `system_config` (`retention_months=12`, `rate_limit_per_hour=30`, `similarity_threshold=0.72`) and the 13 topics from PRD Appendix A

Tests: `tests/test_storage.py`
- Every collection round-trips a document
- Seed script is idempotent — running it twice produces one copy of each topic
- Vector field persists and reads back at the declared dimensionality

---

**Task 1.3 — Nuxt seeker app shell**

`web/app/`:

- Layout with a mobile-first container (360px design baseline), safe-area padding, and a footer carrying the Privacy Policy link (**F-4**)
- Routes: `/` (welcome), `/chat`, `/privasi`
- `useRuntimeConfig()`-backed composable exposing `NUXT_PUBLIC_API_BASE` and the Firebase config — no scattered `import.meta.env`
- Indonesian message catalogue at `locales/id.json`; no hardcoded user-facing string anywhere in a component
- `?embed=1` query parameter suppresses outer chrome (prepares Phase 7 without building it)

Tests: `web/app/tests/`
- Welcome screen renders all three sign-in options (**F-1**)
- Privacy Policy link is present on every route (**F-4**)
- Embed mode hides outer chrome

---

**Task 1.4 — Shared API client**

`web/shared/api/`:

- Typed client for every route in TDD §4.1
- Attaches the Firebase ID token to every request; refreshes on 401 once, then signs out
- Maps HTTP 429 to a typed rate-limit result carrying `retry_after_seconds`, so the UI never parses an error string
- Sends the `platform` hint (`web` \| `widget` \| `android`) — analytics only, never behaviour (**F-40**)

---

**Task 1.5 — Health endpoint and env guard**

`backend/main.py`:

- `GET /api/health` → `{status, env, prompt_version, corpus_chunk_count}`
- Startup aborts when `ENV=development` and `FIRESTORE_EMULATOR_HOST` is unset
- CORS configured from `CORS_ORIGINS`

**Phase 1 Test Requirements**

| Test file | Coverage |
|---|---|
| `tests/test_health.py` | Health shape; env reported correctly |
| `tests/test_storage.py` | Collection round-trips; seed idempotency; vector persistence |
| `web/app/tests/welcome.spec.ts` | Three sign-in options; privacy link; embed mode |

All green via `cd backend && uv run pytest -v` and `npm run test` in each app.

---

### **Phase 2: Chat Core & Guest Access**

**Goal:** A guest user can open the app, ask a question, and receive an answer end to end — using a stub answer engine at prototype parity. Every piece of the request path except the intelligence exists and is tested.

---

**Task 2.1 — Guest authentication**

- Client: Firebase Anonymous Auth on "Lanjutkan sebagai Tamu" (**F-3**)
- Backend: `verify_token` dependency resolving a Firebase ID token to a `users` record, creating it on first sight with `auth_method: guest`
- No personal data written for guests (**PRD §7.4**)

Tests: `tests/test_auth_guest.py`
- First request creates the user record
- Second request reuses it
- No phone fields are written for a guest
- Missing or invalid token → 401

---

**Task 2.2 — Session service**

`backend/services/session.py`:

- `create_session(uid, platform, embed_origin) -> Session`
- `append_turn(session, question, answer)`
- `recent_turns(session, n=2)` — the context window used by retrieval and composition
- `expires_at` set 24h past `last_message_at`; Firestore TTL policy configured

Tests: `tests/test_session_service.py`
- Session belongs to its user; a foreign uid cannot read it
- `recent_turns` returns at most 2 and in chronological order
- Expiry is recalculated on every turn

---

**Task 2.3 — Input bounds and rate limiter**

`backend/services/guards.py`:

- Reject empty input and input over 1,000 characters
- `check_rate_limit(uid) -> RateLimitResult` — 30 per rolling hour (**F-16**), transactional Firestore counter keyed `{uid}:{hour_bucket}`, limit read from `system_config`
- On trip: HTTP 429 with `retry_after_seconds` and the §10.6 copy

Tests: `tests/test_guards.py`
- 30 messages pass, the 31st returns 429
- The counter resets at the window boundary
- Two concurrent requests at the boundary cannot both pass (transactional guarantee)
- Limit is read from config, not hardcoded

---

**Task 2.4 — `POST /api/chat/ask` with a stub engine**

`backend/routers/chat.py` + `backend/engine/stub.py`:

- Full request path: auth → bounds → rate limit → **stub engine** → persist → respond
- The stub returns a fixed grounded answer with two citations drawn from seeded article records, so the response contract in TDD §4.1 is real and testable from day one
- Persists a complete `questions` record including `answer_source`, `latency_ms`, and `citations`

Tests: `tests/test_chat_ask.py`
- Response matches the documented shape exactly
- A `questions` document is written with every required field
- Rate limit trips inside this route, not only in isolation
- Over-length input returns 422 before any engine call

---

**Task 2.5 — Chat UI**

`web/app/pages/chat.vue`:

- Greeting and the persistent source note (**F-6**), per Chat UX Spec §3
- Free-text input and send (**F-7**); multi-turn scrolling transcript (**F-8**)
- Typing indicator while a request is in flight; send disabled, input still editable (**F-26**)
- Error state with **Coba lagi** that resubmits without retyping (**F-27**)
- Rate-limit state rendering the countdown from `retry_after_seconds`
- Citations rendered as tappable links that open in a new tab

Tests: `web/app/tests/chat.spec.ts`
- Question appears optimistically; answer appends below it
- Send is disabled while pending, re-enabled after
- Error state offers retry and resubmits the identical text
- Citations render as links with the correct hosts

---

**Task 2.6 — Like**

- `POST` / `DELETE /api/chat/answers/{question_id}/like`, document ID `{uid}_{question_id}` making it idempotent by construction (**F-33**)
- Denormalised `like_count` on `questions` and a distributed counter on `topics` (**F-18**)
- The Like control renders only when the response carries `likeable: true` (**F-17**) — the frontend reads the flag rather than reimplementing the rule

Tests: `tests/test_likes.py`
- Double-like produces one document and one increment
- Unlike decrements and cannot go below zero
- A refusal response returns `likeable: false` and the like route rejects it

**Phase 2 Test Requirements**

| Test file | Coverage |
|---|---|
| `tests/test_auth_guest.py` | Anonymous identity lifecycle |
| `tests/test_session_service.py` | Session ownership, context window, expiry |
| `tests/test_guards.py` | Bounds, rate limit, concurrency |
| `tests/test_chat_ask.py` | Full request path with the stub engine |
| `tests/test_likes.py` | Idempotency, counters, refusal rejection |
| `web/app/tests/chat.spec.ts` | Transcript, pending, error, retry, citations |

Manual verification: with the emulator running, a guest can ask three questions in a row and see three answers with working links.

---

### **Phase 3: Identity — SMS, WhatsApp, and Admin Auth**

**Goal:** All three sign-in paths work end to end, guest conversion preserves the conversation, and the admin authentication system exists ahead of the portal that will use it.

**Dependencies:** OTP provider account provisioned (PRD OD-1); Firebase project with phone auth enabled.

---

**Task 3.1 — SMS sign-in (F-2)**

- Client: Firebase Phone Auth via the JS SDK on web
- Backend: records `auth_method: sms`, encrypts the phone number with `PHONE_ENCRYPTION_KEY`, stores the HMAC in `phone_hash` for lookup
- OTP throttle accounting: 3 requests per number per hour (**F-24**)

Tests: `tests/test_auth_phone.py`
- Phone number is stored encrypted, never in plaintext
- `phone_hash` finds an existing user without decryption
- The 4th code request within an hour is refused with the cooldown message

---

**Task 3.2 — WhatsApp OTP (F-2)**

`backend/providers/otp.py` with a provider interface and a Twilio Verify implementation:

- `POST /api/auth/otp/request` dispatches over WhatsApp
- `POST /api/auth/otp/verify` verifies, then mints a **Firebase custom token** for that phone number
- Client exchanges the custom token for an ID token; the rest of the system cannot tell the two OTP channels apart
- 5 verification attempts per code (**F-24**)
- `ENV=development` returns a fixed code `000000` and never calls the provider

Tests: `tests/test_auth_whatsapp.py`
- Successful verification returns a custom token
- Wrong code fails; the 6th attempt is refused regardless of correctness
- Provider errors surface as a user-facing Indonesian message, not a stack trace
- Development mode never touches the network

---

**Task 3.3 — Guest conversion (F-25)**

`POST /api/auth/convert`:

- Re-points the anonymous UID's `sessions`, `questions`, and `likes` at the phone UID
- Marks the anonymous record `superseded_by`
- Runs in a batch so a partial merge is impossible

Tests: `tests/test_auth_convert.py`
- Sessions and questions follow the user
- Likes are not duplicated when both identities liked the same answer
- Conversion is idempotent
- A second conversion attempt on a superseded record is rejected

---

**Task 3.4 — Sign-out (F-5)**

- Clears the Firebase session and local state, returns to the welcome screen
- The on-device transcript is cleared; server records are untouched

---

**Task 3.5 — Admin authentication (F-19)**

`backend/routers/admin_auth.py`:

- `POST /api/admin/auth/login` → access token (1h) + refresh token (30d, stored hashed)
- `POST /api/admin/auth/refresh`
- bcrypt password hashing; roles `editor`, `reviewer`, `super_admin`
- `require_admin(role)` dependency, with the role re-checked in the service layer (**PRD §7.4**)
- `POST /api/admin/bootstrap` seeds the first `super_admin`; returns 403 when `ENV=production`

Tests: `tests/test_admin_auth.py`
- Login issues both tokens; the password is never returned
- An expired access token is rejected; refresh issues a new one
- A `reviewer` token is rejected on a `super_admin` route **by the service**, verified by calling the service directly with the wrong role
- Bootstrap is blocked in production
- No route under `/api/admin/` responds without a token

**Phase 3 Test Requirements**

| Test file | Coverage |
|---|---|
| `tests/test_auth_phone.py` | SMS path, encryption, OTP throttle |
| `tests/test_auth_whatsapp.py` | Provider abstraction, custom token, attempt limits |
| `tests/test_auth_convert.py` | Guest conversion integrity |
| `tests/test_admin_auth.py` | JWT lifecycle, role enforcement at both layers |

Manual verification on staging with real test numbers: SMS sign-in on an Android device, WhatsApp sign-in on the same device, and a guest-to-SMS conversion that keeps the visible conversation.

---

### **Phase 4: Corpus — Crawl, Chunk, Embed**

**Goal:** Every approved site is crawled, chunked, embedded, and searchable. Version 1.0 is the fixed five sites; F-42 (admin add site → crawl) is post-v1.0. Scheduled crawl of the five is in scope (F-43).

**Dependencies:** Written confirmation that crawling and content reuse are permitted (PRD §12).

---

**Task 4.1 — Crawler**

`backend/ingestion/crawler.py`:

- Reads `backend/config/approved_sites.yml`; a URL outside it is dropped, not warned about
- Sitemap-first with an HTML-link fallback
- Honours `robots.txt`; configurable politeness delay; identifying User-Agent
- Main-content extraction stripping navigation, sidebars, comments, and footers
- `content_hash` change detection — an unchanged article costs one conditional GET and no writes

Tests: `tests/test_crawler.py`
- Off-allowlist URLs are dropped
- Unchanged content produces zero writes on a second run
- Extraction removes known boilerplate from a fixture page per site
- `robots.txt` disallow is honoured

---

**Task 4.2 — Chunking**

`backend/ingestion/chunker.py`:

- ~400 token windows, ~80 token overlap, split on heading and paragraph boundaries
- Denormalises `article_id`, `site`, `url`, and `title` onto every chunk
- **Flags any chunk containing a V2 forbidden term** ("Tuhan", "TUHAN", "Yesus") into a review collection — this is the OI-1 mitigation from the AI Answer Engine Spec §8.2 and must exist before Phase 5

Tests: `tests/test_chunker.py`
- Chunks stay within the token bound
- Overlap is present between adjacent chunks
- A chunk never spans two articles
- Forbidden-term chunks are flagged, not silently indexed

---

**Task 4.3 — Embedding and upsert**

`backend/ingestion/embedder.py`:

- Vertex AI `text-multilingual-embedding-002`, batched
- Writes `embedding_model` onto every chunk
- Upserts articles and chunks; retires chunks whose parent article vanished
- Resumable: an interrupted run restarts from the last completed article

Tests: `tests/test_embedder.py`
- Embeddings are written at the declared dimensionality
- A model-identifier change marks affected chunks stale
- Retired articles' chunks leave the searchable set
- A run interrupted mid-way resumes without duplicating

---

**Task 4.4 — Retriever**

`backend/engine/retriever.py`:

- Firestore `find_nearest` over `article_chunks`, filtered on the approved-site list **at query time**, redundantly with the crawler
- `top_k=8` retrieved, re-ranked, top 4 returned; max 2 chunks per article
- Threshold from `system_config`; fewer than 2 survivors → no-grounding signal
- Query text is the question plus the last two turns

Tests: `tests/test_retriever.py`
- A known question retrieves its known source article
- An off-topic query returns nothing above threshold
- The site filter is applied even when a rogue chunk exists in the collection (insert one deliberately)
- No more than 2 chunks from one article are returned

---

**Task 4.5 — Retrieval benchmark**

`backend/tests/benchmark/retrieval.yml` — 40 questions with expected source articles.

- Reports recall@4 and mean reciprocal rank
- Used to tune the similarity threshold (**AI Spec OI-4**) rather than guessing it
- Runs in CI on any change to chunking, embedding, or retrieval parameters

**Phase 4 Test Requirements**

| Test file | Coverage |
|---|---|
| `tests/test_crawler.py` | Allowlist, change detection, extraction, robots |
| `tests/test_chunker.py` | Bounds, overlap, forbidden-term flagging |
| `tests/test_embedder.py` | Dimensionality, staleness, retirement, resumability |
| `tests/test_retriever.py` | Recall, threshold, site filter, per-article cap |
| `tests/benchmark/retrieval.yml` | recall@4 ≥ 0.85 on the benchmark set |

Verification: a full crawl of all five sites completes, `/api/health` reports a non-zero `corpus_chunk_count`, and the retrieval benchmark passes its gate.

---

### **Phase 5: Production Answer Engine**

**Goal:** Replace the stub with the real pipeline: crisis guard, classifier, curated override, retrieval, composition, and the five compliance validators.

**Dependencies — all blocking:**
- `crisis_scripts.id.yml` authored, editorially approved, helpline numbers verified (**AI Spec OI-2**)
- Emotional-deferral template + contact number configured (**PRD OD-7 / F-44–F-45**)
- Composer prompt editorially signed off (**AI Spec OI-3**)
- LLM provider Zero Data Retention terms confirmed in writing (**AI Spec OI-6 / PIP B3**)
- The 120-question benchmark set built by a native Indonesian speaker (**AI Spec OI-7**)
- OI-1 corpus terminology conflict resolved
- Phase 4 complete

---

**Task 5.1 — Crisis guard (F-30 – F-32)**

`backend/engine/crisis.py`:

- Runs **first**, before the rate limiter — a person in crisis who has hit their quota still gets the helpline
- Indonesian keyword and phrase list plus a semantic check
- Returns the approved script from config; never generates
- Records the question with `is_crisis: true`, `answer_source: crisis`, `likeable: false`, and excludes it from topic analytics

Tests: `tests/test_crisis_guard.py`
- Every phrase in the benchmark crisis bucket fires the guard — **100%, no exceptions**
- The response comes from config, verified by changing the fixture and seeing the output change
- No LLM call occurs on a crisis path (assert the provider mock was never called)
- A rate-limited user in crisis still receives the script
- Crisis questions do not appear in topic counters

---

**Task 5.2 — Relevance classifier and topic resolver (F-9, F-10)**

`backend/engine/classifier.py` — one structured call producing both outputs.

- Three-way result: `relevant` / `ambiguous` / `irrelevant`
- `ambiguous` proceeds as relevant and is flagged for admin review (**AI Spec §4.2**)
- `injection_attempt` flag set and refused
- Refusal returns §10.2 copy in under a second with no retrieval

Tests: `tests/test_classifier.py`
- Benchmark bucket 4 (out of scope) refuses at ≥95%
- Benchmark buckets 1 and 5 false-refuse at ≤5%
- Ambiguous results proceed and are flagged
- Injection attempts are refused and flagged
- Refusal path makes no retrieval and no composition call

---

**Task 5.3 — Curated answer override (F-23)**

`backend/engine/curated.py`:

- Published curated answer for the resolved topic → returned verbatim with its configured citations, `answer_source: curated`
- Draft curated answers are never served
- Runs before retrieval

Tests: `tests/test_curated.py`
- A published answer is returned byte-identical
- A draft answer is ignored and generation proceeds
- No retrieval or LLM call occurs on the curated path

---

**Task 5.4 — Answer composer (F-11 – F-15)**

`backend/engine/composer.py`:

- Prompt from AI Spec §9.2, versioned, `PROMPT_VERSION` stamped on output
- Passages supplied **indexed and without URLs** — the model can never emit a link
- Structured output per AI Spec §7.2
- Fallback model on primary error or beyond 7 s

Tests: `tests/test_composer.py`
- Passages are passed without URLs (assert the rendered prompt contains no `http`)
- Structured output parses; a malformed response is retried once then fails cleanly
- Fallback engages on primary timeout
- `prompt_version` and `model` are recorded on the question

---

**Task 5.5 — Compliance validators (F-28)**

`backend/engine/validators.py` — V1 through V5 per AI Spec §8, each returning typed failure codes.

- V1 word count, using the **single shared counting function** also used by the admin editor
- V2 terminology; rejects, never substitutes
- V3 scripture balance with Indonesian book-name and surah detection
- V4 citation provenance, allowlist, and liveness
- V5 grounding: Tier 1 always; Tier 2 judge on repairs, on 100% in staging, on 10% sampled in production
- One repair attempt, then the §10.5 fallback and an admin-visible log entry

Tests: `tests/test_validators.py`
- Each validator fails on a crafted violation and passes on a clean answer
- 24 words fails; 25 passes; 250 passes; 251 fails
- "Yesus" fails; "Isa Al-Masih" passes; a quoted "TUHAN" fails (documents the OI-1 behaviour explicitly)
- Two Quran references fail; one leading Quran reference with two Bible references passes
- A citation not in the retrieval result fails **and raises an alert**, because that is a system defect
- The repair loop runs exactly once, never twice
- A twice-failing answer returns the fallback and is never displayed

---

**Task 5.6 — Wire the pipeline and retire the stub**

`backend/engine/pipeline.py` — the node order in AI Spec §3, with the four ordering rules in §3.2 asserted by test rather than by comment.

Tests: `tests/test_pipeline.py`
- Crisis before rate limit
- Classification before retrieval
- Curated before retrieval
- Validation after every composition, including after repair
- Each of the eight exit paths returns a valid response contract

---

**Task 5.7 — Full benchmark harness**

`backend/tests/benchmark/` — the 120-question set with the gates from AI Spec §13.2.

- Runs in CI on any change to a prompt, validator, retrieval parameter, or model identifier
- Crisis recall of 100%, validator pass rate of 100%, and zero fabricated citations are **release-blocking**

**Phase 5 Test Requirements**

| Test file | Coverage |
|---|---|
| `tests/test_crisis_guard.py` | 100% recall; config-sourced; no LLM call; precedence |
| `tests/test_classifier.py` | Accuracy bands, ambiguous handling, injection |
| `tests/test_curated.py` | Verbatim serving, draft exclusion, short-circuit |
| `tests/test_composer.py` | No URLs to the model, structured output, fallback |
| `tests/test_validators.py` | All five rules, boundary values, repair loop |
| `tests/test_pipeline.py` | Node ordering, all eight exit paths |
| `tests/benchmark/` | The §13.2 release gates |

---

### **Phase 6: Editorial Surface — Admin Portal**

**Goal:** The editorial team can complete a full review cycle without engineering help: read questions, see topic demand and similar-question frequency, find content gaps, and publish curated answers.

**Dependencies:** Phase 5 complete (there is nothing meaningful to review before the engine is real).

---

**Task 6.1 — Question list API (F-20, F-35, F-36)**

`GET /api/admin/questions`:

- Cursor-based pagination, default 50
- Filters: date range, topic, refusal, crisis, grounding, validator failure, ambiguous flag
- Phone numbers masked in every response
- `GET /api/admin/questions/export` → CSV of the current filter, **never including phone numbers**

Tests: `tests/test_admin_questions.py`
- Each filter narrows correctly, alone and combined
- Pagination does not skip or repeat across pages
- Phone numbers are masked in list, detail, and export
- A `reviewer` can export; an `editor` cannot delete

---

**Task 6.2 — Topic analytics (F-21)**

`GET /api/admin/topics` — the 13 topics plus `lainnya`, each with question count, like count, curated status, and last update.

Tests: `tests/test_admin_topics.py`
- Counts match the underlying question records
- Crisis questions are excluded from topic counts (**F-32**)
- `lainnya` appears with its own count

---

**Task 6.3 — Similar-question clustering (F-22)**

`backend/services/clustering.py` + `GET /api/admin/clusters`:

- Async assignment on write, within-topic, threshold 0.85
- Nightly centroid recomputation
- Editor actions: rename canonical text, merge two clusters, promote a cluster to a curated answer

Tests: `tests/test_clustering.py`
- Near-identical questions join one cluster
- Clearly different questions seed separate clusters
- Clustering is within-topic; two same-worded questions in different topics do not merge
- Merge preserves the combined member count

---

**Task 6.4 — Content gaps (F-29, US-8)**

`GET /api/admin/gaps` — no-grounding questions, clustered, ordered by frequency. This is the editorial content queue.

---

**Task 6.5 — Curated answer editing (F-23, F-34)**

`PUT /api/admin/topics/{slug}/answer`:

- Runs V1–V4 before save, using the same validator module as the runtime
- `draft` / `published` status; only `published` is served
- Records `updated_by` and `updated_at`; writes to the audit log

Tests: `tests/test_admin_curated.py`
- A 300-word answer is rejected with `V1_TOO_LONG`
- An answer containing "Yesus" is rejected with `V2_FORBIDDEN_TERM`
- An off-allowlist citation is rejected
- Publishing changes what `/api/chat/ask` returns for that topic, verified end to end
- Every save writes an audit entry

---

**Task 6.6 — Admin portal UI**

`web/admin/` — Nuxt 3 SPA, desktop-first, per [Admin UX Specification](admin-ux-specification.md).

- Login, Question List, Question Detail, Topics, Clusters, Content Gaps, Settings
- Access token in memory only; refresh token in an httpOnly cookie
- Role badge in the header; unavailable actions hidden rather than disabled
- Curated answer editor with a live word counter driven by the same counting rule as the backend

---

**Task 6.7 — Audit log and retention (F-37)**

- Every delete, curated-answer change, config change, and manual ingestion run writes an audit entry **before** execution
- Daily retention purge job reading `retention_months`, writing a summary to the audit log

Tests: `tests/test_admin_audit.py`
- A failed action commits no audit entry
- The purge deletes only records past the window and logs the count

**Phase 6 Test Requirements**

| Test file | Coverage |
|---|---|
| `tests/test_admin_questions.py` | Filters, pagination, masking, export, roles |
| `tests/test_admin_topics.py` | Counts, crisis exclusion |
| `tests/test_clustering.py` | Assignment, seeding, within-topic scope, merge |
| `tests/test_admin_curated.py` | Validator parity, publish effect, audit |
| `tests/test_admin_audit.py` | Pre-action logging, purge |

Verification: an editor completes one full cycle unaided — filter last 30 days, identify the top topic, read ten raw questions, write and publish a curated answer, then confirm the chat app returns it.

---

### **Phase 7: Distribution — Widget and Android**

**Goal:** The same Nuxt build reaches users through a WordPress embed and an Android app.

**Dependencies:** Phase 5 complete. Google Play Developer account provisioned.

---

**Task 7.1 — Embed mode and `embed.js` (F-38)**

- Build emits `embed.js`: a dependency-free loader that creates the iframe, sizes it to the host container width, negotiates height over `postMessage`, and passes the host URL for attribution
- Backend sends `Content-Security-Policy: frame-ancestors` listing exactly the five approved domains
- App renders correctly from 320px upward in embed mode

Tests: `web/app/tests/embed.spec.ts` + `tests/test_csp.py`
- Height messages resize the iframe
- A non-approved origin is refused by `frame-ancestors`
- Layout holds at 320px

---

**Task 7.2 — Widget authentication behaviour**

Firebase phone auth's reCAPTCHA challenge is unreliable in a third-party iframe.

- Test the SMS flow inside a real WordPress page early in this phase
- If it fails: the widget offers Guest only, plus a "buka di tab baru" link to the standalone app for users who want to sign in
- Whichever path holds, the behaviour is explicit and tested, not discovered in production

---

**Task 7.3 — Capacitor Android project (F-39)**

- `android/` created; `webDir` points at `web/app/.output/public`
- `@capacitor-firebase/authentication` for native phone auth, behind the same auth abstraction the web uses
- Safe-area insets via CSS environment variables in the root layout
- Hardware back button pops in-app navigation first; confirms before exiting mid-conversation
- HTTPS-only enforced; the baked API base URL validated in CI

Tests: manual on a physical device, matrix in Annex-style form:

| # | Case | Pass condition |
|---|---|---|
| A1 | Cold start on Android 10 and Android 14 | Welcome screen renders, safe areas correct |
| A2 | SMS sign-in with auto-retrieval | Code fills automatically; sign-in completes |
| A3 | WhatsApp sign-in | Completes; identity matches the web flow |
| A4 | Ask 3 questions offline then online | Clear offline error; recovery on reconnect |
| A5 | Back button mid-conversation | Confirm prompt; does not exit silently |
| A6 | Citation link tap | Opens in the external browser, not inside the WebView |
| A7 | Rotate device mid-answer | No loss of transcript |

---

**Task 7.4 — Play Store listing preparation**

Per risk R3: listing copy describing purpose and audience, content rating questionnaire, data-safety declaration matching what the app actually collects, and privacy policy URL. Detail in [Android & WordPress Distribution Runbook](android-and-wordpress-distribution-runbook.md).

**Phase 7 Test Requirements**

| Layer | How |
|---|---|
| Embed | `web/app/tests/embed.spec.ts`; manual on a staging WordPress page |
| CSP | `tests/test_csp.py` |
| Android | Manual device matrix A1–A7 |
| Parity | The same three questions produce identical answers on web, widget, and Android (**F-40**) |

---

### **Phase 8: Pilot Readiness**

**Goal:** Staging is stable, observable, and safe enough to put in front of real testers.

**Dependencies:** Phases 5, 6, 7 complete.

---

**Task 8.1 — Observability**

Per TDD §7: latency by `answer_source`, validator failure rate by code, refusal and no-grounding rates, crisis fires, LLM cost per 1,000 answers, corpus freshness, 429 rate. Alerts on validator failure rate, crisis fire volume, and ingestion job failure.

**Task 8.2 — Staging data hygiene**

Reset procedure that clears `users`, `sessions`, `questions`, `likes`, and clusters while preserving `articles`, `article_chunks`, `topics`, and `admin_users`. Blocked in production.

**Task 8.3 — Load sanity check**

50 concurrent askers for 10 minutes against staging. Confirm average answer time stays inside **5 s** (PRD K5), no Firestore contention on the rate-limit counter, and Cloud Run scales without errors.

**Task 8.4 — Run the pilot**

Per [Pilot Plan](pilot/pilot-plan.md). Feedback captured on the templates in `docs/pilot/`.

**Phase 8 Test Requirements**

| Layer | How |
|---|---|
| Monitoring | Every alert deliberately triggered once and confirmed to fire |
| Reset | Verified to clear user data and preserve corpus |
| Load | Average answer time < 5 s at 50 concurrent |
| Pilot | Exit criteria in the Pilot Plan |

---

### **Phase 9: Launch**

**Goal:** Widget live on the WordPress sites, app live on the Play Store, KPI baselines captured.

**Task 9.1 — Production environment** — separate GCP project, secrets in Secret Manager, production Firestore with indexes, first full corpus crawl.

**Task 9.2 — Play Store submission** — signed AAB, complete listing, submission. Budget one rejection-and-resubmit cycle (risk R3).

**Task 9.3 — Widget rollout** — one host site first, then the remaining four after 7 days of clean metrics (PRD OD-5).

**Task 9.4 — Baselines** — record K1 through K9 in the first fortnight; K4 and K9 are gates, and a regression in either triggers rollback rather than investigation-in-place.

**Task 9.5 — Handover** — runbook walkthrough with whoever operates this after launch: how to read the admin portal, how to publish a curated answer, how to trigger ingestion, how to roll back a prompt version, and who to call.

**Phase 9 Test Requirements**

| Layer | How |
|---|---|
| Production smoke | All three sign-in paths, one question per topic, one refusal, one crisis phrase (on a staging clone, never production) |
| Widget | Live on the first host site; questions attributed to `embed_origin` |
| Android | Internal test track install from the Play Store build |
| Rollback | Prompt version reverted and redeployed as a rehearsal, not a theory |

---

## **4\. Test Plan & QA Strategy**

**Principle:** Every feature ships with tests. No feature is complete until `cd backend && uv run pytest -v` is green and the benchmark gates pass.

### **4.1 Unit tests**

| Module | Test file | Key cases |
|---|---|---|
| `services/guards.py` | `test_guards.py` | Bounds, 30/hour, window reset, concurrency |
| `services/session.py` | `test_session_service.py` | Ownership, context window, expiry |
| `engine/crisis.py` | `test_crisis_guard.py` | 100% recall, config-sourced, precedence, no LLM |
| `engine/classifier.py` | `test_classifier.py` | Accuracy bands, ambiguous, injection |
| `engine/retriever.py` | `test_retriever.py` | Recall, threshold, allowlist, per-article cap |
| `engine/validators.py` | `test_validators.py` | V1–V5, boundaries, repair loop |
| `ingestion/*` | `test_crawler.py`, `test_chunker.py`, `test_embedder.py` | Allowlist, change detection, flagging, resumability |

### **4.2 Integration tests**

| Test file | Key cases |
|---|---|
| `test_chat_ask.py` | Full request path; response contract; all eight exit paths |
| `test_pipeline.py` | Node ordering rules asserted, not assumed |
| `test_admin_questions.py` | Filters, pagination, masking, export, role enforcement |
| `test_admin_curated.py` | Validator parity between editor and runtime; publish takes effect |

### **4.3 Benchmark tests (release gates)**

The 120-question set from AI Spec §13, run in CI on any change to prompts, validators, retrieval parameters, or model identifiers.

| Gate | Threshold |
|---|---|
| Crisis recall | 100% — blocks release |
| Validator pass rate at display | 100% — blocks release (K4) |
| Fabricated citations | 0 — blocks release |
| Refusal accuracy | ≥95% |
| False refusal | ≤5% |
| Average latency | < 5 s |

### **4.4 Manual E2E (per phase, on staging)**

- **Case A — Happy path.** Guest asks a covered question; answer is 25–250 words, uses only "Allah" and "Isa Al-Masih", carries 1–2 working links, and can be liked.
- **Case B — Refusal.** Ask for a football score; standard refusal in under a second, no Like control.
- **Case C — No grounding.** Ask a spiritual question outside the corpus; the §10.3 response appears and the question shows in the admin Content Gaps view.
- **Case D — Crisis.** Send an approved crisis test phrase; the scripted response with helplines appears, no generation occurs, and the event is excluded from topic counters.
- **Case E — Rate limit.** Send 31 messages in an hour; the 31st shows the countdown message.
- **Case F — Curated override.** Publish a curated answer, then ask a question on that topic; the exact curated text is returned.
- **Case G — Guest conversion.** Ask two questions as a guest, sign in with SMS, and confirm the transcript survives.
- **Case H — Channel parity.** The same question on web, in the WordPress widget, and in the Android app returns the same answer.

### **4.5 Human answer review**

20 sampled real answers per week during the pilot, monthly after launch, scored for tone, theological accuracy, and whether the answer addressed the question. Validators measure compliance; only a person measures quality.

---

## **5\. Security & Privacy Review Checkpoints**

Reviewed at the end of every phase, and formally before Phase 8 and Phase 9.

- No secret is committed. `.env` is git-ignored; CI scans for credential patterns
- Phone numbers are encrypted at rest, looked up by HMAC, masked in every admin view, and excluded from CSV export
- Guest identity is not derivable from device attributes and is not linked to a phone identity without explicit conversion
- Firestore rules deny all client access; the backend is the only writing principal
- Admin role checks exist in both the route dependency and the service layer, and the service-layer check is tested directly
- LLM provider Zero Data Retention terms confirmed in writing before the first real question is sent (PIP B3)
- `frame-ancestors` lists exactly the five approved domains
- Every destructive admin action writes to the audit log before executing
- Retention purge runs, and is verified to delete only what it should
- Crisis and emotional-deferral templates contain no placeholder; numbers have recorded verification dates

---

## **6\. Blocking Dependencies**

Each of these stops a phase from starting, and none of them is an engineering task. They should be opened as soon as this plan is approved.

| # | Dependency | Blocks | Owner |
|---|---|---|---|
| B1 | Crisis template authored, approved, helplines verified | Phase 5 | Editorial |
| B2 | Composer prompt and refusal / template copy editorially signed off | Phase 5 | Editorial |
| B3 | LLM provider Zero Data Retention terms confirmed in writing | Phase 5 | Client / Legal + Engineering |
| B4 | 120-question benchmark set built in Indonesian | Phase 5 evaluation | Editorial + Engineering |
| B5 | Written confirmation that crawling and content reuse are permitted | Phase 4 | Product |
| B6 | OTP provider account and cost ceiling agreed (PRD OD-1) | Phase 3 | Product |
| B7 | Google Play Developer account | Phase 7 | Product |
| B8 | Corpus terminology conflict resolved (AI Spec OI-1) | Phase 5 | Editorial + Engineering |
| B9 | Privacy Policy published at a stable URL | Phase 2 (link) and Phase 7 (Play) | Product + Legal |
| B10 | Emotional-deferral contact number + template approved (PRD OD-7) | Phase 5 | Editorial |

---

## **Related Documents**

| Document | Purpose |
|---|---|
| [Product Requirements Document](prd.md) | Requirements and KPIs |
| [Technical Design Document](tdd.md) | Architecture and data model |
| [AI Answer Engine Specification](ai-answer-engine-specification.md) | Pipeline, prompts, validators, benchmark |
| [Frontend Framework Decision — Nuxt](frontend-framework-decision-nuxt.md) | Frontend architecture |
| [Content Ingestion & RAG Runbook](content-ingestion-and-rag-runbook.md) | Corpus operations |
| [Deployment Guide](deployment-guide.md) | Environments and deploys |
| [Branching and Deployment Workflow](branching-and-deployment-workflow.md) | Branch and merge rules |
| [Pilot Plan](pilot/pilot-plan.md) | Pilot scenarios and exit criteria |
