# UI Design System and Approval Mockup — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the presentation layer for the seeker app and admin portal against the existing scaffold, plus a fixture-backed demo mode so the result can be hosted statically for client approval.

**Architecture:** Semantic design tokens live in `web/shared/src/tokens.ts` and are emitted as CSS custom properties into each app's stylesheet; Tailwind maps utility names onto those variables so no component writes a hex value. A `NUXT_PUBLIC_DEMO_MODE=1` flag swaps `createClient` for `createDemoClient` — same `ApiClient` interface, fixture data behind it — at the single seam in `useApi`, so no store, page, or component knows the difference.

**Tech Stack:** Nuxt 3 (SPA, `ssr: false`), Vue 3, Tailwind CSS 3.4, Pinia, TypeScript, Vitest (in `web/shared`), npm workspaces.

**Spec:** `docs/superpowers/specs/2026-09-08-ui-design-system-design.md`
**Governing UX specs:** `docs/chat-ux-specification.md`, `docs/admin-ux-specification.md`

---

## Working agreements

- **Branch:** all work happens on `feature/ui-design-system`, already created off `dev`. Never commit to `dev` or `main` (`docs/branching-and-deployment-workflow.md`).
- **Commands run from the repo root** unless a step says otherwise.
- **No user-facing string in a component.** Every string is added under `ui` in `web/app/locales/id.json` (seeker) or `web/admin/locales/id.json` (admin). Never edit anything under `shared` — `backend/tests/test_copy_parity.py` asserts those are byte-identical to `backend/config/responses.id.yml`, and changing them is a product decision requiring editorial sign-off.
- **No hex values in components.** Only `web/shared/src/tokens.ts` and the two `tailwind.css` files name colours.
- **Demo content is labelled.** Sample answers are written for this work and are not editorially approved. No real helpline number is introduced anywhere (SOW B1).
- **Verify before claiming done.** Run the command, read the output.

## File structure

### New — `web/shared` (shared by both apps)

| File | Responsibility |
|---|---|
| `src/tokens.ts` | The palette. Token name → hex, for seeker and admin. Single source of colour truth. |
| `src/tokens.test.ts` | Asserts every foreground/background pair meets WCAG 2.1 AA. |
| `src/contrast.ts` | Relative-luminance and contrast-ratio maths used by the test. |

### New — `web/app` (seeker)

| File | Responsibility |
|---|---|
| `assets/css/tokens.css` | Seeker tokens as CSS custom properties. Generated content, checked in. |
| `composables/useDemoMode.ts` | Reads the runtime flag. One place decides whether demo mode is on. |
| `composables/useDemoClient.ts` | Fixture-backed `ApiClient`. Deleted wholesale when Phase 5 lands. |
| `demo/scenarios.ts` | The eight sample exchanges and the response-state fixtures. |
| `components/AppShell.vue` | Header, overflow menu, source note, footer privacy link. Embed-aware. |
| `components/AnswerStates.vue` | Renders the non-standard states: refusal, no-grounding, crisis, error, rate limit. |
| `components/CitationList.vue` | Title as link text, domain beneath, opens externally. |
| `components/LikeControl.vue` | Heart, optimistic, reversible, no count. |
| `components/DemoScenarioBar.vue` | Scenario switcher. Renders only in demo mode. |
| `components/PendingBubble.vue` | Three-dot animation and the 8-second notice. |
| `pages/masuk.vue` | Phone entry then OTP, driven by `?channel=`. |
| `pages/privasi.vue` | Privacy policy page. |
| `pages/widget-demo.vue` | Simulated WordPress host article with the widget embedded. |

### Modified — `web/app`

| File | Change |
|---|---|
| `tailwind.config.ts` | Map colour utilities onto the CSS variables; add the type scale. |
| `assets/css/tailwind.css` | Import tokens, set the serif/sans stacks, base body rules. |
| `nuxt.config.ts` | Add `demoMode` to `runtimeConfig.public`; add the font link. |
| `stores/chat.ts` | Carry `answerSource` on `Message`; add retry; add the rate-limit countdown. |
| `composables/useApi.ts` | Swap in the demo client when the flag is set. |
| `components/MessageBubble.vue` | Token classes instead of `emerald-*`/`slate-*`; delegate citations and like. |
| `components/Composer.vue` | Token classes; keep the textarea editable while sending (F-26). |
| `pages/index.vue` | Welcome per Chat UX §5; enable SMS/WhatsApp routes. |
| `pages/chat.vue` | Use `AppShell`; add the *Pesan baru* pill and scroll-anchoring. |
| `locales/id.json` | New keys under `ui` only. |

### New — `web/admin`

| File | Responsibility |
|---|---|
| `assets/css/tokens.css` | Admin tokens as CSS custom properties. |
| `locales/id.json` | Admin copy. |
| `composables/useCopy.ts` | Same flat lookup as the seeker app. |
| `composables/useDemoMode.ts` | Reads the runtime flag. |
| `demo/fixtures.ts` | Questions, topics, clusters, gaps, review items, audit entries, settings. |
| `stores/session.ts` | Signed-in admin and role. Drives role-aware hiding. |
| `layouts/default.vue` | Sidebar with badge counts, header with role badge and email. |
| `layouts/auth.vue` | Bare layout for the login page. |
| `components/*` | `StatusChip`, `DataTable`, `FilterChips`, `PageHeader`, `StatCard`, `EmptyState`, `ConfirmDialog`, `RoleGate`. |
| `pages/*` | The ten pages of Admin UX §3. |

---
## Task 1: Contrast maths in `web/shared`

The token test needs to compute WCAG contrast ratios. Build that first, with tests, because everything downstream trusts it.

**Files:**
- Create: `web/shared/src/contrast.ts`
- Test: `web/shared/src/contrast.test.ts`

- [ ] **Step 1: Write the failing test**

Create `web/shared/src/contrast.test.ts`:

```ts
import { describe, expect, it } from 'vitest'
import { contrastRatio, meetsAA } from './contrast'

describe('contrastRatio', () => {
  it('gives 21:1 for black on white', () => {
    expect(contrastRatio('#000000', '#ffffff')).toBeCloseTo(21, 1)
  })

  it('gives 1:1 for a colour against itself', () => {
    expect(contrastRatio('#4a6b57', '#4a6b57')).toBeCloseTo(1, 5)
  })

  it('is symmetric — order of arguments does not matter', () => {
    const a = contrastRatio('#1f2a24', '#f4f4ee')
    const b = contrastRatio('#f4f4ee', '#1f2a24')
    expect(a).toBeCloseTo(b, 10)
  })

  it('accepts three-digit hex', () => {
    expect(contrastRatio('#000', '#fff')).toBeCloseTo(21, 1)
  })

  it('rejects a malformed hex rather than silently scoring it', () => {
    expect(() => contrastRatio('emerald', '#ffffff')).toThrow(/hex/i)
  })
})

describe('meetsAA', () => {
  it('passes normal text at 4.5:1 or better', () => {
    expect(meetsAA(4.5, 'normal')).toBe(true)
    expect(meetsAA(4.49, 'normal')).toBe(false)
  })

  it('passes large text at 3:1 or better', () => {
    expect(meetsAA(3, 'large')).toBe(true)
    expect(meetsAA(2.99, 'large')).toBe(false)
  })
})
```

- [ ] **Step 2: Run the test and watch it fail**

```bash
npm test --workspace web/shared
```

Expected: fails to resolve `./contrast` — the module does not exist yet.

- [ ] **Step 3: Write the implementation**

Create `web/shared/src/contrast.ts`:

```ts
/**
 * WCAG 2.1 relative luminance and contrast ratio.
 *
 * Used by tokens.test.ts to hold the palette to AA. Both UX specs require AA
 * on every token pair (Chat UX section 13, Admin UX section 17), and the crisis
 * and info states are called out by name — those are exactly the pairs that a
 * designer's eye tends to wave through, so they get asserted instead.
 *
 * Formulae: https://www.w3.org/TR/WCAG21/#dfn-relative-luminance
 */

export type TextSize = 'normal' | 'large'

function parseHex(hex: string): [number, number, number] {
  const match = /^#?([0-9a-f]{3}|[0-9a-f]{6})$/i.exec(hex.trim())
  if (!match) throw new Error(`Not a hex colour: ${hex}`)

  let body = match[1]
  if (body.length === 3) {
    body = body
      .split('')
      .map((c) => c + c)
      .join('')
  }

  return [
    parseInt(body.slice(0, 2), 16),
    parseInt(body.slice(2, 4), 16),
    parseInt(body.slice(4, 6), 16),
  ]
}

function relativeLuminance(hex: string): number {
  const channels = parseHex(hex).map((value) => {
    const c = value / 255
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4
  })

  return 0.2126 * channels[0] + 0.7152 * channels[1] + 0.0722 * channels[2]
}

export function contrastRatio(a: string, b: string): number {
  const la = relativeLuminance(a)
  const lb = relativeLuminance(b)
  const lighter = Math.max(la, lb)
  const darker = Math.min(la, lb)
  return (lighter + 0.05) / (darker + 0.05)
}

/** AA thresholds: 4.5:1 for body text, 3:1 for large text (>=18.66px bold or >=24px). */
export function meetsAA(ratio: number, size: TextSize = 'normal'): boolean {
  return ratio >= (size === 'large' ? 3 : 4.5)
}
```

- [ ] **Step 4: Run the test and watch it pass**

```bash
npm test --workspace web/shared
```

Expected: all `contrast` tests PASS. The existing `word-count` tests must stay green.

- [ ] **Step 5: Commit**

```bash
git add web/shared/src/contrast.ts web/shared/src/contrast.test.ts
git commit -m "feat(shared): add WCAG contrast maths for token verification

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 2: The palette, held to AA by test

Zamrud & Perkamen as data, with a test that fails if any pair drops below AA. Writing the test first is what stops the palette from being tuned by eye.

**Files:**
- Create: `web/shared/src/tokens.ts`
- Test: `web/shared/src/tokens.test.ts`
- Modify: `web/shared/src/index.ts`

- [ ] **Step 1: Write the failing test**

Create `web/shared/src/tokens.test.ts`:

```ts
import { describe, expect, it } from 'vitest'
import { contrastRatio, meetsAA } from './contrast'
import { adminTokens, seekerTokens, type TokenSet } from './tokens'

/**
 * Every pair a user actually reads. Listed explicitly rather than derived,
 * because the point is to state which combinations the design promises are
 * legible — a generated cross-product would also "pass" combinations no screen
 * ever renders.
 */
const seekerPairs: Array<[keyof TokenSet, keyof TokenSet, 'normal' | 'large']> = [
  ['textPrimary', 'bgBase', 'normal'],
  ['textPrimary', 'bgSurface', 'normal'],
  ['textSecondary', 'bgBase', 'normal'],
  ['textSecondary', 'bgSurface', 'normal'],
  ['textOnAccent', 'accentPrimary', 'normal'],
  ['textOnAccent', 'bubbleUser', 'normal'],
  ['textPrimary', 'bubbleAssistant', 'normal'],
  ['accentPrimary', 'bgSurface', 'normal'],
  ['statusWarningText', 'statusWarningBg', 'normal'],
  ['statusInfoText', 'statusInfoBg', 'normal'],
  ['statusCareText', 'statusCareBg', 'normal'],
]

const adminPairs: Array<[keyof TokenSet, keyof TokenSet, 'normal' | 'large']> = [
  ['textPrimary', 'bgBase', 'normal'],
  ['textPrimary', 'bgSurface', 'normal'],
  ['textSecondary', 'bgSurface', 'normal'],
  ['textOnAccent', 'accentPrimary', 'normal'],
  ['accentPrimary', 'bgSurface', 'normal'],
  ['statusSuccessText', 'statusSuccessBg', 'normal'],
  ['statusWarningText', 'statusWarningBg', 'normal'],
  ['statusDangerText', 'statusDangerBg', 'normal'],
  ['statusInfoText', 'statusInfoBg', 'normal'],
]

