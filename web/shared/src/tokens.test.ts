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
