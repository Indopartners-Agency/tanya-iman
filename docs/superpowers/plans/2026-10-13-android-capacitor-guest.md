# Android Capacitor Shell (Guest-only) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a debug Android build of the existing seeker app (`web/app/`) wrapped in Capacitor, guest-only, talking to the **dev** backend, that passes the guest-relevant rows of the device QA matrix.

**Architecture:** Capacitor 7 wraps the static `nuxt generate` output (`web/app/.output/public`) in an Android WebView; the native project lives at the repo root in `android/` (PIP §3). All Android-specific behaviour — external links, hardware back, safe areas, offline state — is added inside the one Nuxt codebase behind `usePlatform()` / `Capacitor.isNativePlatform()`, so web and widget behaviour is unchanged (F-40). Decision logic is pulled into small pure functions under `web/app/utils/` so it can be unit-tested in plain Vitest.

**Tech Stack:** Nuxt 3 SPA, Capacitor 7 (`@capacitor/core`, `cli`, `android`, `app`, `browser`), Vitest 2, Gradle (JDK 21, Android SDK at `%LOCALAPPDATA%\Android\Sdk`).

**Source requirements:** PIP Phase 7 Task 7.3; Distribution Runbook Part B (B1, B4, B5); Chat UX §9, §12; Nuxt decision §6.

**Decisions already made (do not re-open):**
- Guest-only. Native phone auth (`@capacitor-firebase/authentication`) waits for Wave 4, which is on hold.
- Welcome screen keeps the SMS/WhatsApp buttons on Android, identical to web.
- `applicationId` = `id.tanyaiman.app` (permanent once uploaded to Play).
- Capacitor **7**, not 8: Capacitor 8 requires Node 22 and this machine runs Node 20.17; Capacitor 7 supports Node 20 and JDK 21.
- Builds target the dev backend (GCP project `tanya-iman-dev`, Cloud Run service `tanya-iman-backend`, region `asia-southeast2`).

**Out of scope:** release signing, AAB, Play listing (Task 7.4 / 9.2), native phone auth (A2–A4), tappable crisis `tel:` links (A12 — blocked on PRD OD-4 helpline numbers).

---

## File Structure

| File | Status | Responsibility |
|---|---|---|
| `web/app/capacitor.config.ts` | create | App id/name, `webDir`, native project path, HTTPS scheme, edge-to-edge margins |
| `android/` | create (generated) | Native Capacitor project, committed |
| `android/app/src/main/AndroidManifest.xml` | modify | Keyboard resize behaviour |
| `web/app/scripts/api-base.mjs` | create | Refuses a non-HTTPS or local `NUXT_PUBLIC_API_BASE` before a native build |
| `web/app/utils/linkTarget.ts` | create | How a citation link opens per platform |
| `web/app/utils/network.ts` | create | Distinguishes "never reached the server" from a server error |
| `web/app/utils/backAction.ts` | create | Decides what the hardware back button does |
| `web/app/composables/useExitConfirm.ts` | create | Shared open/closed state of the exit dialog |
| `web/app/components/ExitConfirm.vue` | create | In-app exit confirmation dialog |
| `web/app/plugins/android-back.client.ts` | create | Wires the Capacitor `backButton` event to `backAction` |
| `web/app/components/CitationList.vue` | modify | System browser on Android |
| `web/app/stores/chat.ts` | modify | Offline bubble, lazy session, reconnect retry |
| `web/app/pages/chat.vue` | modify | Retry on `online` event |
| `web/app/components/AppShell.vue`, `web/app/pages/{index,masuk,privasi}.vue` | modify | Safe-area padding |
| `web/app/nuxt.config.ts` | modify | `viewport-fit=cover` |
| `web/app/app.vue` | modify | Mount `ExitConfirm` |
| `web/app/locales/id.json` | modify | Exit dialog copy (client-only `ui` keys) |
| `web/app/package.json` | modify | Capacitor deps, `android:check` / `android:sync` scripts |
| `deploy.sh` | modify | Add the Capacitor origin `https://localhost` to CORS |
| `.github/workflows/ci.yml` | modify | Run seeker unit tests and the API-base check |
| `docs/android-and-wordpress-distribution-runbook.md` | modify | B1 build steps match reality |

Tests live in `web/app/tests/` (existing convention, see `welcome.spec.ts`). Run them with `npx vitest run` from `web/app/`.

---

### Task 1: Install Capacitor and generate the Android project

**Files:**
- Create: `web/app/capacitor.config.ts`
- Create: `android/` (generated)
- Modify: `web/app/package.json`, `package-lock.json`

- [ ] **Step 1: Confirm branch and baseline**

Run (repo root): `git branch --show-current && cd web/app && npx vitest run`
Expected: `feature/android-capacitor`, then `6 passed`.

- [ ] **Step 2: Install Capacitor 7 packages**

Run (repo root):
```bash
npm install --workspace web/app @capacitor/core@^7 @capacitor/android@^7 @capacitor/app@^7 @capacitor/browser@^7
npm install --workspace web/app -D @capacitor/cli@^7
```
Expected: `web/app/package.json` lists the five packages, all `^7.x`.