describe.each([
  ['seeker', seekerTokens, seekerPairs],
  ['admin', adminTokens, adminPairs],
] as const)('%s palette', (_name, tokens, pairs) => {
  it.each(pairs)('%s on %s meets WCAG AA', (fg, bg, size) => {
    const ratio = contrastRatio(tokens[fg]!, tokens[bg]!)
    expect(
      meetsAA(ratio, size),
      `${String(fg)} on ${String(bg)} is ${ratio.toFixed(2)}:1`,
    ).toBe(true)
  })

  it('defines every token as a hex value', () => {
    for (const [name, value] of Object.entries(tokens)) {
      expect(value, `${name} is not a hex colour`).toMatch(/^#[0-9a-f]{6}$/i)
    }
  })
})

describe('crisis state', () => {
  it('does not reuse the danger red — care must not read as error', () => {
    // Chat UX section 8.3: status.care is visually distinct from an error state.
    expect(seekerTokens.statusCareBg).not.toBe(adminTokens.statusDangerBg)
    expect(seekerTokens.statusCareText).not.toBe(adminTokens.statusDangerText)
  })
})
```

- [ ] **Step 2: Run the test and watch it fail**

```bash
npm test --workspace web/shared
```

Expected: fails to resolve `./tokens`.

- [ ] **Step 3: Write the implementation**

Create `web/shared/src/tokens.ts`:

```ts
/**
 * Zamrud & Perkamen — the Tanya Iman palette.
 *
 * Deep emerald on warm parchment. Chosen because the audience is Indonesian
 * Muslim seekers and Chat UX section 4.1 requires a surface that is calm, warm,
 * and unbranded in the religious sense: no crosses, no crescents, no imagery of
 * people. Green carries weight for this readership without belonging to either
 * tradition's iconography.
 *
 * Section 4.1 also names a safety constraint that governs these values: the app
 * must be openable on a bus without announcing anything about its user. Nothing
 * here is loud.
 *
 * This file is the only place a hex value is written. Components reference
 * Tailwind utilities that resolve to CSS variables emitted from these tokens.
 * tokens.test.ts holds every rendered pair to WCAG AA.
 */

export interface TokenSet {
  bgBase: string
  bgSurface: string
  bgRaised: string
  textPrimary: string
  textSecondary: string
  textOnAccent: string
  accentPrimary: string
  accentHover: string
  borderSubtle: string
  borderStrong: string
  bubbleUser?: string
  bubbleAssistant?: string
  statusSuccessText?: string
  statusSuccessBg?: string
  statusWarningText: string
  statusWarningBg: string
  statusDangerText?: string
  statusDangerBg?: string
  statusInfoText: string
  statusInfoBg: string
  statusCareText?: string
  statusCareBg?: string
  statusCareBorder?: string
}

/**
 * Seeker surface: warm, roomy, conversational.
 *
 * statusCare is warm sand with a border rather than red. The crisis card must
 * read as care, not as a failure (Chat UX section 8.3).
 */
export const seekerTokens: TokenSet = {
  bgBase: '#f4f2e9',
  bgSurface: '#fffdf7',
  bgRaised: '#ebe8db',

  textPrimary: '#1b2620',
  textSecondary: '#55645c',
  textOnAccent: '#f7fbf8',

  accentPrimary: '#0f3d2e',
  accentHover: '#175142',

  borderSubtle: '#e0dbc9',
  borderStrong: '#c8c2ac',

  bubbleUser: '#0f3d2e',
  bubbleAssistant: '#fffdf7',

  statusWarningText: '#7c4a12',
  statusWarningBg: '#f8ecd9',

  statusInfoText: '#2f5548',
  statusInfoBg: '#e7efea',

  statusCareText: '#6b4423',
  statusCareBg: '#f9efe0',
  statusCareBorder: '#c9a227',
}

/**
 * Admin surface: same hues, flatter and denser. Admin UX section 4.1 asks for
 * professional and neutral over generous whitespace — this is a tool someone
 * uses for hours.
 */
export const adminTokens: TokenSet = {
  bgBase: '#f6f6f2',
  bgSurface: '#ffffff',
  bgRaised: '#eceae2',

  textPrimary: '#1c231f',
  textSecondary: '#5a655e',
  textOnAccent: '#f7fbf8',

  accentPrimary: '#14503c',
  accentHover: '#1b6249',

  borderSubtle: '#e2e1d8',
  borderStrong: '#c6c5b8',

  statusSuccessText: '#1f5c3a',
  statusSuccessBg: '#e3efe7',

  statusWarningText: '#7c4a12',
  statusWarningBg: '#f8ecd9',

  statusDangerText: '#8f2f26',
  statusDangerBg: '#f8e5e2',

  statusInfoText: '#2f5548',
  statusInfoBg: '#e7efea',
}

/** kebab-case CSS custom property name for a token. `bgBase` -> `--bg-base`. */
export function cssVarName(token: string): string {
  return `--${token.replace(/[A-Z]/g, (c) => `-${c.toLowerCase()}`)}`
}

/** Renders a token set as the body of a CSS `:root` block. */
export function toCssVars(tokens: TokenSet): string {
  return Object.entries(tokens)
    .filter(([, value]) => typeof value === 'string')
    .map(([name, value]) => `  ${cssVarName(name)}: ${value};`)
    .join('\n')
}
```

- [ ] **Step 4: Run the test and watch it pass**

```bash
npm test --workspace web/shared
```

Expected: every contrast assertion PASSES. If a pair fails, adjust that token's lightness in `tokens.ts` until it passes — do not weaken the test.

- [ ] **Step 5: Export from the package index**

Replace `web/shared/src/index.ts` with:

```ts
export * from './client'
export * from './contrast'
export * from './tokens'
export * from './types'
export * from './word-count'
```

- [ ] **Step 6: Typecheck**

```bash
npm run typecheck --workspace web/shared
```

Expected: no errors.

- [ ] **Step 7: Commit**

```bash
git add web/shared/src/tokens.ts web/shared/src/tokens.test.ts web/shared/src/index.ts
git commit -m "feat(shared): add Zamrud & Perkamen design tokens

Palette is held to WCAG AA by test rather than by eye. status.care is
warm sand with a border, deliberately not the danger red — Chat UX 8.3
requires the crisis card to read as care rather than as an error.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---
## Task 3: Wire tokens into the seeker app's Tailwind

Turn the tokens into CSS variables and map Tailwind utilities onto them, so `bg-surface` and `text-primary` become the vocabulary and no component reaches for `emerald-600` again.

**Files:**
- Create: `web/app/assets/css/tokens.css`
- Modify: `web/app/assets/css/tailwind.css`, `web/app/tailwind.config.ts`, `web/app/nuxt.config.ts`

- [ ] **Step 1: Write the token stylesheet**

Create `web/app/assets/css/tokens.css`. These values are copied from `seekerTokens` in `web/shared/src/tokens.ts`; that file is the source of truth and `tokens.test.ts` is what holds them to AA.

```css
/* Zamrud & Perkamen — seeker surface.
   Mirrors seekerTokens in web/shared/src/tokens.ts. Do not edit one without
   the other; the palette is verified by web/shared/src/tokens.test.ts. */
:root {
  --bg-base: #f4f2e9;
  --bg-surface: #fffdf7;
  --bg-raised: #ebe8db;

  --text-primary: #1b2620;
  --text-secondary: #55645c;
  --text-on-accent: #f7fbf8;

  --accent-primary: #0f3d2e;
  --accent-hover: #175142;

  --border-subtle: #e0dbc9;
  --border-strong: #c8c2ac;

  --bubble-user: #0f3d2e;
  --bubble-assistant: #fffdf7;

  --status-warning-text: #7c4a12;
  --status-warning-bg: #f8ecd9;

  --status-info-text: #2f5548;
  --status-info-bg: #e7efea;

  --status-care-text: #6b4423;
  --status-care-bg: #f9efe0;
  --status-care-border: #c9a227;

  /* Elevation — warm-tinted, never neutral black, so shadows sit on parchment
     rather than looking like grey smudges. */
  --shadow-sm: 0 1px 2px rgba(27, 38, 32, 0.06);
  --shadow-md: 0 2px 6px -2px rgba(27, 38, 32, 0.1), 0 8px 20px -12px rgba(27, 38, 32, 0.18);
}
```

- [ ] **Step 2: Update the app stylesheet**

Replace `web/app/assets/css/tailwind.css` with:

```css
@import './tokens.css';

@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  html {
    -webkit-text-size-adjust: 100%;
  }

  /* Indonesian text at conversational length reads poorly at the browser
     default. 15px/1.7 is the body setting used throughout the chat surface. */
  body {
    background: var(--bg-base);
    color: var(--text-primary);
    font-family: var(--font-sans);
    text-rendering: optimizeLegibility;
  }

  /* Chat UX 4.3: headings are the one place the serif appears. It supplies the
     editorial weight the product needs without any religious iconography. */
  h1,
  h2,
  h3 {
    font-family: var(--font-serif);
    font-weight: 500;
    letter-spacing: -0.01em;
  }

  :root {
    --font-sans: 'Inter', ui-sans-serif, system-ui, -apple-system, 'Segoe UI',
      Roboto, sans-serif;
    --font-serif: 'Lora', Georgia, Cambria, 'Times New Roman', serif;
  }

  /* Chat UX 13: the pending animation respects reduced motion. */
  @media (prefers-reduced-motion: reduce) {
    *,
    *::before,
    *::after {
      animation-duration: 0.001ms !important;
      animation-iteration-count: 1 !important;
      transition-duration: 0.001ms !important;
    }
  }
}

@layer components {
  /* Chat UX 4.3: the third type level. Used for the source note, timestamps,
     and citation domains. */
  .meta {
    font-size: 12px;
    line-height: 1.5;
    color: var(--text-secondary);
  }
}
```

- [ ] **Step 3: Map Tailwind onto the variables**

Replace `web/app/tailwind.config.ts` with:

```ts
import type { Config } from 'tailwindcss'

/**
 * Colour utilities resolve to the CSS variables in assets/css/tokens.css, which
 * mirror seekerTokens in web/shared. Components therefore never name a colour —
 * Chat UX section 4.2 requires exactly that, and it is what makes a later dark
 * mode a variable swap rather than a rewrite.
 */
export default {
  content: [
    './components/**/*.{vue,ts}',
    './composables/**/*.ts',
    './pages/**/*.vue',
    './stores/**/*.ts',
    './demo/**/*.ts',
    './app.vue',
  ],
  theme: {
    extend: {
      colors: {
        base: 'var(--bg-base)',
        surface: 'var(--bg-surface)',
        raised: 'var(--bg-raised)',
        primary: 'var(--text-primary)',
        secondary: 'var(--text-secondary)',
        'on-accent': 'var(--text-on-accent)',
        accent: {
          DEFAULT: 'var(--accent-primary)',
          hover: 'var(--accent-hover)',
        },
        subtle: 'var(--border-subtle)',
        strong: 'var(--border-strong)',
        'bubble-user': 'var(--bubble-user)',
        'bubble-assistant': 'var(--bubble-assistant)',
        warning: {
          DEFAULT: 'var(--status-warning-text)',
          bg: 'var(--status-warning-bg)',
        },
        info: {
          DEFAULT: 'var(--status-info-text)',
          bg: 'var(--status-info-bg)',
        },
        care: {
          DEFAULT: 'var(--status-care-text)',
          bg: 'var(--status-care-bg)',
          border: 'var(--status-care-border)',
        },
      },
      fontFamily: {
        sans: 'var(--font-sans)',
        serif: 'var(--font-serif)',
      },
      fontSize: {
        // Conversational Indonesian at default browser size is cramped. The
        // chat surface reads at 15px/1.7 throughout.
        base: ['15px', '1.7'],
      },
      maxWidth: {
        // Chat UX 4.4: measure capped near 65 characters; a full-width
        // conversation on a desktop monitor is unreadable.
        measure: '640px',
      },
      boxShadow: {
        sm: 'var(--shadow-sm)',
        md: 'var(--shadow-md)',
      },
    },
  },
} satisfies Config
```

- [ ] **Step 4: Add the fonts and the demo flag**

In `web/app/nuxt.config.ts`, add `demoMode` inside `runtimeConfig.public`, after the `apiBase` line:

```ts
      apiBase: process.env.NUXT_PUBLIC_API_BASE || 'http://localhost:8000',
      // Set to '1' for the hosted client-approval build: the API client is
      // swapped for fixtures so the static bundle needs no backend.
      demoMode: process.env.NUXT_PUBLIC_DEMO_MODE || '',
```

And in the same file, add a `link` array to `app.head`, after the `meta` array:

```ts
      link: [
        { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
        {
          rel: 'stylesheet',
          href: 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Lora:wght@400;500;600&display=swap',
        },
      ],
```

`display=swap` matters: a blocked font request must never leave a seeker staring at a blank conversation. The stacks in `tailwind.css` name real fallbacks.

- [ ] **Step 5: Verify the app still builds**

```bash
npm run build:app
```

Expected: build succeeds. The existing pages still use `emerald-*`/`slate-*` classes at this point — that is fine, they are replaced in Task 8.

- [ ] **Step 6: Commit**

```bash
git add web/app/assets/css/tokens.css web/app/assets/css/tailwind.css web/app/tailwind.config.ts web/app/nuxt.config.ts
git commit -m "feat(app): wire design tokens into Tailwind

Colour utilities now resolve to CSS variables mirroring seekerTokens, so
components stop naming colours (Chat UX 4.2).

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 4: Demo mode seam

One composable decides whether demo mode is on, and `useApi` swaps the client. Nothing else in the app learns about it.

**Files:**
- Create: `web/app/composables/useDemoMode.ts`
- Modify: `web/app/composables/useApi.ts`

- [ ] **Step 1: Write the flag composable**

Create `web/app/composables/useDemoMode.ts`:

```ts
/**
 * Demo mode backs the hosted client-approval build with fixtures instead of a
 * backend, so the static bundle can be deployed and reviewed before Phase 5
 * exists.
 *
 * One place reads the flag. Components ask this, never the runtime config, so
 * removing demo mode later is a matter of deleting this file and its callers.
 */
export function useDemoMode(): boolean {
  return useRuntimeConfig().public.demoMode === '1'
}
```

- [ ] **Step 2: Swap the client at the seam**

Replace `web/app/composables/useApi.ts` with:

```ts
import { createClient, type ApiClient } from '@tanya-iman/shared'
import { useAuthStore } from '~/stores/auth'
import { createDemoClient } from '~/composables/useDemoClient'

let client: ApiClient | null = null

export function useApi(): ApiClient {
  if (!client) {
    const config = useRuntimeConfig()

    // The demo client implements the same ApiClient interface, so the swap is
    // invisible to every store, page, and component downstream.
    if (useDemoMode()) {
      client = createDemoClient()
      return client
    }

    const auth = useAuthStore()
    // Resolved per request rather than captured once: Firebase ID tokens
    // expire after an hour and a seeker may well sit on one conversation
    // longer than that.
    client = createClient({
      baseUrl: config.public.apiBase,
      getToken: () => auth.getIdToken(),
    })
  }
  return client
}
```

- [ ] **Step 3: Commit**

The app will not typecheck until Task 5 creates `useDemoClient`. Commit both together at the end of Task 5 instead — skip this step and continue.

---

## Task 5: Demo fixtures and the demo client

The sample content, and an `ApiClient` that serves it. This is the file Phase 5 deletes.

**Files:**
- Create: `web/app/demo/scenarios.ts`, `web/app/composables/useDemoClient.ts`

- [ ] **Step 1: Write the scenarios**

Create `web/app/demo/scenarios.ts`:

```ts
import type { AnswerSource, Citation } from '@tanya-iman/shared'

/**
 * Sample content for the hosted approval build.
 *
 * DEMO CONTENT — NOT EDITORIALLY APPROVED. These answer bodies were written to
 * demonstrate layout, tone, and citation rendering. They are not the product's
 * answers; Phase 5 produces those from the corpus, and the editorial team
 * approves prompts and refusal copy under SOW dependencies B2 and B8.
 *
 * Template strings (greeting, refusal, no-grounding, rate limit, error) are NOT
 * written here — they come from locales/id.json, which is byte-identical to
 * backend/config/responses.id.yml and asserted by test_copy_parity.py.
 *
 * The crisis scenario deliberately carries no real helpline number. The crisis
 * script is owned by the client's pastoral staff (SOW B1) and is unapproved.
 */

export interface DemoScenario {
  /** Shown in the demo scenario bar. */
  label: string
  question: string
  answerSource: AnswerSource
  /** Omitted for template-driven states, which read their copy from id.json. */
  answerText?: string
  citations: Citation[]
  /** Only for the rate-limit scenario. */
  retryAfterSeconds?: number
}

const ISA_DAN_ISLAM = 'isadanislam.org'
const ISA_DAN_ALQURAN = 'isadanalquran.com'
const ISA_DAN_ALFATIHAH = 'isadanalfatihah.com'
const KAUM_WANITA = 'isaislamdankaumwanita.com'
const TAKUT_NERAKA = 'takutneraka.com'

export const scenarios: DemoScenario[] = [
  {
    label: 'Jawaban tersusun',
    question: 'Siapakah Isa Al-Masih menurut Kitab Suci?',
    answerSource: 'generated',
    answerText:
      'Kitab Suci memperkenalkan Isa Al-Masih sebagai Firman Allah yang menjadi manusia. Ia disebut telah ada sejak semula bersama Allah, lalu hadir di tengah manusia untuk menyatakan kasih dan kebenaran-Nya.\n\nDalam Injil, Isa Al-Masih berkata bahwa Ia datang bukan untuk menghakimi dunia, melainkan supaya dunia diselamatkan melalui Dia. Karena itu Ia dikenal bukan hanya sebagai nabi yang mengajar, tetapi sebagai jalan yang membawa manusia kembali kepada Allah.\n\nBagi banyak orang, yang paling menyentuh bukanlah mukjizat-Nya, melainkan kesediaan-Nya menerima orang yang merasa jauh dan tidak layak. Anda dipersilakan menelusuri sendiri bacaan di bawah ini.',
    citations: [
      {
        title: 'Siapakah Isa Al-Masih dalam Injil?',
        url: `https://${ISA_DAN_ISLAM}/siapakah-isa-al-masih/`,
        site: ISA_DAN_ISLAM,
      },
      {
        title: 'Firman yang Menjadi Manusia',
        url: `https://${ISA_DAN_ALQURAN}/firman-yang-menjadi-manusia/`,
        site: ISA_DAN_ALQURAN,
      },
    ],
  },
  {
    label: 'Jawaban kurasi',
    question: 'Apakah Allah mengampuni dosa yang sudah berulang kali saya lakukan?',
    answerSource: 'curated',
    answerText:
      'Kitab Suci berbicara tentang pengampunan yang tidak diukur dari seberapa sering seseorang jatuh. Ketika ditanya berapa kali seseorang harus mengampuni, Isa Al-Masih menjawab dengan angka yang jauh melampaui hitungan — maksudnya, pengampunan tidak dibatasi jumlah.\n\nDikatakan pula bahwa jika kita mengakui dosa kita, Allah setia dan adil untuk mengampuni serta membersihkan kita. Yang diminta bukan kesempurnaan lebih dahulu, melainkan kejujuran.\n\nBanyak orang merasa dosa yang berulang membuat mereka kehilangan hak untuk kembali. Bacaan berikut menjawab kekhawatiran itu secara langsung.',
    citations: [
      {
        title: 'Pengampunan yang Tidak Terbatas',
        url: `https://${ISA_DAN_ALFATIHAH}/pengampunan-yang-tidak-terbatas/`,
        site: ISA_DAN_ALFATIHAH,
      },
    ],
  },
  {
    label: 'Di luar cakupan',
    question: 'Tolong buatkan saya kode Python untuk mengurutkan daftar.',
    answerSource: 'refusal',
    citations: [],
  },
  {
    label: 'Tanpa dasar',
    question: 'Bagaimana pandangan Kitab Suci tentang penambangan aset kripto?',
    answerSource: 'no_grounding',
    citations: [],
  },
  {
    label: 'Tanggapan kepedulian',
    question: 'Saya merasa tidak sanggup lagi menjalani hidup ini.',
    answerSource: 'crisis',
    citations: [],
  },
  {
    label: 'Gangguan',
    question: 'Apa arti kasih karunia?',
    answerSource: 'error',
    citations: [],
  },
  {
    label: 'Batas pertanyaan',
    question: 'Apakah surga itu nyata?',
    answerSource: 'error',
    retryAfterSeconds: 20 * 60,
    citations: [],
  },
  {
    label: 'Pertanyaan perempuan',
    question: 'Bagaimana Isa Al-Masih memperlakukan perempuan?',
    answerSource: 'generated',
    answerText:
      'Catatan Injil menunjukkan sikap yang tidak lazim pada zamannya. Isa Al-Masih berbicara langsung dengan perempuan di ruang publik, menerima mereka sebagai murid yang belajar, dan membela mereka yang hendak dihukum orang banyak.\n\nKetika seorang perempuan dipermalukan di hadapan umum, Ia tidak ikut menghakimi, melainkan menantang para penuduhnya untuk memeriksa diri sendiri lebih dahulu. Kepada perempuan itu Ia berkata bahwa Ia pun tidak menghukumnya.\n\nBagi banyak pembaca perempuan, bagian inilah yang paling mengejutkan: martabat mereka tidak perlu diperjuangkan, sebab sudah lebih dahulu diakui.',
    citations: [
      {
        title: 'Perempuan dalam Pandangan Isa Al-Masih',
        url: `https://${KAUM_WANITA}/perempuan-dalam-pandangan-isa/`,
        site: KAUM_WANITA,
      },
      {
        title: 'Ia Tidak Menghukum',
        url: `https://${TAKUT_NERAKA}/ia-tidak-menghukum/`,
        site: TAKUT_NERAKA,
      },
    ],
  },
]

/** The scenario served when a question does not match any other. */
export const defaultScenario = scenarios[0]

/** Naive keyword routing — good enough to make the demo feel responsive. */
export function pickScenario(question: string): DemoScenario {
  const q = question.toLowerCase()

  if (/(bunuh diri|mengakhiri hidup|tidak sanggup|ingin mati|putus asa)/.test(q)) {
    return scenarios.find((s) => s.answerSource === 'crisis')!
  }
  if (/(kode|python|javascript|resep|cuaca|sepak bola)/.test(q)) {
    return scenarios.find((s) => s.answerSource === 'refusal')!
  }
  if (/(kripto|bitcoin|saham|investasi)/.test(q)) {
    return scenarios.find((s) => s.answerSource === 'no_grounding')!
  }
  if (/(perempuan|wanita|istri)/.test(q)) {
    return scenarios.find((s) => s.label === 'Pertanyaan perempuan')!
  }
  if (/(ampun|dosa|bertobat)/.test(q)) {
    return scenarios.find((s) => s.answerSource === 'curated')!
  }
  return defaultScenario
}
```

- [ ] **Step 2: Write the demo client**

Create `web/app/composables/useDemoClient.ts`:

```ts
import {
  ApiError,
  isLikeable,
  type ApiClient,
  type AskRequest,
  type AskResponse,
  type CreateSessionRequest,
  type CreateSessionResponse,
  type HealthResponse,
  type LikeResponse,
} from '@tanya-iman/shared'
import { pickScenario, type DemoScenario } from '~/demo/scenarios'

/**
 * A fixture-backed ApiClient for the hosted approval build.
 *
 * Deleted in Phase 5 along with demo/scenarios.ts and useDemoMode.ts — this is
 * the entire footprint of demo mode outside those two files.
 *
 * It reproduces the behaviours the UI has to handle, not just the happy path:
 * a realistic delay so the pending state is visible, a 429 that carries
 * Retry-After so the countdown has something to count, and a thrown error so
 * the retry affordance can be exercised.
 */

/** Long enough that the pending state is visibly real, short enough to demo. */
const LATENCY_MS = 1400

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

let counter = 0

/** Overridden by the scenario bar so a reviewer can force any state. */
let forced: DemoScenario | null = null

export function forceScenario(scenario: DemoScenario | null): void {
  forced = scenario
}

export function createDemoClient(): ApiClient {
  const likes = new Map<string, boolean>()

  return {
    health: async (): Promise<HealthResponse> => ({
      status: 'ok',
      env: 'demo',
      prompt_version: 'demo',
      corpus_chunk_count: 0,
      engine: 'demo',
    }),

    createSession: async (
      _payload: CreateSessionRequest,
    ): Promise<CreateSessionResponse> => {
      await delay(150)
      return { session_id: `demo_session_${Date.now()}` }
    },

    ask: async (payload: AskRequest): Promise<AskResponse> => {
      await delay(LATENCY_MS)

      const scenario = forced ?? pickScenario(payload.text)

      // Rate limit is an HTTP condition, not an answer_source, so it has to be
      // thrown rather than returned — the store branches on ApiError.
      if (scenario.retryAfterSeconds) {
        throw new ApiError(
          429,
          'rate limited',
          scenario.retryAfterSeconds,
        )
      }

      if (scenario.answerSource === 'error') {
        throw new ApiError(503, 'demo failure')
      }

      counter += 1
      return {
        question_id: `demo_q_${counter}`,
        answer_source: scenario.answerSource,
        // Template states render copy from id.json, so the body is empty here
        // and the component selects on answer_source.
        answer_text: scenario.answerText ?? '',
        citations: scenario.citations,
        topic_slug: null,
        likeable: isLikeable(scenario.answerSource),
        latency_ms: LATENCY_MS,
      }
    },

    like: async (questionId: string, liked: boolean): Promise<LikeResponse> => {
      await delay(200)
      likes.set(questionId, liked)
      return { question_id: questionId, liked, like_count: liked ? 1 : 0 }
    },
  }
}
```

- [ ] **Step 3: Typecheck**

```bash
npm run typecheck --workspace web/app
```

Expected: no errors. If `~/demo/scenarios` does not resolve, confirm `./demo/**/*.ts` is in the `content` array of `tailwind.config.ts` and that the path alias is the default Nuxt `~`.

- [ ] **Step 4: Commit**

```bash
git add web/app/composables/useDemoMode.ts web/app/composables/useDemoClient.ts web/app/composables/useApi.ts web/app/demo/scenarios.ts
git commit -m "feat(app): add fixture-backed demo mode

Swaps the API client at the useApi seam so the static approval build
needs no backend. Sample answers are labelled demo content; no crisis
script or helpline number is introduced (SOW B1).

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---
## Task 6: Carry `answerSource` and retry through the chat store

Chat UX section 8 requires the frontend to select rendering on `answer_source` and `likeable` from the API, never to reimplement a business rule. The store currently discards `answer_source`, so no component can do that. It also has no retry, which F-27 requires.

**Files:**
- Modify: `web/app/stores/chat.ts`
- Modify: `web/app/locales/id.json`

- [ ] **Step 1: Add the new copy keys**

In `web/app/locales/id.json`, inside the `ui` object, add these keys after `"retry": "Coba lagi",`:

```json
    "still_working": "Masih menyiapkan jawaban…",
    "new_messages": "Pesan baru",
    "rate_limited_in": "Silakan coba lagi dalam {time}",
    "menu": "Menu",
    "back": "Kembali",
    "demo_banner": "Pratinjau desain — jawaban contoh, bukan jawaban resmi.",
    "demo_scenario": "Skenario",
    "crisis_demo_note": "Nomor bantuan pada contoh ini belum final dan menunggu persetujuan tim pastoral."
```

Do not touch anything under `shared` — `backend/tests/test_copy_parity.py` asserts those strings byte-for-byte against `backend/config/responses.id.yml`.

- [ ] **Step 2: Extend the Message type and capture answerSource**

In `web/app/stores/chat.ts`, replace the `Message` interface with:

```ts
export interface Message {
  id: string
  role: 'seeker' | 'iman'
  text: string
  citations?: Citation[]
  /** Absent on seeker messages and on system copy. */
  questionId?: string
  likeable?: boolean
  liked?: boolean
  pending?: boolean
  /**
   * Drives which bubble treatment renders (Chat UX section 8). The frontend
   * selects on this and on `likeable`; it never re-derives either.
   */
  answerSource?: AnswerSource
  /** Set on a rate-limited turn. Seconds remaining, counted down live. */
  retryAfterSeconds?: number
  /** The seeker text that produced a failed turn, so Coba lagi can resend it. */
  failedQuestion?: string
}
```

Update the import at the top of the file to include `AnswerSource`:

```ts
import { ApiError, type AnswerSource, type AskResponse, type Citation } from '@tanya-iman/shared'
```

- [ ] **Step 3: Record answerSource on success**

In the `ask` function, replace the `replacePending` call in the `try` block with:

```ts
      replacePending(placeholderId, {
        id: response.question_id,
        role: 'iman',
        text: response.answer_text,
        citations: response.citations,
        questionId: response.question_id,
        likeable: response.likeable,
        liked: false,
        answerSource: response.answer_source,
      })
```

- [ ] **Step 4: Tag the error states so they render distinctly**

Replace the whole `handleAskError` function with:

```ts
  function handleAskError(err: unknown, placeholderId: string, question: string) {
    // Rate limits and expired sessions are ordinary outcomes, not faults, and
    // are shown as a message in the conversation rather than as an error
    // banner. Getting told "you have asked a lot today, come back in 20
    // minutes" should not feel like the app broke.
    if (err instanceof ApiError && err.isRateLimited) {
      replacePending(placeholderId, {
        id: placeholderId,
        role: 'iman',
        text: '',
        answerSource: 'rate_limited',
        retryAfterSeconds: err.retryAfterSeconds ?? 60 * 60,
        failedQuestion: question,
      })
      return
    }

    if (err instanceof ApiError && err.isSessionGone) {
      sessionId.value = null
      replacePending(placeholderId, {
        id: placeholderId,
        role: 'iman',
        text: t('ui.session_expired'),
        answerSource: 'error',
        failedQuestion: question,
      })
      return
    }

    replacePending(placeholderId, {
      id: placeholderId,
      role: 'iman',
      text: '',
      answerSource: 'error',
      failedQuestion: question,
    })
  }
```

Note the removed `error.value = t('ui.network_error')`. The failure is now visible inside the conversation with its own retry, so a separate banner would say the same thing twice.

Update the single call site in `ask`'s `catch` block to pass the question:

```ts
    } catch (err) {
      handleAskError(err, placeholderId, trimmed)
    } finally {
```

- [ ] **Step 5: Add the rate-limited source to the shared type**

`rate_limited` is a rendering state, not a backend `answer_source` — the backend signals it with HTTP 429. Add it as a frontend-only widening in `web/app/stores/chat.ts`, directly above the `Message` interface:

```ts
/**
 * The backend's AnswerSource plus the one state that arrives as an HTTP status
 * rather than as a field. Chat UX section 8 lists rate-limited alongside the
 * answer sources because it is a bubble the seeker sees, but the wire type in
 * web/shared mirrors backend/models/schemas.py and must not gain a member the
 * backend never sends.
 */
type MessageSource = AnswerSource | 'rate_limited'
```

Then change the `answerSource` field in `Message` to use it:

```ts
  answerSource?: MessageSource
```

- [ ] **Step 6: Add retry**

Add this function inside the store, after `toggleLike`:

```ts
  /**
   * F-27: the failed question stays in the transcript and Coba lagi resends
   * the identical text. The seeker never retypes.
   */
  async function retry(messageId: string) {
    const index = messages.value.findIndex((m) => m.id === messageId)
    if (index < 0) return

    const question = messages.value[index].failedQuestion
    if (!question) return

    // Drop the failed answer bubble and the seeker bubble above it, then ask
    // again — otherwise the transcript accumulates a copy of the question per
    // attempt.
    const removeFrom = index > 0 && messages.value[index - 1].role === 'seeker' ? index - 1 : index
    messages.value.splice(removeFrom)

    await ask(question)
  }
```

Add `retry` to the returned object:

```ts
  return { messages, sessionId, sending, error, start, ask, toggleLike, retry, reset }
```

- [ ] **Step 7: Typecheck**

```bash
npm run typecheck --workspace web/app
```

Expected: no errors.

- [ ] **Step 8: Commit**

```bash
git add web/app/stores/chat.ts web/app/locales/id.json
git commit -m "feat(app): carry answer_source and add retry to the chat store

Chat UX 8 has the frontend select rendering on answer_source and
likeable from the API; the store was discarding answer_source so no
component could. Adds F-27 retry that resends without retyping.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 7: Seeker presentation components

Five small components, each with one job. Splitting them out is what keeps `MessageBubble` readable once it has to render seven states.

**Files:**
- Create: `web/app/components/CitationList.vue`, `LikeControl.vue`, `PendingBubble.vue`, `AnswerStates.vue`, `AppShell.vue`

- [ ] **Step 1: CitationList**

Create `web/app/components/CitationList.vue`:

```vue
<script setup lang="ts">
import type { Citation } from '@tanya-iman/shared'

/**
 * Chat UX section 9. The article title is the link text and the domain sits
 * beneath it in Meta type, so a seeker can see where a tap will send them
 * before they take it. Never a bare URL.
 */
defineProps<{ citations: Citation[] }>()

const { t } = useCopy()

/**
 * Links open in a new tab on web and in the external browser on Android.
 * Inside the widget they must escape the iframe — a citation that opens in a
 * 620px-tall frame strands the reader (Chat UX section 11).
 */
const { platform } = usePlatform()
const target = platform === 'widget' ? '_top' : '_blank'
</script>

<template>
  <div v-if="citations.length" class="mt-4 border-t border-subtle pt-3">
    <p class="meta mb-2">{{ t('ui.answer_sources') }}</p>
    <ul class="space-y-2.5">
      <li v-for="citation in citations" :key="citation.url" class="flex gap-2">
        <span aria-hidden="true" class="mt-0.5 shrink-0 text-secondary">&#128196;</span>
        <span class="min-w-0">
          <a
            :href="citation.url"
            :target="target"
            rel="noopener noreferrer"
            class="block text-[14px] leading-snug text-accent underline decoration-subtle underline-offset-2 hover:decoration-accent"
          >
            {{ citation.title }}
          </a>
          <span class="meta block">{{ citation.site }}</span>
        </span>
      </li>
    </ul>
  </div>
</template>
```

- [ ] **Step 2: LikeControl**

Create `web/app/components/LikeControl.vue`:

```vue
<script setup lang="ts">
/**
 * Chat UX section 10. One heart, optimistic, reversible (F-33), and no count —
 * a visible count would turn an unpopular answer into a less believable one,
 * which is the opposite of what the signal is for. Editorial reads the counts
 * in the admin portal instead.
 */
defineProps<{ liked: boolean }>()
defineEmits<{ toggle: [] }>()

const { t } = useCopy()
</script>

<template>
  <button
    type="button"
    class="mt-3 flex min-h-[44px] items-center gap-1.5 text-[13px] text-secondary transition hover:text-accent"
    :aria-pressed="liked"
    :aria-label="liked ? t('ui.answer_liked') : t('ui.answer_like')"
    @click="$emit('toggle')"
  >
    <span aria-hidden="true" class="text-[15px]">{{ liked ? '♥' : '♡' }}</span>
    <span>{{ liked ? t('ui.answer_liked') : t('ui.answer_like') }}</span>
  </button>
</template>
```

- [ ] **Step 3: PendingBubble**

Create `web/app/components/PendingBubble.vue`:

```vue
<script setup lang="ts">
/**
 * Chat UX section 8.1. The pending bubble appears immediately on send and is
 * replaced in place — it never vanishes without something taking its spot.
 *
 * Past 8 seconds a Meta line appears. It is honest, and it is what stops a
 * seeker from resending the same question three times.
 */
const { t } = useCopy()

const SLOW_AFTER_MS = 8000
const slow = ref(false)
let timer: ReturnType<typeof setTimeout> | undefined

onMounted(() => {
  timer = setTimeout(() => (slow.value = true), SLOW_AFTER_MS)
})

onUnmounted(() => {
  if (timer) clearTimeout(timer)
})
</script>

<template>
  <div>
    <p class="flex gap-1.5 py-1" aria-live="polite">
      <span class="sr-only">{{ t('ui.composer_thinking') }}</span>
      <span
        v-for="i in 3"
        :key="i"
        class="h-2 w-2 animate-bounce rounded-full bg-strong"
        :style="{ animationDelay: `${(i - 1) * 0.15}s` }"
      />
    </p>
    <p v-if="slow" class="meta mt-1.5">{{ t('ui.still_working') }}</p>
  </div>
</template>
```

- [ ] **Step 4: AnswerStates**

Create `web/app/components/AnswerStates.vue`:

```vue
<script setup lang="ts">
import type { Message } from '~/stores/chat'

/**
 * The non-standard response states (Chat UX section 8).
 *
 * Each is distinguishable without colour — the copy and the layout differ, not
 * only the tint (section 13). The crisis state is a card with no bubble tail,
 * wider padding, and a border, so it does not read as one more reply.
 */
const props = defineProps<{ message: Message }>()
defineEmits<{ retry: [id: string] }>()

const { t } = useCopy()

const remaining = ref(props.message.retryAfterSeconds ?? 0)
let ticker: ReturnType<typeof setInterval> | undefined

onMounted(() => {
  if (props.message.answerSource !== 'rate_limited') return
  // Section 8.4: the countdown ticks live and resolves without a reload.
  ticker = setInterval(() => {
    remaining.value = Math.max(0, remaining.value - 1)
    if (remaining.value === 0 && ticker) clearInterval(ticker)
  }, 1000)
})

onUnmounted(() => {
  if (ticker) clearInterval(ticker)
})

const countdown = computed(() => {
  const minutes = Math.floor(remaining.value / 60)
  const seconds = remaining.value % 60
  return minutes > 0
    ? `${minutes} menit ${String(seconds).padStart(2, '0')} detik`
    : `${seconds} detik`
})
</script>

<template>
  <!-- Refusal and no-grounding: informational, no icon, no citations, no like. -->
  <div
    v-if="message.answerSource === 'refusal' || message.answerSource === 'no_grounding'"
    class="rounded-2xl rounded-bl-md bg-info-bg px-4 py-3.5 text-[15px] leading-relaxed text-info"
  >
    <p class="whitespace-pre-wrap">
      {{ message.answerSource === 'refusal' ? t('shared.refusal') : t('shared.no_grounding') }}
    </p>
  </div>

  <!-- Crisis: a card, not a reply. No scripture, no citations, no like. -->
  <div
    v-else-if="message.answerSource === 'crisis'"
    class="rounded-2xl border-l-4 bg-care-bg px-5 py-4 text-[15px] leading-relaxed text-care"
    style="border-left-color: var(--status-care-border)"
    role="note"
  >
    <p class="whitespace-pre-wrap">{{ message.text }}</p>
    <!-- The real script and its verified helpline numbers are owned by the
         client's pastoral team (SOW B1) and are not shipped here. -->
    <p class="meta mt-3 italic">{{ t('ui.crisis_demo_note') }}</p>
  </div>

  <!-- Rate limited: a live countdown, resolving on its own. -->
  <div
    v-else-if="message.answerSource === 'rate_limited'"
    class="rounded-2xl rounded-bl-md bg-warning-bg px-4 py-3.5 text-[15px] leading-relaxed text-warning"
  >
    <p>{{ t('shared.rate_limit', { minutes: Math.ceil(remaining / 60) }) }}</p>
    <p v-if="remaining > 0" class="meta mt-1.5">
      {{ t('ui.rate_limited_in', { time: countdown }) }}
    </p>
  </div>

  <!-- Error: the one state with an action. -->
  <div
    v-else
    class="rounded-2xl rounded-bl-md bg-warning-bg px-4 py-3.5 text-[15px] leading-relaxed text-warning"
  >
    <p>{{ message.text || t('shared.error') }}</p>
    <button
      v-if="message.failedQuestion"
      type="button"
      class="mt-2 min-h-[44px] font-medium underline underline-offset-2"
      @click="$emit('retry', message.id)"
    >
      {{ t('ui.retry') }}
    </button>
  </div>
</template>
```

- [ ] **Step 5: AppShell**

Create `web/app/components/AppShell.vue`:

```vue
<script setup lang="ts">
/**
 * Header, persistent source note, and the footer privacy link.
 *
 * In embed mode the header and the outer background are suppressed, but the
 * source note and the privacy link stay: F-4 and F-6 apply inside the widget
 * exactly as they do in the app (Chat UX section 11).
 */
defineProps<{ embed?: boolean }>()

const { t } = useCopy()
const auth = useAuthStore()
const chat = useChatStore()
const router = useRouter()

const menuOpen = ref(false)

async function signOut() {
  menuOpen.value = false
  chat.reset()
  await auth.signOut()
  await router.push('/')
}
</script>

<template>
  <div :class="['flex h-dvh flex-col', embed ? 'bg-surface' : 'bg-base']">
    <header
      v-if="!embed"
      class="flex items-center justify-between border-b border-subtle bg-surface px-4 py-3"
    >
      <h1 class="font-serif text-[17px] text-primary">{{ t('ui.app_name') }}</h1>

      <div class="relative">
        <button
          type="button"
          class="grid h-11 w-11 place-items-center rounded-lg text-secondary transition hover:bg-raised"
          :aria-label="t('ui.menu')"
          :aria-expanded="menuOpen"
          @click="menuOpen = !menuOpen"
        >
          <span aria-hidden="true" class="text-lg leading-none">&#8942;</span>
        </button>

        <div
          v-if="menuOpen"
          class="absolute right-0 top-12 z-20 w-56 overflow-hidden rounded-xl border border-subtle bg-surface shadow-md"
        >
          <NuxtLink
            to="/privasi"
            class="block px-4 py-3 text-[14px] text-primary hover:bg-raised"
            @click="menuOpen = false"
          >
            {{ t('ui.privacy') }}
          </NuxtLink>
          <button
            type="button"
            class="block w-full px-4 py-3 text-left text-[14px] text-primary hover:bg-raised"
            @click="signOut"
          >
            {{ t('ui.logout') }}
          </button>
        </div>
      </div>
    </header>

    <!-- F-6: persistent, not dismissible, does not scroll away. -->
    <p class="meta border-b border-subtle bg-raised px-4 py-2">
      {{ t('shared.source_note') }}
    </p>

    <slot />

    <!-- F-4: reachable from every screen, including inside the widget. -->
    <footer class="border-t border-subtle bg-surface px-4 py-2 text-center">
      <NuxtLink
        to="/privasi"
        class="meta inline-flex min-h-[44px] items-center underline underline-offset-2"
      >
        {{ t('ui.privacy') }}
      </NuxtLink>
    </footer>
  </div>
</template>
```

- [ ] **Step 6: Typecheck**

```bash
npm run typecheck --workspace web/app
```

Expected: no errors. `signOut` already exists on the auth store (`web/app/stores/auth.ts`), so the call is direct.

- [ ] **Step 7: Commit**

```bash
git add web/app/components/CitationList.vue web/app/components/LikeControl.vue web/app/components/PendingBubble.vue web/app/components/AnswerStates.vue web/app/components/AppShell.vue
git commit -m "feat(app): add seeker presentation components

Citations, like, pending, the non-standard response states, and the
shell. Each response state differs in copy and layout, not only tint,
so they stay distinguishable without colour (Chat UX 13).

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---
## Task 8: Rebuild MessageBubble and Composer on tokens

Both components currently name Tailwind palette colours directly, which Chat UX section 4.2 forbids. Rebuild them on tokens and delegate the parts now owned by Task 7's components.

**Files:**
- Modify: `web/app/components/MessageBubble.vue`, `web/app/components/Composer.vue`

- [ ] **Step 1: Rewrite MessageBubble**

Replace `web/app/components/MessageBubble.vue` entirely with:

```vue
<script setup lang="ts">
import type { Message } from '~/stores/chat'

/**
 * Selects a treatment on answer_source (Chat UX section 8) and hands the
 * non-standard states to AnswerStates. A curated answer renders identically to
 * a generated one — deliberately. The seeker is never told which they got.
 */
const props = defineProps<{ message: Message }>()
defineEmits<{ like: [questionId: string]; retry: [id: string] }>()

const isSeeker = computed(() => props.message.role === 'seeker')

const STANDARD: Array<string | undefined> = ['generated', 'curated', undefined]
const isStandard = computed(
  () => !props.message.pending && STANDARD.includes(props.message.answerSource),
)
</script>

<template>
  <div :class="['flex w-full', isSeeker ? 'justify-end' : 'justify-start']">
    <!-- Seeker's own message. -->
    <div
      v-if="isSeeker"
      class="max-w-[85%] rounded-2xl rounded-br-md bg-bubble-user px-4 py-3 text-[15px] leading-relaxed text-on-accent"
    >
      <p class="whitespace-pre-wrap">{{ message.text }}</p>
    </div>

    <!-- Pending. -->
    <div
      v-else-if="message.pending"
      class="max-w-[90%] rounded-2xl rounded-bl-md border border-subtle bg-bubble-assistant px-4 py-3 shadow-sm"
    >
      <PendingBubble />
    </div>

    <!-- Standard answer: generated or curated, rendered the same way. -->
    <div
      v-else-if="isStandard"
      class="max-w-[90%] rounded-2xl rounded-bl-md border border-subtle bg-bubble-assistant px-4 py-3.5 text-[15px] leading-relaxed text-primary shadow-sm"
    >
      <p class="whitespace-pre-wrap">{{ message.text }}</p>

      <CitationList v-if="message.citations?.length" :citations="message.citations" />

      <LikeControl
        v-if="message.likeable && message.questionId"
        :liked="Boolean(message.liked)"
        @toggle="$emit('like', message.questionId!)"
      />
    </div>

    <!-- Refusal, no-grounding, crisis, rate limit, error. -->
    <div v-else class="max-w-[90%]">
      <AnswerStates :message="message" @retry="$emit('retry', $event)" />
    </div>
  </div>
</template>
```

- [ ] **Step 2: Rewrite Composer**

Replace `web/app/components/Composer.vue` entirely with:

```vue
<script setup lang="ts">
/**
 * Chat UX section 7.4.
 *
 * Send is disabled while a request is in flight but the textarea stays
 * editable, so a seeker can compose their next question while waiting (F-26).
 * That is why `disabled` gates the button and not the field.
 */
const props = defineProps<{ disabled?: boolean }>()
const emit = defineEmits<{ submit: [text: string] }>()

const { t } = useCopy()
const MAX_CHARS = 1000 // mirrors MAX_QUESTION_CHARS in backend settings
const COUNTER_FROM = 800 // section 7.4: the counter appears only past 800

const text = ref('')
const textarea = ref<HTMLTextAreaElement | null>(null)

const tooLong = computed(() => text.value.length > MAX_CHARS)
const showCounter = computed(() => text.value.length >= COUNTER_FROM)
const canSend = computed(
  () => !props.disabled && text.value.trim().length > 0 && !tooLong.value,
)

/**
 * Enter sends on a physical keyboard; on touch it inserts a newline and the
 * send button is the only way to submit. The opposite convention loses people
 * mid-sentence (section 7.4).
 */
const isTouch = ref(false)
onMounted(() => {
  isTouch.value = window.matchMedia('(pointer: coarse)').matches
})

function submit() {
  if (!canSend.value) return
  emit('submit', text.value)
  text.value = ''
  resize()
}

function onKeydown(event: KeyboardEvent) {
  if (event.key !== 'Enter' || event.shiftKey || isTouch.value) return
  event.preventDefault()
  submit()
}

function resize() {
  const el = textarea.value
  if (!el) return
  el.style.height = 'auto'
  // 1 to 5 lines, then the textarea scrolls internally.
  el.style.height = `${Math.min(el.scrollHeight, 150)}px`
}
</script>

<template>
  <form
    class="flex items-end gap-2 border-t border-subtle bg-surface p-3 pb-[max(0.75rem,env(safe-area-inset-bottom))]"
    @submit.prevent="submit"
  >
    <div class="flex-1">
      <textarea
        ref="textarea"
        v-model="text"
        rows="1"
        :placeholder="t('ui.composer_placeholder')"
        :aria-label="t('ui.composer_placeholder')"
        class="w-full resize-none rounded-xl border border-strong bg-surface px-3 py-2.5 text-[15px] leading-relaxed text-primary outline-none transition placeholder:text-secondary focus:border-accent focus:ring-2 focus:ring-accent/15"
        @input="resize"
        @keydown="onKeydown"
      />
      <p
        v-if="showCounter"
        :class="['mt-1 text-right text-[12px]', tooLong ? 'text-warning' : 'text-secondary']"
      >
        {{ t('ui.composer_counter', { count: text.length }) }}
      </p>
    </div>

    <button
      type="submit"
      :disabled="!canSend"
      class="mb-0.5 min-h-[44px] shrink-0 rounded-xl bg-accent px-4 py-2.5 text-[14px] font-medium text-on-accent transition hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-40"
    >
      {{ t('ui.composer_send') }}
    </button>
  </form>
</template>
```

- [ ] **Step 3: Verify no palette colours remain**

```bash
grep -rnE "(emerald|slate|red|gray|zinc|neutral)-[0-9]{2,3}" web/app/components web/app/pages
```

Expected: no output for `components`. `pages` still has matches until Task 9 — that is fine.

- [ ] **Step 4: Commit**

```bash
git add web/app/components/MessageBubble.vue web/app/components/Composer.vue
git commit -m "refactor(app): rebuild bubble and composer on design tokens

Also fixes two spec deviations: the textarea now stays editable while a
request is in flight (F-26), and Enter no longer submits on touch
keyboards (Chat UX 7.4).

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 9: Seeker pages

Welcome, sign-in, chat, privacy — the four routes of Chat UX section 3.

**Files:**
- Modify: `web/app/pages/index.vue`, `web/app/pages/chat.vue`
- Create: `web/app/pages/masuk.vue`, `web/app/pages/privasi.vue`

- [ ] **Step 1: Welcome**

Replace `web/app/pages/index.vue` with:

```vue
<script setup lang="ts">
/**
 * Chat UX section 5 (F-1).
 *
 * All three options are full-width buttons of equal size. Guest is outline
 * rather than filled — permitted as a difference in weight — but it is never
 * smaller, lower-contrast, or below the fold. Someone with questions about
 * faith may have good reasons not to attach their phone number to them, and
 * making that the awkward path costs us the conversation.
 *
 * No option is explained. If a label needs explaining, the label is wrong.
 */
const { t } = useCopy()
const auth = useAuthStore()
const router = useRouter()

const busy = ref(false)

async function continueAsGuest() {
  busy.value = true
  try {
    await auth.signInAsGuest()
    await router.push('/chat')
  } finally {
    busy.value = false
  }
}
</script>

<template>
  <main class="flex min-h-dvh flex-col bg-base px-6">
    <div class="flex flex-1 flex-col justify-center">
      <div class="mx-auto w-full max-w-[400px]">
        <h1 class="text-center font-serif text-[30px] leading-tight text-primary">
          {{ t('ui.app_name') }}
        </h1>
        <p class="mx-auto mt-3 max-w-[28ch] text-center text-[15px] leading-relaxed text-secondary">
          {{ t('ui.tagline') }}
        </p>

        <div class="mt-10 space-y-3">
          <NuxtLink
            to="/masuk?channel=sms"
            class="flex min-h-[52px] w-full items-center justify-center rounded-xl bg-accent px-4 text-[15px] font-medium text-on-accent transition hover:bg-accent-hover"
          >
            {{ t('ui.login_sms') }}
          </NuxtLink>

          <NuxtLink
            to="/masuk?channel=whatsapp"
            class="flex min-h-[52px] w-full items-center justify-center rounded-xl bg-accent px-4 text-[15px] font-medium text-on-accent transition hover:bg-accent-hover"
          >
            {{ t('ui.login_whatsapp') }}
          </NuxtLink>

          <button
            type="button"
            :disabled="busy"
            class="flex min-h-[52px] w-full items-center justify-center rounded-xl border-2 border-accent bg-transparent px-4 text-[15px] font-medium text-accent transition hover:bg-raised disabled:opacity-50"
            @click="continueAsGuest"
          >
            {{ t('ui.login_guest') }}
          </button>
        </div>
      </div>
    </div>

    <!-- F-4: footer link, 44px tap target even though the text is small. -->
    <footer class="py-4 text-center">
      <NuxtLink
        to="/privasi"
        class="meta inline-flex min-h-[44px] items-center underline underline-offset-2"
      >
        {{ t('ui.privacy') }}
      </NuxtLink>
    </footer>
  </main>
</template>
```

- [ ] **Step 2: Sign-in**

Create `web/app/pages/masuk.vue`:

```vue
<script setup lang="ts">
/**
 * Chat UX section 6. Phone entry, then OTP, in one route driven by `?channel=`.
 *
 * The two steps share a route because a back affordance from OTP has to return
 * to phone entry without losing the number, and nothing has been committed
 * server-side until the code is verified.
 *
 * Real verification is Phase 3 (PIP 3.1-3.3). In demo mode any six digits are
 * accepted, so a reviewer can walk the whole flow.
 */
const { t } = useCopy()
const route = useRoute()
const router = useRouter()
const auth = useAuthStore()
const demo = useDemoMode()

const channel = computed(() => (route.query.channel === 'whatsapp' ? 'whatsapp' : 'sms'))

const step = ref<'phone' | 'otp'>('phone')
const phone = ref('')
const digits = ref<string[]>(Array(6).fill(''))
const inputs = ref<HTMLInputElement[]>([])
const touched = ref(false)
const error = ref<string | null>(null)
const busy = ref(false)

/** Section 6.1: validation only after blur, never while they are still typing. */
const phoneValid = computed(() => /^8[1-9][0-9]{7,11}$/.test(phone.value.replace(/\D/g, '')))
const showPhoneError = computed(() => touched.value && phone.value.length > 0 && !phoneValid.value)

const RESEND_SECONDS = 60
const resendIn = ref(0)
let ticker: ReturnType<typeof setInterval> | undefined

function startResendCountdown() {
  resendIn.value = RESEND_SECONDS
  if (ticker) clearInterval(ticker)
  ticker = setInterval(() => {
    resendIn.value = Math.max(0, resendIn.value - 1)
    if (resendIn.value === 0 && ticker) clearInterval(ticker)
  }, 1000)
}

onUnmounted(() => {
  if (ticker) clearInterval(ticker)
})

async function sendCode() {
  if (!phoneValid.value) {
    touched.value = true
    return
  }
  error.value = null
  step.value = 'otp'
  startResendCountdown()
  await nextTick()
  inputs.value[0]?.focus()
}

function onDigit(index: number, event: Event) {
  const input = event.target as HTMLInputElement
  const value = input.value.replace(/\D/g, '')

  // Paste of a full code fills every box rather than only the one focused.
  if (value.length > 1) {
    const chars = value.slice(0, 6).split('')
    chars.forEach((char, offset) => {
      if (index + offset < 6) digits.value[index + offset] = char
    })
    const next = Math.min(index + chars.length, 5)
    inputs.value[next]?.focus()
    maybeSubmit()
    return
  }

  digits.value[index] = value
  if (value && index < 5) inputs.value[index + 1]?.focus()
  maybeSubmit()
}

function onBackspace(index: number) {
  if (digits.value[index]) return
  if (index > 0) inputs.value[index - 1]?.focus()
}

/** Section 6.2: auto-submit on the sixth character; no separate confirm tap. */
function maybeSubmit() {
  if (digits.value.every((d) => d !== '')) verify()
}

async function verify() {
  busy.value = true
  error.value = null
  try {
    if (demo) {
      await auth.signInAsGuest()
      await router.push('/chat')
      return
    }
    // Phase 3 wires the real provider here.
    error.value = t('ui.otp_invalid')
  } finally {
    busy.value = false
  }
}

function back() {
  if (step.value === 'otp') {
    step.value = 'phone'
    digits.value = Array(6).fill('')
    return
  }
  router.push('/')
}
</script>

<template>
  <main class="flex min-h-dvh flex-col bg-base px-6">
    <header class="py-4">
      <button
        type="button"
        class="flex min-h-[44px] items-center gap-1.5 text-[14px] text-secondary"
        @click="back"
      >
        <span aria-hidden="true">&#8592;</span> {{ t('ui.back') }}
      </button>
    </header>

    <div class="flex flex-1 flex-col justify-center pb-16">
      <div class="mx-auto w-full max-w-[400px]">
        <!-- Phone entry -->
        <template v-if="step === 'phone'">
          <h1 class="font-serif text-[26px] leading-tight text-primary">
            {{ channel === 'whatsapp' ? t('ui.login_whatsapp') : t('ui.login_sms') }}
          </h1>

          <label for="phone" class="mt-8 block text-[14px] font-medium text-primary">
            {{ t('ui.phone_label') }}
          </label>
          <div class="mt-2 flex items-stretch overflow-hidden rounded-xl border border-strong bg-surface focus-within:border-accent focus-within:ring-2 focus-within:ring-accent/15">
            <span class="grid place-items-center border-r border-subtle bg-raised px-3 text-[15px] text-secondary">
              +62
            </span>
            <input
              id="phone"
              v-model="phone"
              type="tel"
              inputmode="numeric"
              autocomplete="tel-national"
              :placeholder="t('ui.phone_placeholder')"
              class="min-h-[52px] w-full bg-transparent px-3 text-[15px] text-primary outline-none placeholder:text-secondary"
              @blur="touched = true"
            />
          </div>
          <p v-if="showPhoneError" class="mt-2 text-[13px] text-warning">
            {{ t('ui.phone_invalid') }}
          </p>

          <button
            type="button"
            class="mt-6 min-h-[52px] w-full rounded-xl bg-accent px-4 text-[15px] font-medium text-on-accent transition hover:bg-accent-hover disabled:opacity-40"
            :disabled="!phoneValid"
            @click="sendCode"
          >
            Kirim kode
          </button>
        </template>

        <!-- OTP entry -->
        <template v-else>
          <h1 class="font-serif text-[26px] leading-tight text-primary">
            {{ t('ui.otp_title') }}
          </h1>
          <p class="mt-2 text-[14px] text-secondary">
            {{ t('ui.otp_sent_to', { phone: `+62${phone}` }) }}
          </p>

          <div class="mt-8 flex justify-between gap-2" role="group" :aria-label="t('ui.otp_label')">
            <input
              v-for="(_, index) in digits"
              :key="index"
              :ref="(el) => { if (el) inputs[index] = el as HTMLInputElement }"
              v-model="digits[index]"
              type="text"
              inputmode="numeric"
              maxlength="6"
              :aria-label="`${t('ui.otp_label')} ${index + 1}`"
              class="h-14 w-full rounded-xl border border-strong bg-surface text-center font-mono text-[20px] text-primary outline-none transition focus:border-accent focus:ring-2 focus:ring-accent/15"
              @input="onDigit(index, $event)"
              @keydown.backspace="onBackspace(index)"
            />
          </div>

          <p v-if="error" class="mt-3 text-[13px] text-warning">{{ error }}</p>

          <div class="mt-6 flex items-center justify-between">
            <button
              type="button"
              class="min-h-[44px] text-[14px] text-accent underline underline-offset-2 disabled:text-secondary disabled:no-underline"
              :disabled="resendIn > 0 || busy"
              @click="startResendCountdown"
            >
              {{ resendIn > 0 ? t('ui.otp_resend_in', { seconds: resendIn }) : t('ui.otp_resend') }}
            </button>
            <button
              type="button"
              class="min-h-[44px] text-[14px] text-secondary underline underline-offset-2"
              @click="back"
            >
              {{ t('ui.otp_change_number') }}
            </button>
          </div>
        </template>
      </div>
    </div>

    <footer class="py-4 text-center">
      <NuxtLink
        to="/privasi"
        class="meta inline-flex min-h-[44px] items-center underline underline-offset-2"
      >
        {{ t('ui.privacy') }}
      </NuxtLink>
    </footer>
  </main>
</template>
```

- [ ] **Step 3: Chat**

Replace `web/app/pages/chat.vue` with:

```vue
<script setup lang="ts">
/**
 * F-5: one conversation, many questions. There is no "new question" button —
 * the seeker just keeps typing.
 *
 * Section 7.5: the view follows new messages only while the seeker is already
 * at the bottom. If they have scrolled up to reread an answer, a Pesan baru
 * pill appears instead of yanking them back down mid-sentence.
 */
const auth = useAuthStore()
const chat = useChatStore()
const router = useRouter()
const route = useRoute()
const { t } = useCopy()
const demo = useDemoMode()

const embed = computed(() => route.query.embed === '1')
const scroller = ref<HTMLElement | null>(null)
const atBottom = ref(true)
const unread = ref(false)

const BOTTOM_TOLERANCE_PX = 80

function onScroll() {
  const el = scroller.value
  if (!el) return
  atBottom.value =
    el.scrollHeight - el.scrollTop - el.clientHeight < BOTTOM_TOLERANCE_PX
  if (atBottom.value) unread.value = false
}

function scrollToBottom(behavior: ScrollBehavior = 'smooth') {
  const el = scroller.value
  if (!el) return
  el.scrollTo({ top: el.scrollHeight, behavior })
  unread.value = false
}

onMounted(async () => {
  if (!auth.isAuthenticated && !demo) {
    await router.replace('/')
    return
  }
  if (demo && !auth.isAuthenticated) await auth.signInAsGuest()
  await chat.start()
})

watch(
  () => chat.messages.length,
  async () => {
    await nextTick()
    if (atBottom.value) scrollToBottom()
    else unread.value = true
  },
)
</script>

<template>
  <AppShell :embed="embed">
    <DemoScenarioBar v-if="demo && !embed" />

    <div class="relative flex-1 overflow-hidden">
      <div
        ref="scroller"
        class="h-full overflow-y-auto px-4 py-4"
        aria-live="polite"
        @scroll="onScroll"
      >
        <div class="mx-auto flex max-w-measure flex-col gap-3">
          <MessageBubble
            v-for="message in chat.messages"
            :key="message.id"
            :message="message"
            @like="chat.toggleLike"
            @retry="chat.retry"
          />
        </div>
      </div>

      <button
        v-if="unread"
        type="button"
        class="absolute bottom-4 left-1/2 min-h-[44px] -translate-x-1/2 rounded-full bg-accent px-4 text-[13px] font-medium text-on-accent shadow-md"
        @click="scrollToBottom()"
      >
        {{ t('ui.new_messages') }}
      </button>
    </div>

    <div class="mx-auto w-full max-w-measure">
      <Composer :disabled="chat.sending" @submit="chat.ask" />
    </div>
  </AppShell>
</template>
```

- [ ] **Step 4: Privacy**

Create `web/app/pages/privasi.vue`:

```vue
<script setup lang="ts">
/**
 * F-4 requires a Privacy Policy reachable from every screen. The published
 * policy lives at a Client-owned URL (SOW dependency B9, owner: Client/Legal)
 * and is not yet available, so this page states what the product does with
 * data and links out once that URL exists.
 */
const { t } = useCopy()
</script>

<template>
  <main class="min-h-dvh bg-base px-6 py-8">
    <div class="mx-auto max-w-measure">
      <NuxtLink
        to="/"
        class="mb-6 flex min-h-[44px] items-center gap-1.5 text-[14px] text-secondary"
      >
        <span aria-hidden="true">&#8592;</span> {{ t('ui.back') }}
      </NuxtLink>

      <h1 class="font-serif text-[28px] leading-tight text-primary">
        {{ t('ui.privacy') }}
      </h1>

      <div class="mt-6 space-y-4 text-[15px] leading-relaxed text-primary">
        <p>
          Tanya Iman menjawab pertanyaan tentang iman berdasarkan tulisan dari
          situs dialog keagamaan berbahasa Indonesia yang telah disetujui.
        </p>
        <p>
          Percakapan Anda disimpan di perangkat ini. Jika Anda masuk sebagai
          tamu, nomor telepon Anda tidak diminta dan tidak disimpan.
        </p>
        <p>
          Pertanyaan yang diajukan dicatat tanpa nomor telepon, agar tim kami
          dapat mengetahui bahan apa yang masih perlu disiapkan.
        </p>
        <p class="rounded-xl bg-info-bg px-4 py-3 text-info">
          Halaman ini adalah ringkasan sementara untuk keperluan pratinjau.
          Kebijakan Privasi resmi akan diterbitkan oleh klien pada alamat tetap
          sebelum peluncuran.
        </p>
      </div>
    </div>
  </main>
</template>
```

- [ ] **Step 5: Verify no palette colours remain anywhere**

```bash
grep -rnE "(emerald|slate|red|gray|zinc|neutral)-[0-9]{2,3}" web/app/components web/app/pages
```

Expected: no output at all.

- [ ] **Step 6: Typecheck and build**

```bash
npm run typecheck --workspace web/app && npm run build:app
```

Expected: both succeed.

- [ ] **Step 7: Commit**

```bash
git add web/app/pages
git commit -m "feat(app): build the four seeker routes on the token system

Welcome, sign-in, chat, and privacy per Chat UX 3. Adds scroll
anchoring with the Pesan baru pill (7.5) and the OTP flow (6.2).

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 10: Demo scenario bar

The control that makes all seven response states reachable in the hosted build. This is the part the client most needs — the crisis and refusal states are what carries editorial weight.

**Files:**
- Create: `web/app/components/DemoScenarioBar.vue`

- [ ] **Step 1: Write the component**

Create `web/app/components/DemoScenarioBar.vue`:

```vue
<script setup lang="ts">
import { scenarios, type DemoScenario } from '~/demo/scenarios'
import { forceScenario } from '~/composables/useDemoClient'

/**
 * Renders only in demo mode. Lets a reviewer walk every response state of Chat
 * UX section 8 without having to guess a question that triggers each one.
 *
 * Deleted with the rest of demo mode in Phase 5.
 */
const { t } = useCopy()
const chat = useChatStore()

const active = ref<DemoScenario | null>(null)
const open = ref(false)

async function run(scenario: DemoScenario) {
  active.value = scenario
  open.value = false
  forceScenario(scenario)
  await chat.ask(scenario.question)
  // One-shot: the next freely-typed question routes by keyword again.
  forceScenario(null)
}
</script>

<template>
  <div class="border-b border-subtle bg-info-bg px-4 py-2">
    <div class="mx-auto flex max-w-measure flex-wrap items-center gap-x-3 gap-y-1.5">
      <p class="meta flex-1 text-info">{{ t('ui.demo_banner') }}</p>

      <div class="relative">
        <button
          type="button"
          class="min-h-[36px] rounded-lg border border-info/30 px-3 text-[12px] font-medium text-info transition hover:bg-surface"
          :aria-expanded="open"
          @click="open = !open"
        >
          {{ t('ui.demo_scenario') }}
          <span aria-hidden="true" class="ml-1">&#9662;</span>
        </button>

        <div
          v-if="open"
          class="absolute right-0 top-10 z-30 w-72 overflow-hidden rounded-xl border border-subtle bg-surface shadow-md"
        >
          <button
            v-for="scenario in scenarios"
            :key="scenario.label"
            type="button"
            class="block w-full px-4 py-3 text-left text-[13px] text-primary transition hover:bg-raised"
            @click="run(scenario)"
          >
            <span class="block font-medium">{{ scenario.label }}</span>
            <span class="meta mt-0.5 block truncate">{{ scenario.question }}</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 2: Verify in the browser**

```bash
NUXT_PUBLIC_DEMO_MODE=1 npm run dev:app
```

On Windows PowerShell:

```powershell
$env:NUXT_PUBLIC_DEMO_MODE=1; npm run dev:app
```

Open `http://localhost:3000`, continue as guest, and step through every scenario in the dropdown. Confirm: the pending dots appear then are replaced; the crisis card has a border and no like control; the rate-limit countdown ticks; the error bubble offers *Coba lagi* and retrying resends without retyping.

- [ ] **Step 3: Commit**

```bash
git add web/app/components/DemoScenarioBar.vue
git commit -m "feat(app): add demo scenario bar

Makes every response state of Chat UX 8 reachable in the hosted
approval build, including the crisis and refusal states.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 11: Widget demo page

A simulated WordPress host article with the widget embedded, so the client sees the widget in the context it will actually appear in rather than as a bare page.

**Files:**
- Create: `web/app/pages/widget-demo.vue`

- [ ] **Step 1: Write the page**

Create `web/app/pages/widget-demo.vue`:

```vue
<script setup lang="ts">
/**
 * A stand-in for one of the five approved host sites, so the widget can be
 * reviewed in context. The iframe URL matches what public/embed.js loads:
 * hash routing, because the widget is served from a static bundle where a
 * deep path would 404 on refresh.
 *
 * Chat UX section 11: inside the frame the header and outer background are
 * suppressed while the source note and privacy link remain, because F-4 and
 * F-6 apply in the widget exactly as they do in the app.
 */
useHead({ title: 'Pratinjau Widget — Tanya Iman' })

const frame = ref<HTMLIFrameElement | null>(null)
const height = ref(620)

/**
 * The widget reports its height so the host page can size the frame instead of
 * scrolling inside a fixed box. Same message shape as public/embed.js.
 */
function onMessage(event: MessageEvent) {
  if (event.data?.type !== 'tanya-iman:height') return
  const next = Number(event.data.height)
  if (Number.isFinite(next) && next > 0) height.value = next
}

onMounted(() => window.addEventListener('message', onMessage))
onUnmounted(() => window.removeEventListener('message', onMessage))
</script>

<template>
  <!-- Deliberately not the Tanya Iman palette: this is somebody else's website,
       and the point of the page is to show the widget sitting inside one. -->
  <div style="background: #ffffff; color: #23282d; font-family: Georgia, serif">
    <header style="border-bottom: 1px solid #e5e5e5">
      <div style="margin: 0 auto; max-width: 1100px; padding: 18px 24px">
        <p style="font-size: 20px; font-weight: 700; letter-spacing: -0.01em">
          Isa dan Islam
        </p>
      </div>
    </header>

    <div
      style="margin: 0 auto; display: grid; max-width: 1100px; gap: 40px; padding: 32px 24px 64px; grid-template-columns: minmax(0, 1fr) 360px"
    >
      <article>
        <h1 style="margin: 0 0 8px; font-size: 32px; line-height: 1.25">
          Mengapa Isa Al-Masih Disebut Firman Allah?
        </h1>
        <p style="margin: 0 0 24px; font-size: 13px; color: #767676">
          Artikel contoh &middot; 8 September 2026
        </p>

        <div style="font-size: 17px; line-height: 1.75; color: #33383d">
          <p style="margin: 0 0 18px">
            Pertanyaan ini sering muncul dalam percakapan sehari-hari, dan
            jawabannya tidak sesederhana yang diduga banyak orang. Halaman ini
            adalah contoh artikel milik situs klien, dipakai untuk memperlihatkan
            bagaimana widget Tanya Iman tampil di dalamnya.
          </p>
          <p style="margin: 0 0 18px">
            Widget di sebelah kanan memuat aplikasi yang sama dengan versi web
            dan Android, dalam mode tersemat. Kolom isi situs berbeda-beda di
            kelima situs yang disetujui, sehingga tata letaknya harus tetap utuh
            hingga lebar 320 piksel.
          </p>
          <p style="margin: 0">
            Tautan bacaan di dalam widget terbuka di jendela utama, bukan di
            dalam bingkai — pembaca yang menekan tautan tidak boleh kehilangan
            percakapannya.
          </p>
        </div>
      </article>

      <aside>
        <p style="margin: 0 0 10px; font-size: 12px; letter-spacing: 0.08em; text-transform: uppercase; color: #767676">
          Tanya Iman
        </p>
        <iframe
          ref="frame"
          src="./#/chat?embed=1"
          title="Tanya Iman"
          :style="{
            width: '100%',
            height: `${height}px`,
            border: '1px solid #e0dbc9',
            borderRadius: '12px',
            background: '#fffdf7',
          }"
        />
      </aside>
    </div>
  </div>
