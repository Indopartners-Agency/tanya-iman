# **Product Requirements Document (PRD)**

**Project:** Tanya Iman — Indonesian Theology Q&A for Muslim Seekers

**Version:** 1.1

**Date:** August 2026

This PRD is the authoritative requirement set for the repository. It preserves the concepts from the Aug 2026 product brief (formerly `init.md` / Word PRD v1.0) and adds engineering detail. Where this document and older briefs diverge, **this PRD wins**.

---

## **1\. Product Vision & Objective**

Tanya Iman is an Indonesian-language **theology Q&A assistant**, written for Muslim seekers. A user asks about Allah, Isa Al-Masih, the Quran, the Holy Scripture, or a faith-related question, and receives a 25–250 word Indonesian answer drawn **only** from an approved corpus of religious-dialogue websites. Every conversation is handled entirely by the AI. There is no human agent in the chat.

The wording of every answer is part of the product. The assistant uses only **"Allah"** and **"Isa Al-Masih"**. The words **"Tuhan"** and **"Yesus"** must never appear. That is how the answer stays readable and respectful to a Muslim reader.

**Tone:** Answers are warm and empathetic. They may meet a reader’s need for emotional *support in tone* — acknowledging feelings briefly — without treating emotional subjects as the topic of discussion. Purely emotional questions (no theology/faith question) are **out of scope** for composition; the system returns a configured template with a contact number set in the admin portal.

The corpus for **Version 1.0** is a **fixed allowlist of five sites**. Articles are crawled, stored, chunked, and embedded so retrieval — not the model's training data — is what the answer is composed from. Each answer points to one or two source articles. Allowlist growth (admin-addable sites that trigger crawl) is **post-v1.0**; v1.0 does include **scheduled crawl** of the five sites to keep the corpus current.

The product ships through two channels: an **Android app on the Google Play Store**, and an **embedded widget on the existing WordPress sites**. Behind both sits an editorial admin panel: editors review questions after the fact, see which topics recur, and write canonical answers. They never join the chat.

**Frontend:** Nuxt 3 (Vue 3) SPA — not React. One static build serves web, widget, and Android (Capacitor). See [Frontend Framework Decision — Nuxt](frontend-framework-decision-nuxt.md).

**What this product is not**

* Not a counselling or emotional-support service. It does not discuss emotional subjects as topics, does not “walk with” someone over many turns, and does not hand anyone to a human in-app.
* Not a debate engine. It answers once from the corpus, kindly, and stops.
* Not a general chatbot. Off-topic and emotional-only questions are not composed by the model.

**Why "Tanya Iman"?**

*Tanya* means "to ask"; *iman* means "faith". The name is the product promise: a place to ask about faith and receive a sourced answer.

---

## **2\. Background & Problem**

The approved sites — isadanislam.org, isadanalquran.com, isadanalfatihah.com, isaislamdankaumwanita.com, and takutneraka.com — have published years of Indonesian religious dialogue written for Muslim readers. That library is real and substantial, but it has three structural problems:

1. **It is scattered.** A reader with one specific theology question must guess which site holds the answer, then search within it.
2. **It is static.** The articles answer the questions their authors anticipated, not the question a particular reader has at 2 a.m.
3. **It is silent about demand.** The editorial team cannot see which questions visitors asked and did not find. Content strategy is driven by intuition rather than evidence.

Tanya Iman crawls that library into a retrieval index, turns a theology question into a sourced answer, and turns the questions themselves into an evidence stream the editorial team can act on.

---

## **3\. Product Goals & Guiding Principles**

### **3.1 Goals**

| # | Goal | How we will know it worked |
|---|---|---|
| G1 | Answer theology questions quickly, relevantly, and traceably from the approved corpus | ≥85% of in-scope theology questions answered without refusal; 100% of composed answers carry 1–2 valid source links |
| G2 | Lower the barrier to asking | Guest path requires zero personal data; OTP paths complete in under 60 seconds |
| G3 | Give the editorial team visibility into real demand | Admin panel shows topic distribution and similar-question frequency from day one |
| G4 | Hold Muslim-facing terminology constant across every answer | 100% terminology compliance ("Allah", "Isa Al-Masih"); 0 occurrences of "Tuhan" or "Yesus" in shipped answers |
| G5 | Reach users on both the Play Store and the existing WordPress properties | One Nuxt codebase, two distribution targets, no feature divergence |
| G6 | Keep the five-site corpus current | Weekly scheduled crawl; admin can trigger a run on demand |

