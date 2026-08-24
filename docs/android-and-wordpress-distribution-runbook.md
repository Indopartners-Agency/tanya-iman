# **Android & WordPress Distribution Runbook**

**Project:** Tanya Iman

**Version:** 1.0

**Date:** August 2026

---

Operational guide for the two distribution channels required by **F-38** and **F-39**. Both ship the same Nuxt static build; the architecture behind that is in [Frontend Framework Decision — Nuxt](frontend-framework-decision-nuxt.md) §5 and §6.

---

# **Part A — WordPress Widget**

## **A1. What the WordPress team receives**

One snippet, pasted into a page, a post, or a Custom HTML block:

```html
<div id="tanya-iman-widget" data-height="620"></div>
<script src="https://app.tanyaiman.id/embed.js" async></script>
```

That is the entire integration. No plugin, no theme edit, no PHP, no build step on the host site. Attributes:

| Attribute | Default | Purpose |
|---|---|---|
| `data-height` | `620` | Initial height in pixels before the first `postMessage` resize |
| `data-max-height` | `900` | Cap for auto-resize, so a long conversation does not push the page footer out of reach |
| `data-topic` | none | Optional. Pre-fills the input with a suggested question for the article's subject |

## **A2. Backend prerequisites**

Before the snippet goes on any site:

1. Every host domain is listed in `FRAME_ANCESTORS`, and the backend redeployed.
2. Every host domain is listed in `CORS_ORIGINS`.
3. The five host domains are the **only** entries. An unlisted site embedding the snippet gets a blocked frame, which is the intended behaviour.

## **A3. Rollout**

Per PRD OD-5, one site first, then the rest after seven days of clean metrics.

| Step | Action | Verify |
|---|---|---|
| 1 | Embed on **one** page of the first host site | Widget renders; a question returns an answer |
| 2 | Confirm attribution | Admin question list shows `widget` channel with the correct host on hover |
| 3 | Test the auth behaviour decided in PIP Task 7.2 | Either sign-in works in-frame, or Guest-only is shown with a working *Buka di tab baru* link. No dead button |
| 4 | Watch for 7 days | No CSP errors in the host page console; no spike in error-state responses |
| 5 | Roll out to the remaining four sites | Repeat steps 1–3 per site |

## **A4. Per-site QA checklist**

**Site:** _________________  **Date:** _________________  **Tester:** _________________

| # | Case | Pass | Notes |
|---|---|---|---|
| W1 | Widget renders inside the theme's content column | ☐ | |
| W2 | Layout holds at 320px viewport width | ☐ | |
| W3 | Iframe grows as the conversation grows, up to `data-max-height` | ☐ | |
| W4 | No inner scrollbar until the height cap is reached | ☐ | |
| W5 | Source note is visible (F-6) | ☐ | |
| W6 | Privacy Policy link is reachable inside the widget (F-4) | ☐ | |
| W7 | A guest question returns an answer with working citations | ☐ | |
| W8 | Citation links open in the top-level window, not inside the iframe | ☐ | |
| W9 | Auth path behaves as decided — works, or Guest-only with a new-tab link | ☐ | |
| W10 | No console errors on the host page | ☐ | |
| W11 | Host theme CSS does not leak into the widget, and vice versa | ☐ | |
| W12 | Question appears in admin with the correct `embed_origin` | ☐ | |

**Sign-off:** Engineering _________________  Site owner _________________

## **A5. Widget troubleshooting**

| Symptom | Cause | Fix |
|---|---|---|
| Blank iframe, console shows a frame-ancestors violation | Host domain missing from `FRAME_ANCESTORS` | Add it, redeploy the backend |
| Widget renders, every request fails | Host origin missing from `CORS_ORIGINS` | Add it, redeploy |
| Iframe never resizes | `postMessage` blocked, or `embed.js` served from a different origin than the iframe | Confirm both come from the same deployed app origin |
| Widget is 100px tall | Host theme sets `iframe { height: auto }` | The embed script sets height inline; if a theme overrides it, raise `data-height` and report the theme |
| Sign-in silently fails | reCAPTCHA in a third-party frame | This is the known case in PIP Task 7.2. Fall back to Guest-only; do not leave a button that does nothing |

---

# **Part B — Android (Google Play)**

## **B1. Build**

```bash
cd web/app
export NUXT_PUBLIC_API_BASE=https://api.tanyaiman.id
npm ci && npm run generate

npx cap sync android
cd ../../android
./gradlew bundleRelease          # → app/build/outputs/bundle/release/app-release.aab
```

Signing key lives in the team password manager, never in the repository. Losing it means never being able to update the app under the same listing, so it is backed up in two places and the Play App Signing enrolment is completed at first upload.

**CI asserts** that the baked `NUXT_PUBLIC_API_BASE` is an HTTPS production URL before a release build is accepted. A release AAB pointing at staging is not a theoretical mistake.

## **B2. Play listing (risk R3)**