</template>
```

- [ ] **Step 2: Verify**

With the dev server running in demo mode, open `http://localhost:3000/widget-demo`. Confirm the widget shows no app header, still shows the source note and the privacy link, holds its layout when the browser is narrowed to 320px, and that the frame resizes itself as the conversation grows.

- [ ] **Step 3: Commit**

```bash
git add web/app/pages/widget-demo.vue
git commit -m "feat(app): add WordPress widget preview page

Shows the embed inside a simulated host article rather than as a bare
page, so the client reviews it in context.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---
## Task 12: Height negotiation and brand colour in the embed script

`public/embed.js` renders a launcher in `#059669` — a Tailwind emerald that is not in the palette — and the widget never reports its height, which the SOW names explicitly ("iframe-based embed script with postMessage height negotiation").

**Files:**
- Modify: `web/app/public/embed.js`
- Create: `web/app/composables/useEmbedHeight.ts`
- Modify: `web/app/components/AppShell.vue`

- [ ] **Step 1: Report height from inside the widget**

Create `web/app/composables/useEmbedHeight.ts`:

```ts
/**
 * Reports the widget's content height to the host page (Chat UX section 11).
 *
 * Without this the host has to guess a fixed frame height, which either clips
 * a long answer or leaves a band of empty space under a short one.
 *
 * postMessage targets '*' because the host origin is not knowable from inside
 * the frame — document.referrer is unreliable once the user navigates. Nothing
 * sensitive is sent: the payload is a single number.
 */
export function useEmbedHeight(enabled: MaybeRef<boolean>): void {
  if (import.meta.server) return

  const active = computed(() => unref(enabled))
  let observer: ResizeObserver | undefined

  function report() {
    if (!active.value) return
    const height = Math.ceil(document.documentElement.scrollHeight)
    window.parent?.postMessage({ type: 'tanya-iman:height', height }, '*')
  }

  onMounted(() => {
    if (!active.value) return
    report()
    observer = new ResizeObserver(report)
    observer.observe(document.documentElement)
  })

  onUnmounted(() => observer?.disconnect())
}
```