### **3.2 Guiding principles**

* **Grounded or silent.** If the approved corpus does not support an answer, the assistant uses a template (no grounding) rather than improvises. There is no acceptable rate of invented theology.
* **Traceable by construction.** Every composed answer carries links back to the articles it came from.
* **AI handles every chat.** Editors work offline. Template paths (refusal, emotional deferral, crisis, no-grounding) never call the composer.
* **Speak the reader's language.** "Allah" and "Isa Al-Masih" only. Neutral product language — no church-register terms in UI or internal role names facing Muslim users.
* **Empathetic tone, theology subject.** Warm acknowledgement is required; discussing emotional subjects as the question topic is not.
* **Low friction, low data.** Guest access is first-class. Phone numbers are collected only when the user chooses SMS/WhatsApp, stored securely, and used only for authentication and session recognition.
* **Editorially governable.** Published curated answers override generation for that topic.
* **Safe before answering.** Crisis signals and emotional-only questions receive **templates** (config / admin), never model composition.

---

## **4\. Target Audience**

### **4.1 Primary — the Seeker**

Indonesian-speaking individuals, predominantly from a Muslim background, with **theology / faith questions**: who is Isa Al-Masih, what the Quran and the Holy Scripture say, the path of salvation, fear of hell, sin and forgiveness, worship and fasting, the search for truth. They access the internet primarily by mobile phone and may prefer anonymity (Guest).

Emotional-only questions (seeking emotional support without a faith/theology question) are **not answered by the composer**; they receive a template with a contact number.

### **4.2 Secondary — the Equipper**

Indonesian Christians who want to understand how to talk about faith with Muslim friends or family. Same answer surface; no separate mode.

### **4.3 Tertiary — the Editorial Admin**

IndoPartners **editorial** staff who review incoming questions, curate the canonical answer per topic, configure contact numbers and templates, and monitor demand. They work on desktop, in bulk.

---

## **5\. Scope**

### **5.1 In scope — Version 1.0**

* Welcome screen with **Masuk dengan SMS**, **Masuk dengan WhatsApp**, and **Lanjutkan sebagai Tamu**.
* Privacy Policy link in the footer of every screen.
* Chat screen with a persistent note that answers are based on the Holy Scripture, free-text input, and multi-turn conversation.
* Relevance classification: **theology / faith** → compose; **emotional-only** → contact template; **irrelevant** → refusal template; **crisis** → crisis template.
* Grounded answers of 25–250 words using only "Allah" and "Isa Al-Masih", optional opening Quranic reference, Bible-majority scripture when used, and 1–2 source article links — written in an **empathetic** tone.
* Crawl, store, chunk, and embed the **five** approved sites into a retrieval index (RAG). **Scheduled** refresh of those five sites. **No allowlist growth in v1.0.**
* **Like** on every composed / curated answer (not on templates).
* Rate limiting at 30 messages per user per rolling hour.
* Crisis and emotional-deferral and no-grounding paths as **templates** (not AI).
* LLM composition on a **Zero Data Retention** provider tier (PIP B3).
* Admin panel: question list, topic grouping, similar-question frequency, curated answers, like counts, filters, CSV export, audit log, and configuration of emotional-support contact number / templates.
* Distribution: Android (Play Store) and WordPress widget from one Nuxt build.

### **5.2 Out of scope — Version 1.0**

* iOS / App Store (same Nuxt + Capacitor stack can add it later).
* Automated moderation of abusive language / spam (manual admin flag/delete only).
* Live human handover or in-app counselling.
* Composing answers on **emotional-only** subjects.
* Allowlist growth / admin “add site → crawl” (**post-v1.0**; pipeline should remain ready for it).
* Multi-language answers; "Tuhan" / "Yesus" in answers.
* Voice input or audio answers.
* Cross-device conversation history replay (device-local sessions in 1.0).
* Detailed phone-encryption scheme as a product requirement beyond secure storage and limited use (implementation may still encrypt; see TDD).

### **5.3 Content sources — five sites in v1.0**

Version 1.0 uses exactly these five domains (Word PRD §6.6). The brief once said “6 situs sumber” in prose and listed five — **five is correct**.

* `isadanislam.org`
* `isadanalquran.com`
* `isadanalfatihah.com`
* `isaislamdankaumwanita.com`
* `takutneraka.com`

