# **Admin UX Specification**

**Project:** Tanya Iman \- Editorial Admin Portal

**Version:** Draft v1 (Phase 6)

**Date:** August 2026

---

## **1\. Purpose**

Define a clear, low-friction admin experience for the editorial team:

- Read what people are actually asking, in bulk and in detail
- See which topics carry demand and which questions repeat
- Find where the corpus has gaps
- Write and publish the canonical answer for a topic
- Do all of the above without asking an engineer for anything

This document complements:

- [Product Requirements Document](prd.md) — F-19 through F-23, F-34 through F-37, F-44–F-45
- [Technical Design Document](tdd.md) §2.8, §4.2 — auth, roles, API surface
- [AI Answer Engine Specification](ai-answer-engine-specification.md) §11, §12 — curated answers and clustering
- [Project Implementation Plan](project-implementation-plan.md) Phase 6 — implementation scope

---

## **2\. UX Principles**

1. **The editor is the user, not the engineer.** Every screen must make sense to someone who has never seen a validator code or a similarity threshold.
2. **Demand first.** The portal's most valuable output is "here is what people want that we have not written." That should be the easiest thing to find, not something buried behind three filters.
3. **Auditability by default.** Every consequential action should be explainable from the UI afterwards, not only from a log file.
4. **Role-aware simplicity.** Hide what a role cannot do rather than showing it disabled.
5. **Fast scanning.** A screen should be useful within five seconds of opening.
6. **Safe destructives.** Anything irreversible requires explicit confirmation with the target named.
7. **Throughput over polish.** This is a daily working tool at a scale of thousands of questions per month.

---

## **3\. Information Architecture**

| # | Page | Purpose | Roles |
|---|---|---|---|
| 1 | **Login** | | — |
| 2 | **Beranda** (Dashboard) | This week at a glance: volume, top topics, gap count, review queue count | all |
| 3 | **Pertanyaan** (Question List) | Every question, filterable (F-20, F-35) | all |
| 4 | **Detail Pertanyaan** | One question with its answer, sources, and diagnostics | all |
| 5 | **Topik** (Topics) | The 13 topics + `lainnya` with demand and curated status (F-21) | all |
| 6 | **Editor Jawaban** | Write and publish a curated answer (F-23) | editor, super_admin |
| 7 | **Pertanyaan Serupa** (Clusters) | Similar-question frequency (F-22) | all |
| 8 | **Kekosongan Materi** (Content Gaps) | Questions the corpus could not answer | all |
| 9 | **Antrean Tinjauan** (Review Queue) | Ambiguous classifications, validator failures, crisis events, emotional-deferral samples | all |
| 10 | **Pengaturan** (Settings) | System config, contact number (F-45), admin accounts, ingestion | super_admin |

Navigation: left sidebar on desktop, top menu on tablet. The role badge (`editor`, `reviewer`, `super_admin`) is always visible in the header, with the signed-in email beside it.

Two badges sit permanently in the sidebar because they represent work waiting to be done: **Kekosongan Materi** carries a count of unresolved gap clusters, and **Antrean Tinjauan** carries a count of unreviewed items.

---

## **4\. Visual Style**

### **4.1 Design tone**

Professional, dense, neutral. This is an internal tool used for hours at a time. Generous whitespace matters less than the number of rows visible without scrolling.

### **4.2 Semantic tokens**

- `bg.base`, `bg.surface`
- `text.primary`, `text.secondary`
- `border.default`
- `accent.primary` — links, selected rows
- `status.success` — passed validation, published
- `status.warning` — draft, ambiguous, needs review
- `status.danger` — destructive actions, validator failures
- `status.info` — neutral metadata chips

### **4.3 Typography**

Three levels: page title, section title, body/metadata. Counts and timestamps use tabular numerals so columns align down a long list.

### **4.4 Density**

- 8px spacing scale
- Comfortable row height by default, with a compact toggle for long review sessions
- Question text in list rows truncates to two lines with the full text on hover and in detail

---

## **5\. Core Interaction Patterns**

### **5.1 Loading, empty, error**

- **Loading:** skeleton rows, never a spinner over an empty page
- **Empty list:** an instructional empty state that explains why it might be empty and offers a filter reset — "Tidak ada pertanyaan pada rentang tanggal ini"
- **Error:** a retry affordance plus enough technical context to describe the problem to an engineer