- [ ] **Step 2: Call it from the shell**

In `web/app/components/AppShell.vue`, add this line to the `<script setup>` block, directly after the `const menuOpen = ref(false)` line:

```ts
// In embed mode the host page sizes its iframe from what we report.
useEmbedHeight(computed(() => Boolean(props.embed)))
```

And change the props declaration on the line above from `defineProps<{ embed?: boolean }>()` to:

```ts
const props = defineProps<{ embed?: boolean }>()
```

- [ ] **Step 3: Receive the height in the embed script**

In `web/app/public/embed.js`, replace the `launcher.style.cssText = [...]` assignment's background line — change `'background:#059669',` to:

```js
    'background:#0f3d2e',
```

That is `accentPrimary` from `web/shared/src/tokens.ts`. It is written literally here because `embed.js` is a plain static file served to third-party sites; it cannot import from the workspace.

Then add height handling. Insert this directly above the `function mount() {` line:

```js
  // The widget reports its content height so a long answer is not clipped and
  // a short one does not leave a band of empty space (Chat UX section 11).
  var MAX_HEIGHT_PX = 620

  window.addEventListener('message', function (event) {
    if (event.source !== frame.contentWindow) return
    if (!event.data || event.data.type !== 'tanya-iman:height') return

    var next = Number(event.data.height)
    if (!isFinite(next) || next <= 0) return

    frame.style.height =
      'min(' + Math.min(next, MAX_HEIGHT_PX) + 'px, calc(100vh - 120px))'
  })
```

- [ ] **Step 4: Verify**

Rebuild and open the widget demo page. Ask two or three questions and confirm the frame grows with the transcript rather than scrolling inside a fixed box.

```bash
npm run build:app
```

- [ ] **Step 5: Commit**

```bash
git add web/app/public/embed.js web/app/composables/useEmbedHeight.ts web/app/components/AppShell.vue
git commit -m "feat(app): add postMessage height negotiation to the widget

The SOW names height negotiation explicitly and the widget was not
reporting one. Also replaces the launcher's off-palette emerald with
the accent token value.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 13: Admin foundation — tokens, copy, session, layout

The admin app has no design layer, no copy file, no store, and no layout. Build the floor before the ten rooms.

**Files:**
- Create: `web/admin/assets/css/tokens.css`, `web/admin/locales/id.json`, `web/admin/composables/useCopy.ts`, `web/admin/composables/useDemoMode.ts`, `web/admin/stores/session.ts`, `web/admin/layouts/default.vue`, `web/admin/layouts/auth.vue`
- Modify: `web/admin/assets/css/tailwind.css`, `web/admin/tailwind.config.ts`, `web/admin/nuxt.config.ts`, `web/admin/app.vue`

- [ ] **Step 1: Admin tokens**

Create `web/admin/assets/css/tokens.css`:

```css
/* Zamrud & Perkamen — admin surface.
   Mirrors adminTokens in web/shared/src/tokens.ts. Same hues as the seeker
   app, flatter and denser: this is a tool someone uses for hours, so row count
   matters more than whitespace (Admin UX 4.1). */
:root {
  --bg-base: #f6f6f2;
  --bg-surface: #ffffff;
  --bg-raised: #eceae2;

  --text-primary: #1c231f;
  --text-secondary: #5a655e;
  --text-on-accent: #f7fbf8;

  --accent-primary: #14503c;
  --accent-hover: #1b6249;

  --border-subtle: #e2e1d8;
  --border-strong: #c6c5b8;

  --status-success-text: #1f5c3a;
  --status-success-bg: #e3efe7;

  --status-warning-text: #7c4a12;
  --status-warning-bg: #f8ecd9;

  --status-danger-text: #8f2f26;
  --status-danger-bg: #f8e5e2;

  --status-info-text: #2f5548;
  --status-info-bg: #e7efea;

  --shadow-sm: 0 1px 2px rgba(28, 35, 31, 0.06);
  --shadow-md: 0 2px 6px -2px rgba(28, 35, 31, 0.1), 0 8px 20px -12px rgba(28, 35, 31, 0.18);
}
```

- [ ] **Step 2: Admin stylesheet**

Replace `web/admin/assets/css/tailwind.css` with:

```css
@import './tokens.css';

@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --font-sans: 'Inter', ui-sans-serif, system-ui, -apple-system, 'Segoe UI',
      Roboto, sans-serif;
    --font-serif: 'Lora', Georgia, Cambria, 'Times New Roman', serif;
  }

  html {
    -webkit-text-size-adjust: 100%;
  }

  body {
    background: var(--bg-base);
    color: var(--text-primary);
    font-family: var(--font-sans);
    font-size: 14px;
    line-height: 1.55;
  }

  h1,
  h2 {
    font-family: var(--font-serif);
    font-weight: 500;
    letter-spacing: -0.01em;
  }

  /* Admin UX 4.3: counts and timestamps use tabular numerals so columns line
     up down a long list. */
  table td,
  table th,
  .tabular {
    font-variant-numeric: tabular-nums;
  }
}

