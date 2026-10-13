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
