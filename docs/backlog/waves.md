# Backlog Resolution Waves

Tactical **order of work** for open and scheduled items in [backlog.md](backlog.md). Strategic phases stay in [Project Implementation Plan](../project-implementation-plan.md) (PIP).

**Last updated:** 2026-09-28 — Wave 1, 2, & 3 shipped; Wave 4 (Phone & OTP Auth) deferred to backlog on hold; Wave 5 (Corpus & RAG) planned next.

---

## What's Next *(2026-09-28)*

| # | Wave | Status | Scope |
|---|------|--------|-------|
| — | **Wave 1** | ✅ shipped | Foundation & Nuxt Shell — Pydantic schemas, storage layer parity, topics/config seeder, automated unit tests (**BL-FOUND-001**, **BL-AUTH-000**) |
| — | **Wave 2** | ✅ shipped | Dev Cloud Infrastructure — Cloud Run backend, Firebase hosting (seeker + admin), `deploy.sh` (**BL-OPS-001**) |
| — | **Wave 3** | ✅ shipped | Admin Authentication & Security Hardening — JWT login, refresh token, bcrypt, dual-layer RBAC, super_admin bootstrap, portal session store (**BL-SEC-001**, **BL-SEC-002**) |
| **4** | **Wave 4** | ⏸️ on_hold | Live Phone Auth (SMS & WhatsApp OTP) & Guest Conversion — (**BL-AUTH-001**, **BL-AUTH-002**, **BL-AUTH-003**, **BL-AUTH-004**) |
| **5** | **Wave 5** | 📋 planned | Corpus Ingestion & RAG Pipeline — 5-site crawler, token chunker, Vertex AI multilingual embeddings, Firestore vector retriever (**BL-CORP-001**, **BL-CORP-002**, **BL-CORP-003**, **BL-CORP-004**) |

**Next candidate:** **Wave 5 (Corpus Ingestion & Vector RAG Pipeline)** is the active planned wave.

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

### Wave 5 — Corpus Ingestion & Vector RAG Pipeline 📋 *(planned)*

**Status:** planned

**Impact:** [Corpus & Knowledge Base](backlog.md#corpus--knowledge-base) — PIP Phase 4 & PRD F-41.

**Scope:**
- 5-site web crawler honoring robots.txt and sitemaps with content-hash change detection (`crawler.py`).
- Article chunking with token bounds (200–400 tokens) and V2 forbidden-term screening (`chunker.py`).
- Vertex AI multilingual embeddings (`text-multilingual-embedding-002`) and Firestore vector upsert (`embedder.py`).
- Query-time filtered vector retriever (`retriever.py`).

| ID | Title | Depends on |
|----|-------|------------|
| **BL-CORP-001** | Five-site crawler with change detection and allowlist | — |
| **BL-CORP-002** | Article chunker with token bounds and forbidden-term screening | **BL-CORP-001** |
| **BL-CORP-003** | Multilingual embeddings and Firestore vector upsert | **BL-CORP-002** |
| **BL-CORP-004** | Vector retriever with query-time site allowlist | **BL-CORP-003** |