@layer components {
  .meta {
    font-size: 12px;
    line-height: 1.5;
    color: var(--text-secondary);
  }
}
```

- [ ] **Step 3: Admin Tailwind config**

Replace `web/admin/tailwind.config.ts` with:

```ts
import type { Config } from 'tailwindcss'

/**
 * Mirrors adminTokens in web/shared via the CSS variables in
 * assets/css/tokens.css. Components never name a colour (Admin UX 4.2).
 */
export default {
  content: [
    './components/**/*.{vue,ts}',
    './composables/**/*.ts',
    './layouts/**/*.vue',
    './pages/**/*.vue',
    './stores/**/*.ts',
    './demo/**/*.ts',
    './app.vue',
  ],
  theme: {
    extend: {
      colors: {
        base: 'var(--bg-base)',
        surface: 'var(--bg-surface)',
        raised: 'var(--bg-raised)',
        primary: 'var(--text-primary)',
        secondary: 'var(--text-secondary)',
        'on-accent': 'var(--text-on-accent)',
        accent: {
          DEFAULT: 'var(--accent-primary)',
          hover: 'var(--accent-hover)',
        },
        subtle: 'var(--border-subtle)',
        strong: 'var(--border-strong)',
        success: {
          DEFAULT: 'var(--status-success-text)',
          bg: 'var(--status-success-bg)',
        },
        warning: {
          DEFAULT: 'var(--status-warning-text)',
          bg: 'var(--status-warning-bg)',
        },
        danger: {
          DEFAULT: 'var(--status-danger-text)',
          bg: 'var(--status-danger-bg)',
        },
        info: {
          DEFAULT: 'var(--status-info-text)',
          bg: 'var(--status-info-bg)',
        },
      },
      fontFamily: {
        sans: 'var(--font-sans)',
        serif: 'var(--font-serif)',
      },
      boxShadow: {
        sm: 'var(--shadow-sm)',
        md: 'var(--shadow-md)',
      },
    },
  },
} satisfies Config
```

- [ ] **Step 4: Admin copy**

Create `web/admin/locales/id.json`:

```json
{
  "_note": "Admin portal copy. The seeker app has its own file; nothing is shared between them, because admin strings are internal tooling language and are not under editorial review.",

  "app": "Tanya Iman",
  "portal": "Portal Editorial",
  "demo_banner": "Pratinjau desain — data contoh, bukan data sungguhan.",

  "nav": {
    "dashboard": "Beranda",
    "questions": "Pertanyaan",
    "topics": "Topik",
    "clusters": "Pertanyaan Serupa",
    "gaps": "Kekosongan Materi",
    "review": "Antrean Tinjauan",
    "settings": "Pengaturan"
  },

  "role": {
    "editor": "Editor",
    "reviewer": "Peninjau",
    "super_admin": "Admin Utama"
  },

  "login": {
    "title": "Masuk ke Portal Editorial",
    "email": "Alamat email",
    "password": "Kata sandi",
    "submit": "Masuk",
    "demo_hint": "Mode pratinjau — pilih peran untuk melihat portal dari sudut pandang berbeda."
  },

  "dashboard": {
    "title": "Beranda",
    "subtitle": "Ringkasan tujuh hari terakhir.",
    "volume": "Jumlah pertanyaan",
    "volume_change": "{change} dibanding minggu lalu",
    "top_topics": "Topik teratas",
    "gaps": "Kekosongan materi",
    "gaps_largest": "Terbesar: {name}",
    "review": "Perlu ditinjau",
    "review_items": "{count} item belum ditinjau",
    "health": "Kesehatan jawaban",
    "health_answer_rate": "Terjawab",
    "health_like_rate": "Disukai",
    "health_validator": "Lolos validator",
    "health_alert": "Tingkat kelulusan validator tidak 100%. Ini gerbang rilis (K4) dan harus ditangani."
  },

  "questions": {
    "title": "Pertanyaan",
    "search": "Cari teks pertanyaan…",
    "export": "Ekspor CSV",
    "clear_filters": "Bersihkan filter",
    "empty": "Tidak ada pertanyaan pada rentang tanggal ini.",
    "col_time": "Waktu",
    "col_question": "Pertanyaan",
    "col_topic": "Topik",
    "col_result": "Hasil",
    "col_likes": "Suka",
    "col_channel": "Kanal",
    "col_flags": "Penanda"
  },

  "detail": {
    "title": "Detail Pertanyaan",
    "exchange": "Percakapan",
    "diagnostics": "Diagnostik",
    "classification": "Klasifikasi",
    "retrieved": "Sumber yang diambil",
    "cited": "Dikutip",
    "retrieved_only": "Diambil",
    "validation": "Validasi",
    "repair": "Perbaikan",
    "technical": "Teknis",
    "copy_link": "Salin tautan",
    "flag": "Tandai untuk ditinjau",
    "delete": "Hapus"
  },

  "topics": {
    "title": "Topik",
    "col_topic": "Topik",
    "col_questions": "Pertanyaan",
    "col_likes": "Suka",
    "col_curated": "Jawaban kurasi",
    "col_refusal": "Tingkat penolakan",
    "write": "Tulis jawaban",
    "edit": "Ubah jawaban",
    "curated_none": "Belum ada",
    "curated_draft": "Draf",
    "curated_published": "Terbit",
    "lainnya_warning": "Porsi ‘lainnya’ melebihi 10% — taksonomi topik perlu ditinjau."
  },

  "editor": {
    "title": "Editor Jawaban",
    "answer_label": "Jawaban",
    "rules": "Aturan",
    "rule_length": "Panjang",
    "rule_terminology": "Sebutan",
    "rule_scripture": "Ayat",
    "rule_citations": "Tautan",
    "words": "{count} / 25–250 kata",
    "terminology_ok": "Sebutan sudah sesuai.",
    "terminology_bad": "Ganti ‘{word}’ — gunakan ‘Allah’ atau ‘Isa Al-Masih’.",
    "citations_count": "{count} dari 1–2 tautan dipilih",
    "citation_search": "Cari artikel dari situs yang disetujui…",
    "save_draft": "Simpan sebagai draf",
    "publish": "Terbitkan",
    "publish_confirm": "Jawaban ini akan langsung ditampilkan kepada semua pengguna yang bertanya tentang topik ini.",
    "draft_notice": "Draf tidak pernah ditampilkan kepada pengguna.",
    "too_narrow": "Editor jawaban memerlukan layar minimal 768px."
  },

  "clusters": {
    "title": "Pertanyaan Serupa",
    "col_canonical": "Pertanyaan umum",
    "col_count": "Jumlah",
    "col_topic": "Topik",
    "col_last": "Terakhir ditanya",
    "col_curated": "Jawaban kurasi",
    "make_curated": "Jadikan jawaban kurasi",
    "members": "Pertanyaan asli"
  },

  "gaps": {
    "title": "Kekosongan Materi",
    "subtitle": "Pertanyaan yang tidak dapat dijawab dari materi yang ada, diurutkan menurut frekuensi.",
    "col_canonical": "Pertanyaan",
    "col_count": "Ditanyakan",
    "col_last": "Terakhir",
    "col_topic": "Topik terdekat",
    "resolved": "Sudah ditulis",
    "resolved_note": "Status ini diturunkan dari materi, bukan ditetapkan manual — kekosongan hilang setelah proses pengambilan materi berikutnya mengonfirmasi jawabannya tersedia."
  },

  "review": {
    "title": "Antrean Tinjauan",
    "sensitive": "Catatan krisis dan penangguhan emosional bersifat sensitif dan tidak boleh keluar dari portal ini.",
    "col_type": "Jenis",
    "col_summary": "Ringkasan",
    "col_time": "Waktu",
    "mark_reviewed": "Tandai sudah ditinjau",
    "note": "Catatan (opsional)",
    "type_ambiguous": "Klasifikasi ambigu",
    "type_validator": "Kegagalan validator",
    "type_crisis": "Peristiwa krisis",
    "type_emotional": "Penangguhan emosional"
  },

  "settings": {
    "title": "Pengaturan",
    "system": "Sistem",
    "contact": "Kontak dukungan emosional",
    "accounts": "Akun admin",
    "corpus": "Materi",
    "audit": "Jejak audit",
    "retention": "Masa simpan (bulan)",
    "rate_limit": "Batas pertanyaan per jam",
    "similarity": "Ambang kemiripan",
    "similarity_warning": "Mengubah nilai ini mengubah pertanyaan mana yang bersedia dijawab oleh asisten. Tinjau hasil benchmark sebelum menyimpan.",
    "contact_name": "Nama kontak",
    "contact_number": "Nomor telepon",
    "contact_pending": "Kontak dukungan belum ditetapkan. Nilai ini menunggu persetujuan tim pastoral klien dan tidak boleh diisi placeholder di staging atau produksi.",
    "run_ingestion": "Jalankan sekarang",
    "last_run": "Pengambilan terakhir",
    "col_actor": "Pelaku",
    "col_action": "Tindakan",
    "col_target": "Objek",
    "col_time": "Waktu"
  },

  "common": {
    "loading": "Memuat…",
    "cancel": "Batal",
    "confirm": "Lanjutkan",
    "save": "Simpan",
    "saved": "Tersimpan.",
    "irreversible": "Tindakan ini tidak dapat dibatalkan.",
    "audit_id": "ID audit: {id}",
    "no_access": "Peran Anda tidak memiliki akses ke halaman ini.",
    "channel_web": "Web",
    "channel_widget": "Widget",
    "channel_android": "Android"
  },

  "result": {
    "generated": "Dijawab",
    "curated": "Kurasi",
    "refusal": "Ditolak",
    "no_grounding": "Tanpa Sumber",
    "crisis": "Krisis",
    "emotional_deferral": "Emosional",
    "error": "Gagal"
  }
}
```

- [ ] **Step 5: Admin copy composable**

Create `web/admin/composables/useCopy.ts`:

```ts
import id from '~/locales/id.json'

/**
 * Same flat lookup as the seeker app's useCopy. Duplicated rather than shared
 * because the two apps have separate locale files with no overlapping keys,
 * and a shared module would create a dependency between them for the sake of
 * fifteen lines.
 */
export function useCopy() {
  function t(path: string, vars?: Record<string, string | number>): string {
    const value = path
      .split('.')
      .reduce<unknown>((acc, key) => (acc as Record<string, unknown>)?.[key], id)

    if (typeof value !== 'string') {
      if (import.meta.dev) console.warn(`[copy] missing key: ${path}`)
      return path
    }

    if (!vars) return value
    return value.replace(/\{(\w+)\}/g, (match, key) =>
      key in vars ? String(vars[key]) : match,
    )
  }

  return { t }
}
```

- [ ] **Step 6: Demo flag**

Create `web/admin/composables/useDemoMode.ts`:

```ts
/** See the seeker app's useDemoMode. Same flag, same lifetime. */
export function useDemoMode(): boolean {
  return useRuntimeConfig().public.demoMode === '1'
}
```

In `web/admin/nuxt.config.ts`, add to `runtimeConfig.public` after the `apiBase` line:

```ts
      demoMode: process.env.NUXT_PUBLIC_DEMO_MODE || '',
```

And add the font link to `app.head`, after the `meta` array:

```ts
      link: [
        { rel: 'preconnect', href: 'https://fonts.googleapis.com' },
        { rel: 'preconnect', href: 'https://fonts.gstatic.com', crossorigin: '' },
        {
          rel: 'stylesheet',
          href: 'https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Lora:wght@400;500;600&display=swap',
        },
      ],
```

- [ ] **Step 7: Session store**

Create `web/admin/stores/session.ts`:

```ts
import { defineStore } from 'pinia'

/** Admin UX section 3. Three roles, hidden capabilities rather than disabled. */
export type AdminRole = 'editor' | 'reviewer' | 'super_admin'

export const useSessionStore = defineStore('session', () => {
  const email = ref<string | null>(null)
  const role = ref<AdminRole>('editor')

  const isAuthenticated = computed(() => email.value !== null)

  /** Section 5.3: a reviewer sees no editing controls anywhere. */
  const canEdit = computed(() => role.value === 'editor' || role.value === 'super_admin')
  const canAdminister = computed(() => role.value === 'super_admin')

  function signIn(nextEmail: string, nextRole: AdminRole) {
    email.value = nextEmail
    role.value = nextRole
  }

  function signOut() {
    email.value = null
  }

  return { email, role, isAuthenticated, canEdit, canAdminister, signIn, signOut }
})
```

- [ ] **Step 8: Layouts**

Create `web/admin/layouts/auth.vue`:

```vue
<template>
  <div class="grid min-h-dvh place-items-center bg-base px-6">
    <slot />
  </div>
</template>
```

Create `web/admin/layouts/default.vue`:

```vue
<script setup lang="ts">
import { useSessionStore } from '~/stores/session'
import { gapCount, reviewCount } from '~/demo/fixtures'

/**
 * Sidebar on desktop, top menu on tablet (Admin UX section 16).
 *
 * Kekosongan Materi and Antrean Tinjauan carry standing badge counts because
 * both represent work waiting to be done — section 3.
 */
const { t } = useCopy()
const session = useSessionStore()
const route = useRoute()
const router = useRouter()
const demo = useDemoMode()

const nav = computed(() => [
  { to: '/', label: t('nav.dashboard') },
  { to: '/pertanyaan', label: t('nav.questions') },
  { to: '/topik', label: t('nav.topics') },
  { to: '/serupa', label: t('nav.clusters') },
  { to: '/kekosongan', label: t('nav.gaps'), badge: gapCount },
  { to: '/tinjauan', label: t('nav.review'), badge: reviewCount },
  ...(session.canAdminister ? [{ to: '/pengaturan', label: t('nav.settings') }] : []),
])

function isActive(to: string): boolean {
  return to === '/' ? route.path === '/' : route.path.startsWith(to)
}

async function signOut() {
  session.signOut()
  await router.push('/masuk')
}
</script>

<template>
  <div class="min-h-dvh lg:grid lg:grid-cols-[240px_minmax(0,1fr)]">
    <aside class="border-b border-subtle bg-surface lg:border-b-0 lg:border-r">
      <div class="flex items-center gap-2 px-5 py-4">
        <span class="font-serif text-[16px] text-primary">{{ t('app') }}</span>
        <span class="meta border-l border-subtle pl-2">{{ t('portal') }}</span>
      </div>

      <nav class="flex gap-1 overflow-x-auto px-3 pb-3 lg:flex-col lg:overflow-visible">
        <NuxtLink
          v-for="item in nav"
          :key="item.to"
          :to="item.to"
          :class="[
            'flex shrink-0 items-center justify-between gap-2 rounded-lg px-3 py-2 text-[13.5px] transition',
            isActive(item.to)
              ? 'bg-accent text-on-accent'
              : 'text-primary hover:bg-raised',
          ]"
        >
          <span>{{ item.label }}</span>
          <span
            v-if="item.badge"
            :class="[
              'rounded-full px-1.5 py-0.5 text-[11px] tabular',
              isActive(item.to) ? 'bg-surface/20' : 'bg-warning-bg text-warning',
            ]"
          >
            {{ item.badge }}
          </span>
        </NuxtLink>
      </nav>
    </aside>

    <div class="flex min-w-0 flex-col">
      <header class="flex items-center gap-3 border-b border-subtle bg-surface px-5 py-3">
        <p v-if="demo" class="meta flex-1 rounded-md bg-info-bg px-2.5 py-1 text-info">
          {{ t('demo_banner') }}
        </p>
        <span v-else class="flex-1" />

        <span class="rounded-full bg-raised px-2.5 py-1 text-[12px] text-primary">
          {{ t(`role.${session.role}`) }}
        </span>
        <span class="meta hidden sm:inline">{{ session.email }}</span>
        <button type="button" class="meta underline underline-offset-2" @click="signOut">
          Keluar
        </button>
      </header>

      <main class="min-w-0 flex-1 px-5 py-6">
        <slot />
      </main>
    </div>
  </div>
</template>
```

- [ ] **Step 9: App root**

Replace `web/admin/app.vue` with:

```vue
<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>
```

- [ ] **Step 10: Commit**

The admin app will not build until Task 14 creates `demo/fixtures.ts`. Commit both together at the end of Task 14.

---
## Task 14: Admin fixtures

The data behind every admin screen. One file, deleted when Phase 6 wires the real API.

**Files:**
- Create: `web/admin/demo/fixtures.ts`

- [ ] **Step 1: Write the fixtures**

Create `web/admin/demo/fixtures.ts`:

```ts
import type { AnswerSource, Platform } from '@tanya-iman/shared'

/**
 * DEMO DATA — NOT REAL. Backs the hosted approval build so the editorial team
 * can review the portal before Phase 6 connects it to the API.
 *
 * Deleted wholesale when the real admin endpoints land.
 *
 * Question texts are invented and no phone number appears anywhere, in keeping
 * with Admin UX section 7.4 — the list view has no phone column at all.
 */

export interface QuestionRow {
  id: string
  askedAt: string
  question: string
  topicSlug: string
  topicLabel: string
  result: AnswerSource
  likes: number
  channel: Platform
  hostSite?: string
  flags: Array<'ambiguous' | 'validator' | 'injection'>
}

export interface TopicRow {
  slug: string
  label: string
  questions: number
  likes: number
  curated: 'none' | 'draft' | 'published'
  curatedBy?: string
  curatedAt?: string
  refusalRate: number
}

export interface ClusterRow {
  id: string
  canonical: string
  count: number
  topicLabel: string
  lastAsked: string
  hasCurated: boolean
  members: string[]
}

export interface GapRow {
  id: string
  canonical: string
  count: number
  lastAsked: string
  nearestTopic: string
}

export interface ReviewRow {
  id: string
  type: 'ambiguous' | 'validator' | 'crisis' | 'emotional'
  summary: string
  at: string
  reviewed: boolean
}

export interface AuditRow {
  id: string
  actor: string
  action: string
  target: string
  at: string
}

export const questions: QuestionRow[] = [
  {
    id: 'q_1041',
    askedAt: '2026-09-08T09:14:00+07:00',
    question: 'Siapakah Isa Al-Masih menurut Kitab Suci?',
    topicSlug: 'identitas-isa',
    topicLabel: 'Identitas Isa Al-Masih',
    result: 'generated',
    likes: 3,
    channel: 'web',
    flags: [],
  },
  {
    id: 'q_1040',
    askedAt: '2026-09-08T08:52:00+07:00',
    question: 'Apakah Allah mengampuni dosa yang sudah berulang kali saya lakukan?',
    topicSlug: 'pengampunan',
    topicLabel: 'Pengampunan',
    result: 'curated',
    likes: 11,
    channel: 'widget',
    hostSite: 'isadanislam.org',
    flags: [],
  },
  {
    id: 'q_1039',
    askedAt: '2026-09-08T08:31:00+07:00',
    question: 'Bagaimana pandangan Kitab Suci tentang penambangan aset kripto?',
    topicSlug: 'lainnya',
    topicLabel: 'Lainnya',
    result: 'no_grounding',
    likes: 0,
    channel: 'android',
    flags: [],
  },
  {
    id: 'q_1038',
    askedAt: '2026-09-08T07:58:00+07:00',
    question: 'Bagaimana Isa Al-Masih memperlakukan perempuan?',
    topicSlug: 'perempuan',
    topicLabel: 'Perempuan dan Keluarga',
    result: 'generated',
    likes: 7,
    channel: 'widget',
    hostSite: 'isaislamdankaumwanita.com',
    flags: [],
  },
  {
    id: 'q_1037',
    askedAt: '2026-09-07T21:12:00+07:00',
    question: 'Apakah benar semua orang akan masuk neraka?',
    topicSlug: 'akhirat',
    topicLabel: 'Akhirat',
    result: 'generated',
    likes: 2,
    channel: 'web',
    flags: ['ambiguous'],
  },
  {
    id: 'q_1036',
    askedAt: '2026-09-07T20:40:00+07:00',
    question: 'Tolong buatkan saya kode Python untuk mengurutkan daftar.',
    topicSlug: 'lainnya',
    topicLabel: 'Lainnya',
    result: 'refusal',
    likes: 0,
    channel: 'web',
    flags: [],
  },
  {
    id: 'q_1035',
    askedAt: '2026-09-07T19:03:00+07:00',
    question: 'Apa maksud kasih karunia dalam Injil?',
    topicSlug: 'keselamatan',
    topicLabel: 'Keselamatan',
    result: 'generated',
    likes: 5,
    channel: 'android',
    flags: ['validator'],
  },
  {
    id: 'q_1034',
    askedAt: '2026-09-07T16:22:00+07:00',
    question: 'Mengapa Kitab Suci disebut tidak berubah?',
    topicSlug: 'kitab-suci',
    topicLabel: 'Kitab Suci',
    result: 'generated',
    likes: 4,
    channel: 'widget',
    hostSite: 'isadanalquran.com',
    flags: [],
  },
]

export const topics: TopicRow[] = [
  { slug: 'identitas-isa', label: 'Identitas Isa Al-Masih', questions: 412, likes: 96, curated: 'published', curatedBy: 'siti@tanyaiman.id', curatedAt: '2026-08-30', refusalRate: 0.04 },
  { slug: 'pengampunan', label: 'Pengampunan', questions: 318, likes: 141, curated: 'published', curatedBy: 'siti@tanyaiman.id', curatedAt: '2026-09-01', refusalRate: 0.06 },
  { slug: 'keselamatan', label: 'Keselamatan', questions: 276, likes: 72, curated: 'draft', curatedBy: 'budi@tanyaiman.id', curatedAt: '2026-09-05', refusalRate: 0.09 },
  { slug: 'kitab-suci', label: 'Kitab Suci', questions: 244, likes: 61, curated: 'none', refusalRate: 0.12 },
  { slug: 'akhirat', label: 'Akhirat', questions: 198, likes: 44, curated: 'none', refusalRate: 0.18 },
  { slug: 'doa', label: 'Doa', questions: 163, likes: 39, curated: 'published', curatedBy: 'budi@tanyaiman.id', curatedAt: '2026-08-24', refusalRate: 0.07 },
  { slug: 'perempuan', label: 'Perempuan dan Keluarga', questions: 149, likes: 58, curated: 'none', refusalRate: 0.11 },
  { slug: 'nabi', label: 'Para Nabi', questions: 131, likes: 27, curated: 'none', refusalRate: 0.14 },
  { slug: 'salib', label: 'Salib dan Penebusan', questions: 118, likes: 33, curated: 'draft', curatedBy: 'siti@tanyaiman.id', curatedAt: '2026-09-03', refusalRate: 0.16 },
  { slug: 'roh', label: 'Roh dan Kehidupan Kekal', questions: 97, likes: 21, curated: 'none', refusalRate: 0.19 },
  { slug: 'ibadah', label: 'Ibadah', questions: 84, likes: 18, curated: 'none', refusalRate: 0.1 },
  { slug: 'keraguan', label: 'Keraguan', questions: 76, likes: 29, curated: 'none', refusalRate: 0.22 },
  { slug: 'komunitas', label: 'Komunitas dan Ibadah Bersama', questions: 54, likes: 12, curated: 'none', refusalRate: 0.13 },
  { slug: 'lainnya', label: 'Lainnya', questions: 208, likes: 9, curated: 'none', refusalRate: 0.41 },
]

