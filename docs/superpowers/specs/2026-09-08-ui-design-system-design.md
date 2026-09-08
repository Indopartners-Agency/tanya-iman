# Design — UI Design System and Client Approval Mockup

**Date:** 2026-09-08
**Branch:** `feature/ui-design-system`
**Status:** Approved for planning

---

## 1. Problem

The seeker app and admin portal are scaffolded and functionally wired — auth, sessions, chat store, composer, message bubbles, likes, and `embed.js` all exist and run against the stub answer engine. What does not exist is the presentation layer. `web/app/tailwind.config.ts` sets a single font size and nothing else; there are no colour tokens, no typography scale, no layouts. `web/admin` is one empty `index.vue`.

The client has not yet approved a visual direction. They need something they can open in a browser and sign off on before Phase 5 and Phase 6 build on top of it.

These are the same problem. A throwaway mockup would answer the approval question and leave the design layer still unbuilt; building the design layer answers both.

## 2. Approach

Fill in the presentation layer of the existing Nuxt apps, and add a demo mode that lets the result be hosted statically without a backend.

`NUXT_PUBLIC_DEMO_MODE=1` swaps the API client for a fixture-backed implementation of the same `ApiClient` interface. `useApi` already wraps `createClient` from `@tanya-iman/shared`, so the swap happens at that seam and no component, store, or page knows the difference. Unset, the apps behave exactly as they do today. One codebase, no throwaway branch, and the client reviews the real components rather than a picture of them.

**Rejected:** a standalone HTML mockup. It would answer the approval question a day sooner and leave the design system unbuilt, with Phase 6 starting from zero.

**Rejected:** waiting for Phase 5 to build UI on real answers. The client approval gate blocks the milestone; the engine does not need to be real for a layout to be judged.

## 3. Visual direction — Zamrud & Perkamen

Deep emerald on warm parchment, serif headings, one accent.

Chosen against a warm-terracotta and a neutral-indigo alternative. The audience is Indonesian Muslim seekers, and Chat UX §4.1 requires a surface that is calm, warm, and unbranded in the religious sense — no crosses, no crescents, no photography of people. Green carries weight for this readership without belonging to either tradition's iconography; parchment and a serif heading supply gravity that a neutral SaaS blue does not.

§4.1 also names a safety constraint that governs the palette: the app must be openable on a bus without announcing anything about its user. Nothing in the chrome names a religion. The wordmark is the product name set in type.

### 3.1 Token layer

Tokens live in `web/shared` and are exposed to both apps as CSS custom properties, consumed through Tailwind. Components never write a hex value — Chat UX §4.2 and Admin UX §4.2 both require this.

Token names are taken from the specs, not invented:

**Seeker (Chat UX §4.2):** `bg.base`, `bg.surface`, `bubble.user`, `bubble.assistant`, `text.primary`, `text.secondary`, `text.onAccent`, `accent.primary`, `border.subtle`, `status.warning`, `status.info`, `status.care`.

**Admin (Admin UX §4.2):** `bg.base`, `bg.surface`, `text.primary`, `text.secondary`, `border.default`, `accent.primary`, `status.success`, `status.warning`, `status.danger`, `status.info`.

The two apps share hues and diverge in saturation and density: the seeker surface is warm and roomy, the admin surface is flatter and tighter, per Admin UX §4.1 ("professional, dense, neutral").

`status.care` is warm sand with a border, deliberately not red. Chat UX §8.3 requires the crisis state to read as care rather than as an error, and `status.danger` already owns red.

Every token pair meets WCAG 2.1 AA, verified by a contrast test rather than by eye — both specs require AA, and `status.care` and `status.info` are called out by name in Chat UX §13.

### 3.2 Typography

Three levels in each app, as both specs require.

Headings are set in a serif; body and UI in the system sans stack already configured. Body stays at 15px/1.7 — the existing `tailwind.config.ts` comment records why, and Chat UX §4.3 sets a 1.6 minimum with measure capped near 65 characters because Indonesian runs 10–15% longer than English and a 250-word answer is a long block on a 360px screen.

Admin counts and timestamps use tabular numerals (Admin UX §4.3).

### 3.3 Out of scope

Dark mode. Chat UX §16 defers it to post-v1.0. The token layer is structured so it can be added by redefining variables rather than by touching components.

## 4. Seeker app

Routes are exactly those in Chat UX §3: `/`, `/masuk`, `/chat`, `/privasi`. No navigation bar; a single overflow control holds *Kebijakan Privasi* and *Keluar*.

**Welcome (§5)** — three sign-in buttons at equal size. Guest may be outline rather than filled but is never smaller, lower-contrast, or below the fold (F-1). Privacy link in the footer at a 44px tap target (F-4).

**Sign-in (§6)** — phone entry with `+62` prefilled and a numeric keypad; then six OTP boxes with auto-advance, paste support, auto-submit on the sixth character, and a resend link disabled behind a visible countdown. Lockout copy after 5 wrong attempts and after 3 requests in an hour (F-24) names the actual problem.

**Chat (§7)** — persistent source note beneath the header that does not scroll away (F-6); greeting as the first assistant message with no Like control; auto-growing composer, 1 to 5 lines; send disabled while in flight with the textarea still editable (F-26); *Pesan baru* pill instead of yanking the view down when the user has scrolled up (F-8).