- [ ] **Step 3: Write `web/app/capacitor.config.ts`**

```ts
import type { CapacitorConfig } from '@capacitor/cli'

// F-39: the Android app is the same static build the web app and the widget
// serve. The native project sits at the repo root (PIP section 3), not inside
// web/app, so it is addressed by path here.
const config: CapacitorConfig = {
  appId: 'id.tanyaiman.app',
  appName: 'Tanya Iman',
  webDir: '.output/public',
  server: {
    // The WebView origin becomes https://localhost. The backend allows that
    // origin in CORS (deploy.sh), and no request is ever plain HTTP.
    androidScheme: 'https',
  },
  android: {
    path: '../../android',
    allowMixedContent: false,
    // Android 15 forces edge-to-edge for targetSdk 35. Capacitor pads the
    // WebView below the system bars so the input never sits under the gesture
    // bar; the CSS env() padding covers devices where it does not.
    adjustMarginsForEdgeToEdge: 'auto',
  },
}

export default config
```

- [ ] **Step 4: Confirm `adjustMarginsForEdgeToEdge` exists in the installed CLI**

Run: `grep -n "adjustMarginsForEdgeToEdge" node_modules/@capacitor/cli/dist/declarations.d.ts`
Expected: one match. If there is **no** match, delete that property and its comment from the config (older 7.x), and rely on the CSS padding in Task 6.

- [ ] **Step 5: Build the web assets once (Capacitor needs `webDir` to exist)**

Run (repo root): `NUXT_PUBLIC_API_BASE=https://api-staging.tanyaiman.id npm run generate --workspace web/app`
Expected: `web/app/.output/public/index.html` exists.

- [ ] **Step 6: Generate the Android project**

Run (from `web/app/`): `npx cap add android`
Expected: `android/` created at the **repo root**; `android/app/build.gradle` contains `applicationId "id.tanyaiman.app"`.

Verify: `grep -n applicationId ../../android/app/build.gradle`

- [ ] **Step 7: Confirm generated build output is ignored**

Run (repo root): `cat android/.gitignore | grep -E "build|local.properties|assets/public"`
Expected: matches for `build/`, `local.properties`, and `app/src/main/assets/public`. Then `git status --short android | head` must not show `build/` or `assets/public`.

- [ ] **Step 8: Debug build smoke test**

```bash
export ANDROID_HOME="$LOCALAPPDATA/Android/Sdk"
cd android && ./gradlew assembleDebug
```
Expected: `BUILD SUCCESSFUL`; `android/app/build/outputs/apk/debug/app-debug.apk` exists.

- [ ] **Step 9: Commit**

```bash
git add web/app/package.json package-lock.json web/app/capacitor.config.ts android
git commit -m "feat(android): add Capacitor 7 shell for the seeker app"
```

---

### Task 2: Refuse a non-HTTPS API base before a native build

**Files:**
- Create: `web/app/scripts/api-base.mjs`
- Test: `web/app/tests/api-base.spec.ts`
- Modify: `web/app/package.json` (scripts), `.github/workflows/ci.yml`

- [ ] **Step 1: Write the failing test** — `web/app/tests/api-base.spec.ts`

```ts
import { describe, expect, it } from 'vitest'
import { checkApiBase } from '../scripts/api-base.mjs'

describe('checkApiBase (PIP Task 7.3: HTTPS-only API base)', () => {
  it('accepts an HTTPS Cloud Run URL', () => {
    expect(checkApiBase('https://tanya-iman-backend-abc123-et.a.run.app')).toBeNull()
  })

  it('rejects a missing value', () => {
    expect(checkApiBase(undefined)).toMatch(/not set/)
    expect(checkApiBase('')).toMatch(/not set/)
  })

  it('rejects something that is not a URL', () => {
    expect(checkApiBase('api.tanyaiman.id')).toMatch(/not a URL/)
  })

  it('rejects plain HTTP', () => {
    expect(checkApiBase('http://api.tanyaiman.id')).toMatch(/HTTPS/)
  })

  it('rejects local and private hosts, which a phone cannot reach', () => {
    for (const url of [
      'https://localhost:8000',
      'https://127.0.0.1:8000',
      'https://10.0.2.2:8000',
      'https://192.168.1.5:8000',
      'https://172.20.0.4:8000',
    ]) {
      expect(checkApiBase(url)).toMatch(/local/)
    }
  })
})
```

- [ ] **Step 2: Run it to verify it fails**

Run (from `web/app/`): `npx vitest run tests/api-base.spec.ts`
Expected: FAIL — cannot resolve `../scripts/api-base.mjs`.

- [ ] **Step 3: Write `web/app/scripts/api-base.mjs`**