export const clusters: ClusterRow[] = [
  {
    id: 'c_1',
    canonical: 'Apakah dosa saya masih bisa diampuni?',
    count: 87,
    topicLabel: 'Pengampunan',
    lastAsked: '2026-09-08T08:52:00+07:00',
    hasCurated: true,
    members: [
      'Apakah Allah mengampuni dosa yang sudah berulang kali saya lakukan?',
      'Dosa saya terlalu banyak, apakah masih ada harapan?',
      'Bisakah orang seperti saya diampuni?',
    ],
  },
  {
    id: 'c_2',
    canonical: 'Siapa sebenarnya Isa Al-Masih?',
    count: 74,
    topicLabel: 'Identitas Isa Al-Masih',
    lastAsked: '2026-09-08T09:14:00+07:00',
    hasCurated: true,
    members: [
      'Siapakah Isa Al-Masih menurut Kitab Suci?',
      'Apakah Isa hanya seorang nabi?',
      'Mengapa Isa disebut Firman Allah?',
    ],
  },
  {
    id: 'c_3',
    canonical: 'Mengapa Kitab Suci dianggap tidak berubah?',
    count: 41,
    topicLabel: 'Kitab Suci',
    lastAsked: '2026-09-07T16:22:00+07:00',
    hasCurated: false,
    members: [
      'Mengapa Kitab Suci disebut tidak berubah?',
      'Bukankah Injil sudah diubah manusia?',
    ],
  },
]

export const gaps: GapRow[] = [
  { id: 'g_1', canonical: 'Bagaimana pandangan Kitab Suci tentang keuangan dan utang?', count: 34, lastAsked: '2026-09-08T08:31:00+07:00', nearestTopic: 'Lainnya' },
  { id: 'g_2', canonical: 'Apa kata Kitab Suci tentang mimpi dan tafsirnya?', count: 27, lastAsked: '2026-09-07T14:10:00+07:00', nearestTopic: 'Lainnya' },
  { id: 'g_3', canonical: 'Bagaimana menghadapi tekanan keluarga soal keyakinan?', count: 22, lastAsked: '2026-09-06T19:45:00+07:00', nearestTopic: 'Komunitas dan Ibadah Bersama' },
  { id: 'g_4', canonical: 'Apakah ada penjelasan tentang kehidupan setelah kematian bagi anak?', count: 15, lastAsked: '2026-09-05T11:02:00+07:00', nearestTopic: 'Akhirat' },
]

export const reviews: ReviewRow[] = [
  { id: 'r_1', type: 'validator', summary: 'V1_TOO_LONG — 271 kata pada jawaban q_1035', at: '2026-09-07T19:04:00+07:00', reviewed: false },
  { id: 'r_2', type: 'ambiguous', summary: 'Klasifikasi ambigu antara teologi dan emosional — q_1037', at: '2026-09-07T21:13:00+07:00', reviewed: false },
  { id: 'r_3', type: 'crisis', summary: 'Peristiwa krisis terdeteksi — rutin ditinjau bulanan (K9)', at: '2026-09-06T23:41:00+07:00', reviewed: false },
  { id: 'r_4', type: 'emotional', summary: 'Penangguhan emosional — periksa tampilan nomor kontak', at: '2026-09-06T10:18:00+07:00', reviewed: true },
]

export const audit: AuditRow[] = [
  { id: 'a_912', actor: 'siti@tanyaiman.id', action: 'Menerbitkan jawaban kurasi', target: 'Topik: Pengampunan', at: '2026-09-01T10:22:00+07:00' },
  { id: 'a_911', actor: 'admin@tanyaiman.id', action: 'Menonaktifkan akun', target: 'rina@tanyaiman.id', at: '2026-08-29T15:40:00+07:00' },
  { id: 'a_910', actor: 'siti@tanyaiman.id', action: 'Menghapus pertanyaan', target: 'q_0987', at: '2026-08-28T09:05:00+07:00' },
]

/** Dashboard numbers. Validator rate is deliberately below 100% so the client
 *  sees what the K4 alert state looks like — Admin UX section 6. */
export const dashboard = {
  volumeThisWeek: 1284,
  volumeChangePct: 12,
  answerRatePct: 91,
  likeRatePct: 34,
  validatorPassPct: 99.2,
}

export const gapCount = gaps.length
export const reviewCount = reviews.filter((r) => !r.reviewed).length

/** Articles the citation picker searches. Approved sites only — Admin UX 10. */
export const articles = [
  { id: 'art_1', title: 'Siapakah Isa Al-Masih dalam Injil?', site: 'isadanislam.org', url: 'https://isadanislam.org/siapakah-isa-al-masih/' },
  { id: 'art_2', title: 'Firman yang Menjadi Manusia', site: 'isadanalquran.com', url: 'https://isadanalquran.com/firman-yang-menjadi-manusia/' },
  { id: 'art_3', title: 'Pengampunan yang Tidak Terbatas', site: 'isadanalfatihah.com', url: 'https://isadanalfatihah.com/pengampunan-yang-tidak-terbatas/' },
  { id: 'art_4', title: 'Perempuan dalam Pandangan Isa Al-Masih', site: 'isaislamdankaumwanita.com', url: 'https://isaislamdankaumwanita.com/perempuan-dalam-pandangan-isa/' },
  { id: 'art_5', title: 'Ia Tidak Menghukum', site: 'takutneraka.com', url: 'https://takutneraka.com/ia-tidak-menghukum/' },
  { id: 'art_6', title: 'Kasih yang Tidak Berkesudahan', site: 'isadanislam.org', url: 'https://isadanislam.org/kasih-yang-tidak-berkesudahan/' },
]

/** Retrieved chunks for the question detail page's diagnostics panel. */
export const retrievedChunks = [
  { id: 'ch_1', articleTitle: 'Siapakah Isa Al-Masih dalam Injil?', site: 'isadanislam.org', score: 0.89, cited: true, text: 'Injil membuka dengan pernyataan bahwa Firman itu telah ada pada mulanya, dan Firman itu bersama-sama dengan Allah…' },
  { id: 'ch_2', articleTitle: 'Firman yang Menjadi Manusia', site: 'isadanalquran.com', score: 0.84, cited: true, text: 'Firman itu telah menjadi manusia dan diam di antara kita, penuh kasih karunia dan kebenaran…' },
  { id: 'ch_3', articleTitle: 'Kasih yang Tidak Berkesudahan', site: 'isadanislam.org', score: 0.71, cited: false, text: 'Kasih Allah tidak diukur dari kelayakan manusia, melainkan dari sifat Allah sendiri…' },
]

/** V1–V5 results for the diagnostics panel. */
export const validators = [
  { code: 'V1', label: 'Panjang', pass: true, measured: '184 kata' },
  { code: 'V2', label: 'Sebutan', pass: true, measured: 'Allah, Isa Al-Masih' },
  { code: 'V3', label: 'Keseimbangan ayat', pass: true, measured: '1 rujukan Quran, 2 rujukan Kitab Suci' },
  { code: 'V4', label: 'Sumber kutipan', pass: true, measured: '2 tautan, keduanya dari situs disetujui' },
  { code: 'V5', label: 'Dasar jawaban', pass: true, measured: 'Seluruh klaim tertaut ke potongan yang diambil' },
]
```

- [ ] **Step 2: Typecheck and commit foundation plus fixtures**

```bash
npm run typecheck --workspace web/admin
```

Expected: no errors.

```bash
git add web/admin/assets web/admin/locales web/admin/composables web/admin/stores web/admin/layouts web/admin/demo web/admin/tailwind.config.ts web/admin/nuxt.config.ts web/admin/app.vue
git commit -m "feat(admin): add design tokens, copy, session store, and layout

Also adds the demo fixtures the ten screens render. Dashboard validator
rate is deliberately below 100% so the K4 alert state is visible.

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 15: Admin shared components

Eight small components the ten pages compose from. Building these first is what keeps the pages short.

**Files:**
- Create: `web/admin/components/PageHeader.vue`, `StatusChip.vue`, `StatCard.vue`, `DataTable.vue`, `FilterChips.vue`, `EmptyState.vue`, `ConfirmDialog.vue`, `RoleGate.vue`

- [ ] **Step 1: PageHeader**

Create `web/admin/components/PageHeader.vue`:

```vue
<script setup lang="ts">
defineProps<{ title: string; subtitle?: string }>()
</script>

<template>
  <div class="mb-5 flex flex-wrap items-end justify-between gap-3">
    <div>
      <h1 class="text-[22px] text-primary">{{ title }}</h1>
      <p v-if="subtitle" class="meta mt-1">{{ subtitle }}</p>
    </div>
    <div class="flex items-center gap-2">
      <slot name="actions" />
    </div>
  </div>
</template>
```

- [ ] **Step 2: StatusChip**

Create `web/admin/components/StatusChip.vue`:

```vue
<script setup lang="ts">
/**
 * Admin UX section 17: no information is encoded by colour alone. Every chip
 * carries its text, and the tint is a second signal rather than the only one.
 */
withDefaults(
  defineProps<{ label: string; tone?: 'neutral' | 'success' | 'warning' | 'danger' | 'info' }>(),
  { tone: 'neutral' },
)

const toneClass: Record<string, string> = {
  neutral: 'bg-raised text-primary',
  success: 'bg-success-bg text-success',
  warning: 'bg-warning-bg text-warning',
  danger: 'bg-danger-bg text-danger',
  info: 'bg-info-bg text-info',
}
</script>

<template>
  <span
    :class="['inline-block whitespace-nowrap rounded-full px-2 py-0.5 text-[11.5px]', toneClass[tone]]"
  >
    {{ label }}
  </span>
</template>
```

- [ ] **Step 3: StatCard**

Create `web/admin/components/StatCard.vue`:

```vue
<script setup lang="ts">
withDefaults(
  defineProps<{ label: string; value: string; to?: string; alert?: boolean }>(),
  { alert: false },
)
</script>

<template>
  <component
    :is="to ? resolveComponent('NuxtLink') : 'div'"
    :to="to"
    :class="[
      'block rounded-xl border p-4 transition',
      alert ? 'border-danger/40 bg-danger-bg' : 'border-subtle bg-surface hover:border-strong',
    ]"
  >
    <p :class="['meta', alert ? 'text-danger' : '']">{{ label }}</p>
    <p :class="['mt-1 text-[24px] tabular', alert ? 'text-danger' : 'text-primary']">
      {{ value }}
    </p>
    <div class="mt-2">
      <slot />
    </div>
  </component>
</template>
```

- [ ] **Step 4: DataTable**

Create `web/admin/components/DataTable.vue`:

```vue
<script setup lang="ts">
/**
 * Admin UX section 7.3 and 16: sticky header, horizontal scroll on tablet with
 * the table never forcing the page itself to scroll sideways.
 */
defineProps<{ columns: Array<{ key: string; label: string; align?: 'right' }> }>()
</script>

<template>
  <div class="overflow-x-auto rounded-xl border border-subtle bg-surface">
    <table class="w-full min-w-[720px] border-collapse text-left">
      <thead class="sticky top-0 z-10 bg-raised">
        <tr>
          <th
            v-for="column in columns"
            :key="column.key"
            :class="[
              'whitespace-nowrap px-3 py-2.5 text-[12px] font-medium text-secondary',
              column.align === 'right' ? 'text-right' : '',
            ]"
          >
            {{ column.label }}
          </th>
        </tr>
      </thead>
      <tbody>
        <slot />
      </tbody>
    </table>
  </div>
</template>
```

- [ ] **Step 5: FilterChips**

Create `web/admin/components/FilterChips.vue`:

```vue
<script setup lang="ts">
/**
 * Section 7.2: active filters render as removable chips above the table, with
 * a single action that clears all of them.
 */
defineProps<{ filters: Array<{ key: string; label: string }> }>()
defineEmits<{ remove: [key: string]; clear: [] }>()

const { t } = useCopy()
</script>

<template>
  <div v-if="filters.length" class="mb-3 flex flex-wrap items-center gap-2">
    <button
      v-for="filter in filters"
      :key="filter.key"
      type="button"
      class="flex items-center gap-1.5 rounded-full bg-raised px-2.5 py-1 text-[12px] text-primary transition hover:bg-strong/40"
      @click="$emit('remove', filter.key)"
    >
      {{ filter.label }}
      <span aria-hidden="true" class="text-secondary">&#215;</span>
    </button>

    <button
      type="button"
      class="meta underline underline-offset-2"
      @click="$emit('clear')"
    >
      {{ t('questions.clear_filters') }}
    </button>
  </div>
</template>
```

- [ ] **Step 6: EmptyState**

Create `web/admin/components/EmptyState.vue`:

```vue
<script setup lang="ts">
/**
 * Section 5.1: an empty list explains why it might be empty and offers a way
 * out, rather than showing a bare "no results".
 */
defineProps<{ message: string }>()
</script>

<template>
  <div class="rounded-xl border border-dashed border-strong bg-surface px-6 py-10 text-center">
    <p class="text-[14px] text-secondary">{{ message }}</p>
    <div class="mt-3">
      <slot />
    </div>
  </div>
</template>
```

- [ ] **Step 7: ConfirmDialog**

Create `web/admin/components/ConfirmDialog.vue`:

```vue
<script setup lang="ts">
/**
 * Section 15 (F-37): destructive actions name the exact target, state that the
 * action is irreversible, and require an explicit confirm. There is no
 * "don't ask again".
 */
defineProps<{ open: boolean; title: string; body: string; danger?: boolean }>()
defineEmits<{ confirm: []; cancel: [] }>()

const { t } = useCopy()
</script>

<template>
  <div
    v-if="open"
    class="fixed inset-0 z-50 grid place-items-center bg-primary/40 px-6"
    role="dialog"
    aria-modal="true"
  >
    <div class="w-full max-w-md rounded-xl border border-subtle bg-surface p-5 shadow-md">
      <h2 class="text-[17px] text-primary">{{ title }}</h2>
      <p class="mt-2 text-[14px] leading-relaxed text-secondary">{{ body }}</p>
      <p v-if="danger" class="mt-2 text-[13px] text-danger">{{ t('common.irreversible') }}</p>

      <div class="mt-5 flex justify-end gap-2">
        <button
          type="button"
          class="rounded-lg border border-strong px-3 py-2 text-[13px] text-primary transition hover:bg-raised"
          @click="$emit('cancel')"
        >
          {{ t('common.cancel') }}
        </button>
        <button
          type="button"
          :class="[
            'rounded-lg px-3 py-2 text-[13px] text-on-accent transition',
            danger ? 'bg-danger hover:opacity-90' : 'bg-accent hover:bg-accent-hover',
          ]"
          @click="$emit('confirm')"
        >
          {{ t('common.confirm') }}
        </button>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 8: RoleGate**

Create `web/admin/components/RoleGate.vue`:

```vue
<script setup lang="ts">
import { useSessionStore } from '~/stores/session'

/**
 * Section 5.3: unavailable actions are hidden rather than disabled, and a
 * reviewer who navigates straight to an editor route gets a role-aware
 * message — not a blank page and not a raw 403.
 */
const props = defineProps<{ need: 'edit' | 'administer' }>()

const { t } = useCopy()
const session = useSessionStore()

const allowed = computed(() =>
  props.need === 'edit' ? session.canEdit : session.canAdminister,
)
</script>

<template>
  <slot v-if="allowed" />
  <div v-else class="rounded-xl border border-subtle bg-surface px-6 py-10 text-center">
    <p class="text-[14px] text-secondary">{{ t('common.no_access') }}</p>
  </div>
</template>
```

- [ ] **Step 9: Commit**

```bash
git add web/admin/components
git commit -m "feat(admin): add shared portal components

Chips carry their own text so no status is encoded by colour alone
(Admin UX 17), and RoleGate hides rather than disables (5.3).

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---
## Task 16: Admin login and dashboard

**Files:**
- Create: `web/admin/pages/masuk.vue`
- Modify: `web/admin/pages/index.vue`

- [ ] **Step 1: Login**

Create `web/admin/pages/masuk.vue`:

```vue
<script setup lang="ts">
import { useSessionStore, type AdminRole } from '~/stores/session'

/**
 * Real admin auth is Phase 3 (hardened admin auth) and Phase 6. In demo mode
 * the role picker stands in for it, which also lets a reviewer see the portal
 * from each of the three roles — section 5.3 hides controls by role, and that
 * is only reviewable if the role can be changed.
 */
definePageMeta({ layout: 'auth' })

const { t } = useCopy()
const session = useSessionStore()
const router = useRouter()
const demo = useDemoMode()

const email = ref('siti@tanyaiman.id')
const role = ref<AdminRole>('editor')

async function signIn() {
  session.signIn(email.value, role.value)
  await router.push('/')
}
</script>

<template>
  <div class="w-full max-w-[380px]">
    <h1 class="text-[22px] text-primary">{{ t('login.title') }}</h1>

    <label for="email" class="mt-6 block text-[13px] font-medium text-primary">
      {{ t('login.email') }}
    </label>
    <input
      id="email"
      v-model="email"
      type="email"
      class="mt-1.5 min-h-[44px] w-full rounded-lg border border-strong bg-surface px-3 text-[14px] text-primary outline-none focus:border-accent focus:ring-2 focus:ring-accent/15"
    />

    <template v-if="demo">
      <p class="meta mt-4">{{ t('login.demo_hint') }}</p>
      <div class="mt-2 grid grid-cols-3 gap-2">
        <button
          v-for="option in (['editor', 'reviewer', 'super_admin'] as AdminRole[])"
          :key="option"
          type="button"
          :class="[
            'min-h-[40px] rounded-lg border px-2 text-[12.5px] transition',
            role === option
              ? 'border-accent bg-accent text-on-accent'
              : 'border-strong text-primary hover:bg-raised',
          ]"
          @click="role = option"
        >
          {{ t(`role.${option}`) }}
        </button>
      </div>
    </template>

    <template v-else>
      <label for="password" class="mt-4 block text-[13px] font-medium text-primary">
        {{ t('login.password') }}
      </label>
      <input
        id="password"
        type="password"
        class="mt-1.5 min-h-[44px] w-full rounded-lg border border-strong bg-surface px-3 text-[14px] text-primary outline-none focus:border-accent focus:ring-2 focus:ring-accent/15"
      />
    </template>

    <button
      type="button"
      class="mt-6 min-h-[44px] w-full rounded-lg bg-accent text-[14px] font-medium text-on-accent transition hover:bg-accent-hover"
      @click="signIn"
    >
      {{ t('login.submit') }}
    </button>
  </div>
</template>
```

- [ ] **Step 2: Dashboard**

Replace `web/admin/pages/index.vue` with:

```vue
<script setup lang="ts">
import { dashboard, gaps, reviewCount, topics } from '~/demo/fixtures'
import { useSessionStore } from '~/stores/session'

/**
 * Admin UX section 6. Five cards, each linking to the view behind it.
 *
 * The answer-health card turns danger and says so plainly whenever the
 * validator pass rate is not 100%. It is a release gate (K4), and a dashboard
 * that lets it slide past as one number among five is not doing its job.
 */
const { t } = useCopy()
const session = useSessionStore()
const router = useRouter()

onMounted(() => {
  if (!session.isAuthenticated) router.replace('/masuk')
})

const validatorFailing = computed(() => dashboard.validatorPassPct < 100)
const topFive = computed(() => topics.slice(0, 5))
const largestGap = computed(() => gaps[0])
</script>

<template>
  <div>
    <PageHeader :title="t('dashboard.title')" :subtitle="t('dashboard.subtitle')" />

    <div class="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">
      <StatCard
        :label="t('dashboard.volume')"
        :value="String(dashboard.volumeThisWeek)"
        to="/pertanyaan"
      >
        <p class="meta">
          {{ t('dashboard.volume_change', { change: `+${dashboard.volumeChangePct}%` }) }}
        </p>
      </StatCard>

      <StatCard
        :label="t('dashboard.gaps')"
        :value="String(gaps.length)"
        to="/kekosongan"
      >
        <p class="meta">{{ t('dashboard.gaps_largest', { name: largestGap.canonical }) }}</p>
      </StatCard>

      <StatCard
        :label="t('dashboard.review')"
        :value="String(reviewCount)"
        to="/tinjauan"
      >
        <p class="meta">{{ t('dashboard.review_items', { count: reviewCount }) }}</p>
      </StatCard>

      <StatCard
        :label="t('dashboard.health')"
        :value="`${dashboard.validatorPassPct}%`"
        :alert="validatorFailing"
        to="/pertanyaan?validator=gagal"
      >
        <p class="meta">
          {{ t('dashboard.health_answer_rate') }} {{ dashboard.answerRatePct }}% ·
          {{ t('dashboard.health_like_rate') }} {{ dashboard.likeRatePct }}%
        </p>
        <p v-if="validatorFailing" class="mt-1.5 text-[12.5px] text-danger">
          {{ t('dashboard.health_alert') }}
        </p>
      </StatCard>

      <div class="rounded-xl border border-subtle bg-surface p-4 sm:col-span-2">
        <p class="meta">{{ t('dashboard.top_topics') }}</p>
        <ul class="mt-2 divide-y divide-subtle">
          <li
            v-for="topic in topFive"
            :key="topic.slug"
            class="flex items-center justify-between gap-3 py-2"
          >
            <NuxtLink to="/topik" class="text-[13.5px] text-primary hover:text-accent">
              {{ topic.label }}
            </NuxtLink>
            <div class="flex items-center gap-2">
              <StatusChip
                :label="t(`topics.curated_${topic.curated}`)"
                :tone="topic.curated === 'published' ? 'success' : topic.curated === 'draft' ? 'warning' : 'neutral'"
              />
              <span class="tabular text-[13px] text-secondary">{{ topic.questions }}</span>
            </div>
          </li>
        </ul>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 3: Commit**

```bash
git add web/admin/pages/masuk.vue web/admin/pages/index.vue
git commit -m "feat(admin): add login and dashboard

The answer-health card turns danger whenever validator pass rate is
below 100%, because K4 is a release gate (Admin UX 6).

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 17: Question list and detail

**Files:**
- Create: `web/admin/pages/pertanyaan/index.vue`, `web/admin/pages/pertanyaan/[id].vue`

- [ ] **Step 1: Question list**

Create `web/admin/pages/pertanyaan/index.vue`:

