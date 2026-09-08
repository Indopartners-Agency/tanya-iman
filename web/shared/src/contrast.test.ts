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
