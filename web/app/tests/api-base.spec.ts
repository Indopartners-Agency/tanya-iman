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