```vue
<script setup lang="ts">
import { questions, topics, type QuestionRow } from '~/demo/fixtures'

/**
 * Admin UX section 7. Seven columns, filters as removable chips, CSV export
 * that exports the current filter rather than the current page (F-36).
 *
 * Filter state lives in the URL query string (section 5.4) so "grief questions
 * in the last 30 days with no grounding" can be pasted into a chat message and
 * opened by a colleague.
 *
 * No phone number appears here, by design (section 7.4).
 */
const { t } = useCopy()
const route = useRoute()
const router = useRouter()

const search = ref(String(route.query.q ?? ''))
const topicFilter = ref(String(route.query.topik ?? ''))
const resultFilter = ref(String(route.query.hasil ?? ''))

watch([search, topicFilter, resultFilter], ([q, topik, hasil]) => {
  router.replace({
    query: {
      ...(q ? { q } : {}),
      ...(topik ? { topik } : {}),
      ...(hasil ? { hasil } : {}),
    },
  })
})

const rows = computed(() =>
  questions.filter((row) => {
    if (search.value && !row.question.toLowerCase().includes(search.value.toLowerCase())) return false
    if (topicFilter.value && row.topicSlug !== topicFilter.value) return false
    if (resultFilter.value && row.result !== resultFilter.value) return false
    return true
  }),
)

const activeFilters = computed(() => [
  ...(search.value ? [{ key: 'q', label: `“${search.value}”` }] : []),
  ...(topicFilter.value
    ? [{ key: 'topik', label: topics.find((t2) => t2.slug === topicFilter.value)?.label ?? topicFilter.value }]
    : []),
  ...(resultFilter.value ? [{ key: 'hasil', label: t(`result.${resultFilter.value}`) }] : []),
])

function removeFilter(key: string) {
  if (key === 'q') search.value = ''
  if (key === 'topik') topicFilter.value = ''
  if (key === 'hasil') resultFilter.value = ''
}

function clearFilters() {
  search.value = ''
  topicFilter.value = ''
  resultFilter.value = ''
}

const resultTone: Record<string, 'success' | 'warning' | 'danger' | 'info' | 'neutral'> = {
  generated: 'success',
  curated: 'success',
  refusal: 'info',
  no_grounding: 'warning',
  crisis: 'danger',
  emotional_deferral: 'info',
  error: 'danger',
}

const channelLabel: Record<string, string> = {
  web: t('common.channel_web'),
  widget: t('common.channel_widget'),
  android: t('common.channel_android'),
}

function timeLabel(iso: string): string {
  return new Date(iso).toLocaleString('id-ID', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

/**
 * F-36: exports every row matching the current filter, not the page on screen.
 * No phone number is included in any form (section 7.4).
 */
function exportCsv() {
  const header = ['waktu', 'pertanyaan', 'topik', 'hasil', 'suka', 'kanal']
  const lines = rows.value.map((row: QuestionRow) =>
    [
      row.askedAt,
      `"${row.question.replace(/"/g, '""')}"`,
      row.topicLabel,
      row.result,
      row.likes,
      row.channel,
    ].join(','),
  )
  const blob = new Blob([[header.join(','), ...lines].join('\n')], {
    type: 'text/csv;charset=utf-8',
  })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = 'pertanyaan.csv'
  link.click()
  URL.revokeObjectURL(url)
}

const columns = [
  { key: 'time', label: t('questions.col_time') },
  { key: 'question', label: t('questions.col_question') },
  { key: 'topic', label: t('questions.col_topic') },
  { key: 'result', label: t('questions.col_result') },
  { key: 'likes', label: t('questions.col_likes'), align: 'right' as const },
  { key: 'channel', label: t('questions.col_channel') },
  { key: 'flags', label: t('questions.col_flags') },
]
</script>

<template>
  <div>
    <PageHeader :title="t('questions.title')">
      <template #actions>
        <button
          type="button"
          class="rounded-lg border border-strong px-3 py-2 text-[13px] text-primary transition hover:bg-raised"
          @click="exportCsv"
        >
          {{ t('questions.export') }}
        </button>
      </template>
    </PageHeader>

    <div class="mb-3 flex flex-wrap gap-2">
      <input
        v-model="search"
        type="search"
        :placeholder="t('questions.search')"
        class="min-h-[40px] flex-1 rounded-lg border border-strong bg-surface px-3 text-[13.5px] text-primary outline-none focus:border-accent"
      />
      <select
        v-model="topicFilter"
        class="min-h-[40px] rounded-lg border border-strong bg-surface px-2 text-[13.5px] text-primary"
      >
        <option value="">{{ t('questions.col_topic') }}</option>
        <option v-for="topic in topics" :key="topic.slug" :value="topic.slug">
          {{ topic.label }}
        </option>
      </select>
      <select
        v-model="resultFilter"
        class="min-h-[40px] rounded-lg border border-strong bg-surface px-2 text-[13.5px] text-primary"
      >
        <option value="">{{ t('questions.col_result') }}</option>
        <option v-for="key in ['generated', 'curated', 'refusal', 'no_grounding', 'crisis', 'error']" :key="key" :value="key">
          {{ t(`result.${key}`) }}
        </option>
      </select>
    </div>

    <FilterChips :filters="activeFilters" @remove="removeFilter" @clear="clearFilters" />

    <EmptyState v-if="!rows.length" :message="t('questions.empty')">
      <button type="button" class="meta underline underline-offset-2" @click="clearFilters">
        {{ t('questions.clear_filters') }}
      </button>
    </EmptyState>

    <DataTable v-else :columns="columns">
      <tr
        v-for="row in rows"
        :key="row.id"
        class="border-t border-subtle transition hover:bg-raised/60"
      >
        <td class="whitespace-nowrap px-3 py-2.5 text-[12.5px] text-secondary">
          {{ timeLabel(row.askedAt) }}
        </td>
        <td class="px-3 py-2.5">
          <NuxtLink
            :to="`/pertanyaan/${row.id}`"
            class="line-clamp-2 text-[13.5px] text-primary hover:text-accent"
            :title="row.question"
          >
            {{ row.question }}
          </NuxtLink>
        </td>
        <td class="px-3 py-2.5">
          <StatusChip
            :label="row.topicLabel"
            :tone="row.topicSlug === 'lainnya' ? 'warning' : 'neutral'"
          />
        </td>
        <td class="px-3 py-2.5">
          <StatusChip :label="t(`result.${row.result}`)" :tone="resultTone[row.result]" />
        </td>
        <td class="px-3 py-2.5 text-right text-[13px] text-primary">{{ row.likes }}</td>
        <td class="px-3 py-2.5 text-[13px] text-secondary" :title="row.hostSite">
          {{ channelLabel[row.channel] }}
        </td>
        <td class="px-3 py-2.5">
          <span v-if="row.flags.includes('ambiguous')" :title="t('review.type_ambiguous')">&#9888;</span>
          <span v-if="row.flags.includes('validator')" :title="t('review.type_validator')">&#9873;</span>
        </td>
      </tr>
    </DataTable>
  </div>
</template>
```

- [ ] **Step 2: Question detail**

Create `web/admin/pages/pertanyaan/[id].vue`:

```vue
<script setup lang="ts">
import { questions, retrievedChunks, validators } from '~/demo/fixtures'
import { useSessionStore } from '~/stores/session'

/**
 * Admin UX section 8. Exchange on the left, diagnostics on the right.
 *
 * The retrieved-chunks block is the most useful diagnostic in the portal: when
 * an editor says "this answer is wrong", the next question is always "what did
 * it read?", and this answers it without an engineer. Cited chunks are marked
 * distinctly from ones that were merely retrieved.
 */
const { t } = useCopy()
const route = useRoute()
const session = useSessionStore()

const question = computed(() => questions.find((q) => q.id === route.params.id))
const confirmDelete = ref(false)
const toast = ref<string | null>(null)

function doDelete() {
  confirmDelete.value = false
  // F-37: the success toast carries the audit entry id.
  toast.value = t('common.audit_id', { id: 'a_913' })
}
</script>

<template>
  <div v-if="question">
    <PageHeader :title="t('detail.title')" :subtitle="question.id">
      <template #actions>
        <button type="button" class="meta underline underline-offset-2">
          {{ t('detail.copy_link') }}
        </button>
        <button type="button" class="meta underline underline-offset-2">
          {{ t('detail.flag') }}
        </button>
        <button
          v-if="session.canAdminister"
          type="button"
          class="rounded-lg bg-danger-bg px-3 py-2 text-[13px] text-danger transition hover:opacity-90"
          @click="confirmDelete = true"
        >
          {{ t('detail.delete') }}
        </button>
      </template>
    </PageHeader>

    <p v-if="toast" class="mb-3 rounded-lg bg-success-bg px-3 py-2 text-[13px] text-success">
      {{ toast }}
    </p>

    <div class="grid gap-4 lg:grid-cols-[minmax(0,1fr)_380px]">
      <section class="rounded-xl border border-subtle bg-surface p-4">
        <p class="meta">{{ t('detail.exchange') }}</p>

        <p class="mt-3 rounded-lg bg-raised px-3 py-2.5 text-[14px] text-primary">
          {{ question.question }}
        </p>

        <div class="mt-3 flex flex-wrap gap-2">
          <StatusChip :label="question.topicLabel" />
          <StatusChip :label="t(`result.${question.result}`)" tone="info" />
          <StatusChip :label="`${question.likes} suka`" />
        </div>

        <p class="mt-4 whitespace-pre-wrap text-[14px] leading-relaxed text-primary">
          Kitab Suci memperkenalkan Isa Al-Masih sebagai Firman Allah yang menjadi
          manusia. Ia disebut telah ada sejak semula bersama Allah, lalu hadir di
          tengah manusia untuk menyatakan kasih dan kebenaran-Nya.
        </p>

        <ul class="mt-4 space-y-1.5 border-t border-subtle pt-3">
          <li v-for="chunk in retrievedChunks.filter((c) => c.cited)" :key="chunk.id">
            <a
              :href="`https://${chunk.site}`"
              target="_blank"
              rel="noopener noreferrer"
              class="text-[13px] text-accent underline underline-offset-2"
            >
              {{ chunk.articleTitle }}
            </a>
            <span class="meta block">{{ chunk.site }}</span>
          </li>
        </ul>
      </section>

      <aside class="space-y-4">
        <section class="rounded-xl border border-subtle bg-surface p-4">
          <p class="meta">{{ t('detail.classification') }}</p>
          <div class="mt-2 flex items-center gap-2">
            <StatusChip label="Teologi" tone="success" />
            <span class="tabular text-[13px] text-secondary">0,94</span>
          </div>
        </section>

        <section class="rounded-xl border border-subtle bg-surface p-4">
          <p class="meta">{{ t('detail.retrieved') }}</p>
          <ul class="mt-2 space-y-2.5">
            <li
              v-for="chunk in retrievedChunks"
              :key="chunk.id"
              class="rounded-lg border border-subtle p-2.5"
            >
              <div class="flex items-start justify-between gap-2">
                <p class="text-[13px] text-primary">{{ chunk.articleTitle }}</p>
                <span class="tabular text-[12px] text-secondary">{{ chunk.score.toFixed(2) }}</span>
              </div>
              <div class="mt-1.5">
                <StatusChip
                  :label="chunk.cited ? t('detail.cited') : t('detail.retrieved_only')"
                  :tone="chunk.cited ? 'success' : 'neutral'"
                />
              </div>
              <p class="meta mt-1.5 line-clamp-2">{{ chunk.text }}</p>
            </li>
          </ul>
        </section>

        <section class="rounded-xl border border-subtle bg-surface p-4">
          <p class="meta">{{ t('detail.validation') }}</p>
          <ul class="mt-2 space-y-1.5">
            <li
              v-for="validator in validators"
              :key="validator.code"
              class="flex items-center justify-between gap-2 text-[13px]"
            >
              <span class="text-primary">{{ validator.code }} {{ validator.label }}</span>
              <StatusChip
                :label="validator.pass ? 'Lolos' : 'Gagal'"
                :tone="validator.pass ? 'success' : 'danger'"
              />
            </li>
          </ul>
          <p class="meta mt-2">{{ validators[0].measured }}</p>
        </section>

        <section class="rounded-xl border border-subtle bg-surface p-4">
          <p class="meta">{{ t('detail.technical') }}</p>
          <dl class="mt-2 space-y-1 text-[12.5px]">
            <div class="flex justify-between gap-2">
              <dt class="text-secondary">Model</dt>
              <dd class="text-primary">claude-sonnet-class</dd>
            </div>
            <div class="flex justify-between gap-2">
              <dt class="text-secondary">prompt_version</dt>
              <dd class="tabular text-primary">v3</dd>
            </div>
            <div class="flex justify-between gap-2">
              <dt class="text-secondary">Latensi</dt>
              <dd class="tabular text-primary">4.120 ms</dd>
            </div>
          </dl>
        </section>
      </aside>
    </div>

    <ConfirmDialog
      :open="confirmDelete"
      :title="t('detail.delete')"
      :body="`${question.question}`"
      danger
      @confirm="doDelete"
      @cancel="confirmDelete = false"
    />
  </div>
</template>
```

- [ ] **Step 3: Commit**

```bash
git add web/admin/pages/pertanyaan
git commit -m "feat(admin): add question list and detail

Filters live in the URL so a filtered view can be pasted to a colleague
(5.4). Export covers the filter, not the page (F-36). No phone number
appears in either view (7.4).

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 18: Topics, clusters, gaps, review queue

Four list screens sharing the same shape.

**Files:**
- Create: `web/admin/pages/topik.vue`, `serupa.vue`, `kekosongan.vue`, `tinjauan.vue`

- [ ] **Step 1: Topics**

Create `web/admin/pages/topik.vue`:

```vue
<script setup lang="ts">
import { topics } from '~/demo/fixtures'
import { useSessionStore } from '~/stores/session'

/**
 * Admin UX section 9. Sorted by question count descending, so read top-down
 * this table is the editorial priority list — the highest-demand topic without
 * a curated answer is the first row the eye lands on.
 */
const { t } = useCopy()
const session = useSessionStore()

const sorted = computed(() => [...topics].sort((a, b) => b.questions - a.questions))

const totalQuestions = computed(() => topics.reduce((sum, t2) => sum + t2.questions, 0))
const lainnya = computed(() => topics.find((t2) => t2.slug === 'lainnya'))
/** PRD Appendix A: past 10%, the taxonomy needs a new topic. */
const lainnyaHigh = computed(
  () => !!lainnya.value && lainnya.value.questions / totalQuestions.value > 0.1,
)

const columns = [
  { key: 'topic', label: t('topics.col_topic') },
  { key: 'questions', label: t('topics.col_questions'), align: 'right' as const },
  { key: 'likes', label: t('topics.col_likes'), align: 'right' as const },
  { key: 'curated', label: t('topics.col_curated') },
  { key: 'refusal', label: t('topics.col_refusal'), align: 'right' as const },
  { key: 'action', label: '' },
]
</script>

<template>
  <div>
    <PageHeader :title="t('topics.title')" />

    <p v-if="lainnyaHigh" class="mb-3 rounded-lg bg-warning-bg px-3 py-2 text-[13px] text-warning">
      {{ t('topics.lainnya_warning') }}
    </p>

    <DataTable :columns="columns">
      <tr
        v-for="topic in sorted"
        :key="topic.slug"
        class="border-t border-subtle transition hover:bg-raised/60"
      >
        <td class="px-3 py-2.5 text-[13.5px] text-primary">
          {{ topic.label }}
        </td>
        <td class="px-3 py-2.5 text-right text-[13px] text-primary">{{ topic.questions }}</td>
        <td class="px-3 py-2.5 text-right text-[13px] text-secondary">{{ topic.likes }}</td>
        <td class="px-3 py-2.5">
          <StatusChip
            :label="t(`topics.curated_${topic.curated}`)"
            :tone="topic.curated === 'published' ? 'success' : topic.curated === 'draft' ? 'warning' : 'neutral'"
          />
          <span v-if="topic.curatedBy" class="meta mt-0.5 block">
            {{ topic.curatedBy }} · {{ topic.curatedAt }}
          </span>
        </td>
        <td class="px-3 py-2.5 text-right text-[13px]" :class="topic.refusalRate > 0.15 ? 'text-warning' : 'text-secondary'">
          {{ Math.round(topic.refusalRate * 100) }}%
        </td>
        <td class="px-3 py-2.5 text-right">
          <NuxtLink
            v-if="session.canEdit"
            :to="`/editor/${topic.slug}`"
            class="text-[13px] text-accent underline underline-offset-2"
          >
            {{ topic.curated === 'none' ? t('topics.write') : t('topics.edit') }}
          </NuxtLink>
        </td>
      </tr>
    </DataTable>
  </div>
</template>
```

- [ ] **Step 2: Clusters**

Create `web/admin/pages/serupa.vue`:

```vue
<script setup lang="ts">
import { clusters } from '~/demo/fixtures'
import { useSessionStore } from '~/stores/session'

/**
 * Admin UX section 11. Sorted by member count descending — read from the top,
 * this list is the content queue.
 *
 * Expanding a cluster shows its members in their original wording, which is
 * where the editorial insight lives: the canonical phrasing tells you the
 * theme, the raw wording tells you how people actually talk about it.
 */
const { t } = useCopy()
const session = useSessionStore()

const expanded = ref<string | null>(null)
const sorted = computed(() => [...clusters].sort((a, b) => b.count - a.count))

function timeLabel(iso: string): string {
  return new Date(iso).toLocaleDateString('id-ID', { day: '2-digit', month: 'short' })
}
</script>

<template>
  <div>
    <PageHeader :title="t('clusters.title')" />

    <div class="space-y-2">
      <div
        v-for="cluster in sorted"
        :key="cluster.id"
        class="rounded-xl border border-subtle bg-surface"
      >
        <button
          type="button"
          class="flex w-full items-center gap-3 px-4 py-3 text-left"
          :aria-expanded="expanded === cluster.id"
          @click="expanded = expanded === cluster.id ? null : cluster.id"
        >
          <span class="tabular w-10 shrink-0 text-[15px] text-primary">{{ cluster.count }}</span>
          <span class="min-w-0 flex-1">
            <span class="block text-[13.5px] text-primary">{{ cluster.canonical }}</span>
            <span class="meta">
              {{ cluster.topicLabel }} · {{ t('clusters.col_last') }} {{ timeLabel(cluster.lastAsked) }}
            </span>
          </span>
          <StatusChip
            :label="cluster.hasCurated ? t('topics.curated_published') : t('topics.curated_none')"
            :tone="cluster.hasCurated ? 'success' : 'neutral'"
          />
        </button>

        <div v-if="expanded === cluster.id" class="border-t border-subtle px-4 py-3">
          <p class="meta mb-2">{{ t('clusters.members') }}</p>
          <ul class="space-y-1.5">
            <li v-for="member in cluster.members" :key="member" class="text-[13px] text-secondary">
              {{ member }}
            </li>
          </ul>
          <NuxtLink
            v-if="session.canEdit"
            to="/editor/pengampunan"
            class="mt-3 inline-block text-[13px] text-accent underline underline-offset-2"
          >
            {{ t('clusters.make_curated') }}
          </NuxtLink>
        </div>
      </div>
    </div>
  </div>
</template>
```

- [ ] **Step 3: Content gaps**

Create `web/admin/pages/kekosongan.vue`:

```vue
<script setup lang="ts">
import { gaps } from '~/demo/fixtures'

/**
 * Admin UX section 12. The highest-value output of the product for editorial:
 * everything else tells them what they have, this tells them what is missing.
 *
 * A gap cannot be marked resolved by assertion — the state is derived from the
 * corpus after the next ingestion run confirms the question is now answerable.
 */
const { t } = useCopy()

const sorted = computed(() => [...gaps].sort((a, b) => b.count - a.count))

const columns = [
  { key: 'canonical', label: t('gaps.col_canonical') },
  { key: 'count', label: t('gaps.col_count'), align: 'right' as const },
  { key: 'last', label: t('gaps.col_last') },
  { key: 'topic', label: t('gaps.col_topic') },
  { key: 'action', label: '' },
]

function timeLabel(iso: string): string {
  return new Date(iso).toLocaleDateString('id-ID', { day: '2-digit', month: 'short' })
}
</script>

<template>
  <div>
    <PageHeader :title="t('gaps.title')" :subtitle="t('gaps.subtitle')" />

    <DataTable :columns="columns">
      <tr
        v-for="gap in sorted"
        :key="gap.id"
        class="border-t border-subtle transition hover:bg-raised/60"
      >
        <td class="px-3 py-2.5 text-[13.5px] text-primary">{{ gap.canonical }}</td>
        <td class="px-3 py-2.5 text-right text-[13px] text-primary">{{ gap.count }}</td>
        <td class="px-3 py-2.5 text-[12.5px] text-secondary">{{ timeLabel(gap.lastAsked) }}</td>
        <td class="px-3 py-2.5">
          <StatusChip :label="gap.nearestTopic" :tone="gap.nearestTopic === 'Lainnya' ? 'warning' : 'neutral'" />
        </td>
        <td class="px-3 py-2.5 text-right">
          <button type="button" class="text-[13px] text-accent underline underline-offset-2">
            {{ t('gaps.resolved') }}
          </button>
        </td>
      </tr>
    </DataTable>

    <p class="meta mt-3 max-w-[70ch]">{{ t('gaps.resolved_note') }}</p>
  </div>
</template>
```

- [ ] **Step 4: Review queue**

Create `web/admin/pages/tinjauan.vue`:

```vue
<script setup lang="ts">
import { reviews } from '~/demo/fixtures'

/**
 * Admin UX section 13. One worklist, four sources.
 *
 * Crisis and emotional-deferral records are visible to every admin role but
 * carry a standing notice that they are sensitive and must not leave the
 * portal.
 */
const { t } = useCopy()

const items = ref([...reviews])

const toneFor: Record<string, 'warning' | 'danger' | 'info'> = {
  ambiguous: 'warning',
  validator: 'danger',
  crisis: 'danger',
  emotional: 'info',
}

function markReviewed(id: string) {
  const item = items.value.find((i) => i.id === id)
  if (item) item.reviewed = true
}

function timeLabel(iso: string): string {
  return new Date(iso).toLocaleString('id-ID', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}

const columns = [
  { key: 'type', label: t('review.col_type') },
  { key: 'summary', label: t('review.col_summary') },
  { key: 'time', label: t('review.col_time') },
  { key: 'action', label: '' },
]
</script>

<template>
  <div>
    <PageHeader :title="t('review.title')" />

    <p class="mb-3 rounded-lg bg-info-bg px-3 py-2 text-[13px] text-info">
      {{ t('review.sensitive') }}
    </p>

    <DataTable :columns="columns">
      <tr
        v-for="item in items"
        :key="item.id"
        :class="['border-t border-subtle', item.reviewed ? 'opacity-55' : '']"
      >
        <td class="px-3 py-2.5">
          <StatusChip :label="t(`review.type_${item.type}`)" :tone="toneFor[item.type]" />
        </td>
        <td class="px-3 py-2.5 text-[13.5px] text-primary">{{ item.summary }}</td>
        <td class="px-3 py-2.5 text-[12.5px] text-secondary">{{ timeLabel(item.at) }}</td>
        <td class="px-3 py-2.5 text-right">
          <button
            v-if="!item.reviewed"
            type="button"
            class="text-[13px] text-accent underline underline-offset-2"
            @click="markReviewed(item.id)"
          >
            {{ t('review.mark_reviewed') }}
          </button>
          <span v-else class="meta">&#10003;</span>
        </td>
      </tr>
    </DataTable>
  </div>
</template>
```

