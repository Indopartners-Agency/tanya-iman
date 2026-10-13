/**
 * Shared between the back-button plugin, which opens the dialog, and the
 * dialog itself. Module scope is safe: the app is a client-only SPA.
 */
const open = ref(false)

export function useExitConfirm() {
  return { open }
}
