# Tanya Iman

An Indonesian-language theology Q&A assistant for Muslim seekers. A user asks about Allah, Isa Al-Masih, the Holy Scripture, or a faith-related question, and receives a 25–250 word answer drawn only from a crawled corpus of **five** approved religious-dialogue websites (fixed in v1.0), with links back to the source articles. Answers are empathetic in tone but do not discuss emotional subjects as topics — emotional-only questions receive a contact template. Every chat is handled by the AI or by fixed templates; there is no human agent in the chat.

It ships as an Android app and as an embedded widget on WordPress sites, from one **Nuxt** codebase, with an editorial admin portal behind it.

**Documentation is the source of truth.** Start at [`docs/README.md`](docs/README.md) and [`docs/prd.md`](docs/prd.md). This file only covers getting the repository running.

## Status

Phases 1 and 2 of the [implementation plan](docs/project-implementation-plan.md) are scaffolded: the full request path exists — auth, sessions, guards, persistence, chat UI, likes — running against a **stub engine that returns a fixed answer**. There is no corpus, no LLM call, and no real authentication yet. That is deliberate; it is what allows Phases 3, 4, and 5 to proceed in parallel.

The application refuses to start outside development while `ANSWER_ENGINE=stub`, and refuses to start in staging or production while the crisis script is unapproved.

## Prerequisites

| Tool | Version | Notes |
|---|---|---|
| Python | 3.12+ | The backend targets 3.12 and will not install on 3.9 |
| [`uv`](https://docs.astral.sh/uv/) | latest | The only supported way to run backend commands |
| Node.js | 20+ | npm workspaces |
| Firebase CLI | latest | Only needed once you switch off the in-memory storage |

If you do not have Python 3.12, `uv` will fetch it for you — you do not need a system-wide install:

```bash
# Windows (PowerShell)
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS / Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

uv python install 3.12
```

## Setup

```bash
# Backend
cd backend
cp .env.example .env
uv sync --extra dev

# Frontend — one install at the repo root covers all three workspaces
cd ..
npm install
```

Commit the `package-lock.json` that first install produces. CI uses `npm ci`, which requires it.

## Run it

Three terminals:

```bash
cd backend && uv run uvicorn main:app --reload --port 8000
npm run dev:app      # http://localhost:3000
npm run dev:admin    # http://localhost:3001
```

Open http://localhost:3000, choose **Lanjut sebagai Tamu**, and ask a question. You will get the stub answer with one citation. SMS and WhatsApp login are disabled until Phase 3.

Nothing needs to be provisioned first. The defaults in `.env.example` use in-memory storage, a fake LLM, and development auth tokens, so the app runs with no Google Cloud project, no Firestore emulator, and no API keys.

## Verify

```bash
cd backend && uv run pytest -v
cd backend && uv run ruff check .
npm test
npm run typecheck
```

The suite covers the guard ordering that safety depends on, word counting on both sides of the stack, config integrity, and the chat endpoint end to end. Two tests are worth knowing about:

- `test_crisis_response_is_still_returned_past_the_rate_limit` — the crisis guard runs before the rate limiter, so someone who has exhausted their quota still gets the helpline. Reordering the router breaks this test, which is the point.
- `test_crisis_script_is_still_unapproved` — currently asserts that `crisis_scripts.id.yml` is a placeholder. It is meant to fail the day the editorial team signs off, as a reminder to delete it.

## Before this can go anywhere real

Blocking dependencies live in [PIP §6](docs/project-implementation-plan.md). The earliest gates:

1. **The crisis template** (`backend/config/crisis_scripts.id.yml`) is a placeholder with fake helpline numbers. Staging and production boot is blocked until the editorial owner approves the copy and every number has been called and confirmed.
2. **Emotional-deferral contact number and template** (F-44 / F-45, PIP B10) must be approved before Phase 5.
3. **Zero Data Retention terms** must be confirmed in writing before any real LLM provider is wired in. A provider that cannot contract for ZDR is disqualified (PIP B3).
4. **Crawl permission** for the five approved sites — the RAG index cannot be built until we may store that text.

## Contributing

Read [`AGENTS.md`](AGENTS.md) first — it states the one rule that shapes every technical decision here, and the constraints that are not negotiable. Branching rules are in [`docs/branching-and-deployment-workflow.md`](docs/branching-and-deployment-workflow.md). Build order is the [Project Implementation Plan](docs/project-implementation-plan.md).
