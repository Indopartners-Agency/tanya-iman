import type { Platform } from '@tanya-iman/shared'

export type CitationLinkMode = 'new-tab' | 'top' | 'system'

/**
 * Web opens a new tab. The widget escapes its 620px iframe. Android hands the
 * URL to the system browser, because a link that opens inside the WebView
 * replaces the conversation, and a seeker who cannot get back has lost it
 * (Chat UX section 9; Runbook A8, a release blocker).
 */
export function citationLinkMode(platform: Platform): CitationLinkMode {
  if (platform === 'widget') return 'top'
  if (platform === 'android') return 'system'
  return 'new-tab'
}
