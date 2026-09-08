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
