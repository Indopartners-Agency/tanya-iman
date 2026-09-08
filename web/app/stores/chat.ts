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

  async function start() {
    const api = useApi()
    const { platform, embedOrigin } = usePlatform()

    const { session_id } = await api.createSession({
      platform,
      embed_origin: embedOrigin,
    })
    sessionId.value = session_id
    messages.value = []

    push({
      id: 'greeting',
      role: 'iman',
      text: t('shared.greeting'),
    })
  }

  async function ask(text: string) {
    const trimmed = text.trim()
    if (!trimmed || sending.value) return
    if (!sessionId.value) await start()

    error.value = null
    sending.value = true

    push({ id: `local_${Date.now()}`, role: 'seeker', text: trimmed })
    const placeholderId = `pending_${Date.now()}`
    push({ id: placeholderId, role: 'iman', text: '', pending: true })

    try {
      const api = useApi()
      const response: AskResponse = await api.ask({
        session_id: sessionId.value!,
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

  function reset() {
    messages.value = []
    sessionId.value = null
    error.value = null
  }

  return { messages, sessionId, sending, error, start, ask, toggleLike, retry, reset }
})
