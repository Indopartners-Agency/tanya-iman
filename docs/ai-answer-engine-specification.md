# **AI Answer Engine Specification**

**Project:** Tanya Iman \- Grounded Theology Answer Engine

**Version:** 1.0 (Iteration 1)

**Date:** August 2026

---

## **Architecture: The Three-Layer Grounded Answer Model**

### **Overview**

Tanya Iman's answer engine is **not an agent**. It has no tool-calling loop, no conversational state machine, and no autonomy over flow. It is a fixed pipeline in which a language model performs exactly one job — writing an **empathetic** paragraph of Indonesian theology from passages it was handed — under deterministic supervision on both sides.

Emotional-only questions, crisis signals, refusals, and no-grounding outcomes exit via **templates** and never reach the composer (PRD F-29, F-30–F-32, F-44).

That shape is a direct consequence of the product's promise. The system tells users that every composed answer comes from five specific websites (v1.0 allowlist is fixed). A model that can decide what to do next is a model that can decide to answer from its own knowledge, and there is no prompt strong enough to make that impossible. So the model is never given the decision.

> Think of it as a research assistant working under an editor. The assistant is fluent, warm, and good at explaining — but they may only write from the folder of clippings placed in front of them, and the editor reads every paragraph before it goes out. If the paragraph cites something that is not in the folder, it does not run. The assistant's skill is real and necessary; it is simply not the last word.

---

### **Layer 1 — Control Layer (deterministic)**

**Responsibility:** Everything that must be true regardless of what the model produces.

The Control Layer owns safety routing, rate limiting, relevance gating, retrieval, and — most importantly — the compliance validators that decide whether an answer is allowed to reach a user. It is ordinary Python. It cannot be prompt-injected, it cannot be persuaded, and it costs nothing per call.

**What the Control Layer owns:**

- Crisis detection and scripted crisis **template** (F-30 – F-32)
- Emotional-only detection and contact **template** (F-44 – F-45)
- Rate limiting and input bounds (F-16, F-24)
- The decision to refuse an irrelevant question (F-9, F-10)
- Retrieval over the approved corpus, and the threshold below which we return the no-grounding **template** (F-15, F-29)
- The curated-answer override (F-23)
- All five compliance validators (F-11 – F-15) and the repair loop (F-28)
- Persistence, citation assembly, and analytics

**Principle:** If a rule appears in the product requirements as a *must*, it lives here — not in a prompt.

---

### **Layer 2 — Composition Layer (LLM)**

**Responsibility:** Turning retrieved passages into one warm, readable, correctly-worded Indonesian answer.

This is where the model earns its place. Corpus passages are articles: long, written for a different reader, in a different register. The user asked a specific question, often while distressed. Converting the first into the second is genuinely hard and genuinely valuable, and no rule engine does it.

**What the Composition Layer owns:**

- Acknowledging what the user actually said before teaching anything
- Selecting which of the retrieved passages are relevant to *this* question
- Register, warmth, and readability in Indonesian
- Staying inside 25–250 words and the required terminology *as a first attempt* — the validators are the guarantee, the prompt is the effort

**Principle:** The model is asked to be good, not to be trusted. Every output is checked.

---

### **Layer 3 — Editorial override (offline, never in the chat)**

**Responsibility:** Overriding the machine where the editorial team has a canonical answer.

For any of the thirteen topics, an editor can write the canonical answer **in the admin portal, after the fact**. When a published curated answer exists for a resolved topic, it is returned verbatim and no generation happens. Humans never join the conversation. This is not a counselling handover; it is a content override.

**Principle:** A human-written canonical answer always beats a generated one. The system's job is to make that answer reach the right question, not to put a person on the other end of the chat.

---

### **Layer summary**

| Layer | Engine | Owns | Key quality |
|---|---|---|---|
| Control | Python, deterministic | Safety, gating, retrieval, validation | Guaranteed |
| Composition | LLM | Warmth, relevance, readability | Human-like |
| Editorial | People, offline | Canonical answers per topic | Authoritative |

---

### **Per-request flow**