`backend/config/approved_sites.yml` is the single allowlist for crawler, retriever, and citation validator. Changing it in v1.0 is a product change with PRD update — not a routine admin action. **Post-v1.0:** admins may append sites in the admin portal; each addition triggers a crawl; scheduled crawl continues for all approved sites.

---

## **6\. Functional Requirements**

Requirements **F-1** through **F-23** originated in the Aug 2026 product brief. **F-24** and above are engineering upgrades retained for v1.0 unless marked deferred. Appendix B records traceability and the v1.0 recommendation set.

### **6.1 Onboarding & Authentication**

| ID | Requirement |
|---|---|
| **F-1** | On first open, the app displays an Indonesian welcome screen with three options: "Masuk dengan SMS", "Masuk dengan WhatsApp", and "Lanjutkan sebagai Tamu". |
| **F-2** | The SMS and WhatsApp flows collect a mobile number, send a one-time verification code over the chosen channel, and verify the code before granting access to the chat screen. |
| **F-3** | "Lanjutkan sebagai Tamu" grants immediate access to the chat screen and collects no personal data. |
| **F-4** | Every screen displays a footer link to the Privacy Policy. |
| **F-5** | The user can log out at any time and return to the welcome screen. |
| **F-24** | OTP entry is limited to 5 attempts per code and 3 code requests per number per hour. Exceeding either limit shows an Indonesian cooldown message with the time remaining. |
| **F-25** | A Guest user can convert to an SMS or WhatsApp account without losing the current on-screen conversation. |

### **6.2 Q&A Screen (Chat)**

| ID | Requirement |
|---|---|
| **F-6** | After sign-in, the app shows a greeting asking how it can help, with a small persistent note that answers are based on the Holy Scripture. |
| **F-7** | The user can type a free-form question and send it. |
| **F-8** | The user can ask repeatedly within one session; every question and answer is appended to a single scrolling conversation view. |
| **F-9** | The system classifies each question as one of: `theology` (faith/theology in scope), `emotional_only` (emotional subject with no theology question), `irrelevant`, or routes via crisis guard when crisis signals are present. |
| **F-26** | While an answer is being generated the app shows a typing/progress indicator, and send is disabled until the answer resolves. |
| **F-27** | If answer generation fails or times out, the app shows an Indonesian error state with a **Coba lagi** action that resubmits the same question without retyping. |

### **6.3 Answer Content Rules**

| ID | Requirement |
|---|---|
| **F-10** | If a question is `irrelevant` (not theology/faith and not emotional-only), the app returns a standard Indonesian refusal template and does not answer the content. |
| **F-11** | Every composed or curated answer is at least 25 and at most 250 words. |
| **F-12** | Answers use only the terms "Allah" and "Isa Al-Masih". The terms "Tuhan", "Yesus", and "Jesus" must not appear. The validator rejects; it never auto-substitutes. |
| **F-13** | Where relevant, an answer may open with a brief reference from the Quran; the substantial majority of scriptural quotation must come from the Bible. |
| **F-14** | Every composed or curated answer includes 1–2 links to related articles from the approved sites. |
| **F-15** | All composed answer content must derive from the crawled corpus of approved sites. No information from outside that corpus may appear in an answer. |
| **F-16** | A single user may send at most 30 messages per rolling hour. |
| **F-28** | An answer that fails any content rule (F-11 through F-15) must not be shown. The system repairs and revalidates; if it still fails, the user receives a fallback template and the failure is logged. |
| **F-29** | If retrieval finds no corpus passage above the relevance threshold, the system returns a **no-grounding template** (not model knowledge) and records the gap for the editorial team. |

### **6.4 Safety, crisis, and emotional deferral**

| ID | Requirement |
|---|---|
| **F-30** | Messages containing self-harm, suicide, or acute crisis signals bypass the answer engine and return a **pre-approved crisis template** containing at least one helpline. Never composed by the model. |
| **F-31** | Crisis templates are authored and approved by the editorial team before launch, served from configuration, and never open a human chat. |
| **F-32** | Crisis events are recorded without generation, visible to admins, and excluded from ordinary topic analytics. |
| **F-44** | Questions classified `emotional_only` return an **emotional-deferral template** that includes a contact number configured in the admin portal / backend. Never composed by the model. No theology lecture on emotional subjects. |
| **F-45** | Admins can view and update the emotional-support contact number (and related template fields) used by F-44. Changes are audited. |

