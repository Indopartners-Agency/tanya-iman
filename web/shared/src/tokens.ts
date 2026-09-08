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