### **5.2 Feedback**

- Non-destructive save: toast confirmation
- Destructive action: modal confirmation naming the target, then a result toast carrying the audit entry ID

### **5.3 Permissions**

Unavailable actions are hidden, not disabled. A `reviewer` who navigates directly to an editor route sees a role-aware message, not a blank page or a raw 403.

### **5.4 Filter state**

Filters live in the URL query string, so a link to "grief questions in the last 30 days with no grounding" can be pasted into a chat message and opened by a colleague.

---

## **6\. Dashboard**

The landing page after login. Five cards, each linking to the view behind it:

| Card | Shows | Links to |
|---|---|---|
| **Volume** | Questions this week, with the change against last week | Question List |
| **Topik teratas** | Top 5 topics by question count, with curated status per topic | Topics |
| **Kekosongan materi** | Count of gap clusters, and the largest one by name | Content Gaps |
| **Perlu ditinjau** | Count of unreviewed items in the review queue | Review Queue |
| **Kesehatan jawaban** | Answer rate, like rate, and validator pass rate for the week | Question List, filtered |

If validator pass rate is anything other than 100%, that card turns `status.danger` and says so plainly. It is a gate metric (K4), and the dashboard should not let it slide by as a number among numbers.

---

## **7\. Question List (F-20, F-35, F-36)**

### **7.1 Columns**

| Column | Notes |
|---|---|
| Waktu | Relative for the last 24h, absolute beyond |
| Pertanyaan | Truncated to two lines |
| Topik | Chip; `lainnya` visually distinct |
| Hasil | `answer_source` chip: Dijawab / Kurasi / Ditolak / Tanpa Sumber / Krisis / Gagal |
| Suka | Like count |
| Kanal | `web` / `widget` / `android`; widget rows show the host site on hover |
| Penanda | Small icons for ambiguous classification, validator failure, injection attempt |

Default sort: newest first.

### **7.2 Filters (F-35)**

- Date range (presets: today, 7 days, 30 days, custom)
- Topic
- Result (`answer_source`)
- Has grounding
- Crisis
- Validator failure — and, nested, the specific failure code
- Ambiguous classification
- Channel
- Free-text search across question text

Active filters render as removable chips above the table. A **Bersihkan filter** action clears all of them.

### **7.3 List behaviour at scale**

- Server-side cursor pagination, 50 per page. The list must stay usable at 100,000+ records (PRD §7.5), so it never loads the full dataset into browser memory.
- Sticky table header
- Saved views for recurring workflows: *Perlu ditinjau*, *Tanpa sumber*, *Ditolak minggu ini*
- **Ekspor CSV** exports the current filter, not the current page (F-36)

### **7.4 Privacy in the list**

No phone number appears anywhere in this view. The user column shows an opaque identifier and the auth method (`SMS`, `WhatsApp`, `Tamu`). Where a phone number is shown at all — only in detail, only for `super_admin` — it is masked as `+62 812 •••• 4471`. CSV export never contains a phone number in any form.

---

## **8\. Question Detail**

Two panels on desktop, stacked on tablet.

**Left — the exchange:**

- The question as typed, with timestamp, channel, and topic
- The answer exactly as the user saw it
- The citations as they were shown, each link live
- Like state

**Right — diagnostics:**

| Block | Contents |
|---|---|
| **Klasifikasi** | Relevance result and confidence; ambiguous flag |
| **Sumber yang diambil** | The retrieved chunks with similarity scores, each expandable to its text and linking to its article. Chunks that were *cited* are marked distinctly from chunks that were merely retrieved |
| **Validasi** | Each of V1–V5 with pass/fail, and for failures the code and measured value ("V1_TOO_LONG — 271 kata") |
| **Perbaikan** | Whether a repair ran, and the pre-repair answer if so |
| **Teknis** | Model, `prompt_version`, latency, `answer_source` |

The retrieved-chunks block is the single most useful diagnostic in the portal. When an editor says "this answer is wrong," the next question is always "what did it read?" — and this answers it without an engineer.

**Actions (top right):** Salin tautan · Tandai untuk ditinjau · Hapus (`super_admin` only).

---

## **9\. Topics (F-21)**