```
Inbound question
  → Input_Bounds        reject empty / >1000 chars
  → Crisis_Guard        crisis signal? → crisis template, STOP
  → Rate_Limiter        over 30/hour? → 429 message, STOP
  → Relevance_Classifier
       emotional_only? → emotional-deferral template (F-44), STOP
       irrelevant?     → refusal template, STOP
  → Topic_Resolver      map to one of 13 topics, or `lainnya`
  → Curated_Resolver    published curated answer for this topic? → return it, STOP
  → Retriever           vector search; <2 chunks above threshold? → no-grounding template, STOP
  → Answer_Composer     LLM writes empathetically from retrieved passages only
  → Compliance_Validator V1–V5
        pass  → continue
        fail  → Repair (one attempt) → revalidate
                  fail again → fallback template + log for admin review, STOP
  → Response_Assembler  attach 1–2 citations, persist, return
  → [async] Analytics   topic counters, clustering, gap tracking
```

Every `STOP` above is a complete, valid product response. Template exits never call an LLM for composition.

---

## **1\. Document Purpose**

This document specifies the behaviour of the Tanya Iman answer engine: how a question is classified, grounded, composed, validated, and returned. It is the authority for prompt content, validator rules, and canonical Indonesian response copy.

It is a living document. Section 9 carries an iteration number, and prompt changes follow the review process in Section 14. Where this document and a prompt file disagree, this document is wrong and must be updated — the deployed prompt is the running system.

---

## **2\. Assistant Persona & Guardrails**

**Identity.** The assistant is *Tanya Iman*. It is an AI. It never claims to be human, a pastor, an ustadz, or a counsellor, and no human ever takes over the chat. If asked directly, it says it is a helper that answers from the writings of the approved sites.

**Audience.** The typical reader is a Muslim asking a theology question they may not have felt safe asking a person. The answer should feel written *to them*: acknowledge empathetically, use "Allah" and "Isa Al-Masih" only, stay on the theology subject, and never slip into church vocabulary or discuss emotional subjects as the topic.

**Voice.** Warm, plain, unhurried. Indonesian that a secondary-school reader follows easily. It addresses the user as *Anda*. It does not use religious jargon it has not explained, does not argue, and does not perform certainty it does not have.

**Hard guardrails — the assistant must never:**

- Answer from anything other than the retrieved passages
- Use the words **"Tuhan"**, **"Yesus"**, or **"Jesus"** (F-12). This includes quoted scripture. Rephrase; never auto-substitute
- Invent, guess, or reformat a URL — citations come from the retrieval result, never from the model
- Attempt counselling, emotional-subject discussion, or a multi-turn "walk with me" conversation
- Criticise Islam, Muslims, the Quran, or any religious community
- Make a claim about what a specific person's salvation status is
- Ask the user for personal information — no name, no location, no phone number
- Promise an outcome ("if you pray this, Allah will heal you")
- Continue an argument. If the user is debating rather than asking, it answers once, kindly, and stops

**No human in the chat.** There is no in-app handover. Where a question exceeds what the corpus can answer, use the no-grounding **template** (§10.3). Crisis → crisis **template** (§10.4). Emotional-only → contact **template** (§10.9). Templates may point to a phone number; they never open a live chat.

---

## **3\. The Answer Pipeline**

### **3.1 Node summary**