```js
import { pathToFileURL } from 'node:url'

/**
 * PIP Task 7.3 / Runbook B1: an Android build bakes NUXT_PUBLIC_API_BASE into
 * the APK. A build pointing at plain HTTP or a developer's machine cannot be
 * fixed without shipping a new build, so it is refused before `cap sync`.
 */
const LOCAL_HOST =
  /^(localhost|0\.0\.0\.0|127\.|10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.)/

/**
 * @param {string | undefined} value
 * @returns {string | null} why the value is unacceptable, or null if it is fine
 */
export function checkApiBase(value) {
  if (!value) return 'NUXT_PUBLIC_API_BASE is not set'

  let url
  try {
    url = new URL(value)
  } catch {
    return `NUXT_PUBLIC_API_BASE is not a URL: ${value}`
  }

  if (url.protocol !== 'https:') return `NUXT_PUBLIC_API_BASE must be HTTPS: ${value}`
  if (LOCAL_HOST.test(url.hostname)) {
    return `NUXT_PUBLIC_API_BASE points at a local host: ${value}`
  }
  return null
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const problem = checkApiBase(process.env.NUXT_PUBLIC_API_BASE)
  if (problem) {
    console.error(`[android] ${problem}`)
    process.exit(1)
  }
  console.log(`[android] API base OK: ${process.env.NUXT_PUBLIC_API_BASE}`)
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `npx vitest run tests/api-base.spec.ts`
Expected: `5 passed`.

- [ ] **Step 5: Add the npm scripts** — in `web/app/package.json` `"scripts"`, after `"typecheck"`:

```json
    "android:check": "node scripts/api-base.mjs",
    "android:sync": "node scripts/api-base.mjs && nuxt generate && cap sync android"
```

Verify the CLI path fails closed: `NUXT_PUBLIC_API_BASE=http://x npm run android:check` → exit code 1 with `must be HTTPS`.

- [ ] **Step 6: Run the check and the seeker tests in CI** — in `.github/workflows/ci.yml`, job `frontend`, insert after the `Install` step:

```yaml
      - name: Unit tests
        if: matrix.app == 'app'
        run: npm test --workspace web/app

      - name: Check Android API base
        if: matrix.app == 'app'
        run: npm run android:check --workspace web/app
        env:
          NUXT_PUBLIC_API_BASE: https://api-staging.tanyaiman.id
```

- [ ] **Step 7: Commit**

```bash
git add web/app/scripts/api-base.mjs web/app/tests/api-base.spec.ts web/app/package.json .github/workflows/ci.yml
git commit -m "feat(android): refuse a non-HTTPS API base before native builds"
```

---

### Task 3: Allow the Capacitor origin in backend CORS

The Android WebView sends `Origin: https://localhost` (from `androidScheme: 'https'`). Without it in `CORS_ORIGINS`, every request from the app fails (Runbook B5, "Every request fails").

**Files:**
- Modify: `deploy.sh` (CORS block, around line 372)

- [ ] **Step 1: Add the origin** — replace:

```bash
    [[ -n "$APP_SITE_ID" ]]   && _cors_parts+=("https://${APP_SITE_ID}.web.app")
```

with:

```bash
    [[ -n "$APP_SITE_ID" ]]   && _cors_parts+=("https://${APP_SITE_ID}.web.app")
    # The Android app is the same bundle served by Capacitor from
    # https://localhost (androidScheme https), so its requests carry that origin.
    [[ -n "$APP_SITE_ID" ]]   && _cors_parts+=("https://localhost")
```

- [ ] **Step 2: Syntax check**

Run: `bash -n deploy.sh && echo ok`
Expected: `ok`.

- [ ] **Step 3: Commit**

```bash
git add deploy.sh
git commit -m "fix(deploy): allow the Capacitor Android origin in CORS"
```

- [ ] **Step 4: Redeploy the dev backend — ASK YOUR HUMAN PARTNER FIRST**

This changes shared dev infrastructure. With approval:
```bash
bash deploy.sh backend --env dev
gcloud run services describe tanya-iman-backend --region asia-southeast2 --project tanya-iman-dev --format='value(spec.template.spec.containers[0].env)' | tr ';' '\n' | grep CORS
```
Expected: `CORS_ORIGINS` contains `https://localhost`.

---

### Task 4: Citations open in the system browser on Android

**Files:**
- Create: `web/app/utils/linkTarget.ts`
- Test: `web/app/tests/link-target.spec.ts`
- Modify: `web/app/components/CitationList.vue`

- [ ] **Step 1: Write the failing test** — `web/app/tests/link-target.spec.ts`

```ts
import { describe, expect, it } from 'vitest'
import { citationLinkMode } from '../utils/linkTarget'

describe('citationLinkMode (Chat UX sections 9 and 11)', () => {
  it('opens a new tab on web', () => {
    expect(citationLinkMode('web')).toBe('new-tab')
  })

  it('escapes the iframe in the widget', () => {
    expect(citationLinkMode('widget')).toBe('top')
  })

  it('hands the link to the system browser on Android, never the WebView', () => {
    expect(citationLinkMode('android')).toBe('system')
  })
})
```

- [ ] **Step 2: Run it to verify it fails**

