# **Frontend Framework Decision — Nuxt 3 (SPA)**

**Project:** Tanya Iman — Indonesian Theology Q&A (Nuxt frontend)

**Status:** **Decided** — August 2026

**Decision:** **Nuxt 3 (Vue 3) + Tailwind CSS in SPA mode (`ssr: false`)**, built to static files with `nuxt generate`

**Applies to:** the seeker application (`web/app/`) and the editorial admin portal (`web/admin/`)

> The Aug 2026 product brief assumed React. **This decision uses Nuxt 3 instead** and is confirmed as product direction. The requirement it was written to satisfy — *one codebase that can be served as a WordPress widget or wrapped as an Android app* — is unchanged and is met by Nuxt.

---

## **1\. Decision**

Both web applications are built with **Nuxt 3 with server-side rendering disabled**:

```ts
// nuxt.config.ts
export default defineNuxtConfig({
  ssr: false,
  nitro: { preset: 'static' },
})
```

`npm run generate` produces a directory of static assets in `.output/public`. That single artefact is what we host, what we embed, and what we package into the Android binary. **No Node process runs in production.**

---

## **2\. Why SPA rather than SSR**

The standard objection to Nuxt is that SSR needs a Node server alive around the clock, which is real infrastructure cost and a real operational surface. That objection is entirely avoided by turning SSR off — and in this product, SSR would have bought us nothing to begin with.

| Consideration | Consequence for Tanya Iman |
|---|---|
| **The app has no indexable content** | Every screen is either a sign-in gate or a conversation the user just created. There is no HTML worth pre-rendering for a crawler. The SEO argument for SSR does not apply. |
| **SEO already lives elsewhere** | The five source sites are the SEO surface, and they already rank. Tanya Iman is the *thing embedded on them*, not a competitor for their traffic. |
| **Capacitor cannot run SSR** | An Android WebView loads files from the APK. It has no origin server to render against. A static build is not a preference here — it is the only shape that can be packaged. |
| **The backend is separate** | Answer generation, auth, and retrieval all live behind the FastAPI service. An SSR layer would be a proxy with no logic of its own. |
| **Server cost** | `nuxt generate` output sits on Firebase Hosting's CDN. Zero compute, zero cold starts, zero scaling configuration for the frontend. |

The result is the server footprint of a plain Vite SPA, while keeping Nuxt's developer experience: file-based routing, auto-imports, layouts, Pinia, and a first-class module ecosystem.

---

## **3\. One codebase, three delivery targets**

This is the requirement that actually constrained the choice, and it is worth being explicit about how each target is produced from the same source.

```
web/app/  (Nuxt 3, ssr: false)
   │
   └── npm run generate  →  .output/public/   ← one static artefact
                                │
        ┌───────────────────────┼───────────────────────┐
        │                       │                       │
   Firebase Hosting        <iframe> embed          Capacitor sync
   (standalone web)        (WordPress widget)      (Android APK/AAB)
```

| Target | How it is produced | Notes |
|---|---|---|
| **Standalone web** | Deploy `.output/public` to Firebase Hosting | The canonical URL; also the source the widget iframe points at |
| **WordPress widget** | Same deployed build, loaded in an iframe by a small embed script | See §5 |
| **Android app** | `npx cap sync android` copies `.output/public` into the Android project, then Gradle builds the AAB | See §6 |

There is no build flag that changes product behaviour between targets. The only runtime difference is a `platform` hint sent with API calls, used for analytics, not for logic — this is required by **F-40**.

---

## **4\. Application structure**

Two separate Nuxt applications, not one app with role-based routing. They have different users, different auth systems, different deployment cadence, and different risk profiles; keeping them separate means an admin bundle can never be shipped to a seeker's phone.

| App | Path | Users | Auth | Ships to |
|---|---|---|---|---|
| **Seeker app** | `web/app/` | Public, Indonesian, mobile-first | Firebase Auth (phone / anonymous) | Web, WordPress widget, Android |
| **Admin portal** | `web/admin/` | Editorial staff | Separate admin JWT (see TDD §6) | Web only, desktop-first |

Shared UI primitives and the API client live in `web/shared/` and are consumed by both via a workspace dependency. Shared code must not import anything from either app.

---

## **5\. WordPress widget**

The widget is an **iframe**, not an inline mount. Inline mounting would put our CSS, our Vue runtime, and the host theme's stylesheet in one cascade across five WordPress sites we do not control — a support burden with no upside.

**Embed snippet** (what the WordPress team pastes into a page or a block):

```html
<div id="tanya-iman-widget" data-height="620"></div>
<script src="https://app.tanyaiman.id/embed.js" async></script>
```

`embed.js` is a small dependency-free script emitted by the build. It:

1. Creates an iframe pointing at the deployed app with `?embed=1`.
2. Sets the iframe to 100% of the host container width, so it inherits the theme's content column.
3. Listens for a `postMessage` height event from the app and resizes the iframe, so the conversation grows without an inner scrollbar.
4. Passes the host page URL as a referrer hint, so admin analytics can attribute questions to the site they came from.

**Constraints this places on the app:**