### **6.5 "Like" Interaction**

| ID | Requirement |
|---|---|
| **F-17** | Every composed or curated answer (never refusal, crisis, emotional-deferral, or no-grounding templates) shows a Like control. |
| **F-18** | Like counts are persisted per answer and per topic and are visible to admins. |
| **F-33** | Like is idempotent per user per answer and can be undone. Guest likes are attributed to the anonymous session identity. |

### **6.6 Admin Panel**

| ID | Requirement |
|---|---|
| **F-19** | The admin panel is reachable only through authentication separate from end-user accounts. |
| **F-20** | Admins can browse every question asked, with timestamp, assigned topic, and like count. |
| **F-21** | Admins can view questions grouped by topic with a count per topic. |
| **F-22** | Admins can see how frequently semantically similar questions are asked. |
| **F-23** | Admins can add or edit the canonical answer for a topic, with automatic validation that the answer stays within 25–250 words. |
| **F-34** | Admin edits to a curated answer are validated against F-11 through F-14 before save. |
| **F-35** | Admins can filter the question list by date range, topic, refusal, crisis, emotional-deferral, and no-grounding. |
| **F-36** | Admins can export the filtered question list as CSV. |
| **F-37** | Destructive admin actions are written to an audit log before execution. |

### **6.7 Distribution**

| ID | Requirement |
|---|---|
| **F-38** | The web build is embeddable on WordPress as a widget without rebuilding the host page, and adapts to container width. |
| **F-39** | The Android build is produced from the same Nuxt frontend and passes Google Play pre-launch checks for a religious-content application. |
| **F-40** | Both distributions talk to the same backend API; there is no channel-specific answer logic. |

### **6.8 Content Sources**

Every composed answer must be traceable to a site on the approved allowlist. Version 1.0 is the five domains in §5.3.

### **6.9 Corpus ingestion (crawl → RAG)**

| ID | Requirement | v1.0 |
|---|---|---|
| **F-41** | The system crawls every domain on the allowlist, extracts article text, chunks it, embeds it, and stores it for vector retrieval. Answers are composed only from retrieved chunks. | Yes |
| **F-42** | Adding a site to the allowlist (admin UI) triggers a crawl of that site and makes its articles eligible for retrieval and citation. Removing a site retires its chunks and requires review of curated answers that cited it. | **Post-v1.0** |
| **F-43** | Ingestion is resumable and idempotent. Unchanged articles produce no writes. A weekly scheduled run keeps the index current for all approved sites; an admin can trigger a run on demand. | Yes (for the five sites) |

---

## **7\. Non-Functional Requirements**

### **7.1 Platform & distribution**

* Responsive web app embeddable as a WordPress widget **and** wrapped as Android via Capacitor, from **one Nuxt 3 SPA** codebase.
* Mobile-first.
* Fully static frontend build (`nuxt generate`) — no Node at request time. See [Frontend Framework Decision — Nuxt](frontend-framework-decision-nuxt.md).

### **7.2 Language & localisation**

* Entire interface, answers, and system messaging in Indonesian.
* Strings in a single message catalogue per surface.

### **7.3 Performance**

Per the Aug 2026 product brief:

| Measure | Target |
|---|---|
| Answer returned to the user (average / typical) | **&lt; 5 seconds** under normal network conditions |
| First contentful paint on 3G mobile | &lt; 3 s |
| Initial JS bundle (widget entry) | &lt; 250 KB gzipped |
| Template paths (refusal, crisis, emotional deferral, no-grounding) | &lt; 1 s (no composer LLM call) |

### **7.4 Security & data privacy**

* Mobile numbers collected via SMS/WhatsApp are stored **securely**, used only for authentication and session recognition, and never displayed in full in the admin panel.
* Guest users generate no personally identifiable data. The anonymous identifier must not be derivable from device fingerprinting.
* The admin panel is protected by real authentication (not a shared static password), enforced at the data layer as well as the UI.
* **LLM calls use a Zero Data Retention (ZDR) tier.** No user question may be retained by a model provider for training. A provider that cannot contract for ZDR cannot be used. Confirmed in writing before Phase 5 (PIP B3).
* Question text is retained for editorial analytics; retention window configurable (default 12 months).

### **7.5 Scalability**

* Data model must absorb growth in question volume without schema redesign.
* Retrieval latency must stay within the §7.3 answer-time budget as the corpus grows within the five sites.
* Admin question list usable at 100,000+ records via server-side pagination and filtering.

