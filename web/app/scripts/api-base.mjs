import { pathToFileURL } from 'node:url'

/**
 * PIP Task 7.3 / Runbook B1: an Android build bakes NUXT_PUBLIC_API_BASE into
 * the APK. A build pointing at plain HTTP or a developer's machine cannot be
 * fixed without shipping a new build, so it is refused before `cap sync`.
 */
const LOCAL_HOST =
  /^(localhost|0\.0\.0\.0|127\.|10\.|192\.168\.|172\.(1[6-9]|2\d|3[01])\.)/

/**
 * @param {string | undefined} value
 * @returns {string | null} why the value is unacceptable, or null if it is fine
 */
export function checkApiBase(value) {
  if (!value) return 'NUXT_PUBLIC_API_BASE is not set'

  let url
  try {
    url = new URL(value)
  } catch {
    return `NUXT_PUBLIC_API_BASE is not a URL: ${value}`
  }

  if (url.protocol !== 'https:') return `NUXT_PUBLIC_API_BASE must be HTTPS: ${value}`
  if (LOCAL_HOST.test(url.hostname)) {
    return `NUXT_PUBLIC_API_BASE points at a local host: ${value}`
  }
  return null
}

if (process.argv[1] && import.meta.url === pathToFileURL(process.argv[1]).href) {
  const problem = checkApiBase(process.env.NUXT_PUBLIC_API_BASE)
  if (problem) {
    console.error(`[android] ${problem}`)
    process.exit(1)
  }
  console.log(`[android] API base OK: ${process.env.NUXT_PUBLIC_API_BASE}`)
}
