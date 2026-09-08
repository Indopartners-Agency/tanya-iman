/**
 * Reports the widget's content height to the host page (Chat UX section 11).
 *
 * Without this the host has to guess a fixed frame height, which either clips
 * a long answer or leaves a band of empty space under a short one.
 *
 * postMessage targets '*' because the host origin is not knowable from inside
 * the frame — document.referrer is unreliable once the user navigates. Nothing
 * sensitive is sent: the payload is a single number.
 */
export function useEmbedHeight(enabled: MaybeRef<boolean>): void {
  if (import.meta.server) return

  const active = computed(() => unref(enabled))
  let observer: ResizeObserver | undefined

  function report() {
    if (!active.value) return
    const height = Math.ceil(document.documentElement.scrollHeight)
    window.parent?.postMessage({ type: 'tanya-iman:height', height }, '*')
  }

  onMounted(() => {
    if (!active.value) return
    report()
    observer = new ResizeObserver(report)
    observer.observe(document.documentElement)
  })

  onUnmounted(() => observer?.disconnect())
}