A table of the 13 topics plus `lainnya`.

| Column | Notes |
|---|---|
| Topik | Indonesian name |
| Pertanyaan | Count in the selected period, with a sparkline |
| Suka | Like count |
| Jawaban kurasi | `Belum ada` / `Draf` / `Terbit`, with last editor and date |
| Tingkat penolakan | Share of questions in this topic that got no grounding — a high value means the corpus is thin here |
| Aksi | **Tulis jawaban** / **Ubah jawaban** |

Default sort: question count descending. Read top-down, this table is the editorial priority list, and that is deliberate — the highest-demand topic without a curated answer should be the first row an editor's eye lands on.

`lainnya` is highlighted when its count exceeds 10% of the period's total, because that means the taxonomy needs a new topic (PRD Appendix A).

---

## **10\. Curated Answer Editor (F-23, F-34)**

The one screen where an editor writes rather than reads. It must make the rules feel like guardrails, not like a rejection at the end.

**Layout:**

- Topic name and current status at the top
- A textarea for the answer
- A **live rule panel** beside it, updating as they type
- Citation picker beneath
- **Simpan sebagai draf** and **Terbitkan**

**The live rule panel:**

| Rule | Live display |
|---|---|
| V1 Panjang | `184 / 25–250 kata` — green in range, red outside, updating per keystroke |
| V2 Sebutan | Green when "Allah" or "Isa Al-Masih" is present; red the moment "Tuhan" or "Yesus" is typed, with the offending word highlighted **in the textarea** |
| V3 Ayat | Counts detected Quran and Bible references and states the balance rule in words, not codes |
| V4 Tautan | `1 dari 1–2 tautan dipilih` |

The word counter must use the **same counting function as the backend** (PIP Task 5.5). If the editor's counter says 249 and the backend says 251, the editor stops trusting the tool, and the whole live-validation idea is worth less than nothing.

**Citation picker:** search across the `articles` collection, filtered to the approved sites, with title and site shown. One or two selectable. An off-allowlist URL cannot be entered at all — there is no free-text URL field.

**Publishing:** **Terbitkan** is a distinct action from saving a draft, with a confirmation that states plainly what will happen: *"Jawaban ini akan langsung ditampilkan kepada semua pengguna yang bertanya tentang topik ini."* Because a published curated answer overrides the engine entirely (AI Spec §11.1), the editor must understand that this is a live product change, not a suggestion to the model.

**Draft answers are never served.** The status chip says so.

---

## **11\. Similar Questions (F-22)**

A list of clusters within each topic.

| Column | Notes |
|---|---|
| Pertanyaan umum | The cluster's canonical phrasing |
| Jumlah | Member count — the number F-22 asks for |
| Topik | |
| Terakhir ditanya | |
| Jawaban kurasi | Whether this cluster's topic already has one |

Expanding a cluster shows its member questions in their original wording, which is where the real editorial insight lives — the canonical phrasing tells you the theme, the raw wording tells you how people actually talk about it.

Editor actions: rename the canonical phrasing, merge two clusters, or **Jadikan jawaban kurasi**, which opens the curated answer editor for that cluster's topic pre-filled with the cluster context.

Sorted by member count descending. This list, read from the top, is the content queue.

---

## **12\. Content Gaps**

Questions that returned no grounding (F-29), clustered and sorted by frequency. Each row shows the canonical phrasing, how many people asked it, when it was last asked, and the nearest topic.

An editor can mark a gap **Sudah ditulis** once an article covering it has been published, which removes it from the active list after the next ingestion run confirms the corpus now answers it. Marking it resolved without the corpus changing is not possible — the state is derived, not asserted.

This screen exists because it is the highest-value output of the entire product for the editorial team. Everything else tells them what they already have; this tells them what they are missing.

---

## **13\. Review Queue**

One worklist, three sources:

| Source | Why it needs a human |
|---|---|
| Ambiguous classifications | To refine the classifier (theology vs emotional-only vs irrelevant) |
| Validator failures | To catch prompt drift or a model change before K4 slips |
| Crisis events | Monthly precision review (K9) — confirm routing was right |
| Emotional-deferral samples | Confirm F-44 routing and that contact number display is correct |

Crisis and emotional-deferral events are visible to all admin roles but carry a standing notice that these records are sensitive and must not leave the portal.