- When `?embed=1` is present the app suppresses its own outer chrome (full-page header, background) and renders in a container that fits an arbitrary width down to 320px.
- The backend must send `Content-Security-Policy: frame-ancestors` listing exactly the five approved host domains. Any other site embedding us gets a blocked frame.
- Firebase Auth's phone flow uses a reCAPTCHA challenge that must be verified to work inside a third-party iframe. If it does not, the widget falls back to Guest-only and offers a "buka di tab baru" link for users who want to sign in. This must be tested before the widget ships — see the Implementation Plan.

---

## **6\. Android via Capacitor**

Capacitor wraps the static build in an Android WebView. The reasons to prefer it over React Native or a native rewrite are the same reasons the product wanted one codebase: the app is a chat interface over an HTTP API, with no requirement for native rendering performance, background services, or platform-specific UI.

**Build path:**

```bash
cd web/app
npm run generate                  # → .output/public
npx cap sync android              # copies build + plugins into android/
cd android && ./gradlew bundleRelease
```

**Things the WebView forces us to get right:**

- **Phone authentication.** Firebase's web SDK phone flow depends on reCAPTCHA and a browser redirect, which is unreliable inside a WebView. Android uses the `@capacitor-firebase/authentication` native plugin instead, which goes through Google Play Services and supports SMS auto-retrieval. The app calls one auth abstraction; the platform decides which implementation backs it.
- **Safe areas.** Status bar and gesture-navigation insets are handled with CSS environment variables, applied in the root layout rather than per-screen.
- **Back button.** The hardware back button must pop the app's own navigation before exiting, and must not exit from mid-conversation without a confirm.
- **No mixed content.** Every request from the WebView must be HTTPS; the API base URL is baked at build time and validated in CI.
- **Play policy.** The listing must describe the app's purpose and audience clearly, per risk R3 in the PRD. Distribution details are in the Android & WordPress Distribution Runbook.

---

## **7\. Alternatives considered**

| Option | Why not |
|---|---|
| **Nuxt with SSR** | Requires a Node runtime in production for no benefit — the app has nothing to pre-render — and cannot be packaged by Capacitor at all |
| **React + Vite** | A perfectly valid choice and what the Aug 2026 product brief originally assumed. Rejected because the team's other active project standardised on Nuxt; two frameworks across one team is a maintenance tax with no product return. Nothing about React was disqualifying |
| **React Native / Expo** | Gives a genuinely native Android app but cannot produce a WordPress-embeddable widget. Would mean two codebases for two channels — the exact outcome the product brief rules out |
| **Native Android (Kotlin)** | Same problem as React Native, plus no web target at all, plus a skill set the team does not have |
| **PWA only, no Play Store** | Drops a required distribution channel (F-39). Indonesian users overwhelmingly discover apps through the Play Store; "add to home screen" is not a substitute |
| **Nuxt with `@nuxtjs/tailwindcss`** | Not an architecture decision but worth recording: this module emits a `postcss.mjs` loaded outside ESM context and fails with `Cannot use 'import.meta' outside a module`. Tailwind is wired through Nuxt's built-in PostCSS support instead |

---

## **8\. Accepted consequences**

| Consequence | Assessment |
|---|---|
| Prototype UI is React | The Phase 1 prototype stays a **reference for interaction and API shape**, not a starting codebase. Screens are rebuilt in Vue |
| Smaller ecosystem than React | Immaterial. The app needs routing, state, a form or two, and an HTTP client. Nuxt covers all of it in core |
| Bundle size | Vue's runtime (~34 KB) is marginally smaller than React's (~45 KB). Neither is the binding constraint; the answer-latency budget is |
| Vue hiring pool in-market | Smaller than React's, and a real consideration for handover. Mitigated by keeping the app deliberately plain — no exotic patterns, no custom reactivity tricks |
| Environment variables are baked at build time | `NUXT_PUBLIC_API_BASE` must be set before `npm run generate`, and a rebuild is required to change it. This is the standard static-site trade-off; it is called out in the Deployment Guide so nobody is surprised by a staging build pointing at production |

---

## **9\. Implementation notes**

- **Tailwind through Nuxt's built-in PostCSS**, not `@nuxtjs/tailwindcss`, per §7.
- **Mobile-first is not optional.** Per PRD §7.1 the seeker app is designed at 360px and scaled up. The admin portal is desktop-first but must remain operable on a tablet.
- **One message catalogue.** All Indonesian copy lives in `web/app/locales/id.json`, including refusal text, error states, and the crisis response. Copy changes must not require a component edit.
- **Runtime config, not `import.meta.env` scattered through components.** `NUXT_PUBLIC_API_BASE` and `NUXT_PUBLIC_FIREBASE_*` are read through `useRuntimeConfig()` in one composable.
- **The deployed origin must be registered** in the backend's `CORS_ORIGINS` and in the `frame-ancestors` allowlist before a build goes live, or every request will fail at exactly the moment someone is watching.

---

## **References**

- [Product Requirements Document](prd.md) §7.1, F-38 – F-40
- [Technical Design Document](tdd.md) §2, §6
- [Chat UX Specification](chat-ux-specification.md)
- [Android & WordPress Distribution Runbook](android-and-wordpress-distribution-runbook.md)
- [Project Implementation Plan](project-implementation-plan.md) Phase 1, Phase 7