- [ ] **Step 5: Commit**

```bash
git add web/admin/pages/topik.vue web/admin/pages/serupa.vue web/admin/pages/kekosongan.vue web/admin/pages/tinjauan.vue
git commit -m "feat(admin): add topics, clusters, gaps, and review queue

Topics sorts by demand so the table reads as the editorial priority
list (9). Gaps states plainly that resolution is derived from the
corpus, not asserted (12).

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 19: Curated answer editor

The one screen where an editor writes rather than reads. The live rule panel has to make the rules feel like guardrails, not like a rejection at the end.

**Files:**
- Create: `web/admin/pages/editor/[slug].vue`

- [ ] **Step 1: Write the editor**

Create `web/admin/pages/editor/[slug].vue`:

```vue
<script setup lang="ts">
import { countWords, MAX_WORDS, MIN_WORDS } from '@tanya-iman/shared'
import { articles, topics } from '~/demo/fixtures'

/**
 * Admin UX section 10 (F-23, F-34).
 *
 * The word counter imports countWords from web/shared, which is a deliberate
 * port of backend/services/text.py. If this counter said 249 and the backend
 * said 251, the editor would stop trusting the tool and the whole idea of live
 * validation would be worth less than nothing.
 *
 * Not offered below 768px (section 16): writing a 250-word answer against live
 * validation on a phone is not a workflow worth designing for.
 */
const { t } = useCopy()
const route = useRoute()

const topic = computed(() => topics.find((tp) => tp.slug === route.params.slug))

const answer = ref('')
const selectedCitations = ref<string[]>([])
const citationSearch = ref('')
const showPublishConfirm = ref(false)
const toast = ref<string | null>(null)

/** V1 — length, counted with the backend's own function. */
const words = computed(() => countWords(answer.value))
const lengthOk = computed(() => words.value >= MIN_WORDS && words.value <= MAX_WORDS)

/**
 * V2 — terminology. The corpus and the product use "Allah" and "Isa Al-Masih";
 * "Tuhan" and "Yesus" are the two substitutions that must not reach a seeker.
 */
const BANNED = ['Tuhan', 'Yesus']
const bannedFound = computed(() =>
  BANNED.filter((word) => new RegExp(`\\b${word}\\b`, 'i').test(answer.value)),
)
const terminologyOk = computed(() => bannedFound.value.length === 0)

/** V3 — scripture balance, stated in words rather than as a code. */
const quranRefs = computed(() => (answer.value.match(/Q\.?S\.?\s?\d+/gi) ?? []).length)
const scriptureRefs = computed(
  () => (answer.value.match(/\b(Yohanes|Matius|Lukas|Markus|Mazmur|Kejadian)\b/gi) ?? []).length,
)

/** V4 — one or two citations, from approved sites only. */
const citationsOk = computed(
  () => selectedCitations.value.length >= 1 && selectedCitations.value.length <= 2,
)

const canPublish = computed(
  () => lengthOk.value && terminologyOk.value && citationsOk.value,
)

const filteredArticles = computed(() =>
  articles.filter((a) =>
    citationSearch.value
      ? a.title.toLowerCase().includes(citationSearch.value.toLowerCase())
      : true,
  ),
)

function toggleCitation(id: string) {
  const index = selectedCitations.value.indexOf(id)
  if (index >= 0) selectedCitations.value.splice(index, 1)
  else if (selectedCitations.value.length < 2) selectedCitations.value.push(id)
}

function saveDraft() {
  toast.value = t('common.saved')
}

function publish() {
  showPublishConfirm.value = false
  toast.value = t('common.saved')
}
</script>

<template>
  <RoleGate need="edit">
    <div>
      <PageHeader :title="t('editor.title')" :subtitle="topic?.label">
        <template #actions>
          <button
            type="button"
            class="rounded-lg border border-strong px-3 py-2 text-[13px] text-primary transition hover:bg-raised"
            @click="saveDraft"
          >
            {{ t('editor.save_draft') }}
          </button>
          <button
            type="button"
            :disabled="!canPublish"
            class="rounded-lg bg-accent px-3 py-2 text-[13px] text-on-accent transition hover:bg-accent-hover disabled:opacity-40"
            @click="showPublishConfirm = true"
          >
            {{ t('editor.publish') }}
          </button>
        </template>
      </PageHeader>

      <p v-if="toast" class="mb-3 rounded-lg bg-success-bg px-3 py-2 text-[13px] text-success">
        {{ toast }}
      </p>

      <!-- Section 16: the editor is not offered below 768px. -->
      <p class="rounded-lg bg-warning-bg px-3 py-2 text-[13px] text-warning md:hidden">
        {{ t('editor.too_narrow') }}
      </p>

      <div class="hidden gap-4 md:grid md:grid-cols-[minmax(0,1fr)_300px]">
        <section>
          <label for="answer" class="block text-[13px] font-medium text-primary">
            {{ t('editor.answer_label') }}
          </label>
          <textarea
            id="answer"
            v-model="answer"
            rows="14"
            class="mt-1.5 w-full resize-y rounded-xl border border-strong bg-surface p-3 text-[14px] leading-relaxed text-primary outline-none focus:border-accent focus:ring-2 focus:ring-accent/15"
          />

          <p class="meta mt-2">{{ t('editor.draft_notice') }}</p>

          <div class="mt-5">
            <label for="citation-search" class="block text-[13px] font-medium text-primary">
              {{ t('editor.rule_citations') }}
            </label>
            <!-- Section 10: no free-text URL field exists, so an off-allowlist
                 link cannot be entered at all. -->
            <input
              id="citation-search"
              v-model="citationSearch"
              type="search"
              :placeholder="t('editor.citation_search')"
              class="mt-1.5 min-h-[40px] w-full rounded-lg border border-strong bg-surface px-3 text-[13.5px] text-primary outline-none focus:border-accent"
            />
            <ul class="mt-2 space-y-1.5">
              <li v-for="article in filteredArticles" :key="article.id">
                <button
                  type="button"
                  :class="[
                    'flex w-full items-start gap-2 rounded-lg border px-3 py-2 text-left transition',
                    selectedCitations.includes(article.id)
                      ? 'border-accent bg-info-bg'
                      : 'border-subtle hover:bg-raised',
                  ]"
                  @click="toggleCitation(article.id)"
                >
                  <span class="min-w-0 flex-1">
                    <span class="block text-[13px] text-primary">{{ article.title }}</span>
                    <span class="meta">{{ article.site }}</span>
                  </span>
                  <span v-if="selectedCitations.includes(article.id)" class="text-accent">&#10003;</span>
                </button>
              </li>
            </ul>
          </div>
        </section>

        <!-- The live rule panel. Updates per keystroke. -->
        <aside class="space-y-2.5">
          <p class="meta">{{ t('editor.rules') }}</p>

          <div
            :class="[
              'rounded-lg border px-3 py-2.5',
              lengthOk ? 'border-success/40 bg-success-bg' : 'border-danger/40 bg-danger-bg',
            ]"
          >
            <p :class="['text-[12px]', lengthOk ? 'text-success' : 'text-danger']">
              V1 {{ t('editor.rule_length') }}
            </p>
            <p :class="['tabular mt-0.5 text-[13.5px]', lengthOk ? 'text-success' : 'text-danger']">
              {{ t('editor.words', { count: words }) }}
            </p>
          </div>

          <div
            :class="[
              'rounded-lg border px-3 py-2.5',
              terminologyOk ? 'border-success/40 bg-success-bg' : 'border-danger/40 bg-danger-bg',
            ]"
            aria-live="polite"
          >
            <p :class="['text-[12px]', terminologyOk ? 'text-success' : 'text-danger']">
              V2 {{ t('editor.rule_terminology') }}
            </p>
            <p :class="['mt-0.5 text-[13px]', terminologyOk ? 'text-success' : 'text-danger']">
              {{
                terminologyOk
                  ? t('editor.terminology_ok')
                  : t('editor.terminology_bad', { word: bannedFound[0] })
              }}
            </p>
          </div>

          <div class="rounded-lg border border-subtle bg-surface px-3 py-2.5">
            <p class="meta">V3 {{ t('editor.rule_scripture') }}</p>
            <p class="mt-0.5 text-[13px] text-primary">
              {{ quranRefs }} rujukan Quran, {{ scriptureRefs }} rujukan Kitab Suci
            </p>
          </div>

          <div
            :class="[
              'rounded-lg border px-3 py-2.5',
              citationsOk ? 'border-success/40 bg-success-bg' : 'border-subtle bg-surface',
            ]"
          >
            <p :class="['text-[12px]', citationsOk ? 'text-success' : 'text-secondary']">
              V4 {{ t('editor.rule_citations') }}
            </p>
            <p :class="['tabular mt-0.5 text-[13px]', citationsOk ? 'text-success' : 'text-primary']">
              {{ t('editor.citations_count', { count: selectedCitations.length }) }}
            </p>
          </div>
        </aside>
      </div>

      <ConfirmDialog
        :open="showPublishConfirm"
        :title="t('editor.publish')"
        :body="t('editor.publish_confirm')"
        @confirm="publish"
        @cancel="showPublishConfirm = false"
      />
    </div>
  </RoleGate>
</template>
```

- [ ] **Step 2: Verify the counter agrees with the backend**

The editor's counter must match `backend/services/text.py` exactly. The shared test already covers the edge cases; confirm it passes:

```bash
npm test --workspace web/shared
cd backend && uv run pytest tests/test_text.py -v && cd ..
```

Expected: both PASS.

- [ ] **Step 3: Commit**

```bash
git add web/admin/pages/editor
git commit -m "feat(admin): add curated answer editor with live rule panel

Word count imports countWords from web/shared, the port of the backend
validator — a counter that disagrees with the backend makes live
validation worth less than nothing (Admin UX 10).

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 20: Settings

**Files:**
- Create: `web/admin/pages/pengaturan.vue`

- [ ] **Step 1: Write the page**

Create `web/admin/pages/pengaturan.vue`:

```vue
<script setup lang="ts">
import { audit } from '~/demo/fixtures'

/**
 * Admin UX section 14. super_admin only.
 *
 * The support contact (F-45) is deliberately shown as unset: the number and
 * the emotional-deferral copy behind it are owned by the client's pastoral
 * team (SOW dependency B1), and the template still carries its PLACEHOLDER
 * marker. Shipping an invented number here would be worse than showing none.
 */
const { t } = useCopy()

const columns = [
  { key: 'actor', label: t('settings.col_actor') },
  { key: 'action', label: t('settings.col_action') },
  { key: 'target', label: t('settings.col_target') },
  { key: 'time', label: t('settings.col_time') },
]

function timeLabel(iso: string): string {
  return new Date(iso).toLocaleString('id-ID', {
    day: '2-digit',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<template>
  <RoleGate need="administer">
    <div>
      <PageHeader :title="t('settings.title')" />

      <div class="grid gap-4 lg:grid-cols-2">
        <section class="rounded-xl border border-subtle bg-surface p-4">
          <h2 class="text-[15px] text-primary">{{ t('settings.system') }}</h2>

          <dl class="mt-3 space-y-3">
            <div>
              <dt class="text-[13px] text-primary">{{ t('settings.retention') }}</dt>
              <dd class="tabular text-[13px] text-secondary">12</dd>
            </div>
            <div>
              <dt class="text-[13px] text-primary">{{ t('settings.rate_limit') }}</dt>
              <dd class="tabular text-[13px] text-secondary">30</dd>
            </div>
            <div>
              <dt class="text-[13px] text-primary">{{ t('settings.similarity') }}</dt>
              <dd class="tabular text-[13px] text-secondary">0,72</dd>
              <p class="mt-1 rounded-lg bg-warning-bg px-2.5 py-1.5 text-[12.5px] text-warning">
                {{ t('settings.similarity_warning') }}
              </p>
            </div>
          </dl>
        </section>

        <section class="rounded-xl border border-subtle bg-surface p-4">
          <h2 class="text-[15px] text-primary">{{ t('settings.contact') }}</h2>

          <p class="mt-3 rounded-lg bg-warning-bg px-3 py-2 text-[13px] text-warning">
            {{ t('settings.contact_pending') }}
          </p>

          <label class="mt-3 block text-[13px] text-primary">{{ t('settings.contact_name') }}</label>
          <input
            type="text"
            disabled
            class="mt-1 min-h-[40px] w-full rounded-lg border border-subtle bg-raised px-3 text-[13.5px] text-secondary"
          />

          <label class="mt-3 block text-[13px] text-primary">{{ t('settings.contact_number') }}</label>
          <input
            type="tel"
            disabled
            class="mt-1 min-h-[40px] w-full rounded-lg border border-subtle bg-raised px-3 text-[13.5px] text-secondary"
          />
        </section>

        <section class="rounded-xl border border-subtle bg-surface p-4">
          <h2 class="text-[15px] text-primary">{{ t('settings.corpus') }}</h2>
          <p class="meta mt-2">{{ t('settings.last_run') }}: 7 Sep 2026, 02:00</p>
          <p class="meta">5 situs · 1.284 artikel · 9.412 potongan</p>
          <button
            type="button"
            class="mt-3 rounded-lg border border-strong px-3 py-2 text-[13px] text-primary transition hover:bg-raised"
          >
            {{ t('settings.run_ingestion') }}
          </button>
        </section>

        <section class="rounded-xl border border-subtle bg-surface p-4">
          <h2 class="text-[15px] text-primary">{{ t('settings.accounts') }}</h2>
          <ul class="mt-2 divide-y divide-subtle">
            <li class="flex items-center justify-between py-2">
              <span class="text-[13px] text-primary">siti@tanyaiman.id</span>
              <StatusChip :label="t('role.editor')" />
            </li>
            <li class="flex items-center justify-between py-2">
              <span class="text-[13px] text-primary">budi@tanyaiman.id</span>
              <StatusChip :label="t('role.reviewer')" />
            </li>
            <li class="flex items-center justify-between py-2">
              <span class="text-[13px] text-primary">admin@tanyaiman.id</span>
              <StatusChip :label="t('role.super_admin')" tone="info" />
            </li>
          </ul>
        </section>
      </div>

      <h2 class="mt-6 text-[15px] text-primary">{{ t('settings.audit') }}</h2>
      <div class="mt-2">
        <DataTable :columns="columns">
          <tr v-for="entry in audit" :key="entry.id" class="border-t border-subtle">
            <td class="px-3 py-2.5 text-[13px] text-primary">{{ entry.actor }}</td>
            <td class="px-3 py-2.5 text-[13px] text-primary">{{ entry.action }}</td>
            <td class="px-3 py-2.5 text-[13px] text-secondary">{{ entry.target }}</td>
            <td class="px-3 py-2.5 text-[12.5px] text-secondary">{{ timeLabel(entry.at) }}</td>
          </tr>
        </DataTable>
      </div>
    </div>
  </RoleGate>
</template>
```

- [ ] **Step 2: Build and verify**

```bash
npm run typecheck --workspace web/admin && npm run build:admin
```

Expected: both succeed.

- [ ] **Step 3: Commit**

```bash
git add web/admin/pages/pengaturan.vue
git commit -m "feat(admin): add settings with audit log

The F-45 support contact is shown unset rather than filled with an
invented number — it is owned by the client's pastoral team (SOW B1).

Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>"
```

---

## Task 21: Full verification pass

Nothing here writes code. This is the evidence that the work is what it claims to be.

- [ ] **Step 1: All automated suites**

```bash
npm test --workspace web/shared
npm run typecheck --workspaces --if-present
cd backend && uv run pytest -v && cd ..
```

Expected: all PASS. `test_copy_parity.py` in particular must be green — it proves the locale edits did not touch anything under `shared`.

- [ ] **Step 2: No component names a colour**

```bash
grep -rnE "(emerald|slate|sky|indigo|rose|amber|gray|zinc|neutral|stone)-[0-9]{2,3}" web/app/components web/app/pages web/admin/components web/admin/pages web/admin/layouts
```

Expected: no output. The one permitted exception is `web/app/pages/widget-demo.vue`, which uses inline hex to imitate somebody else's website — if it appears, confirm the match is inside that file and is a `style` attribute, not a Tailwind class.

- [ ] **Step 3: No hardcoded user-facing string**

Open each page and component changed in this branch and confirm every visible string is a `t(...)` call. The known exceptions, all deliberate:
- `web/app/pages/privasi.vue` — interim policy text, replaced by the client's published policy (SOW B9)
- `web/app/pages/widget-demo.vue` — the simulated host article, which is not product copy
- `web/admin/pages/pengaturan.vue` and `pertanyaan/[id].vue` — demo values (`0,72`, `claude-sonnet-class`, sample answer body), which are fixtures rather than UI copy

- [ ] **Step 4: Both apps build**

```bash
npm run build:app && npm run build:admin
```

Expected: both succeed, producing `web/app/.output/public` and `web/admin/.output/public` — the exact paths the two hosting targets in `firebase.json` already point at.

- [ ] **Step 5: Demo build and manual sweep**

Build both apps in demo mode:

```bash
NUXT_PUBLIC_DEMO_MODE=1 npm run build:app
NUXT_PUBLIC_DEMO_MODE=1 npm run build:admin
```

PowerShell:

```powershell
$env:NUXT_PUBLIC_DEMO_MODE=1; npm run build:app; npm run build:admin
```

Then serve and walk through this checklist, which is taken from the two specs' own acceptance lists:

**Seeker**
- [ ] All three sign-in options are the same size on the welcome screen (F-1)
- [ ] The privacy link is reachable from welcome, sign-in, chat, and inside the widget (F-4)
- [ ] The source note stays put when the transcript scrolls (F-6)
- [ ] Send is disabled while pending but the textarea still accepts typing (F-26)
- [ ] *Coba lagi* resends without retyping (F-27)
- [ ] Refusal, no-grounding, and crisis are each distinguishable with colour removed
- [ ] The crisis card has no like control and no citations (F-30)
- [ ] Like is reversible and shows no count (F-17, F-33)
- [ ] Citations show the title with the domain beneath
- [ ] The layout holds at 320px in both the app and the widget
- [ ] Text at 200% zoom does not clip
- [ ] Tab reaches the input, send, every citation, and every like control

**Admin**
- [ ] Reaching the top topic without a curated answer takes two interactions from login
- [ ] Question filters survive a page reload via the URL
- [ ] No phone number appears in any list view or in the CSV export
- [ ] Question detail marks cited chunks distinctly from merely-retrieved ones
- [ ] Typing "Yesus" in the editor turns V2 red and blocks publish
- [ ] A citation outside the approved sites cannot be entered
- [ ] Publishing shows the confirmation stating the answer goes live immediately
- [ ] Signing in as `reviewer` shows no editing controls anywhere
- [ ] Destructive delete confirms with the target named and returns an audit ID
- [ ] The dashboard answer-health card is in its alert state

- [ ] **Step 6: Push the branch**

```bash
git push -u origin feature/ui-design-system
```

- [ ] **Step 7: Open the PR into `dev`**

`dev` must exist on the remote first:

```bash
git push origin dev:dev
```

Then open the PR:

```bash
gh pr create --base dev --head feature/ui-design-system \
  --title "UI design system and client approval mockup" \
  --body "$(cat <<'BODY'
## Problem

The seeker and admin apps were functionally scaffolded but had no presentation layer — no colour tokens, no typography scale, no layouts, and `web/admin` was a single empty page. Separately, the client needs a browsable surface to approve a visual direction before Phases 5 and 6 build on top of it.

## Approach

Treats those as one problem. Builds the design layer for real against the existing scaffold, and adds a fixture-backed demo mode (`NUXT_PUBLIC_DEMO_MODE=1`) so the result can be hosted statically for approval without a backend. Nothing here is throwaway.

Spec: `docs/superpowers/specs/2026-09-08-ui-design-system-design.md`

## What changed

- **Design tokens** in `web/shared/src/tokens.ts`, held to WCAG 2.1 AA by test rather than by eye
- **Seeker app**: the four routes of Chat UX section 3, all seven response states, citations, like, embed mode, and a WordPress widget preview page
- **Admin portal**: all ten pages of Admin UX section 3, including the curated answer editor with a live rule panel whose word counter imports the backend's own port from `web/shared`
- **Demo mode**: fixtures behind the `ApiClient` interface, swapped at the `useApi` seam

## Deliberately not included

- Real answers, retrieval, or any LLM call (Phase 5)
- Real authentication (Phase 3)
- Dark mode (post-v1.0, Chat UX section 16)
- Any change to backend behaviour, prompts, or validators
- The crisis script and helpline numbers — owned by the client's pastoral team (SOW B1); the mockup shows the card's shape with a visible note that the numbers are unapproved
- The F-45 support contact, shown unset for the same reason

## Sample content

The eight sample answers are demo content written for this branch and are **not editorially approved**. Template copy (greeting, refusal, no-grounding, rate limit, error) is unchanged and still comes from `locales/id.json`, byte-identical to `backend/config/responses.id.yml` — `test_copy_parity.py` is green.

## Verification

- `npm test --workspace web/shared` — contrast and word-count suites pass
- `npm run typecheck --workspaces` — clean
- `backend`: `uv run pytest -v` — green, including `test_copy_parity.py`
- Both apps build to the paths `firebase.json` already targets
- Manual sweep against both specs' acceptance checklists

🤖 Generated with [Claude Code](https://claude.com/claude-code)
BODY
)"
```

- [ ] **Step 8: Report back**

Give the reviewer the PR URL, and state plainly which acceptance items passed and which did not. If any item failed, say so — do not describe the branch as ready while an item is outstanding.

---

## Spec coverage

| Spec section | Task |
|---|---|
| 3.1 Token layer | 1, 2, 3, 13 |
| 3.2 Typography | 3, 13 |
| 4 Seeker — routes | 9 |
| 4 Seeker — response states | 6, 7, 8, 10 |
| 4 Seeker — citations, like | 7, 8 |
| 4 Seeker — embed mode | 11, 12 |
| 5 Admin — all ten pages | 13, 15, 16, 17, 18, 19, 20 |
| 6 Demo data | 5, 14 |
| 7 Delivery | 21 |
| 8 Testing | 1, 2, 19, 21 |
