# Pilot Plan — Tanya Iman (Staging)

**Duration:** 2 weeks · **Environment:** GCP staging only · **Language:** all sessions in Indonesian

---

## Objectives

1. Validate that real Indonesian users can ask a genuine question and receive an answer they find trustworthy.
2. Validate all three sign-in paths on real devices and real networks.
3. Validate answer quality against the content rules — not that the validators pass, but that the answers are *good*.
4. Validate the editorial workflow: can an editor find demand and publish a curated answer without help?
5. Validate the widget on a real WordPress page and the app on a real Android device.
6. Collect structured UX and answer-quality feedback that can be acted on.

---

## Participants (client fills in)

| Role | Count | Names / IDs |
|---|---|---|
| Seekers — Android app | 6–10 | |
| Seekers — WordPress widget | 4–6 | |
| Seekers — guest only, no sign-in | 3–5 | |
| Editorial admins | 2–3 | |
| Editorial reviewer (answer quality) | 1 | |

Recruit seekers who reflect the actual audience described in PRD §4.1 — predominantly from a Muslim background, mobile-first, with genuine questions. A pilot run entirely by ministry staff asking questions they already know the answer to measures nothing.

---

## Privacy and consent

- Testers read and accept a ministry-approved consent notice before their first message. It must state that questions are recorded and reviewed by the team.
- Use staging phone numbers where possible. Where a real number is used, it is deleted from staging at the end of the pilot.
- Reports use the internal `question_id` and `seeker_id`. **No phone number, and no verbatim personal detail, appears in any pilot document.**
- No crisis-path testing with real distress. Only the approved test phrase, and only by a team member who knows what will happen.

---

## Scenarios

| ID | Actor | Steps | Success |
|---|---|---|---|
| **P1** | Seeker | Continue as guest; ask one genuine question | Answer within 9s, 25–250 words, 1–2 working links |
| **P2** | Seeker | Ask three follow-up questions in the same session | Follow-ups understood in context; no repetition |
| **P3** | Seeker | Sign in with SMS on Android | OTP arrives; auto-fill works; chat opens |
| **P4** | Seeker | Sign in with WhatsApp | OTP arrives on WhatsApp; chat opens |
| **P5** | Seeker | Start as guest, ask two questions, then sign in | Transcript survives conversion (F-25) |
| **P6** | Seeker | Ask something clearly off-topic | Polite refusal in under a second; no Like control |
| **P7** | Seeker | Ask a spiritual question the corpus does not cover | No-grounding response; question appears in admin Content Gaps |
| **P8** | Seeker | Like an answer, then unlike it | Like state toggles; count updates in admin |
| **P9** | Seeker | Ask via the WordPress widget on a real page | Same answer as the app; widget resizes; links open in the top window |
| **P10** | Seeker | Lose connection mid-question, then reconnect | Clear offline state; retry works without retyping |
| **P11** | Team | Send the approved crisis test phrase | Scripted response with tappable helpline; no generation; excluded from topic counts |
| **P11b** | Team | Send an emotional-only message (no theology question) | Emotional-deferral **template** with admin contact number; no generation; no Like |
| **P12** | Team | Send 31 messages in one hour | 31st shows the countdown message |
| **P13** | Admin | Filter last 7 days, find the top topic, read 10 questions | Completed unaided in under 10 minutes |
| **P14** | Admin | Write and publish a curated answer for that topic | Live validation guides them; publish succeeds |
| **P15** | Admin | Ask that topic's question in the app | The exact curated text is returned |
| **P16** | Admin | Review the Content Gaps and Similar Questions views | Can name the top three unwritten subjects |
| **P17** | Admin | Export the filtered question list as CSV | Downloads; contains no phone number |
| **P18** | Editorial reviewer | Read 20 sampled answers | Scores recorded on the AI Answer Quality Report template |

---

## Schedule

| Day | Activity |
|---|---|
| 1 | Kickoff; distribute credentials, consent notices, and the Android internal-test link |
| 2–5 | Seeker scenarios P1–P8 on Android |
| 4–6 | Seeker scenarios P9–P10 on the WordPress widget |
| 6 | Team scenarios P11–P12 |
| 7–8 | Admin scenarios P13–P17 |
| 9 | Editorial answer review P18 |
| 10–12 | Buffer, defect fixes, retests |
| 13 | Compile reports using the templates in this folder |
| 14 | Go / no-go review |

---

## Defect severity

| Level | Definition | Response |
|---|---|---|
| **P0** | Safety or data. A crisis message not routed; a phone number exposed; an answer citing an unapproved domain | Halt the pilot. Fix before resuming |
| **P1** | A scenario cannot be completed at all | Fix within the pilot |
| **P2** | A scenario completes but the experience is wrong | Fix before launch |
| **P3** | Cosmetic or nice-to-have | Backlog |

---

## Exit criteria

- **Zero open P0 defects.** No exceptions, no waivers.
- ≥90% of P1–P17 passed, with every failure documented at a severity level.
- **Crisis routing 100% on P11.** A single miss blocks launch.
- Validator pass rate at display time is 100% across every answer produced during the pilot (K4).
- Zero answers citing a domain outside the approved allowlist.
- P18 editorial / theological review completed, with a written statement on whether the answers are acceptable to publish. **This is a judgment, not a metric, and it is the one that matters most.**
- Answer latency average under 5 seconds across the pilot (PRD K5).
- The admin scenarios P13–P16 were completed by an editor without engineering assistance.
- A go / no-go recommendation recorded in the session log summary.

---

## Reporting

| Template | Filled in by | Frequency |
|---|---|---|
| [Pilot Session Log Template](pilot-session-log-template.md) | Facilitator | Per session |
| [UX Feedback Report Template](ux-feedback-report-template.md) | Facilitator | Per participant |
| [AI Answer Quality Report Template](ai-answer-quality-report-template.md) | Editorial reviewer | Per batch of 20 answers |