### **7.6 Accessibility**

* WCAG 2.1 AA contrast minimum; keyboard operable; no information by colour alone; text resize to 200% without loss of function.

---

## **8\. User Stories**

### **8.1 Seeker**

* **US-1** — As someone with a question I am embarrassed to ask a person, I want to ask anonymously, so that I can explore without being identified.
* **US-2** — As a reader who wants to verify what I am told, I want links to the source articles, so that I can read further myself.
* **US-3** — As a Muslim asking about Isa Al-Masih, I want the answer to use "Allah" and "Isa Al-Masih", so that it reads as written for me.
* **US-4** — As a user on a slow connection, I want to see that my question was received, so that I do not send it three times.
* **US-5** — As a returning user, I want to sign in with the phone number I already use for WhatsApp, so that I do not have to remember a password.
* **US-11** — As someone who only needs emotional support (not a faith question), I want a clear way to reach a human contact number, so that I am not given a theology answer I did not ask for.

### **8.2 Equipper**

* **US-6** — As a Christian preparing to talk with a Muslim friend, I want an answer that uses the terms my friend uses, so that the conversation does not stall on vocabulary.

### **8.3 Editorial Admin**

* **US-7** — As an editor, I want to see the twenty most-asked topics this month, so that I know what to write next.
* **US-8** — As an editor, I want to see questions where the system found no grounding, so that I can identify gaps in our corpus.
* **US-9** — As an editor, I want to write the definitive answer for "Jalan Keselamatan" once, so that every user asking about it gets our approved wording.
* **US-10** — As an editor, I want to know which answers were liked, so that I can learn what lands.
* **US-12** — As an editor, I want to set the emotional-support contact number, so that emotional-only questions are deferred correctly.

---

## **9\. Primary Use Cases**

* **UC-1 — Anonymous first question.** Guest asks a theology question; system retrieves, composes an empathetic grounded answer with citations; user may Like.
* **UC-2 — Out-of-scope question.** Football scores → refusal template, &lt; 1 s, no composer.
* **UC-3 — Curated answer.** Topic with published curated answer → verbatim curated text, no generation.
* **UC-4 — Grounding gap.** Theology question, nothing above threshold → no-grounding **template**; flagged in Content Gaps.
* **UC-5 — Crisis signal.** Crisis template with helplines; no generation; excluded from topic analytics.
* **UC-6 — Emotional-only.** Classifier marks `emotional_only` → emotional-deferral **template** with admin-configured contact number; no generation.
* **UC-7 — Rate limit.** 31st message in an hour → rate-limit message.
* **UC-8 — Editorial review.** Admin filters, edits curated answer, validators pass, save.
* **UC-9 — Widget.** Same answers on WordPress embed as on Android.

---

## **10\. Data Model (Product View)**

Engineering schema: **Technical Design Document** §3.

| Entity | What it holds | Why |
|---|---|---|
| **User** | ID, auth method, phone (optional), timestamps | Session, rate limit, usage |
| **Session** | Conversation on one device | Multi-turn (F-8), engagement |
| **Question** | Text, topic, answer, links, likes, flags (`refusal` / `crisis` / `emotional_deferral` / `no_grounding`), latency | Admin analytics and KPIs |
| **Topic** | Name, curated answer, links, editor, aggregates | F-21, F-23 |
| **Article** / **chunk** | Corpus + embeddings | F-15, F-41 |
| **Question cluster** | Similar-question frequency | F-22 |
| **System config** | Emotional contact number, template ids, thresholds | F-44, F-45 |
| **Admin user** / **Audit log** | Auth and accountability | F-19, F-37 |

---

## **11\. Success Metrics (KPIs)**

| # | Metric | Definition | Initial target |
|---|---|---|---|
| K1 | Answer rate | Composed/curated answers ÷ in-scope theology questions | Baseline in pilot; ≥85% by launch + 60 days |
| K2 | Like rate | Likes ÷ answers shown | Trend upward |
| K3 | Questions per session | Mean questions per session | 1–50 (brief); healthy median above 2 |
| K4 | Content-rule compliance | Composed answers passing F-11–F-15 at display | **100%** — gate |
| K5 | Answer latency | Time to display for composed answers | **Average &lt; 5 s** (product brief) |
| K6 | Weekly active users | Distinct users with ≥1 question / week | Set after launch |
| K7 | Grounding-gap rate | No-grounding ÷ theology-classified questions | &lt; 10%, falling as corpus improves |
| K8 | Curated coverage | Share of answers from curated topics | Grows with editorial work |
| K9 | Crisis routing | Sampled crisis-flagged messages that were genuine crisis | Monthly review; false negatives are P0 |

