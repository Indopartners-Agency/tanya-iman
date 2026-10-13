import { defineStore } from 'pinia'
import {
  ApiError,
  type AnswerSource,
  type AskResponse,
  type Citation,
} from '@tanya-iman/shared'

/**
 * The backend's AnswerSource plus the one state that arrives as an HTTP status
 * rather than as a field. Chat UX section 8 lists rate-limited alongside the
 * answer sources because it is a bubble the seeker sees, but the wire type in
 * web/shared mirrors backend/models/schemas.py and must not gain a member the
 * backend never sends.
 */
type MessageSource = AnswerSource | 'rate_limited'

export interface Message {
  id: string
  role: 'seeker' | 'iman'
  text: string
  citations?: Citation[]
  /** Absent on seeker messages and on system copy. */
  questionId?: string
  likeable?: boolean
  liked?: boolean
  pending?: boolean
  /**
   * Drives which bubble treatment renders (Chat UX section 8). The frontend
   * selects on this and on `likeable`; it never re-derives either.
   */
  answerSource?: MessageSource
  /** Set on a rate-limited turn. Seconds remaining, counted down live. */
  retryAfterSeconds?: number
  /** The seeker text that produced a failed turn, so Coba lagi can resend it. */
  failedQuestion?: string
  /** The turn failed because the request never left the device. */
  offline?: boolean
}

export const useChatStore = defineStore('chat', () => {
  const messages = ref<Message[]>([])
  const sessionId = ref<string | null>(null)
  const sending = ref(false)
  const error = ref<string | null>(null)

  const { t } = useCopy()

  function push(message: Message) {
    messages.value.push(message)
  }

  /**
   * Opening the conversation must not depend on the network: offline at
   * launch, the greeting still renders and the session is opened by the first
   * question instead (Chat UX section 12).
   */
  async function start() {
    messages.value = []
    sessionId.value = null
    push({
      id: 'greeting',
      role: 'iman',
      text: t('shared.greeting'),
    })

    try {
      await openSession()
    } catch (err) {
      if (!isNetworkFailure(err, navigator.onLine)) throw err
    }
  }

  async function openSession(): Promise<string> {
    const { platform, embedOrigin } = usePlatform()
    const { session_id } = await useApi().createSession({
      platform,
      embed_origin: embedOrigin,
    })
    sessionId.value = session_id
    return session_id
  }

  async function ask(text: string) {
    const trimmed = text.trim()
    if (!trimmed || sending.value) return

    error.value = null
    sending.value = true

    push({ id: `local_${Date.now()}`, role: 'seeker', text: trimmed })
    const placeholderId = `pending_${Date.now()}`
    push({ id: placeholderId, role: 'iman', text: '', pending: true })

    try {
      const session = sessionId.value ?? (await openSession())
      const response: AskResponse = await useApi().ask({
        session_id: session,
        text: trimmed,
      })
      replacePending(placeholderId, {
        id: response.question_id,
        role: 'iman',
        text: response.answer_text,
        citations: response.citations,
        questionId: response.question_id,
        likeable: response.likeable,
        liked: false,
        answerSource: response.answer_source,
      })
    } catch (err) {
      handleAskError(err, placeholderId, trimmed)
    } finally {
      sending.value = false
    }
  }

  function replacePending(placeholderId: string, message: Message) {
    const index = messages.value.findIndex((m) => m.id === placeholderId)
    if (index >= 0) messages.value[index] = message
  }

  function handleAskError(err: unknown, placeholderId: string, question: string) {
    // Rate limits and expired sessions are ordinary outcomes, not faults, and
    // are shown as a message in the conversation rather than as an error
    // banner. Getting told "you have asked a lot today, come back in 20
    // minutes" should not feel like the app broke.
    if (err instanceof ApiError && err.isRateLimited) {
      replacePending(placeholderId, {
        id: placeholderId,
        role: 'iman',
        text: '',
        answerSource: 'rate_limited',
        retryAfterSeconds: err.retryAfterSeconds ?? 60 * 60,
        failedQuestion: question,
      })
      return
    }

    if (err instanceof ApiError && err.isSessionGone) {
      sessionId.value = null
      replacePending(placeholderId, {
        id: placeholderId,
        role: 'iman',
        text: t('ui.session_expired'),
        answerSource: 'error',
        failedQuestion: question,
      })
      return
    }

    if (isNetworkFailure(err, navigator.onLine)) {
      replacePending(placeholderId, {
        id: placeholderId,
        role: 'iman',
        text: t('ui.network_error'),
        answerSource: 'error',
        failedQuestion: question,
        offline: true,
      })
      return
    }

    // The failure is visible inside the conversation with its own retry, so a
    // separate error banner would say the same thing twice.
    replacePending(placeholderId, {
      id: placeholderId,
      role: 'iman',
      text: '',
      answerSource: 'error',
      failedQuestion: question,
    })
  }

  async function toggleLike(questionId: string) {
    const message = messages.value.find((m) => m.questionId === questionId)
    if (!message || !message.likeable) return

    const next = !message.liked
    message.liked = next // optimistic; a failed like is not worth an error state
    try {
      await useApi().like(questionId, next)
    } catch {
      message.liked = !next
    }
  }

  /**
   * F-27: the failed question stays in the transcript and Coba lagi resends
   * the identical text. The seeker never retypes.
   */
  async function retry(messageId: string) {
    const index = messages.value.findIndex((m) => m.id === messageId)
    if (index < 0) return

    const question = messages.value[index]?.failedQuestion
    if (!question) return

    // Drop the failed answer bubble and the seeker bubble above it, then ask
    // again — otherwise the transcript accumulates a copy of the question per
    // attempt.
    const removeFrom =
      index > 0 && messages.value[index - 1]?.role === 'seeker' ? index - 1 : index
    messages.value.splice(removeFrom)

    await ask(question)
  }

  /** Chat UX section 12: when the connection returns, resend the last turn that never left. */
  async function retryOffline() {
    if (sending.value) return
    const failed = [...messages.value].reverse().find((m) => m.offline && m.failedQuestion)
    if (failed) await retry(failed.id)
  }

  function reset() {
    messages.value = []
    sessionId.value = null
    error.value = null
  }

  return { messages, sessionId, sending, error, start, ask, toggleLike, retry, retryOffline, reset }
})
