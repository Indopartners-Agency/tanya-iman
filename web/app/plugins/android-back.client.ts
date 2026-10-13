import { App } from '@capacitor/app'
import { Capacitor } from '@capacitor/core'

/**
 * Android only. Without a listener, the hardware back button closes the app
 * from any screen, including mid-conversation.
 */
export default defineNuxtPlugin(() => {
  if (!Capacitor.isNativePlatform()) return

  const router = useRouter()
  const chat = useChatStore()
  const { open } = useExitConfirm()

  void App.addListener('backButton', ({ canGoBack }) => {
    const action = backAction({
      path: router.currentRoute.value.path,
      canGoBack,
      hasConversation: chat.messages.some((m) => m.role === 'seeker'),
      dialogOpen: open.value,
    })

    if (action === 'close-dialog') open.value = false
    else if (action === 'confirm-exit') open.value = true
    else if (action === 'go-back') router.back()
    else void App.exitApp()
  })
})