K4 and K9 are release gates.

---

## **12\. Assumptions & Dependencies**

* The five source sites stay reachable and crawling/reuse is permitted for this purpose.
* Accounts exist before production: Firebase / Google Cloud, WhatsApp OTP provider, an **LLM provider on a Zero Data Retention tier** (PIP B3), Google Play Developer.
* An **editorial** reviewer approves composer prompt, refusal copy, crisis scripts, emotional-deferral template, and no-grounding copy **before** pilot.
* The LLM handles Indonesian well and can be constrained to supplied context.
* Phase 1 prototype (keyword engine, ~68 articles, UI flow) is a behaviour reference, not the production codebase.
* Frontend is **Nuxt 3**, not React.

---

## **13\. Risks & Mitigations**

| # | Risk | Impact | Mitigation |
|---|---|---|---|
| R1 | Theologically inaccurate or off-tone answers | Severe | Grounding + validators (F-12) + curated overrides + sampled editorial review |
| R2 | Classifier edges (theology vs emotional-only vs irrelevant) | Medium | LLM classifier with review queue; templates for non-theology paths |
| R3 | Google Play religious-content policy | Severe | Clear listing; not counselling; budget one resubmit |
| R4 | Spam / abuse | Medium | Rate limit 30/h; admin flag/delete; auto-moderation later |
| R5 | OTP / LLM vendor change | Medium–high | Provider abstraction; cost monitoring; fallback model |
| R6 | Crisis message gets theology instead of help | Severe | Crisis guard first; **templates only**; K9 |
| R7 | Thin corpus | Medium | K7 → editorial queue; no-grounding template |
| R8 | Phone number misuse | Severe | Secure storage; masked admin display; no raw export; data-layer ACL |
| R9 | Widget vs WordPress themes | Low–medium | iframe + embed.js + host matrix |
| R10 | Emotional-only misclassified as theology | Medium | Classifier tests; F-44 template; admin contact config |

---

## **14\. Phased Release Plan**

Nine phases. Engineering breakdown: [Project Implementation Plan](project-implementation-plan.md).

| Phase | Outcome | Gate to the next phase |
|---|---|---|
| **P1 — Prototype & validation** *(complete)* | Keyword answer engine, ~68 seeded articles, full UI flow across onboarding, chat, and admin | Interaction model validated with real users |
| **P2 — Production foundation** | Nuxt frontend and backend skeleton, Firestore data model, Guest auth, ask endpoint at prototype parity | Guest can ask and receive an answer on staging |
| **P3 — Identity** | Firebase phone auth for SMS, WhatsApp OTP provider, session model, rate limiting, hardened admin auth | All three sign-in paths work end to end on staging |
| **P4 — Corpus** | Crawl of all five sites, chunking, embeddings, vector index, article metadata, scheduled refresh | Retrieval returns relevant passages for a benchmark question set |
| **P5 — Production answer engine** | Crisis / emotional-deferral / no-grounding **templates**, relevance classifier, RAG composition, compliance validators, curated-answer override | K4 = 100% on the benchmark set; editorial sign-off on prompts and templates |
| **P6 — Editorial surface** | Admin portal: question list, topic grouping, similar-question clustering, curated answers, likes, export, contact-number config (F-45) | Editorial team can complete one full review cycle unaided |
| **P7 — Distribution** | WordPress widget embed, Capacitor Android build, Play Store listing prepared | Widget live on one host site; internal Android build installs and works |
| **P8 — Pilot** | Supervised pilot on staging with real testers, per the **Pilot Plan** | Exit criteria in the Pilot Plan met; go / no-go recorded |
| **P9 — Launch** | Widget on host WordPress sites, Play Store submission, post-launch monitoring | KPI baselines captured; K4 and K9 green |

**Post-v1.0 (after P9):** F-42 allowlist growth via admin (add site → crawl).

---

## **15\. Open Product Decisions**

