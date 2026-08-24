# **Chat UX Specification**

**Project:** Tanya Iman \- Seeker Application

**Version:** Draft v1

**Date:** August 2026

---

## **1\. Purpose**

Define the seeker-facing experience: the welcome screen, the three sign-in paths, the conversation, and every response state the answer engine can produce.

This is a theology Q&A surface for Muslim seekers. There is no counselling chat and no “talk to a person” control inside the conversation. Every turn is handled by the AI **or** by a fixed template (refusal, crisis, emotional deferral with admin-configured contact number, no-grounding).

Answers that are composed must sound **empathetic** while staying on a faith/theology subject. Emotional-only questions never receive a composed answer.

This document complements:

- [Product Requirements Document](prd.md) — F-1 through F-8, F-17, F-24 through F-27
- [AI Answer Engine Specification](ai-answer-engine-specification.md) §10 — the canonical Indonesian copy this document specifies the *presentation* of
- [Frontend Framework Decision — Nuxt](frontend-framework-decision-nuxt.md) — embed and Android constraints

Where this document and the AI Spec disagree about wording, the AI Spec wins. Wording is a product decision under editorial review; layout is not.

---

## **2\. UX Principles**

1. **Ask first, decide later.** Nothing on the welcome screen should feel like a form. The fastest path to asking a question is one tap.
2. **Anonymity is a first-class path, not a downgrade.** "Lanjutkan sebagai Tamu" is presented with equal weight to the other two options, not as fine print at the bottom.
3. **Say less.** These users are often anxious. Every extra sentence of UI copy is a delay between them and their question.
4. **Never leave a message in limbo.** A question the user sent must always be visibly in one of three states: sending, answered, or failed with a retry.
5. **Slow is fine; silent is not.** Under five seconds of visible progress is the product target. Two seconds of nothing is not.
6. **The interface should not preach.** The product's persuasion happens in the answer, if at all. The chrome stays neutral.

---

## **3\. Information Architecture**

| Route | Screen | Auth |
|---|---|---|
| `/` | Welcome | None |
| `/masuk?channel=sms\|whatsapp` | Phone entry, then OTP entry | None |
| `/chat` | Conversation | Required (guest counts) |
| `/privasi` | Privacy Policy | None |

There is no navigation bar. A signed-in user sees only the conversation and a single overflow control (**⋮**) holding *Kebijakan Privasi* and *Keluar*.

The Privacy Policy link appears in the footer of every screen (**F-4**). In the conversation it lives in the overflow menu **and** as a small footer line beneath the input, because F-4 says every screen and the overflow menu is not visible without a tap.

---

## **4\. Visual Style**

### **4.1 Design tone**

Calm, warm, and unbranded in the religious sense. No imagery of people, no crosses, no crescents, no stock photography of hands. The visual identity is typography, whitespace, and one accent colour. A user should be able to have this app open on a bus without it announcing anything about them to the person beside them — this is a genuine safety consideration for parts of the audience, not an aesthetic preference.

### **4.2 Semantic tokens**

Components reference tokens, never hex values.

- `bg.base` — screen background
- `bg.surface` — cards, input
- `bubble.user` — the user's message
- `bubble.assistant` — the answer
- `text.primary`, `text.secondary`, `text.onAccent`
- `accent.primary` — send, primary buttons, links
- `border.subtle`
- `status.warning` — rate limit
- `status.info` — no-grounding and refusal states
- `status.care` — crisis response; visually distinct from `status.danger`, which reads as an error rather than as care

### **4.3 Typography**

Three levels only:

| Level | Use |
|---|---|
| Title | Welcome heading |
| Body | Messages, answers, buttons |
| Meta | The source note, timestamps, citation labels |

Body must remain comfortable at length. Indonesian runs roughly 10–15% longer than English for the same content, and a 250-word answer is a genuinely long block of text on a 360px screen. Line height 1.6 minimum, measure capped at ~65 characters.

### **4.4 Spacing and layout**

- 8px spacing scale
- Design baseline 360px; must hold from 320px
- Maximum content width 640px on larger screens, centred — a full-width conversation on a desktop monitor is unreadable
- Input is pinned to the bottom with safe-area padding; the transcript scrolls beneath it

---

## **5\. Welcome Screen (F-1)**

```
┌──────────────────────────────┐
│                              │
│         Tanya Iman           │
│                              │
│  Tanyakan apa pun yang ada   │
│  di hati Anda.               │
│                              │
│  ┌────────────────────────┐  │
│  │  Masuk dengan SMS      │  │
│  └────────────────────────┘  │
│  ┌────────────────────────┐  │
│  │  Masuk dengan WhatsApp │  │
│  └────────────────────────┘  │
│  ┌────────────────────────┐  │
│  │  Lanjutkan sebagai Tamu│  │
│  └────────────────────────┘  │
│                              │
│      Kebijakan Privasi       │
└──────────────────────────────┘
```

Requirements:

- All three options are full-width buttons of equal size. The guest option may be visually secondary in *weight* (outline rather than filled) but never smaller, lower-contrast, or below the fold.
- No explanation of why a user might choose one over another. If it needs explaining, the labels are wrong.
- The Privacy Policy link is a footer link, tappable at 44px minimum height even though the text is small (**F-4**).

---

## **6\. Sign-in Flows (F-2, F-24)**

### **6.1 Phone entry**

Single field, `+62` prefilled and visible, numeric keypad, inline validation only after blur. One primary button: **Kirim kode**.

A back affordance returns to the welcome screen without losing anything, because nothing has been collected yet.

### **6.2 OTP entry**

- Six single-character boxes with auto-advance and paste support
- Auto-submit on the sixth character; no separate confirm tap
- Android auto-fills from SMS retrieval where available (Phase 7, Task 7.3)
- A resend link, disabled with a visible countdown until it becomes available
- After 5 wrong attempts (**F-24**): the field locks and shows the cooldown message with the remaining time. The user can go back and change the number.
- After 3 code requests in an hour (**F-24**): resend is disabled with the cooldown message.

Error copy names the actual problem — *Kode salah. Sisa 3 percobaan.* — rather than a generic failure. A vague error at this step is where users leave.

### **6.3 Guest conversion (F-25)**

Offered, never demanded. A guest never sees a prompt to sign in mid-conversation. Sign-in is available from the overflow menu as *Masuk dengan nomor*. On success the user stays exactly where they were, with the transcript intact, and sees a single unobtrusive confirmation line.

---

## **7\. Chat Screen**

### **7.1 Anatomy**

```
┌──────────────────────────────┐
│  Tanya Iman              ⋮   │  header
├──────────────────────────────┤
│  Jawaban disusun berdasarkan │  source note — persistent (F-6)
│  Kitab Suci.                 │
├──────────────────────────────┤
│                              │
│  [greeting]                  │  transcript, scrolls
│                    [question]│
│  [answer]                    │
│  📄 Judul artikel            │  citations
│  ♡                           │  like (F-17)
│                              │
├──────────────────────────────┤
│  [ Tulis pertanyaan… ]  ➤    │  input
│  Kebijakan Privasi           │  footer (F-4)
└──────────────────────────────┘
```

### **7.2 The source note (F-6)**

Persistent, directly beneath the header, in `Meta` type. It does not scroll away and it is not a dismissible message. F-6 requires that the user knows what the answers are based on — a note that disappears after the first scroll does not satisfy that.

### **7.3 The greeting (F-6)**

Rendered as the first assistant message on session start, using AI Spec §10.1. It is not a modal, not an overlay, and carries no Like control.

### **7.4 Input**

- Auto-growing textarea, 1 to 5 lines, then internal scroll
- Send is disabled while a request is in flight; the textarea stays editable so the user can compose the next question (**F-26**)
- Enter sends on desktop; on mobile Enter inserts a newline and send is tap-only — the opposite convention loses people mid-sentence
- Placeholder: *Tulis pertanyaan Anda…*
- Character counter appears only past 800 of the 1,000 limit

### **7.5 Multi-turn behaviour (F-8)**

Every question and answer appends to one continuous transcript. The view auto-scrolls to the newest message **only when the user is already at the bottom**. If they have scrolled up to reread an earlier answer, a *Pesan baru* pill appears instead of yanking them down.

---

## **8\. Response States**

Every state the engine can return, and how it renders. The frontend selects on `answer_source` and `likeable` from the API — it never reimplements a business rule (see TDD §4.1).

| `answer_source` | Rendering | Like | Citations |
|---|---|---|---|
| `generated` | Standard answer bubble | Yes | 1–2 |
| `curated` | Identical to `generated` — the user is never told which one they got | Yes | 1–2 |
| `refusal` | `status.info` bubble, no icon | No | None |
| `no_grounding` | `status.info` bubble | No | None |
| `crisis` | `status.care` bubble, visually distinct, helpline numbers as `tel:` links | No | None |
| `error` | `status.warning` bubble with a **Coba lagi** action | No | None |
| *rate limited* (HTTP 429) | `status.warning` bubble with a live countdown | No | None |

### **8.1 Pending state (F-26)**

An assistant bubble containing a three-dot animation appears immediately on send. It is replaced in place by the answer. It never disappears without being replaced by *something* — an answer, an error, or a refusal.

Beyond 8 seconds, a `Meta` line appears below it: *Masih menyiapkan jawaban…*. This is honest and it stops the user from resending.

### **8.2 Error and retry (F-27)**

The failed question stays in the transcript in its user bubble, dimmed. **Coba lagi** resubmits the identical text. The user never retypes.

### **8.3 Crisis state (F-30)**

Deliberately different from every other state:

- `status.care` treatment, wider padding, no bubble tail — it reads as a card, not as a reply
- Helpline numbers are `tel:` links with a minimum 44px tap target
- No Like, no citations, no follow-up prompt, no scripture
- The input remains fully usable. The conversation is not locked; a person who wants to keep talking must be able to.

### **8.4 Rate limit state (F-16)**

A `status.warning` bubble with a countdown that ticks down live and resolves to a normal input state when it reaches zero, without a reload.

