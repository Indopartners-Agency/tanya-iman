export interface TextPart {
  text: string
  tel?: string
}

/**
 * F-30 & F-44: Extracts phone numbers (e.g. "119", "(021) 500-454", "+62 812-3456-7890")
 * so they render as tappable `tel:` links with >=44px touch targets.
 */
export function parseTextWithPhoneLinks(raw: string): TextPart[] {
  const text = raw || ''
  const phoneRegex = /(\+?\d[\d\s()-]{6,}\d|\(\d{2,4}\)\s*\d{3}[-\s]?\d{3,4}|\b119\b)/g
  const parts: TextPart[] = []
  let lastIndex = 0
  for (const match of text.matchAll(phoneRegex)) {
    const idx = match.index ?? 0
    if (idx > lastIndex) {
      parts.push({ text: text.slice(lastIndex, idx) })
    }
    const matched = match[0]
    const cleanTel = matched.replace(/[^\d+]/g, '')
    parts.push({ text: matched, tel: cleanTel })
    lastIndex = idx + matched.length
  }
  if (lastIndex < text.length) {
    parts.push({ text: text.slice(lastIndex) })
  }
  return parts.length > 0 ? parts : [{ text }]
}