| # | Decision | Needed by | Default if undecided |
|---|---|---|---|
| OD-1 | WhatsApp OTP provider and per-message cost ceiling | P3 | Twilio Verify |
| OD-2 | Retention window for question text | P2 | 12 months |
| OD-3 | Signed-in history across devices | P3 | No — device-local in 1.0 |
| OD-4 | Crisis helpline numbers and verification date | P5 | Blocks P5 — no default |
| OD-5 | Widget on all five sites at launch or staged | P9 | One site first, then +7 days |
| OD-6 | Who owns editorial sign-off on prompts/templates and re-review cadence | P5 | Blocks P5 — no default |
| OD-7 | Emotional-support contact number and template copy (F-44 / F-45) | P5 | Blocks P5 — no default |

---

## **Appendix A: Supported Topics**

Topic labels match the Aug 2026 product brief. Each is a grouping key (F-21) and curated-answer slot (F-23). **Emotional-only questions are not answered under these topics** — they use F-44. Topics such as *Duka & Kehilangan* or *Kecemasan & Depresi* apply only when the user asks a **faith/theology** question that maps there and the corpus can ground an answer.

| # | Topic (Indonesian) | Topic (English) | Slug |
|---|---|---|---|
| 1 | Kasih Allah | Love of Allah | `kasih-allah` |
| 2 | Jalan Keselamatan | Path of Salvation | `jalan-keselamatan` |
| 3 | Takut Akan Neraka | Fear of Hell | `takut-neraka` |
| 4 | Ketenangan Hati | Peace of Mind | `ketenangan-hati` |
| 5 | Dosa & Pengampunan | Sin & Forgiveness | `dosa-pengampunan` |
| 6 | Duka & Kehilangan | Grief & Loss | `duka-kehilangan` |
| 7 | Kecemasan & Depresi | Anxiety & Depression | `kecemasan-depresi` |
| 8 | Pernikahan & Keluarga | Marriage & Family | `pernikahan-keluarga` |
| 9 | Identitas Isa Al-Masih | Identity of Isa Al-Masih | `identitas-isa-almasih` |
| 10 | Kematian Isa Al-Masih | Death of Isa Al-Masih | `kematian-isa-almasih` |
| 11 | Keaslian Kitab Suci | Authenticity of the Holy Scripture | `keaslian-kitab-suci` |
| 12 | Ibadah & Puasa | Worship & Fasting | `ibadah-puasa` |
| 13 | Pencarian Kebenaran | Search for Truth | `pencarian-kebenaran` |

Pseudo-topic `lainnya` (Other) catches theology-relevant questions that do not map to the thirteen.

---

## **Appendix B: Requirement Traceability & v1.0 recommendation (E.12)**

| Requirement range | Origin | v1.0 |
|---|---|---|
| F-1 – F-23 | Aug 2026 product brief | Yes (F-9/F-10 clarified for theology vs emotional-only) |
| F-24 – F-27 | Engineering upgrade | Yes — OTP throttle, guest convert, loading, retry |
| F-28 | Engineering upgrade | Yes — validator gate |
| F-29 | Engineering upgrade | Yes — **template**, not AI |
| F-30 – F-32 | Engineering upgrade | Yes — **crisis templates**, not AI |
| F-33 | Engineering upgrade | Yes |
| F-34 – F-37 | Engineering upgrade | Yes — admin parity, filters, CSV, audit |
| F-38 – F-40 | Brief platform prose → requirements | Yes — Nuxt delivery |
| F-41, F-43 | Crawl → RAG | Yes — five sites + schedule |
| F-42 | Allowlist growth via admin | **Post-v1.0** |
| F-44 – F-45 | Product decision Aug 2026 | Yes — emotional deferral template + admin contact |

---

## **Related Documents**

| Document | Purpose |
|---|---|
| [Technical Design Document (TDD)](tdd.md) | Architecture, components, schema, security |
| [AI Answer Engine Specification](ai-answer-engine-specification.md) | Pipeline, prompts, validators, grounding rules |
| [Frontend Framework Decision — Nuxt](frontend-framework-decision-nuxt.md) | Why Nuxt SPA; three delivery targets |
| [Chat UX Specification](chat-ux-specification.md) | Seeker-facing interaction and copy |
| [Admin UX Specification](admin-ux-specification.md) | Editorial portal |
| [Project Implementation Plan](project-implementation-plan.md) | Phases 1–9, tasks, tests, blockers |
| [Content Ingestion & RAG Runbook](content-ingestion-and-rag-runbook.md) | Crawl, chunk, embed, refresh |
| [Pilot Plan](pilot/pilot-plan.md) | Supervised pilot and exit criteria |
