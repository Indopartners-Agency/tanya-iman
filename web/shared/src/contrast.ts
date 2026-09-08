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
  if (!match?.[1]) throw new Error(`Not a hex colour: ${hex}`)

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
  const [r, g, b] = parseHex(hex).map((value) => {
    const c = value / 255
    return c <= 0.03928 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4
  }) as [number, number, number]

  return 0.2126 * r + 0.7152 * g + 0.0722 * b
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