Run: `npx vitest run tests/link-target.spec.ts`
Expected: FAIL — cannot resolve `../utils/linkTarget`.

- [ ] **Step 3: Write `web/app/utils/linkTarget.ts`**

```ts
import type { Platform } from '@tanya-iman/shared'

export type CitationLinkMode = 'new-tab' | 'top' | 'system'

/**
 * Web opens a new tab. The widget escapes its 620px iframe. Android hands the
 * URL to the system browser, because a link that opens inside the WebView
 * replaces the conversation, and a seeker who cannot get back has lost it
 * (Chat UX section 9; Runbook A8, a release blocker).
 */
export function citationLinkMode(platform: Platform): CitationLinkMode {
  if (platform === 'widget') return 'top'
  if (platform === 'android') return 'system'
  return 'new-tab'
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `npx vitest run tests/link-target.spec.ts`
Expected: `3 passed`.

- [ ] **Step 5: Use it in `web/app/components/CitationList.vue`** — replace the platform block in `<script setup>`:

```ts
/**
 * Links open in a new tab on web and in the external browser on Android.
 * Inside the widget they must escape the iframe — a citation that opens in a
 * 620px-tall frame strands the reader (Chat UX section 11).
 */
const { platform } = usePlatform()
const target = platform === 'widget' ? '_top' : '_blank'
```

with:

```ts
/**
 * Links open in a new tab on web, escape the iframe in the widget, and go to
 * the system browser on Android (utils/linkTarget.ts).
 */
const { platform } = usePlatform()
const mode = citationLinkMode(platform)
const target = mode === 'top' ? '_top' : '_blank'

function open(event: MouseEvent, url: string) {
  if (mode !== 'system') return
  event.preventDefault()
  void Browser.open({ url })
}
```

Add at the top of `<script setup>`, under the existing `Citation` import:

```ts
import { Browser } from '@capacitor/browser'
```

And on the `<a>` element add the handler, keeping `href` so long-press and accessibility still see a real link:

```vue
          <a
            :href="citation.url"
            :target="target"
            rel="noopener noreferrer"
            class="block text-[14px] leading-snug text-accent underline decoration-subtle underline-offset-2 hover:decoration-accent"
            @click="open($event, citation.url)"
          >
```

- [ ] **Step 6: Typecheck**

Run (repo root): `npm run typecheck --workspace web/app`
Expected: no errors.

- [ ] **Step 7: Commit**

```bash
git add web/app/utils/linkTarget.ts web/app/tests/link-target.spec.ts web/app/components/CitationList.vue
git commit -m "feat(android): open citations in the system browser"
```

---

### Task 5: Offline state distinct from a server error, with retry on reconnect

`fetch` rejects with a `TypeError` when the request never reached a server; an `ApiError` means the server answered. Today both render as `shared.error`. Chat UX §12 requires a distinct Indonesian offline state and automatic retry on reconnect. The copy already exists: `ui.network_error` = "Koneksi terputus. Silakan coba lagi."

Also fixed here: `chat.start()` currently throws when the app opens offline, leaving a blank transcript and an unhandled rejection. The greeting now renders regardless and the session is opened by the first question instead.

**Files:**
- Create: `web/app/utils/network.ts`
- Test: `web/app/tests/network.spec.ts`
- Modify: `web/app/stores/chat.ts`, `web/app/pages/chat.vue`

- [ ] **Step 1: Write the failing test** — `web/app/tests/network.spec.ts`

```ts
import { describe, expect, it } from 'vitest'
import { ApiError } from '@tanya-iman/shared'
import { isNetworkFailure } from '../utils/network'

describe('isNetworkFailure (Chat UX section 12)', () => {
  it('treats a fetch TypeError as a network failure', () => {
    expect(isNetworkFailure(new TypeError('Failed to fetch'), true)).toBe(true)
  })

  it('treats any non-API failure as network when the device is offline', () => {
    expect(isNetworkFailure(new Error('aborted'), false)).toBe(true)
  })

  it('never treats a server response as a network failure, even offline', () => {
    expect(isNetworkFailure(new ApiError(500, 'boom'), true)).toBe(false)
    expect(isNetworkFailure(new ApiError(503, 'down'), false)).toBe(false)
  })

  it('treats other errors while online as server-side', () => {
    expect(isNetworkFailure(new Error('bad json'), true)).toBe(false)
  })
})
```

- [ ] **Step 2: Run it to verify it fails**

Run: `npx vitest run tests/network.spec.ts`
Expected: FAIL — cannot resolve `../utils/network`.

- [ ] **Step 3: Write `web/app/utils/network.ts`**

```ts
import { ApiError } from '@tanya-iman/shared'

/**
 * Chat UX section 12: being offline must read differently from a server
 * fault. fetch rejects with a TypeError when the request never reached a
 * server; an ApiError means the server answered, however badly.
 */