Each item can be marked reviewed with an optional note. Reviewed items stay searchable.

---

## **14\. Settings (`super_admin`)**

| Section | Contents |
|---|---|
| **Sistem** | `retention_months`, `rate_limit_per_hour`, `similarity_threshold` — each with current value, plain-Indonesian effect, last change |
| **Kontak dukungan emosional (F-45)** | Contact name, phone number (tappable format), and optional short intro line used by the emotional-deferral template (F-44). Changing the number requires confirmation and writes an audit entry. No placeholder may be saved to staging/production |
| **Akun admin** | List, create, deactivate. No self-registration exists |
| **Materi** | Last ingestion run, articles seen, chunks written, and a **Jalankan sekarang** trigger (five approved sites in v1.0; adding sites is post-v1.0 / F-42) |
| **Jejak audit** | The audit log, filterable by actor, action, and date |

Changing `similarity_threshold` is presented with an explicit warning that it changes what the assistant is willing to answer, and a link to the benchmark results. It is a tuning parameter with product consequences, and the settings screen should not present it as a preference.

---

## **15\. Destructive Actions (F-37)**

For `DELETE /api/admin/questions/{id}` and admin account deactivation:

- Confirmation modal naming the exact target and stating that the action is irreversible
- Explicit confirm click; no shortcuts, no "don't ask again"
- The success toast carries the `audit_id`
- The error state must state clearly that no partial deletion should be assumed

---

## **16\. Responsive Behaviour**

| Breakpoint | Layout |
|---|---|
| Desktop ≥1200px | Sidebar + full table; question detail as two panels |
| Tablet 768–1199px | Top menu; tables scroll horizontally with a sticky first column; question detail stacks |
| Mobile <768px | Supported for reading only. The curated answer editor is not offered below 768px — writing a 250-word answer against live validation on a phone is not a workflow worth designing for |

---

## **17\. Accessibility**

- WCAG 2.1 AA contrast
- Keyboard operation of tables, filters, modals, and the editor
- Visible focus rings
- No information encoded by colour alone — every status chip carries text
- Validator failures are announced to assistive technology when they appear in the editor, not only rendered

---

## **18\. Implementation Notes (Phase 6)**

- Separate Nuxt 3 SPA at `web/admin/` (`ssr: false`), desktop-first. It is a distinct Firebase Hosting site from the seeker app, so an admin bundle can never be served to a seeker
- Access token held in memory only; refresh token in an httpOnly cookie
- Every list view keeps filter and sort state in URL query params (§5.4)
- The portal consumes only the routes in TDD §4.2 and never reads Firestore directly
- The word-count function is imported from `web/shared/`, and `web/shared/` must be the same rule the backend implements. A contract test asserts agreement on a set of edge cases (multiple spaces, punctuation, numerals, hyphenated words)

---

## **19\. UX Acceptance Checklist**

- [ ] An editor can find the top topic without a curated answer in ≤2 interactions from login
- [ ] Question list filters work alone and combined, and survive a page reload via the URL
- [ ] No phone number appears in any list view or export
- [ ] Question detail shows the retrieved chunks with similarity scores, distinguishing cited from merely retrieved
- [ ] Validator results are shown per rule with the measured value
- [ ] The curated editor's word count matches the backend exactly on the contract-test edge cases
- [ ] Typing "Yesus" highlights it in the textarea and blocks publish
- [ ] A citation outside the allowlist cannot be entered
- [ ] Publishing shows a confirmation stating the answer goes live immediately
- [ ] A draft curated answer is never served (verified end to end against the chat API)
- [ ] Content Gaps shows clusters ordered by frequency
- [ ] A `reviewer` sees no editing controls anywhere
- [ ] Destructive actions require confirmation and return an audit ID
- [ ] Empty, loading, and error states exist on every list and detail view

---

## **20\. Out of Scope (v1.0)**

- Real-time monitoring of live conversations
- Replying to a user directly from the portal — every chat is handled by the AI; editors work after the fact
- Editing a user's question text
- A/B testing curated answers against generated ones
- Rich text or markdown in curated answers — plain text only, because the chat client renders plain text
- Bulk editing of curated answers
- Analytics dashboards beyond the Dashboard cards in §6