Google Play's policies on religious content are not prohibitive, but they are specific about deception, targeting, and sensitive-content disclosure. The listing must be unambiguous about what the app is.

| Field | Content |
|---|---|
| Title | Tanya Iman |
| Short description | Jawaban atas pertanyaan iman, dalam bahasa Indonesia |
| Full description | States plainly: this is a question-and-answer service; answers are drawn from a specific set of Indonesian religious-dialogue websites; the sources are named; the app does not represent any government or official body; it is not a counselling service |
| Category | Books & Reference *(not Lifestyle — the app is a reading and Q&A tool)* |
| Content rating | Complete the questionnaire honestly, including the religious-content and user-generated-content questions |
| Target audience | 18+ |
| Data safety | Must match reality: phone number collected **only** for SMS/WhatsApp sign-in, not shared, not used for advertising, encrypted in transit and at rest; guest mode collects no personal data; question text collected and retained per the stated policy |
| Privacy policy URL | Must be live before submission and must actually describe what the app does (PIP B9) |

**Do not** claim in the listing that the app provides counselling, mental-health support, or spiritual authority. Beyond being untrue, it invites a content-rating problem the app does not need.

**Budget one rejection-and-resubmit cycle.** Religious apps from first-time publishers are frequently reviewed by a human. Plan the launch date accordingly rather than discovering this at the deadline.

## **B3. Release tracks**

| Track | Purpose | Audience |
|---|---|---|
| Internal testing | Every build during Phase 7 | The team |
| Closed testing | The pilot (PIP Phase 8) | Pilot testers |
| Production, staged | Launch | 10% → 50% → 100% over one week |

Staged rollout is not optional. It is the only mechanism by which a bad Android release can be stopped before it reaches everyone.

## **B4. Device QA matrix**

Run before every production track promotion.

| # | Case | Pass condition |
|---|---|---|
| A1 | Cold start on Android 10 and Android 14 | Welcome screen renders; safe areas correct on both notch and gesture-bar devices |
| A2 | SMS sign-in | Code auto-fills via Play Services retrieval; sign-in completes |
| A3 | WhatsApp sign-in | Completes; resulting identity matches the same number signed in on web |
| A4 | Guest → SMS conversion | Transcript survives (F-25) |
| A5 | Three questions in sequence | Three answers; transcript scrolls correctly |
| A6 | Airplane mode mid-question | Clear Indonesian offline state, distinct from a server error; recovers on reconnect |
| A7 | Back button mid-conversation | Confirm prompt; does not exit silently |
| A8 | Citation tap | Opens in the external browser; returning to the app preserves the transcript |
| A9 | Rotate during a pending answer | Pending state and transcript survive |
| A10 | Keyboard open with a long transcript | Input stays above the keyboard; transcript is not overlapped |
| A11 | Font size at 200% in system settings | No clipping; all controls reachable |
| A12 | Crisis test phrase (approved test string only) | Scripted response; helpline numbers are tappable `tel:` links |
| A13 | Answer parity | The same question returns the same answer as web and widget (F-40) |

**Tester:** _________________  **Build:** _________________  **Date:** _________________

## **B5. Android troubleshooting**

| Symptom | Cause | Fix |
|---|---|---|
| White screen on launch | `webDir` points at a stale or missing build | `npm run generate` then `npx cap sync android` |
| Every request fails | Baked API base is wrong, or is HTTP | Rebuild with the correct HTTPS value; the CI assertion should have caught it |
| SMS code never auto-fills | Native auth plugin not wired, or the app hash is not registered | Confirm `@capacitor-firebase/authentication` is installed and synced |
| Citation opens inside the WebView and traps the user | Link handling not configured for external browser | Configure the app's URL open behaviour; this is A8 and is a release blocker |
| Input hidden behind the keyboard | Missing `windowSoftInputMode` adjustment | Set resize behaviour in the Android manifest |
| Play rejects the submission | Usually the data-safety declaration not matching observed behaviour | Re-read §B2, correct the declaration, resubmit. Do not argue; correct |

## **B6. Post-release monitoring**

For the first two weeks after a production promotion:

- **Play Console vitals** — ANR and crash rate. Either above threshold halts the staged rollout
- **Channel split in admin** — `android` question volume growing as installs grow. Flat volume with rising installs means the app installs and then fails
- **Reviews** — read them. A one-star review saying "tidak bisa masuk" is a bug report with a wider sample than any test matrix

---

## **Related Documents**

| Document | Purpose |
|---|---|
| [Frontend Framework Decision — Nuxt](frontend-framework-decision-nuxt.md) | §5 widget architecture, §6 Capacitor constraints |
| [Chat UX Specification](chat-ux-specification.md) | §11 embed mode, §12 Android behaviour |
| [Deployment Guide](deployment-guide.md) | Build-time environment variables, CORS, frame-ancestors |
| [Project Implementation Plan](project-implementation-plan.md) | Phase 7, Phase 9 |