**Response states (§8)** — all seven render: `generated`, `curated` (visually identical to generated, deliberately), `refusal`, `no_grounding`, `crisis`, `error` with **Coba lagi**, and rate-limited with a live countdown. Plus the pending state, its 8-second *Masih menyiapkan jawaban…* line, citations, and Like.

In demo mode a scenario switcher makes each state reachable. It renders only under the demo flag. This is the part of the mockup with the most editorial weight — the crisis and refusal states are what the client most needs to see before signing off.

**Citations (§9)** — article title as link text, domain in meta type beneath, one or two, never a bare URL, opening in a new tab.

**Like (§10)** — heart beneath the citations, optimistic fill, reversible (F-33), no count shown, rendered only when the API reports `likeable: true` (F-17).

**Embed mode (§11)** — `?embed=1` suppresses the header, outer background, and title while keeping the source note, transcript, input, and privacy link, because F-4 and F-6 apply inside the widget too. Height reported over `postMessage`; layout holds at 320px; links open with `target="_top"`.

A demo page simulates a WordPress host article with the widget embedded, so the client sees the widget in the context it will actually appear in.

## 5. Admin portal

All ten pages in Admin UX §3: Login, Beranda, Pertanyaan, Detail Pertanyaan, Topik, Editor Jawaban, Pertanyaan Serupa, Kekosongan Materi, Antrean Tinjauan, Pengaturan.

Left sidebar on desktop, top menu on tablet. Role badge and signed-in email always visible in the header. Standing badges on **Kekosongan Materi** and **Antrean Tinjauan** carry counts, because both represent work waiting.

Notable screens:

**Beranda (§6)** — five cards. The Kesehatan Jawaban card turns `status.danger` and says so plainly whenever validator pass rate is not 100%, because K4 is a release gate and the dashboard must not let it pass as one number among others.

**Pertanyaan (§7)** — the seven columns of §7.1, the filter set of §7.2 as removable chips, sticky header, 50-row pages, saved views, and CSV export that exports the current filter rather than the current page (F-36). No phone number appears in this view or in any export (§7.4).

**Detail Pertanyaan (§8)** — exchange on the left, diagnostics on the right: classification, retrieved chunks with similarity scores marking cited distinctly from merely retrieved, V1–V5 results with measured values, repair state, and technical metadata.

**Editor Jawaban (§10)** — textarea with a live rule panel: word count against 25–250, terminology check that highlights "Tuhan" or "Yesus" in the textarea itself, scripture balance stated in words rather than codes, and citation count. The citation picker searches approved-site articles only; there is no free-text URL field. **Terbitkan** is separate from saving a draft and confirms with plain language about going live immediately.

The word counter imports from `web/shared/word-count.ts`, which already exists with a test. Admin UX §10 is explicit that a counter disagreeing with the backend destroys trust in the whole live-validation idea.

**Pengaturan (§14)** — system config, the F-45 support contact, admin accounts, ingestion status, and the audit log. `similarity_threshold` carries the §14 warning that it changes what the assistant will answer.

**Responsive (§16)** — desktop-first. The curated answer editor is not offered below 768px, per spec.

**Roles (§5.3)** — unavailable actions are hidden, not disabled. A `reviewer` sees no editing controls. Demo mode includes a role switcher so the client can see all three.

## 6. Demo data

Fixtures live in one file per app (`useDemoData.ts`), so Phase 5 removes them in a single deletion.

Eight Indonesian question-and-answer pairs with citations to the five approved domains, plus admin fixtures: question rows, topic counts, clusters, gaps, review items, and audit entries.

Three constraints:

1. **Template copy is not authored here.** Every template string comes from `web/app/locales/id.json`, which is already authoritative and byte-identical to `backend/config/responses.id.yml` under `test_copy_parity.py`. Only the *bodies of sample answers* are written for this work, and they are labelled as demo content.

2. **The crisis script is not touched.** SOW B1 places it with the client's pastoral staff, and `emotional_deferral` still carries its PLACEHOLDER marker. The mockup shows the *shape* of the crisis card with clearly-marked example numbers. No real helpline number is introduced by this work.

3. **No user-facing string is hardcoded in a component.** Chat UX §14 requires it and a test asserts it. New UI strings are added under `ui` in `id.json`, never under `shared`.

## 7. Delivery

Branch `feature/ui-design-system` off `dev`, PR into `dev`, per `docs/branching-and-deployment-workflow.md`. `dev` does not yet exist on the remote and is created from `main` as part of this work.

`npm run build:app` and `npm run build:admin` produce static output at the paths `firebase.json` already points its two hosting targets at. The deploying team takes it from the branch.

A separate presentation summary is published for the client alongside the branch.

## 8. Testing

- Contrast test over every token pair, asserting WCAG 2.1 AA
- Existing `test_copy_parity.py` must stay green — the locale file is touched, and only under `ui`
- `web/shared/word-count.test.ts` continues to gate the editor's counter
- Typecheck across all three workspaces
- Manual: 320px, 360px, and desktop; 200% text scale without clipping; keyboard reach to input, send, every citation, and every Like

## 9. Explicitly not in this work

- Real answers, retrieval, or any LLM call — Phase 5
- Real authentication — Phase 3
- Dark mode — post-v1.0 per Chat UX §16
- Any change to backend behaviour, prompts, validators, or the crisis script
- Capacitor packaging — Phase 7
