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
