# AGENTS.md

Guidance for AI coding agents and new contributors working in this repository.

## Project overview

**Tanya Iman** is an Indonesian-language theology Q&A assistant for Muslim seekers. Users ask about Allah, Isa Al-Masih, the Holy Scripture, or a faith-related question, and receive a 25–250 word Indonesian answer **drawn only from the crawled corpus of five approved religious-dialogue websites** (fixed in v1.0), with 1–2 links back to the source articles. Answers must sound **empathetic** without treating emotional subjects as the topic.

Every chat is handled by the AI. There is no human agent in the loop. **Emotional-only**, **crisis**, **refusal**, and **no-grounding** paths use **templates** (not the composer). Emotional-only responses include a contact number configured in admin (F-44 / F-45).

It ships through an **Android app** on the Play Store and an **embedded WordPress widget** from one **Nuxt** codebase, with an editorial admin portal behind it.

All planning specifications live in [`docs/`](docs/README.md). Start with [`docs/prd.md`](docs/prd.md) — it is the authoritative requirement set. The code exists to serve those documents.

**Implementation status:** Phase 1 (skeleton) and Phase 2 (chat path on a stub engine) are scaffolded. The answer engine returns a fixed response; there is no corpus, no LLM call, no real auth. Phases 3–9 are specified in [`docs/project-implementation-plan.md`](docs/project-implementation-plan.md) and not yet built.

## The one rule that shapes everything

**No composed content reaches a user that did not come from the approved corpus.** Enforced structurally:

- The model never sees a URL, so it cannot invent a citation
- Citations can only come from the retrieval result for that request
- Five deterministic validators check every composed answer *after* generation and can reject it
- If retrieval finds nothing above threshold, a **no-grounding template** is returned — not model knowledge
- Emotional-only and crisis paths never call the composer

If a change makes any of those weaker, it is the wrong change.

## Tech stack

- **Frontend:** **Nuxt 3 (Vue 3) + Tailwind CSS, SPA mode (`ssr: false`)**, built with `nuxt generate`. Two apps: `web/app/` and `web/admin/`, plus `web/shared/`. Tailwind via Nuxt built-in PostCSS — **not** `@nuxtjs/tailwindcss`
- **Android:** Capacitor wrapping the same static build
- **Backend:** Python 3.12 + FastAPI + Uvicorn on Cloud Run; **`uv`** for deps
- **Database:** Firestore, including vector search over `article_chunks`
- **Auth:** Firebase Auth (phone + anonymous); WhatsApp OTP via a provider → Firebase custom token
- **LLM:** Claude Sonnet class primary on a **Zero Data Retention** tier, Gemini fallback, behind `backend/providers/llm.py`
- **Embeddings:** Vertex AI `text-multilingual-embedding-002`

## Architecture in one paragraph

A static Nuxt SPA talks to a stateless FastAPI service. Every question runs a fixed pipeline: input bounds → crisis guard → rate limiter → relevance classifier (`theology` / `emotional_only` / `irrelevant`) → topic resolver → curated override → vector retrieval → LLM composition → five compliance validators → response assembly. Template exit paths never call the composer. There is no agent and no tool-calling loop.

Full detail: [`docs/tdd.md`](docs/tdd.md) and [`docs/ai-answer-engine-specification.md`](docs/ai-answer-engine-specification.md).

## Repository layout

```
backend/
  config/        settings, YAML config, prompt templates   ← editorial sign-off applies here
  models/        Pydantic schemas and enums
  storage/       Storage protocol + memory and Firestore backends
  providers/     LLM and OTP adapters
  services/      guards, sessions, users, auth, text
  engine/        answer engines behind one interface       ← stub today, RAG in Phase 5
  routers/       FastAPI endpoints
  tests/
web/
  shared/        wire types, API client, word counter
  app/           seeker Nuxt SPA + embed.js
  admin/         editorial Nuxt SPA
```

## Development commands

**All backend commands use `uv`. Never `pip`, never bare `python`.**

```bash
cd backend && uv sync
cd backend && uv run uvicorn main:app --reload
cd backend && uv run pytest -v

npm install
npm run dev:app
npm run dev:admin
```

Copy `backend/.env.example` → `backend/.env` before the first run.

## Testing requirements

Nothing is complete until `cd backend && uv run pytest -v` is green. Prompt/validator/retrieval/model changes must pass the answer benchmark in CI (100% crisis recall, 100% validator pass rate, zero fabricated citations).

## Content rules the engine enforces

| Rule | Requirement | Validator |
|---|---|---|
| 25–250 words | F-11 | V1 |
| Only "Allah" and "Isa Al-Masih"; never "Tuhan" or "Yesus" | F-12 | V2 |
| At most one Quran reference, leading; Bible majority | F-13 | V3 |
| 1–2 citations, all from the approved five domains | F-14 | V4 |
| Every claim traceable to a retrieved passage | F-15 | V5 |

V2 rejects; it never auto-substitutes.

## Safety constraints

- **Crisis guard runs first**, before the rate limiter
- **Crisis, emotional-deferral, refusal, and no-grounding** come from **templates**, never the composer
- **A wrong helpline or contact number is a P0 defect.** No placeholder on staging/production
- Phone numbers are stored securely, masked in admin, never exported raw
- Guest anonymity is real — not derived from device attributes; not linked to phone without explicit conversion
- Prefer minimal LLM retention in practice; **Zero Data Retention is a hard constraint** — a provider that cannot contract for ZDR is disqualified (PIP B3)

## Assistant persona constraints

The composer must always:

- Acknowledge empathetically what the user said before explaining
- Answer only from the retrieved passages (theology subject only)
- Use only "Allah" and "Isa Al-Masih"
- Stay within 25–250 words
- Never write a URL — the assembler adds links
- Never discuss emotional subjects as the topic (defer emotional-only upstream)
- Never criticise Islam, Muslims, or the Quran
- Never state a person's salvation status
- Never promise an outcome
- Never ask for personal information
- Never argue. Answer once, kindly, and stop

## Branching

- Never commit directly to `main` or `dev`
- Branches: `feature/…` or `issue/…` only
- PRs merge into `dev`; production deploys from `main` only
- Prompt / response / crisis / emotional-template changes need **editorial** sign-off in the PR
- `approved_sites.yml` changes in v1.0 require a PRD update in the same PR

## Key reference documents

| Document | Purpose |
|---|---|
| [`docs/README.md`](docs/README.md) | Documentation index |
| [`docs/prd.md`](docs/prd.md) | Requirements F-1 – F-45, KPIs, phases |
| [`docs/tdd.md`](docs/tdd.md) | Architecture, data model, API |
| [`docs/ai-answer-engine-specification.md`](docs/ai-answer-engine-specification.md) | Pipeline, prompts, validators |
| [`docs/project-implementation-plan.md`](docs/project-implementation-plan.md) | Workstreams and blockers |
| [`docs/chat-ux-specification.md`](docs/chat-ux-specification.md) | Seeker UX |
| [`docs/admin-ux-specification.md`](docs/admin-ux-specification.md) | Editorial portal |
