# Tanya Iman — Documentation

Planning and specification documents for **Tanya Iman**, an Indonesian-language theology Q&A assistant for Muslim seekers. Answers come only from a crawled corpus of **five** approved religious-dialogue websites (fixed in v1.0; growth is post-v1.0). Every chat is handled by the AI. Emotional-only questions and crisis signals receive **templates** (including an admin-configured contact number), not model composition. It ships as a WordPress widget and an Android app, with an editorial admin portal behind it.

**Frontend stack:** Nuxt 3 (Vue 3) + Tailwind CSS in SPA mode, built to static files — one artefact serving web, widget, and Android. (Product brief assumed React; Nuxt is the decided stack.)

**Authoritative requirements:** [`prd.md`](./prd.md) (v1.1). The Aug 2026 Word / brief concepts are absorbed there; `init.md` has been removed as obsolete.

---

## Where to start

| If you are… | Read, in this order |
|---|---|
| **New to the project** | [PRD](./prd.md) → [TDD](./tdd.md) → [Project Implementation Plan](./project-implementation-plan.md) |
| **Building the frontend** | [Frontend Framework Decision — Nuxt](./frontend-framework-decision-nuxt.md) → [Chat UX Specification](./chat-ux-specification.md) → [Admin UX Specification](./admin-ux-specification.md) |
| **Building the answer engine** | [AI Answer Engine Specification](./ai-answer-engine-specification.md) → [Content Ingestion & RAG Runbook](./content-ingestion-and-rag-runbook.md) |
| **Deploying or operating** | [Deployment Guide](./deployment-guide.md) → [Android & WordPress Distribution Runbook](./android-and-wordpress-distribution-runbook.md) → [Branching and Deployment Workflow](./branching-and-deployment-workflow.md) |
| **Picking up work today** | [Project Implementation Plan](./project-implementation-plan.md) — Phases 1–9 |
| **Running the pilot** | [pilot/Pilot Plan](./pilot/pilot-plan.md) |

---

## Document map

### Product

| Document | What it decides |
|---|---|
| [Product Requirements Document (PRD)](./prd.md) | Scope, requirements F-1 – F-45, user stories, KPIs, risks, **nine phases** P1–P9. **The authoritative requirement set** |

### Architecture & design

| Document | What it decides |
|---|---|
| [Technical Design Document (TDD)](./tdd.md) | Components, Firestore data model, API surface, environments, security |
| [Frontend Framework Decision — Nuxt](./frontend-framework-decision-nuxt.md) | Nuxt 3 SPA, why not React/SSR, how one build serves web + widget + Android |
| [AI Answer Engine Specification](./ai-answer-engine-specification.md) | Pipeline, Indonesian prompts, validators, template paths, benchmark gates |

### Experience

| Document | What it decides |
|---|---|
| [Chat UX Specification](./chat-ux-specification.md) | Seeker screens, every response state (including emotional deferral), embed and Android |
| [Admin UX Specification](./admin-ux-specification.md) | Editorial portal: questions, topics, clusters, gaps, curated answers, contact config |

### Build & operate

| Document | What it decides |
|---|---|
| [Project Implementation Plan](./project-implementation-plan.md) | Phases 1–9, tasks, tests, blocking dependencies |
| [Content Ingestion & RAG Runbook](./content-ingestion-and-rag-runbook.md) | Crawl, chunk, embed, refresh (five sites in v1.0) |
| [Deployment Guide (Google Cloud & Firebase)](./deployment-guide.md) | Projects, secrets, deploys, rollback, pre-launch checklist |
| [Android & WordPress Distribution Runbook](./android-and-wordpress-distribution-runbook.md) | Widget embed and QA; Play Store build, listing, tracks |
| [Branching and Deployment Workflow](./branching-and-deployment-workflow.md) | Branch naming, PR flow, what may deploy from where |

### Pilot

| Document | Purpose |
|---|---|
| [pilot/Pilot Plan](./pilot/pilot-plan.md) | Scenarios, schedule, exit criteria |
| [pilot/Pilot Session Log Template](./pilot/pilot-session-log-template.md) | Per-session record |
| [pilot/UX Feedback Report Template](./pilot/ux-feedback-report-template.md) | Per-participant experience |
| [pilot/AI Answer Quality Report Template](./pilot/ai-answer-quality-report-template.md) | Editorial review of answer quality |

---

## The things that block everything else

Listed in [PIP §6](./project-implementation-plan.md). Highest priority:

1. **Crisis template and helpline numbers** — editorial approval before Phase 5. A wrong number is a P0 defect. Template only; no AI composition.
2. **Emotional-support contact number and deferral template** (F-44 / F-45, OD-7) — same gate as Phase 5.
3. **Zero Data Retention terms** must be confirmed in writing before any real user question reaches a model provider (PIP B3).
4. **Crawl permission** for the five sites — blocks Phase 4.

---

## Conventions

- **Requirement IDs** — `F-1` through `F-45` in [PRD §6](./prd.md). F-1–F-23 from the Aug 2026 brief; later IDs are upgrades (see PRD Appendix B).
- **KPI IDs** — `K1` – `K9` in PRD §11. K4 and K9 are gates. **K5** is average answer time **&lt; 5 s** (brief).
- **Open decisions** — `OD-1` – `OD-7` in the PRD; `OI-*` in the AI Answer Engine Specification; `B1` – `B9` (updated) in the PIP.
- **Phases** — Nine phases **P1–P9** in the PRD; PIP Phases 1–9 map 1:1 (see PIP §1).
- **Roles** — Prefer **editorial** / **content reviewer** (neutral). Avoid “pastoral” in product copy and role names.
- **Indonesian** — all user-facing copy is Indonesian; these docs are in English.