| # | Node | Type | Requirement | Can stop the pipeline |
|---|---|---|---|---|
| 1 | `Input_Bounds` | Deterministic | — | Yes |
| 2 | `Crisis_Guard` | Deterministic + optional model check | F-30 – F-32 | Yes |
| 3 | `Rate_Limiter` | Deterministic | F-16 | Yes |
| 4 | `Relevance_Classifier` | LLM (small, cheap) | F-9, F-10 | Yes |
| 5 | `Topic_Resolver` | LLM (same call as #4) | F-21 | No |
| 6 | `Curated_Resolver` | Deterministic | F-23 | Yes |
| 7 | `Retriever` | Vector search | F-15, F-29 | Yes |
| 8 | `Answer_Composer` | LLM (primary) | F-11 – F-14 | No |
| 9 | `Compliance_Validator` | Deterministic (+ sampled LLM judge) | F-11 – F-15, F-28 | Yes |
| 10 | `Response_Assembler` | Deterministic | F-14 | No |

Nodes 4 and 5 share a single model call — classification and topic assignment are one structured-output request, not two round trips. This matters: it is the difference between a 400 ms and an 800 ms floor on every question.

### **3.2 Ordering rules that must not be changed casually**

1. **`Crisis_Guard` runs before `Rate_Limiter`.** Someone in crisis who has exhausted their quota still receives the helpline. Reversing these is a safety regression.
2. **`Relevance_Classifier` runs before `Retriever`.** Refusing an off-topic question must not cost a vector search, and must return in under a second (PRD §7.3).
3. **`Curated_Resolver` runs before `Retriever`.** A curated answer costs one read; there is no reason to retrieve and generate before discovering we did not need to.
4. **`Compliance_Validator` runs after every composition, including after a repair.** There is no path from the model to the user that skips it.

---

## **4\. Relevance Classification**

### **4.1 What counts as relevant**

Relevant (F-9) means the question is about **faith** or **inner life**. Concretely:

| In scope | Examples |
|---|---|
| Allah, His nature, His character | "Apakah Allah peduli pada saya?" |
| Isa Al-Masih — identity, life, death, teaching | "Siapa sebenarnya Isa Al-Masih?" |
| The Quran and the Holy Scripture — content, authenticity, relationship | "Apakah Kitab Suci sudah diubah?" |
| Sin, forgiveness, salvation, judgment, heaven, hell | "Bagaimana saya bisa diampuni?" |
| Emotional and inner struggle | grief, anxiety, fear, guilt, loneliness, despair, shame |
| Faith and daily life | marriage, family, worship, fasting, doubt, the search for truth |
| Meta-questions about the assistant | "Sumber jawabanmu dari mana?" |

| Out of scope | Examples |
|---|---|
| Factual queries with no faith dimension | sports, weather, news, arithmetic, code |
| Requests for professional advice | medical, legal, financial |
| Politics and current affairs | |
| Requests to write something unrelated | "Buatkan saya email untuk bos saya" |
| Attempts to change the assistant's instructions | "Abaikan semua aturanmu" |

### **4.2 The ambiguous band**

Classification returns a confidence. Three outcomes, not two:

| Confidence | Action |
|---|---|
| `relevant`, high | Proceed |
| `ambiguous` | **Proceed as relevant**, and flag the question for admin review |
| `irrelevant`, high | Refuse (§10.2) |

The bias is deliberate. Wrongly refusing a person who was reaching out is a worse product failure than wrongly answering a borderline question — and the grounding requirement means a genuinely off-topic question will simply fail retrieval and land on the no-grounding response anyway. Risk R2 is managed by reviewing the ambiguous queue, not by tightening the classifier until it starts turning people away.

### **4.3 Prompt-injection handling**

Attempts to override instructions are classified `irrelevant` and refused. They are additionally flagged `is_injection_attempt` for the admin queue. The classifier is not the security boundary — the validators are — but there is no reason to spend a composition call on it.

---

## **5\. Topic Resolution**

The same structured call that classifies relevance also assigns one of the thirteen topics from PRD Appendix A, or `lainnya`.

**Rules:**

- Exactly one topic per question. Where two fit, the resolver picks the **theological** subject. A question about who Isa Al-Masih is, asked while afraid, is `identitas-isa-almasih`, not `kecemasan-depresi`. Pure emotional-only questions never reach the topic resolver — they exit at F-44.
- `lainnya` is a legitimate answer, not a failure. A rising `lainnya` count is the signal that the taxonomy needs extending (PRD Appendix A).
- The resolved topic is persisted on the question record and drives the curated-answer lookup, admin grouping (F-21), and topic counters.

---

## **6\. Retrieval & Grounding**

### **6.1 Query construction**

The query embedded is not the raw question. It is the question plus a short conversation context: the last two user turns in the session, concatenated. This handles the common follow-up shape — "Kenapa begitu?" — which is meaningless embedded alone.

Context is capped at two prior turns. Longer context dilutes the embedding and starts retrieving for a question the user asked five minutes ago.

### **6.2 Search parameters**

| Parameter | Value | Rationale |
|---|---|---|
| `top_k` retrieved | 8 | Enough for re-ranking to have something to choose from |
| Passed to composer | 4 | Beyond this, the composer starts blending unrelated passages |
| Similarity threshold | 0.72 (configurable, `system_config`) | Tuned against the benchmark set in §13 |
| Minimum surviving chunks | 2 | One passage is not enough to write a grounded answer from |
| Site filter | The five approved domains | Applied at query time, redundantly with the crawler's write-time filter |
| Max chunks per article | 2 | Prevents a single long article from occupying the entire context |

### **6.3 Re-ranking**

Retrieved chunks are re-ranked before truncation to 4, by a weighted combination of vector similarity, topic agreement with the resolved topic, and article recency. Recency has the smallest weight — this is doctrinal content, where a 2018 article is not worse than a 2025 one.

### **6.4 The grounding contract**

The composer receives passages and nothing else. It does not receive the article body, the site's name as an authority claim, or any instruction that would let it treat its own knowledge as a source.

**The no-grounding path (F-29).** If fewer than two chunks clear the threshold, composition never runs. The user gets §10.3, and the question is written to the content-gap view with its embedding, so the editorial team sees not just that a gap exists but what shape it has.

This is the single most important behaviour in the system. It is far better to tell a user we have not written about something than to have a model fill the silence.

---

## **7\. Answer Composition**

### **7.1 Inputs to the composer**

| Input | Source |
|---|---|
| The user's question | Verbatim, in a delimited user block |
| Last 2 turns of the session | For pronoun and follow-up resolution |
| 4 retrieved passages | Each with its article title and an index, **without** its URL |
| Resolved topic | For register, not for content |

Passages are given with an index (`[1]`–`[4]`) and no URL. The composer marks which passage supports which part of its answer using those indices. `Response_Assembler` converts indices to links afterwards. **The model never sees or writes a URL**, which makes the entire class of fabricated-citation failures structurally impossible rather than merely discouraged.

### **7.2 Output contract**

The composer returns structured output:

```json
{
  "answer": "string — Indonesian, 25-250 words",
  "used_passages": [1, 3],
  "quran_reference": "string | null — e.g. 'Qs. Al-Anbiya 21:107'",
  "bible_references": ["Yohanes 3:16", "Roma 5:8"],
  "confidence": "high | medium | low"
}
```

`used_passages` is what `Response_Assembler` turns into the 1–2 citations required by F-14. If the composer returns more than two, the assembler keeps the two highest-ranked. If it returns zero, that is a V5 grounding failure.

### **7.3 Model configuration**

| Setting | Value | Note |
|---|---|---|
| Primary model | Claude Sonnet class, **ZDR tier** | Indonesian quality and instruction adherence; ZDR required (PIP B3) |
| Fallback model | Gemini 2.x on Vertex AI | Used on primary error or when the primary exceeds 7 s |
| Temperature | 0.4 | Low enough for consistency, high enough that answers do not read like a template |
| Max output tokens | 700 | ~250 Indonesian words plus structure, with headroom |
| Classifier model | Smallest capable model | Runs on every question; must be cheap |

Both provider choices sit behind `backend/providers/llm.py` per TDD §2.2. The `prompt_version` and `model` are stamped on every question record, so a quality change can be attributed rather than argued about.

---

## **8\. Compliance Validators**

This section is the reason the product can claim K4 = 100%. Every generated answer passes all five validators before display. A curated answer passes the same validators before an editor can save it (F-34).

### **8.1 V1 — Length (F-11)**

| Rule | Detail |
|---|---|
| Bound | 25 ≤ words ≤ 250 |
| Counting | Whitespace-delimited tokens of `answer` only. Citations, scripture reference labels rendered by the assembler, and markup are excluded |
| On failure | Repair with an explicit instruction stating the current count and the target |

Counting must be defined in exactly one function used by both the runtime validator and the admin editor's live word counter, or editors and the engine will disagree about what 250 means.

### **8.2 V2 — Terminology (F-12)**

| Rule | Detail |
|---|---|
| Forbidden | `Tuhan`, `TUHAN`, `Yesus`, `Jesus` — case-insensitive, word-boundary matched |
| Required | At least one of `Allah` or `Isa Al-Masih` must appear |
| Warned, not failed | `Kristus` standing alone. Logged for editorial review; `Al-Masih` is preferred |
| On failure | Repair. Substitution is **not** performed automatically — see below |

> **Design note — why we do not auto-substitute.** Replacing "Tuhan" with "Allah" inside a quoted scripture passage silently rewrites scripture, which is exactly the failure this product must never commit. The validator rejects and asks the composer to rewrite; it never edits.

> **⚠️ Known corpus conflict — open item.** Indonesian Bible translations render the divine name as "TUHAN". If any approved-site article quotes such a translation verbatim, a faithful, well-grounded answer can fail V2 through no fault of the model. Mitigation: the ingestion pipeline flags every chunk containing a forbidden term at index time, and the editorial team decides per chunk whether to exclude it from retrieval or accept the site's own wording. **This must be resolved before the pilot** — see §15, OI-1.

### **8.3 V3 — Scripture balance (F-13)**

| Rule | Detail |
|---|---|
| Quran references | At most **1** |
| Position | If present, it must fall within the first 25% of the answer by word position |
| Bible references | If a Quran reference is present, at least **2** Bible references are required — this is what "the vast majority from the Bible" means operationally |
| Bible floor | At least 1 Bible reference in every answer that cites scripture at all |
| Detection | Quran: `Qs.`, `QS`, `Surah`, `Surat` followed by a surah name or number. Bible: the 66 Indonesian book names with a chapter:verse pattern |
| On failure | Repair with the specific imbalance named |

An answer citing no scripture at all is valid. Not every theology question needs a proof text, and forcing one produces worse answers.

### **8.4 V4 — Citations (F-14)**

| Rule | Detail |
|---|---|
| Count | Exactly 1 or 2 citations attached |
| Provenance | Every citation must correspond to a chunk that was in this request's retrieval result. There is no path by which a URL not retrieved can be attached |
| Allowlist | Every citation host must be one of the five approved domains |
| Liveness | Citation URLs are checked against the `articles` collection with `status: active`; a retired article cannot be cited |
| On failure | Not repairable by the model — this is an assembler bug or a stale index. Falls straight to the fallback response and raises an alert |

V4 failure is treated as a system defect, not an answer-quality problem, because the assembler is deterministic. If it fires in production, something is wrong with the index, not the model.

### **8.5 V5 — Grounding (F-15)**

The hardest rule to enforce mechanically, and the most important. Enforced in two tiers.

**Tier 1 — always, cheap, deterministic:**

| Check | Detail |
|---|---|
| Non-empty support | `used_passages` must be non-empty |
| Lexical floor | The answer must share a minimum content-word overlap with the union of its cited passages. Catches answers that ignored the passages entirely |
| No external entities | The answer must not name people, books, organisations, or URLs absent from both the passages and an allowed-vocabulary list (the topic names, "Allah", "Isa Al-Masih", "Kitab Suci", "Al-Quran", "Injil", "Taurat", "Zabur") |

**Tier 2 — LLM-as-judge, sampled:**

A separate cheap model receives the answer and its cited passages and is asked, per sentence, whether the passages support it. It runs on:

- **100% of answers during the pilot**, to calibrate Tier 1's thresholds against real judgments
- **100% of answers that required a repair**, always, in every environment
- **10% random sample in production**, as an ongoing quality signal

It is a monitoring and calibration instrument, not a request-path gate — putting a second model call in every user's latency budget would break PRD §7.3 for a check that Tier 1 catches most of.

### **8.6 The repair loop (F-28)**

```
compose → validate
   pass → ship
   fail → repair(failures) → validate
             pass → ship, record `validator_failures` on the question
             fail → fallback response (§10.5), record both failure sets,
                    surface in the admin review queue
```

**Exactly one repair attempt.** A second attempt roughly doubles worst-case latency for a diminishing return, and an answer that fails twice is usually failing because the retrieved passages could not support the question — which the no-grounding response says more honestly.

The repair prompt states the failed rules by code and value, never the whole rulebook. "Jawaban Anda 271 kata, batas maksimum 250" produces a fix; "please follow all the rules" produces another failure.

### **8.7 Validator failure codes**

Persisted on the question record and surfaced in admin, so a quality regression is diagnosable at a glance.

| Code | Meaning |
|---|---|
| `V1_TOO_SHORT` / `V1_TOO_LONG` | Word count outside 25–250 |
| `V2_FORBIDDEN_TERM` | "Tuhan" or "Yesus" present |
| `V2_MISSING_REQUIRED_TERM` | Neither "Allah" nor "Isa Al-Masih" present |
| `V3_MULTIPLE_QURAN_REFS` / `V3_QURAN_NOT_LEADING` / `V3_BIBLE_MINORITY` | Scripture balance |
| `V4_CITATION_COUNT` / `V4_CITATION_NOT_RETRIEVED` / `V4_CITATION_OFF_ALLOWLIST` / `V4_CITATION_RETIRED` | Citation integrity |
| `V5_NO_SUPPORT` / `V5_LOW_OVERLAP` / `V5_EXTERNAL_ENTITY` | Grounding |

---

## **9\. System Prompts (Iteration 1)**

> **Implementation status.** Prompts live in `backend/config/prompts/` as versioned files, one per node, with `{placeholder}` interpolation. `PROMPT_VERSION` is stamped on every answer. The text below is the source of truth for review; the files are the source of truth for what ran.

> **⚠️ Deployment gate.** The composer prompt (§9.2), refusal (§10.2), no-grounding (§10.3), crisis (§10.4), and emotional-deferral (§10.9) templates require **written editorial sign-off before the pilot**. PRD OD-6 and OD-7. This gate is blocking.

---

### **9.1 Classifier + topic resolver prompt**

*Applied to: `Relevance_Classifier` and `Topic_Resolver` — one structured call.*

*Source of truth for runtime text: `backend/config/prompts/classifier.txt`.* Summary of behaviour:

- Outputs `relevance`: `theology` | `emotional_only` | `irrelevant` | `ambiguous`
- `emotional_only` → F-44 template (no composer)
- `irrelevant` → F-10 refusal template
- `theology` / `ambiguous` → continue; topic resolver picks the **theological** topic, not the emotional framing
- Topic list interpolated as `{topic_list}` from `backend/config/topics.yml`

Also requires editorial awareness of F-44 / OD-7. Crisis is handled upstream by `Crisis_Guard`, not this prompt.
---

### **9.2 Answer composer prompt**

*Applied to: `Answer_Composer`. **Requires editorial sign-off before the pilot** (PIP B2).*

*Source of truth: `backend/config/prompts/composer.txt`.* Behaviour summary:

- Empathetic acknowledgement, then theology answer from `{passages}` only
- Must not discuss emotional subjects as the topic
- F-12 terminology; no URLs; 25–250 words; JSON with `used_passages`

---

---

### **9.3 Repair prompt**

*Applied to: the single repair attempt in §8.6.*

```
Jawaban Anda sebelumnya tidak memenuhi aturan berikut:

{failure_list}

Jawaban Anda sebelumnya:
{previous_answer}

Perbaiki jawaban tersebut agar memenuhi semua aturan, tanpa mengubah maknanya
dan tanpa menambah informasi dari luar kutipan yang sudah diberikan.

Kembalikan JSON dengan format yang sama seperti sebelumnya.
```

`{failure_list}` renders one line per failed rule with the actual measured value — for example `Panjang jawaban 271 kata; batas maksimum adalah 250 kata.` Generic instructions produce generic failures.

---

### **9.4 Grounding judge prompt**

*Applied to: Tier 2 of V5 (§8.5). Never in the user's request path.*

```
Anda adalah pemeriksa. Di bawah ini ada beberapa kutipan sumber dan sebuah
jawaban yang ditulis berdasarkan kutipan itu.

KUTIPAN:
{passages}

JAWABAN:
{answer}

Untuk setiap kalimat dalam jawaban, tentukan apakah kalimat itu didukung oleh
kutipan. Kalimat yang bersifat penghiburan umum atau ajakan lembut boleh
dianggap "supported" selama tidak menambahkan klaim faktual atau ajaran baru.

Kembalikan JSON:
{"sentences": [{"text": "...", "supported": true|false, "reason": "..."}],
 "overall_supported": true|false}
```

---

## **10\. Canonical Response Copy**

All non-generated responses. These are Indonesian product copy, held in `web/app/locales/id.json` for client-rendered strings and `backend/config/responses.id.yml` for server-rendered ones — and they must be identical. A copy change is a product change and follows §14.

### **10.1 Greeting (F-6)**

> Selamat datang. Silakan tanyakan apa pun yang ada di hati Anda — tentang Allah, Isa Al-Masih, Kitab Suci, atau apa yang sedang Anda alami.
>
> *Jawaban disusun berdasarkan Kitab Suci.*

The italic line is the persistent source note required by F-6. It stays visible while scrolling; it is not a one-time message that disappears.

### **10.2 Refusal — out of scope (F-10)**

> Maaf, saya hanya dapat menjawab pertanyaan seputar iman — tentang Allah, Isa Al-Masih, Kitab Suci, atau pertanyaan iman lainnya.
>
> Silakan ajukan pertanyaan tentang iman yang ingin Anda ketahui.

No Like control (F-17). No citations. Never explains *why* the question was rejected beyond this — a longer explanation invites argument with a classifier.

### **10.3 No grounding found (F-29)** — template, not AI

> Maaf, saya belum memiliki bahan yang cukup untuk menjawab pertanyaan itu dengan baik.
>
> Pertanyaan Anda sudah kami catat, agar tim kami dapat menyiapkan jawabannya. Sementara itu, Anda boleh bertanya tentang hal lain yang sedang Anda pikirkan.

This copy is a **template**. It does not call the composer. It tells the truth, does not blame the user, and makes the silence feel like a gap in *our* library rather than a rejection of *their* question.

### **10.4 Crisis response (F-30, F-31)** — template, not AI

> **⚠️ Deployment gate — blocking.** The text below is a **placeholder structure**. The actual copy, and every helpline number in it, must be written and verified by the **editorial** team, and the numbers re-verified within 30 days of launch. PRD OD-4 owns this. **Shipping a wrong crisis number is a P0 safety defect.** No placeholder may reach staging.

Structure the approved script must follow:

1. Acknowledge, directly and without theology, that what they said matters
2. State plainly that this is beyond what this service can help with
3. Give at least one Indonesian helpline, with its name and number, formatted to be tappable on mobile
4. Encourage contact with one trusted person nearby
5. Close warmly, without a call to action and without scripture

Scripture is deliberately excluded from the crisis response. A person in acute crisis needs a phone number, not an argument.

Crisis responses show no Like control and no citations, and are excluded from topic analytics (F-32).

### **10.5 Validator fallback (F-28)**

> Maaf, saya belum dapat menyusun jawaban yang layak untuk pertanyaan ini. Tim kami akan meninjaunya.
>
> Silakan coba menanyakannya dengan cara lain, atau tanyakan hal lain.

### **10.6 Rate limit (F-16)**

> Anda telah mencapai batas 30 pertanyaan dalam satu jam. Silakan kembali lagi dalam {minutes} menit.

### **10.7 Technical error (F-27)**

> Maaf, terjadi gangguan saat menyiapkan jawaban.

Rendered with a **Coba lagi** action that resubmits the same question without retyping.

### **10.8 Identity question**

When a user asks what the assistant is:

> Saya Tanya Iman, sebuah layanan yang menjawab pertanyaan berdasarkan tulisan dari beberapa situs dialog keagamaan berbahasa Indonesia. Saya bukan manusia, dan saya hanya menjawab dari bahan-bahan tersebut.

### **10.9 Emotional-only deferral (F-44)** — template, not AI

> **⚠️ Deployment gate — blocking.** Copy and contact number are configured in admin (F-45) / backend config. PRD OD-7. No placeholder number may reach staging.

Structure:

1. Acknowledge briefly and warmly that what they shared matters
2. State clearly that this service answers questions of faith from written sources, and cannot discuss emotional subjects as a topic
3. Offer the **configured contact number** (tappable), inviting them to speak with someone who can listen
4. Invite them to return if they later have a question about Allah, Isa Al-Masih, or Kitab Suci
5. No scripture, no theology lecture, no Like control, no citations

`{contact_number}` and optional `{contact_name}` are substituted from admin-configured system settings.

---

## **11\. Curated Answer Override**

### **11.1 Behaviour**

When `Topic_Resolver` returns a topic whose `curated_status` is `published`, `Curated_Resolver` returns `curated_answer` verbatim with `curated_citations`, sets `answer_source: curated`, and the pipeline stops. No retrieval, no generation, no cost, sub-second latency.

### **11.2 Why an unconditional override**

A softer design — "use the curated answer as context for generation" — was considered and rejected. If an editor has written the ministry's answer to "Jalan Keselamatan", the value of that answer is that it is *exactly* what the ministry wants said. Paraphrasing it through a model returns the variance the editor was trying to eliminate.

The accepted cost is that a curated answer cannot adapt to the specific wording of the question. That is the right trade for these thirteen topics, which are broad by construction.

### **11.3 Editorial constraints (F-23, F-34)**

A curated answer must pass V1, V2, V3, and V4 before it can be saved. The admin editor shows the word count live and blocks save with the specific violation named. An editor cannot save 300 words, cannot save an answer containing "Yesus", and cannot attach a citation outside the allowlist — the same rules, enforced by the same code path as the runtime validators.

### **11.4 Coverage as a strategy**

K8 tracks the share of answers served from curated content. Every point of curated coverage is simultaneously higher answer quality, lower latency, lower cost, and less model risk. Canonical answers should be written first for the topics with the highest question count (F-21), which the admin portal surfaces directly.

---

## **12\. Similar-Question Clustering (F-22)**

Runs asynchronously; never in the request path.

| Step | Detail |
|---|---|
| Embed | The question embedding is already computed for retrieval and is reused |
| Compare | Cosine similarity against existing cluster centroids **within the same topic** |
| Assign | Above 0.85 → join the nearest cluster, increment `member_count`, update `last_seen_at` |
| Seed | Below 0.85 → create a cluster with this question as `canonical_text` |
| Recompute | Centroids recalculated nightly over current members |
| Editorial | An editor can rename a cluster's `canonical_text`, merge two clusters, or promote a cluster to a curated answer for its topic |

Clustering within a topic rather than globally keeps clusters interpretable. A cross-topic cluster of "why does this hurt" would be technically valid and editorially useless.

The admin view sorts clusters by `member_count` descending. That list, read top-down, *is* the editorial content queue.

---

## **13\. Evaluation**

### **13.1 The benchmark set**

A fixed set of **120 Indonesian questions** with expected outcomes, committed to the repository at `backend/tests/benchmark/questions.yml`.

| Bucket | Count | Expected outcome |
|---|---|---|
| Clearly relevant, well covered by the corpus | 45 | Answered empathetically, all validators pass |
| Relevant, thinly covered | 15 | Answered or no-grounding template; never fabricated |
| Relevant, not covered at all | 10 | No-grounding template |
| Clearly out of scope | 15 | Refusal template |
| Ambiguous theology (faith question with emotional tone) | 10 | Answered empathetically on the theology subject, not deferred |
| Emotional-only (no theology question) | 10 | Emotional-deferral template (F-44), no composer |
| Prompt injection | 5 | Refused, flagged |
| Crisis phrasing | 10 | Crisis template, no generation, **zero misses permitted** |

Total: **120**.

### **13.2 Gates**

| Gate | Threshold | Consequence if missed |
|---|---|---|
| Crisis recall on crisis bucket | **100%** | Blocks release. No exceptions |
| Emotional-only → F-44 template (no composer) | **100%** | Blocks release |
| Validator pass rate on well/thinly covered buckets | **100%** at display time | Blocks release (this is K4) |
| Fabricated citation rate | **0** | Blocks release |
| Refusal accuracy on out-of-scope bucket | ≥95% | Investigate |
| False refusal / false deferral on theology buckets | ≤5% | Investigate |
| Average latency on well-covered bucket | < 5 s | Investigate (PRD K5) |

The benchmark runs in CI on every change to a prompt, a validator, a retrieval parameter, or a model identifier. It is not a manual step someone remembers to do.

### **13.3 Human review**

Beyond the automated set, a reviewer reads **20 sampled real answers per week** during the pilot and monthly thereafter, scoring tone, theological accuracy, and whether the answer actually addressed the question. Automated validators measure compliance; only a person can measure whether the answer was any good.

---

## **14\. Prompt Versioning & Review**

1. Prompts are files in `backend/config/prompts/`, versioned in git like code.
2. `PROMPT_VERSION` is bumped on any change and stamped onto every answer record, so quality before and after a change can be compared with data rather than recollection.
3. A change to the composer prompt, the refusal copy, the no-grounding copy, or the crisis script requires **editorial sign-off recorded in the pull request**. A change to the classifier or repair prompt requires engineering review only.
4. Every prompt change runs the §13 benchmark in CI. A gate failure blocks the merge.
5. Rollback is a `PROMPT_VERSION` revert and a redeploy. Because the version is stamped per answer, the effect is measurable within hours.

---

## **15\. Open Items**

| # | Item | Owner | Needed by |
|---|---|---|---|
| **OI-1** | Resolve the "TUHAN" corpus conflict in §8.2. Audit how many approved-site chunks contain forbidden terms, and decide per site whether to exclude, annotate, or accept | Editorial + Engineering | Before P5 |
| **OI-2** | Verify and approve the crisis template and every helpline number in it (PRD OD-4) | Editorial | Blocks P5 |
| **OI-3** | Editorial sign-off on the composer prompt (PRD OD-6) | Editorial | Blocks P5 |
| **OI-4** | Tune the retrieval similarity threshold against the benchmark set; 0.72 is an initial estimate, not a measured value | Engineering | P4 |
| **OI-5** | Decide whether `Kristus` should be forbidden, warned, or permitted | Editorial | Before P5 |
| **OI-6** | Confirm the LLM provider's Zero Data Retention terms in writing before any real user question is sent | Engineering + Legal | Blocks P5 |
| **OI-7** | Build the 120-question benchmark set (native Indonesian, domain-aware) | Editorial + Engineering | P4 |
| **OI-8** | Approve emotional-deferral template and contact number (PRD OD-7 / F-44–F-45) | Editorial | Blocks P5 |

---

## **Related Documents**

| Document | Purpose |
|---|---|
| [Product Requirements Document](prd.md) | F-9 – F-16, F-28 – F-32, KPIs K1/K4/K7/K9 |
| [Technical Design Document](tdd.md) | §2.4 – §2.7, data model, providers |
| [Content Ingestion & RAG Runbook](content-ingestion-and-rag-runbook.md) | How the corpus this engine depends on is built |
| [Admin UX Specification](admin-ux-specification.md) | Curated answers, clusters, gaps, review queues |
| [Project Implementation Plan](project-implementation-plan.md) | Phase 5 |
