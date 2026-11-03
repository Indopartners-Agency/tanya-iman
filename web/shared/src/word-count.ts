/**
 * Word counting for the admin answer editor's live counter.
 *
 * This is a deliberate port of backend/services/text.py, not an independent
 * implementation. The backend validator is what actually blocks publication
 * (F-11, 25-250 words); if this counter disagrees with it, an editor sees
 * "248 words" and then gets rejected on save, and stops trusting the tool.
 *
 * Any change here must be mirrored in backend/services/text.py, and the test
 * cases in word-count.test.ts are duplicated in backend/tests/test_text.py.
 */

// A "word" is a run of characters containing at least one letter or digit.
// Standalone punctuation does not count; hyphenated and apostrophised forms
// count once ("anak-anak", "Al-Masih", "Qur'an").
const WORD = /[\p{L}\p{N}]+(?:[-'\u2019][\p{L}\p{N}]+)*/gu

export const MIN_WORDS = 25
export const MAX_WORDS = 350

export function countWords(text: string): number {
  return (text ?? '').match(WORD)?.length ?? 0
}

export function withinLengthBounds(text: string): boolean {
  const n = countWords(text)
  return n >= MIN_WORDS && n <= MAX_WORDS
}

export type LengthState = 'short' | 'ok' | 'long'

export function lengthState(text: string): LengthState {
  const n = countWords(text)
  if (n < MIN_WORDS) return 'short'
  if (n > MAX_WORDS) return 'long'
  return 'ok'
}