export function isNetworkFailure(err: unknown, online: boolean): boolean {
  if (err instanceof ApiError) return false
  return !online || err instanceof TypeError
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `npx vitest run tests/network.spec.ts`
Expected: `4 passed`.

- [ ] **Step 5: Mark offline turns on the `Message` type** — in `web/app/stores/chat.ts`, inside `interface Message`, after `failedQuestion?: string`:

```ts
  /** The turn failed because the request never left the device. */
  offline?: boolean
```

- [ ] **Step 6: Split session creation out of `start()`** — replace the whole `start` function with:

```ts
  /**
   * Opening the conversation must not depend on the network: offline at
   * launch, the greeting still renders and the session is opened by the first
   * question instead (Chat UX section 12).
   */
  async function start() {
    messages.value = []
    sessionId.value = null
    push({
      id: 'greeting',
      role: 'iman',
      text: t('shared.greeting'),
    })

    try {
      await openSession()
    } catch (err) {
      if (!isNetworkFailure(err, navigator.onLine)) throw err
    }
  }

  async function openSession(): Promise<string> {
    const { platform, embedOrigin } = usePlatform()
    const { session_id } = await useApi().createSession({
      platform,
      embed_origin: embedOrigin,
    })
    sessionId.value = session_id
    return session_id
  }
```

- [ ] **Step 7: Open the session inside `ask`'s try block** — in `ask`, delete the line:

```ts
    if (!sessionId.value) await start()
```

and replace the start of the `try` block:

```ts
    try {
      const api = useApi()
      const response: AskResponse = await api.ask({
        session_id: sessionId.value!,
        text: trimmed,
      })
```

with:

```ts
    try {
      const session = sessionId.value ?? (await openSession())
      const response: AskResponse = await useApi().ask({
        session_id: session,
        text: trimmed,
      })
```

Behaviour note for the commit message: after a session expires, the next question now opens a fresh session **without wiping the transcript** (previously `start()` cleared it). This matches F-27 — the seeker's earlier conversation stays visible.

- [ ] **Step 8: Render offline turns with their own copy** — in `handleAskError`, insert immediately before the final comment `// The failure is visible inside the conversation…`:

```ts
    if (isNetworkFailure(err, navigator.onLine)) {
      replacePending(placeholderId, {
        id: placeholderId,
        role: 'iman',
        text: t('ui.network_error'),
        answerSource: 'error',
        failedQuestion: question,
        offline: true,
      })
      return
    }
```

`AnswerStates.vue` already renders `message.text` when it is set, with the Coba lagi button, so no component change is needed.

- [ ] **Step 9: Add `retryOffline`** — after the `retry` function:

```ts
  /** Chat UX section 12: when the connection returns, resend the last turn that never left. */
  async function retryOffline() {
    if (sending.value) return
    const failed = [...messages.value].reverse().find((m) => m.offline && m.failedQuestion)
    if (failed) await retry(failed.id)
  }
```

and add it to the returned object:

```ts
  return { messages, sessionId, sending, error, start, ask, toggleLike, retry, retryOffline, reset }
```

- [ ] **Step 10: Retry on reconnect in `web/app/pages/chat.vue`** — after the `scrollToBottom` function add:

```ts
function onOnline() {
  void chat.retryOffline()
}
```

At the start of the existing `onMounted` callback (before the auth check), add:

```ts
  window.addEventListener('online', onOnline)
```

and after the `onMounted` block add:

```ts
onUnmounted(() => window.removeEventListener('online', onOnline))
```

- [ ] **Step 11: Typecheck and full test run**

Run (repo root): `npm run typecheck --workspace web/app && cd web/app && npx vitest run`
Expected: no type errors; all tests pass.

- [ ] **Step 12: Manual check in a desktop browser**

Run `npm run dev:app` with the backend running (`cd backend && uv run uvicorn main:app --reload`). Continue as guest, then in DevTools → Network set **Offline** and send a question.
Expected: bubble reads "Koneksi terputus. Silakan coba lagi." (not "Maaf, terjadi gangguan…"). Switch back to **No throttling**: the question is resent automatically and answered.

Note: with the backend process stopped, `fetch` also throws a `TypeError`, so that case correctly shows the **offline** copy too — the request never reached a server. The server-error copy ("Maaf, terjadi gangguan saat menyiapkan jawaban.") only appears when the backend answers with an error status; that path is unchanged by this task.

- [ ] **Step 13: Commit**

```bash
git add web/app/utils/network.ts web/app/tests/network.spec.ts web/app/stores/chat.ts web/app/pages/chat.vue
git commit -m "feat(app): distinct offline state with retry on reconnect

A turn that never reached the server now reads 'Koneksi terputus' and is
resent when the connection returns. Opening the chat offline no longer
leaves a blank transcript: the session opens with the first question.
After a session expires, the next question opens a new session without
clearing the transcript."
```

---

### Task 6: Safe-area padding

Chat UX §12: the root pads with `env(safe-area-inset-*)`; the input never sits under the gesture bar. `Composer.vue` already pads its bottom. `env()` evaluates to `0` on desktop and inside the widget iframe, so this changes nothing there.

**Files:**
- Modify: `web/app/nuxt.config.ts`, `web/app/components/AppShell.vue`, `web/app/pages/index.vue`, `web/app/pages/masuk.vue`, `web/app/pages/privasi.vue`

- [ ] **Step 1: Enable insets** — in `web/app/nuxt.config.ts` replace:

```ts
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
```

with:

```ts
        // viewport-fit=cover is what makes env(safe-area-inset-*) non-zero on
        // notched and gesture-bar Android devices (Chat UX section 12).
        { name: 'viewport', content: 'width=device-width, initial-scale=1, viewport-fit=cover' },
```

- [ ] **Step 2: App header** — in `web/app/components/AppShell.vue` replace the header class:

```vue
      class="flex items-center justify-between border-b border-subtle bg-surface px-4 py-3"
```

with:

```vue
      class="flex items-center justify-between border-b border-subtle bg-surface px-4 pb-3 pt-[max(0.75rem,env(safe-area-inset-top))]"
```

- [ ] **Step 3: Welcome and sign-in pages** — in **both** `web/app/pages/index.vue` and `web/app/pages/masuk.vue` replace:

```vue
  <main class="flex min-h-dvh flex-col bg-base px-6">
```

with:

```vue
  <main class="flex min-h-dvh flex-col bg-base px-6 pt-[env(safe-area-inset-top)]">
```

and replace:

```vue
    <footer class="py-4 text-center">
```

with:

```vue
    <footer class="pt-4 pb-[max(1rem,env(safe-area-inset-bottom))] text-center">
```

- [ ] **Step 4: Privacy page** — in `web/app/pages/privasi.vue` replace:

```vue
  <main class="min-h-dvh bg-base px-6 py-8">
```

with:

```vue
  <main class="min-h-dvh bg-base px-6 pt-[max(2rem,env(safe-area-inset-top))] pb-[max(2rem,env(safe-area-inset-bottom))]">
```

- [ ] **Step 5: Build to confirm Tailwind emits the classes**

Run (repo root): `NUXT_PUBLIC_API_BASE=https://api-staging.tanyaiman.id npm run generate --workspace web/app && grep -o "safe-area-inset-top" -r web/app/.output/public/_nuxt/*.css | head -1`
Expected: build succeeds and prints a match.

- [ ] **Step 6: Commit**

```bash
git add web/app/nuxt.config.ts web/app/components/AppShell.vue web/app/pages/index.vue web/app/pages/masuk.vue web/app/pages/privasi.vue
git commit -m "feat(app): pad for Android safe areas"
```

---

### Task 7: Hardware back button with exit confirmation

Chat UX §12 / Runbook A7: back pops in-app navigation first; from mid-conversation, one confirm before exit. An in-app dialog is used instead of `window.confirm`, which titles itself with the WebView origin (`https://localhost`) and blocks the JS thread.

**Files:**
- Create: `web/app/utils/backAction.ts`, `web/app/composables/useExitConfirm.ts`, `web/app/components/ExitConfirm.vue`, `web/app/plugins/android-back.client.ts`
- Test: `web/app/tests/back-action.spec.ts`
- Modify: `web/app/app.vue`, `web/app/locales/id.json`

- [ ] **Step 1: Write the failing test** — `web/app/tests/back-action.spec.ts`

```ts
import { describe, expect, it } from 'vitest'
import { backAction, type BackContext } from '../utils/backAction'

const base: BackContext = {
  path: '/chat',
  canGoBack: true,
  hasConversation: false,
  dialogOpen: false,
}

describe('backAction (Chat UX section 12)', () => {
  it('closes the exit dialog first if it is open', () => {
    expect(backAction({ ...base, hasConversation: true, dialogOpen: true })).toBe('close-dialog')
  })

  it('asks before leaving a conversation the seeker has started', () => {
    expect(backAction({ ...base, hasConversation: true })).toBe('confirm-exit')
  })

  it('goes back from an empty chat when there is history', () => {
    expect(backAction(base)).toBe('go-back')
  })

  it('pops in-app navigation from secondary screens', () => {
    expect(backAction({ ...base, path: '/privasi' })).toBe('go-back')
    expect(backAction({ ...base, path: '/masuk' })).toBe('go-back')
  })

  it('exits from the welcome screen', () => {
    expect(backAction({ ...base, path: '/' })).toBe('exit')
  })

  it('exits when there is nothing to go back to', () => {
    expect(backAction({ ...base, path: '/privasi', canGoBack: false })).toBe('exit')
  })
})
```

- [ ] **Step 2: Run it to verify it fails**

Run: `npx vitest run tests/back-action.spec.ts`
Expected: FAIL — cannot resolve `../utils/backAction`.

- [ ] **Step 3: Write `web/app/utils/backAction.ts`**

```ts
export type BackAction = 'close-dialog' | 'confirm-exit' | 'go-back' | 'exit'

export interface BackContext {
  path: string
  /** From Capacitor's backButton event: the WebView has history to pop. */
  canGoBack: boolean
  /** The seeker has sent at least one question. */
  hasConversation: boolean
  dialogOpen: boolean
}

/**
 * Chat UX section 12: the hardware back button pops in-app navigation first,
 * and never leaves a conversation silently — one confirm, then exit.
 */
export function backAction(ctx: BackContext): BackAction {
  if (ctx.dialogOpen) return 'close-dialog'
  if (ctx.path === '/chat' && ctx.hasConversation) return 'confirm-exit'
  if (ctx.path === '/' || !ctx.canGoBack) return 'exit'
  return 'go-back'
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `npx vitest run tests/back-action.spec.ts`
Expected: `6 passed`.

- [ ] **Step 5: Add the copy** — in `web/app/locales/id.json`, inside `"ui"`, after `"logout": "Keluar"` (add a comma after it):

```json
    "exit_title": "Keluar dari Tanya Iman?",
    "exit_body": "Percakapan yang sedang berlangsung akan ditutup.",
    "exit_stay": "Tetap di sini",
    "exit_leave": "Keluar"
```

These are client-only `ui` strings, not response templates, so `backend/tests/test_copy_parity.py` is unaffected. Flag them for editorial review in the PR anyway.

- [ ] **Step 6: Write `web/app/composables/useExitConfirm.ts`**

```ts
/**
 * Shared between the back-button plugin, which opens the dialog, and the
 * dialog itself. Module scope is safe: the app is a client-only SPA.
 */
const open = ref(false)

export function useExitConfirm() {
  return { open }
}
```

- [ ] **Step 7: Write `web/app/components/ExitConfirm.vue`**

```vue
<script setup lang="ts">
import { App } from '@capacitor/app'

/**
 * Chat UX section 12. Opened only by the Android back button, mid-conversation.
 */
const { open } = useExitConfirm()
const { t } = useCopy()

function leave() {
  void App.exitApp()
}
</script>

<template>
  <div
    v-if="open"
    class="fixed inset-0 z-50 grid place-items-center bg-[rgba(0,0,0,0.4)] px-6"
    role="dialog"
    aria-modal="true"
    :aria-label="t('ui.exit_title')"
  >
    <div class="w-full max-w-[340px] rounded-2xl bg-surface p-5 shadow-md">
      <p class="font-serif text-[17px] text-primary">{{ t('ui.exit_title') }}</p>
      <p class="mt-2 text-[14px] leading-relaxed text-secondary">{{ t('ui.exit_body') }}</p>
      <div class="mt-5 flex justify-end gap-2">
        <button
          type="button"
          class="min-h-[44px] rounded-lg px-4 text-[14px] font-medium text-accent hover:bg-raised"
          @click="open = false"
        >
          {{ t('ui.exit_stay') }}
        </button>
        <button
          type="button"
          class="min-h-[44px] rounded-lg bg-accent px-4 text-[14px] font-medium text-on-accent hover:bg-accent-hover"
          @click="leave"
        >
          {{ t('ui.exit_leave') }}
        </button>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 8: Write `web/app/plugins/android-back.client.ts`**

```ts
import { App } from '@capacitor/app'
import { Capacitor } from '@capacitor/core'

/**
 * Android only. Without a listener, the hardware back button closes the app
 * from any screen, including mid-conversation.
 */
export default defineNuxtPlugin(() => {
  if (!Capacitor.isNativePlatform()) return

  const router = useRouter()
  const chat = useChatStore()
  const { open } = useExitConfirm()

  void App.addListener('backButton', ({ canGoBack }) => {
    const action = backAction({
      path: router.currentRoute.value.path,
      canGoBack,
      hasConversation: chat.messages.some((m) => m.role === 'seeker'),
      dialogOpen: open.value,
    })

    if (action === 'close-dialog') open.value = false
    else if (action === 'confirm-exit') open.value = true
    else if (action === 'go-back') router.back()
    else void App.exitApp()
  })
})
```

- [ ] **Step 9: Mount the dialog** — replace `web/app/app.vue` with:

```vue
<template>
  <NuxtPage />
  <ExitConfirm />
</template>
```

- [ ] **Step 10: Typecheck and tests**

Run (repo root): `npm run typecheck --workspace web/app && cd web/app && npx vitest run`
Expected: no type errors; all tests pass.

- [ ] **Step 11: Commit**

```bash
git add web/app/utils/backAction.ts web/app/tests/back-action.spec.ts web/app/composables/useExitConfirm.ts web/app/components/ExitConfirm.vue web/app/plugins/android-back.client.ts web/app/app.vue web/app/locales/id.json
git commit -m "feat(android): confirm before the back button leaves a conversation"
```

---

### Task 8: Keyboard and rotation in the manifest

Runbook A9/A10, B5: the input stays above the keyboard; the transcript survives rotation.

**Files:**
- Modify: `android/app/src/main/AndroidManifest.xml`

- [ ] **Step 1: Inspect the generated activity**

Run: `grep -n -A8 "<activity" android/app/src/main/AndroidManifest.xml`
Expected: `android:configChanges` includes `orientation` and `screenSize` (Capacitor's template sets these, so rotation does not recreate the activity and the WebView state survives).

- [ ] **Step 2: Add keyboard resize** — if `android:windowSoftInputMode` is absent from the `MainActivity` `<activity>` element, add this attribute to it:

```xml
            android:windowSoftInputMode="adjustResize"
```

If it is present with a different value, change it to `adjustResize`.

- [ ] **Step 3: Rebuild**

Run: `export ANDROID_HOME="$LOCALAPPDATA/Android/Sdk" && cd android && ./gradlew assembleDebug`
Expected: `BUILD SUCCESSFUL`.

- [ ] **Step 4: Commit**

```bash
git add android/app/src/main/AndroidManifest.xml
git commit -m "feat(android): resize for the keyboard instead of overlapping"
```

---

### Task 9: Dev build on a device and guest QA

**Prerequisite:** Task 3 Step 4 done (dev backend redeployed with `https://localhost` in CORS).

- [ ] **Step 1: Resolve the dev backend URL**

```bash
DEV_API="$(gcloud run services describe tanya-iman-backend --region asia-southeast2 --project tanya-iman-dev --format='value(status.url)')"
echo "$DEV_API"
```
Expected: an `https://…run.app` URL.

- [ ] **Step 2: Build and sync with the dev API**

```bash
NUXT_PUBLIC_API_BASE="$DEV_API" npm run android:sync --workspace web/app
```
Expected: `[android] API base OK: https://…`, generate succeeds, `cap sync` reports `Sync finished`.

- [ ] **Step 3: Build and install the debug APK**

```bash
export ANDROID_HOME="$LOCALAPPDATA/Android/Sdk"
(cd android && ./gradlew assembleDebug)
adb devices
adb install -r android/app/build/outputs/apk/debug/app-debug.apk
```
Expected: one device listed; `Success`.

- [ ] **Step 4: Run the guest rows of the device matrix** (Runbook B4) on a physical device — Android 14, plus Android 10 if available. Record results in the PR.

| # | Case | Pass condition |
|---|---|---|
| A1 | Cold start | Welcome renders; nothing under the status bar or gesture bar |
| A5 | Three questions in sequence (as guest) | Three answers; transcript scrolls |
| A6 | Airplane mode mid-question | "Koneksi terputus. Silakan coba lagi."; answer arrives automatically after airplane mode is turned off |
| A7 | Back button mid-conversation | Exit dialog appears; "Tetap di sini" keeps the transcript; back again closes the dialog |
| A8 | Citation tap | Opens in the browser; returning to the app shows the same transcript |
| A9 | Rotate during a pending answer | Pending bubble and transcript survive |
| A10 | Keyboard open with a long transcript | Input above the keyboard; transcript not covered |
| A11 | System font 200% | No clipping; all controls reachable |
| A13 | Parity | The same question on https://tanya-iman-app-dev.web.app and on the device returns the same answer |

Skipped, with reason: A2–A4 (phone auth, Wave 4 on hold), A12 (helpline numbers pending, PRD OD-4).

- [ ] **Step 5: Debug with Chrome if anything fails**

With the device connected, open `chrome://inspect/#devices` on the desktop, select the Tanya Iman WebView, and read the console and network tabs. CORS failures show as a blocked preflight to the dev API — recheck Task 3.

---

### Task 10: Bring the runbook in line

**Files:**
- Modify: `docs/android-and-wordpress-distribution-runbook.md` (§B1)

- [ ] **Step 1: Replace the B1 code block** with:

```bash
# Release (from the repo root). android:sync refuses a non-HTTPS or local API base.
export NUXT_PUBLIC_API_BASE=https://api.tanyaiman.id
npm ci
npm run android:sync --workspace web/app   # generate + cap sync into android/
cd android
./gradlew bundleRelease          # → app/build/outputs/bundle/release/app-release.aab
```

- [ ] **Step 2: Add a dev-build paragraph** directly after that code block:

```markdown
**Dev build for device testing.** Point the build at the dev Cloud Run backend and install a debug APK:

    NUXT_PUBLIC_API_BASE="$(gcloud run services describe tanya-iman-backend --region asia-southeast2 --project tanya-iman-dev --format='value(status.url)')" \
      npm run android:sync --workspace web/app
    cd android && ./gradlew assembleDebug
    adb install -r app/build/outputs/apk/debug/app-debug.apk

The WebView's origin is `https://localhost`; the backend must list it in `CORS_ORIGINS` (`deploy.sh` adds it).
```

- [ ] **Step 3: Commit**

```bash
git add docs/android-and-wordpress-distribution-runbook.md
git commit -m "docs(android): document the Capacitor build and dev device build"
```

---

## After all tasks

- Run `cd backend && uv run pytest -v` (deploy.sh change only, but AGENTS.md requires green) and `cd web/app && npx vitest run`.
- Push `feature/android-capacitor`, open a PR into `dev` with the A-matrix results and the editorial flag for the four `exit_*` strings.
