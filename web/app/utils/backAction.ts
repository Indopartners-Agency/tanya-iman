export type BackAction = 'close-dialog' | 'confirm-exit' | 'go-back' | 'exit'

export interface BackContext {
  path: string
  /** From Capacitor's backButton event: the WebView has history to pop. */
  canGoBack: boolean
  /** The seeker has sent at least one question. */
  hasConversation: boolean
  dialogOpen: boolean
}

/**
 * Chat UX section 12: the hardware back button pops in-app navigation first,
 * and never leaves a conversation silently — one confirm, then exit.
 */
export function backAction(ctx: BackContext): BackAction {
  if (ctx.dialogOpen) return 'close-dialog'
  if (ctx.path === '/chat' && ctx.hasConversation) return 'confirm-exit'
  if (ctx.path === '/' || !ctx.canGoBack) return 'exit'
  return 'go-back'
}