---

## **9\. Citations (F-14)**

Rendered beneath the answer, above the Like control:

```
📄  Kasih Allah yang Tidak Berkesudahan
    isadanislam.org
```

- One or two, never more
- The article title is the link text; the domain appears in `Meta` type beneath it, so the user can see where they are being sent before they tap
- Opens in a new tab on web; in the **external browser** on Android, never inside the WebView — a user who taps a link and cannot get back has lost their conversation
- Never a bare URL

---

## **10\. Like (F-17, F-33)**

- A single heart control beneath the citations, `♡` → `♥` on press
- Optimistic: fills immediately, reverts with a quiet toast if the request fails
- Tapping again removes it (**F-33**)
- No count is shown to the user. Like counts are an editorial signal, not social proof, and displaying them would make an unpopular-looking answer feel less true
- Rendered only when the API says `likeable: true`

---

## **11\. Embed Mode (F-38)**

When `?embed=1` is present:

- The app header, the outer page background, and the app title are suppressed. The source note, transcript, input, and privacy link all remain — **F-4 and F-6 apply in the widget exactly as they do in the app.**
- The root fills 100% of the iframe width and reports its height over `postMessage` on every content change
- Layout must hold at 320px, since host theme content columns vary across five sites
- Links open in the top-level window (`target="_top"`) so a citation does not open inside a 620px-tall iframe
- If phone auth cannot complete inside the iframe (Phase 7, Task 7.2), the widget shows Guest only plus a *Buka di tab baru* link — it never shows a sign-in button that silently fails

---

## **12\. Android Specifics**

| Concern | Behaviour |
|---|---|
| Safe areas | Root layout pads with `env(safe-area-inset-*)`; the input never sits under the gesture bar |
| Back button | Pops in-app navigation first. From mid-conversation, one confirm before exit |
| Keyboard | The input stays above the keyboard; the transcript resizes rather than being overlapped |
| Offline | A clear Indonesian offline state, distinct from a server error, with automatic retry on reconnect |
| Links | Open in the external browser (**§9**) |
| Rotation | Transcript and pending state survive rotation |

---

## **13\. Accessibility**

- WCAG 2.1 AA contrast on every token pair, including `status.care` and `status.info`
- Full keyboard operation on web: tab reaches input, send, every citation, and every Like
- The transcript is an ARIA live region with `polite`, so a screen reader announces arriving answers without interrupting
- Every state is distinguishable without colour — the refusal, no-grounding, and crisis states differ in copy and layout, not only in tint
- Text scales to 200% without clipping or loss of function
- Tap targets 44×44px minimum, including the footer privacy link
- The pending animation respects `prefers-reduced-motion`

---

## **14\. Copy Inventory**

Every user-facing string lives in `web/app/locales/id.json`. Nothing is hardcoded in a component. Strings that are also rendered server-side must be byte-identical to `backend/config/responses.id.yml`, and a test asserts that.

| Key | Source |
|---|---|
| `welcome.*` | This document §5 |
| `auth.*` | This document §6 |
| `chat.greeting`, `chat.source_note` | AI Spec §10.1 |
| `response.refusal` | AI Spec §10.2 |
| `response.no_grounding` | AI Spec §10.3 |
| `response.crisis` | AI Spec §10.4 — **editorially approved, never edited by an engineer** |
| `response.fallback` | AI Spec §10.5 |
| `response.rate_limit` | AI Spec §10.6 |
| `response.error` | AI Spec §10.7 |
| `response.identity` | AI Spec §10.8 |

---

## **15\. UX Acceptance Checklist**

- [ ] All three sign-in options appear at equal size on the welcome screen (F-1)
- [ ] The Privacy Policy link is reachable from every screen, including inside the widget (F-4)
- [ ] The source note is persistent and does not scroll away (F-6)
- [ ] A sent question is always visibly sending, answered, or failed-with-retry
- [ ] Send is disabled while pending; the input stays editable (F-26)
- [ ] Retry resubmits without retyping (F-27)
- [ ] Refusal, no-grounding, and crisis states are distinguishable without colour
- [ ] The crisis state shows tappable helpline links and no scripture (F-30)
- [ ] Like appears only when the API says `likeable: true` (F-17)
- [ ] Like is reversible (F-33)
- [ ] Citations show the article title with the domain beneath, and open externally
- [ ] Layout holds at 320px in both app and embed mode
- [ ] Guest conversion preserves the visible transcript (F-25)
- [ ] Text at 200% does not clip
- [ ] The transcript announces new answers to a screen reader
- [ ] No user-facing string is hardcoded in a component

---

## **16\. Out of Scope (v1.0)**

- Conversation history across devices or sessions
- Sharing an answer to another app
- Copying an answer to the clipboard *(worth reconsidering — it is cheap and users will want it)*
- Voice input or audio playback
- Dark mode *(the token layer makes this a later addition rather than a rewrite)*
- In-app notifications
- Suggested-question chips on the empty state *(deliberately excluded — they steer people toward questions we have answers for rather than the one they came with)*
